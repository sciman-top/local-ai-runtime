from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from fnmatch import fnmatchcase
import json
from pathlib import Path
import tempfile
from typing import Any

from openai_codex import Sandbox

from host_orchestrator import agentbridge, db
from host_orchestrator.agent_work_assets import (
    validate_handoff_receipt_payload,
    validate_review_result_payload,
)
from host_orchestrator.canonical_result import (
    build_run_id,
    refresh_evidence_index,
    update_result_metadata,
    write_closeout_bundle_artifact,
    write_handoff_receipt_artifact,
    write_planner_result_artifact,
    write_result_bundle,
    write_review_result_artifact,
)
from host_orchestrator.canonical_task import CanonicalTask, load_task, task_from_payload
from host_orchestrator.config_runtime import RuntimeConfigBundle, WorkerProfile, load_runtime_config
from host_orchestrator.dispatch_state import (
    build_dispatch_state_path,
    update_dispatch_state,
    write_dispatch_state,
)
from host_orchestrator.path_guard import (
    capture_workspace_change_set,
    enforce_workspace_change_policy,
    validate_task_paths,
)
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.verification import run_verification
from host_orchestrator.worktree_manager import (
    declared_cleanup_status,
    finalize_task_workspace_cleanup,
    prepare_task_workspace,
)
from host_orchestrator.worker import WorkerLike, WorkerRequest, WorkerResult, WorkerUsage
from host_orchestrator.worker_factory import WorkerBuilder


PRE_WORKER_HANDOFF_NEXT_ACTION = "planner handoff required before worker execution"
PLANNER_HANDOFF_NEXT_ACTION = PRE_WORKER_HANDOFF_NEXT_ACTION
PLANNER_RECEIPT_NEXT_ACTION = "planner receipt recorded; operator may continue to worker execution"
PLANNER_OPERATOR_HANDOFF_NEXT_ACTION = "planner requested operator handoff before worker execution"
REVIEW_HANDOFF_NEXT_ACTION = "heterogeneous review required before downstream use"
LIVE_PLANNER_WORKER_KINDS = {"codex_sdk"}


@dataclass(frozen=True)
class HostLocalConfig:
    workspace_root: Path
    layout: RuntimeLayout
    agentbridge_root: Path | None = None
    worker_id: str = "host-local-default"
    worker_profile: str | None = None
    run_id: str | None = None
    attempt: int = 1
    route_reason: str | None = None


@dataclass(frozen=True)
class RouteDecision:
    worker_profile: WorkerProfile
    route_reason: str


@dataclass(frozen=True)
class PlannerSidecarDecision:
    disposition: str
    reason_summary: str
    blocking_reasons: tuple[str, ...]
    plan_outline: tuple[str, ...]
    usage: WorkerUsage | None = None


class HostLocalRunner:
    _LEASE_TTL = timedelta(minutes=30)

    def __init__(
        self,
        config: HostLocalConfig,
        worker: WorkerLike | None = None,
        *,
        review_worker: WorkerLike | None = None,
        worker_factory: WorkerBuilder | None = None,
    ) -> None:
        self._config = config
        self._worker = worker
        self._review_worker = review_worker
        self._worker_factory = worker_factory
        self._runtime_config = load_runtime_config(config.layout.repo_root)

    def run_task(self, task_path: Path) -> Path:
        task = self._load_intake_task(task_path)
        route_decision = self._resolve_route_decision(task)
        worker_profile = route_decision.worker_profile
        route_reason = route_decision.route_reason
        run_id = self._config.run_id or build_run_id(
            prefix=self._runtime_config.orchestrator.run_id_prefix
        )
        started_at = agentbridge.utc_now_iso()
        lease_expires_at = self._lease_expires_at(started_at)
        dispatch_state_path = build_dispatch_state_path(
            layout=self._config.layout,
            run_id=run_id,
            task_id=task.task_id,
        )
        relative_dispatch_state_path = self._relative_to_repo(dispatch_state_path)
        lease_token = db.acquire_lease(
            self._config.layout.control_plane_db,
            task_id=task.task_id,
            worker_id=self._config.worker_id,
            acquired_at=started_at,
            expires_at=lease_expires_at,
        )
        current_workspace_root = self._config.workspace_root.resolve(strict=False)
        current_cleanup_status = declared_cleanup_status(task)
        current_cleanup_owner = (
            "inline_execution" if current_cleanup_status == "inline_only" else "operator"
        )
        current_next_action = "wait_for_worker_result"
        current_status_reason = "worker executing within graded autonomy boundary"
        try:
            db.initialize_control_plane(self._config.layout.control_plane_db)
            db.upsert_worker(
                self._config.layout.control_plane_db,
                worker_id=self._config.worker_id,
                lane=worker_profile.lane,
                status="busy",
                heartbeat_at=started_at,
            )
            db.record_route_decision(
                self._config.layout.control_plane_db,
                task_id=task.task_id,
                selected_lane=worker_profile.lane,
                reason=route_reason,
                created_at=started_at,
            )
            db.upsert_runtime_task(
                self._config.layout.control_plane_db,
                task_id=task.task_id,
                run_id=run_id,
                attempt=self._config.attempt,
                state="running",
                state_reason=current_status_reason,
                execution_lane=worker_profile.lane,
                worker_profile=worker_profile.name,
                next_action=current_next_action,
                cleanup_status=current_cleanup_status,
                cleanup_owner=current_cleanup_owner,
                created_at=started_at,
                updated_at=started_at,
                dispatch_state_path=relative_dispatch_state_path,
            )
            db.append_event(
                self._config.layout.control_plane_db,
                task_id=task.task_id,
                event_type="task_started",
                payload={
                    "lane": worker_profile.lane,
                    "worker_id": self._config.worker_id,
                    "worker_profile": worker_profile.name,
                    "run_id": run_id,
                    "attempt": self._config.attempt,
                    "lease_token": lease_token,
                    "route_reason": route_reason,
                    "next_action": current_next_action,
                },
                created_at=started_at,
            )
            validate_task_paths(task=task, repo_root=self._config.layout.repo_root)
            planner_reasons = self._planner_gate_reasons(task)
            pre_worker_handoff_reasons = self._worker_execution_gate_reasons(task, worker_profile)
            pre_worker_handoff_reasons.extend(self._quota_gate_reasons(worker_profile))
            if planner_reasons:
                pre_worker_handoff_reasons.extend(
                    self._planner_sidecar_gate_reasons(worker_profile)
                )
            if pre_worker_handoff_reasons:
                finished_at = agentbridge.utc_now_iso()
                current_status_reason = self._format_status_reason(
                    "planner handoff required", pre_worker_handoff_reasons
                )
                verification_payload = self._pre_worker_handoff_verification_payload(
                    "planner and worker execution stayed fail-closed because live planner or worker prerequisites were not available."
                )
                write_dispatch_state(
                    dispatch_state_path,
                    self._dispatch_state_payload(
                        task=task,
                        worker_profile=worker_profile,
                        route_reason=route_reason,
                        run_id=run_id,
                        workspace_root=current_workspace_root,
                        status="waiting_handoff",
                        status_reason=current_status_reason,
                        next_action=PRE_WORKER_HANDOFF_NEXT_ACTION,
                        cleanup_status=current_cleanup_status,
                        cleanup_owner=current_cleanup_owner,
                        started_at=started_at,
                        updated_at=finished_at,
                        heartbeat_at=finished_at,
                        stale_after=lease_expires_at,
                    ),
                )
                worker_result = WorkerResult(
                    final_response=None,
                    raw_result={"kind": "planner_handoff"},
                    stdout_text="",
                    stderr_text="",
                )
                result_bundle = write_result_bundle(
                    layout=self._config.layout,
                    task=task,
                    run_id=run_id,
                    attempt=self._config.attempt,
                    worker_profile=worker_profile,
                    worker_result=worker_result,
                    started_at=started_at,
                    finished_at=finished_at,
                    verification_payload=verification_payload,
                    projection_writer=(
                        lambda artifacts: self._write_compatibility_projection(
                            task=task,
                            worker_profile=worker_profile,
                            worker_result=worker_result,
                            artifacts=artifacts,
                            status="waiting_handoff",
                            handoff_required=True,
                            next_action=PRE_WORKER_HANDOFF_NEXT_ACTION,
                            emit_worker_artifact=False,
                            extra_observations=[
                                "- Pre-worker handoff was derived from repo-side capability, planner-adapter, or quota gates.",
                                "- Repo-side runtime stopped before any live planner or primary worker execution.",
                            ],
                        )
                    ),
                    route_reason=route_reason,
                    result_status="waiting_handoff",
                    termination_reason="planner_handoff_required",
                    handoff_required=True,
                    next_action=PRE_WORKER_HANDOFF_NEXT_ACTION,
                    cost_payload_override=self._planner_handoff_cost_payload(),
                    cleanup_status=current_cleanup_status,
                    cleanup_owner=current_cleanup_owner,
                    status_reason=current_status_reason,
                )
                relative_result_path = self._relative_to_repo(result_bundle.artifacts.result_json)
                handoff_receipt_payload = self._build_handoff_receipt_payload(
                    task=task,
                    worker_profile=worker_profile,
                    route_reason=route_reason,
                    run_id=run_id,
                    status_reason=current_status_reason,
                    pre_worker_handoff_reasons=pre_worker_handoff_reasons,
                    result_ref=relative_result_path,
                    dispatch_state_ref=relative_dispatch_state_path,
                    verification_summary_ref=self._relative_to_repo(
                        result_bundle.artifacts.verification_summary
                    ),
                    next_action=PRE_WORKER_HANDOFF_NEXT_ACTION,
                )
                validate_handoff_receipt_payload(handoff_receipt_payload)
                write_handoff_receipt_artifact(
                    result_bundle.artifacts,
                    handoff_receipt_payload,
                )
                handoff_receipt_ref = self._relative_to_repo(
                    result_bundle.artifacts.handoff_receipt
                )
                closeout_bundle_payload = self._build_closeout_bundle_payload(
                    task=task,
                    artifacts=result_bundle.artifacts,
                    result_payload=result_bundle.result_payload,
                    verification_payload=verification_payload,
                    handoff_receipt_ref=handoff_receipt_ref,
                    planner_result_ref=None,
                    review_result_ref=None,
                    current_next_action=PRE_WORKER_HANDOFF_NEXT_ACTION,
                    cleanup_status=current_cleanup_status,
                    cleanup_owner=current_cleanup_owner,
                )
                write_closeout_bundle_artifact(result_bundle.artifacts, closeout_bundle_payload)
                closeout_bundle_ref = self._relative_to_repo(result_bundle.artifacts.closeout_bundle)
                result_payload = update_result_metadata(
                    result_bundle.artifacts.result_json,
                    handoff_receipt_ref=handoff_receipt_ref,
                    closeout_bundle_ref=closeout_bundle_ref,
                )
                projection_path = result_payload.get("compatibility_projection_ref")
                evidence_index_path = str(
                    result_bundle.artifacts.evidence_index.relative_to(self._config.layout.repo_root)
                ).replace("\\", "/")
                update_dispatch_state(
                    dispatch_state_path,
                    last_result_ref=relative_result_path,
                    verification_summary_ref=self._relative_to_repo(result_bundle.artifacts.verification_summary),
                    evidence_index_ref=evidence_index_path,
                    handoff_receipt_ref=handoff_receipt_ref,
                    planner_result_ref=None,
                    review_result_ref=None,
                    closeout_bundle_ref=closeout_bundle_ref,
                )
                refresh_evidence_index(
                    layout=self._config.layout,
                    artifacts=result_bundle.artifacts,
                    task_id=task.task_id,
                    run_id=run_id,
                )
                db.upsert_runtime_task(
                    self._config.layout.control_plane_db,
                    task_id=task.task_id,
                    run_id=run_id,
                    attempt=self._config.attempt,
                    state="waiting_handoff",
                    state_reason=current_status_reason,
                    execution_lane=worker_profile.lane,
                    worker_profile=worker_profile.name,
                    next_action=PRE_WORKER_HANDOFF_NEXT_ACTION,
                    cleanup_status=current_cleanup_status,
                    cleanup_owner=current_cleanup_owner,
                    created_at=started_at,
                    updated_at=finished_at,
                    result_path=relative_result_path,
                    dispatch_state_path=relative_dispatch_state_path,
                )
                db.append_event(
                    self._config.layout.control_plane_db,
                    task_id=task.task_id,
                    event_type="task_waiting_handoff",
                    payload={
                        "result_path": relative_result_path,
                        "compatibility_projection_ref": projection_path,
                        "evidence_index_ref": evidence_index_path,
                        "handoff_receipt_ref": handoff_receipt_ref,
                        "handoff_required": True,
                        "next_action": PRE_WORKER_HANDOFF_NEXT_ACTION,
                        "route_reason": route_reason,
                        "status_reason": current_status_reason,
                    },
                    created_at=finished_at,
                )
                return result_bundle.artifacts.result_json

            if planner_reasons:
                finished_at = agentbridge.utc_now_iso()
                planner_result = self._run_planner_sidecar(
                    task=task,
                    worker_profile=worker_profile,
                    workspace_root=current_workspace_root,
                    planner_reasons=planner_reasons,
                )
                current_next_action = self._planner_next_action(planner_result)
                current_status_reason = self._planner_status_reason(
                    planner_reasons=planner_reasons,
                    planner_result=planner_result,
                )
                verification_payload = self._planner_sidecar_verification_payload(planner_result)
                write_dispatch_state(
                    dispatch_state_path,
                    self._dispatch_state_payload(
                        task=task,
                        worker_profile=worker_profile,
                        route_reason=route_reason,
                        run_id=run_id,
                        workspace_root=current_workspace_root,
                        status="waiting_handoff",
                        status_reason=current_status_reason,
                        next_action=current_next_action,
                        cleanup_status=current_cleanup_status,
                        cleanup_owner=current_cleanup_owner,
                        started_at=started_at,
                        updated_at=finished_at,
                        heartbeat_at=finished_at,
                        stale_after=lease_expires_at,
                    ),
                )
                handoff_worker_result = WorkerResult(
                    final_response=None,
                    raw_result={
                        "kind": "planner_sidecar",
                        "disposition": planner_result.disposition,
                    },
                    usage=planner_result.usage,
                    stdout_text="",
                    stderr_text="",
                )
                result_bundle = write_result_bundle(
                    layout=self._config.layout,
                    task=task,
                    run_id=run_id,
                    attempt=self._config.attempt,
                    worker_profile=worker_profile,
                    worker_result=handoff_worker_result,
                    started_at=started_at,
                    finished_at=finished_at,
                    verification_payload=verification_payload,
                    projection_writer=(
                        lambda artifacts: self._write_compatibility_projection(
                            task=task,
                            worker_profile=worker_profile,
                            worker_result=handoff_worker_result,
                            artifacts=artifacts,
                            status="waiting_handoff",
                            handoff_required=True,
                            next_action=current_next_action,
                            emit_worker_artifact=False,
                            extra_observations=self._planner_projection_observations(planner_result),
                        )
                    ),
                    route_reason=route_reason,
                    result_status="waiting_handoff",
                    termination_reason="planner_sidecar_result_recorded",
                    handoff_required=True,
                    next_action=current_next_action,
                    cleanup_status=current_cleanup_status,
                    cleanup_owner=current_cleanup_owner,
                    status_reason=current_status_reason,
                )
                planner_result_payload = self._build_planner_result_payload(
                    task=task,
                    worker_profile=worker_profile,
                    artifacts=result_bundle.artifacts,
                    planner_result=planner_result,
                )
                write_planner_result_artifact(result_bundle.artifacts, planner_result_payload)
                planner_result_ref = self._relative_to_repo(result_bundle.artifacts.planner_result)
                closeout_bundle_payload = self._build_closeout_bundle_payload(
                    task=task,
                    artifacts=result_bundle.artifacts,
                    result_payload=result_bundle.result_payload,
                    verification_payload=verification_payload,
                    handoff_receipt_ref=None,
                    planner_result_ref=planner_result_ref,
                    review_result_ref=None,
                    current_next_action=current_next_action,
                    cleanup_status=current_cleanup_status,
                    cleanup_owner=current_cleanup_owner,
                )
                write_closeout_bundle_artifact(result_bundle.artifacts, closeout_bundle_payload)
                closeout_bundle_ref = self._relative_to_repo(result_bundle.artifacts.closeout_bundle)
                result_payload = update_result_metadata(
                    result_bundle.artifacts.result_json,
                    planner_result_ref=planner_result_ref,
                    closeout_bundle_ref=closeout_bundle_ref,
                )
                relative_result_path = str(
                    result_bundle.artifacts.result_json.relative_to(self._config.layout.repo_root)
                ).replace("\\", "/")
                projection_path = result_payload.get("compatibility_projection_ref")
                evidence_index_path = str(
                    result_bundle.artifacts.evidence_index.relative_to(self._config.layout.repo_root)
                ).replace("\\", "/")
                update_dispatch_state(
                    dispatch_state_path,
                    last_result_ref=relative_result_path,
                    verification_summary_ref=self._relative_to_repo(result_bundle.artifacts.verification_summary),
                    evidence_index_ref=evidence_index_path,
                    planner_result_ref=planner_result_ref,
                    review_result_ref=None,
                    closeout_bundle_ref=closeout_bundle_ref,
                )
                refresh_evidence_index(
                    layout=self._config.layout,
                    artifacts=result_bundle.artifacts,
                    task_id=task.task_id,
                    run_id=run_id,
                )
                db.upsert_runtime_task(
                    self._config.layout.control_plane_db,
                    task_id=task.task_id,
                    run_id=run_id,
                    attempt=self._config.attempt,
                    state="waiting_handoff",
                    state_reason=current_status_reason,
                    execution_lane=worker_profile.lane,
                    worker_profile=worker_profile.name,
                    next_action=current_next_action,
                    cleanup_status=current_cleanup_status,
                    cleanup_owner=current_cleanup_owner,
                    created_at=started_at,
                    updated_at=finished_at,
                    result_path=relative_result_path,
                    dispatch_state_path=relative_dispatch_state_path,
                )
                db.append_event(
                    self._config.layout.control_plane_db,
                    task_id=task.task_id,
                    event_type="planner_completed",
                    payload={
                        "planner_result_ref": planner_result_ref,
                        "disposition": planner_result.disposition,
                        "next_action": current_next_action,
                        "route_reason": route_reason,
                    },
                    created_at=finished_at,
                )
                db.append_event(
                    self._config.layout.control_plane_db,
                    task_id=task.task_id,
                    event_type="task_waiting_handoff",
                    payload={
                        "result_path": relative_result_path,
                        "compatibility_projection_ref": projection_path,
                        "evidence_index_ref": evidence_index_path,
                        "planner_result_ref": planner_result_ref,
                        "handoff_required": True,
                        "next_action": current_next_action,
                        "route_reason": route_reason,
                        "status_reason": current_status_reason,
                    },
                    created_at=finished_at,
                )
                return result_bundle.artifacts.result_json

            prepared_workspace = prepare_task_workspace(
                task=task,
                layout=self._config.layout,
                workspace_root=self._config.workspace_root,
            )
            guarded_workspace_root = prepared_workspace.workspace_root
            current_workspace_root = guarded_workspace_root
            current_cleanup_status = prepared_workspace.cleanup_status
            current_cleanup_owner = (
                "runtime" if prepared_workspace.managed_by_runtime else current_cleanup_owner
            )
            if task.worktree_path.strip() not in {".", "./"}:
                db.append_event(
                    self._config.layout.control_plane_db,
                    task_id=task.task_id,
                    event_type="worktree_prepared",
                    payload={
                        "workspace_root": str(guarded_workspace_root),
                        "branch_name": task.branch_name,
                        "worktree_path": task.worktree_path,
                        "created_new_worktree": prepared_workspace.created_new_worktree,
                        "managed_by_runtime": prepared_workspace.managed_by_runtime,
                        "cleanup_status": current_cleanup_status,
                    },
                    created_at=agentbridge.utc_now_iso(),
                )
            baseline_changes = capture_workspace_change_set(guarded_workspace_root)
            request = WorkerRequest(
                prompt=task.render_worker_prompt(),
                cwd=guarded_workspace_root,
                model=worker_profile.model,
                sandbox=worker_profile.sandbox(),
                approval_mode=worker_profile.approval_mode(),
            )
            worker = self._resolve_worker(worker_profile)
            worker_result = worker.run(request)
            enforce_workspace_change_policy(
                task=task,
                workspace_root=guarded_workspace_root,
                baseline_changes=baseline_changes,
            )
            verification_payload = run_verification(
                task=task,
                workspace_root=guarded_workspace_root,
            )
            review_reasons = []
            if verification_payload.get("status") != "failed":
                review_reasons = self._review_gate_reasons(task)
            review_required = bool(review_reasons)
            result_status = "needs_review" if review_required else (
                "failed" if verification_payload.get("status") == "failed" else "succeeded"
            )
            termination_reason = (
                "review_required_before_downstream"
                if review_required
                else (
                    "verification_failed"
                    if verification_payload.get("status") == "failed"
                    else "worker_completed"
                )
            )
            current_next_action = (
                REVIEW_HANDOFF_NEXT_ACTION
                if review_required
                else ("inspect_verification_failure" if verification_payload.get("status") == "failed" else "none")
            )
            current_status_reason = (
                self._format_status_reason("review required", review_reasons)
                if review_required
                else (
                    "verification failed during graded autonomy execution"
                    if verification_payload.get("status") == "failed"
                    else "task completed within graded autonomy boundary"
                )
            )
            if task.worktree_path.strip() not in {".", "./"}:
                cleanup_outcome = finalize_task_workspace_cleanup(
                    task=task,
                    repo_root=self._config.layout.repo_root,
                    prepared_workspace=prepared_workspace,
                    result_status=result_status,
                    handoff_required=review_required,
                    current_next_action=current_next_action,
                )
                current_cleanup_status = cleanup_outcome.cleanup_status
                current_cleanup_owner = cleanup_outcome.cleanup_owner
                if cleanup_outcome.next_action is not None:
                    current_next_action = cleanup_outcome.next_action
                db.append_event(
                    self._config.layout.control_plane_db,
                    task_id=task.task_id,
                    event_type="worktree_cleanup",
                    payload=cleanup_outcome.payload,
                    created_at=agentbridge.utc_now_iso(),
                )
            finished_at = agentbridge.utc_now_iso()
            write_dispatch_state(
                dispatch_state_path,
                self._dispatch_state_payload(
                    task=task,
                    worker_profile=worker_profile,
                    route_reason=route_reason,
                    run_id=run_id,
                    workspace_root=current_workspace_root,
                    status="needs_review" if review_required else (
                        "failed" if verification_payload.get("status") == "failed" else "completed"
                    ),
                    status_reason=current_status_reason,
                    next_action=current_next_action,
                    cleanup_status=current_cleanup_status,
                    cleanup_owner=current_cleanup_owner,
                    started_at=started_at,
                    updated_at=finished_at,
                    heartbeat_at=finished_at,
                    stale_after=lease_expires_at,
                ),
            )
            result_bundle = write_result_bundle(
                layout=self._config.layout,
                task=task,
                run_id=run_id,
                attempt=self._config.attempt,
                worker_profile=worker_profile,
                worker_result=worker_result,
                started_at=started_at,
                finished_at=finished_at,
                verification_payload=verification_payload,
                projection_writer=(
                    lambda artifacts: self._write_compatibility_projection(
                        task=task,
                        worker_profile=worker_profile,
                        worker_result=worker_result,
                        artifacts=artifacts,
                        status="needs_review" if review_required else "succeeded",
                        human_review_required=review_required,
                        handoff_required=review_required,
                        next_action=REVIEW_HANDOFF_NEXT_ACTION if review_required else "none",
                        extra_observations=(
                            [
                                "- Review gate was derived from repo-side risk/write/policy predicates.",
                                "- Repo-side runtime produced formal result artifacts but stopped before downstream flow.",
                            ]
                            if review_required
                            else None
                        ),
                    )
                ),
                route_reason=route_reason,
                result_status="needs_review" if review_required else None,
                termination_reason=termination_reason if review_required or verification_payload.get("status") == "failed" else None,
                handoff_required=review_required,
                next_action=current_next_action,
                cleanup_status=current_cleanup_status,
                cleanup_owner=current_cleanup_owner,
                status_reason=current_status_reason,
            )
            review_result_ref: str | None = None
            if review_required:
                review_result_payload = self._materialize_review_result_payload(
                    task=task,
                    primary_worker_profile=worker_profile,
                    artifacts=result_bundle.artifacts,
                    review_reasons=review_reasons,
                    result_payload=result_bundle.result_payload,
                    verification_payload=verification_payload,
                )
                write_review_result_artifact(result_bundle.artifacts, review_result_payload)
                review_result_ref = self._relative_to_repo(result_bundle.artifacts.review_result)

            closeout_bundle_payload = self._build_closeout_bundle_payload(
                task=task,
                artifacts=result_bundle.artifacts,
                result_payload=result_bundle.result_payload,
                verification_payload=verification_payload,
                handoff_receipt_ref=None,
                planner_result_ref=None,
                review_result_ref=review_result_ref,
                current_next_action=current_next_action,
                cleanup_status=current_cleanup_status,
                cleanup_owner=current_cleanup_owner,
            )
            write_closeout_bundle_artifact(result_bundle.artifacts, closeout_bundle_payload)
            closeout_bundle_ref = self._relative_to_repo(result_bundle.artifacts.closeout_bundle)
            result_payload = update_result_metadata(
                result_bundle.artifacts.result_json,
                review_result_ref=review_result_ref,
                closeout_bundle_ref=closeout_bundle_ref,
            )
            relative_result_path = str(
                result_bundle.artifacts.result_json.relative_to(self._config.layout.repo_root)
            ).replace("\\", "/")
            update_dispatch_state(
                dispatch_state_path,
                last_result_ref=relative_result_path,
                verification_summary_ref=self._relative_to_repo(result_bundle.artifacts.verification_summary),
                evidence_index_ref=self._relative_to_repo(result_bundle.artifacts.evidence_index),
                review_result_ref=review_result_ref,
                closeout_bundle_ref=closeout_bundle_ref,
            )
            refresh_evidence_index(
                layout=self._config.layout,
                artifacts=result_bundle.artifacts,
                task_id=task.task_id,
                run_id=run_id,
            )
            projection_path = result_payload.get("compatibility_projection_ref")
            evidence_index_path = str(
                result_bundle.artifacts.evidence_index.relative_to(self._config.layout.repo_root)
            ).replace("\\", "/")
            runtime_state = "needs_review" if review_required else (
                "failed" if verification_payload.get("status") == "failed" else "completed"
            )
            completion_event_type = (
                "task_needs_review"
                if review_required
                else ("task_failed" if verification_payload.get("status") == "failed" else "task_completed")
            )
            db.upsert_runtime_task(
                self._config.layout.control_plane_db,
                task_id=task.task_id,
                run_id=run_id,
                attempt=self._config.attempt,
                state=runtime_state,
                state_reason=current_status_reason,
                execution_lane=worker_profile.lane,
                worker_profile=worker_profile.name,
                next_action=current_next_action,
                cleanup_status=current_cleanup_status,
                cleanup_owner=current_cleanup_owner,
                created_at=started_at,
                updated_at=finished_at,
                result_path=relative_result_path,
                dispatch_state_path=relative_dispatch_state_path,
            )
            db.append_event(
                self._config.layout.control_plane_db,
                task_id=task.task_id,
                event_type=completion_event_type,
                payload={
                    "result_path": relative_result_path,
                    "compatibility_projection_ref": projection_path,
                    "evidence_index_ref": evidence_index_path,
                    "usage": self._usage_payload(worker_result.usage),
                    "handoff_required": review_required,
                    "next_action": current_next_action,
                    "route_reason": route_reason,
                    "status_reason": current_status_reason,
                },
                created_at=finished_at,
            )
            return result_bundle.artifacts.result_json
        except Exception as exc:
            failed_at = agentbridge.utc_now_iso()
            current_status_reason = str(exc)
            write_dispatch_state(
                dispatch_state_path,
                self._dispatch_state_payload(
                    task=task,
                    worker_profile=worker_profile,
                    route_reason=route_reason,
                    run_id=run_id,
                    workspace_root=current_workspace_root,
                    status="failed",
                    status_reason=current_status_reason,
                    next_action="inspect_failure_and_retry",
                    cleanup_status=current_cleanup_status,
                    cleanup_owner=current_cleanup_owner,
                    started_at=started_at,
                    updated_at=failed_at,
                    heartbeat_at=failed_at,
                    stale_after=lease_expires_at,
                ),
            )
            db.upsert_runtime_task(
                self._config.layout.control_plane_db,
                task_id=task.task_id,
                run_id=run_id,
                attempt=self._config.attempt,
                state="failed",
                state_reason=current_status_reason,
                execution_lane=worker_profile.lane,
                worker_profile=worker_profile.name,
                next_action="inspect_failure_and_retry",
                cleanup_status=current_cleanup_status,
                cleanup_owner=current_cleanup_owner,
                created_at=started_at,
                updated_at=failed_at,
                dispatch_state_path=relative_dispatch_state_path,
            )
            db.append_event(
                self._config.layout.control_plane_db,
                task_id=task.task_id,
                event_type="task_failed",
                payload={
                    "worker_id": self._config.worker_id,
                    "worker_profile": worker_profile.name,
                    "lane": worker_profile.lane,
                    "run_id": run_id,
                    "attempt": self._config.attempt,
                    "lease_token": lease_token,
                    "route_reason": route_reason,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "status_reason": current_status_reason,
                },
                created_at=failed_at,
            )
            raise
        finally:
            finished_at = agentbridge.utc_now_iso()
            db.release_lease(
                self._config.layout.control_plane_db,
                lease_token=lease_token,
            )
            db.upsert_worker(
                self._config.layout.control_plane_db,
                worker_id=self._config.worker_id,
                lane=worker_profile.lane,
                status="idle",
                heartbeat_at=finished_at,
            )

    def _load_intake_task(self, task_path: Path) -> CanonicalTask:
        if task_path.suffix.lower() != ".md":
            return load_task(task_path)

        projection = agentbridge.load_markdown_task(task_path)
        payload = agentbridge.markdown_task_to_canonical_payload(
            projection,
            repo_root=self._config.layout.repo_root,
        )
        return task_from_payload(task_path, payload)

    def _write_compatibility_projection(
        self,
        *,
        task: CanonicalTask,
        worker_profile: WorkerProfile,
        worker_result: object,
        artifacts: object,
        status: str = "succeeded",
        human_review_required: bool = False,
        handoff_required: bool = False,
        next_action: str = "none",
        emit_worker_artifact: bool = True,
        extra_observations: list[str] | None = None,
    ) -> Path | None:
        if self._config.agentbridge_root is None:
            return None
        if not self._runtime_config.orchestrator.projection_required:
            return None
        if worker_profile.projection_mode != "compatibility_dual_write":
            return None

        if not isinstance(worker_result, object) or not hasattr(artifacts, "worker_output"):
            return None

        compatibility_root = self._config.agentbridge_root
        compatibility_root.mkdir(parents=True, exist_ok=True)
        (compatibility_root / "results").mkdir(parents=True, exist_ok=True)
        (compatibility_root / "artifacts").mkdir(parents=True, exist_ok=True)

        final_response = getattr(worker_result, "final_response", None)
        artifact = None
        if emit_worker_artifact:
            artifact = agentbridge.write_text_artifact(
                compatibility_root,
                task.task_id,
                final_response or "",
            )
        observations = [
            "- Markdown result remains a compatibility projection from canonical runtime output.",
            "- The formal runtime truth lives under `.ai/runs/<run_id>/<task_id>/result.json`.",
        ]
        if emit_worker_artifact:
            observations.extend(self._build_usage_observations(getattr(worker_result, "usage", None)))
        if extra_observations:
            observations.extend(extra_observations)
        return agentbridge.write_result_projection(
            agentbridge_root=compatibility_root,
            task_id=task.task_id,
            status=status,
            model=worker_profile.model,
            provider=worker_profile.provider,
            worker_id=self._config.worker_id,
            lane=worker_profile.lane,
            sandbox_mode=worker_profile.sandbox_profile,
            network_mode=worker_profile.network_profile,
            final_response=final_response if emit_worker_artifact else None,
            artifact=artifact,
            failures=[],
            observations=observations,
            human_review_required=human_review_required,
            handoff_required=handoff_required,
            next_action=next_action,
        )

    @staticmethod
    def _pre_worker_handoff_verification_payload(reason: str) -> dict[str, Any]:
        return {
            "status": "waiting_handoff",
            "commands_run": [],
            "reason": reason,
        }

    @staticmethod
    def _planner_handoff_cost_payload() -> dict[str, Any]:
        return {
            "mode": "token_only",
            "source": "planner_handoff_no_worker_usage",
            "currency": None,
            "estimated_cost": None,
            "usage": None,
        }

    def _planner_sidecar_verification_payload(
        self,
        planner_result: PlannerSidecarDecision,
    ) -> dict[str, Any]:
        return {
            "status": "waiting_handoff",
            "commands_run": [],
            "reason": planner_result.reason_summary,
            "planner_disposition": planner_result.disposition,
            "planner_blocking_reasons": list(planner_result.blocking_reasons),
        }

    def _build_planner_result_payload(
        self,
        *,
        task: CanonicalTask,
        worker_profile: WorkerProfile,
        artifacts: Any,
        planner_result: PlannerSidecarDecision,
    ) -> dict[str, Any]:
        return {
            "task_id": task.task_id,
            "planner_kind": worker_profile.worker_kind,
            "planner_mode": "blocking",
            "planner_profile": worker_profile.name,
            "model": worker_profile.model,
            "risk": task.risk_level,
            "disposition": planner_result.disposition,
            "reason_summary": planner_result.reason_summary,
            "blocking_reasons": list(planner_result.blocking_reasons),
            "plan_outline": list(planner_result.plan_outline),
            "source_evidence_refs": [
                self._relative_to_repo(artifacts.result_json),
                self._relative_to_repo(artifacts.dispatch_state),
                self._relative_to_repo(artifacts.verification_summary),
                self._relative_to_repo(artifacts.cost_summary),
            ],
        }

    def _planner_next_action(self, planner_result: PlannerSidecarDecision) -> str:
        if planner_result.disposition == "proceed":
            return PLANNER_RECEIPT_NEXT_ACTION
        return PLANNER_OPERATOR_HANDOFF_NEXT_ACTION

    def _planner_status_reason(
        self,
        *,
        planner_reasons: list[str],
        planner_result: PlannerSidecarDecision,
    ) -> str:
        reasons = list(planner_reasons)
        if planner_result.disposition == "proceed":
            reasons.append("planner_disposition=proceed")
        else:
            reasons.extend(planner_result.blocking_reasons)
        return self._format_status_reason(planner_result.reason_summary, reasons)

    def _planner_projection_observations(
        self,
        planner_result: PlannerSidecarDecision,
    ) -> list[str]:
        observations = [
            "- Live planner sidecar ran inside the current repo-owned host_local boundary.",
            "- Runtime still stopped before primary worker execution; this slice does not yet auto-continue from planner into worker.",
        ]
        if planner_result.disposition == "proceed":
            observations.append("- Planner disposition was proceed; the next worker step still requires an explicit follow-up action.")
        else:
            observations.append("- Planner disposition was handoff; operator follow-up is required before any worker execution.")
        return observations

    def _run_planner_sidecar(
        self,
        *,
        task: CanonicalTask,
        worker_profile: WorkerProfile,
        workspace_root: Path,
        planner_reasons: list[str],
    ) -> PlannerSidecarDecision:
        request = WorkerRequest(
            prompt=self._planner_prompt(task=task, planner_reasons=planner_reasons),
            cwd=workspace_root,
            model=worker_profile.model,
            sandbox=Sandbox.read_only,
            approval_mode=worker_profile.approval_mode(),
        )
        worker = self._resolve_worker(worker_profile)
        worker_result = worker.run(request)
        return self._parse_planner_response(
            response_text=worker_result.final_response,
            usage=worker_result.usage,
        )

    def _parse_planner_response(
        self,
        *,
        response_text: str | None,
        usage: WorkerUsage | None,
    ) -> PlannerSidecarDecision:
        normalized_text = (response_text or "").strip()
        if not normalized_text:
            return PlannerSidecarDecision(
                disposition="handoff",
                reason_summary="Planner sidecar returned no JSON output and the runtime stayed fail-closed.",
                blocking_reasons=("planner_output_missing",),
                plan_outline=("Inspect or rerun the planner sidecar before attempting worker execution.",),
                usage=usage,
            )

        try:
            payload = json.loads(self._strip_markdown_json_fence(normalized_text))
        except json.JSONDecodeError:
            return PlannerSidecarDecision(
                disposition="handoff",
                reason_summary="Planner sidecar returned non-parseable JSON and the runtime stayed fail-closed.",
                blocking_reasons=("planner_output_unparseable",),
                plan_outline=("Repair the planner response contract before attempting worker execution.",),
                usage=usage,
            )

        if not isinstance(payload, dict):
            return PlannerSidecarDecision(
                disposition="handoff",
                reason_summary="Planner sidecar returned a non-object payload and the runtime stayed fail-closed.",
                blocking_reasons=("planner_output_not_object",),
                plan_outline=("Return a top-level JSON object from the planner sidecar.",),
                usage=usage,
            )

        disposition = str(payload.get("disposition") or "").strip()
        if disposition not in {"proceed", "handoff"}:
            return PlannerSidecarDecision(
                disposition="handoff",
                reason_summary="Planner sidecar omitted a supported disposition and the runtime stayed fail-closed.",
                blocking_reasons=("planner_disposition_invalid",),
                plan_outline=("Return disposition=proceed or disposition=handoff from the planner sidecar.",),
                usage=usage,
            )

        reason_summary = str(payload.get("reason_summary") or "").strip()
        if not reason_summary:
            reason_summary = (
                "Planner sidecar recorded a proceed disposition and kept the run at the worker boundary."
                if disposition == "proceed"
                else "Planner sidecar requested operator handoff before worker execution."
            )

        blocking_reasons = tuple(
            item.strip()
            for item in payload.get("blocking_reasons", [])
            if isinstance(item, str) and item.strip()
        )
        if disposition == "handoff" and not blocking_reasons:
            blocking_reasons = ("planner_requested_handoff",)

        plan_outline = tuple(
            item.strip()
            for item in payload.get("plan_outline", [])
            if isinstance(item, str) and item.strip()
        )
        if not plan_outline:
            plan_outline = (reason_summary,)

        return PlannerSidecarDecision(
            disposition=disposition,
            reason_summary=reason_summary,
            blocking_reasons=blocking_reasons,
            plan_outline=plan_outline,
            usage=usage,
        )

    @staticmethod
    def _strip_markdown_json_fence(text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```") and stripped.endswith("```"):
            lines = stripped.splitlines()
            if len(lines) >= 3:
                return "\n".join(lines[1:-1]).strip()
        return stripped

    def _planner_prompt(
        self,
        *,
        task: CanonicalTask,
        planner_reasons: list[str],
    ) -> str:
        prompt_payload = {
            "task_id": task.task_id,
            "title": task.title,
            "risk_level": task.risk_level,
            "merge_policy": task.merge_policy,
            "execution_lane": task.execution_lane,
            "allowed_paths": list(task.allowed_paths),
            "forbidden_paths": list(task.forbidden_paths),
            "depends_on": list(task.depends_on),
            "planner_reasons": list(planner_reasons),
            "write_access": task.write_access,
            "requires_network": task.requires_network,
            "requires_gui": task.requires_gui,
            "verification_commands": {
                "build": task.verification_commands.build,
                "test": task.verification_commands.test,
                "lint": task.verification_commands.lint,
                "typecheck": task.verification_commands.typecheck,
                "contract": task.verification_commands.contract,
                "hotspot": task.verification_commands.hotspot,
            },
            "description": task.description,
        }
        return "\n".join(
            [
                "You are the repo-owned planner sidecar for Local AI Runtime.",
                "Stay inside the current repo-owned host_local boundary.",
                "Do not claim that live review, non-host-local runners, or live accepted status already exist.",
                "Return JSON only with this shape:",
                '{',
                '  "disposition": "proceed" | "handoff",',
                '  "reason_summary": "short explanation",',
                '  "blocking_reasons": ["reason when handoff is required"],',
                '  "plan_outline": ["2-5 concise next steps"]',
                '}',
                "Choose handoff when the task should not continue automatically within the current repo-side boundary.",
                "Current canonical task context:",
                json.dumps(prompt_payload, ensure_ascii=False, indent=2),
            ]
        )

    def _build_review_result_payload(
        self,
        *,
        task: CanonicalTask,
        worker_profile: WorkerProfile,
        artifacts: Any,
        review_reasons: list[str],
    ) -> dict[str, Any]:
        return {
            "task_id": task.task_id,
            "reviewer_kind": "codex_review",
            "review_mode": "blocking",
            "model": "repo_policy_gate",
            "risk": task.risk_level,
            "findings": [
                {
                    "severity": task.risk_level,
                    "category": "review_gate",
                    "title": "Repo-side blocking review required before downstream use",
                    "detail": (
                        "The repo-side review gate derived blocking reasons before downstream use: "
                        + "; ".join(review_reasons)
                        + ". This receipt is repo-owned and does not imply that a live heterogeneous reviewer ran."
                    ),
                    "suggested_fix": "Produce a downstream review decision or operator disposition before downstream use.",
                }
            ],
            "blocking_reasons": list(review_reasons),
            "missing_tests": [],
            "recommended_action": "revise",
            "source_evidence_refs": [
                self._relative_to_repo(artifacts.result_json),
                self._relative_to_repo(artifacts.dispatch_state),
                self._relative_to_repo(artifacts.verification_summary),
            ],
        }

    def _materialize_review_result_payload(
        self,
        *,
        task: CanonicalTask,
        primary_worker_profile: WorkerProfile,
        artifacts: Any,
        review_reasons: list[str],
        result_payload: dict[str, Any],
        verification_payload: dict[str, Any],
    ) -> dict[str, Any]:
        review_worker_profile = self._resolve_review_worker_profile()
        if review_worker_profile is None:
            return self._build_review_result_payload(
                task=task,
                worker_profile=primary_worker_profile,
                artifacts=artifacts,
                review_reasons=review_reasons,
            )

        review_worker = self._resolve_review_worker(review_worker_profile)
        if review_worker is None:
            return self._build_review_result_payload(
                task=task,
                worker_profile=primary_worker_profile,
                artifacts=artifacts,
                review_reasons=review_reasons,
            )

        worker_output_excerpt = self._review_target_excerpt(artifacts)
        if not worker_output_excerpt:
            fallback_payload = self._build_review_result_payload(
                task=task,
                worker_profile=primary_worker_profile,
                artifacts=artifacts,
                review_reasons=review_reasons + ["live_review_sidecar_missing_worker_output"],
            )
            fallback_payload["findings"][0]["detail"] += (
                " The live heterogeneous review sidecar requires a bounded primary worker output summary and the runtime fell back to the repo-side blocking receipt."
            )
            return fallback_payload

        try:
            with tempfile.TemporaryDirectory(prefix="local-ai-runtime-review-") as review_cwd:
                review_worker_result = review_worker.run(
                    WorkerRequest(
                        prompt=self._review_prompt(
                            task=task,
                            primary_worker_profile=primary_worker_profile,
                            review_worker_profile=review_worker_profile,
                            review_reasons=review_reasons,
                            result_payload=result_payload,
                            verification_payload=verification_payload,
                            worker_output_excerpt=worker_output_excerpt,
                        ),
                        cwd=Path(review_cwd),
                        model=review_worker_profile.model,
                        sandbox=review_worker_profile.sandbox(),
                        approval_mode=review_worker_profile.approval_mode(),
                    )
                )

            return self._build_live_review_result_payload(
                task=task,
                review_worker_profile=review_worker_profile,
                artifacts=artifacts,
                review_reasons=review_reasons,
                review_worker_result=review_worker_result,
            )
        except Exception as exc:
            fallback_payload = self._build_review_result_payload(
                task=task,
                worker_profile=primary_worker_profile,
                artifacts=artifacts,
                review_reasons=review_reasons + [f"live_review_sidecar_failed={type(exc).__name__}"],
            )
            fallback_payload["findings"][0]["detail"] += (
                " The live heterogeneous review sidecar did not materialize and the runtime fell back to the repo-side blocking receipt."
            )
            return fallback_payload

    def _build_live_review_result_payload(
        self,
        *,
        task: CanonicalTask,
        review_worker_profile: WorkerProfile,
        artifacts: Any,
        review_reasons: list[str],
        review_worker_result: WorkerResult,
    ) -> dict[str, Any]:
        payload = self._parse_review_sidecar_response(review_worker_result)
        reviewer_kind = str(payload.get("reviewer_kind") or "").strip() or "claude_glm"
        review_mode = str(payload.get("review_mode") or "").strip() or "blocking"
        recommended_action = str(payload.get("recommended_action") or "").strip() or "revise"
        findings = payload.get("findings")
        if not isinstance(findings, list):
            findings = []
        blocking_reasons = payload.get("blocking_reasons")
        if not isinstance(blocking_reasons, list):
            blocking_reasons = list(review_reasons)
        missing_tests = payload.get("missing_tests")
        if not isinstance(missing_tests, list):
            missing_tests = []
        summary = str(payload.get("summary") or "").strip()
        if summary:
            findings.append(
                {
                    "severity": task.risk_level,
                    "category": "review_summary",
                    "title": "Live heterogeneous review summary",
                    "detail": summary,
                    "suggested_fix": "Resolve the heterogeneous review findings before downstream use.",
                }
            )

        review_payload = {
            "task_id": task.task_id,
            "reviewer_kind": reviewer_kind,
            "review_mode": review_mode,
            "model": review_worker_profile.model,
            "risk": task.risk_level,
            "findings": findings,
            "blocking_reasons": [str(item) for item in blocking_reasons if isinstance(item, str)],
            "missing_tests": [str(item) for item in missing_tests if isinstance(item, str)],
            "recommended_action": recommended_action,
            "source_evidence_refs": [
                self._relative_to_repo(artifacts.result_json),
                self._relative_to_repo(artifacts.dispatch_state),
                self._relative_to_repo(artifacts.verification_summary),
                self._relative_to_repo(artifacts.cost_summary),
            ],
        }
        validate_review_result_payload(review_payload)
        return review_payload

    @staticmethod
    def _parse_review_sidecar_response(
        review_worker_result: WorkerResult,
    ) -> dict[str, Any]:
        text = (review_worker_result.final_response or "").strip()
        if not text:
            raise RuntimeError("review sidecar returned no structured output")
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise RuntimeError("review sidecar returned a non-object payload")
        return payload

    def _review_prompt(
        self,
        *,
        task: CanonicalTask,
        primary_worker_profile: WorkerProfile,
        review_worker_profile: WorkerProfile,
        review_reasons: list[str],
        result_payload: dict[str, Any],
        verification_payload: dict[str, Any],
        worker_output_excerpt: str,
    ) -> str:
        verification_gates = "; ".join(
            f"{entry.get('gate')}={entry.get('status')}"
            for entry in verification_payload.get("commands_run", [])
            if isinstance(entry, dict)
        )
        review_reasons_text = ", ".join(review_reasons) if review_reasons else "none"
        verification_gates_text = verification_gates or "none"
        status_text = (
            f"worker_status={result_payload.get('status')}; "
            f"termination_reason={result_payload.get('termination_reason')}; "
            f"next_action={result_payload.get('next_action')}; "
            f"verification_status={verification_payload.get('status')}; "
            f"verification_gates={verification_gates_text}"
        )
        return " ".join(
            [
                "Return a blocking review receipt for this bounded runtime slice.",
                (
                    f"Use reviewer_kind {review_worker_profile.worker_kind}, one {task.risk_level} "
                    "heterogeneous_review finding, blocking_reasons "
                    f"{review_reasons_text}, missing_tests empty, recommended_action revise, and a short summary."
                ),
                (
                    f"Runtime status: {status_text}. Primary worker profile={primary_worker_profile.name}; "
                    f"review worker profile={review_worker_profile.name}."
                ),
                f"Review target summary: {worker_output_excerpt}",
                "Base the finding only on the provided runtime status and review target summary. Do not invent unrelated files, services, or requirements.",
                "Do not ask questions.",
            ]
        )

    @staticmethod
    def _review_target_excerpt(
        artifacts: Any,
        *,
        max_chars: int = 1200,
    ) -> str:
        worker_output_path = getattr(artifacts, "worker_output", None)
        if not isinstance(worker_output_path, Path) or not worker_output_path.exists():
            return ""
        text = worker_output_path.read_text(encoding="utf-8").strip()
        if not text:
            return ""
        normalized = " ".join(text.split())
        if len(normalized) <= max_chars:
            return normalized
        return normalized[: max_chars - 3].rstrip() + "..."

    def _build_handoff_receipt_payload(
        self,
        *,
        task: CanonicalTask,
        worker_profile: WorkerProfile,
        route_reason: str,
        run_id: str,
        status_reason: str,
        pre_worker_handoff_reasons: list[str],
        result_ref: str,
        dispatch_state_ref: str,
        verification_summary_ref: str,
        next_action: str,
    ) -> dict[str, Any]:
        return {
            "task_id": task.task_id,
            "run_id": run_id,
            "receipt_kind": "pre_worker_handoff",
            "status": "waiting_handoff",
            "handoff_required": True,
            "reason_codes": self._handoff_reason_codes(pre_worker_handoff_reasons),
            "reason_details": list(pre_worker_handoff_reasons),
            "source_runtime": "host_local",
            "requested_execution_lane": task.execution_lane,
            "selected_lane": worker_profile.lane,
            "worker_profile": worker_profile.name,
            "worker_kind": worker_profile.worker_kind,
            "route_reason": route_reason,
            "status_reason": status_reason,
            "worker_execution_attempted": False,
            "requested_lane_runner_wired": task.execution_lane == "host_local",
            "selected_profile_runner_wired": worker_profile.lane == "host_local",
            "next_action": next_action,
            "source_evidence_refs": [
                result_ref,
                dispatch_state_ref,
                verification_summary_ref,
            ],
        }

    @staticmethod
    def _handoff_reason_codes(reasons: list[str]) -> list[str]:
        codes: list[str] = []
        for reason in reasons:
            if "runner_not_wired" in reason and "selected_lane=" in reason:
                codes.append("selected_lane_runner_not_wired")
            elif reason.startswith("execution_lane="):
                codes.append("execution_lane_profile_mismatch")
            elif reason == "requires_network=true":
                codes.append("requires_network_with_offline_profile")
            elif reason == "requires_gui=true":
                codes.append("requires_gui_boundary")
            elif reason.startswith("lease_quota_exhausted"):
                codes.append("lease_quota_exhausted")
            elif reason.startswith("planner_sidecar_not_wired"):
                codes.append("planner_sidecar_not_wired")
            else:
                codes.append("pre_worker_handoff")
        return codes

    def _build_closeout_bundle_payload(
        self,
        *,
        task: CanonicalTask,
        artifacts: Any,
        result_payload: dict[str, Any],
        verification_payload: dict[str, Any],
        handoff_receipt_ref: str | None,
        planner_result_ref: str | None,
        review_result_ref: str | None,
        current_next_action: str,
        cleanup_status: str,
        cleanup_owner: str,
    ) -> dict[str, Any]:
        result_status = str(result_payload.get("status") or "")
        evidence_refs = [
            self._relative_to_repo(artifacts.result_json),
            self._relative_to_repo(artifacts.dispatch_state),
            self._relative_to_repo(artifacts.verification_summary),
            self._relative_to_repo(artifacts.cost_summary),
            self._relative_to_repo(artifacts.evidence_index),
        ]
        if artifacts.projection_markdown is not None:
            evidence_refs.append(self._relative_to_repo(artifacts.projection_markdown))
        if handoff_receipt_ref is not None:
            evidence_refs.append(handoff_receipt_ref)
        if planner_result_ref is not None:
            evidence_refs.append(planner_result_ref)
        if review_result_ref is not None:
            evidence_refs.append(review_result_ref)

        payload = {
            "run_id": str(result_payload.get("run_id") or ""),
            "repo_root": str(self._config.layout.repo_root),
            "objective": task.title,
            "status": self._closeout_status(result_status),
            "completed": self._closeout_completed(
                result_status,
                planner_result_ref,
                review_result_ref,
                artifacts.projection_markdown,
            ),
            "not_completed": self._closeout_not_completed(result_status, planner_result_ref),
            "conflicts": self._closeout_conflicts(cleanup_status),
            "tests": self._closeout_tests(
                verification_payload=verification_payload,
                verification_ref=self._relative_to_repo(artifacts.verification_summary),
            ),
            "evidence_refs": evidence_refs,
            "cleanup_status": cleanup_status,
            "cleanup_owner": cleanup_owner,
            "branches_removed": [],
            "worktrees_removed": (
                [task.worktree_path]
                if cleanup_status == "cleaned" and task.worktree_path.strip() not in {".", "./"}
                else []
            ),
            "residual_risks": self._closeout_residual_risks(
                result_status,
                cleanup_status,
                planner_result_ref,
                review_result_ref,
            ),
            "repo_side_done": self._closeout_repo_side_done(
                planner_result_ref,
                review_result_ref,
                artifacts.projection_markdown,
            ),
            "still_open": self._closeout_still_open(
                result_status,
                current_next_action,
                planner_result_ref,
            ),
            "next_action": current_next_action,
        }
        if handoff_receipt_ref is not None:
            payload["handoff_receipt_ref"] = handoff_receipt_ref
        return payload

    @staticmethod
    def _closeout_status(result_status: str) -> str:
        if result_status == "succeeded":
            return "succeeded"
        if result_status in {"waiting_handoff", "needs_review"}:
            return "partial"
        return "blocked"

    @staticmethod
    def _closeout_completed(
        result_status: str,
        planner_result_ref: str | None,
        review_result_ref: str | None,
        projection_markdown: Path | None,
    ) -> list[str]:
        completed = [
            "result.json formal evidence written",
            "dispatch_state.json runtime ledger written",
            "verification summary recorded",
            "closeout bundle recorded",
        ]
        if projection_markdown is not None:
            completed.append("compatibility projection refreshed")
        if planner_result_ref is not None:
            completed.append("structured planner receipt recorded")
        if review_result_ref is not None:
            completed.append("repo-side blocking review receipt recorded")
        if result_status == "succeeded":
            completed.append("worker execution completed within current repo-side boundary")
        return completed

    @staticmethod
    def _closeout_not_completed(
        result_status: str,
        planner_result_ref: str | None,
    ) -> list[str]:
        if result_status == "waiting_handoff":
            if planner_result_ref is not None:
                return ["planner disposition follow-up before worker execution"]
            return ["planner handoff resolution before worker execution"]
        if result_status == "needs_review":
            return ["blocking review disposition before downstream use"]
        if result_status == "failed":
            return ["verification or worker failure remediation"]
        return []

    @staticmethod
    def _closeout_conflicts(cleanup_status: str) -> list[str]:
        if cleanup_status == "deferred":
            return ["cleanup remains deferred to the operator"]
        if cleanup_status == "cleanup_failed":
            return ["runtime cleanup failed and requires operator follow-up"]
        return []

    @staticmethod
    def _closeout_tests(
        *,
        verification_payload: dict[str, Any],
        verification_ref: str,
    ) -> list[dict[str, str]]:
        commands_run = verification_payload.get("commands_run")
        if not isinstance(commands_run, list):
            return []
        tests: list[dict[str, str]] = []
        for entry in commands_run:
            if not isinstance(entry, dict):
                continue
            gate = str(entry.get("gate") or "").strip()
            status = str(entry.get("status") or "").strip()
            if not gate or not status:
                continue
            tests.append(
                {
                    "name": gate,
                    "status": status,
                    "evidence_ref": verification_ref,
                }
            )
        return tests

    @staticmethod
    def _closeout_residual_risks(
        result_status: str,
        cleanup_status: str,
        planner_result_ref: str | None,
        review_result_ref: str | None,
    ) -> list[str]:
        risks = ["repo-side green does not imply live accepted"]
        if result_status == "waiting_handoff":
            if planner_result_ref is not None:
                risks.append("planner receipt is repo-side only and still stops before worker execution")
            else:
                risks.append("live planner remains unwired; current handoff receipt is repo-side only")
        if result_status == "needs_review" and review_result_ref is not None:
            risks.append("review_result is a repo-side gate receipt; live heterogeneous review sidecar remains unwired")
        if cleanup_status == "deferred":
            risks.append("worktree cleanup may still require manual follow-up")
        if cleanup_status == "cleanup_failed":
            risks.append("cleanup failed and may leave residual isolated workspace state")
        return risks

    @staticmethod
    def _closeout_repo_side_done(
        planner_result_ref: str | None,
        review_result_ref: str | None,
        projection_markdown: Path | None,
    ) -> list[str]:
        done = [
            "formal result, verification, cost, and ledger artifacts were written",
            "closeout bundle captures the current repo-side truth boundary",
        ]
        if projection_markdown is not None:
            done.append("compatibility projection remains aligned with canonical runtime output")
        if planner_result_ref is not None:
            done.append("structured planner receipt now exists as a repo-side blocking artifact")
        if review_result_ref is not None:
            done.append("structured review receipt now exists as a repo-side blocking artifact")
        return done

    @staticmethod
    def _closeout_still_open(
        result_status: str,
        current_next_action: str,
        planner_result_ref: str | None,
    ) -> list[str]:
        still_open = ["live accepted"]
        if result_status == "waiting_handoff" and planner_result_ref is None:
            still_open.append("live planner wiring")
        if result_status == "needs_review":
            still_open.append("live heterogeneous review wiring")
        if result_status == "failed":
            still_open.append("retry or manual remediation")
        if current_next_action and current_next_action != "none":
            still_open.append(current_next_action)
        return still_open

    def _planner_gate_reasons(
        self,
        task: CanonicalTask,
    ) -> list[str]:
        reasons: list[str] = []
        if task.user_forced_planner:
            reasons.append("user_forced_planner=true")
        if task.risk_level in {"high", "critical"}:
            reasons.append(f"risk_level={task.risk_level}")
        if task.depends_on:
            reasons.append("depends_on=" + ", ".join(task.depends_on))
        return reasons

    def _worker_execution_gate_reasons(
        self,
        task: CanonicalTask,
        worker_profile: WorkerProfile,
    ) -> list[str]:
        reasons: list[str] = []
        if task.execution_lane != worker_profile.lane:
            reasons.append(f"execution_lane={task.execution_lane}")
        if task.requires_network and worker_profile.network_profile == "off":
            reasons.append("requires_network=true")
        if task.requires_gui:
            reasons.append("requires_gui=true")
        reasons.extend(self._runtime_capability_gate_reasons(worker_profile))
        return reasons

    def _planner_sidecar_gate_reasons(
        self,
        worker_profile: WorkerProfile,
    ) -> list[str]:
        if worker_profile.worker_kind in LIVE_PLANNER_WORKER_KINDS:
            return []
        return [
            (
                "planner_sidecar_not_wired "
                f"worker_kind={worker_profile.worker_kind} "
                f"worker_profile={worker_profile.name}"
            )
        ]

    def _quota_gate_reasons(
        self,
        worker_profile: WorkerProfile,
    ) -> list[str]:
        active_leases = db.count_active_leases_for_worker_profile(
            self._config.layout.control_plane_db,
            worker_profile=worker_profile.name,
        )
        if active_leases <= worker_profile.max_active_leases:
            return []
        return [
            (
                "lease_quota_exhausted "
                f"worker_profile={worker_profile.name} "
                f"active_leases={active_leases} "
                f"max_active_leases={worker_profile.max_active_leases}"
            )
        ]

    def _runtime_capability_gate_reasons(
        self,
        worker_profile: WorkerProfile,
    ) -> list[str]:
        if worker_profile.lane == "host_local":
            return []
        return [
            (
                "host_runtime=host_local "
                f"selected_lane={worker_profile.lane} "
                "runner_not_wired "
                f"worker_profile={worker_profile.name}"
            )
        ]

    def _review_gate_reasons(self, task: CanonicalTask) -> list[str]:
        reasons: list[str] = []
        touches_policy_surface = self._touches_policy_surface(task)
        if task.risk_level in {"medium", "high", "critical"}:
            reasons.append(f"risk_level={task.risk_level}")
        if task.write_access and (
            task.risk_level in {"medium", "high", "critical"} or touches_policy_surface
        ):
            reasons.append("write_access=true")
        if task.user_forced_review:
            reasons.append("user_forced_review=true")
        if touches_policy_surface:
            reasons.append("touches_policy_surface=true")
        return reasons

    def _touches_policy_surface(self, task: CanonicalTask) -> bool:
        return any(
            self._globs_overlap(allowed_path, policy_surface)
            for allowed_path in task.allowed_paths
            for policy_surface in self._runtime_config.policies.policy_surface_globs
        )

    @staticmethod
    def _globs_overlap(left: str, right: str) -> bool:
        normalized_left = left.replace("\\", "/").strip()
        normalized_right = right.replace("\\", "/").strip()
        if normalized_left == normalized_right:
            return True

        left_prefix = HostLocalRunner._glob_prefix(normalized_left)
        right_prefix = HostLocalRunner._glob_prefix(normalized_right)
        if left_prefix and right_prefix:
            if left_prefix == right_prefix:
                return True
            if left_prefix.startswith(right_prefix.rstrip("/") + "/"):
                return True
            if right_prefix.startswith(left_prefix.rstrip("/") + "/"):
                return True

        # Fall back to one-way glob checks when a literal or narrower pattern exists.
        if "*" not in normalized_left and fnmatchcase(normalized_left, normalized_right):
            return True
        if "*" not in normalized_right and fnmatchcase(normalized_right, normalized_left):
            return True
        return False

    @staticmethod
    def _glob_prefix(pattern: str) -> str:
        normalized = pattern.replace("\\", "/").strip()
        wildcard_index = min(
            [index for index in (normalized.find("*"), normalized.find("?")) if index != -1],
            default=-1,
        )
        if wildcard_index != -1:
            normalized = normalized[:wildcard_index]
        return normalized.rstrip("/")

    @staticmethod
    def _build_usage_observations(usage: WorkerUsage | None) -> list[str]:
        if usage is None:
            return ["- Structured token usage was not available from the worker runtime."]

        return [
            "- Structured token usage captured from the worker runtime.",
            (
                f"- usage source={usage.source}; total={usage.total.total_tokens}; "
                f"input={usage.total.input_tokens}; output={usage.total.output_tokens}; "
                f"cached_input={usage.total.cached_input_tokens}; "
                f"reasoning_output={usage.total.reasoning_output_tokens}."
            ),
            (
                f"- usage last_turn total={usage.last.total_tokens}; input={usage.last.input_tokens}; "
                f"output={usage.last.output_tokens}."
            ),
        ]

    @staticmethod
    def _usage_payload(usage: WorkerUsage | None) -> dict[str, Any] | None:
        if usage is None:
            return None

        return {
            "source": usage.source,
            "last": {
                "cached_input_tokens": usage.last.cached_input_tokens,
                "input_tokens": usage.last.input_tokens,
                "output_tokens": usage.last.output_tokens,
                "reasoning_output_tokens": usage.last.reasoning_output_tokens,
                "total_tokens": usage.last.total_tokens,
            },
            "total": {
                "cached_input_tokens": usage.total.cached_input_tokens,
                "input_tokens": usage.total.input_tokens,
                "output_tokens": usage.total.output_tokens,
                "reasoning_output_tokens": usage.total.reasoning_output_tokens,
                "total_tokens": usage.total.total_tokens,
            },
            "model_context_window": usage.model_context_window,
        }

    @classmethod
    def _lease_expires_at(cls, acquired_at: str) -> str:
        acquired = datetime.fromisoformat(acquired_at.replace("Z", "+00:00"))
        expires = acquired + cls._LEASE_TTL
        return expires.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _dispatch_state_payload(
        self,
        *,
        task: CanonicalTask,
        worker_profile: WorkerProfile,
        route_reason: str,
        run_id: str,
        workspace_root: Path,
        status: str,
        status_reason: str,
        next_action: str,
        cleanup_status: str,
        cleanup_owner: str,
        started_at: str,
        updated_at: str,
        heartbeat_at: str,
        stale_after: str,
    ) -> dict[str, Any]:
        return {
            "run_id": run_id,
            "attempt": self._config.attempt,
            "task_id": task.task_id,
            "agent_role": "worker",
            "model_policy": self._model_policy(task, worker_profile),
            "repo_root": str(self._config.layout.repo_root),
            "target_repo": task.target_repo,
            "branch_name": task.branch_name,
            "worktree_path": task.worktree_path,
            "workspace_root": str(workspace_root),
            "route_reason": route_reason,
            "allowed_paths": list(task.allowed_paths),
            "forbidden_paths": list(task.forbidden_paths),
            "source_ref": self._source_ref(task.path),
            "lease_owner": self._config.worker_id,
            "started_at": started_at,
            "updated_at": updated_at,
            "heartbeat_at": heartbeat_at,
            "stale_after": stale_after,
            "execution_lane": worker_profile.lane,
            "worker_profile": worker_profile.name,
            "status": status,
            "status_reason": status_reason,
            "next_action": next_action,
            "cleanup_status": cleanup_status,
            "cleanup_owner": cleanup_owner,
        }

    def _model_policy(
        self,
        task: CanonicalTask,
        worker_profile: WorkerProfile,
    ) -> dict[str, str]:
        if task.risk_level in {"high", "critical"}:
            reasoning_effort = "xhigh"
        elif task.write_access or self._touches_policy_surface(task):
            reasoning_effort = "high"
        else:
            reasoning_effort = "medium"
        return {
            "model": worker_profile.model,
            "reasoning_effort": reasoning_effort,
            "rationale": "derived from worker role, task risk, and policy-surface sensitivity",
        }

    def _resolve_route_decision(self, task: CanonicalTask) -> RouteDecision:
        if self._config.worker_profile is not None:
            worker_profile = self._runtime_config.worker_profile(self._config.worker_profile)
            route_reason = (
                self._config.route_reason
                or f"runner override worker_profile={worker_profile.name} selected for host_local execution"
            )
            return RouteDecision(worker_profile=worker_profile, route_reason=route_reason)

        if task.worker_profile is not None:
            worker_profile = self._runtime_config.worker_profile(task.worker_profile)
            route_reason = (
                self._config.route_reason
                or f"repo-owned worker_profile={worker_profile.name} selected from canonical task"
            )
            return RouteDecision(worker_profile=worker_profile, route_reason=route_reason)

        worker_profile = self._runtime_config.worker_profile()
        route_reason = (
            self._config.route_reason
            or f"repo default worker_profile={worker_profile.name} selected from orchestrator.yaml"
        )
        return RouteDecision(worker_profile=worker_profile, route_reason=route_reason)

    def _resolve_worker(self, worker_profile: WorkerProfile) -> WorkerLike:
        if self._worker is not None:
            return self._worker
        if self._worker_factory is not None:
            return self._worker_factory.build(worker_profile)
        raise RuntimeError(
            "HostLocalRunner reached worker execution without a configured worker or worker factory "
            f"(worker_profile={worker_profile.name})"
        )

    def _resolve_review_worker_profile(self) -> WorkerProfile | None:
        profile_name = self._runtime_config.orchestrator.review_worker_profile
        if profile_name is None:
            return None
        return self._runtime_config.worker_profile(profile_name)

    def _resolve_review_worker(
        self,
        worker_profile: WorkerProfile,
    ) -> WorkerLike | None:
        if self._review_worker is not None:
            return self._review_worker
        if self._worker_factory is not None and hasattr(self._worker_factory, "build_review_sidecar"):
            builder = getattr(self._worker_factory, "build_review_sidecar")
            return builder(worker_profile)
        return None

    @staticmethod
    def _format_status_reason(prefix: str, reasons: list[str]) -> str:
        if not reasons:
            return prefix
        return f"{prefix}: {'; '.join(reasons)}"

    def _relative_to_repo(self, path: Path) -> str:
        return str(path.relative_to(self._config.layout.repo_root)).replace("\\", "/")

    def _source_ref(self, path: Path) -> str:
        try:
            return self._relative_to_repo(path)
        except ValueError:
            return str(path)
