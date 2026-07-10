from __future__ import annotations

import json
import tomllib

from host_orchestrator.agent_work_assets import (
    DEFAULT_ORCHESTRATION_CONSTRAINTS,
    REQUIRED_VERIFICATION_COMMANDS,
    load_mapping_file,
    normalize_manifest_payload,
    validate_closeout_bundle_payload,
    validate_dispatch_state_payload,
    validate_handoff_receipt_payload,
    validate_manifest_payload,
    validate_planner_result_payload,
    validate_review_result_payload,
)
from host_orchestrator.runner_acceptance import (
    RUNNER_ACCEPTANCE_SCHEMA_VERSION,
    validate_runner_acceptance_payload,
)

from support import REPO_ROOT


def test_project_codex_config_bounds_subagents_and_read_only_roles() -> None:
    config = tomllib.loads((REPO_ROOT / ".codex" / "config.toml").read_text(encoding="utf-8"))

    assert config["sandbox_workspace_write"]["network_access"] is True
    assert config["agents"] == {"max_threads": 4, "max_depth": 1}

    expected_agents = {
        "explorer": ("gpt-5.6-terra", "medium"),
        "spec_reviewer": ("gpt-5.6-sol", "high"),
        "quality_reviewer": ("gpt-5.6-sol", "high"),
    }
    for agent_name, (model, reasoning_effort) in expected_agents.items():
        payload = tomllib.loads(
            (REPO_ROOT / ".codex" / "agents" / f"{agent_name}.toml").read_text(
                encoding="utf-8"
            )
        )
        assert payload["name"] == agent_name
        assert payload["model"] == model
        assert payload["model_reasoning_effort"] == reasoning_effort
        assert payload["sandbox_mode"] == "read-only"
        assert payload["description"]
        assert payload["developer_instructions"]


def test_manifest_template_aligns_with_repo_owned_contract() -> None:
    payload = load_mapping_file(REPO_ROOT / "templates" / "agent-work-manifest.example.yaml")

    validate_manifest_payload(payload)

    schema = json.loads((REPO_ROOT / "templates" / "agent-work-manifest.schema.json").read_text(encoding="utf-8"))
    assert "tasks" in schema["required"]
    assert "model_policy" in schema["required"]
    assert "schema_version" not in schema["required"]
    assert "orchestration_constraints" not in schema["required"]
    assert schema["properties"]["schema_version"]["const"] == "agent_work_manifest.v1"
    task_properties = schema["properties"]["tasks"]["items"]["properties"]
    assert "depends_on" in task_properties
    assert "blocked_by" not in task_properties
    assert "general" in task_properties["intent"]["enum"]
    assert "bugfix" in task_properties["intent"]["enum"]
    assert task_properties["user_forced_planner"]["const"] is True
    assert task_properties["user_forced_review"]["const"] is True
    verification_schema = task_properties["verification_commands"]
    assert verification_schema["required"] == list(REQUIRED_VERIFICATION_COMMANDS)
    model_policy_schema = schema["properties"]["model_policy"]
    assert model_policy_schema["required"] == ["model", "reasoning_effort"]
    assert model_policy_schema["properties"]["model"]["type"] == "string"
    assert model_policy_schema["properties"]["reasoning_effort"]["enum"] == [
        "low",
        "medium",
        "high",
        "xhigh",
        "max",
    ]
    orchestration_schema = schema["properties"]["orchestration_constraints"]
    assert orchestration_schema["required"] == [
        "profile",
        "mode_preference",
        "max_concurrent_subagents",
        "max_total_subagents",
        "max_tree_depth",
        "write_conflict_policy",
        "stop_policy",
    ]
    orchestration_properties = orchestration_schema["properties"]
    assert orchestration_properties["mode_preference"]["enum"] == [
        "auto",
        "single_agent",
        "multi_agent",
    ]
    assert orchestration_properties["max_concurrent_subagents"]["maximum"] == 3
    assert orchestration_properties["max_total_subagents"]["maximum"] == 6
    assert orchestration_properties["max_tree_depth"]["maximum"] == 1
    zero_budget_then = orchestration_schema["allOf"][0]["then"]["properties"]
    assert zero_budget_then["max_total_subagents"]["const"] == 0
    assert zero_budget_then["max_tree_depth"]["const"] == 0
    enabled_budget_then = orchestration_schema["allOf"][1]["then"]["properties"]
    assert enabled_budget_then["max_total_subagents"]["minimum"] == 1
    assert enabled_budget_then["max_tree_depth"]["const"] == 1


def test_legacy_manifest_normalizes_to_safe_observe_defaults() -> None:
    payload = load_mapping_file(REPO_ROOT / "templates" / "agent-work-manifest.example.yaml")
    payload.pop("schema_version")
    payload.pop("orchestration_constraints")

    validate_manifest_payload(payload)
    normalized = normalize_manifest_payload(payload)

    assert normalized["schema_version"] == "agent_work_manifest.v1"
    assert normalized["orchestration_constraints"] == DEFAULT_ORCHESTRATION_CONSTRAINTS


def test_manifest_rejects_repo_escape_path_patterns() -> None:
    payload = load_mapping_file(REPO_ROOT / "templates" / "agent-work-manifest.example.yaml")
    payload["tasks"][0]["read_set"] = ["../outside/**"]

    try:
        validate_manifest_payload(payload)
    except ValueError as exc:
        assert "must not escape the repo" in str(exc)
    else:
        raise AssertionError("expected repo-escape read_set to be rejected")


def test_manifest_orchestration_constraints_enforce_bounded_delegation() -> None:
    payload = load_mapping_file(REPO_ROOT / "templates" / "agent-work-manifest.example.yaml")
    constraints = payload["orchestration_constraints"]
    assert isinstance(constraints, dict)

    constraints.update(
        {
            "max_concurrent_subagents": 0,
            "max_total_subagents": 0,
            "max_tree_depth": 0,
        }
    )
    validate_manifest_payload(payload)

    constraints.update(
        {
            "max_concurrent_subagents": 3,
            "max_total_subagents": 2,
            "max_tree_depth": 1,
        }
    )
    try:
        validate_manifest_payload(payload)
    except ValueError as exc:
        assert "max_concurrent_subagents cannot exceed max_total_subagents" in str(exc)
    else:
        raise AssertionError("expected inverted subagent budgets to be rejected")

    constraints.update(
        {
            "max_concurrent_subagents": 4,
            "max_total_subagents": 6,
        }
    )
    try:
        validate_manifest_payload(payload)
    except ValueError as exc:
        assert "max_concurrent_subagents must be between 0 and 3" in str(exc)
    else:
        raise AssertionError("expected excessive subagent concurrency to be rejected")

    constraints.update(
        {
            "max_concurrent_subagents": 3,
            "max_total_subagents": 7,
            "max_tree_depth": 1,
        }
    )
    try:
        validate_manifest_payload(payload)
    except ValueError as exc:
        assert "max_total_subagents must be between 0 and 6" in str(exc)
    else:
        raise AssertionError("expected excessive total subagent budget to be rejected")

    constraints.update(
        {
            "max_concurrent_subagents": 3,
            "max_total_subagents": 6,
            "max_tree_depth": 2,
        }
    )
    try:
        validate_manifest_payload(payload)
    except ValueError as exc:
        assert "max_tree_depth must be 1" in str(exc)
    else:
        raise AssertionError("expected nested subagent depth to be rejected")


def test_manifest_force_on_overrides_allow_true_but_reject_false() -> None:
    payload = load_mapping_file(REPO_ROOT / "templates" / "agent-work-manifest.example.yaml")
    first_task = payload["tasks"][0]
    assert isinstance(first_task, dict)

    first_task["user_forced_planner"] = True
    first_task["user_forced_review"] = True
    validate_manifest_payload(payload)

    first_task["user_forced_planner"] = False
    try:
        validate_manifest_payload(payload)
    except ValueError as exc:
        assert "user_forced_planner only allows true" in str(exc)
    else:
        raise AssertionError("expected false user_forced_planner override to be rejected")

    first_task["user_forced_planner"] = True
    first_task["user_forced_review"] = False
    try:
        validate_manifest_payload(payload)
    except ValueError as exc:
        assert "user_forced_review only allows true" in str(exc)
    else:
        raise AssertionError("expected false user_forced_review override to be rejected")


def test_dispatch_state_template_is_machine_readable() -> None:
    payload = load_mapping_file(REPO_ROOT / "templates" / "dispatch-state.example.json")

    validate_dispatch_state_payload(payload)

    schema = json.loads((REPO_ROOT / "templates" / "dispatch-state.schema.json").read_text(encoding="utf-8"))
    assert schema["required"] == [
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
    ]
    assert schema["properties"]["status"]["enum"] == [
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
    ]
    assert schema["properties"]["resume_point"]["enum"] == [
        "task_intake",
        "worker_execution",
        "verification",
        "handoff",
        "cleanup",
    ]
    assert schema["properties"]["retry_rewind"]["enum"] == [
        "task_intake",
        "worker_execution",
        "verification",
        "handoff",
        "cleanup",
    ]
    assert schema["properties"]["planner_result_ref"]["type"] == "string"
    assert schema["properties"]["handoff_receipt_ref"]["type"] == "string"
    assert schema["properties"]["review_result_ref"]["type"] == "string"
    assert schema["properties"]["closeout_bundle_ref"]["type"] == "string"


def test_closeout_bundle_template_captures_cleanup_and_truth_boundary() -> None:
    payload = load_mapping_file(REPO_ROOT / "templates" / "closeout-bundle.example.json")

    validate_closeout_bundle_payload(payload)

    schema = json.loads((REPO_ROOT / "templates" / "closeout-bundle.schema.json").read_text(encoding="utf-8"))
    assert "cleanup_status" in schema["required"]
    assert "repo_side_done" in schema["required"]
    assert "still_open" in schema["required"]
    assert schema["properties"]["cleanup_status"]["enum"] == [
        "deferred",
        "inline_only",
        "cleaned",
        "cleanup_failed",
    ]
    assert schema["properties"]["tests"]["items"]["properties"]["status"]["enum"] == [
        "pass",
        "fail",
        "skipped",
        "gate_na",
    ]
    assert schema["properties"]["handoff_receipt_ref"]["type"] == "string"


def test_handoff_receipt_template_aligns_with_pre_worker_handoff_contract() -> None:
    payload = load_mapping_file(REPO_ROOT / "templates" / "handoff-receipt.example.json")

    validate_handoff_receipt_payload(payload)

    schema = json.loads((REPO_ROOT / "templates" / "handoff-receipt.schema.json").read_text(encoding="utf-8"))
    assert schema["required"] == [
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
    ]
    assert schema["properties"]["receipt_kind"]["enum"] == ["pre_worker_handoff"]
    assert "selected_lane_runner_not_wired" in schema["properties"]["reason_codes"]["items"]["enum"]
    assert schema["properties"]["worker_execution_attempted"]["type"] == "boolean"


def test_review_result_template_aligns_with_review_contract() -> None:
    payload = load_mapping_file(REPO_ROOT / "templates" / "review-result.example.json")

    validate_review_result_payload(payload)

    schema = json.loads((REPO_ROOT / "templates" / "review-result.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["reviewer_kind"]["enum"] == [
        "claude_glm",
        "codex_review",
        "gpt54_direct_review",
    ]
    assert schema["properties"]["review_mode"]["enum"] == ["advisory", "blocking"]
    assert schema["properties"]["recommended_action"]["enum"] == ["approve", "revise", "reject"]
    finding_required = schema["properties"]["findings"]["items"]["required"]
    assert finding_required == ["severity", "category", "title", "detail", "suggested_fix"]


def test_planner_result_template_aligns_with_planner_contract() -> None:
    payload = load_mapping_file(REPO_ROOT / "templates" / "planner-result.example.json")

    validate_planner_result_payload(payload)

    schema = json.loads((REPO_ROOT / "templates" / "planner-result.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["planner_kind"]["enum"] == [
        "codex_sdk",
        "gpt54_direct",
        "repo_policy_gate",
    ]
    assert schema["properties"]["planner_mode"]["enum"] == ["advisory", "blocking"]
    assert schema["properties"]["disposition"]["enum"] == ["proceed", "handoff"]


def test_runner_acceptance_template_aligns_with_non_host_local_guard() -> None:
    payload = load_mapping_file(REPO_ROOT / "templates" / "non-host-local-runner-acceptance.example.json")

    validate_runner_acceptance_payload(payload)

    schema = json.loads(
        (REPO_ROOT / "templates" / "non-host-local-runner-acceptance.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert schema["required"] == [
        "schema_version",
        "acceptance_status",
        "worker_profile",
        "lane",
        "runner_kind",
        "accepted_by",
        "accepted_at",
        "acceptance_scope",
        "evidence_refs",
    ]
    assert schema["properties"]["schema_version"]["const"] == RUNNER_ACCEPTANCE_SCHEMA_VERSION
    assert schema["properties"]["acceptance_status"]["const"] == "accepted"
    assert schema["properties"]["lane"]["enum"] == ["remote_non_gui", "vm_gui"]
    assert schema["properties"]["evidence_refs"]["minItems"] == 1
