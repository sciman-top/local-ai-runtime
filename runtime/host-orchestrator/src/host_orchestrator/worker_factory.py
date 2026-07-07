from __future__ import annotations

from typing import Protocol

from openai_codex import Codex

from host_orchestrator.claude_code_worker import ClaudeCodeStructuredWorker
from host_orchestrator.config_runtime import WorkerProfile
from host_orchestrator.exec_fallback import CodexExecFallbackWorker
from host_orchestrator.worker import CodexSdkWorker, WorkerLike


class WorkerFactoryError(RuntimeError):
    """Raised when a repo-owned worker profile cannot be materialized."""


class WorkerBuilder(Protocol):
    def build(self, worker_profile: WorkerProfile) -> WorkerLike: ...


class ReviewWorkerBuilder(Protocol):
    def build_review_sidecar(self, worker_profile: WorkerProfile) -> WorkerLike: ...


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

    def build_review_sidecar(self, worker_profile: WorkerProfile) -> WorkerLike:
        worker_kind = worker_profile.worker_kind
        if worker_kind == "claude_glm":
            return ClaudeCodeStructuredWorker(json_schema=_review_result_schema())
        if worker_kind == "codex_sdk":
            return CodexSdkWorker(self._codex())
        raise WorkerFactoryError(
            f"Unsupported worker_kind for live review sidecar: {worker_kind} "
            f"(worker_profile={worker_profile.name})"
        )


def _review_result_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "reviewer_kind",
            "review_mode",
            "findings",
            "blocking_reasons",
            "missing_tests",
            "recommended_action",
            "summary",
        ],
        "properties": {
            "reviewer_kind": {
                "type": "string",
                "enum": ["claude_glm", "gpt54_direct_review", "codex_review"],
            },
            "review_mode": {
                "type": "string",
                "enum": ["advisory", "blocking"],
            },
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["severity", "category", "title", "detail", "suggested_fix"],
                    "properties": {
                        "severity": {"type": "string"},
                        "category": {"type": "string"},
                        "title": {"type": "string"},
                        "detail": {"type": "string"},
                        "suggested_fix": {"type": "string"},
                    },
                },
            },
            "blocking_reasons": {
                "type": "array",
                "items": {"type": "string"},
            },
            "missing_tests": {
                "type": "array",
                "items": {"type": "string"},
            },
            "recommended_action": {
                "type": "string",
                "enum": ["approve", "revise", "reject"],
            },
            "summary": {"type": "string"},
        },
    }
