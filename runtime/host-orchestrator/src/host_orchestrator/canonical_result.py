from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable

from host_orchestrator.canonical_task import CanonicalTask
from host_orchestrator.config_runtime import WorkerProfile
from host_orchestrator.evidence_index import (
    build_evidence_index_payload,
    render_relative_path,
)
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.worker import WorkerResult, WorkerUsage


ProjectionWriter = Callable[["RunArtifacts"], Path | None]


@dataclass(frozen=True)
class RunArtifacts:
    run_id: str
    task_root: Path
    stdout_log: Path
    stderr_log: Path
    verification_summary: Path
    cost_summary: Path
    worker_output: Path
    result_json: Path
    dispatch_state: Path
    evidence_index: Path
    planner_result: Path
    review_result: Path
    closeout_bundle: Path
    projection_markdown: Path | None


@dataclass(frozen=True)
class ResultBundle:
    artifacts: RunArtifacts
    result_payload: dict[str, Any]
    evidence_index_payload: dict[str, Any]


def build_run_id(*, prefix: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{timestamp}"


def build_run_artifacts(
    *,
    layout: RuntimeLayout,
    run_id: str,
    task_id: str,
) -> RunArtifacts:
    task_root = layout.runs_root / run_id / task_id
    return RunArtifacts(
        run_id=run_id,
        task_root=task_root,
        stdout_log=task_root / "stdout.log",
        stderr_log=task_root / "stderr.log",
        verification_summary=task_root / "verification_summary.json",
        cost_summary=task_root / "cost_summary.json",
        worker_output=task_root / "artifacts" / "worker-output.txt",
        result_json=task_root / "result.json",
        dispatch_state=task_root / "dispatch_state.json",
        evidence_index=task_root / "evidence_index.json",
        planner_result=task_root / "planner_result.json",
        review_result=task_root / "review_result.json",
        closeout_bundle=task_root / "closeout_bundle.json",
        projection_markdown=None,
    )


def write_result_bundle(
    *,
    layout: RuntimeLayout,
    task: CanonicalTask,
    run_id: str,
    attempt: int,
    worker_profile: WorkerProfile,
    worker_result: WorkerResult,
    started_at: str,
    finished_at: str,
    verification_payload: dict[str, Any] | None = None,
    projection_writer: ProjectionWriter | None = None,
    route_reason: str = "",
    result_status: str | None = None,
    termination_reason: str | None = None,
    handoff_required: bool = False,
    next_action: str = "none",
    cost_payload_override: dict[str, Any] | None = None,
    cleanup_status: str = "deferred",
    cleanup_owner: str = "operator",
    status_reason: str = "",
) -> ResultBundle:
    artifacts = build_run_artifacts(layout=layout, run_id=run_id, task_id=task.task_id)
    artifacts.task_root.mkdir(parents=True, exist_ok=True)
    artifacts.worker_output.parent.mkdir(parents=True, exist_ok=True)

    artifacts.stdout_log.write_text(_extract_stdout_text(worker_result), encoding="utf-8")
    artifacts.stderr_log.write_text(_extract_stderr_text(worker_result), encoding="utf-8")
    artifacts.worker_output.write_text(worker_result.final_response or "", encoding="utf-8")

    verification_payload = verification_payload or {
        "status": "no_commands_configured",
        "commands_run": [],
    }
    _write_json(artifacts.verification_summary, verification_payload)

    cost_payload = cost_payload_override or {
        "mode": "token_only",
        "source": worker_result.usage.source if worker_result.usage is not None else "worker_usage_unavailable",
        "currency": None,
        "estimated_cost": None,
        "usage": _usage_payload(worker_result.usage),
    }
    _write_json(artifacts.cost_summary, cost_payload)

    projection_path = projection_writer(artifacts) if projection_writer is not None else None
    artifacts = replace(artifacts, projection_markdown=projection_path)

    relative_stdout = render_relative_path(layout.repo_root, artifacts.stdout_log)
    relative_stderr = render_relative_path(layout.repo_root, artifacts.stderr_log)
    relative_verification = render_relative_path(layout.repo_root, artifacts.verification_summary)
    relative_cost = render_relative_path(layout.repo_root, artifacts.cost_summary)
    relative_worker_output = render_relative_path(layout.repo_root, artifacts.worker_output)
    relative_dispatch_state = render_relative_path(layout.repo_root, artifacts.dispatch_state)

    result_status = result_status or (
        "failed" if verification_payload.get("status") == "failed" else "succeeded"
    )
    termination_reason = termination_reason or (
        "verification_failed" if verification_payload.get("status") == "failed" else "worker_completed"
    )

    result_payload = {
        "task_id": task.task_id,
        "run_id": run_id,
        "attempt": attempt,
        "worker_kind": worker_profile.worker_kind,
        "worker_profile": worker_profile.name,
        "lane": worker_profile.lane,
        "sandbox_profile": worker_profile.sandbox_profile,
        "network_profile": worker_profile.network_profile,
        "status": result_status,
        "started_at": started_at,
        "finished_at": finished_at,
        "route_reason": route_reason,
        "stdout_log": relative_stdout,
        "stderr_log": relative_stderr,
        "verification_summary_ref": relative_verification,
        "cost_summary": relative_cost,
        "termination_reason": termination_reason,
        "cleanup_status": cleanup_status,
        "cleanup_owner": cleanup_owner,
        "artifacts": [relative_worker_output],
        "compatibility_projection_ref": (
            render_relative_path(layout.repo_root, projection_path) if projection_path is not None else None
        ),
        "handoff_required": handoff_required,
        "status_reason": status_reason,
        "next_action": next_action,
        "dispatch_state_ref": relative_dispatch_state,
        "planner_result_ref": None,
        "review_result_ref": None,
        "closeout_bundle_ref": None,
    }
    _write_json(artifacts.result_json, result_payload)

    indexed_paths = [
        artifacts.stdout_log,
        artifacts.stderr_log,
        artifacts.verification_summary,
        artifacts.cost_summary,
        artifacts.worker_output,
        artifacts.result_json,
    ]
    if artifacts.dispatch_state.exists():
        indexed_paths.append(artifacts.dispatch_state)
    if projection_path is not None:
        indexed_paths.append(projection_path)

    evidence_index_payload = build_evidence_index_payload(
        repo_root=layout.repo_root,
        task_id=task.task_id,
        run_id=run_id,
        indexed_paths=indexed_paths,
    )
    _write_json(artifacts.evidence_index, evidence_index_payload)

    return ResultBundle(
        artifacts=artifacts,
        result_payload=result_payload,
        evidence_index_payload=evidence_index_payload,
    )


def update_result_cleanup_status(
    result_path: Path,
    *,
    cleanup_status: str,
    next_action: str | None = None,
) -> dict[str, Any]:
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload["cleanup_status"] = cleanup_status
    if next_action is not None:
        payload["next_action"] = next_action
    _write_json(result_path, payload)
    return payload


def update_result_metadata(
    result_path: Path,
    **updates: Any,
) -> dict[str, Any]:
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    for key, value in updates.items():
        payload[key] = value
    _write_json(result_path, payload)
    return payload


def write_review_result_artifact(
    artifacts: RunArtifacts,
    payload: dict[str, Any],
) -> dict[str, Any]:
    _write_json(artifacts.review_result, payload)
    return payload


def write_planner_result_artifact(
    artifacts: RunArtifacts,
    payload: dict[str, Any],
) -> dict[str, Any]:
    _write_json(artifacts.planner_result, payload)
    return payload


def write_closeout_bundle_artifact(
    artifacts: RunArtifacts,
    payload: dict[str, Any],
) -> dict[str, Any]:
    _write_json(artifacts.closeout_bundle, payload)
    return payload


def refresh_evidence_index(
    *,
    layout: RuntimeLayout,
    artifacts: RunArtifacts,
    task_id: str,
    run_id: str,
) -> dict[str, Any]:
    indexed_paths = [
        artifacts.stdout_log,
        artifacts.stderr_log,
        artifacts.verification_summary,
        artifacts.cost_summary,
        artifacts.worker_output,
        artifacts.result_json,
    ]
    if artifacts.dispatch_state.exists():
        indexed_paths.append(artifacts.dispatch_state)
    if artifacts.planner_result.exists():
        indexed_paths.append(artifacts.planner_result)
    if artifacts.review_result.exists():
        indexed_paths.append(artifacts.review_result)
    if artifacts.closeout_bundle.exists():
        indexed_paths.append(artifacts.closeout_bundle)
    if artifacts.projection_markdown is not None:
        indexed_paths.append(artifacts.projection_markdown)

    payload = build_evidence_index_payload(
        repo_root=layout.repo_root,
        task_id=task_id,
        run_id=run_id,
        indexed_paths=indexed_paths,
    )
    _write_json(artifacts.evidence_index, payload)
    return payload


def _extract_stdout_text(worker_result: WorkerResult) -> str:
    if worker_result.stdout_text is not None:
        return worker_result.stdout_text
    return worker_result.final_response or ""


def _extract_stderr_text(worker_result: WorkerResult) -> str:
    if worker_result.stderr_text is not None:
        return worker_result.stderr_text
    return ""

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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
