from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import uuid4


class AdmissionConflictError(RuntimeError):
    """Raised when a worker profile has no available execution slot."""


def acquire_slot(
    db_path: Path,
    *,
    worker_profile: str,
    max_slots: int,
    attempt_id: str,
    worker_id: str,
    acquired_at: str,
) -> str:
    if max_slots < 1:
        raise ValueError("max_slots must be >= 1")

    slot_token = str(uuid4())
    with sqlite3.connect(db_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        active = connection.execute(
            """
            SELECT COUNT(*)
            FROM leases
            WHERE worker_profile = ? AND released_at IS NULL
            """,
            (worker_profile,),
        ).fetchone()
        active_slots = int(active[0] if active is not None else 0)
        if active_slots >= max_slots:
            raise AdmissionConflictError(
                "No available execution slot for worker profile "
                f"{worker_profile} (active_slots={active_slots}, max_slots={max_slots})"
            )
        connection.execute(
            """
            INSERT INTO leases (
                slot_token,
                attempt_id,
                worker_profile,
                worker_id,
                acquired_at,
                released_at
            )
            VALUES (?, ?, ?, ?, ?, NULL)
            """,
            (slot_token, attempt_id, worker_profile, worker_id, acquired_at),
        )
        connection.commit()
    return slot_token


def release_slot(db_path: Path, *, slot_token: str, released_at: str) -> bool:
    with sqlite3.connect(db_path) as connection:
        updated = connection.execute(
            """
            UPDATE leases
            SET released_at = ?
            WHERE slot_token = ? AND released_at IS NULL
            """,
            (released_at, slot_token),
        ).rowcount
        connection.commit()
    return updated > 0


def count_active_slots(db_path: Path, *, worker_profile: str) -> int:
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT COUNT(*)
            FROM leases
            WHERE worker_profile = ? AND released_at IS NULL
            """,
            (worker_profile,),
        ).fetchone()
    return int(row[0] if row is not None else 0)
