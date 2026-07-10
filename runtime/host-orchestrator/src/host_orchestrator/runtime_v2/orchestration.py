from __future__ import annotations

from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Protocol

from host_orchestrator.adaptive_orchestration import (
    AdaptiveOrchestrationError,
    WorktreeInspector,
    evaluate_orchestration_manifest,
    read_active_leases,
    validate_orchestration_execution_payload,
    write_orchestration_decision,
)
from host_orchestrator.agent_work_assets import load_mapping_file
from host_orchestrator.config_runtime import RuntimeConfigBundle, load_runtime_config
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.runtime_v2 import storage
from host_orchestrator.runtime_v2.artifacts import repo_relative, write_json
from host_orchestrator.runtime_v2.contracts import write_task
from host_orchestrator.runtime_v2.runner import RuntimeV2Config, RuntimeV2Runner
from host_orchestrator.worker_factory import RuntimeWorkerFactory


class TaskRunner(Protocol):
    def run_task(self, task_path: Path) -> Path: ...


RunnerBuilder = Callable[[RuntimeV2Config, Mapping[str, Any]], TaskRunner]


def run_orchestration_manifest_v2(
    manifest_path: Path,
    *,
    repo_root: Path,
    layout: RuntimeLayout,
    runner_builder: RunnerBuilder | None = None,
    worktree_inspector: WorktreeInspector | None = None,
) -> tuple[Path, dict[str, Any]]:
    runtime_config = load_runtime_config(repo_root)
    if not runtime_config.runtime.experimental_v2_enabled:
        raise AdaptiveOrchestrationError(
            "guarded orchestration requires runtime.experimental_v2_enabled=true"
        )
    layout = layout.with_runtime_v2_paths(
        control_plane_db_v2=runtime_config.runtime.control_plane_db_v2,
        artifact_root_v2=runtime_config.runtime.artifact_root_v2,
    )
    active_leases = read_active_leases(
        db_path=layout.control_plane_v2_db,
        worker_profiles=sorted(runtime_config.workers),
    )
    decision = evaluate_orchestration_manifest(
        manifest_path,
        repo_root=repo_root,
        runtime_config=runtime_config,
        active_leases=active_leases,
        worktree_inspector=worktree_inspector,
    )
    decision_path = write_orchestration_decision(layout=layout, decision=decision)
    decision_ref = repo_relative(layout, decision_path)
    if decision["effect"] != "guarded":
        raise AdaptiveOrchestrationError(
            "guarded execution requires a manifest orchestration profile with effect=guarded"
        )
    if decision["decision_status"] != "guarded_ready":
        raise AdaptiveOrchestrationError(
            "guarded execution is blocked: "
            + ", ".join(decision["blocking_reason_codes"])
        )

    manifest = load_mapping_file(manifest_path)
    task_map = {
        str(task["task_id"]): task
        for task in manifest["tasks"]
        if isinstance(task, dict)
    }
    task_routes = {
        str(route["task_id"]): route
        for route in decision["task_routes"]
        if isinstance(route, dict)
    }
    decision_root = decision_path.parent
    task_paths = _materialize_runtime_v2_tasks(
        manifest=manifest,
        decision_root=decision_root,
        runtime_config=runtime_config,
        task_routes=task_routes,
    )
    storage.initialize_control_plane_v2(layout.control_plane_v2_db)
    build_runner = runner_builder or _default_runner_builder
    started = perf_counter()
    results: list[dict[str, Any]] = []
    skipped_task_ids: list[str] = []
    stop_requested = False

    for wave in decision["waves"]:
        task_ids = [str(task_id) for task_id in wave["task_ids"]]
        if stop_requested:
            skipped_task_ids.extend(task_ids)
            continue
        wave_results = _run_wave(
            task_ids=task_ids,
            parallel=bool(wave["parallel"]),
            task_paths=task_paths,
            task_routes=task_routes,
            repo_root=repo_root,
            layout=layout,
            decision=decision,
            decision_ref=decision_ref,
            conflict_count=len(decision["conflicts"]),
            runner_builder=build_runner,
        )
        results.extend(wave_results)
        if decision["stop_policy"] == "stop_on_scope_or_contract_conflict":
            stop_requested = any(
                result.get("status") not in {"completed"}
                for result in wave_results
            )

    elapsed_ms = int((perf_counter() - started) * 1000)
    _attach_batch_metrics(
        repo_root=repo_root,
        results=results,
        batch_wall_time_ms=elapsed_ms,
        batch_result_count=len(results),
    )
    status_counts: dict[str, int] = {}
    for result in results:
        status = str(result.get("status") or "error")
        status_counts[status] = status_counts.get(status, 0) + 1
    execution_status = (
        "completed"
        if results
        and not skipped_task_ids
        and all(result.get("status") == "completed" for result in results)
        else "partial"
    )
    if not results:
        execution_status = "blocked"

    summary = {
        "schema_version": "orchestration_execution.v1",
        "decision_id": decision["decision_id"],
        "orchestration_decision_ref": decision_ref,
        "run_id": decision["run_id"],
        "policy_version": decision["policy_version"],
        "profile": decision["profile"],
        "selected_mode": decision["selected_mode"],
        "status": execution_status,
        "worker_execution_attempted": any(
            result.get("worker_execution_attempted") is True for result in results
        ),
        "result_count": len(results),
        "status_counts": dict(sorted(status_counts.items())),
        "parallel_wave_count": sum(1 for wave in decision["waves"] if wave["parallel"]),
        "serial_wave_count": sum(1 for wave in decision["waves"] if not wave["parallel"]),
        "skipped_task_ids": skipped_task_ids,
        "wall_time_ms": elapsed_ms,
        "results": results,
        "default_entrypoint_changed": False,
        "active_queue_changed": False,
        "live_accepted": False,
    }
    summary_path = decision_root / "orchestration-execution.json"
    validate_orchestration_execution_payload(summary)
    write_json(summary_path, summary)
    return summary_path, summary


def _materialize_runtime_v2_tasks(
    *,
    manifest: Mapping[str, Any],
    decision_root: Path,
    runtime_config: RuntimeConfigBundle,
    task_routes: Mapping[str, Mapping[str, Any]],
) -> dict[str, Path]:
    task_root = decision_root / "tasks"
    task_paths: dict[str, Path] = {}
    for raw_task in manifest["tasks"]:
        if not isinstance(raw_task, dict):
            raise AdaptiveOrchestrationError("manifest task must be an object")
        task_id = str(raw_task["task_id"])
        route = task_routes[task_id]
        verification_profile = _verification_profile_for_manifest_task(
            raw_task,
            runtime_config=runtime_config,
        )
        continuation_policy = (
            "guarded"
            if bool(raw_task["write_access"]) or bool(route["review_required"])
            else "auto"
        )
        done_when = [str(value) for value in raw_task["done_when"]]
        description = str(raw_task["goal"]).strip()
        if done_when:
            description += "\n\nDone when:\n" + "\n".join(
                f"- {value}" for value in done_when
            )
        task_payload = {
            "task_id": task_id,
            "title": str(raw_task["title"]),
            "description": description,
            "target_repo": str(raw_task["target_repo"]),
            "base_branch": str(raw_task["base_branch"]),
            "branch_name": str(raw_task["branch_name"]),
            "worktree_path": str(raw_task["worktree_path"])
            if bool(raw_task["write_access"])
            else ".",
            "allowed_paths": [str(value) for value in raw_task["allowed_paths"]],
            "forbidden_paths": [str(value) for value in raw_task["forbidden_paths"]],
            "write_access": bool(raw_task["write_access"]),
            "risk_level": str(raw_task["risk_level"]),
            "merge_policy": str(raw_task["merge_policy"]),
            "requires_network": bool(raw_task["requires_network"]),
            "requires_gui": bool(raw_task["requires_gui"]),
            "dependency_refs": [str(value) for value in raw_task["depends_on"]],
            "artifacts_out": [
                f".ai/runs-v2/{manifest['run_id']}/{task_id}/<attempt_id>/result.json"
            ],
            "verification_profile": verification_profile,
            "continuation_policy": continuation_policy,
            "worker_profile": str(route["worker_profile"]),
        }
        task_path = task_root / f"{task_id}.yaml"
        write_task(task_path, task_payload)
        task_paths[task_id] = task_path
    return task_paths


def _verification_profile_for_manifest_task(
    task: Mapping[str, Any],
    *,
    runtime_config: RuntimeConfigBundle,
) -> str:
    commands = task.get("verification_commands")
    if not isinstance(commands, dict):
        raise AdaptiveOrchestrationError(
            f"task {task.get('task_id')} verification_commands must be an object"
        )
    for name, profile in runtime_config.policies.verification_profiles.items():
        if all(
            commands.get(gate) == getattr(profile, gate)
            for gate in ("build", "lint", "typecheck", "test", "contract", "hotspot")
        ):
            return name
    raise AdaptiveOrchestrationError(
        f"task {task.get('task_id')} verification_commands do not match a repo-owned verification profile"
    )


def _run_wave(
    *,
    task_ids: list[str],
    parallel: bool,
    task_paths: Mapping[str, Path],
    task_routes: Mapping[str, Mapping[str, Any]],
    repo_root: Path,
    layout: RuntimeLayout,
    decision: Mapping[str, Any],
    decision_ref: str,
    conflict_count: int,
    runner_builder: RunnerBuilder,
) -> list[dict[str, Any]]:
    if parallel:
        results_by_task: dict[str, dict[str, Any]] = {}
        with ThreadPoolExecutor(max_workers=len(task_ids)) as executor:
            futures = {
                executor.submit(
                    _run_one,
                    task_id=task_id,
                    task_path=task_paths[task_id],
                    route=task_routes[task_id],
                    repo_root=repo_root,
                    layout=layout,
                    decision=decision,
                    decision_ref=decision_ref,
                    conflict_count=conflict_count,
                    runner_builder=runner_builder,
                ): task_id
                for task_id in task_ids
            }
            for future in as_completed(futures):
                task_id = futures[future]
                try:
                    results_by_task[task_id] = future.result()
                except Exception as exc:
                    results_by_task[task_id] = _error_result(
                        task_id=task_id,
                        route=task_routes[task_id],
                        decision=decision,
                        decision_ref=decision_ref,
                        exc=exc,
                    )
        return [results_by_task[task_id] for task_id in task_ids]

    results: list[dict[str, Any]] = []
    for task_id in task_ids:
        try:
            results.append(
                _run_one(
                    task_id=task_id,
                    task_path=task_paths[task_id],
                    route=task_routes[task_id],
                    repo_root=repo_root,
                    layout=layout,
                    decision=decision,
                    decision_ref=decision_ref,
                    conflict_count=conflict_count,
                    runner_builder=runner_builder,
                )
            )
        except Exception as exc:
            results.append(
                _error_result(
                    task_id=task_id,
                    route=task_routes[task_id],
                    decision=decision,
                    decision_ref=decision_ref,
                    exc=exc,
                )
            )
    return results


def _run_one(
    *,
    task_id: str,
    task_path: Path,
    route: Mapping[str, Any],
    repo_root: Path,
    layout: RuntimeLayout,
    decision: Mapping[str, Any],
    decision_ref: str,
    conflict_count: int,
    runner_builder: RunnerBuilder,
) -> dict[str, Any]:
    model_policy = route["model_policy"]
    config = RuntimeV2Config(
        workspace_root=repo_root,
        layout=layout,
        worker_profile=str(route["worker_profile"]),
        run_id=str(decision["run_id"]),
        model_override=str(model_policy["model"]),
        reasoning_effort=str(model_policy["reasoning_effort"]),
        orchestration_decision_id=str(decision["decision_id"]),
        orchestration_decision_ref=decision_ref,
        orchestration_policy_version=str(decision["policy_version"]),
        orchestration_selected_mode=str(decision["selected_mode"]),
        orchestration_conflict_count=conflict_count,
        orchestration_evaluation_context=(
            dict(decision["evaluation_context"])
            if isinstance(decision.get("evaluation_context"), dict)
            else None
        ),
    )
    runner = runner_builder(config, route)
    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    return {
        "task_id": task_id,
        "result_path": repo_relative(layout, result_path),
        "attempt_id": result_payload.get("attempt_id"),
        "status": result_payload.get("status"),
        "next_action": result_payload.get("next_action"),
        "worker_profile": result_payload.get("worker_profile"),
        "model_policy": result_payload.get("model_policy"),
        "orchestration_decision_ref": result_payload.get(
            "orchestration_decision_ref"
        ),
        "worker_execution_attempted": _trace_has_execution_stage(result_path.parent),
    }


def _error_result(
    *,
    task_id: str,
    route: Mapping[str, Any],
    decision: Mapping[str, Any],
    decision_ref: str,
    exc: Exception,
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "result_path": None,
        "attempt_id": None,
        "status": "error",
        "next_action": "inspect_orchestration_error",
        "worker_profile": route.get("worker_profile"),
        "model_policy": route.get("model_policy"),
        "orchestration_decision_ref": decision_ref,
        "decision_id": decision.get("decision_id"),
        "policy_version": decision.get("policy_version"),
        "worker_execution_attempted": False,
        "error_type": type(exc).__name__,
        "error": str(exc),
    }


def _trace_has_execution_stage(attempt_root: Path) -> bool:
    trace_path = attempt_root / "trace_manifest.json"
    if not trace_path.exists():
        return False
    payload = json.loads(trace_path.read_text(encoding="utf-8"))
    stages = payload.get("stages")
    if not isinstance(stages, list):
        return False
    return any(
        isinstance(stage, dict)
        and stage.get("stage") == "execution"
        and stage.get("status") not in {None, "skipped", "not_started"}
        for stage in stages
    )


def _default_runner_builder(
    config: RuntimeV2Config,
    route: Mapping[str, Any],
) -> RuntimeV2Runner:
    del route
    return RuntimeV2Runner(
        config,
        worker_factory=RuntimeWorkerFactory(),
    )


def _attach_batch_metrics(
    *,
    repo_root: Path,
    results: list[dict[str, Any]],
    batch_wall_time_ms: int,
    batch_result_count: int,
) -> None:
    for result in results:
        result_ref = result.get("result_path")
        if not isinstance(result_ref, str):
            continue
        fixture_path = repo_root / Path(result_ref).parent / "regression_fixture.json"
        if not fixture_path.exists():
            continue
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        metrics = payload.get("orchestration_metrics")
        if not isinstance(metrics, dict):
            continue
        metrics["batch_wall_time_ms"] = batch_wall_time_ms
        metrics["batch_result_count"] = batch_result_count
        write_json(fixture_path, payload)
