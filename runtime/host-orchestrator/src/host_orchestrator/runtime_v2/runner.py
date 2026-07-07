from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from datetime import datetime, timezone
from fnmatch import fnmatchcase
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
from typing import Any

from host_orchestrator.config_runtime import RuntimeConfigBundle, RuntimeConfigError, load_runtime_config
from host_orchestrator.canonical_result import build_run_id
from host_orchestrator.path_guard import (
    capture_workspace_change_set,
    enforce_workspace_change_policy,
    validate_task_paths,
)
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.worker import WorkerLike
from host_orchestrator.worker_factory import RuntimeWorkerFactory

from host_orchestrator.runtime_v2 import admission, storage
from host_orchestrator.runtime_v2.artifacts import (
    V2Artifacts,
    build_artifacts,
    ensure_artifact_dirs,
    repo_relative,
    write_json,
)
from host_orchestrator.runtime_v2.contracts import RuntimeV2Task, load_task
from host_orchestrator.runtime_v2.executor import execute_task
from host_orchestrator.runtime_v2.scheduler import (
    determine_execution_profile,
    should_enter_review,
    should_pause_for_policy,
)
from host_orchestrator.runtime_v2.tracing import trace_manifest_payload


FIXED_GATE_ORDER = ("build", "lint", "typecheck", "test", "contract", "hotspot")


@dataclass(frozen=True)
class RuntimeV2Config:
    workspace_root: Path
    layout: RuntimeLayout
    worker_id: str = "runtime-v2-default"
    worker_profile: str | None = None
    run_id: str | None = None


class RuntimeV2Runner:
    def __init__(
        self,
        config: RuntimeV2Config,
        worker: WorkerLike | None = None,
        *,
        worker_factory: RuntimeWorkerFactory | None = None,
    ) -> None:
        self._config = config
        self._worker = worker
        self._worker_factory = worker_factory or RuntimeWorkerFactory()
        self._runtime_config = load_runtime_config(config.layout.repo_root)
        self._layout = config.layout.with_runtime_v2_paths(
            control_plane_db_v2=self._runtime_config.runtime.control_plane_db_v2,
            artifact_root_v2=self._runtime_config.runtime.artifact_root_v2,
        )
        self._config = replace(config, layout=self._layout)
        if not self._runtime_config.runtime.experimental_v2_enabled:
            raise RuntimeConfigError(
                "runtime_v2 is disabled. Set orchestrator.yaml:runtime.experimental_v2_enabled=true before running v2."
            )

    def run_task(self, task_path: Path) -> Path:
        task = load_task(task_path)
        worker_profile = self._resolve_worker_profile(task)
        verification_profile = self._resolve_verification_profile(task)
        continuation_policy = self._resolve_continuation_policy(task)
        retry_policy = self._resolve_retry_policy()
        started_at = _utc_now_iso()
        run_id = self._config.run_id or build_run_id(
            prefix=f"{self._runtime_config.orchestrator.run_id_prefix}-v2"
        )

        storage.initialize_control_plane_v2(self._layout.control_plane_v2_db)
        storage.upsert_task(
            self._layout.control_plane_v2_db,
            task_id=task.task_id,
            title=task.title,
            risk_level=task.risk_level,
            worker_profile=worker_profile.name,
            verification_profile=verification_profile.name,
            continuation_policy=continuation_policy.name,
            write_access=task.write_access,
            requires_network=task.requires_network,
            requires_gui=task.requires_gui,
            status="queued",
            status_reason="task registered for runtime_v2 scheduling",
            created_at=started_at,
            updated_at=started_at,
        )
        storage.replace_dependencies(
            self._layout.control_plane_v2_db,
            task_id=task.task_id,
            dependency_refs=task.dependency_refs,
            created_at=started_at,
        )

        attempt_number = storage.next_attempt_number(
            self._layout.control_plane_v2_db,
            task_id=task.task_id,
        )
        attempt_id = f"{task.task_id}-a{attempt_number:03d}"
        execution_profile = determine_execution_profile(task)
        artifacts = build_artifacts(
            layout=self._layout,
            run_id=run_id,
            task_id=task.task_id,
            attempt_id=attempt_id,
        )
        ensure_artifact_dirs(artifacts)

        unresolved = storage.unresolved_dependency_refs(
            self._layout.control_plane_v2_db,
            task_id=task.task_id,
        )
        if unresolved:
            storage.create_attempt(
                self._layout.control_plane_v2_db,
                attempt_id=attempt_id,
                task_id=task.task_id,
                run_id=run_id,
                attempt_number=attempt_number,
                state="blocked",
                status_reason="waiting for dependency completion",
                execution_profile=execution_profile,
                worker_profile=worker_profile.name,
                started_at=started_at,
                updated_at=started_at,
            )
            return self._write_blocked_result(
                task=task,
                worker_profile_name=worker_profile.name,
                verification_profile_name=verification_profile.name,
                continuation_policy_name=continuation_policy.name,
                run_id=run_id,
                attempt_id=attempt_id,
                attempt_number=attempt_number,
                artifacts=artifacts,
                blocked_reasons=unresolved,
                created_at=started_at,
            )

        storage.create_attempt(
            self._layout.control_plane_v2_db,
            attempt_id=attempt_id,
            task_id=task.task_id,
            run_id=run_id,
            attempt_number=attempt_number,
            state="ready",
            status_reason="dependency checks satisfied",
            execution_profile=execution_profile,
            worker_profile=worker_profile.name,
            started_at=started_at,
            updated_at=started_at,
        )

        slot_token: str | None = None
        try:
            slot_token = admission.acquire_slot(
                self._layout.control_plane_v2_db,
                worker_profile=worker_profile.name,
                max_slots=worker_profile.max_active_leases,
                attempt_id=attempt_id,
                worker_id=self._config.worker_id,
                acquired_at=started_at,
            )
        except admission.AdmissionConflictError as exc:
            return self._write_paused_result(
                task=task,
                worker_profile_name=worker_profile.name,
                verification_profile_name=verification_profile.name,
                continuation_policy_name=continuation_policy.name,
                run_id=run_id,
                attempt_id=attempt_id,
                attempt_number=attempt_number,
                artifacts=artifacts,
                status_reason=str(exc),
                next_action="wait_for_available_worker_slot",
                created_at=started_at,
            )

        try:
            storage.update_attempt(
                self._layout.control_plane_v2_db,
                attempt_id=attempt_id,
                state="running",
                updated_at=started_at,
                status_reason="worker execution in progress",
            )
            storage.upsert_task(
                self._layout.control_plane_v2_db,
                task_id=task.task_id,
                title=task.title,
                risk_level=task.risk_level,
                worker_profile=worker_profile.name,
                verification_profile=verification_profile.name,
                continuation_policy=continuation_policy.name,
                write_access=task.write_access,
                requires_network=task.requires_network,
                requires_gui=task.requires_gui,
                status="running",
                status_reason="worker execution in progress",
                created_at=started_at,
                updated_at=started_at,
            )

            workspace_root = self._resolve_workspace_root(task)
            baseline_changes = capture_workspace_change_set(workspace_root)
            worker = self._worker or self._worker_factory.build(worker_profile)
            worker_result = execute_task(
                task=task,
                worker=worker,
                worker_profile=worker_profile,
                workspace_root=workspace_root,
            )

            guard_task = SimpleNamespace(
                worktree_path=task.worktree_path,
                allowed_paths=task.allowed_paths,
                forbidden_paths=task.forbidden_paths,
                artifacts_out=task.artifacts_out,
                write_access=task.write_access,
                branch_name=task.branch_name,
            )
            enforce_workspace_change_policy(
                task=guard_task,
                workspace_root=workspace_root,
                baseline_changes=baseline_changes,
            )
            gate_report = _run_verification_profile(
                verification_profile=verification_profile,
                workspace_root=workspace_root,
            )
            gate_failed = gate_report["status"] == "failed"
            policy_surface_touched = _touches_policy_surface(
                runtime_config=self._runtime_config,
                changed_paths=gate_report["changed_paths"],
            )
            review_required = should_enter_review(
                task=task,
                continuation_policy=continuation_policy,
                policy_surface_touched=policy_surface_touched,
                gate_failed=gate_failed,
            )
            policy_pause = should_pause_for_policy(
                continuation_policy=continuation_policy,
                policy_surface_touched=policy_surface_touched,
                gate_failed=gate_failed,
            )

            if gate_failed and retry_policy.retry_on_gate_failure:
                final_state = "retryable"
                next_action = "retry_from_verification"
                status_reason = "verification profile reported failures that allow retry"
            elif review_required:
                final_state = "reviewing" if continuation_policy.auto_continue else "paused"
                next_action = "review_task_artifacts"
                status_reason = "risk level or policy surface requires bounded review"
            elif policy_pause:
                final_state = "paused"
                next_action = "resolve_policy_pause_and_resume"
                status_reason = "continuation policy blocked autonomous closeout"
            else:
                final_state = "completed"
                next_action = "none"
                status_reason = "task completed within runtime_v2 autonomous boundary"

            finished_at = _utc_now_iso()
            review_result_ref = None
            if review_required:
                review_payload = {
                    "review_mode": "blocking",
                    "state": final_state,
                    "reasons": [
                        "risk_level requires review"
                        if task.risk_level in continuation_policy.review_on_risk_levels
                        else "policy surface requires review"
                    ],
                    "recommended_action": "revise" if gate_failed else "inspect",
                }
                write_json(artifacts.review_result, review_payload)
                review_result_ref = repo_relative(self._layout, artifacts.review_result)
                storage.record_artifact(
                    self._layout.control_plane_v2_db,
                    attempt_id=attempt_id,
                    kind="review_result",
                    path=review_result_ref,
                    created_at=finished_at,
                )

            return self._write_final_result(
                task=task,
                worker_profile_name=worker_profile.name,
                verification_profile_name=verification_profile.name,
                continuation_policy_name=continuation_policy.name,
                run_id=run_id,
                attempt_id=attempt_id,
                attempt_number=attempt_number,
                execution_profile=execution_profile,
                artifacts=artifacts,
                worker_result=worker_result,
                gate_report=gate_report,
                final_state=final_state,
                next_action=next_action,
                status_reason=status_reason,
                review_result_ref=review_result_ref,
                started_at=started_at,
                finished_at=finished_at,
            )
        except Exception as exc:
            failed_at = _utc_now_iso()
            failure_state = "retryable" if retry_policy.retry_on_worker_failure else "failed"
            failure_next_action = (
                "retry_from_worker_execution"
                if retry_policy.retry_on_worker_failure
                else "inspect_failure_and_retry"
            )
            return self._write_failure_result(
                task=task,
                worker_profile_name=worker_profile.name,
                verification_profile_name=verification_profile.name,
                continuation_policy_name=continuation_policy.name,
                run_id=run_id,
                attempt_id=attempt_id,
                attempt_number=attempt_number,
                artifacts=artifacts,
                final_state=failure_state,
                next_action=failure_next_action,
                status_reason=str(exc),
                failed_at=failed_at,
            )
        finally:
            if slot_token is not None:
                admission.release_slot(
                    self._layout.control_plane_v2_db,
                    slot_token=slot_token,
                    released_at=_utc_now_iso(),
                )

    def resume_attempt(self, *, attempt_id: str, resume_point: str, reason: str) -> dict[str, object]:
        record = storage.load_attempt(self._layout.control_plane_v2_db, attempt_id=attempt_id)
        task = storage.load_task(self._layout.control_plane_v2_db, task_id=record.task_id)
        updated_at = _utc_now_iso()
        storage.update_attempt(
            self._layout.control_plane_v2_db,
            attempt_id=attempt_id,
            state="ready",
            updated_at=updated_at,
            status_reason=reason or f"resume requested from {resume_point}",
            resume_point=resume_point,
        )
        storage.upsert_task(
            self._layout.control_plane_v2_db,
            task_id=task.task_id,
            title=task.title,
            risk_level=task.risk_level,
            worker_profile=task.worker_profile,
            verification_profile=task.verification_profile,
            continuation_policy=task.continuation_policy,
            write_access=task.write_access,
            requires_network=task.requires_network,
            requires_gui=task.requires_gui,
            status="ready",
            status_reason=reason or f"resume requested from {resume_point}",
            created_at=task.created_at,
            updated_at=updated_at,
        )
        storage.append_event(
            self._layout.control_plane_v2_db,
            task_id=record.task_id,
            attempt_id=attempt_id,
            event_type="attempt_resumed",
            payload={"resume_point": resume_point, "reason": reason},
            created_at=updated_at,
        )
        return {"attempt_id": attempt_id, "state": "ready", "resume_point": resume_point}

    def retry_attempt(self, *, attempt_id: str, retry_rewind: str, reason: str) -> dict[str, object]:
        record = storage.load_attempt(self._layout.control_plane_v2_db, attempt_id=attempt_id)
        task = storage.load_task(self._layout.control_plane_v2_db, task_id=record.task_id)
        updated_at = _utc_now_iso()
        new_attempt_number = storage.next_attempt_number(
            self._layout.control_plane_v2_db,
            task_id=record.task_id,
        )
        new_attempt_id = f"{record.task_id}-a{new_attempt_number:03d}"
        artifacts = build_artifacts(
            layout=self._layout,
            run_id=record.run_id,
            task_id=record.task_id,
            attempt_id=new_attempt_id,
        )
        ensure_artifact_dirs(artifacts)
        attempt_payload = {
            "attempt_id": new_attempt_id,
            "task_id": record.task_id,
            "run_id": record.run_id,
            "attempt_number": new_attempt_number,
            "state": "queued",
            "status_reason": reason or f"retry requested from {retry_rewind}",
            "retry_rewind": retry_rewind,
        }
        write_json(artifacts.attempt_json, attempt_payload)
        storage.create_attempt(
            self._layout.control_plane_v2_db,
            attempt_id=new_attempt_id,
            task_id=record.task_id,
            run_id=record.run_id,
            attempt_number=new_attempt_number,
            state="queued",
            status_reason=reason or f"retry requested from {retry_rewind}",
            execution_profile=record.execution_profile,
            worker_profile=record.worker_profile,
            retry_rewind=retry_rewind,
            started_at=updated_at,
            updated_at=updated_at,
            trace_manifest_path=repo_relative(self._layout, artifacts.trace_manifest),
        )
        storage.upsert_task(
            self._layout.control_plane_v2_db,
            task_id=task.task_id,
            title=task.title,
            risk_level=task.risk_level,
            worker_profile=task.worker_profile,
            verification_profile=task.verification_profile,
            continuation_policy=task.continuation_policy,
            write_access=task.write_access,
            requires_network=task.requires_network,
            requires_gui=task.requires_gui,
            status="queued",
            status_reason=reason or f"retry requested from {retry_rewind}",
            created_at=task.created_at,
            updated_at=updated_at,
        )
        storage.append_event(
            self._layout.control_plane_v2_db,
            task_id=record.task_id,
            attempt_id=new_attempt_id,
            event_type="attempt_retry_requested",
            payload={"retry_rewind": retry_rewind, "reason": reason, "source_attempt_id": attempt_id},
            created_at=updated_at,
        )
        return {
            "source_attempt_id": attempt_id,
            "new_attempt_id": new_attempt_id,
            "state": "queued",
            "retry_rewind": retry_rewind,
        }

    def _resolve_worker_profile(self, task: RuntimeV2Task):
        if self._config.worker_profile is not None:
            return self._runtime_config.worker_profile(self._config.worker_profile)
        if task.worker_profile is not None:
            return self._runtime_config.worker_profile(task.worker_profile)
        return self._runtime_config.worker_profile()

    def _resolve_verification_profile(self, task: RuntimeV2Task):
        try:
            return self._runtime_config.policies.verification_profiles[task.verification_profile]
        except KeyError as exc:
            raise RuntimeConfigError(
                f"Unknown verification profile: {task.verification_profile}"
            ) from exc

    def _resolve_continuation_policy(self, task: RuntimeV2Task):
        try:
            return self._runtime_config.policies.continuation_policies[task.continuation_policy]
        except KeyError as exc:
            raise RuntimeConfigError(
                f"Unknown continuation policy: {task.continuation_policy}"
            ) from exc

    def _resolve_retry_policy(self):
        policies = self._runtime_config.policies.retry_policies
        if "default" in policies:
            return policies["default"]
        if policies:
            return next(iter(policies.values()))
        raise RuntimeConfigError("No retry_policies configured for runtime_v2")

    def _resolve_workspace_root(self, task: RuntimeV2Task) -> Path:
        guard_task = SimpleNamespace(
            worktree_path=task.worktree_path,
            allowed_paths=task.allowed_paths,
            forbidden_paths=task.forbidden_paths,
            artifacts_out=task.artifacts_out,
        )
        workspace_root = validate_task_paths(
            task=guard_task,
            repo_root=self._layout.repo_root,
        )
        workspace_root.mkdir(parents=True, exist_ok=True)
        return workspace_root

    def _write_blocked_result(
        self,
        *,
        task: RuntimeV2Task,
        worker_profile_name: str,
        verification_profile_name: str,
        continuation_policy_name: str,
        run_id: str,
        attempt_id: str,
        attempt_number: int,
        artifacts: V2Artifacts,
        blocked_reasons: list[str],
        created_at: str,
    ) -> Path:
        gate_report = {"status": "blocked", "commands_run": [], "changed_paths": []}
        trace_payload = trace_manifest_payload(
            task_id=task.task_id,
            attempt_id=attempt_id,
            state="blocked",
            execution_profile="blocked",
            stages=[{"stage": "dependency_check", "status": "blocked"}],
            usage=None,
        )
        result_payload = {
            "task_id": task.task_id,
            "run_id": run_id,
            "attempt_id": attempt_id,
            "attempt_number": attempt_number,
            "status": "blocked",
            "worker_profile": worker_profile_name,
            "verification_profile": verification_profile_name,
            "continuation_policy": continuation_policy_name,
            "repo_side_done": [],
            "still_open": blocked_reasons,
            "live_accepted": False,
            "next_action": "complete_dependencies_then_retry",
            "status_reason": "dependency_refs are not satisfied",
            "gate_report_ref": repo_relative(self._layout, artifacts.gate_report),
            "trace_manifest_ref": repo_relative(self._layout, artifacts.trace_manifest),
            "review_result_ref": None,
            "closeout_bundle_ref": repo_relative(self._layout, artifacts.closeout_bundle),
        }
        write_json(artifacts.attempt_json, {
            "attempt_id": attempt_id,
            "task_id": task.task_id,
            "run_id": run_id,
            "attempt_number": attempt_number,
            "state": "blocked",
            "status_reason": "dependency_refs are not satisfied",
        })
        write_json(artifacts.gate_report, gate_report)
        write_json(artifacts.trace_manifest, trace_payload)
        write_json(artifacts.closeout_bundle, {
            "status": "blocked",
            "repo_side_done": [],
            "still_open": blocked_reasons,
            "next_action": "complete_dependencies_then_retry",
        })
        write_json(artifacts.result_json, result_payload)
        storage.update_attempt(
            self._layout.control_plane_v2_db,
            attempt_id=attempt_id,
            state="blocked",
            updated_at=created_at,
            status_reason="dependency_refs are not satisfied",
            gate_report_path=repo_relative(self._layout, artifacts.gate_report),
            result_path=repo_relative(self._layout, artifacts.result_json),
            trace_manifest_path=repo_relative(self._layout, artifacts.trace_manifest),
        )
        storage.upsert_task(
            self._layout.control_plane_v2_db,
            task_id=task.task_id,
            title=task.title,
            risk_level=task.risk_level,
            worker_profile=worker_profile_name,
            verification_profile=verification_profile_name,
            continuation_policy=continuation_policy_name,
            write_access=task.write_access,
            requires_network=task.requires_network,
            requires_gui=task.requires_gui,
            status="blocked",
            status_reason="dependency_refs are not satisfied",
            created_at=created_at,
            updated_at=created_at,
        )
        storage.append_event(
            self._layout.control_plane_v2_db,
            task_id=task.task_id,
            attempt_id=attempt_id,
            event_type="task_blocked",
            payload={"blocked_reasons": blocked_reasons},
            created_at=created_at,
        )
        return artifacts.result_json

    def _write_paused_result(
        self,
        *,
        task: RuntimeV2Task,
        worker_profile_name: str,
        verification_profile_name: str,
        continuation_policy_name: str,
        run_id: str,
        attempt_id: str,
        attempt_number: int,
        artifacts: V2Artifacts,
        status_reason: str,
        next_action: str,
        created_at: str,
    ) -> Path:
        write_json(artifacts.attempt_json, {
            "attempt_id": attempt_id,
            "task_id": task.task_id,
            "run_id": run_id,
            "attempt_number": attempt_number,
            "state": "paused",
            "status_reason": status_reason,
        })
        write_json(artifacts.gate_report, {"status": "paused", "commands_run": [], "changed_paths": []})
        write_json(
            artifacts.trace_manifest,
            trace_manifest_payload(
                task_id=task.task_id,
                attempt_id=attempt_id,
                state="paused",
                execution_profile="admission_wait",
                stages=[{"stage": "admission", "status": "paused"}],
                usage=None,
            ),
        )
        write_json(artifacts.closeout_bundle, {
            "status": "paused",
            "repo_side_done": [],
            "still_open": [next_action],
            "next_action": next_action,
        })
        write_json(artifacts.result_json, {
            "task_id": task.task_id,
            "run_id": run_id,
            "attempt_id": attempt_id,
            "attempt_number": attempt_number,
            "status": "paused",
            "worker_profile": worker_profile_name,
            "verification_profile": verification_profile_name,
            "continuation_policy": continuation_policy_name,
            "repo_side_done": [],
            "still_open": [next_action],
            "live_accepted": False,
            "next_action": next_action,
            "status_reason": status_reason,
            "gate_report_ref": repo_relative(self._layout, artifacts.gate_report),
            "trace_manifest_ref": repo_relative(self._layout, artifacts.trace_manifest),
            "review_result_ref": None,
            "closeout_bundle_ref": repo_relative(self._layout, artifacts.closeout_bundle),
        })
        storage.update_attempt(
            self._layout.control_plane_v2_db,
            attempt_id=attempt_id,
            state="paused",
            updated_at=created_at,
            status_reason=status_reason,
            gate_report_path=repo_relative(self._layout, artifacts.gate_report),
            result_path=repo_relative(self._layout, artifacts.result_json),
            trace_manifest_path=repo_relative(self._layout, artifacts.trace_manifest),
        )
        storage.upsert_task(
            self._layout.control_plane_v2_db,
            task_id=task.task_id,
            title=task.title,
            risk_level=task.risk_level,
            worker_profile=worker_profile_name,
            verification_profile=verification_profile_name,
            continuation_policy=continuation_policy_name,
            write_access=task.write_access,
            requires_network=task.requires_network,
            requires_gui=task.requires_gui,
            status="paused",
            status_reason=status_reason,
            created_at=created_at,
            updated_at=created_at,
        )
        storage.append_event(
            self._layout.control_plane_v2_db,
            task_id=task.task_id,
            attempt_id=attempt_id,
            event_type="attempt_paused",
            payload={"next_action": next_action, "status_reason": status_reason},
            created_at=created_at,
        )
        return artifacts.result_json

    def _write_final_result(
        self,
        *,
        task: RuntimeV2Task,
        worker_profile_name: str,
        verification_profile_name: str,
        continuation_policy_name: str,
        run_id: str,
        attempt_id: str,
        attempt_number: int,
        execution_profile: str,
        artifacts: V2Artifacts,
        worker_result,
        gate_report: dict[str, Any],
        final_state: str,
        next_action: str,
        status_reason: str,
        review_result_ref: str | None,
        started_at: str,
        finished_at: str,
    ) -> Path:
        changed_paths = gate_report["changed_paths"]
        repo_side_done = ["formal result artifact", "gate report", "trace manifest"]
        still_open = [] if final_state == "completed" else [next_action]
        result_payload = {
            "task_id": task.task_id,
            "run_id": run_id,
            "attempt_id": attempt_id,
            "attempt_number": attempt_number,
            "status": final_state,
            "worker_profile": worker_profile_name,
            "verification_profile": verification_profile_name,
            "continuation_policy": continuation_policy_name,
            "execution_profile": execution_profile,
            "repo_side_done": repo_side_done,
            "still_open": still_open,
            "live_accepted": False,
            "next_action": next_action,
            "status_reason": status_reason,
            "started_at": started_at,
            "finished_at": finished_at,
            "gate_report_ref": repo_relative(self._layout, artifacts.gate_report),
            "trace_manifest_ref": repo_relative(self._layout, artifacts.trace_manifest),
            "review_result_ref": review_result_ref,
            "closeout_bundle_ref": repo_relative(self._layout, artifacts.closeout_bundle),
            "stdout_log": repo_relative(self._layout, artifacts.stdout_log),
            "stderr_log": repo_relative(self._layout, artifacts.stderr_log),
        }
        write_json(artifacts.attempt_json, {
            "attempt_id": attempt_id,
            "task_id": task.task_id,
            "run_id": run_id,
            "attempt_number": attempt_number,
            "state": final_state,
            "status_reason": status_reason,
            "execution_profile": execution_profile,
        })
        artifacts.stdout_log.write_text(worker_result.stdout_text or (worker_result.final_response or ""), encoding="utf-8")
        artifacts.stderr_log.write_text(worker_result.stderr_text or "", encoding="utf-8")
        write_json(artifacts.gate_report, gate_report)
        write_json(
            artifacts.trace_manifest,
            trace_manifest_payload(
                task_id=task.task_id,
                attempt_id=attempt_id,
                state=final_state,
                execution_profile=execution_profile,
                stages=[
                    {"stage": "execution", "status": "completed"},
                    {"stage": "gating", "status": gate_report["status"]},
                    {"stage": "closeout", "status": final_state},
                ],
                usage=_usage_payload(worker_result),
            ),
        )
        write_json(artifacts.closeout_bundle, {
            "status": final_state,
            "repo_side_done": repo_side_done,
            "still_open": still_open,
            "next_action": next_action,
            "changed_paths": changed_paths,
        })
        write_json(artifacts.result_json, result_payload)

        storage.update_attempt(
            self._layout.control_plane_v2_db,
            attempt_id=attempt_id,
            state=final_state,
            updated_at=finished_at,
            status_reason=status_reason,
            gate_report_path=repo_relative(self._layout, artifacts.gate_report),
            result_path=repo_relative(self._layout, artifacts.result_json),
            trace_manifest_path=repo_relative(self._layout, artifacts.trace_manifest),
        )
        storage.upsert_task(
            self._layout.control_plane_v2_db,
            task_id=task.task_id,
            title=task.title,
            risk_level=task.risk_level,
            worker_profile=worker_profile_name,
            verification_profile=verification_profile_name,
            continuation_policy=continuation_policy_name,
            write_access=task.write_access,
            requires_network=task.requires_network,
            requires_gui=task.requires_gui,
            status=final_state,
            status_reason=status_reason,
            created_at=started_at,
            updated_at=finished_at,
        )
        storage.record_artifact(
            self._layout.control_plane_v2_db,
            attempt_id=attempt_id,
            kind="result",
            path=repo_relative(self._layout, artifacts.result_json),
            created_at=finished_at,
        )
        storage.append_event(
            self._layout.control_plane_v2_db,
            task_id=task.task_id,
            attempt_id=attempt_id,
            event_type=f"attempt_{final_state}",
            payload={"next_action": next_action, "changed_paths": changed_paths},
            created_at=finished_at,
        )
        return artifacts.result_json

    def _write_failure_result(
        self,
        *,
        task: RuntimeV2Task,
        worker_profile_name: str,
        verification_profile_name: str,
        continuation_policy_name: str,
        run_id: str,
        attempt_id: str,
        attempt_number: int,
        artifacts: V2Artifacts,
        final_state: str,
        next_action: str,
        status_reason: str,
        failed_at: str,
    ) -> Path:
        write_json(artifacts.attempt_json, {
            "attempt_id": attempt_id,
            "task_id": task.task_id,
            "run_id": run_id,
            "attempt_number": attempt_number,
            "state": final_state,
            "status_reason": status_reason,
        })
        write_json(artifacts.gate_report, {"status": final_state, "commands_run": [], "changed_paths": []})
        write_json(
            artifacts.trace_manifest,
            trace_manifest_payload(
                task_id=task.task_id,
                attempt_id=attempt_id,
                state=final_state,
                execution_profile=final_state,
                stages=[{"stage": "execution", "status": final_state}],
                usage=None,
            ),
        )
        write_json(artifacts.closeout_bundle, {
            "status": final_state,
            "repo_side_done": [],
            "still_open": [next_action],
            "next_action": next_action,
        })
        write_json(artifacts.result_json, {
            "task_id": task.task_id,
            "run_id": run_id,
            "attempt_id": attempt_id,
            "attempt_number": attempt_number,
            "status": final_state,
            "worker_profile": worker_profile_name,
            "verification_profile": verification_profile_name,
            "continuation_policy": continuation_policy_name,
            "repo_side_done": [],
            "still_open": [next_action],
            "live_accepted": False,
            "next_action": next_action,
            "status_reason": status_reason,
            "gate_report_ref": repo_relative(self._layout, artifacts.gate_report),
            "trace_manifest_ref": repo_relative(self._layout, artifacts.trace_manifest),
            "review_result_ref": None,
            "closeout_bundle_ref": repo_relative(self._layout, artifacts.closeout_bundle),
        })
        storage.update_attempt(
            self._layout.control_plane_v2_db,
            attempt_id=attempt_id,
            state=final_state,
            updated_at=failed_at,
            status_reason=status_reason,
            gate_report_path=repo_relative(self._layout, artifacts.gate_report),
            result_path=repo_relative(self._layout, artifacts.result_json),
            trace_manifest_path=repo_relative(self._layout, artifacts.trace_manifest),
        )
        storage.upsert_task(
            self._layout.control_plane_v2_db,
            task_id=task.task_id,
            title=task.title,
            risk_level=task.risk_level,
            worker_profile=worker_profile_name,
            verification_profile=verification_profile_name,
            continuation_policy=continuation_policy_name,
            write_access=task.write_access,
            requires_network=task.requires_network,
            requires_gui=task.requires_gui,
            status=final_state,
            status_reason=status_reason,
            created_at=failed_at,
            updated_at=failed_at,
        )
        storage.record_artifact(
            self._layout.control_plane_v2_db,
            attempt_id=attempt_id,
            kind="result",
            path=repo_relative(self._layout, artifacts.result_json),
            created_at=failed_at,
        )
        storage.append_event(
            self._layout.control_plane_v2_db,
            task_id=task.task_id,
            attempt_id=attempt_id,
            event_type=f"attempt_{final_state}",
            payload={"status_reason": status_reason, "next_action": next_action},
            created_at=failed_at,
        )
        return artifacts.result_json


def _run_verification_profile(*, verification_profile, workspace_root: Path) -> dict[str, Any]:
    commands_run: list[dict[str, Any]] = []
    changed_paths = sorted(_changed_paths_after_execution(workspace_root))
    failed = False
    for gate in FIXED_GATE_ORDER:
        command = getattr(verification_profile, gate)
        if command is None:
            commands_run.append(
                {
                    "gate": gate,
                    "status": "not_configured",
                    "command": None,
                    "exit_code": None,
                    "stdout": "",
                    "stderr": "",
                }
            )
            continue
        completed = subprocess.run(
            command,
            cwd=workspace_root,
            shell=True,
            text=True,
            capture_output=True,
            check=False,
        )
        status = "pass" if completed.returncode == 0 else "fail"
        if status == "fail":
            failed = True
        commands_run.append(
            {
                "gate": gate,
                "status": status,
                "command": command,
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
    return {
        "status": "failed" if failed else "pass",
        "commands_run": commands_run,
        "changed_paths": changed_paths,
    }


def _touches_policy_surface(*, runtime_config: RuntimeConfigBundle, changed_paths: list[str]) -> bool:
    for path in changed_paths:
        normalized = path.replace("\\", "/")
        for pattern in runtime_config.policies.policy_surface_globs:
            if fnmatchcase(normalized, pattern.replace("\\", "/")):
                return True
    return False


def _changed_paths_after_execution(workspace_root: Path) -> set[str]:
    return capture_workspace_change_set(workspace_root)


def _usage_payload(worker_result) -> dict[str, Any] | None:
    usage = getattr(worker_result, "usage", None)
    if usage is None:
        return None
    return {
        "source": usage.source,
        "last_total_tokens": usage.last.total_tokens,
        "total_tokens": usage.total.total_tokens,
        "model_context_window": usage.model_context_window,
    }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
