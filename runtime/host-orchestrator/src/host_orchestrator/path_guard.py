from __future__ import annotations

from pathlib import Path
import subprocess

from host_orchestrator.canonical_task import CanonicalTask


class PathGuardError(ValueError):
    """Raised when task path claims do not match the execution context."""


def validate_task_paths(*, task: CanonicalTask, repo_root: Path) -> Path:
    repo_root_resolved = repo_root.resolve(strict=False)
    _validate_relative_value(task.worktree_path, field="worktree_path")
    expected_worktree_root = (repo_root_resolved / task.worktree_path).resolve(strict=False)
    if not expected_worktree_root.is_relative_to(repo_root_resolved):
        raise PathGuardError(
            "worktree_path must stay under the repository root: "
            f"{task.worktree_path}"
        )

    for field_name, values in (
        ("allowed_paths", task.allowed_paths),
        ("forbidden_paths", task.forbidden_paths),
        ("artifacts_out", task.artifacts_out),
    ):
        for index, value in enumerate(values):
            _validate_relative_value(value, field=f"{field_name}[{index}]")

    return expected_worktree_root


def validate_worker_workspace(
    *,
    task: CanonicalTask,
    repo_root: Path,
    workspace_root: Path,
) -> Path:
    expected_worktree_root = validate_task_paths(task=task, repo_root=repo_root)
    actual_workspace_root = workspace_root.resolve(strict=False)
    if actual_workspace_root != expected_worktree_root:
        raise PathGuardError(
            "workspace_root does not match declared worktree_path: "
            f"expected {expected_worktree_root}, got {actual_workspace_root}"
        )

    if task.worktree_path.strip() not in {".", "./"}:
        git_root = Path(_run_git(workspace_root, "rev-parse", "--show-toplevel"))
        if git_root.resolve(strict=False) != actual_workspace_root:
            raise PathGuardError(
                "git root does not match workspace_root for declared worktree: "
                f"expected {actual_workspace_root}, got {git_root}"
            )

        branch_name = _run_git(workspace_root, "branch", "--show-current")
        if branch_name != task.branch_name:
            raise PathGuardError(
                "git branch does not match declared branch_name: "
                f"expected {task.branch_name}, got {branch_name or '(detached)'}"
            )

    return actual_workspace_root


def _validate_relative_value(value: str, *, field: str) -> None:
    normalized = value.replace("\\", "/").strip()
    candidate = Path(normalized)
    if candidate.is_absolute():
        raise PathGuardError(f"{field} must be repo-relative, not absolute: {value}")

    segments = [segment for segment in normalized.split("/") if segment not in {"", "."}]
    if any(segment == ".." for segment in segments):
        raise PathGuardError(f"{field} must not escape the repo via '..': {value}")


def _run_git(cwd: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(cwd), *args],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError as exc:
        raise PathGuardError("git is required for isolated worktree path guard checks") from exc

    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        raise PathGuardError(
            "git path guard probe failed for isolated worktree: "
            f"{' '.join(args)} ({stderr or f'exit_code={completed.returncode}'})"
        )
    return (completed.stdout or "").strip()
