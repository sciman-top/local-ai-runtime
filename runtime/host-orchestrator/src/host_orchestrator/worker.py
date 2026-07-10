from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from openai_codex import ApprovalMode, Sandbox


@dataclass(frozen=True)
class UsageBreakdown:
    cached_input_tokens: int
    input_tokens: int
    output_tokens: int
    reasoning_output_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class WorkerUsage:
    source: str
    last: UsageBreakdown
    total: UsageBreakdown
    model_context_window: int | None = None


@dataclass(frozen=True)
class WorkerRequest:
    prompt: str
    cwd: Path
    model: str
    reasoning_effort: str | None = None
    sandbox: Sandbox = Sandbox.workspace_write
    approval_mode: ApprovalMode = ApprovalMode.deny_all


@dataclass(frozen=True)
class WorkerResult:
    final_response: str | None
    raw_result: object
    usage: WorkerUsage | None = None
    stdout_text: str | None = None
    stderr_text: str | None = None


class ThreadLike(Protocol):
    def run(self, input: str, **kwargs: object) -> object: ...


class CodexLike(Protocol):
    def thread_start(self, **kwargs: object) -> ThreadLike: ...


class WorkerLike(Protocol):
    def run(self, request: WorkerRequest) -> WorkerResult: ...


def _extract_usage_breakdown(candidate: object) -> UsageBreakdown | None:
    if candidate is None:
        return None

    cached_input_tokens = getattr(candidate, "cached_input_tokens", None)
    input_tokens = getattr(candidate, "input_tokens", None)
    output_tokens = getattr(candidate, "output_tokens", None)
    reasoning_output_tokens = getattr(candidate, "reasoning_output_tokens", None)
    total_tokens = getattr(candidate, "total_tokens", None)

    values = (
        cached_input_tokens,
        input_tokens,
        output_tokens,
        reasoning_output_tokens,
        total_tokens,
    )
    if any(value is None for value in values):
        return None

    return UsageBreakdown(
        cached_input_tokens=int(cached_input_tokens),
        input_tokens=int(input_tokens),
        output_tokens=int(output_tokens),
        reasoning_output_tokens=int(reasoning_output_tokens),
        total_tokens=int(total_tokens),
    )


def extract_worker_usage(result: object) -> WorkerUsage | None:
    usage = getattr(result, "usage", None)
    if usage is None:
        return None

    last = _extract_usage_breakdown(getattr(usage, "last", None))
    total = _extract_usage_breakdown(getattr(usage, "total", None))
    if last is None or total is None:
        return None

    model_context_window = getattr(usage, "model_context_window", None)
    return WorkerUsage(
        source="sdk_structured",
        last=last,
        total=total,
        model_context_window=int(model_context_window) if model_context_window is not None else None,
    )


def build_thread_start_options(request: WorkerRequest) -> dict[str, object]:
    options: dict[str, object] = {
        "cwd": str(request.cwd),
        "model": request.model,
        "sandbox": request.sandbox,
        "approval_mode": request.approval_mode,
    }
    if request.reasoning_effort is not None:
        options["config"] = {"model_reasoning_effort": request.reasoning_effort}
    return options


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
        usage=extract_worker_usage(result),
        stdout_text=None,
        stderr_text=None,
    )


class CodexSdkWorker:
    def __init__(self, codex: CodexLike) -> None:
        self._codex = codex

    def run(self, request: WorkerRequest) -> WorkerResult:
        return execute_request(request, self._codex)
