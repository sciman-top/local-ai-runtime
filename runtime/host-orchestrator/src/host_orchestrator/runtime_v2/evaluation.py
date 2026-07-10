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
    orchestration_fixtures: list[dict[str, Any]] = []

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
        if isinstance(payload.get("orchestration_metrics"), dict):
            orchestration_fixtures.append(payload)
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

    orchestration_evaluation = evaluate_orchestration_experiments(
        orchestration_fixtures
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
        "orchestration_fixture_count": len(orchestration_fixtures),
        "orchestration_evaluation": orchestration_evaluation,
        "fixtures": evaluated_fixtures,
        "summary_path": str(summary_path),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=True), encoding="utf-8")
    return summary


def evaluate_orchestration_experiments(
    fixtures: list[dict[str, Any]],
    *,
    minimum_repeats: int = 3,
) -> dict[str, Any]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for fixture in fixtures:
        context = fixture.get("evaluation_context")
        metrics = fixture.get("orchestration_metrics")
        if not isinstance(context, dict) or not isinstance(metrics, dict):
            continue
        experiment_id = str(context.get("experiment_id") or "").strip()
        variant = str(context.get("variant") or "").strip()
        if not experiment_id or variant not in {"baseline", "candidate"}:
            continue
        grouped.setdefault(experiment_id, {}).setdefault(variant, []).append(fixture)

    experiments: list[dict[str, Any]] = []
    for experiment_id in sorted(grouped):
        variants = grouped[experiment_id]
        baseline = _aggregate_variant(variants.get("baseline", []))
        candidate = _aggregate_variant(variants.get("candidate", []))
        comparison = _compare_variants(
            baseline=baseline,
            candidate=candidate,
            minimum_repeats=minimum_repeats,
        )
        experiments.append(
            {
                "experiment_id": experiment_id,
                "baseline": baseline,
                "candidate": candidate,
                **comparison,
            }
        )

    if not experiments or any(
        experiment["promotion_status"] == "insufficient_evidence"
        for experiment in experiments
    ):
        promotion_status = "insufficient_evidence"
    elif all(
        experiment["promotion_status"] == "eligible_for_manual_review"
        for experiment in experiments
    ):
        promotion_status = "eligible_for_manual_review"
    else:
        promotion_status = "not_eligible"
    return {
        "minimum_repeats": minimum_repeats,
        "experiment_count": len(experiments),
        "promotion_status": promotion_status,
        "automatic_promotion_performed": False,
        "experiments": experiments,
    }


def _aggregate_variant(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    repeat_indexes = {
        int(context["repeat_index"])
        for fixture in fixtures
        if isinstance((context := fixture.get("evaluation_context")), dict)
        and isinstance(context.get("repeat_index"), int)
    }
    metrics = [
        fixture["orchestration_metrics"]
        for fixture in fixtures
        if isinstance(fixture.get("orchestration_metrics"), dict)
    ]
    model_policies = {
        (
            str(policy.get("model") or ""),
            str(policy.get("reasoning_effort") or ""),
        )
        for fixture in fixtures
        if isinstance((policy := fixture.get("model_policy")), dict)
    }
    return {
        "fixture_count": len(fixtures),
        "repeat_count": len(repeat_indexes),
        "task_ids": sorted({str(fixture.get("task_id") or "") for fixture in fixtures}),
        "verification_profiles": sorted(
            {str(fixture.get("verification_profile") or "") for fixture in fixtures}
        ),
        "model_policies": [
            {"model": model, "reasoning_effort": effort}
            for model, effort in sorted(model_policies)
        ],
        "task_success_rate": _boolean_rate(metrics, "task_success"),
        "gate_pass_rate": _boolean_rate(metrics, "gate_pass"),
        "evidence_complete_rate": _boolean_rate(metrics, "evidence_complete"),
        "average_total_tokens": _numeric_average(metrics, "total_tokens"),
        "average_wall_time_ms": _numeric_average(metrics, "wall_time_ms"),
        "average_batch_wall_time_ms": _numeric_average(metrics, "batch_wall_time_ms"),
        "average_human_handoff_count": _numeric_average(metrics, "human_handoff_count"),
        "average_subagent_count": _numeric_average(metrics, "subagent_count"),
        "average_conflict_count": _numeric_average(metrics, "conflict_count"),
        "average_retry_count": _numeric_average(metrics, "retry_count"),
        "average_rework_count": _numeric_average(metrics, "rework_count"),
    }


def _compare_variants(
    *,
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    minimum_repeats: int,
) -> dict[str, Any]:
    if baseline["repeat_count"] < minimum_repeats or candidate["repeat_count"] < minimum_repeats:
        return {
            "contract_match": False,
            "primary_non_regression": False,
            "secondary_pareto_improvement": False,
            "promotion_status": "insufficient_evidence",
            "reason_codes": ["minimum_repeats_not_met"],
        }
    contract_match = all(
        baseline[field] == candidate[field]
        for field in ("task_ids", "verification_profiles", "model_policies")
    )
    if not contract_match:
        return {
            "contract_match": False,
            "primary_non_regression": False,
            "secondary_pareto_improvement": False,
            "promotion_status": "not_eligible",
            "reason_codes": ["comparison_contract_mismatch"],
        }

    primary_fields = (
        "task_success_rate",
        "gate_pass_rate",
        "evidence_complete_rate",
    )
    primary_non_regression = all(
        _not_lower(candidate[field], baseline[field]) for field in primary_fields
    )
    secondary_fields = (
        "average_total_tokens",
        "average_batch_wall_time_ms",
        "average_human_handoff_count",
        "average_retry_count",
        "average_rework_count",
    )
    comparable = [
        (candidate[field], baseline[field])
        for field in secondary_fields
        if candidate[field] is not None and baseline[field] is not None
    ]
    secondary_pareto_improvement = bool(comparable) and all(
        candidate_value <= baseline_value
        for candidate_value, baseline_value in comparable
    ) and any(
        candidate_value < baseline_value
        for candidate_value, baseline_value in comparable
    )
    eligible = primary_non_regression and secondary_pareto_improvement
    reason_codes: list[str] = []
    if not primary_non_regression:
        reason_codes.append("primary_metric_regression")
    if not secondary_pareto_improvement:
        reason_codes.append("no_secondary_pareto_improvement")
    if eligible:
        reason_codes.append("manual_promotion_review_allowed")
    return {
        "contract_match": True,
        "primary_non_regression": primary_non_regression,
        "secondary_pareto_improvement": secondary_pareto_improvement,
        "promotion_status": "eligible_for_manual_review" if eligible else "not_eligible",
        "reason_codes": reason_codes,
    }


def _boolean_rate(metrics: list[dict[str, Any]], field: str) -> float | None:
    values = [value for metric in metrics if isinstance((value := metric.get(field)), bool)]
    if not values:
        return None
    return sum(1 for value in values if value) / len(values)


def _numeric_average(metrics: list[dict[str, Any]], field: str) -> float | None:
    values = [
        float(value)
        for metric in metrics
        if isinstance((value := metric.get(field)), (int, float))
        and not isinstance(value, bool)
    ]
    if not values:
        return None
    return sum(values) / len(values)


def _not_lower(candidate: object, baseline: object) -> bool:
    if candidate is None or baseline is None:
        return False
    return float(candidate) >= float(baseline)


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
