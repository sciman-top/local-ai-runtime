from __future__ import annotations

import json

from host_orchestrator.agent_work_assets import (
    MODEL_NAME,
    REASONING_EFFORT,
    REQUIRED_VERIFICATION_COMMANDS,
    load_mapping_file,
    validate_closeout_bundle_payload,
    validate_dispatch_state_payload,
    validate_manifest_payload,
    validate_review_result_payload,
)

from support import REPO_ROOT


def test_manifest_template_aligns_with_repo_owned_contract() -> None:
    payload = load_mapping_file(REPO_ROOT / "templates" / "agent-work-manifest.example.yaml")

    validate_manifest_payload(payload)

    schema = json.loads((REPO_ROOT / "templates" / "agent-work-manifest.schema.json").read_text(encoding="utf-8"))
    assert "tasks" in schema["required"]
    assert "model_policy" in schema["required"]
    task_properties = schema["properties"]["tasks"]["items"]["properties"]
    assert "depends_on" in task_properties
    assert "blocked_by" not in task_properties
    assert task_properties["user_forced_planner"]["const"] is True
    assert task_properties["user_forced_review"]["const"] is True
    verification_schema = task_properties["verification_commands"]
    assert verification_schema["required"] == list(REQUIRED_VERIFICATION_COMMANDS)
    assert schema["properties"]["model_policy"]["properties"]["model"]["const"] == MODEL_NAME
    assert schema["properties"]["model_policy"]["properties"]["reasoning_effort"]["const"] == REASONING_EFFORT


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
        "source_manifest_ref",
        "lease_owner",
        "started_at",
        "heartbeat_at",
        "status",
        "next_action",
    ]
    assert schema["properties"]["status"]["enum"] == [
        "pending",
        "running",
        "completed",
        "failed",
        "blocked",
        "stale",
        "closed",
    ]


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
