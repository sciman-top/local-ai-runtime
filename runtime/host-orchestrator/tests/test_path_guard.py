from __future__ import annotations

import json
from pathlib import Path
import shutil
import sqlite3
import subprocess

import pytest

from host_orchestrator.canonical_task import write_task
from host_orchestrator.host_local import HostLocalConfig, HostLocalRunner
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.worker import WorkerRequest, WorkerResult

from support import canonical_task_payload, copy_runtime_config


def _init_git_repo(repo_root: Path) -> None:
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Codex Test"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "codex-test@example.com"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "add", "."],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "test: seed repo"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


def _add_worktree(repo_root: Path, worktree_path: Path, branch_name: str) -> Path:
    subprocess.run(
        ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return worktree_path


def _run_git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _seed_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    copy_runtime_config(repo_root)
    _init_git_repo(repo_root)
    return repo_root


def test_host_local_runner_rejects_parent_escape_in_allowed_paths(tmp_path: Path) -> None:
    from host_orchestrator.path_guard import PathGuardError

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    copy_runtime_config(repo_root)

    task_id = "TASK-20260707-path-escape"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = canonical_task_payload(task_id)
    payload["risk_level"] = "low"
    payload["write_access"] = False
    payload["allowed_paths"] = ["../secrets/**"]
    write_task(task_path, payload)

    class UnexpectedWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            raise AssertionError("path guard should fail before worker execution")

    layout = RuntimeLayout.from_repo_root(repo_root)
    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=layout,
            run_id="path-escape-test",
            worker_id="path-escape-worker",
        ),
        UnexpectedWorker(),
    )

    with pytest.raises(PathGuardError, match="allowed_paths"):
        runner.run_task(task_path)

    with sqlite3.connect(layout.control_plane_db) as connection:
        runtime_task = connection.execute(
            "SELECT state, result_path FROM runtime_tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        events = connection.execute(
            "SELECT event_type, payload_json FROM events ORDER BY created_at"
        ).fetchall()

    assert runtime_task == ("failed", None)
    assert [event_type for (event_type, _) in events] == ["task_started", "task_failed"]
    failed_payload = json.loads(events[1][1])
    assert failed_payload["error_type"] == "PathGuardError"
    assert "allowed_paths" in failed_payload["error_message"]


def test_host_local_runner_materializes_declared_worktree_from_repo_root(tmp_path: Path) -> None:
    repo_root = _seed_repo(tmp_path)
    managed_worktree_root = repo_root / ".worktrees" / "worktree-mismatch"

    task_id = "TASK-20260707-worktree-mismatch"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = canonical_task_payload(task_id)
    payload["risk_level"] = "low"
    payload["write_access"] = False
    payload["branch_name"] = "codex/worktree-mismatch"
    payload["worktree_path"] = ".worktrees/worktree-mismatch"
    payload["allowed_paths"] = ["runtime/host-orchestrator/**"]
    payload["verification_commands"]["test"] = (
        "python -c \"from pathlib import Path; print(Path.cwd().name)\""
    )
    payload["verification_commands"]["contract"] = (
        "python -c \"from pathlib import Path; print(Path.cwd().name)\""
    )
    write_task(task_path, payload)

    class RecordingWorker:
        def __init__(self) -> None:
            self.requests: list[WorkerRequest] = []

        def run(self, request: WorkerRequest) -> WorkerResult:
            self.requests.append(request)
            return WorkerResult(
                final_response="WORKTREE_MANAGER_OK",
                raw_result={"kind": "fake"},
            )

    layout = RuntimeLayout.from_repo_root(repo_root)
    worker = RecordingWorker()
    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=layout,
            run_id="worktree-mismatch-test",
            worker_id="worktree-mismatch-worker",
        ),
        worker,
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    verification_payload = json.loads((result_path.parent / "verification_summary.json").read_text(encoding="utf-8"))

    assert not managed_worktree_root.exists()
    assert [request.cwd for request in worker.requests] == [managed_worktree_root]
    assert verification_payload["commands_run"][3]["stdout"].strip() == "worktree-mismatch"
    assert verification_payload["commands_run"][4]["stdout"].strip() == "worktree-mismatch"
    assert result_payload["cleanup_status"] == "cleaned"

    with sqlite3.connect(layout.control_plane_db) as connection:
        events = connection.execute(
            "SELECT event_type, payload_json FROM events ORDER BY created_at"
        ).fetchall()

    event_types = [event_type for (event_type, _) in events]
    assert len(event_types) == 4
    assert event_types.count("task_started") == 1
    assert event_types.count("worktree_prepared") == 1
    assert event_types.count("worktree_cleanup") == 1
    assert event_types.count("task_completed") == 1
    prepared_payload = next(
        json.loads(payload_json)
        for (event_type, payload_json) in events
        if event_type == "worktree_prepared"
    )
    assert prepared_payload["created_new_worktree"] is True
    assert prepared_payload["branch_name"] == "codex/worktree-mismatch"
    assert prepared_payload["cleanup_status"] == "deferred"
    cleanup_payload = next(
        json.loads(payload_json)
        for (event_type, payload_json) in events
        if event_type == "worktree_cleanup"
    )
    assert cleanup_payload["cleanup_status"] == "cleaned"
    assert cleanup_payload["cleanup_owner"] == "runtime"
    assert cleanup_payload["worktree_removed"] is True


def test_host_local_runner_rejects_branch_mismatch_for_declared_worktree(tmp_path: Path) -> None:
    from host_orchestrator.path_guard import PathGuardError

    repo_root = _seed_repo(tmp_path)
    worktree_root = _add_worktree(
        repo_root,
        repo_root / ".worktrees" / "branch-mismatch",
        "codex/actual-branch",
    )

    task_id = "TASK-20260707-branch-mismatch"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = canonical_task_payload(task_id)
    payload["risk_level"] = "low"
    payload["write_access"] = False
    payload["branch_name"] = "codex/expected-branch"
    payload["worktree_path"] = ".worktrees/branch-mismatch"
    write_task(task_path, payload)

    class UnexpectedWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            raise AssertionError("branch guard should fail before worker execution")

    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=worktree_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            run_id="branch-mismatch-test",
            worker_id="branch-mismatch-worker",
        ),
        UnexpectedWorker(),
    )

    with pytest.raises(PathGuardError, match="branch"):
        runner.run_task(task_path)


def test_host_local_runner_uses_declared_worktree_as_worker_cwd(tmp_path: Path) -> None:
    repo_root = _seed_repo(tmp_path)
    worktree_root = _add_worktree(
        repo_root,
        repo_root / ".worktrees" / "guarded-success",
        "codex/guarded-success",
    )

    task_id = "TASK-20260707-worktree-success"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = canonical_task_payload(task_id)
    payload["risk_level"] = "low"
    payload["write_access"] = False
    payload["branch_name"] = "codex/guarded-success"
    payload["worktree_path"] = ".worktrees/guarded-success"
    payload["verification_commands"]["test"] = (
        "python -c \"from pathlib import Path; print(Path.cwd().name)\""
    )
    payload["verification_commands"]["contract"] = (
        "python -c \"from pathlib import Path; print(Path.cwd().name)\""
    )
    write_task(task_path, payload)

    class RecordingWorker:
        def __init__(self) -> None:
            self.requests: list[WorkerRequest] = []

        def run(self, request: WorkerRequest) -> WorkerResult:
            self.requests.append(request)
            return WorkerResult(
                final_response="WORKTREE_GUARD_OK",
                raw_result={"kind": "fake"},
            )

    worker = RecordingWorker()
    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=worktree_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            run_id="worktree-success-test",
            worker_id="worktree-success-worker",
        ),
        worker,
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    verification_payload = json.loads((result_path.parent / "verification_summary.json").read_text(encoding="utf-8"))

    assert [request.cwd for request in worker.requests] == [worktree_root]
    assert verification_payload["commands_run"][3]["stdout"].strip() == "guarded-success"
    assert verification_payload["commands_run"][4]["stdout"].strip() == "guarded-success"
    assert result_payload["cleanup_status"] == "deferred"


def test_host_local_runner_keeps_dirty_runtime_managed_worktree(tmp_path: Path) -> None:
    repo_root = _seed_repo(tmp_path)
    managed_worktree_root = repo_root / ".worktrees" / "dirty-managed"

    task_id = "TASK-20260707-dirty-managed"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = canonical_task_payload(task_id)
    payload["risk_level"] = "low"
    payload["write_access"] = False
    payload["branch_name"] = "codex/dirty-managed"
    payload["worktree_path"] = ".worktrees/dirty-managed"
    payload["allowed_paths"] = ["runtime/host-orchestrator/**"]
    write_task(task_path, payload)

    class DirtyWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            dirty_file = request.cwd / "runtime" / "host-orchestrator" / "dirty-generated.txt"
            dirty_file.parent.mkdir(parents=True, exist_ok=True)
            dirty_file.write_text("DIRTY_WORKTREE\n", encoding="utf-8")
            return WorkerResult(
                final_response="DIRTY_MANAGED_OK",
                raw_result={"kind": "fake"},
            )

    layout = RuntimeLayout.from_repo_root(repo_root)
    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=layout,
            run_id="dirty-managed-test",
            worker_id="dirty-managed-worker",
        ),
        DirtyWorker(),
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert managed_worktree_root.exists()
    assert result_payload["status"] == "succeeded"
    assert result_payload["cleanup_status"] == "deferred"
    assert result_payload["next_action"] == "manual cleanup required for dirty runtime-managed worktree"

    with sqlite3.connect(layout.control_plane_db) as connection:
        events = connection.execute(
            "SELECT event_type, payload_json FROM events ORDER BY created_at"
        ).fetchall()

    event_types = [event_type for (event_type, _) in events]
    assert len(event_types) == 4
    assert event_types.count("task_started") == 1
    assert event_types.count("worktree_prepared") == 1
    assert event_types.count("worktree_cleanup") == 1
    assert event_types.count("task_completed") == 1
    cleanup_payload = next(
        json.loads(payload_json)
        for (event_type, payload_json) in events
        if event_type == "worktree_cleanup"
    )
    assert cleanup_payload["cleanup_status"] == "deferred"
    assert cleanup_payload["cleanup_owner"] == "operator"
    assert cleanup_payload["worktree_removed"] is False
    assert cleanup_payload["dirty_entries"] == ["?? runtime/"]


def test_host_local_runner_keeps_review_pending_managed_worktree(tmp_path: Path) -> None:
    repo_root = _seed_repo(tmp_path)
    managed_worktree_root = repo_root / ".worktrees" / "review-managed"

    task_id = "TASK-20260707-review-managed"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = canonical_task_payload(task_id)
    payload["branch_name"] = "codex/review-managed"
    payload["worktree_path"] = ".worktrees/review-managed"
    write_task(task_path, payload)

    class ReviewWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            return WorkerResult(
                final_response="REVIEW_MANAGED_OK",
                raw_result={"kind": "fake"},
            )

    layout = RuntimeLayout.from_repo_root(repo_root)
    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=layout,
            run_id="review-managed-test",
            worker_id="review-managed-worker",
        ),
        ReviewWorker(),
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert managed_worktree_root.exists()
    assert result_payload["status"] == "needs_review"
    assert result_payload["cleanup_status"] == "deferred"
    assert result_payload["next_action"] == "heterogeneous review required before downstream use"

    with sqlite3.connect(layout.control_plane_db) as connection:
        events = connection.execute(
            "SELECT event_type, payload_json FROM events ORDER BY created_at"
        ).fetchall()

    event_types = [event_type for (event_type, _) in events]
    assert len(event_types) == 4
    assert event_types.count("task_started") == 1
    assert event_types.count("worktree_prepared") == 1
    assert event_types.count("worktree_cleanup") == 1
    assert event_types.count("task_needs_review") == 1
    cleanup_payload = json.loads(events[2][1])
    assert cleanup_payload["cleanup_status"] == "deferred"
    assert cleanup_payload["cleanup_owner"] == "operator"
    assert cleanup_payload["reason"] == (
        "runtime kept the managed worktree because review or operator handoff is still required"
    )


def test_host_local_runner_marks_cleanup_failed_when_worktree_remove_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from host_orchestrator import worktree_manager
    from host_orchestrator.path_guard import PathGuardError

    repo_root = _seed_repo(tmp_path)
    managed_worktree_root = repo_root / ".worktrees" / "cleanup-failure"

    task_id = "TASK-20260707-cleanup-failure"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = canonical_task_payload(task_id)
    payload["risk_level"] = "low"
    payload["write_access"] = False
    payload["branch_name"] = "codex/cleanup-failure"
    payload["worktree_path"] = ".worktrees/cleanup-failure"
    payload["allowed_paths"] = ["runtime/host-orchestrator/**"]
    write_task(task_path, payload)

    original_run_git = worktree_manager._run_git

    def failing_run_git(cwd: Path, *args: str) -> str:
        if args[:2] == ("worktree", "remove"):
            raise PathGuardError("simulated cleanup remove failure")
        return original_run_git(cwd, *args)

    monkeypatch.setattr(worktree_manager, "_run_git", failing_run_git)

    class CleanWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            return WorkerResult(
                final_response="CLEANUP_FAILURE_OK",
                raw_result={"kind": "fake"},
            )

    layout = RuntimeLayout.from_repo_root(repo_root)
    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=layout,
            run_id="cleanup-failure-test",
            worker_id="cleanup-failure-worker",
        ),
        CleanWorker(),
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert managed_worktree_root.exists()
    assert result_payload["cleanup_status"] == "cleanup_failed"
    assert result_payload["next_action"] == "manual cleanup required after runtime worktree removal failure"

    with sqlite3.connect(layout.control_plane_db) as connection:
        events = connection.execute(
            "SELECT event_type, payload_json FROM events ORDER BY created_at"
        ).fetchall()

    cleanup_payload = next(
        json.loads(payload_json)
        for (event_type, payload_json) in events
        if event_type == "worktree_cleanup"
    )
    assert cleanup_payload["cleanup_status"] == "cleanup_failed"
    assert cleanup_payload["reason"] == "simulated cleanup remove failure"
