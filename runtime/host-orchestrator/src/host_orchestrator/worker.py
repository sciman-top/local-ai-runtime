from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from openai_codex import ApprovalMode, Sandbox


@dataclass(frozen=True)
class WorkerRequest:
    prompt: str
    cwd: Path
    model: str
    sandbox: Sandbox = Sandbox.workspace_write
    approval_mode: ApprovalMode = ApprovalMode.deny_all


@dataclass(frozen=True)
class WorkerResult:
    final_response: str | None
    raw_result: object


class ThreadLike(Protocol):
    def run(self, input: str, **kwargs: object) -> object: ...


class CodexLike(Protocol):
    def thread_start(self, **kwargs: object) -> ThreadLike: ...


class WorkerLike(Protocol):
    def run(self, request: WorkerRequest) -> WorkerResult: ...


def build_thread_start_options(request: WorkerRequest) -> dict[str, object]:
    return {
        "cwd": str(request.cwd),
        "model": request.model,
        "sandbox": request.sandbox,
        "approval_mode": request.approval_mode,
    }


def build_turn_run_options(request: WorkerRequest) -> dict[str, object]:
    return {
        "cwd": str(request.cwd),
        "model": request.model,
        "sandbox": request.sandbox,
        "approval_mode": request.approval_mode,
    }


def execute_request(request: WorkerRequest, codex: CodexLike) -> WorkerResult:
    thread = codex.thread_start(**build_thread_start_options(request))
    result = thread.run(request.prompt, **build_turn_run_options(request))
    return WorkerResult(
        final_response=getattr(result, "final_response", None),
        raw_result=result,
    )


class CodexSdkWorker:
    def __init__(self, codex: CodexLike) -> None:
        self._codex = codex

    def run(self, request: WorkerRequest) -> WorkerResult:
        return execute_request(request, self._codex)
