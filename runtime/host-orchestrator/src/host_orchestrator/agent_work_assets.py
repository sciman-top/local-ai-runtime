from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from host_orchestrator.dispatch_state import DISPATCH_STATUSES, REASONING_EFFORTS

TASK_KINDS = {"explore", "implement", "review", "docs_sync", "closeout"}
TASK_INTENTS = {
    "general",
    "bugfix",
    "feature",
    "refactor",
    "research",
    "docs",
    "review",
    "migration",
    "operations",
}
RISK_LEVELS = {"low", "medium", "high", "critical"}
MERGE_POLICIES = {"draft_pr_only", "manual_merge_only", "never_merge"}
EXECUTION_LANES = {"host_local", "remote_non_gui", "vm_gui"}
HANDOFF_POLICIES = {"none", "handoff_on_risk", "handoff_before_merge", "handoff_always"}
REQUIRED_VERIFICATION_COMMANDS = ("build", "test", "lint", "typecheck", "contract", "hotspot")
REVIEWER_KINDS = {"claude_glm", "codex_review", "gpt54_direct_review"}
REVIEW_MODES = {"advisory", "blocking"}
PLANNER_KINDS = {"codex_sdk", "gpt54_direct", "repo_policy_gate"}
PLANNER_MODES = {"advisory", "blocking"}
PLANNER_DISPOSITIONS = {"proceed", "handoff"}
RECOMMENDED_ACTIONS = {"approve", "revise", "reject"}
REVIEW_DISPOSITIONS = {"approve", "revise", "reject"}
HANDOFF_RECEIPT_KINDS = {"pre_worker_handoff"}
HANDOFF_REASON_CODES = {
    "execution_lane_profile_mismatch",
    "requires_network_with_offline_profile",
    "requires_gui_boundary",
    "selected_lane_runner_not_wired",
    "lease_quota_exhausted",
    "planner_sidecar_not_wired",
    "pre_worker_handoff",
}
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
MANIFEST_SCHEMA_VERSION = "agent_work_manifest.v1"
DEFAULT_ORCHESTRATION_CONSTRAINTS = {
    "profile": "observe_default",
    "mode_preference": "single_agent",
    "max_concurrent_subagents": 0,
    "max_total_subagents": 0,
    "max_tree_depth": 0,
    "write_conflict_policy": "serialize",
    "stop_policy": "stop_on_scope_or_contract_conflict",
}
ORCHESTRATION_MODE_PREFERENCES = {"auto", "single_agent", "multi_agent"}
WRITE_CONFLICT_POLICIES = {"serialize", "reject"}
ORCHESTRATION_STOP_POLICIES = {
    "stop_on_scope_or_contract_conflict",
    "finish_independent_workstreams",
}


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


def normalize_manifest_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(dict(payload))
    normalized.setdefault("schema_version", MANIFEST_SCHEMA_VERSION)
    normalized.setdefault(
        "orchestration_constraints",
        deepcopy(DEFAULT_ORCHESTRATION_CONSTRAINTS),
    )
    return normalized


def validate_manifest_payload(payload: Mapping[str, Any]) -> None:
    payload = normalize_manifest_payload(payload)
    required = (
        "schema_version",
        "run_id",
        "repo_root",
        "objective",
        "model_policy",
        "orchestration_constraints",
        "truth_sources",
        "tasks",
    )
    for key in required:
        _require_present(payload, key, "manifest")

    schema_version = _require_string(payload, "schema_version", "manifest")
    if schema_version != MANIFEST_SCHEMA_VERSION:
        raise ValueError(
            f"manifest.schema_version must be {MANIFEST_SCHEMA_VERSION}, got '{schema_version}'"
        )

    _validate_model_policy(_require_mapping(payload, "model_policy", "manifest"))
    _validate_orchestration_constraints(
        _require_mapping(payload, "orchestration_constraints", "manifest")
    )
    truth_sources = _require_string_list(payload, "truth_sources", "manifest", min_items=1)
    for index, value in enumerate(truth_sources):
        _validate_repo_relative_pattern(value, field=f"truth_sources[{index}]")
    if "evaluation_context" in payload:
        _validate_evaluation_context(
            _require_mapping(payload, "evaluation_context", "manifest")
        )
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
    for field in ("orchestration_decision_ref", "decision_id", "policy_version"):
        if field in payload and payload[field] is not None:
            _require_string(payload, field, "dispatch_state")
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
    if "planner_result_ref" in payload and payload["planner_result_ref"] is not None:
        _require_string(payload, "planner_result_ref", "dispatch_state")
    if "handoff_receipt_ref" in payload and payload["handoff_receipt_ref"] is not None:
        _require_string(payload, "handoff_receipt_ref", "dispatch_state")
    if "closeout_bundle_ref" in payload and payload["closeout_bundle_ref"] is not None:
        _require_string(payload, "closeout_bundle_ref", "dispatch_state")
    if "resume_point" in payload and payload["resume_point"] is not None:
        _require_enum(payload, "resume_point", RESUME_POINTS, "dispatch_state")
    if "retry_rewind" in payload and payload["retry_rewind"] is not None:
        _require_enum(payload, "retry_rewind", RESUME_POINTS, "dispatch_state")
    if "review_disposition" in payload and payload["review_disposition"] is not None:
        _require_enum(payload, "review_disposition", REVIEW_DISPOSITIONS, "dispatch_state")
    if "review_disposition_at" in payload and payload["review_disposition_at"] is not None:
        _require_string(payload, "review_disposition_at", "dispatch_state")


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
    if "handoff_receipt_ref" in payload and payload["handoff_receipt_ref"] is not None:
        _require_string(payload, "handoff_receipt_ref", "closeout_bundle")
    for field in ("orchestration_decision_ref", "decision_id", "policy_version"):
        if field in payload and payload[field] is not None:
            _require_string(payload, field, "closeout_bundle")


def validate_handoff_receipt_payload(payload: Mapping[str, Any]) -> None:
    required = (
        "task_id",
        "run_id",
        "receipt_kind",
        "status",
        "handoff_required",
        "reason_codes",
        "reason_details",
        "source_runtime",
        "requested_execution_lane",
        "selected_lane",
        "worker_profile",
        "worker_kind",
        "route_reason",
        "status_reason",
        "worker_execution_attempted",
        "requested_lane_runner_wired",
        "selected_profile_runner_wired",
        "next_action",
        "source_evidence_refs",
    )
    for key in required:
        _require_present(payload, key, "handoff_receipt")

    _require_string(payload, "task_id", "handoff_receipt")
    _require_string(payload, "run_id", "handoff_receipt")
    _require_enum(payload, "receipt_kind", HANDOFF_RECEIPT_KINDS, "handoff_receipt")
    _require_enum(payload, "status", set(DISPATCH_STATUSES), "handoff_receipt")
    _require_bool(payload, "handoff_required", "handoff_receipt")
    _require_string(payload, "source_runtime", "handoff_receipt")
    _require_enum(payload, "requested_execution_lane", EXECUTION_LANES, "handoff_receipt")
    _require_enum(payload, "selected_lane", EXECUTION_LANES, "handoff_receipt")
    _require_string(payload, "worker_profile", "handoff_receipt")
    _require_string(payload, "worker_kind", "handoff_receipt")
    _require_string(payload, "route_reason", "handoff_receipt")
    _require_string(payload, "status_reason", "handoff_receipt")
    _require_bool(payload, "worker_execution_attempted", "handoff_receipt")
    _require_bool(payload, "requested_lane_runner_wired", "handoff_receipt")
    _require_bool(payload, "selected_profile_runner_wired", "handoff_receipt")
    _require_string(payload, "next_action", "handoff_receipt")
    _require_string_list(payload, "reason_details", "handoff_receipt", min_items=1)
    _require_string_list(payload, "source_evidence_refs", "handoff_receipt", min_items=1)
    reason_codes = _require_string_list(payload, "reason_codes", "handoff_receipt", min_items=1)
    for index, reason_code in enumerate(reason_codes):
        if reason_code not in HANDOFF_REASON_CODES:
            raise ValueError(
                f"handoff_receipt.reason_codes[{index}] must be one of "
                f"{sorted(HANDOFF_REASON_CODES)}, got '{reason_code}'"
            )


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


def validate_planner_result_payload(payload: Mapping[str, Any]) -> None:
    required = (
        "task_id",
        "planner_kind",
        "planner_mode",
        "planner_profile",
        "model",
        "risk",
        "disposition",
        "reason_summary",
        "blocking_reasons",
        "plan_outline",
        "source_evidence_refs",
    )
    for key in required:
        _require_present(payload, key, "planner_result")

    _require_string(payload, "task_id", "planner_result")
    _require_enum(payload, "planner_kind", PLANNER_KINDS, "planner_result")
    _require_enum(payload, "planner_mode", PLANNER_MODES, "planner_result")
    _require_string(payload, "planner_profile", "planner_result")
    _require_string(payload, "model", "planner_result")
    _require_enum(payload, "risk", RISK_LEVELS, "planner_result")
    _require_enum(payload, "disposition", PLANNER_DISPOSITIONS, "planner_result")
    _require_string(payload, "reason_summary", "planner_result")
    _require_string_list(payload, "blocking_reasons", "planner_result")
    _require_string_list(payload, "plan_outline", "planner_result")
    _require_string_list(payload, "source_evidence_refs", "planner_result", min_items=1)


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
    if "intent" in task:
        _require_enum(task, "intent", TASK_INTENTS, context)
    _require_string(task, "goal", context)
    _require_string(task, "target_repo", context)
    _require_string(task, "base_branch", context)
    _require_string(task, "branch_name", context)
    worktree_path = _require_string(task, "worktree_path", context)
    _validate_repo_relative_pattern(worktree_path, field=f"{context}.worktree_path")
    for field_name in (
        "read_set",
        "write_set",
        "allowed_paths",
        "forbidden_paths",
        "artifacts_out",
    ):
        values = _require_string_list(task, field_name, context)
        for index, value in enumerate(values):
            _validate_repo_relative_pattern(
                value,
                field=f"{context}.{field_name}[{index}]",
            )
    _require_bool(task, "write_access", context)
    _require_enum(task, "risk_level", RISK_LEVELS, context)
    _require_enum(task, "merge_policy", MERGE_POLICIES, context)
    _require_enum(task, "execution_lane", EXECUTION_LANES, context)
    _require_bool(task, "requires_network", context)
    _require_bool(task, "requires_gui", context)
    _require_true_if_present(task, "user_forced_planner", context)
    _require_true_if_present(task, "user_forced_review", context)
    _require_string_list(task, "depends_on", context)
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


def _validate_orchestration_constraints(payload: Mapping[str, Any]) -> None:
    context = "orchestration_constraints"
    required = (
        "profile",
        "mode_preference",
        "max_concurrent_subagents",
        "max_total_subagents",
        "max_tree_depth",
        "write_conflict_policy",
        "stop_policy",
    )
    for key in required:
        _require_present(payload, key, context)

    _require_string(payload, "profile", context)
    _require_enum(
        payload,
        "mode_preference",
        ORCHESTRATION_MODE_PREFERENCES,
        context,
    )
    max_concurrent = _require_int(payload, "max_concurrent_subagents", context)
    max_total = _require_int(payload, "max_total_subagents", context)
    max_tree_depth = _require_int(payload, "max_tree_depth", context)
    _require_enum(payload, "write_conflict_policy", WRITE_CONFLICT_POLICIES, context)
    _require_enum(payload, "stop_policy", ORCHESTRATION_STOP_POLICIES, context)

    if not 0 <= max_concurrent <= 3:
        raise ValueError(f"{context}.max_concurrent_subagents must be between 0 and 3")
    if not 0 <= max_total <= 6:
        raise ValueError(f"{context}.max_total_subagents must be between 0 and 6")
    if max_concurrent > max_total:
        raise ValueError(
            f"{context}.max_concurrent_subagents cannot exceed max_total_subagents"
        )
    if max_concurrent == 0:
        if (max_total, max_tree_depth) != (0, 0):
            raise ValueError(
                f"{context} zero concurrency requires zero total budget and tree depth"
            )
        return
    if max_total < 1:
        raise ValueError(f"{context}.max_total_subagents must be positive when concurrency is enabled")
    if max_tree_depth != 1:
        raise ValueError(
            f"{context}.max_tree_depth must be 1 when subagent concurrency is enabled"
        )


def _validate_evaluation_context(payload: Mapping[str, Any]) -> None:
    context = "evaluation_context"
    for key in ("experiment_id", "variant", "repeat_index"):
        _require_present(payload, key, context)
    _require_string(payload, "experiment_id", context)
    variant = _require_enum(payload, "variant", {"baseline", "candidate"}, context)
    repeat_index = _require_int(payload, "repeat_index", context)
    if repeat_index < 1:
        raise ValueError(f"{context}.repeat_index must be >= 1")
    if variant == "candidate":
        _require_string(payload, "baseline_run_id", context)
    elif "baseline_run_id" in payload and payload["baseline_run_id"] is not None:
        _require_string(payload, "baseline_run_id", context)


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


def _validate_repo_relative_pattern(value: str, *, field: str) -> None:
    normalized = value.replace("\\", "/").strip()
    candidate = Path(normalized)
    if candidate.is_absolute() or candidate.drive:
        raise ValueError(f"{field} must be repo-relative, not absolute: {value}")
    segments = [segment for segment in normalized.split("/") if segment not in {"", "."}]
    if any(segment == ".." for segment in segments):
        raise ValueError(f"{field} must not escape the repo via '..': {value}")
