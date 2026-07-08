from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sqlite3
from typing import Any

from host_orchestrator.paths import RuntimeLayout


REQUIRED_FIXTURE_FIELDS = (
    "schema_version",
    "task_id",
    "run_id",
    "attempt_id",
    "attempt_number",
    "status",
    "next_action",
    "worker_profile",
    "verification_profile",
    "continuation_policy",
    "execution_profile",
    "artifact_refs",
)


def evaluate_regression_fixtures(
    *,
    layout: RuntimeLayout,
    summary_path: Path | None = None,
) -> dict[str, Any]:
    summary_path = summary_path or (layout.runs_v2_root / "_eval" / "regression-fixture-summary.json")
    fixture_rows = _regression_fixture_artifact_rows(layout.control_plane_v2_db)
    status_counts: Counter[str] = Counter()
    next_action_counts: Counter[str] = Counter()
    evaluated_fixtures: list[dict[str, Any]] = []
    invalid_fixture_count = 0
    missing_fixture_count = 0
    review_required_count = 0
    policy_guard_fixture_count = 0
    retry_fixture_count = 0

    for row in fixture_rows:
        fixture_path = _resolve_artifact_path(layout, row["path"])
        if not fixture_path.exists():
            missing_fixture_count += 1
            evaluated_fixtures.append(
                {
                    "attempt_id": row["attempt_id"],
                    "path": row["path"],
                    "valid": False,
                    "issues": ["missing_fixture_file"],
                }
            )
            continue

        try:
            payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            invalid_fixture_count += 1
            evaluated_fixtures.append(
                {
                    "attempt_id": row["attempt_id"],
                    "path": row["path"],
                    "valid": False,
                    "issues": [type(exc).__name__],
                }
            )
            continue

        issues = _fixture_issues(payload)
        if issues:
            invalid_fixture_count += 1
        status = str(payload.get("status") or "")
        next_action = str(payload.get("next_action") or "")
        status_counts[status] += 1
        next_action_counts[next_action] += 1
        if payload.get("review_required") is True:
            review_required_count += 1
        if payload.get("policy_guard_reasons"):
            policy_guard_fixture_count += 1
        if payload.get("retry_rewind"):
            retry_fixture_count += 1
        evaluated_fixtures.append(
            {
                "attempt_id": str(payload.get("attempt_id") or row["attempt_id"]),
                "task_id": str(payload.get("task_id") or ""),
                "path": row["path"],
                "status": status,
                "next_action": next_action,
                "valid": not issues,
                "issues": issues,
            }
        )

    summary = {
        "schema_version": "runtime_v2_regression_eval.v1",
        "ok": bool(fixture_rows) and invalid_fixture_count == 0 and missing_fixture_count == 0,
        "fixture_count": len(fixture_rows),
        "valid_fixture_count": len(fixture_rows) - invalid_fixture_count - missing_fixture_count,
        "invalid_fixture_count": invalid_fixture_count,
        "missing_fixture_count": missing_fixture_count,
        "status_counts": dict(sorted(status_counts.items())),
        "next_action_counts": dict(sorted(next_action_counts.items())),
        "review_required_count": review_required_count,
        "policy_guard_fixture_count": policy_guard_fixture_count,
        "retry_fixture_count": retry_fixture_count,
        "fixtures": evaluated_fixtures,
        "summary_path": str(summary_path),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=True), encoding="utf-8")
    return summary


def _regression_fixture_artifact_rows(db_path: Path) -> list[dict[str, str]]:
    if not db_path.exists():
        return []
    with sqlite3.connect(db_path) as connection:
        try:
            rows = connection.execute(
                """
                SELECT attempt_id, path
                FROM artifacts
                WHERE kind = 'regression_fixture'
                ORDER BY created_at, attempt_id, path
                """
            ).fetchall()
        except sqlite3.OperationalError:
            return []
    return [{"attempt_id": str(attempt_id), "path": str(path)} for attempt_id, path in rows]


def _resolve_artifact_path(layout: RuntimeLayout, path_ref: str) -> Path:
    path = Path(path_ref)
    if path.is_absolute():
        return path
    return layout.repo_root / path


def _fixture_issues(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["fixture_payload_not_object"]
    issues: list[str] = []
    for field in REQUIRED_FIXTURE_FIELDS:
        if field not in payload:
            issues.append(f"missing_{field}")
    if payload.get("schema_version") != "runtime_v2_regression_fixture.v1":
        issues.append("unexpected_schema_version")
    if not isinstance(payload.get("artifact_refs"), dict):
        issues.append("artifact_refs_not_object")
    if not str(payload.get("status") or "").strip():
        issues.append("missing_status")
    if not str(payload.get("next_action") or "").strip():
        issues.append("missing_next_action")
    return issues
