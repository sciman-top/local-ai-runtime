from __future__ import annotations

import json
from pathlib import Path
import sqlite3

from host_orchestrator import db
from host_orchestrator.cli import main as cli_main
from host_orchestrator.dispatch_state import write_dispatch_state
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.task_lifecycle import (
    cancel_task,
    reconcile_stale_tasks,
    record_review_disposition,
    resume_task,
    retry_task,
)
import pytest


def _seed_repo(tmp_path: Path) -> tuple[Path, RuntimeLayout]:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    layout = RuntimeLayout.from_repo_root(repo_root)
    db.initialize_control_plane(layout.control_plane_db)
    return repo_root, layout


def _seed_dispatch_and_runtime_task(
    *,
    layout: RuntimeLayout,
    task_id: str,
    run_id: str,
    state: str,
    attempt: int = 1,
    next_action: str = "wait_for_worker_result",
    status_reason: str = "worker executing within graded autonomy boundary",
    started_at: str = "2026-07-07T01:00:00Z",
    updated_at: str = "2026-07-07T01:05:00Z",
    heartbeat_at: str = "2026-07-07T01:05:00Z",
    stale_after: str = "2026-07-07T01:30:00Z",
) -> Path:
    dispatch_state_path = layout.runs_root / run_id / task_id / "dispatch_state.json"
    dispatch_state_path.parent.mkdir(parents=True, exist_ok=True)
    write_dispatch_state(
        dispatch_state_path,
        {
            "run_id": run_id,
            "attempt": attempt,
            "task_id": task_id,
            "agent_role": "worker",
            "model_policy": {
                "model": "gpt-5.4",
                "reasoning_effort": "high",
                "rationale": "test fixture",
            },
            "repo_root": str(layout.repo_root),
            "target_repo": "local-ai-dev-orchestrator",
            "branch_name": "codex/test-lifecycle",
            "worktree_path": ".",
            "workspace_root": str(layout.repo_root),
            "allowed_paths": ["runtime/host-orchestrator/**"],
            "forbidden_paths": [".env", ".env.*", ".git/config"],
            "source_ref": f"tests/{task_id}.json",
            "lease_owner": "host-local-default",
            "started_at": started_at,
            "updated_at": updated_at,
            "heartbeat_at": heartbeat_at,
            "stale_after": stale_after,
            "execution_lane": "host_local",
            "worker_profile": "local_maint",
            "status": state,
            "status_reason": status_reason,
            "next_action": next_action,
            "cleanup_status": "inline_only",
            "cleanup_owner": "inline_execution",
        },
    )
    db.upsert_runtime_task(
        layout.control_plane_db,
        task_id=task_id,
        run_id=run_id,
        attempt=attempt,
        state=state,
        state_reason=status_reason,
        execution_lane="host_local",
        worker_profile="local_maint",
        next_action=next_action,
        cleanup_status="inline_only",
        cleanup_owner="inline_execution",
        created_at=started_at,
        updated_at=updated_at,
        dispatch_state_path=str(dispatch_state_path.relative_to(layout.repo_root)).replace("\\", "/"),
    )
    return dispatch_state_path


def test_reconcile_stale_tasks_marks_expired_running_dispatch_state_as_stale(tmp_path: Path) -> None:
    _, layout = _seed_repo(tmp_path)
    task_id = "TASK-20260707-stale"
    dispatch_state_path = _seed_dispatch_and_runtime_task(
        layout=layout,
        task_id=task_id,
        run_id="stale-run",
        state="running",
    )

    reconciled = reconcile_stale_tasks(layout, as_of="2026-07-07T00:45:00-01:00")

    assert reconciled == [task_id]
    dispatch_payload = json.loads(dispatch_state_path.read_text(encoding="utf-8"))
    assert dispatch_payload["status"] == "stale"
    assert dispatch_payload["next_action"] == "inspect_stale_run_and_resume"
    assert dispatch_payload["status_reason"] == "stale heartbeat detected at 2026-07-07T01:45:00Z"

    with sqlite3.connect(layout.control_plane_db) as connection:
        runtime_task = connection.execute(
            "SELECT state, next_action, state_reason FROM runtime_tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        events = connection.execute(
            "SELECT event_type FROM events ORDER BY created_at"
        ).fetchall()

    assert runtime_task == (
        "stale",
        "inspect_stale_run_and_resume",
        "stale heartbeat detected at 2026-07-07T01:45:00Z",
    )
    assert [event_type for (event_type,) in events] == ["task_stale"]


def test_cancel_resume_and_retry_keep_dispatch_state_and_runtime_task_in_sync(tmp_path: Path) -> None:
    _, layout = _seed_repo(tmp_path)
    task_id = "TASK-20260707-cancel-resume-retry"
    dispatch_state_path = _seed_dispatch_and_runtime_task(
        layout=layout,
        task_id=task_id,
        run_id="retry-run",
        state="waiting_handoff",
        next_action="planner handoff required before worker execution",
        status_reason="planner handoff required: depends_on=TASK-UPSTREAM",
    )
    db.acquire_lease(
        layout.control_plane_db,
        task_id=task_id,
        worker_id="host-local-default",
        acquired_at="2026-07-07T01:00:00Z",
        expires_at="2026-07-07T02:30:00Z",
        lease_token="lease-cancel",
    )

    cancel_task(
        layout,
        task_id=task_id,
        cancelled_at="2026-07-07T02:00:00Z",
        reason="operator requested stop",
    )
    cancelled_payload = json.loads(dispatch_state_path.read_text(encoding="utf-8"))
    assert cancelled_payload["status"] == "cancelled"
    assert cancelled_payload["next_action"] == "operator may resume or retry"
    assert cancelled_payload["status_reason"] == "operator requested stop"
    with sqlite3.connect(layout.control_plane_db) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM leases WHERE task_id = ?",
            (task_id,),
        ).fetchone() == (0,)

    db.acquire_lease(
        layout.control_plane_db,
        task_id=task_id,
        worker_id="host-local-default",
        acquired_at="2026-07-07T02:01:00Z",
        expires_at="2026-07-07T02:31:00Z",
        lease_token="lease-resume",
    )

    resume_task(
        layout,
        task_id=task_id,
        resumed_at="2026-07-07T02:10:00Z",
        resume_point="handoff",
        reason="operator resumed after triage",
    )
    resumed_payload = json.loads(dispatch_state_path.read_text(encoding="utf-8"))
    assert resumed_payload["status"] == "resumed"
    assert resumed_payload["resume_point"] == "handoff"
    assert resumed_payload["next_action"] == "resume_from_handoff"
    assert resumed_payload["status_reason"] == "operator resumed after triage"
    assert resumed_payload["attempt"] == 1
    assert resumed_payload["heartbeat_at"] == "2026-07-07T02:10:00Z"
    assert resumed_payload["stale_after"] == "2026-07-07T02:40:00Z"
    with sqlite3.connect(layout.control_plane_db) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM leases WHERE task_id = ?",
            (task_id,),
        ).fetchone() == (0,)

    db.acquire_lease(
        layout.control_plane_db,
        task_id=task_id,
        worker_id="host-local-default",
        acquired_at="2026-07-07T02:11:00Z",
        expires_at="2026-07-07T02:41:00Z",
        lease_token="lease-retry",
    )

    retry_task(
        layout,
        task_id=task_id,
        retried_at="2026-07-07T02:20:00Z",
        retry_rewind="worker_execution",
        reason="retry after workspace repair",
    )
    retried_payload = json.loads(dispatch_state_path.read_text(encoding="utf-8"))
    assert retried_payload["status"] == "resumed"
    assert retried_payload["attempt"] == 2
    assert retried_payload["resume_point"] == "worker_execution"
    assert retried_payload["retry_rewind"] == "worker_execution"
    assert retried_payload["next_action"] == "retry_from_worker_execution"
    assert retried_payload["status_reason"] == "retry after workspace repair"
    assert retried_payload["heartbeat_at"] == "2026-07-07T02:20:00Z"
    assert retried_payload["stale_after"] == "2026-07-07T02:50:00Z"

    with sqlite3.connect(layout.control_plane_db) as connection:
        runtime_task = connection.execute(
            "SELECT state, attempt, next_action, state_reason FROM runtime_tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        events = connection.execute(
            "SELECT event_type FROM events ORDER BY created_at"
        ).fetchall()
        assert connection.execute(
            "SELECT COUNT(*) FROM leases WHERE task_id = ?",
            (task_id,),
        ).fetchone() == (0,)

    assert runtime_task == (
        "resumed",
        2,
        "retry_from_worker_execution",
        "retry after workspace repair",
    )
    assert [event_type for (event_type,) in events] == [
        "task_cancelled",
        "task_resumed",
        "task_retry_requested",
    ]


def test_review_disposition_closes_or_requeues_needs_review_tasks(tmp_path: Path) -> None:
    _, layout = _seed_repo(tmp_path)

    approve_task_id = "TASK-20260708-review-approve"
    approve_dispatch_path = _seed_dispatch_and_runtime_task(
        layout=layout,
        task_id=approve_task_id,
        run_id="review-approve-run",
        state="needs_review",
        next_action="heterogeneous review required before downstream use",
        status_reason="risk_level=medium",
    )
    db.acquire_lease(
        layout.control_plane_db,
        task_id=approve_task_id,
        worker_id="host-local-default",
        acquired_at="2026-07-08T01:00:00Z",
        expires_at="2026-07-08T01:30:00Z",
        lease_token="lease-review-approve",
    )

    approve_payload = record_review_disposition(
        layout,
        task_id=approve_task_id,
        disposition="approve",
        disposition_at="2026-07-08T01:10:00Z",
        reason="operator approved repo-side review receipt",
    )

    assert approve_payload["status"] == "completed"
    assert approve_payload["review_disposition"] == "approve"
    assert approve_payload["review_disposition_at"] == "2026-07-08T01:10:00Z"
    assert approve_payload["next_action"] == "repo-side review disposition approved; live acceptance still pending"
    assert json.loads(approve_dispatch_path.read_text(encoding="utf-8"))["status"] == "completed"

    revise_task_id = "TASK-20260708-review-revise"
    revise_dispatch_path = _seed_dispatch_and_runtime_task(
        layout=layout,
        task_id=revise_task_id,
        run_id="review-revise-run",
        state="needs_review",
        attempt=2,
        next_action="heterogeneous review required before downstream use",
        status_reason="review requested changes",
    )
    revise_payload = record_review_disposition(
        layout,
        task_id=revise_task_id,
        disposition="revise",
        disposition_at="2026-07-08T01:20:00Z",
        reason="review requested a worker rework pass",
    )

    assert revise_payload["status"] == "resumed"
    assert revise_payload["attempt"] == 3
    assert revise_payload["review_disposition"] == "revise"
    assert revise_payload["resume_point"] == "worker_execution"
    assert revise_payload["retry_rewind"] == "worker_execution"
    assert revise_payload["next_action"] == "retry_from_worker_execution"
    assert json.loads(revise_dispatch_path.read_text(encoding="utf-8"))["attempt"] == 3

    reject_task_id = "TASK-20260708-review-reject"
    reject_dispatch_path = _seed_dispatch_and_runtime_task(
        layout=layout,
        task_id=reject_task_id,
        run_id="review-reject-run",
        state="needs_review",
        next_action="heterogeneous review required before downstream use",
        status_reason="review found blocking issue",
    )
    reject_payload = record_review_disposition(
        layout,
        task_id=reject_task_id,
        disposition="reject",
        disposition_at="2026-07-08T01:30:00Z",
        reason="review rejected downstream use",
    )

    assert reject_payload["status"] == "cancelled"
    assert reject_payload["review_disposition"] == "reject"
    assert reject_payload["next_action"] == "operator may resume or retry"
    assert json.loads(reject_dispatch_path.read_text(encoding="utf-8"))["status"] == "cancelled"

    with sqlite3.connect(layout.control_plane_db) as connection:
        runtime_rows = connection.execute(
            "SELECT task_id, state, attempt, next_action FROM runtime_tasks ORDER BY task_id"
        ).fetchall()
        event_types = [
            event_type
            for (event_type,) in connection.execute(
                "SELECT event_type FROM events ORDER BY created_at"
            ).fetchall()
        ]
        assert connection.execute(
            "SELECT COUNT(*) FROM leases WHERE task_id = ?",
            (approve_task_id,),
        ).fetchone() == (0,)

    assert runtime_rows == [
        (
            approve_task_id,
            "completed",
            1,
            "repo-side review disposition approved; live acceptance still pending",
        ),
        (reject_task_id, "cancelled", 1, "operator may resume or retry"),
        (revise_task_id, "resumed", 3, "retry_from_worker_execution"),
    ]
    assert event_types == [
        "task_review_approved",
        "task_review_revision_requested",
        "task_review_rejected",
    ]


def test_review_disposition_requires_needs_review_state(tmp_path: Path) -> None:
    _, layout = _seed_repo(tmp_path)
    task_id = "TASK-20260708-review-disposition-invalid"
    _seed_dispatch_and_runtime_task(
        layout=layout,
        task_id=task_id,
        run_id="review-invalid-run",
        state="running",
    )

    with pytest.raises(ValueError, match="can only be recorded for needs_review"):
        record_review_disposition(
            layout,
            task_id=task_id,
            disposition="approve",
            disposition_at="2026-07-08T01:40:00Z",
            reason="invalid state",
        )


def test_cli_cancel_task_updates_runtime_state(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_id = "TASK-20260707-cli-cancel"
    dispatch_state_path = _seed_dispatch_and_runtime_task(
        layout=layout,
        task_id=task_id,
        run_id="cli-cancel-run",
        state="running",
    )

    exit_code = cli_main(
        [
            "--repo-root",
            str(repo_root),
            "--cancel-task",
            task_id,
            "--at",
            "2026-07-07T03:00:00Z",
            "--reason",
            "cli cancel request",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["status"] == "cancelled"
    assert payload["next_action"] == "operator may resume or retry"
    assert payload["status_reason"] == "cli cancel request"
    dispatch_payload = json.loads(dispatch_state_path.read_text(encoding="utf-8"))
    assert dispatch_payload["status"] == "cancelled"


def test_cli_record_review_disposition_requeues_for_revision(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_id = "TASK-20260708-cli-review-disposition"
    dispatch_state_path = _seed_dispatch_and_runtime_task(
        layout=layout,
        task_id=task_id,
        run_id="cli-review-disposition-run",
        state="needs_review",
        next_action="heterogeneous review required before downstream use",
    )

    exit_code = cli_main(
        [
            "--repo-root",
            str(repo_root),
            "--record-review-disposition",
            task_id,
            "--review-disposition",
            "revise",
            "--at",
            "2026-07-08T02:00:00Z",
            "--reason",
            "cli reviewer requested rework",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["status"] == "resumed"
    assert payload["attempt"] == 2
    assert payload["review_disposition"] == "revise"
    assert payload["next_action"] == "retry_from_worker_execution"
    dispatch_payload = json.loads(dispatch_state_path.read_text(encoding="utf-8"))
    assert dispatch_payload["retry_rewind"] == "worker_execution"
