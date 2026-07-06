from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS runtime_tasks (
    task_id TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    execution_lane TEXT NOT NULL,
    worker_profile TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    result_path TEXT
);

CREATE TABLE IF NOT EXISTS leases (
    task_id TEXT NOT NULL,
    worker_id TEXT NOT NULL,
    lease_token TEXT UNIQUE NOT NULL,
    acquired_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workers (
    worker_id TEXT PRIMARY KEY,
    lane TEXT NOT NULL,
    status TEXT NOT NULL,
    heartbeat_at TEXT
);

CREATE TABLE IF NOT EXISTS route_decisions (
    task_id TEXT NOT NULL,
    selected_lane TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    task_id TEXT,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def initialize_control_plane(db_path: Path) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.executescript(SCHEMA_SQL)
        connection.commit()
    return db_path


class LeaseError(RuntimeError):
    """Raised when lease lifecycle operations fail."""


class LeaseConflictError(LeaseError):
    """Raised when an active lease already exists for the task."""


class LeaseNotFoundError(LeaseError):
    """Raised when a lease token cannot be found."""


def upsert_runtime_task(
    db_path: Path,
    *,
    task_id: str,
    state: str,
    execution_lane: str,
    worker_profile: str,
    created_at: str,
    updated_at: str,
    result_path: str | None = None,
) -> None:
    initialize_control_plane(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO runtime_tasks (
                task_id, state, execution_lane, worker_profile, created_at, updated_at, result_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET
                state = excluded.state,
                execution_lane = excluded.execution_lane,
                worker_profile = excluded.worker_profile,
                updated_at = excluded.updated_at,
                result_path = COALESCE(excluded.result_path, runtime_tasks.result_path)
            """,
            (task_id, state, execution_lane, worker_profile, created_at, updated_at, result_path),
        )
        connection.commit()


def upsert_worker(
    db_path: Path,
    *,
    worker_id: str,
    lane: str,
    status: str,
    heartbeat_at: str | None,
) -> None:
    initialize_control_plane(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO workers (worker_id, lane, status, heartbeat_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(worker_id) DO UPDATE SET
                lane = excluded.lane,
                status = excluded.status,
                heartbeat_at = excluded.heartbeat_at
            """,
            (worker_id, lane, status, heartbeat_at),
        )
        connection.commit()


def record_route_decision(
    db_path: Path,
    *,
    task_id: str,
    selected_lane: str,
    reason: str,
    created_at: str,
) -> None:
    initialize_control_plane(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO route_decisions (task_id, selected_lane, reason, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (task_id, selected_lane, reason, created_at),
        )
        connection.commit()


def append_event(
    db_path: Path,
    *,
    task_id: str | None,
    event_type: str,
    payload: dict[str, Any],
    created_at: str,
) -> None:
    initialize_control_plane(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO events (event_id, task_id, event_type, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(uuid4()), task_id, event_type, json.dumps(payload, ensure_ascii=True), created_at),
        )
        connection.commit()


def acquire_lease(
    db_path: Path,
    *,
    task_id: str,
    worker_id: str,
    acquired_at: str,
    expires_at: str,
    lease_token: str | None = None,
) -> str:
    initialize_control_plane(db_path)
    token = lease_token or str(uuid4())
    with sqlite3.connect(db_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "DELETE FROM leases WHERE task_id = ? AND expires_at <= ?",
            (task_id, acquired_at),
        )
        existing = connection.execute(
            """
            SELECT lease_token, worker_id, expires_at
            FROM leases
            WHERE task_id = ?
            ORDER BY acquired_at DESC
            LIMIT 1
            """,
            (task_id,),
        ).fetchone()
        if existing is not None:
            active_lease_token, active_worker_id, active_expires_at = existing
            raise LeaseConflictError(
                "Active lease already exists for task "
                f"{task_id} (worker_id={active_worker_id}, lease_token={active_lease_token}, "
                f"expires_at={active_expires_at})"
            )

        connection.execute(
            """
            INSERT INTO leases (task_id, worker_id, lease_token, acquired_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task_id, worker_id, token, acquired_at, expires_at),
        )
        connection.commit()
    return token


def renew_lease(
    db_path: Path,
    *,
    lease_token: str,
    expires_at: str,
) -> None:
    initialize_control_plane(db_path)
    with sqlite3.connect(db_path) as connection:
        updated = connection.execute(
            "UPDATE leases SET expires_at = ? WHERE lease_token = ?",
            (expires_at, lease_token),
        ).rowcount
        if updated == 0:
            raise LeaseNotFoundError(f"Lease token not found: {lease_token}")
        connection.commit()


def release_lease(
    db_path: Path,
    *,
    lease_token: str,
) -> bool:
    initialize_control_plane(db_path)
    with sqlite3.connect(db_path) as connection:
        deleted = connection.execute(
            "DELETE FROM leases WHERE lease_token = ?",
            (lease_token,),
        ).rowcount
        connection.commit()
    return deleted > 0


def reap_stale_leases(
    db_path: Path,
    *,
    as_of: str,
) -> list[str]:
    initialize_control_plane(db_path)
    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT lease_token FROM leases WHERE expires_at <= ? ORDER BY acquired_at",
            (as_of,),
        ).fetchall()
        lease_tokens = [lease_token for (lease_token,) in rows]
        if lease_tokens:
            connection.execute(
                "DELETE FROM leases WHERE expires_at <= ?",
                (as_of,),
            )
            connection.commit()
    return lease_tokens
