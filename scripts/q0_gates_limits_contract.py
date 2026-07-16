"""Stdlib-only verifier for the v3.25 Q0, gate, feature and limit bundle."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable


Q0_BUNDLE_PATHS = {
    "catalog": Path(
        "docs/specs/local-ai-runtime-0.2/normative/QualificationGateCatalog.v1.json"
    ),
    "feature": Path(
        "docs/specs/local-ai-runtime-0.2/catalogs/CodexFeaturePolicy.v1.json"
    ),
    "limits": Path(
        "docs/specs/local-ai-runtime-0.2/catalogs/ResourceLimitPolicy.v1.json"
    ),
    "fixture": Path(
        "docs/specs/local-ai-runtime-0.2/fixtures/q0/manifest.json"
    ),
}

EXPECTED_Q0_BUNDLE_IDENTITIES = {
    "catalog": {
        "byte_count": 16513,
        "sha256": "bad2899fa6af96af2800d05d6c78e0e17ebf9ac08ecb5d89b68518630a31070b",
    },
    "feature": {
        "byte_count": 4274,
        "sha256": "6b61e82dfb4051b6da52cfd104ed3ed9b070e076d914bf45f3c06f345c1865aa",
    },
    "limits": {
        "byte_count": 9009,
        "sha256": "d28327965428f2be9789758cb47aba7fcc2f279de3d6ed8c48a19f57221ef590",
    },
    "fixture": {
        "byte_count": 10990,
        "sha256": "efed4e6cb06a1c1d1a11c44721c316274894cc915087908f186461898952f708",
    },
}

EXPECTED_GATE_ORDER = [
    "supply_chain_identity",
    "build",
    "test",
    "contract_invariant",
    "hotspot",
]

EXPECTED_VALIDATION_CLASSES = {"full_q0", "quick_preflight", "daily_canary"}

EXPECTED_Q0_PROBE_SETS = {
    "binary_toolchain",
    "codex_capability_surface",
    "sandbox_auth",
    "permission_network",
    "process_isolation",
    "windows_objects",
    "filesystem_resource",
    "stream_adapter",
    "gate_environment",
    "git",
    "recovery",
    "operations",
    "platform_capability_composition",
}

EXPECTED_ENVIRONMENT_CASES = {
    "empty_environment",
    "one_entry",
    "case_collision",
    "invalid_key",
    "value_limit_minus_one",
    "value_limit",
    "value_limit_plus_one",
    "invalid_double_nul",
    "create_process_flag_mismatch",
}

EXPECTED_ENVIRONMENT_ALLOWLIST = [
    "CODEX_HOME",
    "CODEX_SQLITE_HOME",
    "HOME",
    "USERPROFILE",
    "APPDATA",
    "LOCALAPPDATA",
    "XDG_CONFIG_HOME",
    "TEMP",
    "TMP",
    "SYSTEMROOT",
    "WINDIR",
    "COMSPEC",
    "PATHEXT",
    "PATH",
]

EXPECTED_RESOURCE_LIMITS = {
    "writer_wall_time_ms": (3600000, "milliseconds", "controller_deadline"),
    "gate_wall_time_ms": (1800000, "milliseconds", "controller_deadline"),
    "all_gates_cumulative_wall_time_ms": (
        7200000,
        "milliseconds",
        "controller_deadline",
    ),
    "deterministic_closeout_wall_time_ms": (
        900000,
        "milliseconds",
        "controller_deadline",
    ),
    "attempt_wall_time_ms": (11700000, "milliseconds", "controller_deadline"),
    "scheduled_invocation_wall_time_ms": (
        12600000,
        "milliseconds",
        "controller_deadline",
    ),
    "writer_jsonl_stdout_aggregate_bytes": (8388608, "bytes", "bounded_reader"),
    "writer_stderr_bytes": (8388608, "bytes", "bounded_reader"),
    "jsonl_line_before_lf_bytes": (262144, "bytes", "bounded_parser"),
    "normalized_journal_aggregate_bytes": (8388608, "bytes", "bounded_writer"),
    "normalized_event_bytes": (16384, "bytes", "bounded_writer"),
    "writer_final_result_bytes": (1048576, "bytes", "bounded_parser"),
    "non_writer_stream_bytes": (8388608, "bytes", "bounded_reader"),
    "validated_diff_representation_bytes": (16777216, "bytes", "bounded_parser"),
    "changed_paths": (200, "count", "bounded_parser"),
    "validated_changed_regular_file_bytes": (33554432, "bytes", "bounded_reader"),
    "validated_changed_file_aggregate_bytes": (
        268435456,
        "bytes",
        "bounded_reader",
    ),
    "published_artifact_aggregate_bytes": (268435456, "bytes", "bounded_writer"),
    "gate_run_writable_cache_output_bytes": (
        536870912,
        "bytes",
        "accounting_kill_audit",
    ),
    "gate_run_writable_entries": (20000, "count", "accounting_kill_audit"),
    "attempt_writable_growth_bytes": (
        2147483648,
        "bytes",
        "accounting_kill_audit",
    ),
    "attempt_writable_entries": (50000, "count", "accounting_kill_audit"),
    "attempt_local_git_object_store_growth_bytes": (
        536870912,
        "bytes",
        "accounting_kill_audit",
    ),
    "common_store_promoted_object_growth_bytes": (
        536870912,
        "bytes",
        "bounded_writer",
    ),
    "attempts_per_task_generation": (3, "count", "state_guard"),
    "process_tree_active_processes": (64, "count", "job_limit"),
    "per_process_committed_memory_bytes": (4294967296, "bytes", "job_limit"),
    "process_bearing_job_committed_memory_bytes": (
        8589934592,
        "bytes",
        "job_limit",
    ),
}

EXPECTED_PROCESS_INPUT_LIMITS = {
    "environment_value_utf16_code_units": (
        8191,
        "utf16_code_units",
        "bounded_parser",
    ),
    "environment_block_utf16_code_units": (
        32767,
        "utf16_code_units_including_double_nul",
        "bounded_serializer",
    ),
    "create_process_command_line_utf16_code_units": (
        32766,
        "utf16_code_units_excluding_terminal_nul",
        "bounded_serializer",
    ),
    "permission_overlay_assignment_count": (64, "count", "bounded_serializer"),
    "permission_overlay_aggregate_utf16_code_units": (
        16384,
        "utf16_code_units",
        "bounded_serializer",
    ),
    "pipe_eof_after_job_terminal_ms": (
        5000,
        "milliseconds",
        "controller_deadline",
    ),
}

EXPECTED_NEGATIVE_MUTATIONS = {
    "gate_shell_placeholder": "q0_gate_command",
    "gate_missing_managed_config": "q0_gate_command",
    "unknown_effective_capability_ignored": "q0_feature_policy",
    "environment_case_sensitive_uniqueness": "q0_environment_policy",
    "child_pre_resume_observation_claim": "q0_environment_proof",
    "job_termination_implies_eof": "q0_process_handle_policy",
    "dpapi_proves_purpose_separation": "q0_external_evidence_dpapi",
    "restore_multi_consumption": "q0_external_evidence_dpapi",
    "resource_boundary_removed": "q0_fixture_resource_boundaries",
    "hard_quota_made_mandatory": "q0_resource_limits",
    "accounting_fallback_too_slow": "q0_write_accounting",
    "disk_pressure_maps_environment": "q0_disk_pressure",
}


class Q0BundleValidationError(RuntimeError):
    """Raised with a stable reason code for a Q0 bundle failure."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def _object(value: Any, label: str, reason: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise Q0BundleValidationError(reason, f"{label} must be an object")
    return value


def _array(value: Any, label: str, reason: str) -> list[Any]:
    if not isinstance(value, list):
        raise Q0BundleValidationError(reason, f"{label} must be an array")
    return value


def _exact(
    value: Any, fields: set[str], label: str, reason: str
) -> dict[str, Any]:
    result = _object(value, label, reason)
    if set(result) != fields:
        raise Q0BundleValidationError(reason, f"{label} fields mismatch")
    return result


def _string_array(value: Any, label: str, reason: str) -> list[str]:
    result = _array(value, label, reason)
    if not all(isinstance(item, str) and item for item in result):
        raise Q0BundleValidationError(reason, f"{label} must contain strings")
    if len(result) != len(set(result)):
        raise Q0BundleValidationError(reason, f"{label} contains duplicates")
    return result


def _contains_null(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, dict):
        return any(_contains_null(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_null(item) for item in value)
    return False


def _load(root: Path, key: str) -> tuple[dict[str, Any], bytes]:
    relative = Q0_BUNDLE_PATHS[key]
    try:
        raw = (root / relative).read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Q0BundleValidationError(
            "q0_bundle_json", f"cannot read {relative.as_posix()}"
        ) from exc
    if not isinstance(value, dict) or _contains_null(value):
        raise Q0BundleValidationError(
            "q0_bundle_json", f"{relative.as_posix()} must be a null-free object"
        )
    return value, raw


def _validate_gate_command(gate: dict[str, Any]) -> None:
    _exact(
        gate,
        {
            "gate_id",
            "profile",
            "executable_ref",
            "argv",
            "environment_digest_ref",
            "cwd_ref",
            "timeout_ms",
            "expected_report",
            "failure_scope",
        },
        "gate run",
        "q0_gate_command",
    )
    argv = _string_array(gate["argv"], "gate argv", "q0_gate_command")
    if (
        not isinstance(gate["executable_ref"], str)
        or not gate["executable_ref"].startswith("RuntimeToolchainManifest.v1.executables.")
        or not gate["executable_ref"].endswith(".absolute_path")
        or not isinstance(gate["environment_digest_ref"], str)
        or not gate["environment_digest_ref"].endswith(".sha256")
        or not isinstance(gate["cwd_ref"], str)
        or "final_identity" not in gate["cwd_ref"]
        or not isinstance(gate["timeout_ms"], int)
        or gate["timeout_ms"] <= 0
        or not isinstance(gate["expected_report"], str)
        or not gate["expected_report"].endswith(".v1")
    ):
        raise Q0BundleValidationError("q0_gate_command", "gate binding is not exact")
    rendered = " ".join(argv)
    if any(token in rendered for token in ("<", ">", "...", "${", "$(")):
        raise Q0BundleValidationError(
            "q0_gate_command", "gate argv contains a shell placeholder"
        )
    if gate["profile"] in {"batch-gate", "batch-git-audit", "batch-git-local"}:
        if "--include-managed-config" not in argv:
            raise Q0BundleValidationError(
                "q0_gate_command", "managed sandbox or Git gate omitted managed config"
            )


def _validate_environment_policy(policy: dict[str, Any]) -> None:
    if (
        policy.get("policy_id") != "ProcessEnvironmentPolicy.v1"
        or policy.get("construction") != "from_empty_environment"
        or policy.get("public_allowlist") != EXPECTED_ENVIRONMENT_ALLOWLIST
    ):
        raise Q0BundleValidationError(
            "q0_environment_policy", "process environment identity mismatch"
        )
    key_contract = _object(
        policy.get("key_contract"), "key contract", "q0_environment_policy"
    )
    required_rejects = {
        "empty_key",
        "equals_in_key",
        "nul_in_key",
        "nul_in_value",
        "case_alias",
        "duplicate_key",
        "hidden_equals_prefixed_entry",
        "drive_current_directory_pseudo_variable",
    }
    if (
        key_contract.get("catalog_spelling") != "ascii"
        or key_contract.get("uniqueness") != "OrdinalIgnoreCase"
        or set(_string_array(key_contract.get("reject"), "environment rejects", "q0_environment_policy"))
        != required_rejects
    ):
        raise Q0BundleValidationError(
            "q0_environment_policy", "environment key rules mismatch"
        )
    serialization = _object(
        policy.get("serialization"), "serialization", "q0_environment_policy"
    )
    if serialization != {
        "encoding": "UTF-16LE",
        "sort": "Windows_OrdinalIgnoreCase",
        "entry_form": "key_equals_value_then_utf16_nul",
        "terminal_form": "exactly_two_trailing_utf16_nul_code_units",
        "inherited_block_allowed": False,
        "digest": "sha256_full_serialized_bytes",
    }:
        raise Q0BundleValidationError(
            "q0_environment_policy", "environment serialization mismatch"
        )
    if policy.get("create_process_flags") != [
        "CREATE_UNICODE_ENVIRONMENT",
        "CREATE_SUSPENDED",
        "EXTENDED_STARTUPINFO_PRESENT",
    ]:
        raise Q0BundleValidationError(
            "q0_environment_policy", "CreateProcess flags mismatch"
        )
    if policy.get("resource_limit_refs") != [
        "environment_value_utf16_code_units",
        "environment_block_utf16_code_units",
        "create_process_command_line_utf16_code_units",
        "permission_overlay_assignment_count",
        "permission_overlay_aggregate_utf16_code_units",
    ]:
        raise Q0BundleValidationError(
            "q0_environment_policy", "environment resource limit references mismatch"
        )
    proof = _object(policy.get("two_stage_proof"), "two-stage proof", "q0_environment_proof")
    parent = _object(
        proof.get("pre_resume_parent_environment_proof"),
        "parent proof",
        "q0_environment_proof",
    )
    child = _object(
        proof.get("post_resume_q0_child_environment_observation"),
        "child observation",
        "q0_environment_proof",
    )
    production = _object(
        proof.get("production_launch"), "production launch", "q0_environment_proof"
    )
    parent_binds = {
        "canonical_utf16_bytes",
        "key_grammar",
        "ordinal_ignore_case_uniqueness",
        "ordering",
        "per_value_and_aggregate_limits",
        "double_nul_terminator",
        "sha256",
        "create_process_flags",
    }
    if (
        parent.get("claim_scope") != "parent_input_only"
        or set(_string_array(parent.get("binds"), "parent proof bindings", "q0_environment_proof"))
        != parent_binds
        or parent.get("mismatch_action") != "terminate_suspended_job_before_resume"
        or child.get("actor") != "dedicated_no_write_q0_child"
        or child.get("timing") != "first_application_action_after_resume"
        or child.get("api") != "GetEnvironmentStringsW"
        or child.get("comparison")
        != "child_canonical_digest_equals_parent_proof_digest"
        or child.get("mismatch_result") != "platform_incompatible"
        or proof.get("forbidden_claim")
        != "child_observed_or_reported_its_environment_before_ResumeThread"
        or production.get("per_launch_parent_proof") is not True
        or production.get("per_child_q0_probe") is not False
        or production.get("never_claim_per_child_pre_resume_environment_read_back")
        is not True
    ):
        raise Q0BundleValidationError(
            "q0_environment_proof", "two-stage environment proof mismatch"
        )


def _validate_process_handle_policy(policy: dict[str, Any]) -> None:
    if policy.get("policy_id") != "ProcessHandlePolicy.v1":
        raise Q0BundleValidationError(
            "q0_process_handle_policy", "process handle identity mismatch"
        )
    creation = _object(policy.get("creation"), "process creation", "q0_process_handle_policy")
    manifest = _object(
        policy.get("child_handle_manifest"),
        "child handle manifest",
        "q0_process_handle_policy",
    )
    eof = _object(policy.get("eof_proof"), "EOF proof", "q0_process_handle_policy")
    if (
        creation.get("suspended") is not True
        or creation.get("attribute_list")
        != ["PROC_THREAD_ATTRIBUTE_JOB_LIST", "PROC_THREAD_ATTRIBUTE_HANDLE_LIST"]
        or creation.get("startup_flag") != "STARTF_USESTDHANDLES"
        or manifest.get("manifest_version") != "ChildHandleManifest.v1"
        or manifest.get("ambient_sensitive_handles") != "deny"
        or manifest.get("parent_child_pipe_ends_closed_before_resume") is not True
        or set(eof.get("scenarios", []))
        != {"normal_exit", "job_kill", "controller_crash_recovery", "response_loss"}
        or set(eof.get("required_conditions", []))
        != {
            "all_parent_and_descendant_writer_handles_closed",
            "job_zero_processes",
            "all_pipes_observed_eof",
            "stage_launch_record_terminal",
        }
        or eof.get("job_termination_alone_implies_eof") is not False
        or eof.get("bounded_after_job_terminal_ms") != 5000
        or eof.get("resource_limit_ref") != "pipe_eof_after_job_terminal_ms"
        or eof.get("last_job_handle_closed_required_for_kill_on_close") is not True
    ):
        raise Q0BundleValidationError(
            "q0_process_handle_policy", "process handle or EOF contract mismatch"
        )


def _validate_external_evidence_dpapi(policy: dict[str, Any]) -> None:
    external = _object(
        policy.get("external_evidence_policy"),
        "external evidence policy",
        "q0_external_evidence_dpapi",
    )
    envelopes = _object(
        policy.get("dpapi_envelopes"), "DPAPI envelopes", "q0_external_evidence_dpapi"
    )
    restore = _object(
        policy.get("restore_eligibility"),
        "restore eligibility",
        "q0_external_evidence_dpapi",
    )
    if (
        external.get("mode") != "runtime_external_v1"
        or external.get("operator_absolute_path_allowed") is not False
        or external.get("task_process_access") != "deny_read_write"
        or envelopes.get("scope") != "current_user"
        or envelopes.get("purpose_separation_required") is not True
        or envelopes.get("plaintext_or_plaintext_hash_persisted") is not False
        or envelopes.get("dpapi_alone_proves_application_invariants") is not False
        or envelopes.get("quarantine", {}).get("purpose") != "quarantine_encryption"
        or envelopes.get("runtime_integrity", {}).get("purpose") != "runtime_integrity"
        or restore.get("head") != "BackupRestoreEligibility.v1"
        or set(restore.get("states", [])) != {"eligible", "stale", "restoring", "consumed"}
        or restore.get("single_consumption") is not True
        or restore.get("same_sid_unwrap_required") is not True
        or restore.get("post_restore_state") != "suspended"
    ):
        raise Q0BundleValidationError(
            "q0_external_evidence_dpapi", "evidence, DPAPI or restore contract mismatch"
        )


def _validate_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    _exact(catalog, {"domain", "payload", "schema_version"}, "Q0 catalog", "q0_catalog")
    payload = _object(catalog["payload"], "Q0 catalog payload", "q0_catalog")
    if (
        catalog["domain"] != "local-ai-runtime/QualificationGateCatalog/v1"
        or catalog["schema_version"] != 1
        or payload.get("artifact_version") != "QualificationGateCatalog.v1"
        or payload.get("baseline_id") != "local-ai-runtime-0.2-v3.25"
        or payload.get("status") != "normative_preimplementation_contract"
    ):
        raise Q0BundleValidationError("q0_catalog", "Q0 catalog identity mismatch")
    classes = _array(payload.get("validation_classes"), "validation classes", "q0_catalog")
    if {item.get("class_id") for item in classes if isinstance(item, dict)} != EXPECTED_VALIDATION_CLASSES:
        raise Q0BundleValidationError("q0_catalog", "validation class set mismatch")
    full_q0 = next(item for item in classes if item.get("class_id") == "full_q0")
    if full_q0.get("live_execution_allowed_during_contract_authoring") is not False:
        raise Q0BundleValidationError("q0_catalog", "live Q0 authoring boundary changed")
    graph = _object(payload.get("gate_graph"), "gate graph", "q0_gate_graph")
    if (
        graph.get("graph_id") != "GateGraph.v1"
        or graph.get("fixed_stage_order") != EXPECTED_GATE_ORDER
        or graph.get("qualification_precedes_activation") is not True
        or graph.get("environment_preparation_is_gate") is not False
    ):
        raise Q0BundleValidationError("q0_gate_graph", "gate graph mismatch")
    gates = _array(payload.get("gate_runs"), "gate runs", "q0_gate_command")
    if len(gates) < 6:
        raise Q0BundleValidationError("q0_gate_command", "gate catalog is incomplete")
    for gate in gates:
        _validate_gate_command(_object(gate, "gate run", "q0_gate_command"))
    trigger = _object(
        payload.get("q0_trigger_policy"), "Q0 trigger policy", "q0_trigger_policy"
    )
    if (
        trigger.get("policy_id") != "Q0TriggerPolicy.v1"
        or trigger.get("operator_override_allowed") is not False
        or trigger.get("unknown_classification") != "full_q0"
        or "binary_model_effort_profile_feature_config_or_tool_version"
        not in trigger.get("full_q0_triggers", [])
    ):
        raise Q0BundleValidationError("q0_trigger_policy", "Q0 trigger policy mismatch")
    activation = _object(
        payload.get("activation_admission_chain"),
        "activation chain",
        "q0_activation_chain",
    )
    if (
        activation.get("chain_id") != "activation_admission_chain_v1"
        or activation.get("activate_before_full_q0") is not False
        or activation.get("full_q0_selects_runtime") is not False
        or activation.get("active_terminal_result")
        != "activated_and_preflight_passed"
    ):
        raise Q0BundleValidationError("q0_activation_chain", "activation chain mismatch")
    probe_sets = _array(payload.get("q0_probe_sets"), "Q0 probe sets", "q0_probe_sets")
    by_set = {
        item.get("set_id"): item
        for item in probe_sets
        if isinstance(item, dict) and isinstance(item.get("set_id"), str)
    }
    if set(by_set) != EXPECTED_Q0_PROBE_SETS or any(
        not _string_array(item.get("probe_ids"), "probe IDs", "q0_probe_sets")
        for item in by_set.values()
    ):
        raise Q0BundleValidationError("q0_probe_sets", "Q0 probe set mismatch")
    _validate_environment_policy(
        _object(payload.get("process_environment_policy"), "environment policy", "q0_environment_policy")
    )
    _validate_process_handle_policy(
        _object(payload.get("process_handle_policy"), "process handle policy", "q0_process_handle_policy")
    )
    _validate_external_evidence_dpapi(
        _object(
            payload.get("external_evidence_and_dpapi"),
            "external evidence and DPAPI",
            "q0_external_evidence_dpapi",
        )
    )
    failure = _object(
        payload.get("failure_scope_policy"), "failure scope policy", "q0_failure_scope"
    )
    mappings = _array(failure.get("mappings"), "failure mappings", "q0_failure_scope")
    if (
        {item.get("scope") for item in mappings if isinstance(item, dict)}
        < {"platform", "repo", "template", "attempt"}
        or failure.get("unknown_scope") != "platform_incompatible"
        or failure.get("successful_unauthorized_egress_never_scoped_to_template")
        is not True
    ):
        raise Q0BundleValidationError("q0_failure_scope", "failure scope mismatch")
    return {"validation_class_count": len(classes), "q0_probe_set_count": len(probe_sets)}


def _validate_feature_policy(policy: dict[str, Any]) -> dict[str, Any]:
    if (
        policy.get("catalog_version") != "CodexFeaturePolicy.v1"
        or policy.get("baseline_id") != "local-ai-runtime-0.2-v3.25"
        or policy.get("unknown_effective_capability") != "fail_incompatible"
        or policy.get("generation_axes")
        != ["profile_generation", "capability_generation", "architecture_epoch"]
    ):
        raise Q0BundleValidationError("q0_feature_policy", "feature policy identity mismatch")
    surfaces = _array(
        policy.get("required_runtime_surfaces"), "runtime surfaces", "q0_feature_policy"
    )
    if {item.get("surface_id") for item in surfaces if isinstance(item, dict)} != {
        "cli_execution_interface",
        "app_server_client_protocol",
        "managed_worktree_isolation",
        "automations_scheduling",
    } or any(
        item.get("qualification") != "independent_full_q0"
        or item.get("composition_probe_required") is not True
        for item in surfaces
        if isinstance(item, dict)
    ):
        raise Q0BundleValidationError("q0_feature_policy", "runtime surface policy mismatch")
    managed = _object(
        policy.get("include_managed_config_contract"),
        "managed config contract",
        "q0_feature_policy",
    )
    if (
        set(managed.get("required_for_profiles", []))
        != {"batch-gate", "batch-git-audit", "batch-git-local"}
        or managed.get("required_argv_token") != "--include-managed-config"
        or managed.get("omission_result") != "platform_incompatible"
    ):
        raise Q0BundleValidationError("q0_feature_policy", "managed config policy mismatch")
    features = _array(policy.get("effective_features"), "effective features", "q0_feature_policy")
    feature_ids = {item.get("feature_id") for item in features if isinstance(item, dict)}
    if len(features) != len(feature_ids) or not {
        "strict_config",
        "task_network",
        "gate_network",
        "git_network",
        "sandbox_secret_state",
        "hard_write_quota",
    }.issubset(feature_ids):
        raise Q0BundleValidationError("q0_feature_policy", "effective feature set mismatch")
    return {"effective_feature_count": len(features), "surface_count": len(surfaces)}


def _validate_resource_limits(policy: dict[str, Any]) -> dict[str, Any]:
    if (
        policy.get("catalog_version") != "ResourceLimitPolicy.v1"
        or policy.get("baseline_id") != "local-ai-runtime-0.2-v3.25"
        or policy.get("unit_definitions", {}).get("MiB") != 1048576
        or policy.get("unit_definitions", {}).get("GiB") != 1073741824
    ):
        raise Q0BundleValidationError("q0_resource_limits", "resource policy identity mismatch")
    limits = _array(policy.get("limits"), "resource limits", "q0_resource_limits")
    by_id = {
        item.get("limit_id"): item
        for item in limits
        if isinstance(item, dict) and isinstance(item.get("limit_id"), str)
    }
    if set(by_id) != set(EXPECTED_RESOURCE_LIMITS) or len(limits) != len(by_id):
        raise Q0BundleValidationError("q0_resource_limits", "resource limit set mismatch")
    for limit_id, (ceiling, unit, enforcement) in EXPECTED_RESOURCE_LIMITS.items():
        item = by_id[limit_id]
        if (
            item.get("ceiling") != ceiling
            or item.get("unit") != unit
            or item.get("enforcement_class") != enforcement
            or not isinstance(item.get("failure_scope"), str)
        ):
            raise Q0BundleValidationError(
                "q0_resource_limits", f"resource limit mismatch: {limit_id}"
            )
    process_limits = _array(
        policy.get("process_input_limits"),
        "process input limits",
        "q0_resource_limits",
    )
    process_by_id = {
        item.get("limit_id"): item
        for item in process_limits
        if isinstance(item, dict) and isinstance(item.get("limit_id"), str)
    }
    if set(process_by_id) != set(EXPECTED_PROCESS_INPUT_LIMITS):
        raise Q0BundleValidationError(
            "q0_resource_limits", "process input limit set mismatch"
        )
    for limit_id, (ceiling, unit, enforcement) in EXPECTED_PROCESS_INPUT_LIMITS.items():
        item = process_by_id[limit_id]
        if (
            item.get("ceiling") != ceiling
            or item.get("unit") != unit
            or item.get("enforcement_class") != enforcement
            or not isinstance(item.get("failure_scope"), str)
        ):
            raise Q0BundleValidationError(
                "q0_resource_limits", f"process input limit mismatch: {limit_id}"
            )
    accounting = _object(
        policy.get("write_accounting_policy"),
        "write accounting policy",
        "q0_write_accounting",
    )
    if (
        accounting.get("policy_id") != "WriteAccountingPolicy.v1"
        or accounting.get("mandatory_mode") != "accounting_kill_audit"
        or accounting.get("fallback_rescan_max_interval_ms", 501) > 500
        or accounting.get("limit_plus_one_sequence")
        != [
            "persist_resource_limit_exceeded_intent",
            "terminate_job_under_current_fence",
            "drain_all_pipes_to_eof",
            "persist_final_counts_and_reason",
            "seal_journal_segment",
            "durable_recovery_handoff",
            "no_follow_final_audit",
        ]
        or accounting.get("publication_after_limit_plus_one") is not False
        or accounting.get("atomic_prewrite_denial_claim") is not False
    ):
        raise Q0BundleValidationError("q0_write_accounting", "write accounting mismatch")
    reserve = _object(
        policy.get("emergency_disk_reserve"),
        "emergency reserve",
        "q0_emergency_reserve",
    )
    if (
        reserve.get("record_version") != "EmergencyDiskReserveRecord.v1"
        or reserve.get("allocated_bytes") != 1073741824
        or reserve.get("controller_only") is not True
        or reserve.get("fully_allocated") is not True
        or reserve.get("post_release_platform_state") != "suspended"
        or reserve.get("rebuild_requires_zero_active_attempts") is not True
    ):
        raise Q0BundleValidationError("q0_emergency_reserve", "emergency reserve mismatch")
    hard_quota = _object(
        policy.get("hard_write_quota_capability"),
        "hard quota capability",
        "q0_resource_limits",
    )
    if (
        hard_quota.get("capability_version") != "HardWriteQuotaCapability.v1"
        or hard_quota.get("required_for_p2") is not False
        or hard_quota.get("default_state") != "absent_accounting_kill_audit"
        or hard_quota.get("active_attempt_silent_downgrade") is not False
    ):
        raise Q0BundleValidationError("q0_resource_limits", "hard quota policy mismatch")
    disk = _object(
        policy.get("disk_pressure_policy"), "disk pressure policy", "q0_disk_pressure"
    )
    if (
        disk.get("state") != "disk_pressure"
        or disk.get("attempt_result") != "resource_exhausted_recovery_pending"
        or disk.get("forbidden_classification") != "needs_environment"
        or disk.get("running_floor_bytes") != 1073741824
    ):
        raise Q0BundleValidationError("q0_disk_pressure", "disk pressure policy mismatch")
    return {
        "resource_limit_count": len(limits),
        "process_input_limit_count": len(process_limits),
    }


def _validate_fixture(
    fixture: dict[str, Any], resource_policy: dict[str, Any]
) -> dict[str, Any]:
    if (
        fixture.get("fixture_id")
        != "QualificationGateCatalog.v1.contract-fixtures"
        or fixture.get("schema_version") != 1
        or fixture.get("baseline_id") != "local-ai-runtime-0.2-v3.25"
        or fixture.get("qualification_gate_catalog_path")
        != Q0_BUNDLE_PATHS["catalog"].as_posix()
        or fixture.get("feature_policy_path") != Q0_BUNDLE_PATHS["feature"].as_posix()
        or fixture.get("resource_limit_policy_path")
        != Q0_BUNDLE_PATHS["limits"].as_posix()
    ):
        raise Q0BundleValidationError("q0_fixture", "Q0 fixture identity mismatch")
    boundaries = _array(
        fixture.get("resource_boundary_cases"),
        "resource boundary cases",
        "q0_fixture_resource_boundaries",
    )
    limit_values = {
        item["limit_id"]: item["ceiling"] for item in resource_policy["limits"]
    }
    if len(boundaries) != len(EXPECTED_RESOURCE_LIMITS):
        raise Q0BundleValidationError(
            "q0_fixture_resource_boundaries", "resource boundary count mismatch"
        )
    by_id = {
        item.get("limit_id"): item
        for item in boundaries
        if isinstance(item, dict) and isinstance(item.get("limit_id"), str)
    }
    if set(by_id) != set(limit_values):
        raise Q0BundleValidationError(
            "q0_fixture_resource_boundaries", "resource boundary IDs mismatch"
        )
    for limit_id, ceiling in limit_values.items():
        case = by_id[limit_id]
        if case != {
            "limit_id": limit_id,
            "limit_minus_one": ceiling - 1,
            "limit": ceiling,
            "limit_plus_one": ceiling + 1,
            "expected": ["accepted", "accepted", "resource_limit_exceeded"],
        }:
            raise Q0BundleValidationError(
                "q0_fixture_resource_boundaries",
                f"resource boundary mismatch: {limit_id}",
            )
    process_boundaries = _array(
        fixture.get("process_input_boundary_cases"),
        "process input boundary cases",
        "q0_fixture_resource_boundaries",
    )
    process_values = {
        item["limit_id"]: item["ceiling"]
        for item in resource_policy["process_input_limits"]
    }
    process_by_id = {
        item.get("limit_id"): item
        for item in process_boundaries
        if isinstance(item, dict) and isinstance(item.get("limit_id"), str)
    }
    if set(process_by_id) != set(process_values):
        raise Q0BundleValidationError(
            "q0_fixture_resource_boundaries", "process input boundary IDs mismatch"
        )
    for limit_id, ceiling in process_values.items():
        if process_by_id[limit_id] != {
            "limit_id": limit_id,
            "limit_minus_one": ceiling - 1,
            "limit": ceiling,
            "limit_plus_one": ceiling + 1,
            "expected": ["accepted", "accepted", "resource_limit_exceeded"],
        }:
            raise Q0BundleValidationError(
                "q0_fixture_resource_boundaries",
                f"process input boundary mismatch: {limit_id}",
            )
    environment = _array(
        fixture.get("environment_cases"), "environment cases", "q0_fixture_environment"
    )
    if {item.get("case_id") for item in environment if isinstance(item, dict)} != EXPECTED_ENVIRONMENT_CASES:
        raise Q0BundleValidationError(
            "q0_fixture_environment", "environment fixture set mismatch"
        )
    eof_cases = _array(
        fixture.get("process_handle_eof_cases"),
        "process EOF cases",
        "q0_fixture_process_handles",
    )
    response_loss = next(
        (item for item in eof_cases if item.get("case_id") == "response_loss_with_open_writer"),
        {},
    )
    if len(eof_cases) != 4 or response_loss.get("expected") != "eof_not_proven":
        raise Q0BundleValidationError(
            "q0_fixture_process_handles", "EOF fixture set mismatch"
        )
    negatives = _array(
        fixture.get("negative_mutations"), "negative mutations", "q0_fixture_negative"
    )
    if {
        item.get("mutation") for item in negatives if isinstance(item, dict)
    } != set(EXPECTED_NEGATIVE_MUTATIONS):
        raise Q0BundleValidationError(
            "q0_fixture_negative", "negative mutation set mismatch"
        )
    for item in negatives:
        if item.get("expected_reason") != EXPECTED_NEGATIVE_MUTATIONS.get(
            item.get("mutation")
        ):
            raise Q0BundleValidationError(
                "q0_fixture_negative", "negative mutation reason mismatch"
            )
    return {
        "resource_boundary_case_count": len(boundaries) * 3,
        "process_input_boundary_case_count": len(process_boundaries) * 3,
        "environment_fixture_count": len(environment),
        "negative_fixture_count": len(negatives),
    }


def _mutation_registry() -> dict[
    str, tuple[str, Callable[[dict[str, Any]], None]]
]:
    return {
        "gate_shell_placeholder": (
            "catalog",
            lambda value: value["payload"]["gate_runs"][0]["argv"].append("<shell>"),
        ),
        "gate_missing_managed_config": (
            "catalog",
            lambda value: value["payload"]["gate_runs"][1]["argv"].remove(
                "--include-managed-config"
            ),
        ),
        "unknown_effective_capability_ignored": (
            "feature",
            lambda value: value.__setitem__("unknown_effective_capability", "ignore"),
        ),
        "environment_case_sensitive_uniqueness": (
            "catalog",
            lambda value: value["payload"]["process_environment_policy"][
                "key_contract"
            ].__setitem__("uniqueness", "case_sensitive"),
        ),
        "child_pre_resume_observation_claim": (
            "catalog",
            lambda value: value["payload"]["process_environment_policy"][
                "two_stage_proof"
            ]["pre_resume_parent_environment_proof"].__setitem__(
                "claim_scope", "child_observed_before_resume"
            ),
        ),
        "job_termination_implies_eof": (
            "catalog",
            lambda value: value["payload"]["process_handle_policy"][
                "eof_proof"
            ].__setitem__("job_termination_alone_implies_eof", True),
        ),
        "dpapi_proves_purpose_separation": (
            "catalog",
            lambda value: value["payload"]["external_evidence_and_dpapi"][
                "dpapi_envelopes"
            ].__setitem__("dpapi_alone_proves_application_invariants", True),
        ),
        "restore_multi_consumption": (
            "catalog",
            lambda value: value["payload"]["external_evidence_and_dpapi"][
                "restore_eligibility"
            ].__setitem__("single_consumption", False),
        ),
        "resource_boundary_removed": (
            "fixture",
            lambda value: value["process_input_boundary_cases"].pop(),
        ),
        "hard_quota_made_mandatory": (
            "limits",
            lambda value: value["hard_write_quota_capability"].__setitem__(
                "required_for_p2", True
            ),
        ),
        "accounting_fallback_too_slow": (
            "limits",
            lambda value: value["write_accounting_policy"].__setitem__(
                "fallback_rescan_max_interval_ms", 501
            ),
        ),
        "disk_pressure_maps_environment": (
            "limits",
            lambda value: value["disk_pressure_policy"].__setitem__(
                "forbidden_classification", "resource_exhausted"
            ),
        ),
    }


def _validate_bundle_values(values: dict[str, dict[str, Any]]) -> dict[str, Any]:
    catalog_counts = _validate_catalog(values["catalog"])
    feature_counts = _validate_feature_policy(values["feature"])
    limit_counts = _validate_resource_limits(values["limits"])
    fixture_counts = _validate_fixture(values["fixture"], values["limits"])
    return {**catalog_counts, **feature_counts, **limit_counts, **fixture_counts}


def _validate_negative_fixtures(values: dict[str, dict[str, Any]]) -> None:
    registry = _mutation_registry()
    fixture = values["fixture"]
    for case in fixture["negative_mutations"]:
        mutation = case["mutation"]
        target, mutate = registry[mutation]
        candidate = {key: copy.deepcopy(value) for key, value in values.items()}
        mutate(candidate[target])
        try:
            _validate_bundle_values(candidate)
        except Q0BundleValidationError as exc:
            if exc.reason != case["expected_reason"]:
                raise Q0BundleValidationError(
                    "q0_fixture_negative_reason",
                    f"{mutation}: expected {case['expected_reason']}, got {exc.reason}",
                ) from exc
        else:
            raise Q0BundleValidationError(
                "q0_fixture_negative_accepted", f"mutation accepted: {mutation}"
            )


def _verify_identities(raw_values: dict[str, bytes]) -> None:
    for key, raw in raw_values.items():
        identity = EXPECTED_Q0_BUNDLE_IDENTITIES[key]
        if (
            len(raw) != identity["byte_count"]
            or hashlib.sha256(raw).hexdigest() != identity["sha256"]
        ):
            raise Q0BundleValidationError(
                f"q0_{key}_identity", f"{key} bundle identity mismatch"
            )


def verify_q0_gate_limit_bundle(repo_root: Path) -> dict[str, Any]:
    """Verify the frozen Q0 catalog bundle and its offline contract fixtures."""

    root = repo_root.resolve()
    values: dict[str, dict[str, Any]] = {}
    raw_values: dict[str, bytes] = {}
    for key in Q0_BUNDLE_PATHS:
        values[key], raw_values[key] = _load(root, key)
    counts = _validate_bundle_values(values)
    _validate_negative_fixtures(values)
    _verify_identities(raw_values)
    catalog_raw = raw_values["catalog"]
    return {
        "status": "pass",
        "artifact_version": "QualificationGateCatalog.v1",
        "artifact_byte_count": len(catalog_raw),
        "artifact_sha256": hashlib.sha256(catalog_raw).hexdigest(),
        "feature_policy_sha256": hashlib.sha256(raw_values["feature"]).hexdigest(),
        "resource_limit_policy_sha256": hashlib.sha256(raw_values["limits"]).hexdigest(),
        "fixture_sha256": hashlib.sha256(raw_values["fixture"]).hexdigest(),
        **counts,
    }
