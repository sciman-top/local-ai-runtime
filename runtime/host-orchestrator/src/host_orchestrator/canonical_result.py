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
    evidence_index: Path
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
        evidence_index=task_root / "evidence_index.json",
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
    projection_writer: ProjectionWriter | None = None,
) -> ResultBundle:
    artifacts = build_run_artifacts(layout=layout, run_id=run_id, task_id=task.task_id)
    artifacts.task_root.mkdir(parents=True, exist_ok=True)
    artifacts.worker_output.parent.mkdir(parents=True, exist_ok=True)

    artifacts.stdout_log.write_text(_extract_stdout_text(worker_result), encoding="utf-8")
    artifacts.stderr_log.write_text(_extract_stderr_text(worker_result), encoding="utf-8")
    artifacts.worker_output.write_text(worker_result.final_response or "", encoding="utf-8")

    verification_payload = {
        "status": "no_commands_configured",
        "commands_run": [],
    }
    _write_json(artifacts.verification_summary, verification_payload)

    cost_payload = {
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

    result_payload = {
        "task_id": task.task_id,
        "run_id": run_id,
        "attempt": attempt,
        "worker_kind": worker_profile.worker_kind,
        "worker_profile": worker_profile.name,
        "lane": worker_profile.lane,
        "sandbox_profile": worker_profile.sandbox_profile,
        "network_profile": worker_profile.network_profile,
        "status": "succeeded",
        "started_at": started_at,
        "finished_at": finished_at,
        "stdout_log": relative_stdout,
        "stderr_log": relative_stderr,
        "verification_summary_ref": relative_verification,
        "cost_summary": relative_cost,
        "termination_reason": "worker_completed",
        "cleanup_status": "deferred",
        "artifacts": [relative_worker_output],
        "compatibility_projection_ref": (
            render_relative_path(layout.repo_root, projection_path) if projection_path is not None else None
        ),
        "handoff_required": False,
        "next_action": "none",
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
