from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import signal
import subprocess
from typing import Protocol


@dataclass(frozen=True)
class GuardedCommandResult:
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str


class GuardedProcessTimeout(TimeoutError):
    def __init__(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        pid: int,
        stdout: str,
        stderr: str,
    ) -> None:
        self.argv = list(argv)
        self.cwd = cwd
        self.timeout_seconds = timeout_seconds
        self.pid = pid
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(
            f"Process timed out after {timeout_seconds} seconds (pid={pid}): {' '.join(argv)}"
        )


class ProcessTreeKiller(Protocol):
    def kill_tree(self, pid: int) -> None: ...


class SystemProcessTreeKiller:
    def kill_tree(self, pid: int) -> None:
        if pid <= 0:
            return

        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            else:
                os.killpg(os.getpgid(pid), signal.SIGKILL)
        except Exception:
            # Cleanup is best-effort. The caller is already handling a failure path.
            return


def run_guarded_process(
    argv: list[str],
    cwd: Path,
    *,
    timeout_seconds: float | None = None,
    process_tree_killer: ProcessTreeKiller | None = None,
    encoding: str | None = None,
    errors: str | None = None,
) -> GuardedCommandResult:
    killer = process_tree_killer or SystemProcessTreeKiller()
    popen_kwargs: dict[str, object] = {
        "cwd": cwd,
        "text": True,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
    }
    if encoding is not None:
        popen_kwargs["encoding"] = encoding
    if errors is not None:
        popen_kwargs["errors"] = errors
    if os.name == "nt":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        popen_kwargs["start_new_session"] = True

    process = subprocess.Popen(argv, **popen_kwargs)
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        killer.kill_tree(process.pid)
        stdout, stderr = process.communicate()
        raise GuardedProcessTimeout(
            argv=list(argv),
            cwd=cwd,
            timeout_seconds=timeout_seconds or 0.0,
            pid=process.pid,
            stdout=stdout or (exc.stdout or ""),
            stderr=stderr or (exc.stderr or ""),
        ) from exc
    except BaseException:
        killer.kill_tree(process.pid)
        process.communicate()
        raise

    return GuardedCommandResult(
        argv=list(argv),
        returncode=process.returncode,
        stdout=stdout,
        stderr=stderr,
    )
