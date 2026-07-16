"""Stdlib-only verifier for the v3.24 state, guard and operator catalogs."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable


STATE_POLICY_PATHS = {
    "state_policy": Path(
        "docs/specs/local-ai-runtime-0.2/normative/StatePolicyCatalog.v1.json"
    ),
    "guard_catalog": Path(
        "docs/specs/local-ai-runtime-0.2/catalogs/GuardCatalog.v1.json"
    ),
    "operator_catalog": Path(
        "docs/specs/local-ai-runtime-0.2/catalogs/OperatorActionCatalog.v1.json"
    ),
    "fixture": Path(
        "docs/specs/local-ai-runtime-0.2/fixtures/state-policy/manifest.json"
    ),
}

EXPECTED_STATE_POLICY_IDENTITIES = {
    "state_policy": {
        "byte_count": 41279,
        "sha256": "423f90a0550630b0d413cc82a53f98b6602d05cd6b7a9072f2a65759e15189de",
    },
    "guard_catalog": {
        "byte_count": 10131,
        "sha256": "17b2022df58299ded4ca9897df2de236b8e73f3707d5e288e017635aafede31b",
    },
    "operator_catalog": {
        "byte_count": 9644,
        "sha256": "14f98ab03f4884736ea3b3a443ec3641aec7768cdce708d48f072bb49d860c87",
    },
    "fixture": {
        "byte_count": 5761,
        "sha256": "03afaef9f99f2b7152c335b058a32279c84fd815567ed0f7e929f13daf0c276b",
    },
}

EXPECTED_POLICY_IDS = [
    "SubmissionFamilyStatePolicy",
    "BatchTaskStatePolicy",
    "AttemptStatePolicy",
    "PlatformOperationalStatePolicy",
    "RepoCutoverMaintenancePolicy",
    "TemplateLifecyclePolicy",
    "AutonomyPolicy",
]

EXPECTED_ROW_FIELDS = {
    "row_id",
    "source_state",
    "operation_or_event",
    "guard_ids",
    "allowed_effects",
    "target_state",
    "exit_code",
    "capacity_disposition",
    "scheduler_priority",
    "retry_policy",
}

EXPECTED_PRECEDENCE = [
    "baseline_approval",
    "implementation_acceptance",
    "p2_q0",
    "platform_incompatible",
    "manual_drain_suspend",
    "needs_auth",
    "platform_unavailable_or_qualification_suspended",
    "disk_pressure",
    "repo_ownership_maintenance_requalification",
    "template_qualification_authorization",
    "task_base_environment_limits",
    "due_recovery",
    "writer_capacity",
]

EXPECTED_SCHEDULER_PRIORITY = [
    "live_process_safety",
    "publication_recovery",
    "deterministic_closeout",
    "cleanup",
    "due_retry",
    "new_promoted_task",
]

EXPECTED_ACTION_IDS = {
    "platform_login_required",
    "environment_requalification_required",
    "disk_pressure_remediation",
    "authorization_activation_required",
    "repo_requalification_required",
    "template_suspension_review",
    "recovery_required",
    "reconcile_required",
    "cleanup_required",
    "ownership_repair_required",
    "maintenance_recovery_required",
    "activation_rollback_required",
    "backup_restore_required",
    "cutover_or_rollback_required",
    "platform_suspend_review",
    "emergency_kill_current",
}

EXPECTED_NEGATIVE_MUTATIONS = {
    "remove_policy_table": "state_policy_table_set",
    "duplicate_transition_row": "state_policy_row_identity",
    "remove_row_field": "state_policy_row_schema",
    "add_unknown_guard": "state_policy_guard_reference",
    "set_unknown_target_state": "state_policy_target_state",
    "allow_unknown_combination_effect": "state_policy_unknown_combination",
    "make_journal_authority": "state_policy_authority_boundary",
    "remove_restart_from_rejected_inputs": "state_policy_recovery_determinism",
    "move_new_work_before_recovery": "state_policy_scheduler_priority",
    "remove_cleanup_bypass": "state_policy_cleanup_finalizer",
    "create_guard_cycle": "state_policy_guard_cycle",
    "swap_guard_precedence": "state_policy_guard_precedence",
    "remove_operator_action": "state_policy_operator_action_set",
    "make_toast_required": "state_policy_operator_presentation",
    "allow_push_to_close_action": "state_policy_operator_presentation",
    "activate_b3_row": "state_policy_b3_deferred",
    "add_b3_operator_action": "state_policy_b3_deferred",
    "allow_resume_to_clear_repo_block": "state_policy_scoped_resume",
}

SOURCE_ALIASES = {"any", "terminal", "preclaim", "any_nonterminal"}
CAPACITY_DISPOSITIONS = {
    "acquire",
    "not_acquired",
    "release",
    "release_after_handoff",
    "retain",
    "retain_until_handoff",
    "unchanged",
}
RETRY_POLICIES = {
    "due_backoff",
    "guard_change_only",
    "guarded_same_generation",
    "never",
    "operator_resolution",
    "same_finalizer",
    "same_identity_replay",
}


class StatePolicyValidationError(RuntimeError):
    """Raised with a stable reason code for a state-policy contract failure."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def _object(value: Any, label: str, reason: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise StatePolicyValidationError(reason, f"{label} must be an object")
    return value


def _array(value: Any, label: str, reason: str) -> list[Any]:
    if not isinstance(value, list):
        raise StatePolicyValidationError(reason, f"{label} must be an array")
    return value


def _exact(
    value: Any, fields: set[str], label: str, reason: str
) -> dict[str, Any]:
    result = _object(value, label, reason)
    if set(result) != fields:
        raise StatePolicyValidationError(reason, f"{label} fields mismatch")
    return result


def _string_array(value: Any, label: str, reason: str) -> list[str]:
    result = _array(value, label, reason)
    if not all(isinstance(item, str) and item for item in result):
        raise StatePolicyValidationError(reason, f"{label} must contain strings")
    if len(result) != len(set(result)):
        raise StatePolicyValidationError(reason, f"{label} contains duplicates")
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
    relative = STATE_POLICY_PATHS[key]
    path = root / relative
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StatePolicyValidationError(
            "state_policy_json", f"cannot read {relative.as_posix()}"
        ) from exc
    if not isinstance(value, dict) or _contains_null(value):
        raise StatePolicyValidationError(
            "state_policy_json", f"{relative.as_posix()} must be a null-free object"
        )
    identity = EXPECTED_STATE_POLICY_IDENTITIES[key]
    if (
        len(raw) != identity["byte_count"]
        or hashlib.sha256(raw).hexdigest() != identity["sha256"]
    ):
        raise StatePolicyValidationError(
            f"state_policy_{key}_identity",
            f"{relative.as_posix()} identity mismatch",
        )
    return value, raw


def _expanded_guard_catalog(
    catalog: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], int]:
    expected_fields = {
        "catalog_version",
        "baseline_id",
        "guard_contract",
        "precedence_order",
        "guard_groups",
        "dependency_edges",
        "safety_only_contract",
        "global_resume_contract",
        "b3_guard",
    }
    _exact(catalog, expected_fields, "GuardCatalog", "state_policy_guard_catalog")
    if (
        catalog["catalog_version"] != "GuardCatalog.v1"
        or catalog["baseline_id"] != "local-ai-runtime-0.2-v3.24"
    ):
        raise StatePolicyValidationError(
            "state_policy_guard_catalog", "guard catalog identity mismatch"
        )
    if catalog["precedence_order"] != EXPECTED_PRECEDENCE:
        raise StatePolicyValidationError(
            "state_policy_guard_precedence", "guard precedence mismatch"
        )
    contract = _object(
        catalog["guard_contract"], "guard contract", "state_policy_guard_catalog"
    )
    if (
        contract.get("dependency_graph") != "acyclic"
        or contract.get("evaluation")
        != "first_failed_guard_in_precedence_then_guard_id_order"
        or contract.get("reason_code_derivation")
        != "remove_guard_prefix_then_append__blocked"
    ):
        raise StatePolicyValidationError(
            "state_policy_guard_catalog", "guard contract mismatch"
        )

    guards: dict[str, dict[str, Any]] = {}
    precedence_index = {
        precedence: index for index, precedence in enumerate(EXPECTED_PRECEDENCE)
    }
    for raw_group in _array(
        catalog["guard_groups"], "guard groups", "state_policy_guard_catalog"
    ):
        group = _exact(
            raw_group,
            {
                "precedence",
                "scope",
                "immutable_input_snapshot",
                "safety_only",
                "guard_ids",
            },
            "guard group",
            "state_policy_guard_catalog",
        )
        precedence = group["precedence"]
        if precedence not in precedence_index:
            raise StatePolicyValidationError(
                "state_policy_guard_precedence", "unknown guard precedence"
            )
        if (
            not isinstance(group["scope"], str)
            or not group["scope"]
            or type(group["safety_only"]) is not bool
        ):
            raise StatePolicyValidationError(
                "state_policy_guard_catalog", "guard group metadata invalid"
            )
        snapshot = _string_array(
            group["immutable_input_snapshot"],
            "guard immutable input snapshot",
            "state_policy_guard_catalog",
        )
        for guard_id in _string_array(
            group["guard_ids"], "guard IDs", "state_policy_guard_catalog"
        ):
            if not guard_id.startswith("guard_") or guard_id in guards:
                raise StatePolicyValidationError(
                    "state_policy_guard_identity", f"duplicate guard {guard_id}"
                )
            guards[guard_id] = {
                "guard_id": guard_id,
                "scope": group["scope"],
                "immutable_input_snapshot": snapshot,
                "precedence": precedence,
                "reason_code": f"{guard_id.removeprefix('guard_')}_blocked",
                "depends_on_guard_ids": [],
                "safety_only": group["safety_only"],
            }

    b3 = _exact(
        catalog["b3_guard"],
        {
            "guard_id",
            "scope",
            "immutable_input_snapshot",
            "precedence",
            "reason_code",
            "depends_on_guard_ids",
            "safety_only",
            "result",
        },
        "B3 guard",
        "state_policy_b3_deferred",
    )
    if (
        b3["guard_id"] != "guard_b3_deferred"
        or b3["result"] != "deny_activation_exit_2"
        or b3["reason_code"] != "b3_deferred_blocked"
        or b3["precedence"] != "template_qualification_authorization"
    ):
        raise StatePolicyValidationError(
            "state_policy_b3_deferred", "B3 guard mismatch"
        )
    if b3["guard_id"] in guards:
        raise StatePolicyValidationError(
            "state_policy_guard_identity", "duplicate B3 guard"
        )
    guards[b3["guard_id"]] = copy.deepcopy(b3)

    edges_seen: set[tuple[str, str]] = set()
    for raw_edge in _array(
        catalog["dependency_edges"],
        "guard dependency edges",
        "state_policy_guard_catalog",
    ):
        edge = _exact(
            raw_edge,
            {"guard_id", "depends_on_guard_id"},
            "guard dependency edge",
            "state_policy_guard_catalog",
        )
        pair = (edge["guard_id"], edge["depends_on_guard_id"])
        if pair in edges_seen or pair[0] not in guards or pair[1] not in guards:
            raise StatePolicyValidationError(
                "state_policy_guard_reference", "invalid guard dependency"
            )
        edges_seen.add(pair)
        guards[pair[0]]["depends_on_guard_ids"].append(pair[1])
        if (
            precedence_index[guards[pair[1]]["precedence"]]
            > precedence_index[guards[pair[0]]["precedence"]]
        ):
            raise StatePolicyValidationError(
                "state_policy_guard_precedence",
                "guard depends on a lower-precedence guard",
            )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(guard_id: str) -> None:
        if guard_id in visiting:
            raise StatePolicyValidationError(
                "state_policy_guard_cycle", f"guard cycle at {guard_id}"
            )
        if guard_id in visited:
            return
        visiting.add(guard_id)
        for dependency in guards[guard_id]["depends_on_guard_ids"]:
            visit(dependency)
        visiting.remove(guard_id)
        visited.add(guard_id)

    for guard_id in guards:
        visit(guard_id)

    resume = _object(
        catalog["global_resume_contract"],
        "global resume contract",
        "state_policy_scoped_resume",
    )
    if (
        resume.get("may_change_only")
        != ["PlatformOperationalStatePolicy.control"]
        or set(resume.get("must_not_clear", []))
        != {
            "RepoCutoverMaintenancePolicy.qualification",
            "TemplateLifecyclePolicy.suspended",
            "repo_ownership_block",
            "template_authorization_block",
        }
    ):
        raise StatePolicyValidationError(
            "state_policy_scoped_resume", "global resume scope mismatch"
        )

    safety = _object(
        catalog["safety_only_contract"],
        "safety-only contract",
        "state_policy_guard_catalog",
    )
    if not {
        "create_writer",
        "publish_git_ref",
        "publish_evidence",
        "delete_unknown_path",
        "expand_repo_or_task_state",
    }.issubset(set(safety.get("forbidden_effects", []))):
        raise StatePolicyValidationError(
            "state_policy_guard_catalog", "safety-only effect closure mismatch"
        )
    return guards, len(edges_seen)


def _policy_states(policy: dict[str, Any]) -> tuple[set[str], set[str]]:
    if policy["state_model"] == "orthogonal_lanes":
        lanes = _object(
            policy.get("lanes"),
            f"{policy['policy_id']} lanes",
            "state_policy_target_state",
        )
        states: set[str] = set()
        for lane, values in lanes.items():
            if not isinstance(lane, str):
                raise StatePolicyValidationError(
                    "state_policy_target_state", "lane name invalid"
                )
            for value in _string_array(
                values, f"{lane} values", "state_policy_target_state"
            ):
                states.add(f"{lane}={value}")
        return states, set()
    states = set(
        _string_array(
            policy.get("states"),
            f"{policy['policy_id']} states",
            "state_policy_target_state",
        )
    )
    terminal = set(
        _string_array(
            policy.get("terminal_states"),
            f"{policy['policy_id']} terminal states",
            "state_policy_target_state",
        )
    )
    if not terminal.issubset(states):
        raise StatePolicyValidationError(
            "state_policy_target_state", "terminal state is undeclared"
        )
    return states, terminal


def _verify_terminal_reachability(
    policy: dict[str, Any],
    states: set[str],
    terminal: set[str],
    rows: list[dict[str, Any]],
) -> None:
    if not terminal:
        return
    graph: dict[str, set[str]] = {state: set() for state in states}
    nonterminal = states - terminal
    for row in rows:
        source = row["source_state"]
        target = row["target_state"]
        if target == "unchanged":
            continue
        if source == "any_nonterminal":
            sources = nonterminal
        elif source == "terminal":
            sources = terminal
        elif source == "any":
            sources = states
        elif source == "preclaim":
            sources = {"submitted", "queued", "parked"} & states
        else:
            sources = {source} if source in states else set()
        if target in states:
            for item in sources:
                graph[item].add(target)

    reachable = set(terminal)
    changed = True
    while changed:
        changed = False
        for state, targets in graph.items():
            if state not in reachable and targets & reachable:
                reachable.add(state)
                changed = True
    missing = nonterminal - reachable
    if missing:
        raise StatePolicyValidationError(
            "state_policy_terminal_reachability",
            f"{policy['policy_id']} cannot reach terminal from {sorted(missing)}",
        )


def _validate_state_policy(
    document: dict[str, Any], guard_ids: set[str]
) -> tuple[dict[str, Any], int]:
    envelope = _exact(
        document,
        {"domain", "schema_version", "payload"},
        "StatePolicyCatalog envelope",
        "state_policy_catalog",
    )
    if (
        envelope["domain"] != "local-ai-runtime/StatePolicyCatalog/v1"
        or envelope["schema_version"] != 1
    ):
        raise StatePolicyValidationError(
            "state_policy_catalog", "state policy envelope mismatch"
        )
    payload = _exact(
        envelope["payload"],
        {
            "artifact_id",
            "artifact_version",
            "baseline_id",
            "contract_status",
            "authority_model",
            "row_schema_fields",
            "unknown_combination",
            "adapter_violation",
            "scheduler_contract",
            "cleanup_finalizer_contract",
            "policies",
            "b3_disposition",
        },
        "StatePolicyCatalog payload",
        "state_policy_catalog",
    )
    if (
        payload["artifact_id"] != "P0A-STATE"
        or payload["artifact_version"] != "StatePolicyCatalog.v1"
        or payload["baseline_id"] != "local-ai-runtime-0.2-v3.24"
        or payload["contract_status"] != "normative_preimplementation_contract"
    ):
        raise StatePolicyValidationError(
            "state_policy_catalog", "state policy identity mismatch"
        )
    expected_row_order = [
        "row_id",
        "source_state",
        "operation_or_event",
        "guard_ids",
        "allowed_effects",
        "target_state",
        "exit_code",
        "capacity_disposition",
        "scheduler_priority",
        "retry_policy",
    ]
    if payload["row_schema_fields"] != expected_row_order:
        raise StatePolicyValidationError(
            "state_policy_row_schema", "row schema fields mismatch"
        )

    authority = _object(
        payload["authority_model"],
        "authority model",
        "state_policy_authority_boundary",
    )
    if (
        authority.get("policy_and_transition_authority") != "sqlite_only"
        or authority.get("write_transaction_mode") != "BEGIN IMMEDIATE"
        or authority.get("journal_role")
        != "append_only_observation_and_recovery_input"
        or authority.get("journal_may_create_policy_state") is not False
    ):
        raise StatePolicyValidationError(
            "state_policy_authority_boundary", "SQLite/journal boundary mismatch"
        )
    rejected_inputs = set(authority.get("rejected_replay_inputs", []))
    if not {
        "observation_time",
        "controller_restart_count",
        "scan_count",
        "unaccepted_journal_event",
        "wrong_generation_event",
    }.issubset(rejected_inputs):
        raise StatePolicyValidationError(
            "state_policy_recovery_determinism",
            "nondeterministic replay input is not rejected",
        )
    if authority.get("deterministic_recovery_outcomes") != [
        "same_deterministic_result",
        "terminal_failure",
        "durable_park_with_operator_action",
    ]:
        raise StatePolicyValidationError(
            "state_policy_recovery_determinism",
            "recovery outcome closure mismatch",
        )

    unknown = _object(
        payload["unknown_combination"],
        "unknown combination",
        "state_policy_unknown_combination",
    )
    if (
        unknown.get("exit_code") != 2
        or unknown.get("allowed_effects") != []
        or unknown.get("capacity_disposition") != "unchanged"
    ):
        raise StatePolicyValidationError(
            "state_policy_unknown_combination",
            "unknown combination must exit 2 without effects",
        )
    adapter = _object(
        payload["adapter_violation"],
        "adapter violation",
        "state_policy_adapter_violation",
    )
    if (
        adapter.get("exit_code") != 6
        or "terminate_exact_job" not in adapter.get("required_effects", [])
        or "suspend_platform_incompatible"
        not in adapter.get("required_effects", [])
    ):
        raise StatePolicyValidationError(
            "state_policy_adapter_violation", "adapter violation mismatch"
        )

    scheduler = _object(
        payload["scheduler_contract"],
        "scheduler contract",
        "state_policy_scheduler_priority",
    )
    if (
        scheduler.get("global_writer_capacity") != 1
        or scheduler.get("priority_order") != EXPECTED_SCHEDULER_PRIORITY
        or scheduler.get("recovery_outranks_new_work") is not True
        or scheduler.get("one_controller_invocation_max_claims") != 1
        or scheduler.get("stable_tie_break")
        != ["ready_at_utc", "root_task_id", "generation", "attempt_no"]
    ):
        raise StatePolicyValidationError(
            "state_policy_scheduler_priority", "scheduler contract mismatch"
        )

    cleanup = _object(
        payload["cleanup_finalizer_contract"],
        "cleanup finalizer contract",
        "state_policy_cleanup_finalizer",
    )
    if (
        cleanup.get("lane") != "explicit_finalizer"
        or set(cleanup.get("required_guards", []))
        != {
            "guard_cleanup_owned_paths",
            "guard_cleanup_job_zero_process",
            "guard_cleanup_fence_current",
            "guard_cleanup_actions_terminal",
            "guard_cleanup_evidence_terminal",
            "guard_cleanup_head_index_clean",
        }
        or set(cleanup.get("forbidden_bypass", []))
        != {
            "delete_guard_row",
            "delete_marker",
            "delete_journal_segment",
            "clear_db_row",
            "direct_terminal_state_edit",
            "skip_read_back",
        }
        or cleanup.get("repair_disposition")
        != "satisfy_replace_or_terminally_close_finalizer_condition"
    ):
        raise StatePolicyValidationError(
            "state_policy_cleanup_finalizer", "cleanup finalizer mismatch"
        )

    policies = _array(
        payload["policies"], "state policies", "state_policy_table_set"
    )
    if [policy.get("policy_id") for policy in policies if isinstance(policy, dict)] != EXPECTED_POLICY_IDS:
        raise StatePolicyValidationError(
            "state_policy_table_set", "state policy table set/order mismatch"
        )
    row_ids: set[str] = set()
    transition_keys: set[tuple[str, str, str]] = set()
    row_count = 0
    for policy in policies:
        policy_id = policy["policy_id"]
        states, terminal = _policy_states(policy)
        legal_operations = set(
            _string_array(
                policy.get("legal_operations"),
                f"{policy_id} legal operations",
                "state_policy_operation_set",
            )
        )
        rows = _array(
            policy.get("rows"), f"{policy_id} rows", "state_policy_row_schema"
        )
        actual_operations: set[str] = set()
        checked_rows: list[dict[str, Any]] = []
        for raw_row in rows:
            row = _exact(
                raw_row,
                EXPECTED_ROW_FIELDS,
                f"{policy_id} row",
                "state_policy_row_schema",
            )
            if not isinstance(row["row_id"], str) or row["row_id"] in row_ids:
                raise StatePolicyValidationError(
                    "state_policy_row_identity", "duplicate or invalid row ID"
                )
            row_ids.add(row["row_id"])
            key = (
                policy_id,
                str(row["source_state"]),
                str(row["operation_or_event"]),
            )
            if key in transition_keys:
                raise StatePolicyValidationError(
                    "state_policy_row_identity", "duplicate transition key"
                )
            transition_keys.add(key)
            actual_operations.add(row["operation_or_event"])
            guards = _string_array(
                row["guard_ids"],
                f"{row['row_id']} guards",
                "state_policy_guard_reference",
            )
            if not set(guards).issubset(guard_ids):
                raise StatePolicyValidationError(
                    "state_policy_guard_reference", "row references unknown guard"
                )
            _string_array(
                row["allowed_effects"],
                f"{row['row_id']} effects",
                "state_policy_row_schema",
            )
            source = row["source_state"]
            target = row["target_state"]
            lane_wildcard = (
                isinstance(source, str)
                and source.endswith("=any")
                and any(
                    state.startswith(source.removesuffix("any"))
                    for state in states
                )
            )
            if (
                not isinstance(source, str)
                or (
                    source not in states
                    and source not in SOURCE_ALIASES
                    and not lane_wildcard
                )
                or not isinstance(target, str)
                or (target not in states and target != "unchanged")
            ):
                raise StatePolicyValidationError(
                    "state_policy_target_state",
                    f"{row['row_id']} source or target is undeclared",
                )
            if row["exit_code"] not in {0, 2, 3, 4, 5, 6}:
                raise StatePolicyValidationError(
                    "state_policy_row_schema", "row exit code invalid"
                )
            if (
                row["capacity_disposition"] not in CAPACITY_DISPOSITIONS
                or row["scheduler_priority"]
                not in {*EXPECTED_SCHEDULER_PRIORITY, "none"}
                or row["retry_policy"] not in RETRY_POLICIES
            ):
                raise StatePolicyValidationError(
                    "state_policy_row_schema", "row disposition invalid"
                )
            checked_rows.append(row)
            row_count += 1
        if actual_operations != legal_operations:
            raise StatePolicyValidationError(
                "state_policy_operation_set",
                f"{policy_id} operation coverage mismatch",
            )
        _verify_terminal_reachability(policy, states, terminal, checked_rows)

    b3 = _object(
        payload["b3_disposition"],
        "B3 disposition",
        "state_policy_b3_deferred",
    )
    if (
        b3.get("status") != "deferred_data_only"
        or b3.get("runtime_0_2_activation_row_exists") is not False
        or b3.get("operator_activation_action_exists") is not False
        or b3.get("allowed_0_2_effects") != ["record_nonactivating_observation"]
    ):
        raise StatePolicyValidationError(
            "state_policy_b3_deferred", "B3 disposition mismatch"
        )
    autonomy = next(
        policy for policy in policies if policy["policy_id"] == "AutonomyPolicy"
    )
    activation_row = next(
        row
        for row in autonomy["rows"]
        if row["operation_or_event"] == "request_b3_activation"
    )
    if (
        activation_row["exit_code"] != 2
        or activation_row["allowed_effects"] != []
        or any(
            "activate_b3" in effect
            for row in autonomy["rows"]
            for effect in row["allowed_effects"]
        )
    ):
        raise StatePolicyValidationError(
            "state_policy_b3_deferred", "B3 activation became executable"
        )
    return payload, row_count


def _validate_operator_catalog(
    catalog: dict[str, Any], guard_ids: set[str]
) -> int:
    _exact(
        catalog,
        {
            "catalog_version",
            "baseline_id",
            "row_schema_fields",
            "storage_contract",
            "presentation_contract",
            "operator_work_session_contract",
            "actions",
            "b3_disposition",
        },
        "OperatorActionCatalog",
        "state_policy_operator_catalog",
    )
    if (
        catalog["catalog_version"] != "OperatorActionCatalog.v1"
        or catalog["baseline_id"] != "local-ai-runtime-0.2-v3.24"
    ):
        raise StatePolicyValidationError(
            "state_policy_operator_catalog", "operator catalog identity mismatch"
        )
    expected_fields = {
        "action_id",
        "reason_code",
        "scope",
        "precondition_guard_ids",
        "allowed_command",
        "dedup_key_fields",
        "notification_policy_id",
        "capacity_disposition",
        "terminal_conditions",
    }
    if set(catalog["row_schema_fields"]) != expected_fields:
        raise StatePolicyValidationError(
            "state_policy_operator_row", "operator row schema mismatch"
        )
    actions = _array(
        catalog["actions"], "operator actions", "state_policy_operator_action_set"
    )
    declared_action_ids = {
        action.get("action_id") for action in actions if isinstance(action, dict)
    }
    if any(
        isinstance(action_id, str) and "b3" in action_id
        for action_id in declared_action_ids
    ):
        raise StatePolicyValidationError(
            "state_policy_b3_deferred", "B3 operator action exists"
        )
    if declared_action_ids != EXPECTED_ACTION_IDS:
        raise StatePolicyValidationError(
            "state_policy_operator_action_set", "operator action set mismatch"
        )
    seen: set[str] = set()
    for raw_action in actions:
        action = _exact(
            raw_action,
            expected_fields,
            "operator action",
            "state_policy_operator_row",
        )
        action_id = action["action_id"]
        if action_id in seen or not isinstance(action_id, str):
            raise StatePolicyValidationError(
                "state_policy_operator_action_set", "duplicate action"
            )
        seen.add(action_id)
        guards = set(
            _string_array(
                action["precondition_guard_ids"],
                f"{action_id} precondition guards",
                "state_policy_operator_row",
            )
        )
        if not guards.issubset(guard_ids):
            raise StatePolicyValidationError(
                "state_policy_guard_reference",
                f"{action_id} references unknown guard",
            )
        dedup = _string_array(
            action["dedup_key_fields"],
            f"{action_id} dedup key",
            "state_policy_operator_row",
        )
        if not dedup or dedup[0] != "action_id":
            raise StatePolicyValidationError(
                "state_policy_operator_row", "dedup key must start with action_id"
            )
        if (
            not isinstance(action["allowed_command"], str)
            or not action["allowed_command"]
            or action["notification_policy_id"]
            != "durable_inbox_optional_qualified_toast_v1"
            or action["capacity_disposition"] not in CAPACITY_DISPOSITIONS
        ):
            raise StatePolicyValidationError(
                "state_policy_operator_row", "operator action metadata invalid"
            )
        _string_array(
            action["terminal_conditions"],
            f"{action_id} terminal conditions",
            "state_policy_operator_row",
        )

    presentation = _object(
        catalog["presentation_contract"],
        "operator presentation",
        "state_policy_operator_presentation",
    )
    if (
        presentation.get("required_inbox") != "durable_local_status_v1"
        or presentation.get("optional_push_transport")
        != "qualified_windows_toast_v1"
        or presentation.get("push_failure_effect")
        != "record_transport_outcome_only"
        or set(presentation.get("push_must_not", []))
        != {"close_action", "drop_inbox_action", "expand_action_scope"}
    ):
        raise StatePolicyValidationError(
            "state_policy_operator_presentation",
            "durable inbox or optional push boundary mismatch",
        )
    storage = _object(
        catalog["storage_contract"],
        "operator storage",
        "state_policy_operator_catalog",
    )
    if (
        storage.get("action_row") != "immutable"
        or storage.get("resolution_log") != "append_only"
        or storage.get("active_head") != "mutable_generation_cas"
        or storage.get("free_text_in_database") is not False
    ):
        raise StatePolicyValidationError(
            "state_policy_operator_catalog", "operator storage mismatch"
        )
    b3 = _object(
        catalog["b3_disposition"],
        "operator B3 disposition",
        "state_policy_b3_deferred",
    )
    if (
        b3.get("status") != "deferred_no_runtime_0_2_action"
        or any("b3" in action_id for action_id in seen)
    ):
        raise StatePolicyValidationError(
            "state_policy_b3_deferred", "B3 operator action exists"
        )
    return len(actions)


def _mutation_registry() -> dict[
    str, tuple[str, Callable[[dict[str, Any]], None]]
]:
    return {
        "remove_policy_table": (
            "state_policy",
            lambda value: value["payload"]["policies"].pop(),
        ),
        "duplicate_transition_row": (
            "state_policy",
            lambda value: value["payload"]["policies"][0]["rows"].append(
                copy.deepcopy(value["payload"]["policies"][0]["rows"][0])
            ),
        ),
        "remove_row_field": (
            "state_policy",
            lambda value: value["payload"]["policies"][0]["rows"][0].pop(
                "retry_policy"
            ),
        ),
        "add_unknown_guard": (
            "state_policy",
            lambda value: value["payload"]["policies"][0]["rows"][0][
                "guard_ids"
            ].append("guard_unknown"),
        ),
        "set_unknown_target_state": (
            "state_policy",
            lambda value: value["payload"]["policies"][0]["rows"][0].__setitem__(
                "target_state", "unknown_state"
            ),
        ),
        "allow_unknown_combination_effect": (
            "state_policy",
            lambda value: value["payload"]["unknown_combination"][
                "allowed_effects"
            ].append("create_task"),
        ),
        "make_journal_authority": (
            "state_policy",
            lambda value: value["payload"]["authority_model"].__setitem__(
                "journal_may_create_policy_state", True
            ),
        ),
        "remove_restart_from_rejected_inputs": (
            "state_policy",
            lambda value: value["payload"]["authority_model"][
                "rejected_replay_inputs"
            ].remove("controller_restart_count"),
        ),
        "move_new_work_before_recovery": (
            "state_policy",
            lambda value: value["payload"]["scheduler_contract"].__setitem__(
                "priority_order",
                [
                    "live_process_safety",
                    "new_promoted_task",
                    "publication_recovery",
                    "deterministic_closeout",
                    "cleanup",
                    "due_retry",
                ],
            ),
        ),
        "remove_cleanup_bypass": (
            "state_policy",
            lambda value: value["payload"]["cleanup_finalizer_contract"][
                "forbidden_bypass"
            ].pop(),
        ),
        "create_guard_cycle": (
            "guard_catalog",
            lambda value: value["dependency_edges"].extend(
                [
                    {
                        "guard_id": "guard_cleanup_required",
                        "depends_on_guard_id": "guard_cleanup_terminal",
                    },
                    {
                        "guard_id": "guard_cleanup_terminal",
                        "depends_on_guard_id": "guard_cleanup_required",
                    },
                ]
            ),
        ),
        "swap_guard_precedence": (
            "guard_catalog",
            lambda value: value["precedence_order"].__setitem__(
                slice(0, 2), list(reversed(value["precedence_order"][:2]))
            ),
        ),
        "remove_operator_action": (
            "operator_catalog",
            lambda value: value["actions"].pop(),
        ),
        "make_toast_required": (
            "operator_catalog",
            lambda value: value["presentation_contract"].__setitem__(
                "optional_push_transport", "required_windows_toast"
            ),
        ),
        "allow_push_to_close_action": (
            "operator_catalog",
            lambda value: value["presentation_contract"]["push_must_not"].remove(
                "close_action"
            ),
        ),
        "activate_b3_row": (
            "state_policy",
            lambda value: value["payload"]["b3_disposition"].__setitem__(
                "runtime_0_2_activation_row_exists", True
            ),
        ),
        "add_b3_operator_action": (
            "operator_catalog",
            lambda value: value["actions"].append(
                {
                    **copy.deepcopy(value["actions"][0]),
                    "action_id": "activate_b3_portfolio_generation",
                }
            ),
        ),
        "allow_resume_to_clear_repo_block": (
            "guard_catalog",
            lambda value: value["global_resume_contract"][
                "may_change_only"
            ].append("RepoCutoverMaintenancePolicy.qualification"),
        ),
    }


def _validate_fixture(
    fixture: dict[str, Any],
    state_policy: dict[str, Any],
    guard_catalog: dict[str, Any],
    operator_catalog: dict[str, Any],
    guards: dict[str, dict[str, Any]],
    row_count: int,
    edge_count: int,
    action_count: int,
) -> tuple[int, int]:
    _exact(
        fixture,
        {
            "fixture_id",
            "schema_version",
            "baseline_id",
            "state_policy_path",
            "guard_catalog_path",
            "operator_action_catalog_path",
            "expected_counts",
            "positive_cases",
            "negative_mutations",
        },
        "state-policy fixture",
        "state_policy_fixture",
    )
    if (
        fixture["fixture_id"] != "StatePolicyCatalog.v1.contract-fixtures"
        or fixture["schema_version"] != 1
        or fixture["baseline_id"] != "local-ai-runtime-0.2-v3.24"
        or fixture["state_policy_path"]
        != STATE_POLICY_PATHS["state_policy"].as_posix()
        or fixture["guard_catalog_path"]
        != STATE_POLICY_PATHS["guard_catalog"].as_posix()
        or fixture["operator_action_catalog_path"]
        != STATE_POLICY_PATHS["operator_catalog"].as_posix()
    ):
        raise StatePolicyValidationError(
            "state_policy_fixture", "fixture identity mismatch"
        )
    counts = fixture["expected_counts"]
    if counts != {
        "policy_tables": 7,
        "transition_rows": row_count,
        "guards": len(guards),
        "guard_precedence_levels": len(EXPECTED_PRECEDENCE),
        "operator_actions": action_count,
    }:
        raise StatePolicyValidationError(
            "state_policy_fixture", "fixture counts mismatch"
        )
    positive_cases = {
        case.get("case_id"): case
        for case in _array(
            fixture["positive_cases"],
            "positive cases",
            "state_policy_fixture",
        )
        if isinstance(case, dict)
    }
    if set(positive_cases) != {
        "deterministic_recovery_restart_invariant",
        "journal_ahead_without_acceptance_parks",
        "cleanup_finalizer_requires_all_proofs",
        "global_resume_preserves_scoped_blocks",
        "b3_activation_denied",
    }:
        raise StatePolicyValidationError(
            "state_policy_fixture", "positive case set mismatch"
        )
    deterministic = positive_cases["deterministic_recovery_restart_invariant"]
    excluded = {"observation_time", "controller_restart_count"}
    if (
        {
            key: value
            for key, value in deterministic["history_a"].items()
            if key not in excluded
        }
        != {
            key: value
            for key, value in deterministic["history_b"].items()
            if key not in excluded
        }
        or deterministic["expected_decision"] != "same_deterministic_result"
    ):
        raise StatePolicyValidationError(
            "state_policy_recovery_determinism",
            "deterministic recovery fixture mismatch",
        )
    ahead = positive_cases["journal_ahead_without_acceptance_parks"]
    if (
        ahead["journal_last_seq"] <= ahead["accepted_cursor"]
        or ahead["journal_fence"] == ahead["current_fence"]
        or ahead["expected_decision"] != "durable_park_with_operator_action"
    ):
        raise StatePolicyValidationError(
            "state_policy_authority_boundary", "journal-ahead fixture mismatch"
        )

    registry = _mutation_registry()
    negatives = _array(
        fixture["negative_mutations"],
        "negative mutations",
        "state_policy_fixture",
    )
    if {
        case.get("mutation")
        for case in negatives
        if isinstance(case, dict)
    } != set(registry):
        raise StatePolicyValidationError(
            "state_policy_fixture", "negative mutation set mismatch"
        )
    originals = {
        "state_policy": state_policy,
        "guard_catalog": guard_catalog,
        "operator_catalog": operator_catalog,
    }
    for raw_case in negatives:
        case = _exact(
            raw_case,
            {"case_id", "target", "mutation", "expected_reason"},
            "negative mutation",
            "state_policy_fixture",
        )
        if case["expected_reason"] != EXPECTED_NEGATIVE_MUTATIONS.get(
            case["mutation"]
        ):
            raise StatePolicyValidationError(
                "state_policy_fixture", "negative reason mismatch"
            )
        expected_target, mutate = registry[case["mutation"]]
        if case["target"] != expected_target:
            raise StatePolicyValidationError(
                "state_policy_fixture", "negative target mismatch"
            )
        candidate = copy.deepcopy(originals[expected_target])
        mutate(candidate)
        try:
            if expected_target == "state_policy":
                _validate_state_policy(candidate, set(guards))
            elif expected_target == "guard_catalog":
                _expanded_guard_catalog(candidate)
            else:
                _validate_operator_catalog(candidate, set(guards))
        except StatePolicyValidationError as exc:
            if exc.reason != case["expected_reason"]:
                raise StatePolicyValidationError(
                    "state_policy_fixture_reason",
                    f"{case['case_id']}: expected {case['expected_reason']}, got {exc.reason}",
                ) from exc
        else:
            raise StatePolicyValidationError(
                "state_policy_negative_accepted", str(case["case_id"])
            )
    return len(positive_cases), len(negatives)


def verify_state_policy_bundle(repo_root: Path) -> dict[str, Any]:
    """Verify the immutable state/guard/operator bundle and offline fixtures."""

    root = repo_root.resolve()
    state_policy, state_raw = _load(root, "state_policy")
    guard_catalog, _ = _load(root, "guard_catalog")
    operator_catalog, _ = _load(root, "operator_catalog")
    fixture, _ = _load(root, "fixture")
    guards, edge_count = _expanded_guard_catalog(guard_catalog)
    payload, row_count = _validate_state_policy(state_policy, set(guards))
    action_count = _validate_operator_catalog(operator_catalog, set(guards))
    positive_count, negative_count = _validate_fixture(
        fixture,
        state_policy,
        guard_catalog,
        operator_catalog,
        guards,
        row_count,
        edge_count,
        action_count,
    )
    return {
        "artifact_version": payload["artifact_version"],
        "artifact_byte_count": len(state_raw),
        "artifact_sha256": hashlib.sha256(state_raw).hexdigest(),
        "policy_table_count": len(payload["policies"]),
        "transition_row_count": row_count,
        "guard_count": len(guards),
        "guard_dependency_edge_count": edge_count,
        "guard_precedence_level_count": len(EXPECTED_PRECEDENCE),
        "operator_action_count": action_count,
        "positive_fixture_count": positive_count,
        "negative_fixture_count": negative_count,
        "scheduler_priority_order": copy.deepcopy(EXPECTED_SCHEDULER_PRIORITY),
        "bundle_identities": copy.deepcopy(EXPECTED_STATE_POLICY_IDENTITIES),
    }
