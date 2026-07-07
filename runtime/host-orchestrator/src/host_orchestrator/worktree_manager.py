from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

from host_orchestrator.canonical_task import CanonicalTask
from host_orchestrator.path_guard import PathGuardError, validate_task_paths, validate_worker_workspace
from host_orchestrator.paths import RuntimeLayout


@dataclass(frozen=True)
class PreparedWorkspace:
    workspace_root: Path
    cleanup_status: str
    created_new_worktree: bool
    managed_by_runtime: bool


@dataclass(frozen=True)
class CleanupOutcome:
    cleanup_status: str
    cleanup_owner: str
    next_action: str | None
    payload: dict[str, object]


def declared_cleanup_status(task: CanonicalTask) -> str:
    return "inline_only" if task.worktree_path.strip() in {".", "./"} else "deferred"


def prepare_task_workspace(
    *,
    task: CanonicalTask,
    layout: RuntimeLayout,
    workspace_root: Path,
) -> PreparedWorkspace:
    repo_root = layout.repo_root.resolve(strict=False)
    declared_worktree_root = validate_task_paths(task=task, repo_root=repo_root)
    actual_workspace_root = workspace_root.resolve(strict=False)

    if task.worktree_path.strip() in {".", "./"}:
        validated_root = validate_worker_workspace(
            task=task,
            repo_root=repo_root,
            workspace_root=actual_workspace_root,
        )
        return PreparedWorkspace(
            workspace_root=validated_root,
            cleanup_status="inline_only",
            created_new_worktree=False,
            managed_by_runtime=False,
        )

    if actual_workspace_root == repo_root:
        created_new_worktree = _ensure_worktree(
            repo_root=repo_root,
            target_root=declared_worktree_root,
            branch_name=task.branch_name,
            base_branch=task.base_branch,
        )
        validated_root = validate_worker_workspace(
            task=task,
            repo_root=repo_root,
            workspace_root=declared_worktree_root,
        )
        return PreparedWorkspace(
            workspace_root=validated_root,
            cleanup_status="deferred",
            created_new_worktree=created_new_worktree,
            managed_by_runtime=True,
        )

    validated_root = validate_worker_workspace(
        task=task,
        repo_root=repo_root,
        workspace_root=actual_workspace_root,
    )
    return PreparedWorkspace(
        workspace_root=validated_root,
        cleanup_status="deferred",
        created_new_worktree=False,
        managed_by_runtime=False,
    )


def finalize_task_workspace_cleanup(
    *,
    task: CanonicalTask,
    repo_root: Path,
    prepared_workspace: PreparedWorkspace,
    result_status: str,
    handoff_required: bool,
    current_next_action: str,
) -> CleanupOutcome:
    workspace_root = prepared_workspace.workspace_root.resolve(strict=False)
    base_payload: dict[str, object] = {
        "workspace_root": str(workspace_root),
        "branch_name": task.branch_name,
        "worktree_path": task.worktree_path,
        "managed_by_runtime": prepared_workspace.managed_by_runtime,
    }

    if task.worktree_path.strip() in {".", "./"}:
        return CleanupOutcome(
            cleanup_status="inline_only",
            cleanup_owner="inline_execution",
            next_action=None,
            payload={
                **base_payload,
                "cleanup_status": "inline_only",
                "cleanup_owner": "inline_execution",
                "worktree_removed": False,
                "reason": "inline task does not use linked worktree cleanup",
            },
        )

    if not prepared_workspace.managed_by_runtime:
        return _deferred_cleanup(
            base_payload=base_payload,
            reason="runtime did not create or adopt this isolated worktree, so cleanup stays with the operator",
            current_next_action=current_next_action,
        )

    if handoff_required:
        return _deferred_cleanup(
            base_payload=base_payload,
            reason="runtime kept the managed worktree because review or operator handoff is still required",
            current_next_action=current_next_action,
        )

    if result_status != "succeeded":
        return _deferred_cleanup(
            base_payload=base_payload,
            reason=f"runtime kept the managed worktree because result status is {result_status}",
            current_next_action=current_next_action,
            fallback_next_action="inspect failed runtime-managed worktree before manual cleanup",
        )

    if not workspace_root.exists():
        return CleanupOutcome(
            cleanup_status="cleaned",
            cleanup_owner="runtime",
            next_action=None,
            payload={
                **base_payload,
                "cleanup_status": "cleaned",
                "cleanup_owner": "runtime",
                "worktree_removed": True,
                "reason": "managed worktree was already absent at cleanup time",
            },
        )

    dirty_entries = _git_status_entries(workspace_root)
    if dirty_entries:
        return _deferred_cleanup(
            base_payload=base_payload,
            reason="runtime kept the managed worktree because it still has uncommitted changes",
            current_next_action=current_next_action,
            fallback_next_action="manual cleanup required for dirty runtime-managed worktree",
            dirty_entries=dirty_entries,
        )

    try:
        _run_git(repo_root, "worktree", "remove", str(workspace_root))
    except PathGuardError as exc:
        return CleanupOutcome(
            cleanup_status="cleanup_failed",
            cleanup_owner="operator",
            next_action=_manual_cleanup_next_action(
                current_next_action,
                "manual cleanup required after runtime worktree removal failure",
            ),
            payload={
                **base_payload,
                "cleanup_status": "cleanup_failed",
                "cleanup_owner": "operator",
                "worktree_removed": False,
                "reason": str(exc),
            },
        )

    return CleanupOutcome(
        cleanup_status="cleaned",
        cleanup_owner="runtime",
        next_action=None,
        payload={
            **base_payload,
            "cleanup_status": "cleaned",
            "cleanup_owner": "runtime",
            "worktree_removed": True,
            "reason": "runtime removed a clean managed worktree",
        },
    )


def _ensure_worktree(
    *,
    repo_root: Path,
    target_root: Path,
    branch_name: str,
    base_branch: str,
) -> bool:
    if target_root.exists():
        if not target_root.is_dir():
            raise PathGuardError(
                "declared worktree_path already exists but is not a directory: "
                f"{target_root}"
            )

        actual_root = Path(_run_git(target_root, "rev-parse", "--show-toplevel")).resolve(strict=False)
        if actual_root != target_root.resolve(strict=False):
            raise PathGuardError(
                "declared worktree_path already exists but is not a valid linked worktree root: "
                f"{target_root}"
            )

        actual_branch = _run_git(target_root, "branch", "--show-current")
        if actual_branch != branch_name:
            raise PathGuardError(
                "declared worktree_path already exists on a different branch: "
                f"expected {branch_name}, got {actual_branch or '(detached)'}"
            )
        return False

    target_root.parent.mkdir(parents=True, exist_ok=True)
    if _branch_exists(repo_root, branch_name):
        _run_git(repo_root, "worktree", "add", str(target_root), branch_name)
    else:
        if not _branch_exists(repo_root, base_branch):
            raise PathGuardError(
                "base_branch does not exist locally for worktree creation: "
                f"{base_branch}"
            )
        _run_git(
            repo_root,
            "worktree",
            "add",
            "-b",
            branch_name,
            str(target_root),
            base_branch,
        )
    return True


def _branch_exists(repo_root: Path, branch_name: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.returncode == 0


def _deferred_cleanup(
    *,
    base_payload: dict[str, object],
    reason: str,
    current_next_action: str,
    fallback_next_action: str | None = None,
    dirty_entries: list[str] | None = None,
) -> CleanupOutcome:
    payload: dict[str, object] = {
        **base_payload,
        "cleanup_status": "deferred",
        "cleanup_owner": "operator",
        "worktree_removed": False,
        "reason": reason,
    }
    if dirty_entries:
        payload["dirty_entries"] = dirty_entries
    return CleanupOutcome(
        cleanup_status="deferred",
        cleanup_owner="operator",
        next_action=_manual_cleanup_next_action(current_next_action, fallback_next_action),
        payload=payload,
    )


def _manual_cleanup_next_action(
    current_next_action: str,
    fallback_next_action: str | None,
) -> str | None:
    if not fallback_next_action:
        return None
    if current_next_action and current_next_action != "none":
        return None
    return fallback_next_action


def _git_status_entries(workspace_root: Path) -> list[str]:
    stdout = _run_git(workspace_root, "status", "--short")
    if not stdout:
        return []
    return [line for line in stdout.splitlines() if line.strip()]


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
        raise PathGuardError("git is required for runtime worktree management") from exc

    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        raise PathGuardError(
            "git worktree manager command failed: "
            f"{' '.join(args)} ({stderr or f'exit_code={completed.returncode}'})"
        )
    return (completed.stdout or "").strip()
