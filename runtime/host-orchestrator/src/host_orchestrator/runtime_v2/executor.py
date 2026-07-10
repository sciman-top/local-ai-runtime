from __future__ import annotations

from pathlib import Path

from host_orchestrator.config_runtime import WorkerProfile
from host_orchestrator.worker import WorkerLike, WorkerRequest, WorkerResult

from host_orchestrator.runtime_v2.contracts import RuntimeV2Task


def execute_task(
    *,
    task: RuntimeV2Task,
    worker: WorkerLike,
    worker_profile: WorkerProfile,
    workspace_root: Path,
    reasoning_effort: str | None = None,
) -> WorkerResult:
    request = WorkerRequest(
        prompt=task.render_worker_prompt(),
        cwd=workspace_root,
        model=worker_profile.model,
        reasoning_effort=reasoning_effort,
        sandbox=worker_profile.sandbox(),
        approval_mode=worker_profile.approval_mode(),
    )
    return worker.run(request)
