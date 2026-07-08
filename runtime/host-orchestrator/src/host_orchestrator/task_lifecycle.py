from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
from typing import Any

from host_orchestrator import db
from host_orchestrator.canonical_result import update_result_metadata
from host_orchestrator.dispatch_state import update_dispatch_state
from host_orchestrator.paths import RuntimeLayout


RESUME_POINTS = {
    "task_intake",
    "worker_execution",
    "verification",
    "handoff",
    "cleanup",
}
REVIEW_DISPOSITIONS = {"approve", "revise", "reject"}
STALE_CANDIDATE_STATES = {"queued", "running", "input_required", "resumed"}
LEASE_TTL = timedelta(minutes=30)


@dataclass(frozen=True)
class RuntimeTaskRecord:
    task_id: str
    run_id: str | None
    attempt: int
    state: str
    state_reason: str | None
    execution_lane: str
    worker_profile: str
    next_action: str | None
    cleanup_status: str | None
    cleanup_owner: str | None
    created_at: str
    updated_at: str
    result_path: str | None
    dispatch_state_path: str


def reconcile_stale_tasks(layout: RuntimeLayout, *, as_of: str) -> list[str]:
    normalized_as_of = normalize_timestamp(as_of)
    db.reap_stale_leases(layout.control_plane_db, as_of=normalized_as_of)
    stale_task_ids: list[str] = []
    for record in _load_records(layout, states=STALE_CANDIDATE_STATES):
        dispatch_state_path = _dispatch_state_path(layout, record)
        payload = json.loads(dispatch_state_path.read_text(encoding="utf-8"))
        stale_after = str(payload.get("stale_after") or "").strip()
        if not stale_after:
            continue
        if _parse_timestamp(stale_after) > _parse_timestamp(normalized_as_of):
            continue
        _apply_transition(
            layout=layout,
            record=record,
            changed_at=normalized_as_of,
            state="stale",
            status_reason=f"stale heartbeat detected at {normalized_as_of}",
            next_action="inspect_stale_run_and_resume",
            event_type="task_stale",
            event_payload={"stale_after": stale_after},
        )
        stale_task_ids.append(record.task_id)
    return stale_task_ids


def cancel_task(
    layout: RuntimeLayout,
    *,
    task_id: str,
    cancelled_at: str,
    reason: str,
) -> dict[str, Any]:
    record = _load_record(layout, task_id)
    normalized_cancelled_at = normalize_timestamp(cancelled_at)
    return _apply_transition(
        layout=layout,
        record=record,
        changed_at=normalized_cancelled_at,
        state="cancelled",
        status_reason=reason,
        next_action="operator may resume or retry",
        event_type="task_cancelled",
        event_payload={"reason": reason},
        release_active_leases=True,
    )


def resume_task(
    layout: RuntimeLayout,
    *,
    task_id: str,
    resumed_at: str,
    resume_point: str,
    reason: str,
) -> dict[str, Any]:
    _require_resume_point(resume_point)
    record = _load_record(layout, task_id)
    normalized_resumed_at = normalize_timestamp(resumed_at)
    return _apply_transition(
        layout=layout,
        record=record,
        changed_at=normalized_resumed_at,
        state="resumed",
        status_reason=reason,
        next_action=f"resume_from_{resume_point}",
        event_type="task_resumed",
        dispatch_updates={
            "resume_point": resume_point,
            "heartbeat_at": normalized_resumed_at,
            "stale_after": _lease_expires_at(normalized_resumed_at),
        },
        event_payload={"resume_point": resume_point},
        release_active_leases=True,
    )


def retry_task(
    layout: RuntimeLayout,
    *,
    task_id: str,
    retried_at: str,
    retry_rewind: str,
    reason: str,
) -> dict[str, Any]:
    _require_resume_point(retry_rewind)
    record = _load_record(layout, task_id)
    normalized_retried_at = normalize_timestamp(retried_at)
    return _apply_transition(
        layout=layout,
        record=record,
        changed_at=normalized_retried_at,
        state="resumed",
        status_reason=reason,
        next_action=f"retry_from_{retry_rewind}",
        event_type="task_retry_requested",
        attempt=record.attempt + 1,
        dispatch_updates={
            "resume_point": retry_rewind,
            "retry_rewind": retry_rewind,
            "heartbeat_at": normalized_retried_at,
            "stale_after": _lease_expires_at(normalized_retried_at),
        },
        event_payload={"retry_rewind": retry_rewind},
        release_active_leases=True,
    )


def record_review_disposition(
    layout: RuntimeLayout,
    *,
    task_id: str,
    disposition: str,
    disposition_at: str,
    reason: str,
) -> dict[str, Any]:
    _require_review_disposition(disposition)
    record = _load_record(layout, task_id)
    if record.state != "needs_review":
        raise ValueError(
            "review disposition can only be recorded for needs_review tasks, "
            f"got {record.state!r}"
        )

    normalized_disposition_at = normalize_timestamp(disposition_at)
    base_dispatch_updates = {
        "review_disposition": disposition,
        "review_disposition_at": normalized_disposition_at,
    }
    if disposition == "approve":
        return _apply_transition(
            layout=layout,
            record=record,
            changed_at=normalized_disposition_at,
            state="completed",
            status_reason=reason or "repo-side review disposition approved",
            next_action="repo-side review disposition approved; live acceptance still pending",
            event_type="task_review_approved",
            dispatch_updates=base_dispatch_updates,
            event_payload={"review_disposition": disposition, "reason": reason},
            release_active_leases=True,
        )
    if disposition == "revise":
        return _apply_transition(
            layout=layout,
            record=record,
            changed_at=normalized_disposition_at,
            state="resumed",
            status_reason=reason or "repo-side review requested revision",
            next_action="retry_from_worker_execution",
            event_type="task_review_revision_requested",
            attempt=record.attempt + 1,
            dispatch_updates={
                **base_dispatch_updates,
                "resume_point": "worker_execution",
                "retry_rewind": "worker_execution",
                "heartbeat_at": normalized_disposition_at,
                "stale_after": _lease_expires_at(normalized_disposition_at),
            },
            event_payload={"review_disposition": disposition, "reason": reason},
            release_active_leases=True,
        )
    return _apply_transition(
        layout=layout,
        record=record,
        changed_at=normalized_disposition_at,
        state="cancelled",
        status_reason=reason or "repo-side review rejected downstream use",
        next_action="operator may resume or retry",
        event_type="task_review_rejected",
        dispatch_updates=base_dispatch_updates,
        event_payload={"review_disposition": disposition, "reason": reason},
        release_active_leases=True,
    )


def _apply_transition(
    *,
    layout: RuntimeLayout,
    record: RuntimeTaskRecord,
    changed_at: str,
    state: str,
    status_reason: str,
    next_action: str,
    event_type: str,
    attempt: int | None = None,
    dispatch_updates: dict[str, Any] | None = None,
    event_payload: dict[str, Any] | None = None,
    release_active_leases: bool = False,
) -> dict[str, Any]:
    dispatch_state_path = _dispatch_state_path(layout, record)
    released_leases = (
        db.release_task_leases(layout.control_plane_db, task_id=record.task_id)
        if release_active_leases
        else []
    )
    payload_updates: dict[str, Any] = {
        "status": state,
        "status_reason": status_reason,
        "next_action": next_action,
        "updated_at": changed_at,
        "attempt": attempt if attempt is not None else record.attempt,
    }
    if dispatch_updates:
        payload_updates.update(dispatch_updates)
    payload = update_dispatch_state(dispatch_state_path, **payload_updates)

    db.upsert_runtime_task(
        layout.control_plane_db,
        task_id=record.task_id,
        run_id=record.run_id,
        attempt=payload["attempt"],
        state=state,
        state_reason=status_reason,
        execution_lane=record.execution_lane,
        worker_profile=record.worker_profile,
        next_action=next_action,
        cleanup_status=record.cleanup_status,
        cleanup_owner=record.cleanup_owner,
        created_at=record.created_at,
        updated_at=changed_at,
        result_path=record.result_path,
        dispatch_state_path=record.dispatch_state_path,
    )

    if record.result_path:
        result_path = layout.repo_root / record.result_path
        if result_path.exists():
            update_result_metadata(
                result_path,
                next_action=next_action,
                status_reason=status_reason,
            )
            _refresh_closeout_bundle(
                result_path=result_path,
                state=state,
                next_action=next_action,
                cleanup_status=str(record.cleanup_status or ""),
                cleanup_owner=str(record.cleanup_owner or ""),
            )

    db.append_event(
        layout.control_plane_db,
        task_id=record.task_id,
        event_type=event_type,
        payload={
            "state": state,
            "status_reason": status_reason,
            "next_action": next_action,
            "attempt": payload["attempt"],
            "dispatch_state_path": record.dispatch_state_path,
            "released_leases": released_leases,
            **(event_payload or {}),
        },
        created_at=changed_at,
    )
    return payload


def _refresh_closeout_bundle(
    *,
    result_path: Path,
    state: str,
    next_action: str,
    cleanup_status: str,
    cleanup_owner: str,
) -> None:
    closeout_bundle_path = result_path.parent / "closeout_bundle.json"
    if not closeout_bundle_path.exists():
        return

    payload = json.loads(closeout_bundle_path.read_text(encoding="utf-8"))
    payload["status"] = _closeout_status_for_state(state)
    payload["not_completed"] = _not_completed_for_state(state)
    payload["conflicts"] = _conflicts_for_cleanup(cleanup_status)
    payload["cleanup_status"] = cleanup_status
    payload["cleanup_owner"] = cleanup_owner
    payload["still_open"] = _still_open_for_state(state, next_action)
    payload["next_action"] = next_action
    closeout_bundle_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _closeout_status_for_state(state: str) -> str:
    if state == "completed":
        return "succeeded"
    if state == "resumed":
        return "partial"
    return "blocked"


def _not_completed_for_state(state: str) -> list[str]:
    if state == "completed":
        return []
    if state == "cancelled":
        return ["run was explicitly cancelled before downstream closeout"]
    if state == "stale":
        return ["stale runtime state still requires replay or operator recovery"]
    if state == "resumed":
        return ["resumed task still requires a fresh worker or verification pass"]
    return []


def _conflicts_for_cleanup(cleanup_status: str) -> list[str]:
    if cleanup_status == "deferred":
        return ["cleanup remains deferred to the operator"]
    if cleanup_status == "cleanup_failed":
        return ["runtime cleanup failed and requires operator follow-up"]
    return []


def _still_open_for_state(state: str, next_action: str) -> list[str]:
    still_open = ["live accepted"]
    if state == "completed":
        still_open.append("remote/vm runner acceptance if required by the broader queue")
    if state == "cancelled":
        still_open.append("explicit operator restart or closure")
    if state == "stale":
        still_open.append("stale recovery replay")
    if state == "resumed":
        still_open.append("fresh execution after resume or retry")
    if next_action and next_action != "none":
        still_open.append(next_action)
    return still_open


def _load_record(layout: RuntimeLayout, task_id: str) -> RuntimeTaskRecord:
    with sqlite3.connect(layout.control_plane_db) as connection:
        row = connection.execute(
            """
            SELECT
                task_id,
                run_id,
                attempt,
                state,
                state_reason,
                execution_lane,
                worker_profile,
                next_action,
                cleanup_status,
                cleanup_owner,
                created_at,
                updated_at,
                result_path,
                dispatch_state_path
            FROM runtime_tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()
    if row is None:
        raise ValueError(f"runtime task not found: {task_id}")
    return RuntimeTaskRecord(*row)


def _load_records(layout: RuntimeLayout, *, states: set[str]) -> list[RuntimeTaskRecord]:
    placeholders = ", ".join("?" for _ in states)
    with sqlite3.connect(layout.control_plane_db) as connection:
        rows = connection.execute(
            f"""
            SELECT
                task_id,
                run_id,
                attempt,
                state,
                state_reason,
                execution_lane,
                worker_profile,
                next_action,
                cleanup_status,
                cleanup_owner,
                created_at,
                updated_at,
                result_path,
                dispatch_state_path
            FROM runtime_tasks
            WHERE state IN ({placeholders}) AND dispatch_state_path IS NOT NULL
            """,
            tuple(sorted(states)),
        ).fetchall()
    return [RuntimeTaskRecord(*row) for row in rows]


def _dispatch_state_path(layout: RuntimeLayout, record: RuntimeTaskRecord) -> Path:
    return layout.repo_root / record.dispatch_state_path


def _require_resume_point(value: str) -> None:
    if value not in RESUME_POINTS:
        raise ValueError(f"resume/retry point must be one of {sorted(RESUME_POINTS)}, got {value!r}")


def _require_review_disposition(value: str) -> None:
    if value not in REVIEW_DISPOSITIONS:
        raise ValueError(f"review disposition must be one of {sorted(REVIEW_DISPOSITIONS)}, got {value!r}")


def normalize_timestamp(value: str) -> str:
    parsed = _parse_timestamp(value)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _lease_expires_at(changed_at: str) -> str:
    parsed = _parse_timestamp(changed_at)
    return (parsed + LEASE_TTL).astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
