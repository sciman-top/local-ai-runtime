from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from host_orchestrator.exec_fallback import CommandResult, SubprocessCommandExecutor
from host_orchestrator.process_guard import (
    GuardedCommandResult,
    GuardedProcessTimeout,
    run_guarded_process,
)


def test_run_guarded_process_kills_tree_on_timeout(monkeypatch, tmp_path: Path) -> None:
    class FakeProcess:
        pid = 4321
        returncode = -9

        def __init__(self) -> None:
            self._timed_out = False

        def communicate(self, timeout=None):
            if not self._timed_out:
                self._timed_out = True
                raise subprocess.TimeoutExpired(cmd=["codex"], timeout=timeout)
            return ("partial-stdout", "partial-stderr")

    class RecordingKiller:
        def __init__(self) -> None:
            self.killed_pids: list[int] = []

        def kill_tree(self, pid: int) -> None:
            self.killed_pids.append(pid)

    monkeypatch.setattr(
        "host_orchestrator.process_guard.subprocess.Popen",
        lambda argv, **kwargs: FakeProcess(),
    )

    killer = RecordingKiller()
    with pytest.raises(GuardedProcessTimeout, match="Process timed out"):
        run_guarded_process(
            ["codex", "exec"],
            tmp_path,
            timeout_seconds=0.1,
            process_tree_killer=killer,
        )

    assert killer.killed_pids == [4321]


def test_subprocess_command_executor_uses_process_guard(monkeypatch, tmp_path: Path) -> None:
    observed: dict[str, object] = {}

    def fake_run_guarded_process(argv, cwd, *, timeout_seconds=None):
        observed["argv"] = list(argv)
        observed["cwd"] = cwd
        observed["timeout_seconds"] = timeout_seconds
        return GuardedCommandResult(
            argv=list(argv),
            returncode=0,
            stdout="stdout-ok",
            stderr="",
        )

    monkeypatch.setattr(
        "host_orchestrator.exec_fallback.run_guarded_process",
        fake_run_guarded_process,
    )

    executor = SubprocessCommandExecutor(timeout_seconds=12.5)
    result = executor.run(["codex", "exec", "--json"], tmp_path)

    assert result == CommandResult(
        argv=["codex", "exec", "--json"],
        returncode=0,
        stdout="stdout-ok",
        stderr="",
    )
    assert observed == {
        "argv": ["codex", "exec", "--json"],
        "cwd": tmp_path,
        "timeout_seconds": 12.5,
    }
