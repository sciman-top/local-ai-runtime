from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from host_orchestrator.dispatch_state import DISPATCH_STATUSES, REASONING_EFFORTS

TASK_KINDS = {"explore", "implement", "review", "docs_sync", "closeout"}
RISK_LEVELS = {"low", "medium", "high", "critical"}
MERGE_POLICIES = {"draft_pr_only", "manual_merge_only", "never_merge"}
EXECUTION_LANES = {"host_local", "remote_non_gui", "vm_gui"}
HANDOFF_POLICIES = {"none", "handoff_on_risk", "handoff_before_merge", "handoff_always"}
REQUIRED_VERIFICATION_COMMANDS = ("build", "test", "lint", "typecheck", "contract", "hotspot")
REVIEWER_KINDS = {"claude_glm", "codex_review", "gpt54_direct_review"}
REVIEW_MODES = {"advisory", "blocking"}
RECOMMENDED_ACTIONS = {"approve", "revise", "reject"}
DISPATCH_AGENT_ROLES = {
    "master",
    "explorer",
    "worker",
    "spec_reviewer",
    "quality_reviewer",
    "closeout",
}
CLOSEOUT_STATUSES = {"succeeded", "partial", "blocked"}
CLEANUP_STATUSES = {"deferred", "inline_only", "cleaned", "cleanup_failed"}
TEST_STATUSES = {"pass", "fail", "skipped", "gate_na"}
RESUME_POINTS = {"task_intake", "worker_execution", "verification", "handoff", "cleanup"}


def load_mapping_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        payload = yaml.safe_load(text)
    elif suffix == ".json":
        payload = json.loads(text)
    else:
        raise ValueError(f"Unsupported agent work asset suffix: {path}")

    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a top-level mapping/object")
    return payload


def validate_manifest_payload(payload: Mapping[str, Any]) -> None:
    required = ("run_id", "repo_root", "objective", "model_policy", "truth_sources", "tasks")
    for key in required:
        _require_present(payload, key, "manifest")

    _validate_model_policy(_require_mapping(payload, "model_policy", "manifest"))
    _require_string_list(payload, "truth_sources", "manifest", min_items=1)
    if "global_forbidden_scope" in payload:
        _require_string_list(payload, "global_forbidden_scope", "manifest")

    tasks = _require_list(payload, "tasks", "manifest", min_items=1)
    for index, task in enumerate(tasks):
        context = f"manifest.tasks[{index}]"
        task_payload = _require_mapping_from_value(task, context)
        _validate_manifest_task(task_payload, context)


def validate_dispatch_state_payload(payload: Mapping[str, Any]) -> None:
    required = (
        "run_id",
        "task_id",
        "agent_role",
        "model_policy",
        "repo_root",
        "target_repo",
        "branch_name",
        "worktree_path",
        "allowed_paths",
        "forbidden_paths",
        "source_ref",
        "lease_owner",
        "started_at",
        "updated_at",
        "heartbeat_at",
        "stale_after",
        "execution_lane",
        "worker_profile",
        "status",
        "status_reason",
        "next_action",
        "cleanup_status",
        "cleanup_owner",
    )
    for key in required:
        _require_present(payload, key, "dispatch_state")

    _validate_model_policy(_require_mapping(payload, "model_policy", "dispatch_state"))
    _require_string(payload, "run_id", "dispatch_state")
    _require_string(payload, "task_id", "dispatch_state")
    _require_enum(payload, "agent_role", DISPATCH_AGENT_ROLES, "dispatch_state")
    _require_string(payload, "repo_root", "dispatch_state")
    _require_string(payload, "target_repo", "dispatch_state")
    _require_string(payload, "branch_name", "dispatch_state")
    _require_string(payload, "worktree_path", "dispatch_state")
    _require_string_list(payload, "allowed_paths", "dispatch_state")
    _require_string_list(payload, "forbidden_paths", "dispatch_state")
    _require_string(payload, "source_ref", "dispatch_state")
    _require_string(payload, "lease_owner", "dispatch_state")
    _require_string(payload, "started_at", "dispatch_state")
    _require_string(payload, "updated_at", "dispatch_state")
    _require_string(payload, "heartbeat_at", "dispatch_state")
    _require_string(payload, "stale_after", "dispatch_state")
    _require_enum(payload, "execution_lane", EXECUTION_LANES, "dispatch_state")
    _require_string(payload, "worker_profile", "dispatch_state")
    _require_enum(payload, "status", DISPATCH_STATUSES, "dispatch_state")
    _require_string(payload, "status_reason", "dispatch_state")
    _require_string(payload, "next_action", "dispatch_state")
    _require_enum(payload, "cleanup_status", CLEANUP_STATUSES, "dispatch_state")
    _require_string(payload, "cleanup_owner", "dispatch_state")
    if "attempt" in payload:
        _require_int(payload, "attempt", "dispatch_state")
    if "workspace_root" in payload and payload["workspace_root"] is not None:
        _require_string(payload, "workspace_root", "dispatch_state")
    if "route_reason" in payload and payload["route_reason"] is not None:
        _require_string(payload, "route_reason", "dispatch_state")
    if "notes" in payload:
        _require_string_list(payload, "notes", "dispatch_state")
    if "last_result_ref" in payload and payload["last_result_ref"] is not None:
        _require_string(payload, "last_result_ref", "dispatch_state")
    if "verification_summary_ref" in payload and payload["verification_summary_ref"] is not None:
        _require_string(payload, "verification_summary_ref", "dispatch_state")
    if "evidence_index_ref" in payload and payload["evidence_index_ref"] is not None:
        _require_string(payload, "evidence_index_ref", "dispatch_state")
    if "review_result_ref" in payload and payload["review_result_ref"] is not None:
        _require_string(payload, "review_result_ref", "dispatch_state")
    if "closeout_bundle_ref" in payload and payload["closeout_bundle_ref"] is not None:
        _require_string(payload, "closeout_bundle_ref", "dispatch_state")
    if "resume_point" in payload and payload["resume_point"] is not None:
        _require_enum(payload, "resume_point", RESUME_POINTS, "dispatch_state")
    if "retry_rewind" in payload and payload["retry_rewind"] is not None:
        _require_enum(payload, "retry_rewind", RESUME_POINTS, "dispatch_state")


def validate_closeout_bundle_payload(payload: Mapping[str, Any]) -> None:
    required = (
        "run_id",
        "repo_root",
        "objective",
        "status",
        "completed",
        "not_completed",
        "conflicts",
        "tests",
        "evidence_refs",
        "cleanup_status",
        "cleanup_owner",
        "branches_removed",
        "worktrees_removed",
        "residual_risks",
        "repo_side_done",
        "still_open",
        "next_action",
    )
    for key in required:
        _require_present(payload, key, "closeout_bundle")

    _require_string(payload, "run_id", "closeout_bundle")
    _require_string(payload, "repo_root", "closeout_bundle")
    _require_string(payload, "objective", "closeout_bundle")
    _require_enum(payload, "status", CLOSEOUT_STATUSES, "closeout_bundle")
    _require_string_list(payload, "completed", "closeout_bundle")
    _require_string_list(payload, "not_completed", "closeout_bundle")
    _require_string_list(payload, "conflicts", "closeout_bundle")
    _require_string_list(payload, "evidence_refs", "closeout_bundle")
    _require_enum(payload, "cleanup_status", CLEANUP_STATUSES, "closeout_bundle")
    _require_string(payload, "cleanup_owner", "closeout_bundle")
    _require_string_list(payload, "branches_removed", "closeout_bundle")
    _require_string_list(payload, "worktrees_removed", "closeout_bundle")
    _require_string_list(payload, "residual_risks", "closeout_bundle")
    _require_string_list(payload, "repo_side_done", "closeout_bundle")
    _require_string_list(payload, "still_open", "closeout_bundle")
    _require_string(payload, "next_action", "closeout_bundle")

    tests = _require_list(payload, "tests", "closeout_bundle")
    for index, test in enumerate(tests):
        context = f"closeout_bundle.tests[{index}]"
        test_payload = _require_mapping_from_value(test, context)
        _require_string(test_payload, "name", context)
        _require_enum(test_payload, "status", TEST_STATUSES, context)
        _require_string(test_payload, "evidence_ref", context)


def validate_review_result_payload(payload: Mapping[str, Any]) -> None:
    required = (
        "task_id",
        "reviewer_kind",
        "review_mode",
        "model",
        "risk",
        "findings",
        "blocking_reasons",
        "missing_tests",
        "recommended_action",
        "source_evidence_refs",
    )
    for key in required:
        _require_present(payload, key, "review_result")

    _require_string(payload, "task_id", "review_result")
    _require_enum(payload, "reviewer_kind", REVIEWER_KINDS, "review_result")
    _require_enum(payload, "review_mode", REVIEW_MODES, "review_result")
    _require_string(payload, "model", "review_result")
    _require_enum(payload, "risk", RISK_LEVELS, "review_result")
    _require_string_list(payload, "blocking_reasons", "review_result")
    _require_string_list(payload, "missing_tests", "review_result")
    _require_enum(payload, "recommended_action", RECOMMENDED_ACTIONS, "review_result")
    _require_string_list(payload, "source_evidence_refs", "review_result", min_items=1)

    findings = _require_list(payload, "findings", "review_result")
    for index, finding in enumerate(findings):
        context = f"review_result.findings[{index}]"
        finding_payload = _require_mapping_from_value(finding, context)
        _require_string(finding_payload, "severity", context)
        _require_string(finding_payload, "category", context)
        _require_string(finding_payload, "title", context)
        _require_string(finding_payload, "detail", context)
        _require_string(finding_payload, "suggested_fix", context)


def _validate_manifest_task(task: Mapping[str, Any], context: str) -> None:
    required = (
        "task_id",
        "title",
        "kind",
        "goal",
        "target_repo",
        "base_branch",
        "branch_name",
        "worktree_path",
        "read_set",
        "write_set",
        "allowed_paths",
        "forbidden_paths",
        "write_access",
        "risk_level",
        "merge_policy",
        "execution_lane",
        "requires_network",
        "requires_gui",
        "depends_on",
        "artifacts_out",
        "handoff_policy",
        "verification_commands",
        "done_when",
    )
    for key in required:
        _require_present(task, key, context)
    if "blocked_by" in task:
        raise ValueError(f"{context} uses deprecated field 'blocked_by'; use 'depends_on'")

    _require_string(task, "task_id", context)
    _require_string(task, "title", context)
    _require_enum(task, "kind", TASK_KINDS, context)
    _require_string(task, "goal", context)
    _require_string(task, "target_repo", context)
    _require_string(task, "base_branch", context)
    _require_string(task, "branch_name", context)
    _require_string(task, "worktree_path", context)
    _require_string_list(task, "read_set", context)
    _require_string_list(task, "write_set", context)
    _require_string_list(task, "allowed_paths", context)
    _require_string_list(task, "forbidden_paths", context)
    _require_bool(task, "write_access", context)
    _require_enum(task, "risk_level", RISK_LEVELS, context)
    _require_enum(task, "merge_policy", MERGE_POLICIES, context)
    _require_enum(task, "execution_lane", EXECUTION_LANES, context)
    _require_bool(task, "requires_network", context)
    _require_bool(task, "requires_gui", context)
    _require_true_if_present(task, "user_forced_planner", context)
    _require_true_if_present(task, "user_forced_review", context)
    _require_string_list(task, "depends_on", context)
    _require_string_list(task, "artifacts_out", context)
    _require_enum(task, "handoff_policy", HANDOFF_POLICIES, context)
    _require_string_list(task, "done_when", context, min_items=1)
    if "worker_profile" in task and task["worker_profile"] is not None:
        _require_string(task, "worker_profile", context)

    verification_commands = _require_mapping(task, "verification_commands", context)
    missing_keys = [key for key in REQUIRED_VERIFICATION_COMMANDS if key not in verification_commands]
    if missing_keys:
        raise ValueError(f"{context}.verification_commands missing required keys: {missing_keys}")
    for key in REQUIRED_VERIFICATION_COMMANDS:
        value = verification_commands[key]
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{context}.verification_commands.{key} must be string or null")


def _validate_model_policy(payload: Mapping[str, Any]) -> None:
    _require_string(payload, "model", "model_policy")
    _require_enum(payload, "reasoning_effort", set(REASONING_EFFORTS), "model_policy")
    if "fallback_model" in payload and payload["fallback_model"] is not None:
        _require_string(payload, "fallback_model", "model_policy")
    if "rationale" in payload and payload["rationale"] is not None:
        _require_string(payload, "rationale", "model_policy")


def _require_present(payload: Mapping[str, Any], key: str, context: str) -> None:
    if key not in payload:
        raise ValueError(f"{context} missing required key: {key}")


def _require_mapping(payload: Mapping[str, Any], key: str, context: str) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{context}.{key} must be a mapping/object")
    return value


def _require_mapping_from_value(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be a mapping/object")
    return value


def _require_list(payload: Mapping[str, Any], key: str, context: str, min_items: int = 0) -> list[Any]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{context}.{key} must be an array/list")
    if len(value) < min_items:
        raise ValueError(f"{context}.{key} must contain at least {min_items} item(s)")
    return value


def _require_string(payload: Mapping[str, Any], key: str, context: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string")
    return value


def _require_bool(payload: Mapping[str, Any], key: str, context: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{context}.{key} must be a boolean")
    return value


def _require_int(payload: Mapping[str, Any], key: str, context: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{context}.{key} must be an integer")
    return value


def _require_string_list(payload: Mapping[str, Any], key: str, context: str, min_items: int = 0) -> list[str]:
    values = _require_list(payload, key, context, min_items=min_items)
    for index, value in enumerate(values):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{context}.{key}[{index}] must be a non-empty string")
    return list(values)


def _require_enum(payload: Mapping[str, Any], key: str, allowed: set[str], context: str) -> str:
    value = _require_string(payload, key, context)
    if value not in allowed:
        raise ValueError(f"{context}.{key} must be one of {sorted(allowed)}, got '{value}'")
    return value


def _require_true_if_present(payload: Mapping[str, Any], key: str, context: str) -> bool:
    if key not in payload:
        return False

    value = payload.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{context}.{key} must be a boolean when present")
    if value is not True:
        raise ValueError(f"{context}.{key} only allows true when present; omit the field instead")
    return True
