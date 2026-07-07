from __future__ import annotations

from typing import Protocol

from openai_codex import Codex

from host_orchestrator.config_runtime import WorkerProfile
from host_orchestrator.exec_fallback import CodexExecFallbackWorker
from host_orchestrator.worker import CodexSdkWorker, WorkerLike


class WorkerFactoryError(RuntimeError):
    """Raised when a repo-owned worker profile cannot be materialized."""


class WorkerBuilder(Protocol):
    def build(self, worker_profile: WorkerProfile) -> WorkerLike: ...


class RuntimeWorkerFactory:
    def __init__(self) -> None:
        self._codex_client: Codex | None = None

    def build(self, worker_profile: WorkerProfile) -> WorkerLike:
        worker_kind = worker_profile.worker_kind
        if worker_kind == "codex_sdk":
            return CodexSdkWorker(self._codex())
        if worker_kind == "codex_exec":
            return CodexExecFallbackWorker()
        if worker_kind == "scripted":
            raise WorkerFactoryError(
                "worker_kind=scripted is only supported by repo-side deterministic fixtures, "
                f"not live task execution (worker_profile={worker_profile.name})"
            )
        if worker_kind in {"gpt54_direct", "claude_glm"}:
            raise WorkerFactoryError(
                f"worker_kind={worker_kind} is declared in the contract but not wired for live task execution yet "
                f"(worker_profile={worker_profile.name})"
            )
        raise WorkerFactoryError(
            f"Unsupported worker_kind for live task execution: {worker_kind} "
            f"(worker_profile={worker_profile.name})"
        )

    def _codex(self) -> Codex:
        if self._codex_client is None:
            self._codex_client = Codex()
        return self._codex_client
