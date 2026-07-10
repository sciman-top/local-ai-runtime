from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from host_orchestrator.paths import RuntimeLayout


DISPATCH_STATUSES = (
    "queued",
    "running",
    "input_required",
    "waiting_handoff",
    "needs_review",
    "completed",
    "failed",
    "cancelled",
    "stale",
    "resumed",
)

REASONING_EFFORTS = ("low", "medium", "high", "xhigh", "max")


def build_dispatch_state_path(
    *,
    layout: RuntimeLayout,
    run_id: str,
    task_id: str,
) -> Path:
    return layout.runs_root / run_id / task_id / "dispatch_state.json"


def write_dispatch_state(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def update_dispatch_state(path: Path, **updates: Any) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(updates)
    write_dispatch_state(path, payload)
    return payload
