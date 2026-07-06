from __future__ import annotations

import sqlite3

import pytest

from host_orchestrator import db


def test_acquire_and_release_lease_round_trip(tmp_path) -> None:
    db_path = tmp_path / "control-plane.db"

    lease_token = db.acquire_lease(
        db_path,
        task_id="TASK-LEASE-001",
        worker_id="worker-1",
        acquired_at="2026-07-06T12:00:00Z",
        expires_at="2026-07-06T12:30:00Z",
    )

    with sqlite3.connect(db_path) as connection:
        lease_row = connection.execute(
            "SELECT task_id, worker_id, lease_token, expires_at FROM leases"
        ).fetchone()

    assert lease_row == (
        "TASK-LEASE-001",
        "worker-1",
        lease_token,
        "2026-07-06T12:30:00Z",
    )
    assert db.release_lease(db_path, lease_token=lease_token) is True

    with sqlite3.connect(db_path) as connection:
        remaining_count = connection.execute("SELECT COUNT(*) FROM leases").fetchone()[0]

    assert remaining_count == 0


def test_acquire_lease_rejects_second_active_claim(tmp_path) -> None:
    db_path = tmp_path / "control-plane.db"
    db.acquire_lease(
        db_path,
        task_id="TASK-LEASE-002",
        worker_id="worker-1",
        acquired_at="2026-07-06T12:00:00Z",
        expires_at="2026-07-06T12:30:00Z",
        lease_token="lease-a",
    )

    with pytest.raises(db.LeaseConflictError, match="Active lease already exists"):
        db.acquire_lease(
            db_path,
            task_id="TASK-LEASE-002",
            worker_id="worker-2",
            acquired_at="2026-07-06T12:05:00Z",
            expires_at="2026-07-06T12:35:00Z",
            lease_token="lease-b",
        )


def test_renew_and_reap_stale_leases(tmp_path) -> None:
    db_path = tmp_path / "control-plane.db"
    lease_token = db.acquire_lease(
        db_path,
        task_id="TASK-LEASE-003",
        worker_id="worker-1",
        acquired_at="2026-07-06T12:00:00Z",
        expires_at="2026-07-06T12:30:00Z",
        lease_token="lease-c",
    )

    db.renew_lease(
        db_path,
        lease_token=lease_token,
        expires_at="2026-07-06T12:45:00Z",
    )
    assert db.reap_stale_leases(db_path, as_of="2026-07-06T12:40:00Z") == []
    assert db.reap_stale_leases(db_path, as_of="2026-07-06T12:50:00Z") == ["lease-c"]

    with sqlite3.connect(db_path) as connection:
        remaining_count = connection.execute("SELECT COUNT(*) FROM leases").fetchone()[0]

    assert remaining_count == 0
