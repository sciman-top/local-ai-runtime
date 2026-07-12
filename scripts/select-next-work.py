from __future__ import annotations

import argparse
from datetime import date
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATUS_PATH = ROOT / "docs" / "architecture" / "planning-status.json"
DEFAULT_POLICY_PATH = ROOT / "docs" / "architecture" / "next-work-selection-policy.json"
DEFAULT_VERIFIER_PATH = ROOT / "scripts" / "verify-planning-status.py"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Select the next Local AI Runtime work item without mutating state."
    )
    parser.add_argument("--repo-root", default=str(ROOT))
    parser.add_argument("--status-path", default=str(DEFAULT_STATUS_PATH))
    parser.add_argument("--policy-path", default=str(DEFAULT_POLICY_PATH))
    parser.add_argument("--verifier-path", default=str(DEFAULT_VERIFIER_PATH))
    args = parser.parse_args()

    result = select_next_work(
        repo_root=Path(args.repo_root),
        status_path=Path(args.status_path),
        policy_path=Path(args.policy_path),
        verifier_path=Path(args.verifier_path),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def select_next_work(
    *,
    repo_root: Path,
    status_path: Path,
    policy_path: Path,
    verifier_path: Path,
) -> dict[str, object]:
    root = repo_root.resolve(strict=False)
    try:
        policy = _load_json(policy_path)
        reasons = _validate_policy(policy)
        governance_issues = _inspect_required_refs(root, policy)
    except ValueError as exc:
        return _result(
            action="repair_gate_first",
            reason="Selector policy is missing or invalid.",
            current_work_item_id=None,
            policy_path=policy_path,
            governance_issues=[str(exc)],
            verifier_status=None,
            stage_snapshot=None,
        )

    if governance_issues:
        return _result(
            action="repair_gate_first",
            reason=reasons["repair_gate_first"],
            current_work_item_id=None,
            policy_path=policy_path,
            governance_issues=governance_issues,
            verifier_status=None,
            stage_snapshot=None,
        )

    review_expires_at = date.fromisoformat(policy["review_expires_at"])
    if review_expires_at < date.today():
        return _result(
            action="repair_gate_first",
            reason="Selector policy review has expired.",
            current_work_item_id=None,
            policy_path=policy_path,
            governance_issues=[f"review_expires_at={review_expires_at.isoformat()}"],
            verifier_status=None,
            stage_snapshot=None,
        )

    verifier_status = _run_verifier(root, status_path, verifier_path)
    verifier_payload = verifier_status.get("payload")
    if (
        verifier_status["exit_code"] != 0
        or not isinstance(verifier_payload, dict)
        or verifier_payload.get("status") != "pass"
    ):
        output_issue = verifier_status.get("stderr")
        return _result(
            action="repair_gate_first",
            reason=reasons["repair_gate_first"],
            current_work_item_id=None,
            policy_path=policy_path,
            governance_issues=(
                [str(output_issue)]
                if verifier_status["exit_code"] == 0 and output_issue
                else []
            ),
            verifier_status=verifier_status,
            stage_snapshot=None,
        )

    try:
        status = _load_json(status_path)
    except ValueError as exc:
        return _result(
            action="repair_gate_first",
            reason=reasons["repair_gate_first"],
            current_work_item_id=None,
            policy_path=policy_path,
            governance_issues=[str(exc)],
            verifier_status=verifier_status,
            stage_snapshot=None,
        )

    try:
        baseline = _required_object(status, "baseline_candidate")
        package = _required_object(status, "normative_package")
        approval = _required_object(status, "approval_state")
        truth_reset = _required_object(status, "truth_reset")
        legacy = _required_object(status, "legacy_runtime_posture")
        implementation = _required_object(status, "implementation")
        p2 = _required_object(status, "p2_admission")
        rollout = _required_object(status, "rollout")
        current_work = _required_object(status, "current_work_item")
        current_id = current_work["task_id"]
        missing = package["missing_artifact_ids"]
        if not isinstance(current_id, str) or not isinstance(missing, list):
            raise ValueError("planning status contains invalid selector fields")
    except (KeyError, TypeError, ValueError) as exc:
        return _result(
            action="repair_gate_first",
            reason=reasons["repair_gate_first"],
            current_work_item_id=None,
            policy_path=policy_path,
            governance_issues=[str(exc)],
            verifier_status=verifier_status,
            stage_snapshot=None,
        )

    if (
        verifier_payload.get("baseline_id") != baseline.get("id")
        or verifier_payload.get("current_work_item_id") != current_id
    ):
        return _result(
            action="repair_gate_first",
            reason=reasons["repair_gate_first"],
            current_work_item_id=None,
            policy_path=policy_path,
            governance_issues=[
                "planning verifier attestation does not match planning status identity"
            ],
            verifier_status=verifier_status,
            stage_snapshot=None,
        )

    if package["status"] != "complete" or not package["approval_eligible"]:
        historical_archive_selected = current_id == "LAR-P0A-001"
        rebaseline_selected = current_id == "LAR-P0A-REBASELINE-V322"
        review_task_selected = current_id == "LAR-P0A-013"
        review_artifacts_pending = (
            missing in policy["baseline_review_missing_artifact_sets"]
        )
        if review_task_selected != review_artifacts_pending:
            return _result(
                action="repair_gate_first",
                reason=reasons["repair_gate_first"],
                current_work_item_id=current_id,
                policy_path=policy_path,
                governance_issues=[
                    "baseline review closure state must pair LAR-P0A-013 with an exact declared missing-artifact set"
                ],
                verifier_status=verifier_status,
                stage_snapshot=_stage_snapshot(status),
            )
        if historical_archive_selected:
            action = "archive_lineage_sources_first"
        elif rebaseline_selected:
            action = "draft_v3_22_candidate_first"
        elif review_task_selected:
            action = "run_baseline_consistency_review"
        else:
            action = "close_baseline_normative_package_first"
    elif not approval["active"]:
        action = "record_baseline_approval_first"
    elif not truth_reset["performed"]:
        action = "implement_truth_reset_first"
    elif not legacy["legacy_guard_complete"]:
        action = "implement_legacy_guard_first"
    elif not implementation["code_complete"]:
        action = "implement_local_ai_runtime_first"
    elif not implementation["implementation_acceptance_active"]:
        action = "run_implementation_acceptance_first"
    elif not implementation["full_q0_passed"]:
        action = "run_full_q0_first"
    elif not p2["admitted"]:
        action = "repair_gate_first"
    elif not rollout["p2_pilot_complete"]:
        action = "run_single_p2_pilot_first"
    elif not rollout["p3_scheduled_self_host_complete"]:
        action = "run_five_scheduled_self_host_first"
    elif not rollout["p4_cohort_complete"]:
        action = "run_30_task_cohort_first"
    elif not rollout["p5_cutover_complete"] or not rollout["legacy_writer_retired"]:
        action = "cut_over_repositories_first"
    else:
        action = "operate_approved_runtime"

    if action not in policy["allowed_next_actions"]:
        return _result(
            action="repair_gate_first",
            reason="Selected action is not allowed by the current selector policy.",
            current_work_item_id=current_id,
            policy_path=policy_path,
            governance_issues=[f"disallowed selected action: {action}"],
            verifier_status=verifier_status,
            stage_snapshot=_stage_snapshot(status),
        )

    return _result(
        action=action,
        reason=reasons[action],
        current_work_item_id=current_id,
        policy_path=policy_path,
        governance_issues=[],
        verifier_status=verifier_status,
        stage_snapshot=_stage_snapshot(status),
    )


def _validate_policy(policy: dict[str, Any]) -> dict[str, str]:
    required = [
        "schema_version",
        "policy_id",
        "reviewed_on",
        "review_expires_at",
        "baseline_review_missing_artifact_sets",
        "allowed_next_actions",
        "selection_order",
        "required_entrypoints",
        "required_doc_refs",
        "rollback_ref",
    ]
    missing = [field for field in required if field not in policy]
    if missing:
        raise ValueError("selector policy missing fields: " + ", ".join(missing))
    try:
        date.fromisoformat(policy["review_expires_at"])
    except (TypeError, ValueError) as exc:
        raise ValueError("selector review_expires_at must be an ISO date") from exc
    allowed = policy["allowed_next_actions"]
    if (
        not isinstance(allowed, list)
        or not allowed
        or not all(isinstance(action, str) and action for action in allowed)
        or len(allowed) != len(set(allowed))
        or "repair_gate_first" not in allowed
    ):
        raise ValueError(
            "selector allowed_next_actions must be a unique string array containing repair_gate_first"
        )
    review_sets = policy["baseline_review_missing_artifact_sets"]
    if (
        not isinstance(review_sets, list)
        or not review_sets
        or any(
            not isinstance(item, list)
            or not item
            or not all(isinstance(value, str) and value for value in item)
            or len(item) != len(set(item))
            for item in review_sets
        )
        or len({tuple(item) for item in review_sets}) != len(review_sets)
    ):
        raise ValueError(
            "selector baseline_review_missing_artifact_sets must be unique non-empty string arrays"
        )
    selection = policy["selection_order"]
    if not isinstance(selection, list) or not selection:
        raise ValueError("selector selection_order must be a non-empty array")
    reasons: dict[str, str] = {}
    for index, item in enumerate(selection):
        if not isinstance(item, dict):
            raise ValueError(f"selector selection_order[{index}] must be an object")
        action = item.get("next_action")
        why = item.get("why")
        if not isinstance(action, str) or action not in allowed:
            raise ValueError(
                f"selector selection_order[{index}].next_action must be allowed"
            )
        if action in reasons:
            raise ValueError(f"selector selection_order contains duplicate action: {action}")
        if not isinstance(why, str) or not why.strip():
            raise ValueError(f"selector selection_order[{index}].why must be non-empty")
        reasons[action] = why
    missing_reasons = [action for action in allowed if action not in reasons]
    if missing_reasons:
        raise ValueError("selector actions missing reasons: " + ", ".join(missing_reasons))
    entrypoints = policy["required_entrypoints"]
    if not isinstance(entrypoints, list) or not all(
        isinstance(item, str) and item for item in entrypoints
    ):
        raise ValueError("selector required_entrypoints must be a string array")
    doc_refs = policy["required_doc_refs"]
    if not isinstance(doc_refs, list) or not all(
        isinstance(item, dict)
        and isinstance(item.get("path"), str)
        and bool(item["path"])
        and isinstance(item.get("contains"), str)
        and bool(item["contains"])
        for item in doc_refs
    ):
        raise ValueError("selector required_doc_refs must contain path/contains objects")
    return reasons


def _inspect_required_refs(root: Path, policy: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for relative in policy["required_entrypoints"]:
        try:
            path = _repo_path(root, relative)
        except ValueError as exc:
            issues.append(str(exc))
            continue
        if not path.exists():
            issues.append(f"missing entrypoint: {relative}")
    for item in policy["required_doc_refs"]:
        try:
            path = _repo_path(root, item["path"])
        except ValueError as exc:
            issues.append(str(exc))
            continue
        if not path.is_file():
            issues.append(f"missing doc ref: {item['path']}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            issues.append(f"unreadable doc ref: {item['path']}: {exc}")
            continue
        if item["contains"] not in text:
            issues.append(f"missing required text: {item['path']}:{item['contains']}")
    return issues


def _run_verifier(root: Path, status_path: Path, verifier_path: Path) -> dict[str, object]:
    command = [
        sys.executable,
        str(verifier_path),
        "--repo-root",
        str(root),
        "--status-path",
        str(status_path),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=60,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "exit_code": 124,
            "payload": None,
            "stderr": "planning verifier timed out after 60 seconds",
        }
    except OSError as exc:
        return {
            "command": command,
            "exit_code": 127,
            "payload": None,
            "stderr": f"planning verifier could not start: {exc}",
        }
    payload = None
    output_error = ""
    if completed.returncode == 0 and completed.stdout.strip():
        try:
            payload = _loads_json_object(completed.stdout, "planning verifier output")
        except ValueError as exc:
            output_error = str(exc)
    elif completed.returncode == 0:
        output_error = "planning verifier returned empty stdout"
    stderr = completed.stderr.strip()
    if output_error:
        stderr = "\n".join(part for part in (stderr, output_error) if part)
    return {
        "command": command,
        "exit_code": completed.returncode,
        "payload": payload,
        "stderr": stderr,
    }


def _stage_snapshot(status: dict[str, Any]) -> dict[str, object]:
    return {
        "baseline_status": status["baseline_candidate"]["status"],
        "blocking_stage": status["baseline_candidate"]["blocking_stage"],
        "normative_package_status": status["normative_package"]["status"],
        "missing_artifact_count": len(status["normative_package"]["missing_artifact_ids"]),
        "approval_active": status["approval_state"]["active"],
        "truth_reset_performed": status["truth_reset"]["performed"],
        "legacy_guard_complete": status["legacy_runtime_posture"]["legacy_guard_complete"],
        "implementation_started": status["implementation"]["started"],
        "implementation_acceptance_active": status["implementation"][
            "implementation_acceptance_active"
        ],
        "full_q0_passed": status["implementation"]["full_q0_passed"],
        "p2_admitted": status["p2_admission"]["admitted"],
        "p2_pilot_complete": status["rollout"]["p2_pilot_complete"],
        "p3_scheduled_self_host_complete": status["rollout"][
            "p3_scheduled_self_host_complete"
        ],
        "p4_cohort_complete": status["rollout"]["p4_cohort_complete"],
        "p5_cutover_complete": status["rollout"]["p5_cutover_complete"],
        "legacy_writer_retired": status["rollout"]["legacy_writer_retired"],
    }


def _result(
    *,
    action: str,
    reason: str,
    current_work_item_id: str | None,
    policy_path: Path,
    governance_issues: list[str],
    verifier_status: dict[str, object] | None,
    stage_snapshot: dict[str, object] | None,
) -> dict[str, object]:
    return {
        "status": "pass",
        "next_action": action,
        "current_work_item_id": current_work_item_id,
        "why": reason,
        "policy_path": policy_path.resolve(strict=False).as_posix(),
        "governance_issues": governance_issues,
        "verifier_status": verifier_status,
        "stage_snapshot": stage_snapshot,
        "side_effects_performed": False,
        "preflight_run": False,
    }


def _load_json(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
        payload = _loads_json_object(text, str(path))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise ValueError(f"JSON file is unreadable or invalid: {path}: {exc}") from exc
    return payload


def _loads_json_object(text: str, label: str) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for key, value in pairs:
            if key in payload:
                raise ValueError(f"duplicate JSON key {key!r} in {label}")
            payload[key] = value
        return payload

    try:
        payload = json.loads(text, object_pairs_hook=reject_duplicates)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {label}: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON value must be an object: {label}")
    return payload


def _required_object(payload: dict[str, Any], field: str) -> dict[str, Any]:
    value = payload.get(field)
    if not isinstance(value, dict):
        raise ValueError(f"planning status field must be an object: {field}")
    return value


def _repo_path(root: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("repo-relative path must be a non-empty string")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"path must remain repo-relative: {value}")
    path = (root / relative).resolve(strict=False)
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes repo root: {value}") from exc
    return path


if __name__ == "__main__":
    raise SystemExit(main())
