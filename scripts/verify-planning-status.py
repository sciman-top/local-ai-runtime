from __future__ import annotations

import argparse
import hashlib
import json
import stat
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATUS_PATH = ROOT / "docs" / "architecture" / "planning-status.json"
POLICY_PATH = Path("docs/architecture/next-work-selection-policy.json")
CURRENT_BASELINE_ID = "local-ai-runtime-0.2-v3.23"
CURRENT_BASELINE_PATH = "docs/specs/local-ai-runtime-0.2-v3.23-baseline-candidate.md"
CURRENT_BASELINE_ENTRY_PATH = "docs/specs/local-ai-runtime-0.2-baseline-candidate.md"
CURRENT_LINEAGE_PATH = (
    "docs/specs/local-ai-runtime-0.2/normative/BaselineLineage.v2.json"
)
HISTORICAL_SOURCE_RECORD_PATH = (
    "docs/specs/local-ai-runtime-0.2/history/HistoricalSourceArchive.v1.json"
)
BASELINE_ENTRY_ROLE = "non_normative_navigation"
BASELINE_ENTRY_MAXIMUM_BYTE_COUNT = 4096
EXPECTED_SELECTOR_ENTRYPOINTS = [
    "docs/architecture/planning-status.json",
    CURRENT_BASELINE_ENTRY_PATH,
    CURRENT_BASELINE_PATH,
    "docs/specs/local-ai-runtime-0.2-normative-package.json",
    "docs/plans/local-ai-runtime-0.2-work-items.json",
    "scripts/verify-planning-status.py",
    "scripts/select-next-work.py",
    "scripts/governance/preflight.ps1",
]
EXPECTED_SELECTOR_STEPS = [
    ("planning_integrity_red", "repair_gate_first"),
    (
        "native_thin_path_semantic_change_requires_successor",
        "create_successor_candidate_first",
    ),
    ("native_thin_path_evaluation_pending", "run_native_thin_path_evaluation_first"),
    ("baseline_review_closure_pending", "run_baseline_consistency_review"),
    ("normative_package_incomplete", "close_baseline_normative_package_first"),
    ("approval_eligible_without_active_approval", "record_baseline_approval_first"),
    ("approved_truth_reset_missing", "implement_truth_reset_first"),
    ("truth_reset_done_legacy_guard_missing", "implement_legacy_guard_first"),
    ("legacy_guard_done_implementation_incomplete", "implement_local_ai_runtime_first"),
    ("implementation_complete_acceptance_missing", "run_implementation_acceptance_first"),
    ("implementation_accepted_full_q0_missing", "run_full_q0_first"),
    ("full_q0_green_p2_pilot_missing", "run_single_p2_pilot_first"),
    ("p2_pilot_green_p3_missing", "run_five_scheduled_self_host_first"),
    ("p3_green_p4_missing", "run_30_task_cohort_first"),
    ("p4_green_b3_work_item_selected", "activate_b3_portfolio_generation_first"),
    ("p4_green_p5_missing", "cut_over_repositories_first"),
    ("p5_complete", "operate_approved_runtime"),
]
EXPECTED_SELECTOR_ACTIONS = [action for _, action in EXPECTED_SELECTOR_STEPS]
CURRENT_WORK_ITEM_COUNT = 65
EXPECTED_ARTIFACT_IDS = [
    "P0A-SOURCE",
    "P0A-LINEAGE",
    "P0A-CANONICAL",
    "P0A-PRODUCT",
    "P0A-QUALIFICATION",
    "P0A-EXECUTION",
    "P0A-EVIDENCE",
    "P0A-GIT",
    "P0A-STATE",
    "P0A-Q0",
    "P0A-MIGRATION",
    "P0A-EXAMPLES",
    "P0A-VERIFIER",
    "P0A-MANIFEST",
    "P0A-REVIEW",
]
EXPECTED_P1_IMPLEMENTATION_TASK_IDS = {
    *(f"LAR-P1A-{index:03d}" for index in range(1, 5)),
    *(f"LAR-P1B-{index:03d}" for index in range(1, 6)),
    *(f"LAR-P1C-{index:03d}" for index in range(1, 8)),
    *(f"LAR-P1D-{index:03d}" for index in range(1, 7)),
    *(f"LAR-P1E-{index:03d}" for index in range(1, 8)),
    *(f"LAR-P1F-{index:03d}" for index in range(1, 7)),
}
EXPECTED_REVIEW_MISSING_ARTIFACT_SETS = [
    ["P0A-MANIFEST", "P0A-REVIEW"],
    ["P0A-REVIEW"],
]
RUNTIME_SOURCE_PREFIX = "runtime/local-ai-runtime/src/local_ai_runtime/"
APPROVED_RUNTIME_SOURCE_ROOT_FILES = ("__init__.py", "__main__.py")
APPROVED_RUNTIME_SOURCE_PACKAGES = (
    "contracts",
    "kernel",
    "qualification",
    "storage",
    "execution",
    "recovery",
    "git_local",
    "operations",
    "compat",
)
EXPECTED_RUNTIME_SOURCE_OWNERS = {
    "__init__.py": "LAR-P0D-001",
    "__main__.py": "LAR-P0D-001",
    "contracts/__init__.py": "LAR-P1A-001",
    "kernel/__init__.py": "LAR-P1A-003",
    "storage/__init__.py": "LAR-P1B-001",
    "operations/__init__.py": "LAR-P1C-001",
    "qualification/__init__.py": "LAR-P1C-002",
    "execution/__init__.py": "LAR-P1D-001",
    "recovery/__init__.py": "LAR-P1D-005",
    "git_local/__init__.py": "LAR-P1E-001",
    "compat/__init__.py": "LAR-P1F-006",
}
IGNORED_RUNTIME_SOURCE_TREE_ENTRIES = frozenset({"__pycache__"})
WORK_ITEM_SCHEMA_VERSION = "local_ai_runtime_work_items.v3"
EXPECTED_WORK_ITEM_STATUSES = [
    "completed",
    "contract_pending",
    "execution_pending",
    "preserve_v3_23_semantics",
    "narrow_profile_or_adapter_candidate",
    "supersede_required",
    "ready",
    "pending",
    "blocked",
    "in_progress",
    "cancelled",
    "superseded",
]
EXPECTED_VERIFICATION_PROFILES = {"planning", "new_runtime"}
EXPECTED_NEW_RUNTIME_VERIFICATION = [
    "uv lock --check --offline --project runtime/local-ai-runtime",
    "uv build --offline --project runtime/local-ai-runtime runtime/local-ai-runtime",
    "uv run --locked --offline --project runtime/local-ai-runtime python -m pytest",
    "uv run --locked --offline --project runtime/local-ai-runtime python -m local_ai_runtime contracts verify",
    "uv run --locked --offline --project runtime/local-ai-runtime ruff check runtime/local-ai-runtime",
    "uv run --locked --offline --project runtime/local-ai-runtime pyright --project runtime/local-ai-runtime",
    "python scripts/verify-planning-status.py",
    "python scripts/select-next-work.py",
    "git diff --check",
]
EXPECTED_GRAPH_ROOTS = ["LAR-P0A-001"]
EXPECTED_SUPERSEDED_PLAN = {
    "plan_id": "local-ai-runtime-0.2-v3.22-implementation-work-items",
    "terminal_status": "superseded",
    "last_commit": "6fd6cd54037f17e44192bc272306b137def7f8a4",
    "byte_count": 202002,
    "sha256": "acabe34f188d73015536a141a8990c333ce6643dc28347671c2523adcaf7d2cc",
}
CURRENT_LINEAGE_BYTE_COUNT = 3495
CURRENT_LINEAGE_SHA256 = (
    "49141a69c9aed6065ba063714fb2349750e500199ed8dfaf64fa6e2b198b9043"
)
NATIVE_THIN_PATH_EVALUATION_ROOT = Path("docs/evaluations/local-ai-runtime-0.2")
NATIVE_THIN_PATH_EVALUATION_CONTRACT_SET_ID = (
    "local-ai-runtime-0.2-v3.23-native-thin-path-evaluation-v1"
)
NATIVE_THIN_PATH_EVALUATION_SNAPSHOT = {
    "commit": "6fd6cd54037f17e44192bc272306b137def7f8a4",
    "tree": "11c8ab770769b3aeff5c111063a316e712fa7241",
}
NATIVE_THIN_PATH_EVALUATION_CONTRACTS = (
    (
        "docs/evaluations/local-ai-runtime-0.2/"
        "native-thin-path-capability-evaluation.v1.json",
        "NativeThinPathCapabilityEvaluation.v1",
    ),
    (
        "docs/evaluations/local-ai-runtime-0.2/"
        "native-thin-path-task-family-manifest.v1.json",
        "NativeThinPathTaskFamilyManifest.v1",
    ),
    (
        "docs/evaluations/local-ai-runtime-0.2/"
        "native-thin-path-evidence-schema.v1.json",
        "NativeThinPathEvidenceSchema.v1",
    ),
)
NATIVE_THIN_PATH_EVALUATION_CONTRACT_REFS = {
    "evaluation_contract": NATIVE_THIN_PATH_EVALUATION_CONTRACTS[0][0],
    "task_family_manifest": NATIVE_THIN_PATH_EVALUATION_CONTRACTS[1][0],
    "evidence_schema": NATIVE_THIN_PATH_EVALUATION_CONTRACTS[2][0],
}
NATIVE_THIN_PATH_EVALUATION_VARIANTS = [
    "thin_codex_native",
    "native_plus_key_gates",
    "superpowers_when_applicable",
    "trellis_when_applicable",
    "hermes_when_applicable",
]
NATIVE_THIN_PATH_EVALUATION_SURFACES = [
    "codex_cli_execution_interface",
    "codex_app_server_client_protocol",
    "codex_sdk_execution_interface",
    "codex_managed_worktree_isolation",
    "codex_automations_scheduling",
]
NATIVE_THIN_PATH_EVALUATION_METRICS = [
    "task_success_rate",
    "missed_defect_or_regression_rate",
    "safety_gate_evidence_completeness",
    "net_human_minutes",
    "wall_time_p50_p95",
    "token_and_cost",
    "conflict_and_rework",
    "recovery_and_rollback_success_rate",
    "sampled_downstream_outcome",
]
NATIVE_THIN_PATH_EVALUATION_HARD_RULES = [
    "quality_security_or_evidence_regression_invalidates_efficiency_gain",
    "unknown_or_unowned_external_effect_stops_evaluation",
    "unreproducible_recovery_or_rollback_stops_evaluation",
    "censored_or_unknown_downstream_outcome_remains_in_denominator",
]
NATIVE_THIN_PATH_EVALUATION_DECISIONS = [
    "preserve_v3_23_semantics",
    "narrow_profile_or_adapter_candidate",
    "supersede_required",
]
NATIVE_THIN_PATH_RESULTS_SCHEMA = "NativeThinPathCapabilityResults.v1"
NATIVE_THIN_PATH_DECISION_SCHEMA = "NativeThinPathCapabilityDecision.v1"
NATIVE_THIN_PATH_EVIDENCE_SCHEMA = "NativeThinPathCapabilityEvidence.v1"
BASELINE_MANIFEST_SCHEMA_PATH = Path(
    "docs/specs/local-ai-runtime-0.2/normative/BaselineManifest.v1.schema.json"
)
BASELINE_MANIFEST_FIXTURE_PATH = Path(
    "docs/specs/local-ai-runtime-0.2/fixtures/baseline-bytes/manifest.json"
)
BASELINE_VERIFIER_SKELETON_PATH = Path("scripts/verify-local-ai-runtime-baseline.py")
FINAL_BASELINE_MANIFEST_PATH = Path(
    "docs/specs/local-ai-runtime-0.2/normative/BaselineManifest.v1.json"
)
EXPECTED_CONTRACT_PROJECTIONS = [
    {
        "projection_id": "work_definition_task_family_v1",
        "required_contract_tokens": ["WorkDefinition", "TaskFamily"],
        "normative_producer_task_id": "LAR-P0A-004",
        "implementation_task_ids": ["LAR-P1A-002", "LAR-P1F-003"],
        "acceptance_task_ids": ["LAR-P1G-001", "LAR-P4-001"],
    },
    {
        "projection_id": "effect_plan_v1",
        "required_contract_tokens": ["EffectPlan"],
        "normative_producer_task_id": "LAR-P0A-006",
        "implementation_task_ids": ["LAR-P1A-002", "LAR-P1B-003", "LAR-P1D-003"],
        "acceptance_task_ids": ["LAR-P1G-001"],
    },
    {
        "projection_id": "gate_graph_v1",
        "required_contract_tokens": ["GateGraph"],
        "normative_producer_task_id": "LAR-P0A-010",
        "implementation_task_ids": ["LAR-P1D-006"],
        "acceptance_task_ids": ["LAR-P1E-007", "LAR-P1G-001"],
    },
    {
        "projection_id": "three_level_evolution_v1",
        "required_contract_tokens": [
            "profile_generation",
            "capability_generation",
            "architecture_epoch",
        ],
        "normative_producer_task_id": "LAR-P0A-010",
        "implementation_task_ids": ["LAR-P1A-002", "LAR-P1C-001", "LAR-P1C-006"],
        "acceptance_task_ids": ["LAR-P1G-001", "LAR-Q0-001"],
    },
    {
        "projection_id": "writer_effect_launch_identity_v1",
        "required_contract_tokens": ["writer_effect_id", "writer_launch_id"],
        "normative_producer_task_id": "LAR-P0A-006",
        "implementation_task_ids": ["LAR-P1B-003", "LAR-P1D-002"],
        "acceptance_task_ids": ["LAR-P1G-001"],
    },
    {
        "projection_id": "durable_operator_action_inbox_v1",
        "required_contract_tokens": [
            "durable_local_status_v1",
            "qualified_windows_toast_v1",
        ],
        "normative_producer_task_id": "LAR-P0A-009",
        "implementation_task_ids": ["LAR-P1F-005"],
        "acceptance_task_ids": ["LAR-P1G-001"],
    },
    {
        "projection_id": "git_hybrid_materialization_v1",
        "required_contract_tokens": [
            "git_hybrid_materialization_v1",
            "hash-object -w",
            "cat-file",
        ],
        "normative_producer_task_id": "LAR-P0A-008",
        "implementation_task_ids": ["LAR-P1E-003"],
        "acceptance_task_ids": ["LAR-P1E-007", "LAR-P1G-001"],
    },
    {
        "projection_id": "q0_trigger_policy_v1",
        "required_contract_tokens": ["Q0TriggerPolicy"],
        "normative_producer_task_id": "LAR-P0A-010",
        "implementation_task_ids": ["LAR-P1C-006"],
        "acceptance_task_ids": ["LAR-P1G-001", "LAR-Q0-001"],
    },
    {
        "projection_id": "controlled_baseline_approval_v1",
        "required_contract_tokens": [
            "BaselineApprovalCommandPolicy",
            "anti_replay_challenge",
        ],
        "normative_producer_task_id": "LAR-P0A-013",
        "implementation_task_ids": [],
        "acceptance_task_ids": ["LAR-GOV-001"],
    },
    {
        "projection_id": "activation_admission_chain_v1",
        "required_contract_tokens": [
            "RuntimeCompositionManifest",
            "SelectedRuntimeIdentity",
            "ActiveRuntimeIdentity",
        ],
        "normative_producer_task_id": "LAR-P0A-010",
        "implementation_task_ids": ["LAR-P1C-001"],
        "acceptance_task_ids": ["LAR-P1G-001", "LAR-Q0-001"],
    },
    {
        "projection_id": "portfolio_data_only_v1",
        "required_contract_tokens": ["portfolio_data_only_v1"],
        "normative_producer_task_id": "LAR-P0A-009",
        "implementation_task_ids": ["LAR-P1F-003"],
        "acceptance_task_ids": ["LAR-P4-001", "LAR-P4-002"],
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the Local AI Runtime planning control plane."
    )
    parser.add_argument("--repo-root", default=str(ROOT))
    parser.add_argument("--status-path", default=str(DEFAULT_STATUS_PATH))
    args = parser.parse_args()

    try:
        result = verify(
            repo_root=Path(args.repo_root),
            status_path=Path(args.status_path),
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # Fail closed on malformed nested control-plane data.
        print(
            f"planning status verification failed unexpectedly: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def verify(*, repo_root: Path, status_path: Path) -> dict[str, object]:
    root = repo_root.resolve(strict=False)
    status, status_raw = _load_json_with_bytes(status_path)
    failures: list[str] = []

    _require_fields(
        status,
        [
            "schema_version",
            "status_id",
            "updated_on",
            "baseline_candidate",
            "baseline_entry",
            "approval_state",
            "normative_package",
            "native_thin_path_evaluation",
            "current_active_queue",
            "current_work_item",
            "legacy_runtime_posture",
            "truth_reset",
            "implementation",
            "p2_admission",
            "rollout",
            "current_evidence_ref",
            "authoritative_docs",
            "doc_contracts",
            "forbidden_state_combinations",
            "rollback_ref",
        ],
        "planning status",
        failures,
    )
    if status.get("schema_version") != "2.0":
        failures.append("planning status schema_version must be '2.0'")

    baseline = _as_dict(status.get("baseline_candidate"), "baseline_candidate", failures)
    baseline_entry = _as_dict(status.get("baseline_entry"), "baseline_entry", failures)
    approval = _as_dict(status.get("approval_state"), "approval_state", failures)
    package_state = _as_dict(status.get("normative_package"), "normative_package", failures)
    evaluation = _as_dict(
        status.get("native_thin_path_evaluation"),
        "native_thin_path_evaluation",
        failures,
    )
    queue = _as_dict(status.get("current_active_queue"), "current_active_queue", failures)
    current_work = _as_dict(status.get("current_work_item"), "current_work_item", failures)
    legacy = _as_dict(status.get("legacy_runtime_posture"), "legacy_runtime_posture", failures)
    truth_reset = _as_dict(status.get("truth_reset"), "truth_reset", failures)
    implementation = _as_dict(status.get("implementation"), "implementation", failures)
    p2 = _as_dict(status.get("p2_admission"), "p2_admission", failures)
    rollout = _as_dict(status.get("rollout"), "rollout", failures)

    _verify_baseline(root, baseline, failures)
    _verify_baseline_entry(root, baseline_entry, baseline, failures)

    inventory: dict[str, Any] = {}
    inventory_ref = package_state.get("inventory_ref")
    try:
        inventory_path = _resolve_repo_path(root, inventory_ref, "normative package inventory")
        inventory = _load_json(inventory_path)
    except ValueError as exc:
        failures.append(str(exc))
        inventory_path = root / "__missing_inventory__"

    if inventory:
        _verify_inventory(
            root=root,
            inventory_path=inventory_path,
            baseline=baseline,
            package_state=package_state,
            inventory=inventory,
            failures=failures,
        )
        _verify_baseline_entry_inventory_exclusion(
            baseline_entry,
            inventory,
            failures,
        )
        _verify_current_lineage(root, baseline, inventory, failures)

    work_items_payload: dict[str, Any] = {}
    work_items_ref = queue.get("source_work_items")
    try:
        work_items_path = _resolve_repo_path(root, work_items_ref, "work-item source")
        work_items_payload = _load_json(work_items_path)
    except ValueError as exc:
        failures.append(str(exc))
        work_items_path = root / "__missing_work_items__"

    work_items: dict[str, dict[str, Any]] = {}
    if work_items_payload:
        work_items = _verify_work_items(
            work_items_payload,
            baseline,
            queue,
            current_work,
            failures,
        )
        _verify_runtime_source_tree(
            root,
            work_items_payload.get("runtime_source_layout"),
            failures,
        )
        if inventory:
            _verify_inventory_task_links(inventory, work_items, current_work, failures)
        _verify_manifest_contract_slice(root, work_items, inventory, failures)

    try:
        policy_path = _resolve_repo_path(root, str(POLICY_PATH), "selector policy")
        policy, policy_raw = _load_json_with_bytes(policy_path)
    except ValueError as exc:
        failures.append(str(exc))
        policy = {}
        policy_path = root / POLICY_PATH
    if policy:
        _verify_selector_policy(
            root,
            policy,
            package_state,
            current_work,
            failures,
        )

    _verify_approval_and_stages(
        root=root,
        approval=approval,
        package_state=package_state,
        queue=queue,
        current_work=current_work,
        evaluation=evaluation,
        legacy=legacy,
        truth_reset=truth_reset,
        implementation=implementation,
        p2=p2,
        rollout=rollout,
        failures=failures,
    )
    _verify_authoritative_docs(root, status, failures)
    try:
        evidence_path = _resolve_repo_path(
            root, status.get("current_evidence_ref"), "current evidence"
        )
    except ValueError as exc:
        failures.append(str(exc))
    else:
        if not evidence_path.is_file():
            failures.append("current evidence file does not exist")

    if failures:
        rendered = "\n- ".join(failures)
        raise ValueError(f"planning status verification failed:\n- {rendered}")

    return {
        "status": "pass",
        "status_path": _relative_or_absolute(root, status_path),
        "status_sha256": hashlib.sha256(status_raw).hexdigest(),
        "selector_policy_path": _relative_or_absolute(root, policy_path),
        "selector_policy_sha256": hashlib.sha256(policy_raw).hexdigest(),
        "baseline_id": baseline["id"],
        "baseline_status": baseline["status"],
        "baseline_byte_count": baseline["byte_count"],
        "baseline_sha256": baseline["sha256"],
        "blocking_stage": baseline["blocking_stage"],
        "approval_active": approval["active"],
        "native_thin_path_evaluation_status": evaluation["status"],
        "native_thin_path_evaluation_decision": evaluation["decision"],
        "normative_package_status": package_state["status"],
        "missing_artifact_count": len(package_state["missing_artifact_ids"]),
        "current_queue": queue["queue_id"],
        "current_work_item_id": current_work["task_id"],
        "current_selector_action": current_work["selector_action"],
        "authoritative_doc_count": len(status["authoritative_docs"]),
        "work_item_count": len(work_items),
        "truth_reset_performed": truth_reset["performed"],
        "implementation_started": implementation["started"],
        "p2_admitted": p2["admitted"],
        "rollout_complete": rollout["p5_cutover_complete"],
    }


def _verify_baseline(root: Path, baseline: dict[str, Any], failures: list[str]) -> None:
    _require_fields(
        baseline,
        [
            "id",
            "path",
            "byte_count",
            "sha256",
            "status",
            "decision",
            "blocking_stage",
        ],
        "baseline_candidate",
        failures,
    )
    if baseline.get("id") != CURRENT_BASELINE_ID:
        failures.append(f"baseline_candidate.id must be {CURRENT_BASELINE_ID}")
    if baseline.get("path") != CURRENT_BASELINE_PATH:
        failures.append(f"baseline_candidate.path must be {CURRENT_BASELINE_PATH}")
    if baseline.get("status") != "baseline_candidate":
        failures.append("baseline_candidate.status must remain baseline_candidate before approval")
    if baseline.get("blocking_stage") != "baseline_approval":
        failures.append("baseline_candidate.blocking_stage must be baseline_approval")

    try:
        path = _resolve_repo_path(root, baseline.get("path"), "baseline candidate")
        raw = path.read_bytes()
    except (OSError, ValueError) as exc:
        failures.append(f"baseline candidate is unreadable: {exc}")
        return

    _verify_normative_bytes(raw, "baseline candidate", failures)
    expected_count = baseline.get("byte_count")
    if not isinstance(expected_count, int) or isinstance(expected_count, bool):
        failures.append("baseline_candidate.byte_count must be an integer")
    elif len(raw) != expected_count:
        failures.append(
            f"baseline candidate byte count mismatch: expected {expected_count}, got {len(raw)}"
        )
    actual_hash = hashlib.sha256(raw).hexdigest()
    expected_hash = baseline.get("sha256")
    if not _is_sha256(expected_hash):
        failures.append("baseline_candidate.sha256 must be 64 lowercase hex characters")
    elif actual_hash != expected_hash:
        failures.append(
            f"baseline candidate SHA-256 mismatch: expected {expected_hash}, got {actual_hash}"
        )


def _verify_baseline_entry(
    root: Path,
    entry: dict[str, Any],
    baseline: dict[str, Any],
    failures: list[str],
) -> None:
    _require_fields(
        entry,
        [
            "path",
            "role",
            "target_baseline_id",
            "target_path",
            "target_byte_count",
            "target_sha256",
            "approval_input",
            "maximum_byte_count",
            "byte_count",
            "sha256",
        ],
        "baseline_entry",
        failures,
    )
    if entry.get("path") != CURRENT_BASELINE_ENTRY_PATH:
        failures.append(f"baseline_entry.path must be {CURRENT_BASELINE_ENTRY_PATH}")
    if entry.get("role") != BASELINE_ENTRY_ROLE:
        failures.append(
            f"baseline_entry.role must be {BASELINE_ENTRY_ROLE}"
        )
    if entry.get("approval_input") is not False:
        failures.append("baseline_entry.approval_input must remain false")
    if entry.get("maximum_byte_count") != BASELINE_ENTRY_MAXIMUM_BYTE_COUNT:
        failures.append(
            "baseline_entry.maximum_byte_count must be "
            f"{BASELINE_ENTRY_MAXIMUM_BYTE_COUNT}"
        )

    for entry_field, baseline_field in (
        ("target_baseline_id", "id"),
        ("target_path", "path"),
        ("target_byte_count", "byte_count"),
        ("target_sha256", "sha256"),
    ):
        if entry.get(entry_field) != baseline.get(baseline_field):
            failures.append(
                f"baseline_entry.{entry_field} must match "
                f"baseline_candidate.{baseline_field}"
            )

    try:
        path = _resolve_repo_path(root, entry.get("path"), "baseline entry")
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        failures.append(f"baseline entry is unreadable: {exc}")
        return

    maximum = entry.get("maximum_byte_count")
    if isinstance(maximum, int) and not isinstance(maximum, bool) and len(raw) > maximum:
        failures.append("baseline entry exceeds its maximum_byte_count")
    _verify_normative_bytes(raw, "baseline entry", failures)
    expected_count = entry.get("byte_count")
    if not isinstance(expected_count, int) or isinstance(expected_count, bool):
        failures.append("baseline_entry.byte_count must be an integer")
    elif len(raw) != expected_count:
        failures.append(
            f"baseline entry byte count mismatch: expected {expected_count}, got {len(raw)}"
        )
    expected_hash = entry.get("sha256")
    if not _is_sha256(expected_hash):
        failures.append("baseline_entry.sha256 must be 64 lowercase hex characters")
    else:
        actual_hash = hashlib.sha256(raw).hexdigest()
        if actual_hash != expected_hash:
            failures.append(
                "baseline entry SHA-256 mismatch: "
                f"expected {expected_hash}, got {actual_hash}"
            )

    required_markers = (
        "role=non_normative_navigation",
        "approval_input=false",
        str(baseline.get("id")),
        str(baseline.get("path")),
        str(baseline.get("sha256")),
        "not a narrative specification",
        "BaselineManifest.v1",
        "BaselineApprovalRecord",
    )
    for marker in required_markers:
        if marker not in text:
            failures.append(f"baseline entry missing required marker: {marker}")


def _verify_baseline_entry_inventory_exclusion(
    entry: dict[str, Any],
    inventory: dict[str, Any],
    failures: list[str],
) -> None:
    entry_path = entry.get("path")
    if not isinstance(entry_path, str):
        return

    source = inventory.get("candidate_source")
    if isinstance(source, dict) and source.get("path") == entry_path:
        failures.append("baseline entry must not be the inventory candidate source")

    artifacts = inventory.get("required_artifacts")
    if not isinstance(artifacts, list):
        return
    for index, artifact in enumerate(artifacts):
        if isinstance(artifact, dict) and artifact.get("path") == entry_path:
            failures.append(
                "baseline entry must not be a normative artifact: "
                f"inventory.required_artifacts[{index}]"
            )


def _verify_normative_bytes(raw: bytes, label: str, failures: list[str]) -> None:
    if raw.startswith(b"\xef\xbb\xbf"):
        failures.append(f"{label} must not contain a UTF-8 BOM")
    if b"\r" in raw:
        failures.append(f"{label} must use LF and contain no CR")
    if b"\x00" in raw:
        failures.append(f"{label} must contain no NUL")
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        failures.append(f"{label} must end with exactly one LF")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        failures.append(f"{label} must be valid UTF-8: {exc}")
        return
    if text != unicodedata.normalize("NFC", text):
        failures.append(f"{label} must already be Unicode NFC")
    for line_no, line in enumerate(text.split("\n"), start=1):
        if line.endswith((" ", "\t")):
            failures.append(f"{label} has trailing SP/HTAB at line {line_no}")
            break
    disallowed_format_or_control = sorted(
        {
            (ord(ch), unicodedata.category(ch))
            for ch in text
            if ch != "\n" and unicodedata.category(ch) in {"Cc", "Cf"}
        }
    )
    if disallowed_format_or_control:
        failures.append(
            f"{label} contains disallowed Unicode Cc/Cf characters: "
            f"{disallowed_format_or_control[:16]}"
        )
    disallowed_separators = sorted(
        {
            (ord(ch), unicodedata.category(ch))
            for ch in text
            if unicodedata.category(ch) in {"Zl", "Zp"}
        }
    )
    if disallowed_separators:
        failures.append(
            f"{label} contains non-LF Unicode line/paragraph separators: "
            f"{disallowed_separators[:16]}"
        )
    noncharacters = sorted({ord(ch) for ch in text if _is_unicode_noncharacter(ord(ch))})
    if noncharacters:
        failures.append(
            f"{label} contains Unicode noncharacters: {noncharacters[:16]}"
        )


def _verify_lineage_archives(
    root: Path, value: Any, failures: list[str]
) -> None:
    lineage = _as_dict(value, "inventory.lineage", failures)
    candidates = lineage.get("superseded_candidates")
    if not isinstance(candidates, list):
        failures.append("inventory.lineage.superseded_candidates must be an array")
        return

    seen_ids: set[str] = set()
    candidates_by_id: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(candidates):
        label = f"inventory.lineage.superseded_candidates[{index}]"
        candidate = _as_dict(value, label, failures)
        candidate_id = candidate.get("id")
        if not isinstance(candidate_id, str) or not candidate_id:
            failures.append(f"{label}.id must be a non-empty string")
            continue
        if candidate_id in seen_ids:
            failures.append(f"duplicate superseded candidate id: {candidate_id}")
        seen_ids.add(candidate_id)
        candidates_by_id[candidate_id] = candidate

        archive_status = candidate.get("archive_status")
        if archive_status == "missing_verified_archive":
            continue
        if archive_status != "present_verified_archive":
            failures.append(f"{label}.archive_status is unknown: {archive_status!r}")
            continue

        _require_fields(candidate, ["path", "byte_count", "sha256"], label, failures)
        expected_count = candidate.get("byte_count")
        expected_hash = candidate.get("sha256")
        if not isinstance(expected_count, int) or isinstance(expected_count, bool):
            failures.append(f"{label}.byte_count must be an integer")
        if not _is_sha256(expected_hash):
            failures.append(f"{label}.sha256 must be 64 lowercase hex characters")

        try:
            path = _resolve_repo_path(root, candidate.get("path"), label)
            raw = path.read_bytes()
        except (OSError, ValueError) as exc:
            failures.append(f"{label} archive is unreadable: {exc}")
            continue

        _verify_normative_bytes(raw, f"{candidate_id} archive", failures)
        if isinstance(expected_count, int) and not isinstance(expected_count, bool):
            if len(raw) != expected_count:
                failures.append(
                    f"{candidate_id} archive byte count mismatch: "
                    f"expected {expected_count}, got {len(raw)}"
                )
        if _is_sha256(expected_hash):
            actual_hash = hashlib.sha256(raw).hexdigest()
            if actual_hash != expected_hash:
                failures.append(
                    f"{candidate_id} archive SHA-256 mismatch: "
                    f"expected {expected_hash}, got {actual_hash}"
                )

    required_archives = {
        "local-ai-runtime-0.2-v3.19": {
            "path": "docs/specs/local-ai-runtime-0.2-v3.19-baseline-candidate.md",
            "byte_count": 111952,
            "sha256": "275306d2e88baafa803170ee4ef99fb822c4e13769721b806805b834bb9d7670",
        },
        "local-ai-runtime-0.2-v3.20": {
            "path": "docs/specs/local-ai-runtime-0.2-v3.20-baseline-candidate.md",
            "byte_count": 130890,
            "sha256": "43cb98737daa5d171a9cda2dca49c8f118fb8be92745b4076948d9178e56a130",
        },
    }
    for candidate_id, expected in required_archives.items():
        candidate = candidates_by_id.get(candidate_id)
        if candidate is None:
            failures.append(f"inventory lineage must include frozen {candidate_id} archive")
            continue
        if candidate.get("archive_status") != "present_verified_archive":
            failures.append(f"{candidate_id} must be a present_verified_archive")
        for field, value in expected.items():
            if candidate.get(field) != value:
                failures.append(f"{candidate_id}.{field} must equal {value!r}")

    v317 = candidates_by_id.get("local-ai-runtime-0.2-v3.17")
    if v317 is None:
        failures.append("inventory lineage must retain the v3.17 superseded candidate")
    elif v317.get("archive_status") == "missing_verified_archive":
        if v317.get("sha256") is not None:
            failures.append("unarchived v3.17 sha256 must remain null")
        if not _is_sha256(v317.get("provisional_transcript_sha256")):
            failures.append("unarchived v3.17 must retain a provisional transcript SHA-256")

    historical_record_path = root / HISTORICAL_SOURCE_RECORD_PATH
    if historical_record_path.is_file():
        try:
            historical_record = _load_json(historical_record_path)
        except ValueError as exc:
            failures.append(str(exc))
        else:
            _verify_historical_source_record(root, historical_record, failures)

    conflicted = lineage.get("conflicted_candidate_ids")
    if not isinstance(conflicted, list) or len(conflicted) != 1:
        failures.append("inventory lineage must contain exactly one conflicted candidate ID")
    else:
        v318 = _as_dict(conflicted[0], "inventory.lineage.conflicted_candidate_ids[0]", failures)
        expected_v318_archives = [
            {
                "archive_id": "local-ai-runtime-0.2-v3.18-a",
                "path": "docs/specs/local-ai-runtime-0.2/history/local-ai-runtime-0.2-v3.18-a.md",
                "byte_count": 66328,
                "sha256": "6924ba562dda8e69274eb80fef9e3a9699eb493570ee08330fcad5ec4bc3baa5",
            },
            {
                "archive_id": "local-ai-runtime-0.2-v3.18-b",
                "path": "docs/specs/local-ai-runtime-0.2/history/local-ai-runtime-0.2-v3.18-b.md",
                "byte_count": 43908,
                "sha256": "8da5aa20fb44d95503e443822163397a2aa1df590e1916d1a5a10a6c24ea06b7",
            },
        ]
        if v318.get("id") != "local-ai-runtime-0.2-v3.18":
            failures.append("conflicted candidate ID must remain local-ai-runtime-0.2-v3.18")
        if v318.get("required_distinct_archives") != 2:
            failures.append("v3.18 must require exactly two distinct archives")
        if v318.get("verified_archives") != expected_v318_archives:
            failures.append("v3.18 verified archive identities must match recovered bytes")
        if v318.get("archive_status") != "present_verified_archives":
            failures.append("v3.18 archive_status must be present_verified_archives")
        if v318.get("source_record") != HISTORICAL_SOURCE_RECORD_PATH:
            failures.append("v3.18 source_record must reference HistoricalSourceArchive.v1")


def _verify_historical_source_record(
    root: Path, record: dict[str, Any], failures: list[str]
) -> None:
    if record.get("schema_version") != "HistoricalSourceArchive.v1":
        failures.append("historical source record schema_version mismatch")
    if record.get("record_kind") != "exact_message_content_archive":
        failures.append("historical source record kind mismatch")
    if record.get("normative") is not False:
        failures.append("historical source record must be non-normative")
    if record.get("session_id") != "019f5081-9022-7681-9378-fa14e695131b":
        failures.append("historical source record session_id mismatch")
    if record.get("session_basename") != (
        "rollout-2026-07-11T17-28-21-019f5081-9022-7681-9378-fa14e695131b.jsonl"
    ):
        failures.append("historical source record session basename mismatch")
    if record.get("required_independent_hash_methods") != [
        "python_hashlib_sha256",
        "powershell_get_file_hash_sha256",
    ]:
        failures.append("historical source record must require both independent hash methods")

    expected = {
        "local-ai-runtime-0.2-v3.17": (
            "docs/specs/local-ai-runtime-0.2/history/local-ai-runtime-0.2-v3.17.md",
            32825,
            "a285f5f421a8ccd4debd8794609a2aa0eb07bb1bf651c2467a95f7cad25a5f81",
            7409,
            "assistant",
            "output_text",
            "unwrap_proposed_plan",
            16,
            16,
        ),
        "local-ai-runtime-0.2-v3.18-a": (
            "docs/specs/local-ai-runtime-0.2/history/local-ai-runtime-0.2-v3.18-a.md",
            66328,
            "6924ba562dda8e69274eb80fef9e3a9699eb493570ee08330fcad5ec4bc3baa5",
            8408,
            "assistant",
            "output_text",
            "unwrap_proposed_plan",
            16,
            16,
        ),
        "local-ai-runtime-0.2-v3.18-b": (
            "docs/specs/local-ai-runtime-0.2/history/local-ai-runtime-0.2-v3.18-b.md",
            43908,
            "8da5aa20fb44d95503e443822163397a2aa1df590e1916d1a5a10a6c24ea06b7",
            8429,
            "user",
            "input_text",
            "from_unique_title",
            105,
            0,
        ),
    }
    archives = record.get("archives")
    if not isinstance(archives, list) or len(archives) != len(expected):
        failures.append("historical source record must contain exactly three archives")
        return
    seen: set[str] = set()
    for index, value in enumerate(archives):
        archive = _as_dict(value, f"historical archives[{index}]", failures)
        archive_id = archive.get("archive_id")
        if archive_id not in expected or archive_id in seen:
            failures.append(f"unexpected or duplicate historical archive ID: {archive_id!r}")
            continue
        seen.add(archive_id)
        path_value, byte_count, sha256, line, role, content_type, extraction, prefix, suffix = expected[archive_id]
        if archive.get("path") != path_value:
            failures.append(f"{archive_id} historical path mismatch")
        try:
            raw = _resolve_repo_path(root, path_value, archive_id).read_bytes()
        except (OSError, ValueError) as exc:
            failures.append(f"{archive_id} historical archive is unreadable: {exc}")
            continue
        _verify_normative_bytes(raw, f"{archive_id} historical archive", failures)
        if archive.get("byte_count") != byte_count or len(raw) != byte_count:
            failures.append(f"{archive_id} historical byte count mismatch")
        if archive.get("sha256") != sha256 or hashlib.sha256(raw).hexdigest() != sha256:
            failures.append(f"{archive_id} historical SHA-256 mismatch")
        source = _as_dict(archive.get("source"), f"{archive_id}.source", failures)
        expected_source = {
            "jsonl_line": line,
            "outer_record_type": "response_item",
            "payload_type": "message",
            "role": role,
            "content_index": 0,
            "content_type": content_type,
            "text_field": "payload.content[0].text",
            "extraction": extraction,
            "excluded_prefix_utf8_bytes": prefix,
            "excluded_suffix_utf8_bytes": suffix,
        }
        if source != expected_source:
            failures.append(f"{archive_id} historical source boundary mismatch")


def _project_inventory_lineage(
    entries: list[Any], failures: list[str]
) -> dict[str, Any]:
    canonical_predecessors: list[dict[str, Any]] = []
    withdrawn_candidates: list[dict[str, Any]] = []
    superseded_candidates: list[dict[str, Any]] = []
    conflicted_archives: dict[str, list[dict[str, Any]]] = {}
    conflicted_sources: dict[str, set[str]] = {}
    withdrawn_drafts: list[dict[str, Any]] = []

    for index, value in enumerate(entries):
        label = f"BaselineLineage.v1.entries[{index}]"
        entry = _as_dict(value, label, failures)
        role = entry.get("role")
        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or not entry_id:
            failures.append(f"{label}.id must be a non-empty string")
            continue

        if role == "canonical_predecessor":
            canonical_predecessors.append(
                {"id": entry_id, "sha256": entry.get("sha256")}
            )
        elif role == "withdrawn_candidate":
            withdrawn_candidates.append(
                {"id": entry_id, "sha256": entry.get("sha256")}
            )
        elif role == "superseded_candidate":
            candidate = {
                "id": entry_id,
                "sha256": entry.get("sha256"),
                "byte_count": entry.get("byte_count"),
                "path": entry.get("path"),
            }
            if "source_record" in entry:
                candidate["source_record"] = entry.get("source_record")
            candidate["archive_status"] = "present_verified_archive"
            superseded_candidates.append(candidate)
        elif role == "conflicted_candidate_archive":
            shared_id = entry.get("shared_candidate_id")
            source_record = entry.get("source_record")
            if not isinstance(shared_id, str) or not shared_id:
                failures.append(f"{label}.shared_candidate_id must be a non-empty string")
                continue
            if not isinstance(source_record, str) or not source_record:
                failures.append(f"{label}.source_record must be a non-empty string")
                continue
            conflicted_archives.setdefault(shared_id, []).append(
                {
                    "archive_id": entry_id,
                    "path": entry.get("path"),
                    "byte_count": entry.get("byte_count"),
                    "sha256": entry.get("sha256"),
                }
            )
            conflicted_sources.setdefault(shared_id, set()).add(source_record)
        elif role == "withdrawn_draft":
            withdrawn_drafts.append({"id": entry_id, "sha256": None})
        else:
            failures.append(f"{label}.role is unknown: {role!r}")

    if len(canonical_predecessors) != 1:
        failures.append("BaselineLineage.v1 must contain exactly one canonical predecessor")

    conflicted_candidates: list[dict[str, Any]] = []
    for shared_id, archives in conflicted_archives.items():
        sources = conflicted_sources[shared_id]
        if len(sources) != 1:
            failures.append(
                f"conflicted candidate {shared_id} archives must share one source record"
            )
        conflicted_candidates.append(
            {
                "id": shared_id,
                "required_distinct_archives": len(archives),
                "verified_archives": archives,
                "source_record": next(iter(sources), None),
                "archive_status": "present_verified_archives",
            }
        )

    return {
        "canonical_predecessor": (
            canonical_predecessors[0] if canonical_predecessors else None
        ),
        "withdrawn_candidates": withdrawn_candidates,
        "superseded_candidates": superseded_candidates,
        "conflicted_candidate_ids": conflicted_candidates,
        "withdrawn_drafts": withdrawn_drafts,
    }


def _verify_current_lineage(
    root: Path,
    baseline: dict[str, Any],
    inventory: dict[str, Any],
    failures: list[str],
) -> None:
    artifacts = inventory.get("required_artifacts")
    if not isinstance(artifacts, list):
        return
    lineage_artifact = next(
        (
            artifact
            for artifact in artifacts
            if isinstance(artifact, dict)
            and artifact.get("artifact_id") == "P0A-LINEAGE"
        ),
        None,
    )
    expected_artifact = {
        "artifact_version": "BaselineLineage.v2",
        "path": CURRENT_LINEAGE_PATH,
        "status": "present",
        "byte_count": CURRENT_LINEAGE_BYTE_COUNT,
        "sha256": CURRENT_LINEAGE_SHA256,
        "producer_task_id": "LAR-P0A-REBASELINE-V323",
    }
    if lineage_artifact is None:
        failures.append("inventory must contain the P0A-LINEAGE artifact")
        return
    for field, expected in expected_artifact.items():
        if lineage_artifact.get(field) != expected:
            failures.append(f"P0A-LINEAGE.{field} must equal {expected!r}")

    try:
        lineage_path = _resolve_repo_path(root, CURRENT_LINEAGE_PATH, "BaselineLineage.v2")
        raw = lineage_path.read_bytes()
        lineage = _loads_json_object(raw.decode("utf-8"), CURRENT_LINEAGE_PATH)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        failures.append(f"BaselineLineage.v2 is unreadable: {exc}")
        return
    _verify_normative_bytes(raw, "BaselineLineage.v2", failures)
    if len(raw) != CURRENT_LINEAGE_BYTE_COUNT:
        failures.append("BaselineLineage.v2 byte count mismatch")
    if hashlib.sha256(raw).hexdigest() != CURRENT_LINEAGE_SHA256:
        failures.append("BaselineLineage.v2 SHA-256 mismatch")
    if lineage.get("domain") != "local-ai-runtime/BaselineLineage/v2":
        failures.append("BaselineLineage.v2 domain mismatch")
    if lineage.get("schema_version") != 2:
        failures.append("BaselineLineage.v2 schema_version must be 2")
    payload = _as_dict(lineage.get("payload"), "BaselineLineage.v2.payload", failures)
    expected_candidate = {
        "byte_count": baseline.get("byte_count"),
        "id": baseline.get("id"),
        "path": baseline.get("path"),
        "role": "baseline_candidate",
        "sha256": baseline.get("sha256"),
    }
    if payload.get("candidate") != expected_candidate:
        failures.append("BaselineLineage.v2 candidate must bind the current v3.23 identity")

    entries_value = payload.get("entries")
    if not isinstance(entries_value, list):
        failures.append("BaselineLineage.v2 entries must be an array")
        return
    entries = {
        entry.get("id"): entry for entry in entries_value if isinstance(entry, dict)
    }
    expected_v322 = {
        "byte_count": 178330,
        "id": "local-ai-runtime-0.2-v3.22",
        "path": "docs/specs/local-ai-runtime-0.2-v3.22-baseline-candidate.md",
        "role": "superseded_candidate",
        "sha256": "8338a9dcf4bbbb40ca28f4f2ec6dca37587ee94fbfbbc6e3a0063c4de379569c",
    }
    if entries.get("local-ai-runtime-0.2-v3.22") != expected_v322:
        failures.append("BaselineLineage.v2 must bind the exact superseded v3.22 identity")
    if len(entries) != len(entries_value):
        failures.append("BaselineLineage.v2 entry IDs must be unique")

    projected_inventory_lineage = _project_inventory_lineage(entries_value, failures)
    if inventory.get("lineage") != projected_inventory_lineage:
        failures.append("inventory lineage must exactly project BaselineLineage.v2")

    historical = _as_dict(
        payload.get("historical_source_archive"),
        "BaselineLineage.v2.historical_source_archive",
        failures,
    )
    historical_path = historical.get("path")
    try:
        historical_bytes = _resolve_repo_path(
            root, historical_path, "BaselineLineage historical source"
        ).read_bytes()
    except (OSError, ValueError) as exc:
        failures.append(f"BaselineLineage historical source is unreadable: {exc}")
    else:
        if historical.get("byte_count") != len(historical_bytes):
            failures.append("BaselineLineage historical source byte count mismatch")
        if (
            not _is_sha256(historical.get("sha256"))
            or hashlib.sha256(historical_bytes).hexdigest() != historical.get("sha256")
        ):
            failures.append("BaselineLineage historical source SHA-256 mismatch")


def _verify_inventory(
    *,
    root: Path,
    inventory_path: Path,
    baseline: dict[str, Any],
    package_state: dict[str, Any],
    inventory: dict[str, Any],
    failures: list[str],
) -> None:
    _require_fields(
        inventory,
        [
            "schema_version",
            "record_kind",
            "normative",
            "package_id",
            "baseline_id",
            "package_status",
            "approval_eligible",
            "blocking_stage",
            "candidate_source",
            "lineage",
            "required_artifacts",
            "missing_artifact_ids",
            "approval_record",
            "invariants",
        ],
        "normative package inventory",
        failures,
    )
    if inventory.get("record_kind") != "preapproval_inventory" or inventory.get("normative") is not False:
        failures.append("normative package inventory must be a non-normative preapproval_inventory")
    if inventory.get("baseline_id") != baseline.get("id"):
        failures.append("inventory baseline_id must match planning baseline id")
    if inventory.get("package_id") != f"{CURRENT_BASELINE_ID}-normative-package":
        failures.append("inventory package_id must match the v3.23 package identity")
    if inventory.get("blocking_stage") != baseline.get("blocking_stage"):
        failures.append("inventory blocking_stage must match planning baseline")

    source = _as_dict(inventory.get("candidate_source"), "inventory.candidate_source", failures)
    for field in ("path", "byte_count", "sha256", "status"):
        if source.get(field) != baseline.get(field):
            failures.append(f"inventory candidate_source.{field} must match planning baseline")

    _verify_lineage_archives(root, inventory.get("lineage"), failures)

    artifacts = inventory.get("required_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        failures.append("inventory.required_artifacts must be a non-empty array")
        return
    artifact_ids = [item.get("artifact_id") for item in artifacts if isinstance(item, dict)]
    if artifact_ids != EXPECTED_ARTIFACT_IDS:
        failures.append(
            "inventory artifact IDs/order must match the v3.23 closure sequence"
        )

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    artifacts_by_id: dict[str, dict[str, Any]] = {}
    actual_missing: list[str] = []
    present_count = 0
    verifier_path: Path | None = None
    for index, item in enumerate(artifacts):
        label = f"inventory.required_artifacts[{index}]"
        if not isinstance(item, dict):
            failures.append(f"{label} must be an object")
            continue
        _require_fields(
            item,
            [
                "artifact_id",
                "kind",
                "artifact_version",
                "path",
                "status",
                "required_for_approval",
                "producer_task_id",
                "verification",
            ],
            label,
            failures,
        )
        artifact_id = item.get("artifact_id")
        path_value = item.get("path")
        if not isinstance(artifact_id, str) or not artifact_id:
            failures.append(f"{label}.artifact_id must be non-empty")
            continue
        if artifact_id in seen_ids:
            failures.append(f"duplicate inventory artifact_id: {artifact_id}")
        seen_ids.add(artifact_id)
        artifacts_by_id[artifact_id] = item
        artifact_version = item.get("artifact_version")
        if not isinstance(artifact_version, str) or not artifact_version:
            failures.append(f"{label}.artifact_version must be non-empty")
        if not isinstance(path_value, str) or not path_value:
            failures.append(f"{label}.path must be non-empty")
            continue
        if path_value in seen_paths:
            failures.append(f"duplicate inventory path: {path_value}")
        seen_paths.add(path_value)
        try:
            artifact_path = _resolve_repo_path(root, path_value, label)
        except ValueError as exc:
            failures.append(str(exc))
            continue

        item_status = item.get("status")
        if item.get("required_for_approval") is not True:
            failures.append(f"{label}.required_for_approval must be true")
        if item_status == "present":
            present_count += 1
            if not artifact_path.is_file():
                failures.append(f"present artifact does not exist: {path_value}")
            else:
                raw = artifact_path.read_bytes()
                byte_count = item.get("byte_count")
                sha256 = item.get("sha256")
                if byte_count != len(raw):
                    failures.append(
                        f"{label}.byte_count must match present artifact bytes"
                    )
                if not _is_sha256(sha256) or hashlib.sha256(raw).hexdigest() != sha256:
                    failures.append(f"{label}.sha256 must match present artifact bytes")
                if artifact_id == "P0A-VERIFIER":
                    verifier_path = artifact_path
        elif item_status == "missing":
            actual_missing.append(artifact_id)
            if artifact_path.exists():
                failures.append(
                    f"artifact exists but inventory still marks it missing: {path_value}"
                )
        elif item_status == "in_progress":
            actual_missing.append(artifact_id)
            if not artifact_path.exists():
                failures.append(f"in-progress artifact does not exist: {path_value}")
        else:
            failures.append(f"{label}.status must be present, in_progress or missing")

    source_artifact = artifacts_by_id.get("P0A-SOURCE", {})
    if source_artifact.get("artifact_version") != CURRENT_BASELINE_ID:
        failures.append("P0A-SOURCE artifact_version must equal the narrative ID")
    if source_artifact.get("producer_task_id") is not None:
        failures.append("P0A-SOURCE must not have a producer task")
    for field in ("path", "byte_count", "sha256"):
        if source_artifact.get(field) != baseline.get(field):
            failures.append(f"P0A-SOURCE.{field} must match planning baseline")
    if source_artifact.get("status") != "present":
        failures.append("P0A-SOURCE must remain present")

    manifest_artifact = artifacts_by_id.get("P0A-MANIFEST", {})
    review_artifact = artifacts_by_id.get("P0A-REVIEW", {})
    if manifest_artifact.get("producer_task_id") != "LAR-P0A-013":
        failures.append("P0A-MANIFEST producer must be LAR-P0A-013")
    if review_artifact.get("producer_task_id") != "LAR-P0A-013":
        failures.append("P0A-REVIEW producer must be LAR-P0A-013")
    if (
        "P0A-MANIFEST" in artifact_ids
        and "P0A-REVIEW" in artifact_ids
        and artifact_ids.index("P0A-MANIFEST") >= artifact_ids.index("P0A-REVIEW")
    ):
        failures.append("P0A-MANIFEST must precede P0A-REVIEW in closure order")

    invariants = inventory.get("invariants")
    if not isinstance(invariants, list) or not all(
        isinstance(item, str) and item for item in invariants
    ):
        failures.append("inventory.invariants must be a non-empty string array")
    else:
        invariant_text = "\n".join(invariants)
        for token in (
            "narrative specification ID",
            "artifact ID",
            "artifact ID, schema version",
            "package_review_head",
            "approval_review_head",
            "final BaselineManifest",
        ):
            if token not in invariant_text:
                failures.append(f"inventory invariants missing version/closure token: {token}")

    declared_missing = inventory.get("missing_artifact_ids")
    if declared_missing != actual_missing:
        failures.append("inventory missing_artifact_ids must exactly match missing artifacts in order")
    if package_state.get("missing_artifact_ids") != actual_missing:
        failures.append("planning normative_package.missing_artifact_ids must match inventory")
    if package_state.get("required_artifact_count") != len(artifacts):
        failures.append("planning required_artifact_count must match inventory")
    if package_state.get("present_artifact_count") != present_count:
        failures.append("planning present_artifact_count must match inventory")

    expected_status = "incomplete" if actual_missing else "complete"
    standalone_verified = False
    if not actual_missing:
        standalone_verified = _verify_standalone_package(
            root=root,
            inventory_path=inventory_path,
            verifier_path=verifier_path,
            baseline_id=baseline.get("id"),
            failures=failures,
        )
    expected_eligible = not actual_missing and standalone_verified
    if inventory.get("package_status") != expected_status:
        failures.append(f"inventory package_status must be {expected_status}")
    if package_state.get("status") != expected_status:
        failures.append(f"planning normative_package.status must be {expected_status}")
    if inventory.get("approval_eligible") is not expected_eligible:
        failures.append(f"inventory approval_eligible must be {expected_eligible}")
    if package_state.get("approval_eligible") is not expected_eligible:
        failures.append(f"planning normative_package.approval_eligible must be {expected_eligible}")
    if actual_missing and inventory.get("approval_record") is not None:
        failures.append("incomplete inventory must not reference an approval record")


def _verify_standalone_package(
    *,
    root: Path,
    inventory_path: Path,
    verifier_path: Path | None,
    baseline_id: Any,
    failures: list[str],
) -> bool:
    if verifier_path is None:
        failures.append("complete package must include the P0A-VERIFIER artifact")
        return False

    command = [
        sys.executable,
        "-I",
        "-s",
        "-E",
        str(verifier_path),
        "--repo-root",
        str(root),
        "--inventory-path",
        str(inventory_path),
        "--json",
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired:
        failures.append("standalone normative package verifier timed out")
        return False
    except OSError as exc:
        failures.append(f"standalone normative package verifier could not start: {exc}")
        return False

    if completed.returncode != 0:
        failures.append(
            "standalone normative package verifier failed with "
            f"exit code {completed.returncode}"
        )
        return False
    try:
        payload = _loads_json_object(
            completed.stdout, "standalone normative package verifier output"
        )
    except ValueError as exc:
        failures.append(str(exc))
        return False
    if payload.get("status") != "pass" or payload.get("baseline_id") != baseline_id:
        failures.append(
            "standalone normative package verifier output must report matching baseline_id and status=pass"
        )
        return False
    return True


def _verify_work_items(
    payload: dict[str, Any],
    baseline: dict[str, Any],
    queue: dict[str, Any],
    current_work: dict[str, Any],
    failures: list[str],
) -> dict[str, dict[str, Any]]:
    _require_fields(
        payload,
        [
            "schema_version",
            "plan_id",
            "baseline_id",
            "supersedes_plan",
            "task_identity",
            "graph_policy",
            "contract_projection_policy",
            "baseline_status",
            "blocking_stage",
            "updated_on",
            "status_catalog",
            "global_constraints",
            "verification_profiles",
            "runtime_source_layout",
            "work_items",
        ],
        "work-item plan",
        failures,
    )
    if payload.get("schema_version") != WORK_ITEM_SCHEMA_VERSION:
        failures.append(
            f"work-item schema_version must be {WORK_ITEM_SCHEMA_VERSION}"
        )
    if payload.get("plan_id") != f"{CURRENT_BASELINE_ID}-implementation-work-items":
        failures.append("work-item plan_id must match the v3.23 implementation graph")
    if payload.get("baseline_id") != baseline.get("id"):
        failures.append("work-item baseline_id must match planning baseline")
    if payload.get("baseline_status") != baseline.get("status"):
        failures.append("work-item baseline_status must match planning baseline")
    if payload.get("blocking_stage") != baseline.get("blocking_stage"):
        failures.append("work-item blocking_stage must match planning baseline")
    if payload.get("supersedes_plan") != EXPECTED_SUPERSEDED_PLAN:
        failures.append("work-item supersedes_plan must match the frozen v3.22 plan identity")
    if payload.get("task_identity") != "plan_id_plus_task_id":
        failures.append("work-item task_identity must be plan_id_plus_task_id")
    if not isinstance(payload.get("updated_on"), str) or not payload["updated_on"].strip():
        failures.append("work-item updated_on must be a non-empty string")
    global_constraints = payload.get("global_constraints")
    if (
        not isinstance(global_constraints, list)
        or not global_constraints
        or not all(
            isinstance(constraint, str) and constraint for constraint in global_constraints
        )
        or len(global_constraints) != len(set(global_constraints))
    ):
        failures.append(
            "work-item global_constraints must be a unique non-empty string array"
        )
    verification_profiles = payload.get("verification_profiles")
    if not isinstance(verification_profiles, dict):
        failures.append("work-item verification_profiles must be an object")
    else:
        if set(verification_profiles) != EXPECTED_VERIFICATION_PROFILES:
            failures.append(
                "work-item verification_profiles must contain exactly planning and new_runtime"
            )
        for profile_name, commands in verification_profiles.items():
            if (
                not isinstance(commands, list)
                or not commands
                or not all(isinstance(command, str) and command for command in commands)
                or len(commands) != len(set(commands))
            ):
                failures.append(
                    "work-item verification profile must be a unique non-empty "
                    f"string array: {profile_name}"
                )
        if verification_profiles.get("new_runtime") != EXPECTED_NEW_RUNTIME_VERIFICATION:
            failures.append(
                "work-item new_runtime verification profile must match the locked offline command set"
            )
    runtime_source_layout = payload.get("runtime_source_layout")
    if not isinstance(runtime_source_layout, dict):
        failures.append("work-item runtime_source_layout must be an object")
    else:
        expected_layout_keys = {
            "source_root",
            "approved_root_files",
            "approved_subpackages",
            "required_source_owners",
        }
        if set(runtime_source_layout) != expected_layout_keys:
            failures.append(
                "work-item runtime_source_layout must contain exactly source_root, "
                "approved_root_files, approved_subpackages and required_source_owners"
            )
        if runtime_source_layout.get("source_root") != RUNTIME_SOURCE_PREFIX:
            failures.append("work-item runtime source_root must match the approved root")
        if runtime_source_layout.get("approved_root_files") != list(
            APPROVED_RUNTIME_SOURCE_ROOT_FILES
        ):
            failures.append(
                "work-item approved_root_files must contain only __init__.py and __main__.py"
            )
        if runtime_source_layout.get("approved_subpackages") != list(
            APPROVED_RUNTIME_SOURCE_PACKAGES
        ):
            failures.append(
                "work-item approved_subpackages must match the frozen nine-package order"
            )
        if (
            runtime_source_layout.get("required_source_owners")
            != EXPECTED_RUNTIME_SOURCE_OWNERS
        ):
            failures.append(
                "work-item required_source_owners must match the bootstrap/initializer ownership map"
            )
    items_value = payload.get("work_items")
    if not isinstance(items_value, list) or not items_value:
        failures.append("work-item plan work_items must be a non-empty array")
        return {}
    if len(items_value) != CURRENT_WORK_ITEM_COUNT:
        failures.append(
            f"work-item graph must contain {CURRENT_WORK_ITEM_COUNT} tasks"
        )
    if queue.get("work_item_count") != len(items_value):
        failures.append("current queue work_item_count must match the machine graph")
    status_catalog = payload.get("status_catalog")
    if (
        not isinstance(status_catalog, list)
        or not all(isinstance(status, str) and status for status in status_catalog)
        or len(status_catalog) != len(set(status_catalog))
    ):
        failures.append("work-item status_catalog must be a unique array")
        status_catalog = []
    elif status_catalog != EXPECTED_WORK_ITEM_STATUSES:
        failures.append("work-item status_catalog must match the v3.23 state set and order")

    required = [
        "task_id",
        "phase",
        "priority",
        "status",
        "title",
        "goal",
        "depends_on",
        "preconditions",
        "scope",
        "acceptance",
        "verification",
        "evidence_path",
        "rollback",
        "stop_conditions",
        "prohibited_actions",
        "next_task_ids",
    ]
    items: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for index, item in enumerate(items_value):
        label = f"work_items[{index}]"
        if not isinstance(item, dict):
            failures.append(f"{label} must be an object")
            continue
        _require_fields(item, required, label, failures)
        task_id = item.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            failures.append(f"{label}.task_id must be non-empty")
            continue
        if task_id in items:
            failures.append(f"duplicate work-item task_id: {task_id}")
            continue
        items[task_id] = item
        order.append(task_id)
        phase = item.get("phase")
        task_id_parts = task_id.split("-")
        if task_id in {"LAR-P0A-REBASELINE-V322", "LAR-P0A-REBASELINE-V323"}:
            expected_phase = "P0A"
        elif task_id in {"LAR-P0A-EVAL-001", "LAR-P0A-EVAL-002"}:
            expected_phase = "EVAL"
        elif (
            len(task_id_parts) != 3
            or task_id_parts[0] != "LAR"
            or not task_id_parts[1]
            or len(task_id_parts[2]) != 3
            or not task_id_parts[2].isdigit()
        ):
            failures.append(f"invalid work-item task_id format: {task_id}")
            expected_phase = None
        else:
            expected_phase = (
                "Governance" if task_id_parts[1] == "GOV" else task_id_parts[1]
            )
        if not isinstance(phase, str) or not phase:
            failures.append(f"{task_id}.phase must be a non-empty string")
        elif expected_phase is not None and phase != expected_phase:
            failures.append(
                f"{task_id}.phase must match its task ID: expected {expected_phase}"
            )
        priority = item.get("priority")
        if (
            not isinstance(priority, int)
            or isinstance(priority, bool)
            or priority < 0
        ):
            failures.append(f"{task_id}.priority must be a non-negative integer")
        for string_field in ("title", "goal", "evidence_path", "rollback"):
            value = item.get(string_field)
            if not isinstance(value, str) or not value.strip():
                failures.append(f"{task_id}.{string_field} must be a non-empty string")
        if item.get("status") not in status_catalog:
            failures.append(f"{task_id} has unknown status {item.get('status')!r}")
        for array_field in (
            "depends_on",
            "preconditions",
            "acceptance",
            "verification",
            "stop_conditions",
            "prohibited_actions",
            "next_task_ids",
        ):
            value = item.get(array_field)
            if not isinstance(value, list):
                failures.append(f"{task_id}.{array_field} must be an array")
            elif any(not isinstance(entry, str) or not entry for entry in value):
                failures.append(
                    f"{task_id}.{array_field} must contain non-empty strings"
                )
            elif len(value) != len(set(value)):
                failures.append(f"{task_id}.{array_field} must not contain duplicates")
            elif array_field not in {"depends_on", "next_task_ids"} and not value:
                failures.append(f"{task_id}.{array_field} must not be empty")
        scope = item.get("scope")
        if not isinstance(scope, dict):
            failures.append(f"{task_id}.scope must be an object")
        else:
            _require_fields(scope, ["in", "out", "primary_files"], f"{task_id}.scope", failures)
            for scope_field in ("in", "out", "primary_files"):
                value = scope.get(scope_field)
                if not isinstance(value, list) or not value:
                    failures.append(f"{task_id}.scope.{scope_field} must be a non-empty array")
                elif any(not isinstance(entry, str) or not entry for entry in value):
                    failures.append(
                        f"{task_id}.scope.{scope_field} must contain non-empty strings"
                    )
                elif len(value) != len(set(value)):
                    failures.append(
                        f"{task_id}.scope.{scope_field} must not contain duplicates"
                    )

    position = {task_id: index for index, task_id in enumerate(order)}
    runtime_source_path_owners: dict[str, list[str]] = {}
    for task_id, item in items.items():
        dependencies = _work_item_list(item, "depends_on")
        for dependency in dependencies:
            if not isinstance(dependency, str):
                continue
            if dependency not in items:
                failures.append(f"{task_id} depends on unknown task {dependency}")
            elif dependency == task_id:
                failures.append(f"{task_id} cannot depend on itself")
            elif position[dependency] >= position[task_id]:
                failures.append(f"{task_id} dependency {dependency} must precede it")
        for successor in _work_item_list(item, "next_task_ids"):
            if not isinstance(successor, str):
                continue
            if successor not in items:
                failures.append(f"{task_id} references unknown successor {successor}")
            elif task_id not in _work_item_list(items[successor], "depends_on"):
                failures.append(f"{task_id} successor {successor} must depend on it")
        for dependency in dependencies:
            if not isinstance(dependency, str) or dependency not in items:
                continue
            if task_id not in _work_item_list(items[dependency], "next_task_ids"):
                failures.append(
                    f"{task_id} dependency {dependency} must list it as successor"
                )

    _verify_acyclic_dependencies(items, failures)
    _verify_graph_policy(payload.get("graph_policy"), items, current_work, failures)
    _verify_contract_projection_policy(
        payload.get("contract_projection_policy"), items, failures
    )
    actual_p1_ids = {
        task_id
        for task_id in items
        if task_id.startswith(("LAR-P1A-", "LAR-P1B-", "LAR-P1C-", "LAR-P1D-", "LAR-P1E-", "LAR-P1F-"))
    }
    if actual_p1_ids != EXPECTED_P1_IMPLEMENTATION_TASK_IDS:
        missing = sorted(EXPECTED_P1_IMPLEMENTATION_TASK_IDS - actual_p1_ids)
        unexpected = sorted(actual_p1_ids - EXPECTED_P1_IMPLEMENTATION_TASK_IDS)
        failures.append(
            f"P1 implementation task IDs mismatch: missing={missing}, unexpected={unexpected}"
        )

    required_task_tokens = {
        "LAR-P0A-002": [
            "No final BaselineManifest.v1.json exists",
            "P0A-MANIFEST remains missing",
        ],
        "LAR-P0A-003": [
            "policy_query_denied",
            "does not require globally disabling short-name creation",
        ],
        "LAR-P0A-004": [
            "volatile existing-family lookup",
            "Existing-family replay remains stable",
            "secret scan",
        ],
        "LAR-P0A-005": [
            "AuthorizationExecutionGrant",
            "sandbox.log is an opaque bounded diagnostic",
            "basis_kind=active_authorization",
        ],
        "LAR-P0A-006": [
            "SafetyOnlyExecutionRecord",
            "execution_authority_kind",
            "release_emergency_reserve",
            "rebuild_emergency_reserve",
        ],
        "LAR-P0A-010": [
            "accounting_kill_audit",
            "EmergencyDiskReserve",
            "HardWriteQuotaCapability is optional",
        ],
        "LAR-P0A-013": [
            "package_review_head",
            "approval_review_head",
            "BaselineManifest.v1.json",
        ],
        "LAR-P0D-001": [
            "pinned Python 3.11",
            "contracts/kernel/qualification/storage/execution/recovery/"
            "git_local/operations/compat modules",
            "approved_root_files",
            "approved_subpackages",
        ],
    }
    for task_id, tokens in required_task_tokens.items():
        item = items.get(task_id)
        if item is None:
            failures.append(f"missing required semantic work item: {task_id}")
            continue
        rendered = json.dumps(item, ensure_ascii=False, sort_keys=True)
        for token in tokens:
            if token not in rendered:
                failures.append(f"{task_id} missing required semantic token: {token}")

    manifest_schema_task = items.get("LAR-P0A-002", {})
    manifest_close_task = items.get("LAR-P0A-013", {})
    final_manifest_path = (
        "docs/specs/local-ai-runtime-0.2/normative/BaselineManifest.v1.json"
    )
    if final_manifest_path in _work_item_scope_list(
        manifest_schema_task, "primary_files"
    ):
        failures.append("LAR-P0A-002 must not create the final BaselineManifest instance")
    if final_manifest_path not in _work_item_scope_list(
        manifest_close_task, "primary_files"
    ):
        failures.append("LAR-P0A-013 must create the final BaselineManifest instance")

    p4_cohort = items.get("LAR-P4-001", {})
    b3_activation = items.get("LAR-P4-002", {})
    p5_cutover = items.get("LAR-P5-001", {})
    if _work_item_list(b3_activation, "depends_on") != ["LAR-P4-001"]:
        failures.append("B3 activation must depend only on the green P4 cohort")
    if _work_item_list(p5_cutover, "depends_on") != ["LAR-P4-001"]:
        failures.append("P5 must depend on the green P4 cohort, not B3 activation")
    if _work_item_list(p4_cohort, "next_task_ids") != [
        "LAR-P4-002",
        "LAR-P5-001",
    ]:
        failures.append("P4 must independently release B3 activation and P5 cutover")

    for task_id in EXPECTED_P1_IMPLEMENTATION_TASK_IDS:
        item = items.get(task_id)
        if item is None:
            continue
        primary_files = _work_item_scope_list(item, "primary_files")
        if any(not isinstance(path, str) or path.endswith(("/", "\\")) for path in primary_files):
            failures.append(f"{task_id} must name concrete primary files")
        verification_text = "\n".join(
            entry
            for entry in _work_item_list(item, "verification")
            if isinstance(entry, str)
        )
        if "python -m pytest tests/" in verification_text:
            failures.append(f"{task_id} pytest paths must be repo-root relative")

    for task_id, item in items.items():
        verification_text = "\n".join(
            entry
            for entry in _work_item_list(item, "verification")
            if isinstance(entry, str)
        )
        if "git diff --check" not in verification_text:
            failures.append(f"{task_id} must include git diff --check")
        primary_files = _work_item_scope_list(item, "primary_files")
        for path in primary_files:
            if not isinstance(path, str) or not path.startswith(RUNTIME_SOURCE_PREFIX):
                continue
            relative_path = path.removeprefix(RUNTIME_SOURCE_PREFIX)
            runtime_source_path_owners.setdefault(relative_path, []).append(task_id)
            if "/" not in relative_path:
                if relative_path not in APPROVED_RUNTIME_SOURCE_ROOT_FILES:
                    failures.append(
                        f"{task_id} uses unapproved runtime source root file: "
                        f"{relative_path}"
                    )
                continue
            source_package = relative_path.split("/", 1)[0]
            if source_package not in APPROVED_RUNTIME_SOURCE_PACKAGES:
                failures.append(
                    f"{task_id} uses unapproved runtime source package: {source_package}"
                )

    for relative_path, owners in runtime_source_path_owners.items():
        if len(owners) != 1:
            failures.append(
                "runtime source path must have exactly one owner: "
                f"{relative_path}: {owners}"
            )
    for relative_path, expected_owner in EXPECTED_RUNTIME_SOURCE_OWNERS.items():
        actual_owners = runtime_source_path_owners.get(relative_path, [])
        if actual_owners != [expected_owner]:
            failures.append(
                "runtime required source owner mismatch: "
                f"{relative_path}: expected={expected_owner}, actual={actual_owners}"
            )

    selectable_statuses = {
        "contract_pending",
        "execution_pending",
        "narrow_profile_or_adapter_candidate",
        "supersede_required",
        "ready",
    }
    selectable = [
        task_id
        for task_id, item in items.items()
        if item.get("status") in selectable_statuses
        and all(
            items.get(dependency, {}).get("status") == "completed"
            for dependency in _work_item_list(item, "depends_on")
            if isinstance(dependency, str)
        )
    ]
    current_id = current_work.get("task_id")
    if selectable != [current_id]:
        failures.append(
            "exactly the current work item must be selectable: "
            f"current={current_id!r}, selectable={selectable!r}"
        )
    current_item = items.get(str(current_id))
    if current_item is None:
        failures.append(f"current work item does not exist in work-item plan: {current_id!r}")
    else:
        if current_item.get("status") != current_work.get("status"):
            failures.append("current_work_item.status must match machine work-item status")
        for dependency in _work_item_list(current_item, "depends_on"):
            if not isinstance(dependency, str):
                continue
            if items.get(dependency, {}).get("status") != "completed":
                failures.append(
                    f"selectable current work item has incomplete dependency: {dependency}"
                )
    return items


def _work_item_reaches(
    work_items: dict[str, dict[str, Any]], source: Any, target: Any
) -> bool:
    if not isinstance(source, str) or not isinstance(target, str):
        return False
    pending = [source]
    visited: set[str] = set()
    while pending:
        task_id = pending.pop()
        if task_id == target:
            return True
        if task_id in visited:
            continue
        visited.add(task_id)
        item = work_items.get(task_id, {})
        pending.extend(
            successor
            for successor in _work_item_list(item, "next_task_ids")
            if isinstance(successor, str)
        )
    return False


def _verify_inventory_task_links(
    inventory: dict[str, Any],
    work_items: dict[str, dict[str, Any]],
    current_work: dict[str, Any],
    failures: list[str],
) -> None:
    artifacts_value = inventory.get("required_artifacts", [])
    if not isinstance(artifacts_value, list):
        failures.append("inventory.required_artifacts must be an array")
        return
    artifacts = [item for item in artifacts_value if isinstance(item, dict)]
    if len(artifacts) != len(artifacts_value):
        failures.append("inventory.required_artifacts entries must be objects")
    missing = [item for item in artifacts if item.get("status") == "missing"]
    for item in artifacts:
        producer = item.get("producer_task_id")
        if producer is not None and producer not in work_items:
            failures.append(
                f"inventory artifact {item.get('artifact_id')} references unknown producer {producer}"
            )
    if missing:
        first_producer = missing[0].get("producer_task_id")
        current_id = current_work.get("task_id")
        if current_id != first_producer and not _work_item_reaches(
            work_items, current_id, first_producer
        ):
            failures.append(
                "current work item must produce or lead to the first missing normative artifact: "
                f"expected {first_producer}, got {current_work.get('task_id')}"
            )


def _verify_manifest_contract_slice(
    root: Path,
    work_items: dict[str, dict[str, Any]],
    inventory: dict[str, Any],
    failures: list[str],
) -> None:
    task = work_items.get("LAR-P0A-002", {})
    if task.get("status") != "completed":
        return

    for relative_path, label in (
        (BASELINE_MANIFEST_SCHEMA_PATH, "BaselineManifest.v1 schema"),
        (BASELINE_MANIFEST_FIXTURE_PATH, "BaselineManifest.v1 fixture manifest"),
        (BASELINE_VERIFIER_SKELETON_PATH, "baseline verifier skeleton"),
    ):
        path = root / relative_path
        if not path.is_file():
            failures.append(f"completed LAR-P0A-002 is missing {label}: {relative_path}")
            return
        try:
            raw = path.read_bytes()
        except OSError as exc:
            failures.append(f"completed LAR-P0A-002 cannot read {label}: {exc}")
            return
        _verify_normative_bytes(raw, label, failures)

    verifier_entry = next(
        (
            item
            for item in inventory.get("required_artifacts", [])
            if isinstance(item, dict) and item.get("artifact_id") == "P0A-VERIFIER"
        ),
        None,
    )
    verifier_freeze_complete = (
        work_items.get("LAR-P0A-012", {}).get("status") == "completed"
    )
    expected_verifier_status = "present" if verifier_freeze_complete else "in_progress"
    if (
        not isinstance(verifier_entry, dict)
        or verifier_entry.get("status") != expected_verifier_status
    ):
        failures.append(
            "P0A-VERIFIER status must follow verifier freeze state: "
            f"expected {expected_verifier_status}"
        )
    manifest_close_started = work_items.get("LAR-P0A-013", {}).get("status") in {
        "in_progress",
        "completed",
    }
    if not manifest_close_started and (root / FINAL_BASELINE_MANIFEST_PATH).exists():
        failures.append("LAR-P0A-002 must not create the final BaselineManifest instance")

    command = [
        sys.executable,
        str(root / BASELINE_VERIFIER_SKELETON_PATH),
        "--component",
        "manifest",
        "--self-test",
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired:
        failures.append("BaselineManifest verifier self-test timed out")
        return
    try:
        payload = _loads_json_object(completed.stdout, "manifest verifier self-test")
    except ValueError as exc:
        failures.append(str(exc))
        return
    if completed.returncode != 0 or payload.get("status") != "pass":
        failures.append(
            "BaselineManifest verifier self-test must return exit 0 and status=pass"
        )
    if payload.get("final_manifest_exists") is not False:
        failures.append("BaselineManifest verifier self-test must prove final manifest absence")


def _verify_selector_policy(
    root: Path,
    policy: dict[str, Any],
    package_state: dict[str, Any],
    current_work: dict[str, Any],
    failures: list[str],
) -> None:
    _require_fields(
        policy,
        [
            "schema_version",
            "policy_id",
            "reviewed_on",
            "review_expires_at",
            "baseline_review_missing_artifact_sets",
            "allowed_next_actions",
            "selection_order",
            "required_entrypoints",
            "required_doc_refs",
            "selector_invariants",
            "rollback_ref",
        ],
        "selector policy",
        failures,
    )
    allowed = policy.get("allowed_next_actions")
    if (
        not isinstance(allowed, list)
        or not all(isinstance(action, str) and action for action in allowed)
        or len(allowed) != len(set(allowed))
    ):
        failures.append("selector allowed_next_actions must be a unique array")
        allowed = []
    if allowed != EXPECTED_SELECTOR_ACTIONS:
        failures.append("selector allowed_next_actions must match the v3.23 action catalog")
    if current_work.get("selector_action") not in allowed:
        failures.append("current selector action is not allowed by selector policy")
    completed_history_actions = {
        "archive_lineage_sources_first",
        "draft_v3_22_candidate_first",
    }
    forbidden_history_actions = sorted(completed_history_actions.intersection(allowed))
    if forbidden_history_actions:
        failures.append(
            "selector must not allow a completed historical selector action: "
            f"{forbidden_history_actions}"
        )
    if current_work.get("selector_action") in completed_history_actions:
        failures.append("current work item cannot select a completed historical action")

    review_sets = policy.get("baseline_review_missing_artifact_sets")
    if review_sets != EXPECTED_REVIEW_MISSING_ARTIFACT_SETS:
        failures.append(
            "selector baseline_review_missing_artifact_sets must match the v3.23 manifest/review closure"
        )
    missing = package_state.get("missing_artifact_ids")
    review_phase = (
        current_work.get("task_id") == "LAR-P0A-013"
        and isinstance(missing, list)
        and missing in EXPECTED_REVIEW_MISSING_ARTIFACT_SETS
    )
    if current_work.get("selector_action") == "run_baseline_consistency_review" and not review_phase:
        failures.append(
            "run_baseline_consistency_review requires LAR-P0A-013 and an exact review missing-artifact set"
        )
    if review_phase and current_work.get("selector_action") != "run_baseline_consistency_review":
        failures.append(
            "LAR-P0A-013 review closure must select run_baseline_consistency_review"
        )

    selection = policy.get("selection_order")
    if not isinstance(selection, list) or not selection:
        failures.append("selector selection_order must be non-empty")
    else:
        priorities: list[int] = []
        condition_ids: set[str] = set()
        for index, item in enumerate(selection):
            if not isinstance(item, dict):
                failures.append(f"selection_order[{index}] must be an object")
                continue
            _require_fields(
                item,
                ["priority", "condition_id", "next_action", "why"],
                f"selection_order[{index}]",
                failures,
            )
            priority = item.get("priority")
            if isinstance(priority, int) and not isinstance(priority, bool):
                priorities.append(priority)
            else:
                failures.append(f"selection_order[{index}].priority must be an integer")
            condition_id = item.get("condition_id")
            if condition_id in condition_ids:
                failures.append(f"duplicate selector condition_id: {condition_id}")
            condition_ids.add(condition_id)
            if item.get("next_action") not in allowed:
                failures.append(
                    f"selector action {item.get('next_action')!r} is not in allowed_next_actions"
                )
        if priorities != sorted(priorities) or len(priorities) != len(set(priorities)):
            failures.append("selector priorities must be unique and ascending")
        actual_steps = [
            (item.get("condition_id"), item.get("next_action"))
            for item in selection
            if isinstance(item, dict)
        ]
        if actual_steps != EXPECTED_SELECTOR_STEPS:
            failures.append(
                "selector condition/action order must match the v3.23 stage graph"
            )

    required_entrypoints = policy.get("required_entrypoints")
    if required_entrypoints != EXPECTED_SELECTOR_ENTRYPOINTS:
        failures.append("selector required_entrypoints must match the exact control-plane set")
        required_entrypoints = (
            required_entrypoints if isinstance(required_entrypoints, list) else []
        )
    for relative in required_entrypoints:
        try:
            path = _resolve_repo_path(root, relative, "selector required entrypoint")
        except ValueError as exc:
            failures.append(str(exc))
            continue
        if not path.exists():
            failures.append(f"missing selector entrypoint: {relative}")
    for ref in policy.get("required_doc_refs", []):
        if not isinstance(ref, dict) or not isinstance(ref.get("contains"), str):
            failures.append("selector required_doc_refs entries must contain path and contains")
            continue
        try:
            path = _resolve_repo_path(root, ref.get("path"), "selector doc ref")
            text = path.read_text(encoding="utf-8")
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            failures.append(f"selector doc ref is unreadable: {exc}")
            continue
        if ref["contains"] not in text:
            failures.append(f"selector doc ref missing text: {ref['path']}:{ref['contains']}")


def _verify_approval_and_stages(
    *,
    root: Path,
    approval: dict[str, Any],
    package_state: dict[str, Any],
    queue: dict[str, Any],
    current_work: dict[str, Any],
    evaluation: dict[str, Any],
    legacy: dict[str, Any],
    truth_reset: dict[str, Any],
    implementation: dict[str, Any],
    p2: dict[str, Any],
    rollout: dict[str, Any],
    failures: list[str],
) -> None:
    for label, value in (
        ("approval_state.active", approval.get("active")),
        ("normative_package.approval_eligible", package_state.get("approval_eligible")),
        ("legacy_runtime_posture.new_package_exists", legacy.get("new_package_exists")),
        ("legacy_runtime_posture.legacy_guard_complete", legacy.get("legacy_guard_complete")),
        ("legacy_runtime_posture.new_batch_claims_allowed", legacy.get("new_batch_claims_allowed")),
        ("truth_reset.performed", truth_reset.get("performed")),
        ("truth_reset.permitted", truth_reset.get("permitted")),
        ("implementation.started", implementation.get("started")),
        ("implementation.package_created", implementation.get("package_created")),
        ("implementation.code_complete", implementation.get("code_complete")),
        (
            "implementation.implementation_acceptance_active",
            implementation.get("implementation_acceptance_active"),
        ),
        ("implementation.full_q0_passed", implementation.get("full_q0_passed")),
        ("p2_admission.admitted", p2.get("admitted")),
        ("rollout.p2_pilot_complete", rollout.get("p2_pilot_complete")),
        (
            "rollout.p3_scheduled_self_host_complete",
            rollout.get("p3_scheduled_self_host_complete"),
        ),
        ("rollout.p4_cohort_complete", rollout.get("p4_cohort_complete")),
        (
            "rollout.b3_portfolio_generation_active",
            rollout.get("b3_portfolio_generation_active"),
        ),
        ("rollout.p5_cutover_complete", rollout.get("p5_cutover_complete")),
        ("rollout.legacy_writer_retired", rollout.get("legacy_writer_retired")),
    ):
        if not isinstance(value, bool):
            failures.append(f"{label} must be boolean")

    if approval.get("active") and not package_state.get("approval_eligible"):
        failures.append("active baseline approval requires an approval-eligible package")
    if approval.get("active"):
        record = approval.get("approval_record")
        try:
            record_path = _resolve_repo_path(root, record, "BaselineApprovalRecord")
        except ValueError as exc:
            failures.append(str(exc))
        else:
            if not record_path.is_file():
                failures.append("active BaselineApprovalRecord does not exist")
        if not isinstance(approval.get("generation"), int) or approval.get("generation", 0) < 1:
            failures.append("active baseline approval requires generation >= 1")
        if approval.get("revocation_record") is not None:
            failures.append("active baseline approval cannot also have an active revocation record")
    elif approval.get("generation") == 0:
        if approval.get("approval_record") is not None or approval.get("revocation_record") is not None:
            failures.append("approval generation 0 must not reference approval/revocation records")

    if truth_reset.get("performed") and not approval.get("active"):
        failures.append("Truth Reset cannot be performed without active Baseline Approval")
    if truth_reset.get("permitted") != approval.get("active"):
        failures.append("truth_reset.permitted must equal active Baseline Approval")
    if implementation.get("started") and not truth_reset.get("performed"):
        failures.append("implementation cannot start before Truth Reset")
    if implementation.get("started") and not legacy.get("legacy_guard_complete"):
        failures.append("implementation cannot start before Legacy Ownership Guard")
    if implementation.get("package_created") != implementation.get("started"):
        failures.append("implementation.package_created must match implementation.started")
    if implementation.get("code_complete") and not implementation.get("started"):
        failures.append("implementation.code_complete requires implementation.started")
    if implementation.get("implementation_acceptance_active") and not implementation.get("code_complete"):
        failures.append("Implementation Acceptance requires code_complete")
    if implementation.get("full_q0_passed") and not implementation.get(
        "implementation_acceptance_active"
    ):
        failures.append("Full Q0 requires active Implementation Acceptance")
    if p2.get("admitted") and not implementation.get("full_q0_passed"):
        failures.append("P2 admission requires Full Q0")
    if implementation.get("full_q0_passed") and not p2.get("admitted"):
        failures.append("Full Q0 and P2 Admission must be activated as the same gate")
    if rollout.get("p2_pilot_complete") and not p2.get("admitted"):
        failures.append("P2 pilot completion requires P2 Admission")
    if rollout.get("p3_scheduled_self_host_complete") and not rollout.get(
        "p2_pilot_complete"
    ):
        failures.append("P3 completion requires the P2 pilot")
    if rollout.get("p4_cohort_complete") and not rollout.get(
        "p3_scheduled_self_host_complete"
    ):
        failures.append("P4 completion requires P3 scheduled self-host evidence")
    if rollout.get("b3_portfolio_generation_active") and not rollout.get(
        "p4_cohort_complete"
    ):
        failures.append("B3 portfolio activation requires the green P4 cohort")
    if rollout.get("p5_cutover_complete") and not rollout.get("p4_cohort_complete"):
        failures.append("P5 completion requires the P4 cohort")
    if rollout.get("legacy_writer_retired") and not rollout.get("p5_cutover_complete"):
        failures.append("legacy writer retirement requires completed P5 cutover")
    if legacy.get("new_batch_claims_allowed") and not legacy.get("legacy_guard_complete"):
        failures.append("new Batch claims require Legacy Ownership Guard")

    new_package_value = legacy.get("new_package_path")
    try:
        new_package_path = _resolve_repo_path(root, new_package_value, "new package path")
    except ValueError as exc:
        failures.append(str(exc))
    else:
        if new_package_path.exists() != legacy.get("new_package_exists"):
            failures.append("declared new_package_exists does not match filesystem")
    try:
        current_kernel = _resolve_repo_path(root, legacy.get("current_kernel"), "current kernel")
    except ValueError as exc:
        failures.append(str(exc))
    else:
        if not current_kernel.is_dir():
            failures.append("declared current kernel directory does not exist")

    _verify_native_thin_path_evaluation(
        root=root,
        evaluation=evaluation,
        package_state=package_state,
        current_work=current_work,
        failures=failures,
    )

    if package_state.get("status") == "incomplete":
        if queue.get("queue_id") != "LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE":
            failures.append("incomplete package requires baseline-closure queue")
        if current_work.get("selector_action") not in {
            "create_successor_candidate_first",
            "run_native_thin_path_evaluation_first",
            "close_baseline_normative_package_first",
            "run_baseline_consistency_review",
        }:
            failures.append("incomplete package requires a normative-closure selector action")


def _verify_native_thin_path_evaluation(
    *,
    root: Path,
    evaluation: dict[str, Any],
    package_state: dict[str, Any],
    current_work: dict[str, Any],
    failures: list[str],
) -> None:
    _require_fields(
        evaluation,
        [
            "status",
            "decision",
            "contract_task_id",
            "execution_task_id",
            "contract_output_refs",
            "contract_identity",
            "result_ref",
            "decision_ref",
            "evidence_ref",
            "comparison_variants",
            "independent_capability_surfaces",
            "required_metrics",
            "hard_promotion_rules",
            "successor_baseline_id",
        ],
        "native_thin_path_evaluation",
        failures,
    )
    status = evaluation.get("status")
    decision = evaluation.get("decision")
    expected_contract_task = "LAR-P0A-EVAL-001"
    expected_execution_task = "LAR-P0A-EVAL-002"
    if evaluation.get("contract_task_id") != expected_contract_task:
        failures.append(
            "native_thin_path_evaluation.contract_task_id must be LAR-P0A-EVAL-001"
        )
    if evaluation.get("execution_task_id") != expected_execution_task:
        failures.append(
            "native_thin_path_evaluation.execution_task_id must be LAR-P0A-EVAL-002"
        )
    if evaluation.get("successor_baseline_id") != "local-ai-runtime-0.2-v3.24":
        failures.append(
            "native_thin_path_evaluation.successor_baseline_id must be local-ai-runtime-0.2-v3.24"
        )

    for field, expected in (
        ("comparison_variants", NATIVE_THIN_PATH_EVALUATION_VARIANTS),
        ("independent_capability_surfaces", NATIVE_THIN_PATH_EVALUATION_SURFACES),
        ("required_metrics", NATIVE_THIN_PATH_EVALUATION_METRICS),
        ("hard_promotion_rules", NATIVE_THIN_PATH_EVALUATION_HARD_RULES),
    ):
        if evaluation.get(field) != expected:
            failures.append(
                f"native_thin_path_evaluation.{field} must match the frozen v3.23 evaluation contract"
            )

    refs = evaluation.get("contract_output_refs")
    if (
        not isinstance(refs, list)
        or len(refs) != 3
        or not all(isinstance(reference, str) and reference for reference in refs)
        or len(refs) != len(set(refs))
    ):
        failures.append(
            "native_thin_path_evaluation.contract_output_refs must be three unique non-empty paths"
        )
    elif any(not reference.startswith("docs/evaluations/local-ai-runtime-0.2/") for reference in refs):
        failures.append(
            "native_thin_path_evaluation.contract_output_refs must remain under the evaluation evidence root"
        )

    terminal_decisions = set(NATIVE_THIN_PATH_EVALUATION_DECISIONS)
    state_rules = {
        "contract_pending": {
            "current_task": expected_contract_task,
            "allowed_decisions": {None},
            "sealed_refs": False,
        },
        "execution_pending": {
            "current_task": expected_execution_task,
            "allowed_decisions": {None},
            "sealed_refs": False,
        },
        "preserve_v3_23_semantics": {
            "current_task": None,
            "allowed_decisions": {"preserve_v3_23_semantics"},
            "sealed_refs": True,
        },
        "narrow_profile_or_adapter_candidate": {
            "current_task": expected_execution_task,
            "allowed_decisions": {"narrow_profile_or_adapter_candidate"},
            "sealed_refs": True,
        },
        "supersede_required": {
            "current_task": expected_execution_task,
            "allowed_decisions": {"supersede_required"},
            "sealed_refs": True,
        },
    }
    rule = state_rules.get(status)
    if rule is None:
        failures.append(
            "native_thin_path_evaluation.status must be contract_pending, execution_pending or a terminal decision state"
        )
        return
    if decision not in rule["allowed_decisions"]:
        failures.append(
            "native_thin_path_evaluation.decision must match its lifecycle status"
        )
    current_task = current_work.get("task_id")
    expected_current = rule["current_task"]
    if expected_current is not None and current_task != expected_current:
        failures.append(
            "native_thin_path_evaluation pending status must select its matching evaluation work item"
        )
    if expected_current is None and current_task in {
        expected_contract_task,
        expected_execution_task,
    }:
        failures.append(
            "terminal native_thin_path_evaluation cannot keep an evaluation work item selected"
        )

    contract_identity = evaluation.get("contract_identity")
    identity_required = status != "contract_pending"
    if not identity_required:
        if contract_identity is not None:
            failures.append(
                "contract_pending native_thin_path_evaluation.contract_identity must remain null"
            )
    elif not isinstance(contract_identity, dict):
        failures.append(
            "execution or terminal native_thin_path_evaluation requires contract_identity"
        )
    else:
        _verify_native_thin_path_evaluation_contract_identity(
            root=root,
            identity=contract_identity,
            evaluation=evaluation,
            failures=failures,
        )

    sealed_refs = rule["sealed_refs"]
    for field in ("result_ref", "decision_ref", "evidence_ref"):
        value = evaluation.get(field)
        if sealed_refs:
            if not isinstance(value, str) or not value.startswith(
                "docs/evaluations/local-ai-runtime-0.2/"
            ):
                failures.append(
                    f"terminal native_thin_path_evaluation requires an evaluation-root {field}"
                )
        elif value is not None:
            failures.append(
                f"pending native_thin_path_evaluation.{field} must remain null"
            )

    if sealed_refs:
        _verify_terminal_native_thin_path_evaluation_artifacts(
            root=root,
            evaluation=evaluation,
            contract_identity=contract_identity,
            status=status,
            decision=decision,
            failures=failures,
        )

    if decision in terminal_decisions and status != decision:
        failures.append(
            "native_thin_path_evaluation terminal decision must equal its terminal status"
        )
    if decision == "preserve_v3_23_semantics":
        if package_state.get("status") == "incomplete" and current_task == expected_execution_task:
            failures.append(
                "preserve_v3_23_semantics must release the evaluation task before normative closure continues"
            )
    elif decision in {
        "narrow_profile_or_adapter_candidate",
        "supersede_required",
    }:
        if package_state.get("approval_eligible"):
            failures.append(
                "a semantic-change evaluation decision must keep v3.23 approval-ineligible"
            )
        if current_work.get("selector_action") != "create_successor_candidate_first":
            failures.append(
                "a semantic-change evaluation decision must select create_successor_candidate_first"
            )


def _verify_native_thin_path_evaluation_contract_identity(
    *,
    root: Path,
    identity: dict[str, Any],
    evaluation: dict[str, Any],
    failures: list[str],
) -> None:
    """Fail closed unless the pending/terminal state binds exact sealed contract bytes."""

    _require_fields(
        identity,
        [
            "contract_set_id",
            "baseline_id",
            "contract_task_id",
            "execution_task_id",
            "snapshot",
            "contracts",
        ],
        "native_thin_path_evaluation.contract_identity",
        failures,
    )
    if identity.get("contract_set_id") != NATIVE_THIN_PATH_EVALUATION_CONTRACT_SET_ID:
        failures.append(
            "native_thin_path_evaluation.contract_identity must bind the v3.23 evaluation contract set"
        )
    for field, expected in (
        ("baseline_id", CURRENT_BASELINE_ID),
        ("contract_task_id", "LAR-P0A-EVAL-001"),
        ("execution_task_id", "LAR-P0A-EVAL-002"),
    ):
        if identity.get(field) != expected:
            failures.append(
                "native_thin_path_evaluation.contract_identity."
                f"{field} must match the frozen evaluation contract"
            )
    if identity.get("snapshot") != NATIVE_THIN_PATH_EVALUATION_SNAPSHOT:
        failures.append(
            "native_thin_path_evaluation.contract_identity.snapshot must match the frozen evaluation snapshot"
        )

    contracts = identity.get("contracts")
    if not isinstance(contracts, list) or len(contracts) != len(
        NATIVE_THIN_PATH_EVALUATION_CONTRACTS
    ):
        failures.append(
            "native_thin_path_evaluation.contract_identity.contracts must contain every sealed contract"
        )
        return

    expected_paths = [path for path, _ in NATIVE_THIN_PATH_EVALUATION_CONTRACTS]
    actual_paths = [entry.get("path") for entry in contracts if isinstance(entry, dict)]
    if actual_paths != expected_paths:
        failures.append(
            "native_thin_path_evaluation.contract_identity.contracts must use the frozen contract path order"
        )
        return
    if evaluation.get("contract_output_refs") != expected_paths:
        failures.append(
            "native_thin_path_evaluation.contract_output_refs must match the sealed contract path order"
        )

    expected_by_path = dict(NATIVE_THIN_PATH_EVALUATION_CONTRACTS)
    loaded_contracts: dict[str, tuple[dict[str, Any], bytes]] = {}
    for entry in contracts:
        if not isinstance(entry, dict):
            failures.append(
                "native_thin_path_evaluation.contract_identity.contracts entries must be objects"
            )
            continue
        _require_fields(
            entry,
            ["path", "byte_count", "sha256"],
            "native_thin_path_evaluation.contract_identity.contracts entry",
            failures,
        )
        path_value = entry.get("path")
        if path_value not in expected_by_path:
            continue
        if (
            not isinstance(entry.get("byte_count"), int)
            or isinstance(entry.get("byte_count"), bool)
            or entry["byte_count"] < 1
        ):
            failures.append(
                "native_thin_path_evaluation.contract_identity contract byte_count must be a positive integer"
            )
        if not _is_sha256(entry.get("sha256")):
            failures.append(
                "native_thin_path_evaluation.contract_identity contract sha256 must be lowercase SHA-256"
            )
        try:
            path = _resolve_repo_path(root, path_value, "evaluation contract")
        except ValueError as exc:
            failures.append(str(exc))
            continue
        if not path.is_file():
            failures.append(
                f"native_thin_path_evaluation sealed contract does not exist: {path_value}"
            )
            continue
        try:
            payload, raw = _load_json_with_bytes(path)
        except ValueError as exc:
            failures.append(
                f"native_thin_path_evaluation sealed contract must be a readable JSON object: {path_value}: {exc}"
            )
            continue
        loaded_contracts[path_value] = (payload, raw)
        if entry.get("byte_count") != len(raw):
            failures.append(
                "native_thin_path_evaluation.contract_identity contract byte_count must match file bytes"
            )
        if entry.get("sha256") != hashlib.sha256(raw).hexdigest():
            failures.append(
                "native_thin_path_evaluation.contract_identity contract sha256 must match file bytes"
            )
        expected_schema = expected_by_path[path_value]
        if payload.get("schema_version") != expected_schema:
            failures.append(
                f"native_thin_path_evaluation sealed contract has unexpected schema_version: {path_value}"
            )
        for field, expected in (
            ("contract_set_id", NATIVE_THIN_PATH_EVALUATION_CONTRACT_SET_ID),
            ("baseline_id", CURRENT_BASELINE_ID),
            ("contract_task_id", "LAR-P0A-EVAL-001"),
            ("execution_task_id", "LAR-P0A-EVAL-002"),
            ("snapshot", NATIVE_THIN_PATH_EVALUATION_SNAPSHOT),
            ("contract_refs", NATIVE_THIN_PATH_EVALUATION_CONTRACT_REFS),
        ):
            if payload.get(field) != expected:
                failures.append(
                    "native_thin_path_evaluation sealed contract must preserve "
                    f"{field}: {path_value}"
                )

    if set(loaded_contracts) != set(expected_paths):
        return

    evaluation_contract = loaded_contracts[expected_paths[0]][0]
    task_manifest = loaded_contracts[expected_paths[1]][0]
    evidence_schema = loaded_contracts[expected_paths[2]][0]
    _verify_native_thin_path_evaluation_contract_content(
        evaluation_contract=evaluation_contract,
        task_manifest=task_manifest,
        evidence_schema=evidence_schema,
        failures=failures,
    )


def _verify_native_thin_path_evaluation_contract_content(
    *,
    evaluation_contract: dict[str, Any],
    task_manifest: dict[str, Any],
    evidence_schema: dict[str, Any],
    failures: list[str],
) -> None:
    variants = evaluation_contract.get("variants")
    if not isinstance(variants, list) or [
        variant.get("variant_id") for variant in variants if isinstance(variant, dict)
    ] != NATIVE_THIN_PATH_EVALUATION_VARIANTS:
        failures.append("native thin-path evaluation contract must preserve the five comparison variants")
    surfaces = evaluation_contract.get("capability_probes")
    if not isinstance(surfaces, list) or [
        surface.get("surface_id") for surface in surfaces if isinstance(surface, dict)
    ] != NATIVE_THIN_PATH_EVALUATION_SURFACES:
        failures.append("native thin-path evaluation contract must preserve the five independent capability surfaces")
    metrics = evaluation_contract.get("metrics")
    if not isinstance(metrics, list) or [
        metric.get("metric_id") for metric in metrics if isinstance(metric, dict)
    ] != NATIVE_THIN_PATH_EVALUATION_METRICS:
        failures.append("native thin-path evaluation contract must preserve every required metric")
    hard_floors = evaluation_contract.get("hard_floors")
    if not isinstance(hard_floors, list) or [
        rule.get("rule_id") for rule in hard_floors if isinstance(rule, dict)
    ] != NATIVE_THIN_PATH_EVALUATION_HARD_RULES:
        failures.append("native thin-path evaluation contract must preserve every hard floor")
    decision_contract = evaluation_contract.get("decision_contract")
    if not isinstance(decision_contract, dict) or decision_contract.get(
        "allowed_decisions"
    ) != NATIVE_THIN_PATH_EVALUATION_DECISIONS:
        failures.append("native thin-path evaluation contract must preserve the three decision values")
    execution_controls = evaluation_contract.get("execution_controls")
    if not isinstance(execution_controls, dict):
        failures.append("native thin-path evaluation contract must declare execution controls")
    else:
        model = execution_controls.get("model")
        worktree = execution_controls.get("worktree")
        if not isinstance(model, dict) or model.get("model_id") != "gpt-5.6-sol" or model.get(
            "reasoning_effort"
        ) != "high":
            failures.append("native thin-path evaluation contract must fix gpt-5.6-sol/high")
        if not isinstance(worktree, dict) or worktree.get(
            "base_commit"
        ) != NATIVE_THIN_PATH_EVALUATION_SNAPSHOT["commit"] or worktree.get(
            "base_tree"
        ) != NATIVE_THIN_PATH_EVALUATION_SNAPSHOT["tree"] or not worktree.get(
            "primary_worktree_may_not_execute_trials"
        ):
            failures.append("native thin-path evaluation contract must require a detached disposable worktree")
        requested_environment = execution_controls.get("requested_environment")
        if not isinstance(requested_environment, dict) or requested_environment != {
            "sandbox_intent": "workspace_write",
            "network_access": "disabled",
            "approval_mode": "deny_all",
            "credential_mutation": "prohibited",
        }:
            failures.append(
                "native thin-path evaluation contract must preserve the fixed sandbox and permission intent"
            )
    human_intervention = evaluation_contract.get("human_intervention")
    if not isinstance(human_intervention, dict) or any(
        not isinstance(human_intervention.get(field), str)
        or not human_intervention[field].strip()
        for field in (
            "active_minute_rule",
            "passive_wait_rule",
            "unknown_observation_rule",
        )
    ):
        failures.append(
            "native thin-path evaluation contract must define active, passive, and unknown observation rules"
        )
    generation_rules = evaluation_contract.get("generation_and_q0_rules")
    expected_generation_triggers = {
        "model_change",
        "reasoning_effort_change",
        "tool_inventory_change",
        "sandbox_or_permission_change",
        "sdk_or_app_server_behavior_change",
        "managed_worktree_behavior_change",
        "automation_or_external_effect_change",
    }
    if (
        not isinstance(generation_rules, dict)
        or set(generation_rules.get("new_generation_triggers", []))
        != expected_generation_triggers
        or "Q0" not in str(generation_rules.get("required_followup"))
    ):
        failures.append(
            "native thin-path evaluation contract must preserve capability-generation triggers and Q0 followup"
        )
    task_families = task_manifest.get("task_families")
    if not isinstance(task_families, list) or len(task_families) < 3:
        failures.append("native thin-path task-family manifest must contain at least three task families")
    else:
        ids = [family.get("task_family_id") for family in task_families if isinstance(family, dict)]
        if len(ids) != len(task_families) or len(ids) != len(set(ids)):
            failures.append("native thin-path task-family manifest task IDs must be unique")
        for family in task_families:
            if not isinstance(family, dict):
                failures.append("native thin-path task-family manifest entries must be objects")
                continue
            if not isinstance(family.get("task_input"), dict) or not isinstance(
                family.get("success_oracle"), dict
            ):
                failures.append("native thin-path task family must define task_input and success_oracle")
            else:
                task_input = family["task_input"]
                oracle = family["success_oracle"]
                if not isinstance(task_input.get("prompt"), str) or not task_input[
                    "prompt"
                ].strip():
                    failures.append("native thin-path task family task_input.prompt must be non-empty")
                for field in ("required_facts", "required_commands"):
                    value = oracle.get(field)
                    if (
                        not isinstance(value, list)
                        or not value
                        or not all(isinstance(item, str) and item for item in value)
                    ):
                        failures.append(
                            "native thin-path task family success_oracle must define non-empty "
                            f"{field}"
                        )
            if not isinstance(family.get("repeat_count"), int) or family["repeat_count"] < 1:
                failures.append("native thin-path task family repeat_count must be positive")
            eligible_variants = family.get("eligible_variants")
            if not isinstance(eligible_variants, list) or not eligible_variants or not set(eligible_variants).issubset(
                set(NATIVE_THIN_PATH_EVALUATION_VARIANTS)
            ):
                failures.append("native thin-path task family may only reference declared variants")
    counterbalancing = task_manifest.get("counterbalancing")
    if not isinstance(counterbalancing, dict) or counterbalancing.get(
        "method"
    ) != "balanced_latin_square_v1":
        failures.append("native thin-path task-family manifest must define counterbalancing")
    elif (
        counterbalancing.get("core_variant_order")
        != NATIVE_THIN_PATH_EVALUATION_VARIANTS[:2]
        or counterbalancing.get("conditional_variant_order")
        != NATIVE_THIN_PATH_EVALUATION_VARIANTS[2:]
        or counterbalancing.get("block_count") != 3
    ):
        failures.append(
            "native thin-path task-family manifest must preserve the fixed variant counterbalancing"
        )
    denominator_rules = task_manifest.get("denominator_rules")
    expected_denominator_keys = {
        "core_comparison",
        "conditional_harness_comparison",
        "downstream_outcome",
        "recovery_rollback",
    }
    if (
        not isinstance(denominator_rules, dict)
        or set(denominator_rules) != expected_denominator_keys
        or any(
            not isinstance(value, str) or not value.strip()
            for value in denominator_rules.values()
        )
    ):
        failures.append(
            "native thin-path task-family manifest must preserve every denominator rule"
        )
    record_types = evidence_schema.get("record_types")
    if not isinstance(record_types, dict) or set(record_types) != {
        "environment_capture",
        "trial_record",
        "capability_probe_record",
        "recovery_rollback_record",
        "downstream_outcome_record",
        "results_artifact",
        "decision_artifact",
        "evidence_artifact",
    }:
        failures.append("native thin-path evidence schema must define every required record type")
    identity_requirement = evidence_schema.get("contract_identity_requirement")
    if not isinstance(identity_requirement, dict) or identity_requirement.get(
        "identity_field"
    ) != "contract_identity":
        failures.append("native thin-path evidence schema must require complete contract_identity")
    elif set(identity_requirement.get("required_in", [])) != {
        "environment_capture",
        "trial_record",
        "capability_probe_record",
        "recovery_rollback_record",
        "downstream_outcome_record",
        "results_artifact",
        "decision_artifact",
        "evidence_artifact",
    }:
        failures.append(
            "native thin-path evidence schema must require contract_identity in every evidence record"
        )


def _verify_terminal_native_thin_path_evaluation_artifacts(
    *,
    root: Path,
    evaluation: dict[str, Any],
    contract_identity: Any,
    status: Any,
    decision: Any,
    failures: list[str],
) -> None:
    """Bind a terminal evaluation decision to real, cross-referenced JSON evidence."""

    if not isinstance(status, str) or not isinstance(decision, str):
        return

    artifacts: dict[str, tuple[dict[str, Any], bytes]] = {}
    for field in ("result_ref", "decision_ref", "evidence_ref"):
        artifact = _load_native_thin_path_evaluation_artifact(
            root=root,
            value=evaluation.get(field),
            field=field,
            failures=failures,
        )
        if artifact is not None:
            artifacts[field] = artifact

    if set(artifacts) != {"result_ref", "decision_ref", "evidence_ref"}:
        return

    result, result_raw = artifacts["result_ref"]
    decision_record, decision_raw = artifacts["decision_ref"]
    evidence, _ = artifacts["evidence_ref"]
    contract_refs = evaluation.get("contract_output_refs")

    _require_fields(
        result,
        [
            "schema_version",
            "baseline_id",
            "status",
            "decision",
            "contract_output_refs",
            "contract_identity",
            "decision_ref",
            "evidence_ref",
        ],
        "terminal native thin-path results artifact",
        failures,
    )
    if result.get("schema_version") != NATIVE_THIN_PATH_RESULTS_SCHEMA:
        failures.append(
            "terminal native thin-path results artifact has an unexpected schema_version"
        )
    if result.get("baseline_id") != CURRENT_BASELINE_ID:
        failures.append(
            "terminal native thin-path results artifact must bind the current baseline"
        )
    if result.get("status") != status or result.get("decision") != decision:
        failures.append(
            "terminal native thin-path results artifact must match planning status and decision"
        )
    if result.get("contract_output_refs") != contract_refs:
        failures.append(
            "terminal native thin-path results artifact must bind the frozen contract output refs"
        )
    if result.get("contract_identity") != contract_identity:
        failures.append(
            "terminal native thin-path results artifact must bind the exact contract_identity"
        )
    if (
        result.get("decision_ref") != evaluation.get("decision_ref")
        or result.get("evidence_ref") != evaluation.get("evidence_ref")
    ):
        failures.append(
            "terminal native thin-path results artifact must bind the declared decision and evidence refs"
        )

    _require_fields(
        decision_record,
        [
            "schema_version",
            "baseline_id",
            "status",
            "decision",
            "contract_identity",
            "result_ref",
            "evidence_ref",
        ],
        "terminal native thin-path decision artifact",
        failures,
    )
    if decision_record.get("schema_version") != NATIVE_THIN_PATH_DECISION_SCHEMA:
        failures.append(
            "terminal native thin-path decision artifact has an unexpected schema_version"
        )
    if decision_record.get("baseline_id") != CURRENT_BASELINE_ID:
        failures.append(
            "terminal native thin-path decision artifact must bind the current baseline"
        )
    if (
        decision_record.get("status") != status
        or decision_record.get("decision") != decision
    ):
        failures.append(
            "terminal native thin-path decision artifact must match planning status and decision"
        )
    if (
        decision_record.get("result_ref") != evaluation.get("result_ref")
        or decision_record.get("evidence_ref") != evaluation.get("evidence_ref")
    ):
        failures.append(
            "terminal native thin-path decision artifact must bind the declared result and evidence refs"
        )
    if decision_record.get("contract_identity") != contract_identity:
        failures.append(
            "terminal native thin-path decision artifact must bind the exact contract_identity"
        )

    _require_fields(
        evidence,
        [
            "schema_version",
            "baseline_id",
            "status",
            "decision",
            "contract_identity",
            "result_ref",
            "decision_ref",
            "result_sha256",
            "decision_sha256",
        ],
        "terminal native thin-path evidence artifact",
        failures,
    )
    if evidence.get("schema_version") != NATIVE_THIN_PATH_EVIDENCE_SCHEMA:
        failures.append(
            "terminal native thin-path evidence artifact has an unexpected schema_version"
        )
    if evidence.get("baseline_id") != CURRENT_BASELINE_ID:
        failures.append(
            "terminal native thin-path evidence artifact must bind the current baseline"
        )
    if evidence.get("status") != status or evidence.get("decision") != decision:
        failures.append(
            "terminal native thin-path evidence artifact must match planning status and decision"
        )
    if (
        evidence.get("result_ref") != evaluation.get("result_ref")
        or evidence.get("decision_ref") != evaluation.get("decision_ref")
    ):
        failures.append(
            "terminal native thin-path evidence artifact must bind the declared result and decision refs"
        )
    if evidence.get("contract_identity") != contract_identity:
        failures.append(
            "terminal native thin-path evidence artifact must bind the exact contract_identity"
        )
    if evidence.get("result_sha256") != hashlib.sha256(result_raw).hexdigest():
        failures.append(
            "terminal native thin-path evidence artifact result_sha256 must match result bytes"
        )
    if evidence.get("decision_sha256") != hashlib.sha256(decision_raw).hexdigest():
        failures.append(
            "terminal native thin-path evidence artifact decision_sha256 must match decision bytes"
        )
    _verify_terminal_generation_projection(result, evidence, failures)


def _verify_terminal_generation_projection(
    result: dict[str, Any],
    evidence: dict[str, Any],
    failures: list[str],
) -> None:
    """Require pooled trial metrics to remain attributable to capability generations."""

    execution = result.get("execution_condition")
    comparison = result.get("core_comparison")
    if not isinstance(execution, dict) or not isinstance(comparison, dict):
        failures.append(
            "terminal native thin-path results artifact must contain execution_condition and core_comparison objects"
        )
        return

    generation_ids = execution.get("core_generation_sha256")
    generation_count = execution.get("core_generation_count")
    current_generation = execution.get("current_qualified_cli_generation_sha256")
    if (
        not isinstance(generation_ids, list)
        or not generation_ids
        or any(not _is_sha256(value) for value in generation_ids)
        or len(set(generation_ids)) != len(generation_ids)
    ):
        failures.append(
            "terminal native thin-path results artifact core_generation_sha256 must contain distinct SHA-256 identities"
        )
        return
    if type(generation_count) is not int or generation_count != len(generation_ids):
        failures.append(
            "terminal native thin-path results artifact core_generation_count must match core_generation_sha256"
        )
    if execution.get("core_generation_policy") != (
        "append_only_resume_after_new_generation_q0"
    ):
        failures.append(
            "terminal native thin-path results artifact must declare append-only generation/Q0 resume policy"
        )
    if current_generation not in generation_ids:
        failures.append(
            "terminal native thin-path results artifact current qualified generation must be a core generation"
        )

    q0_only = execution.get("q0_only_invalidated_generation_sha256", [])
    if (
        not isinstance(q0_only, list)
        or any(not _is_sha256(value) for value in q0_only)
        or set(q0_only) & set(generation_ids)
    ):
        failures.append(
            "terminal native thin-path results artifact q0-only generations must be distinct SHA-256 identities outside the core set"
        )

    strata = comparison.get("generation_strata")
    if not isinstance(strata, list) or len(strata) != len(generation_ids):
        failures.append(
            "terminal native thin-path results artifact generation_strata must cover every core generation"
        )
        return
    strata_by_generation: dict[str, dict[str, Any]] = {}
    for stratum in strata:
        if not isinstance(stratum, dict) or not _is_sha256(
            stratum.get("generation_sha256")
        ):
            failures.append(
                "terminal native thin-path results artifact generation_strata entries must be identified objects"
            )
            continue
        generation_id = stratum["generation_sha256"]
        if generation_id in strata_by_generation:
            failures.append(
                "terminal native thin-path results artifact generation_strata must not duplicate a generation"
            )
        strata_by_generation[generation_id] = stratum
    if set(strata_by_generation) != set(generation_ids):
        failures.append(
            "terminal native thin-path results artifact generation_strata identities must match core generations"
        )

    receipts = evidence.get("trial_receipts")
    projections = evidence.get("generation_trial_projection")
    generation_records = evidence.get("generation_record_projection")
    completeness = evidence.get("evidence_completeness")
    supporting = evidence.get("supporting_records")
    if (
        not isinstance(receipts, list)
        or not isinstance(projections, list)
        or not isinstance(generation_records, list)
        or not isinstance(completeness, dict)
        or not isinstance(supporting, dict)
    ):
        failures.append(
            "terminal native thin-path evidence artifact must contain receipts, generation projections, completeness and supporting records"
        )
        return

    record_generation_ids: list[str] = []

    def valid_private_evidence_path(value: Any) -> bool:
        return (
            isinstance(value, str)
            and value.startswith("private-local/")
            and ".." not in value.split("/")
        )

    def valid_support_record(key: Any) -> bool:
        record = supporting.get(key) if isinstance(key, str) else None
        return (
            isinstance(record, dict)
            and valid_private_evidence_path(record.get("path"))
            and _is_sha256(record.get("sha256"))
        )

    def is_non_negative_int(value: Any) -> bool:
        return type(value) is int and value >= 0

    def is_non_negative_number(value: Any) -> bool:
        return (
            type(value) in {int, float}
            and value >= 0
            and value < float("inf")
        )

    for projection in generation_records:
        if not isinstance(projection, dict):
            failures.append(
                "terminal native thin-path evidence generation record projection entries must be objects"
            )
            continue
        generation_id = projection.get("generation_sha256")
        lock_key = projection.get("lock_record")
        q0_key = projection.get("q0_record")
        selected_for_core = projection.get("selected_for_core")
        if (
            not _is_sha256(generation_id)
            or not isinstance(lock_key, str)
            or not isinstance(q0_key, str)
            or not valid_support_record(lock_key)
            or not valid_support_record(q0_key)
            or not isinstance(projection.get("q0_state"), str)
            or not projection["q0_state"].strip()
            or not isinstance(selected_for_core, bool)
            or selected_for_core != (generation_id in generation_ids)
        ):
            failures.append(
                "terminal native thin-path evidence generation record projection must bind each generation to lock and Q0 evidence"
            )
            continue
        record_generation_ids.append(generation_id)
    expected_record_generations = set(generation_ids) | set(q0_only)
    if (
        len(record_generation_ids) != len(set(record_generation_ids))
        or set(record_generation_ids) != expected_record_generations
    ):
        failures.append(
            "terminal native thin-path evidence generation record projection must cover core and q0-only generations exactly once"
        )

    receipt_by_hash: dict[str, dict[str, Any]] = {}
    for receipt in receipts:
        if (
            not isinstance(receipt, dict)
            or not valid_private_evidence_path(receipt.get("path"))
            or not _is_sha256(receipt.get("sha256"))
            or not isinstance(receipt.get("variant_id"), str)
            or receipt.get("normalized_outcome")
            not in {"succeeded", "failed", "stopped"}
            or not is_non_negative_number(receipt.get("wall_seconds"))
            or not is_non_negative_int(receipt.get("input_tokens"))
            or not is_non_negative_int(receipt.get("output_tokens"))
        ):
            failures.append(
                "terminal native thin-path evidence trial receipts must contain private-local locators, typed non-negative metrics and SHA-256 identities"
            )
            continue
        receipt_by_hash[receipt["sha256"]] = receipt
    if len(receipt_by_hash) != len(receipts):
        failures.append(
            "terminal native thin-path evidence trial receipt identities must be unique"
        )

    projected_hashes: list[str] = []
    projected_generation_ids: list[str] = []
    projected_by_generation: dict[str, list[dict[str, Any]]] = {}
    for projection in projections:
        if not isinstance(projection, dict):
            failures.append(
                "terminal native thin-path evidence generation projection entries must be objects"
            )
            continue
        generation_id = projection.get("generation_sha256")
        hashes = projection.get("receipt_sha256")
        if (
            generation_id not in generation_ids
            or not isinstance(hashes, list)
            or any(not _is_sha256(value) for value in hashes)
        ):
            failures.append(
                "terminal native thin-path evidence generation projection must bind a core generation to receipt hashes"
            )
            continue
        projected_generation_ids.append(generation_id)
        projected_hashes.extend(hashes)
        projected_by_generation[generation_id] = [
            receipt_by_hash[value] for value in hashes if value in receipt_by_hash
        ]
    if (
        len(projected_generation_ids) != len(set(projected_generation_ids))
        or set(projected_generation_ids) != set(generation_ids)
    ):
        failures.append(
            "terminal native thin-path evidence generation projection must cover each core generation exactly once"
        )
    if (
        len(projected_hashes) != len(set(projected_hashes))
        or set(projected_hashes) != set(receipt_by_hash)
    ):
        failures.append(
            "terminal native thin-path evidence generation projection must cover each trial receipt exactly once"
        )

    for generation_id, generation_receipts in projected_by_generation.items():
        stratum = strata_by_generation.get(generation_id)
        if stratum is None:
            continue
        outcome_counts = {
            outcome: sum(
                receipt.get("normalized_outcome") == outcome
                for receipt in generation_receipts
            )
            for outcome in ("succeeded", "failed", "stopped")
        }
        expected = {
            "trials": len(generation_receipts),
            "successes": outcome_counts["succeeded"],
            "failures": outcome_counts["failed"],
            "stops": outcome_counts["stopped"],
            "input_tokens": sum(
                receipt.get("input_tokens", 0) for receipt in generation_receipts
            ),
            "output_tokens": sum(
                receipt.get("output_tokens", 0) for receipt in generation_receipts
            ),
        }
        for field, value in expected.items():
            if not is_non_negative_int(stratum.get(field)) or stratum.get(
                field
            ) != value:
                failures.append(
                    f"terminal native thin-path generation stratum {field} must match projected receipts: {generation_id}"
                )
        wall_total = round(
            sum(receipt.get("wall_seconds", 0) for receipt in generation_receipts), 3
        )
        if not is_non_negative_number(
            stratum.get("wall_time_total_seconds")
        ) or stratum.get("wall_time_total_seconds") != wall_total:
            failures.append(
                f"terminal native thin-path generation stratum wall time must match projected receipts: {generation_id}"
            )
        variants = stratum.get("variants")
        if not isinstance(variants, list):
            failures.append(
                f"terminal native thin-path generation stratum variants must be an array: {generation_id}"
            )
            continue
        variants_by_id = {
            value.get("variant_id"): value
            for value in variants
            if isinstance(value, dict) and isinstance(value.get("variant_id"), str)
        }
        expected_variant_ids = {
            receipt["variant_id"] for receipt in generation_receipts
        }
        if len(variants_by_id) != len(variants) or set(variants_by_id) != expected_variant_ids:
            failures.append(
                f"terminal native thin-path generation stratum variants must match projected receipts: {generation_id}"
            )
            continue
        for variant_id in expected_variant_ids:
            variant_receipts = [
                receipt
                for receipt in generation_receipts
                if receipt["variant_id"] == variant_id
            ]
            variant = variants_by_id[variant_id]
            variant_expected = {
                "trials": len(variant_receipts),
                "successes": sum(
                    receipt["normalized_outcome"] == "succeeded"
                    for receipt in variant_receipts
                ),
                "failures": sum(
                    receipt["normalized_outcome"] == "failed"
                    for receipt in variant_receipts
                ),
                "stops": sum(
                    receipt["normalized_outcome"] == "stopped"
                    for receipt in variant_receipts
                ),
            }
            for field, value in variant_expected.items():
                if not is_non_negative_int(variant.get(field)) or variant.get(
                    field
                ) != value:
                    failures.append(
                        f"terminal native thin-path generation variant {field} must match projected receipts: {generation_id}/{variant_id}"
                    )

    declared_trials = comparison.get("declared_trials")
    if not is_non_negative_int(declared_trials) or declared_trials != len(receipts):
        failures.append(
            "terminal native thin-path evidence receipt count must match declared core trials"
        )
    if not is_non_negative_int(
        comparison.get("pooled_across_generation_count")
    ) or comparison.get("pooled_across_generation_count") != len(generation_ids):
        failures.append(
            "terminal native thin-path pooled generation count must match execution condition"
        )
    if comparison.get("pooled_profile_promotion_eligible") is not False:
        failures.append(
            "terminal native thin-path pooled cross-generation metrics must not be promotion-eligible"
        )
    aggregate_fields = {
        "declared_trials": "trials",
        "normalized_successes": "successes",
        "normalized_failures": "failures",
        "normalized_stops": "stops",
    }
    for aggregate_field, stratum_field in aggregate_fields.items():
        values = [stratum.get(stratum_field) for stratum in strata_by_generation.values()]
        if not all(is_non_negative_int(value) for value in values) or comparison.get(
            aggregate_field
        ) != sum(values):
            failures.append(
                f"terminal native thin-path pooled {aggregate_field} must equal generation strata"
            )

    transition_keys = sorted(
        key for key in supporting if key.startswith("generation_transition_")
    )
    expected_transition_count = max(len(generation_ids) - 1, 0)
    transition_summary = comparison.get("generation_transition_summary")
    if (
        not isinstance(transition_summary, dict)
        or transition_summary.get("transition_records")
        != expected_transition_count
        or transition_summary.get("q0_admitted_trial_generations")
        != len(generation_ids)
        or transition_summary.get("q0_only_invalidated_generations") != len(q0_only)
    ):
        failures.append(
            "terminal native thin-path generation transition summary must match execution generations"
        )
    if (
        completeness.get("core_generation_count") != len(generation_ids)
        or completeness.get("generation_transition_records_present")
        != len(transition_keys)
        or completeness.get("generation_transition_records_expected")
        != expected_transition_count
        or len(transition_keys) != expected_transition_count
        or completeness.get("q0_only_invalidated_generation_count") != len(q0_only)
        or completeness.get("cross_generation_strata_reported")
        != (len(generation_ids) > 1)
    ):
        failures.append(
            "terminal native thin-path generation completeness must match strata and transition evidence"
        )
    for key in transition_keys:
        if not valid_support_record(key):
            failures.append(
                f"terminal native thin-path supporting generation transition is invalid: {key}"
            )


def _load_native_thin_path_evaluation_artifact(
    *,
    root: Path,
    value: Any,
    field: str,
    failures: list[str],
) -> tuple[dict[str, Any], bytes] | None:
    label = f"terminal native_thin_path_evaluation.{field}"
    try:
        path = _resolve_repo_path(root, value, label)
    except ValueError as exc:
        failures.append(str(exc))
        return None

    evaluation_root = (root / NATIVE_THIN_PATH_EVALUATION_ROOT).resolve(strict=False)
    try:
        path.relative_to(evaluation_root)
    except ValueError:
        failures.append(f"{label} must remain under the evaluation evidence root")
        return None
    if not path.is_file():
        failures.append(f"{label} artifact does not exist")
        return None
    try:
        return _load_json_with_bytes(path)
    except ValueError as exc:
        failures.append(f"{label} must be a readable JSON object: {exc}")
        return None


def _verify_authoritative_docs(
    root: Path, status: dict[str, Any], failures: list[str]
) -> None:
    docs = status.get("authoritative_docs")
    if not isinstance(docs, list) or not docs:
        failures.append("authoritative_docs must be a non-empty array")
        return
    if len(docs) != len(set(docs)):
        failures.append("authoritative_docs must not contain duplicates")
    for relative in docs:
        try:
            path = _resolve_repo_path(root, relative, "authoritative doc")
        except ValueError as exc:
            failures.append(str(exc))
            continue
        if not path.is_file():
            failures.append(f"missing authoritative doc: {relative}")

    contracts = status.get("doc_contracts")
    if not isinstance(contracts, list):
        failures.append("doc_contracts must be an array")
        return
    for index, contract in enumerate(contracts):
        if not isinstance(contract, dict):
            failures.append(f"doc_contracts[{index}] must be an object")
            continue
        relative = contract.get("path")
        required = contract.get("required_strings")
        if relative not in docs:
            failures.append(f"doc contract path is not authoritative: {relative}")
        if not isinstance(required, list) or not required:
            failures.append(f"doc contract required_strings must be non-empty: {relative}")
            continue
        try:
            path = _resolve_repo_path(root, relative, "doc contract")
            text = path.read_text(encoding="utf-8")
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            failures.append(f"doc contract is unreadable: {relative}: {exc}")
            continue
        for token in required:
            if not isinstance(token, str) or token not in text:
                failures.append(f"doc contract missing required string: {relative}:{token}")


def _verify_runtime_source_tree(
    root: Path,
    layout: Any,
    failures: list[str],
) -> None:
    if not isinstance(layout, dict):
        return
    source_root_value = layout.get("source_root")
    if not isinstance(source_root_value, str):
        return
    try:
        source_root = _resolve_repo_path(
            root,
            source_root_value.rstrip("/"),
            "runtime source root",
        )
    except ValueError as exc:
        failures.append(str(exc))
        return
    if not source_root.exists():
        return
    if not source_root.is_dir():
        failures.append("runtime source root must be a directory")
        return

    root_files = layout.get("approved_root_files")
    subpackages = layout.get("approved_subpackages")
    if not isinstance(root_files, list) or not isinstance(subpackages, list):
        return
    approved_root_files = set(root_files)
    approved_subpackages = set(subpackages)

    for child in sorted(source_root.iterdir(), key=lambda path: path.name):
        if child.name in IGNORED_RUNTIME_SOURCE_TREE_ENTRIES:
            continue
        try:
            child_stat = child.lstat()
        except OSError as exc:
            failures.append(
                f"runtime source tree entry is unreadable: {child.name}: {exc}"
            )
            continue
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        file_attributes = getattr(child_stat, "st_file_attributes", 0)
        if child.is_symlink() or bool(file_attributes & reparse_flag):
            failures.append(
                f"runtime source tree contains symlink/reparse entry: {child.name}"
            )
            continue
        if child.is_file():
            if child.name not in approved_root_files:
                failures.append(
                    f"runtime source tree contains unapproved root file: {child.name}"
                )
            continue
        if child.is_dir():
            if child.name not in approved_subpackages:
                failures.append(
                    f"runtime source tree contains unapproved subpackage: {child.name}"
                )
                continue
            _verify_runtime_source_subtree(
                source_root,
                child,
                failures,
            )
            continue
        failures.append(f"runtime source tree contains unsupported entry: {child.name}")


def _verify_runtime_source_subtree(
    source_root: Path,
    directory: Path,
    failures: list[str],
) -> None:
    pending = [directory]
    while pending:
        current = pending.pop()
        try:
            children = sorted(current.iterdir(), key=lambda path: path.name)
        except OSError as exc:
            relative = current.relative_to(source_root).as_posix()
            failures.append(
                f"runtime source tree directory is unreadable: {relative}: {exc}"
            )
            continue
        for child in children:
            if child.name in IGNORED_RUNTIME_SOURCE_TREE_ENTRIES:
                continue
            relative = child.relative_to(source_root).as_posix()
            try:
                child_stat = child.lstat()
            except OSError as exc:
                failures.append(
                    f"runtime source tree entry is unreadable: {relative}: {exc}"
                )
                continue
            reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            file_attributes = getattr(child_stat, "st_file_attributes", 0)
            if child.is_symlink() or bool(file_attributes & reparse_flag):
                failures.append(
                    f"runtime source tree contains symlink/reparse entry: {relative}"
                )
                continue
            if child.is_dir():
                pending.append(child)
                continue
            if not child.is_file():
                failures.append(
                    f"runtime source tree contains unsupported entry: {relative}"
                )


def _work_item_list(item: dict[str, Any], field: str) -> list[Any]:
    value = item.get(field)
    return value if isinstance(value, list) else []


def _work_item_scope_list(item: dict[str, Any], field: str) -> list[Any]:
    scope = item.get("scope")
    if not isinstance(scope, dict):
        return []
    value = scope.get(field)
    return value if isinstance(value, list) else []


def _verify_acyclic_dependencies(
    items: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visited:
            return
        if task_id in visiting:
            failures.append(f"work-item dependency cycle includes {task_id}")
            return
        visiting.add(task_id)
        for dependency in _work_item_list(items[task_id], "depends_on"):
            if isinstance(dependency, str) and dependency in items:
                visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in items:
        visit(task_id)


def _verify_graph_policy(
    value: Any,
    items: dict[str, dict[str, Any]],
    current_work: dict[str, Any],
    failures: list[str],
) -> None:
    policy = _as_dict(value, "work-item graph_policy", failures)
    expected = {
        "kind": "deterministic_dag_v1",
        "root_task_ids": EXPECTED_GRAPH_ROOTS,
        "ready_order": ["priority_ascending", "task_id_utf8_ascending"],
        "single_selected_ready_task": True,
        "real_writer_requires": ["LAR-P1G-001", "LAR-Q0-001"],
    }
    if policy != expected:
        failures.append("work-item graph_policy must match the deterministic v3.23 DAG policy")

    for root in EXPECTED_GRAPH_ROOTS:
        if root not in items:
            failures.append(f"declared graph root does not exist: {root}")
        elif _work_item_list(items[root], "depends_on"):
            failures.append(f"declared graph root must have no dependencies: {root}")

    reachable: set[str] = set()
    pending = list(reversed(EXPECTED_GRAPH_ROOTS))
    while pending:
        task_id = pending.pop()
        if task_id in reachable or task_id not in items:
            continue
        reachable.add(task_id)
        pending.extend(
            reversed(
                [
                    successor
                    for successor in _work_item_list(items[task_id], "next_task_ids")
                    if isinstance(successor, str)
                ]
            )
        )
    unreachable = sorted(set(items) - reachable)
    if unreachable:
        failures.append(
            "work items are not reachable from the declared graph roots: "
            f"{unreachable}"
        )

    selectable = [
        (item.get("priority"), task_id)
        for task_id, item in items.items()
        if item.get("status")
        in {
            "contract_pending",
            "execution_pending",
            "narrow_profile_or_adapter_candidate",
            "supersede_required",
            "ready",
        }
        and isinstance(item.get("priority"), int)
        and not isinstance(item.get("priority"), bool)
        and all(
            items.get(dependency, {}).get("status") == "completed"
            for dependency in _work_item_list(item, "depends_on")
            if isinstance(dependency, str)
        )
    ]
    selected = min(
        selectable,
        default=(None, None),
        key=lambda entry: (entry[0], entry[1]),
    )
    if selected[1] != current_work.get("task_id"):
        failures.append(
            "current work item must match deterministic priority/task-id selectable selection"
        )


def _verify_contract_projection_policy(
    value: Any,
    items: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    policy = _as_dict(value, "work-item contract_projection_policy", failures)
    if policy.get("kind") != "closed_contract_projection_v1":
        failures.append(
            "work-item contract_projection_policy.kind must be closed_contract_projection_v1"
        )
    if policy.get("projection_identity") != "plan_id_plus_projection_id":
        failures.append(
            "work-item projection_identity must be plan_id_plus_projection_id"
        )
    rules = policy.get("rules")
    if (
        not isinstance(rules, list)
        or not rules
        or not all(isinstance(rule, str) and rule for rule in rules)
        or len(rules) != len(set(rules))
    ):
        failures.append("work-item projection rules must be unique non-empty strings")
    if policy.get("projections") != EXPECTED_CONTRACT_PROJECTIONS:
        failures.append(
            "work-item contract projections must match the frozen v3.23 projection catalog"
        )

    expected_by_task: dict[str, dict[str, list[str]]] = {}
    expected_tokens_by_task: dict[str, list[str]] = {}

    def add_projection(task_id: str, kind: str, projection_id: str) -> None:
        declaration = expected_by_task.setdefault(
            task_id, {"produces": [], "implements": [], "accepts": []}
        )
        declaration[kind].append(projection_id)

    def add_tokens(task_id: str, tokens: list[str]) -> None:
        task_tokens = expected_tokens_by_task.setdefault(task_id, [])
        for token in tokens:
            if token not in task_tokens:
                task_tokens.append(token)

    for projection in EXPECTED_CONTRACT_PROJECTIONS:
        projection_id = projection["projection_id"]
        producer = projection["normative_producer_task_id"]
        implementations = projection["implementation_task_ids"]
        acceptances = projection["acceptance_task_ids"]
        participants = [producer, *implementations, *acceptances]
        if producer not in items or not producer.startswith("LAR-P0A-"):
            failures.append(
                f"{projection_id} must have one existing P0A normative producer"
            )
        if not implementations and not acceptances:
            failures.append(
                f"{projection_id} must have an implementation or acceptance consumer"
            )
        if len(participants) != len(set(participants)):
            failures.append(f"{projection_id} task roles must not overlap")
        for task_id in participants:
            if task_id not in items:
                failures.append(f"{projection_id} references unknown task {task_id}")
        add_projection(producer, "produces", projection_id)
        for task_id in implementations:
            add_projection(task_id, "implements", projection_id)
        for task_id in acceptances:
            add_projection(task_id, "accepts", projection_id)
        for task_id in participants:
            add_tokens(task_id, projection["required_contract_tokens"])

    for task_id, item in items.items():
        expected_declaration = expected_by_task.get(task_id)
        actual_declaration = item.get("contract_projections")
        if expected_declaration is None:
            if actual_declaration is not None:
                failures.append(
                    f"{task_id} must not declare unreferenced contract projections"
                )
            if item.get("contract_projection_tokens") is not None:
                failures.append(
                    f"{task_id} must not declare unreferenced contract projection tokens"
                )
            continue
        if not isinstance(actual_declaration, dict):
            failures.append(f"{task_id}.contract_projections must be an object")
            actual_declaration = {}
        elif set(actual_declaration) != {"produces", "implements", "accepts"}:
            failures.append(
                f"{task_id}.contract_projections must contain exactly "
                "produces, implements and accepts"
            )
        for kind in ("produces", "implements", "accepts"):
            expected_ids = expected_declaration[kind]
            if actual_declaration.get(kind) != expected_ids:
                failures.append(
                    f"{task_id}.{kind} projections must exactly match policy"
                )
                for projection_id in expected_ids:
                    role = {
                        "produces": "producer",
                        "implements": "implementation",
                        "accepts": "acceptance",
                    }[kind]
                    failures.append(
                        f"{projection_id} {role} reverse projection mismatch for {task_id}"
                    )
        actual_tokens = item.get("contract_projection_tokens")
        expected_tokens = expected_tokens_by_task[task_id]
        if actual_tokens != expected_tokens:
            failures.append(
                f"{task_id} contract projection tokens must exactly match policy"
            )
            for projection in EXPECTED_CONTRACT_PROJECTIONS:
                projection_id = projection["projection_id"]
                if projection_id not in sum(expected_declaration.values(), []):
                    continue
                missing = [
                    token
                    for token in projection["required_contract_tokens"]
                    if not isinstance(actual_tokens, list) or token not in actual_tokens
                ]
                for token in missing:
                    failures.append(
                        f"{projection_id} task {task_id} missing required contract token: {token}"
                    )


def _load_json(path: Path) -> dict[str, Any]:
    payload, _ = _load_json_with_bytes(path)
    return payload


def _load_json_with_bytes(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"JSON file is not readable: {path} ({exc})") from exc

    return _loads_json_object(text, str(path)), raw


def _loads_json_object(text: str, label: str) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"JSON contains duplicate key {key!r}: {label}")
            result[key] = value
        return result

    try:
        payload = json.loads(text, object_pairs_hook=reject_duplicates)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON is invalid: {label} ({exc.msg})") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON must contain an object: {label}")
    return payload


def _resolve_repo_path(root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} path must be a non-empty repo-relative string")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{label} path must remain repo-relative: {value}")
    resolved = (root / relative).resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} path escapes repo root: {value}") from exc
    return resolved


def _require_fields(
    payload: dict[str, Any],
    fields: list[str],
    label: str,
    failures: list[str],
) -> None:
    missing = [field for field in fields if field not in payload]
    if missing:
        failures.append(f"{label} missing fields: {', '.join(missing)}")


def _as_dict(value: Any, label: str, failures: list[str]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    failures.append(f"{label} must be an object")
    return {}


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and value == value.lower()
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_unicode_noncharacter(codepoint: int) -> bool:
    return 0xFDD0 <= codepoint <= 0xFDEF or (codepoint & 0xFFFF) in {0xFFFE, 0xFFFF}


def _relative_or_absolute(root: Path, path: Path) -> str:
    resolved = path.resolve(strict=False)
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return resolved.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
