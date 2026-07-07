from __future__ import annotations

from typing import Any


def task_trace_id(task_id: str) -> str:
    return f"task-trace::{task_id}"


def trace_manifest_payload(
    *,
    task_id: str,
    attempt_id: str,
    state: str,
    execution_profile: str,
    stages: list[dict[str, Any]],
    usage: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "task_trace_id": task_trace_id(task_id),
        "attempt_id": attempt_id,
        "state": state,
        "execution_profile": execution_profile,
        "stages": stages,
        "usage": usage,
    }
