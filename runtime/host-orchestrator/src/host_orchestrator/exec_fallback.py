from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
from typing import Protocol

from openai_codex import ApprovalMode, Sandbox

from host_orchestrator.process_guard import run_guarded_process
from host_orchestrator.worker import WorkerRequest, WorkerResult


@dataclass(frozen=True)
class CommandResult:
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str


class CommandExecutor(Protocol):
    def run(self, argv: list[str], cwd: Path) -> CommandResult: ...


class SubprocessCommandExecutor:
    def __init__(self, *, timeout_seconds: float | None = None) -> None:
        self._timeout_seconds = timeout_seconds

    def run(self, argv: list[str], cwd: Path) -> CommandResult:
        completed = run_guarded_process(
            argv,
            cwd=cwd,
            timeout_seconds=self._timeout_seconds,
        )
        return CommandResult(
            argv=list(argv),
            returncode=int(completed.returncode),
            stdout=str(completed.stdout),
            stderr=str(completed.stderr),
        )


def sandbox_to_cli(sandbox: Sandbox) -> str:
    return str(sandbox.value)


def approval_mode_to_cli_policy(approval_mode: ApprovalMode) -> str:
    if approval_mode is ApprovalMode.deny_all:
        return "never"
    if approval_mode is ApprovalMode.auto_review:
        return "on-request"
    raise ValueError(f"Unsupported approval mode for codex exec fallback: {approval_mode}")


def build_exec_argv(request: WorkerRequest, output_last_message_path: Path) -> list[str]:
    return [
        "codex",
        "exec",
        "--json",
        "-C",
        str(request.cwd),
        "-m",
        request.model,
        "-s",
        sandbox_to_cli(request.sandbox),
        "-c",
        f'approval_policy="{approval_mode_to_cli_policy(request.approval_mode)}"',
        "--output-last-message",
        str(output_last_message_path),
        request.prompt,
    ]


class CodexExecFallbackWorker:
    def __init__(self, executor: CommandExecutor | None = None) -> None:
        self._executor = executor or SubprocessCommandExecutor()

    def run(self, request: WorkerRequest) -> WorkerResult:
        with tempfile.TemporaryDirectory(prefix="host-orchestrator-exec-") as temp_dir:
            output_path = Path(temp_dir) / "last-message.txt"
            command = build_exec_argv(request, output_path)
            result = self._executor.run(command, request.cwd)
            if result.returncode != 0:
                raise RuntimeError(
                    "codex exec fallback failed "
                    f"(exit={result.returncode}): {result.stderr or result.stdout}"
                )

            final_response = output_path.read_text(encoding="utf-8") if output_path.exists() else None
            return WorkerResult(
                final_response=final_response,
                raw_result=result,
                stdout_text=result.stdout,
                stderr_text=result.stderr,
            )
