from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4


SCHEMA_SQL_V2 = """
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    worker_profile TEXT NOT NULL,
    verification_profile TEXT NOT NULL,
    continuation_policy TEXT NOT NULL,
    write_access INTEGER NOT NULL,
    requires_network INTEGER NOT NULL,
    requires_gui INTEGER NOT NULL,
    status TEXT NOT NULL,
    status_reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_dependencies (
    task_id TEXT NOT NULL,
    dependency_ref TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_attempts (
    attempt_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    state TEXT NOT NULL,
    status_reason TEXT,
    execution_profile TEXT NOT NULL,
    worker_profile TEXT NOT NULL,
    resume_point TEXT,
    retry_rewind TEXT,
    started_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    gate_report_path TEXT,
    result_path TEXT,
    trace_manifest_path TEXT
);

CREATE TABLE IF NOT EXISTS leases (
    slot_token TEXT PRIMARY KEY,
    attempt_id TEXT NOT NULL,
    worker_profile TEXT NOT NULL,
    worker_id TEXT NOT NULL,
    acquired_at TEXT NOT NULL,
    released_at TEXT
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    attempt_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    path TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    attempt_id TEXT,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    title: str
    risk_level: str
    worker_profile: str
    verification_profile: str
    continuation_policy: str
    write_access: bool
    requires_network: bool
    requires_gui: bool
    status: str
    status_reason: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class AttemptRecord:
    attempt_id: str
    task_id: str
    run_id: str
    attempt_number: int
    state: str
    status_reason: str | None
    execution_profile: str
    worker_profile: str
    resume_point: str | None
    retry_rewind: str | None
    started_at: str
    updated_at: str
    gate_report_path: str | None
    result_path: str | None
    trace_manifest_path: str | None


def initialize_control_plane_v2(db_path: Path) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.executescript(SCHEMA_SQL_V2)
        _ensure_attempt_columns(connection)
        connection.commit()
    return db_path


def upsert_task(
    db_path: Path,
    *,
    task_id: str,
    title: str,
    risk_level: str,
    worker_profile: str,
    verification_profile: str,
    continuation_policy: str,
    write_access: bool,
    requires_network: bool,
    requires_gui: bool,
    status: str,
    status_reason: str | None,
    created_at: str,
    updated_at: str,
) -> None:
    initialize_control_plane_v2(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO tasks (
                task_id,
                title,
                risk_level,
                worker_profile,
                verification_profile,
                continuation_policy,
                write_access,
                requires_network,
                requires_gui,
                status,
                status_reason,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET
                title = excluded.title,
                risk_level = excluded.risk_level,
                worker_profile = excluded.worker_profile,
                verification_profile = excluded.verification_profile,
                continuation_policy = excluded.continuation_policy,
                write_access = excluded.write_access,
                requires_network = excluded.requires_network,
                requires_gui = excluded.requires_gui,
                status = excluded.status,
                status_reason = excluded.status_reason,
                updated_at = excluded.updated_at
            """,
            (
                task_id,
                title,
                risk_level,
                worker_profile,
                verification_profile,
                continuation_policy,
                int(write_access),
                int(requires_network),
                int(requires_gui),
                status,
                status_reason,
                created_at,
                updated_at,
            ),
        )
        connection.commit()


def replace_dependencies(
    db_path: Path,
    *,
    task_id: str,
    dependency_refs: tuple[str, ...],
    created_at: str,
) -> None:
    initialize_control_plane_v2(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute("DELETE FROM task_dependencies WHERE task_id = ?", (task_id,))
        for dependency_ref in dependency_refs:
            connection.execute(
                """
                INSERT INTO task_dependencies (task_id, dependency_ref, created_at)
                VALUES (?, ?, ?)
                """,
                (task_id, dependency_ref, created_at),
            )
        connection.commit()


def unresolved_dependency_refs(db_path: Path, *, task_id: str) -> list[str]:
    initialize_control_plane_v2(db_path)
    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT dependency_ref
            FROM task_dependencies
            WHERE task_id = ?
            ORDER BY dependency_ref
            """,
            (task_id,),
        ).fetchall()
        unresolved: list[str] = []
        for (dependency_ref,) in rows:
            dependency = connection.execute(
                "SELECT status FROM tasks WHERE task_id = ?",
                (dependency_ref,),
            ).fetchone()
            if dependency is None or dependency[0] != "completed":
                unresolved.append(str(dependency_ref))
    return unresolved


def next_attempt_number(db_path: Path, *, task_id: str) -> int:
    initialize_control_plane_v2(db_path)
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            "SELECT COALESCE(MAX(attempt_number), 0) FROM task_attempts WHERE task_id = ?",
            (task_id,),
        ).fetchone()
    return int(row[0] if row is not None else 0) + 1


def create_attempt(
    db_path: Path,
    *,
    attempt_id: str,
    task_id: str,
    run_id: str,
    attempt_number: int,
    state: str,
    status_reason: str | None,
    execution_profile: str,
    worker_profile: str,
    resume_point: str | None = None,
    retry_rewind: str | None = None,
    started_at: str,
    updated_at: str,
    gate_report_path: str | None = None,
    result_path: str | None = None,
    trace_manifest_path: str | None = None,
) -> None:
    initialize_control_plane_v2(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO task_attempts (
                attempt_id,
                task_id,
                run_id,
                attempt_number,
                state,
                status_reason,
                execution_profile,
                worker_profile,
                resume_point,
                retry_rewind,
                started_at,
                updated_at,
                gate_report_path,
                result_path,
                trace_manifest_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt_id,
                task_id,
                run_id,
                attempt_number,
                state,
                status_reason,
                execution_profile,
                worker_profile,
                resume_point,
                retry_rewind,
                started_at,
                updated_at,
                gate_report_path,
                result_path,
                trace_manifest_path,
            ),
        )
        connection.commit()


def update_attempt(
    db_path: Path,
    *,
    attempt_id: str,
    state: str,
    updated_at: str,
    status_reason: str | None = None,
    resume_point: str | None = None,
    retry_rewind: str | None = None,
    gate_report_path: str | None = None,
    result_path: str | None = None,
    trace_manifest_path: str | None = None,
) -> None:
    initialize_control_plane_v2(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            UPDATE task_attempts
            SET
                state = ?,
                status_reason = COALESCE(?, status_reason),
                resume_point = COALESCE(?, resume_point),
                retry_rewind = COALESCE(?, retry_rewind),
                updated_at = ?,
                gate_report_path = COALESCE(?, gate_report_path),
                result_path = COALESCE(?, result_path),
                trace_manifest_path = COALESCE(?, trace_manifest_path)
            WHERE attempt_id = ?
            """,
            (
                state,
                status_reason,
                resume_point,
                retry_rewind,
                updated_at,
                gate_report_path,
                result_path,
                trace_manifest_path,
                attempt_id,
            ),
        )
        connection.commit()


def record_artifact(
    db_path: Path,
    *,
    attempt_id: str,
    kind: str,
    path: str,
    created_at: str,
) -> None:
    initialize_control_plane_v2(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO artifacts (artifact_id, attempt_id, kind, path, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(uuid4()), attempt_id, kind, path, created_at),
        )
        connection.commit()


def append_event(
    db_path: Path,
    *,
    task_id: str,
    attempt_id: str | None,
    event_type: str,
    payload: dict[str, Any],
    created_at: str,
) -> None:
    initialize_control_plane_v2(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO events (event_id, task_id, attempt_id, event_type, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                task_id,
                attempt_id,
                event_type,
                json.dumps(payload, ensure_ascii=True),
                created_at,
            ),
        )
        connection.commit()


def load_task(db_path: Path, *, task_id: str) -> TaskRecord:
    initialize_control_plane_v2(db_path)
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT
                task_id,
                title,
                risk_level,
                worker_profile,
                verification_profile,
                continuation_policy,
                write_access,
                requires_network,
                requires_gui,
                status,
                status_reason,
                created_at,
                updated_at
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()
    if row is None:
        raise ValueError(f"Unknown v2 task: {task_id}")
    return TaskRecord(
        task_id=str(row[0]),
        title=str(row[1]),
        risk_level=str(row[2]),
        worker_profile=str(row[3]),
        verification_profile=str(row[4]),
        continuation_policy=str(row[5]),
        write_access=bool(row[6]),
        requires_network=bool(row[7]),
        requires_gui=bool(row[8]),
        status=str(row[9]),
        status_reason=str(row[10]) if row[10] is not None else None,
        created_at=str(row[11]),
        updated_at=str(row[12]),
    )


def load_attempt(db_path: Path, *, attempt_id: str) -> AttemptRecord:
    initialize_control_plane_v2(db_path)
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT
                attempt_id,
                task_id,
                run_id,
                attempt_number,
                state,
                status_reason,
                execution_profile,
                worker_profile,
                resume_point,
                retry_rewind,
                started_at,
                updated_at,
                gate_report_path,
                result_path,
                trace_manifest_path
            FROM task_attempts
            WHERE attempt_id = ?
            """,
            (attempt_id,),
        ).fetchone()
    if row is None:
        raise ValueError(f"Unknown v2 attempt: {attempt_id}")
    return AttemptRecord(
        attempt_id=str(row[0]),
        task_id=str(row[1]),
        run_id=str(row[2]),
        attempt_number=int(row[3]),
        state=str(row[4]),
        status_reason=str(row[5]) if row[5] is not None else None,
        execution_profile=str(row[6]),
        worker_profile=str(row[7]),
        resume_point=str(row[8]) if row[8] is not None else None,
        retry_rewind=str(row[9]) if row[9] is not None else None,
        started_at=str(row[10]),
        updated_at=str(row[11]),
        gate_report_path=str(row[12]) if row[12] is not None else None,
        result_path=str(row[13]) if row[13] is not None else None,
        trace_manifest_path=str(row[14]) if row[14] is not None else None,
    )


def list_tables(db_path: Path) -> set[str]:
    initialize_control_plane_v2(db_path)
    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()
    return {str(name) for (name,) in rows}


def _ensure_attempt_columns(connection: sqlite3.Connection) -> None:
    existing_columns = {
        str(row[1])
        for row in connection.execute("PRAGMA table_info(task_attempts)").fetchall()
    }
    if "resume_point" not in existing_columns:
        connection.execute("ALTER TABLE task_attempts ADD COLUMN resume_point TEXT")
    if "retry_rewind" not in existing_columns:
        connection.execute("ALTER TABLE task_attempts ADD COLUMN retry_rewind TEXT")
