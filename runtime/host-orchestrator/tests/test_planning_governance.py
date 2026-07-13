from __future__ import annotations

import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
STATUS_PATH = REPO_ROOT / "docs" / "architecture" / "planning-status.json"
BASELINE_PATH = (
    REPO_ROOT
    / "docs"
    / "specs"
    / "local-ai-runtime-0.2-v3.23-baseline-candidate.md"
)
BASELINE_ENTRY_PATH = (
    REPO_ROOT
    / "docs"
    / "specs"
    / "local-ai-runtime-0.2-baseline-candidate.md"
)
V320_PATH = (
    REPO_ROOT
    / "docs"
    / "specs"
    / "local-ai-runtime-0.2-v3.20-baseline-candidate.md"
)
VERIFIER_PATH = REPO_ROOT / "scripts" / "verify-planning-status.py"
SELECTOR_PATH = REPO_ROOT / "scripts" / "select-next-work.py"
HISTORY_EXTRACTOR_PATH = REPO_ROOT / "scripts" / "extract-local-ai-runtime-history.py"
POLICY_PATH = REPO_ROOT / "docs" / "architecture" / "next-work-selection-policy.json"
INVENTORY_PATH = (
    REPO_ROOT / "docs" / "specs" / "local-ai-runtime-0.2-normative-package.json"
)
LINEAGE_PATH = (
    REPO_ROOT
    / "docs"
    / "specs"
    / "local-ai-runtime-0.2"
    / "normative"
    / "BaselineLineage.v2.json"
)
BASELINE_MANIFEST_SCHEMA_PATH = (
    REPO_ROOT
    / "docs"
    / "specs"
    / "local-ai-runtime-0.2"
    / "normative"
    / "BaselineManifest.v1.schema.json"
)
BASELINE_MANIFEST_FIXTURE_PATH = (
    REPO_ROOT
    / "docs"
    / "specs"
    / "local-ai-runtime-0.2"
    / "fixtures"
    / "baseline-bytes"
    / "manifest.json"
)
BASELINE_PACKAGE_VERIFIER_PATH = REPO_ROOT / "scripts" / "verify-local-ai-runtime-baseline.py"
WORK_ITEMS_PATH = REPO_ROOT / "docs" / "plans" / "local-ai-runtime-0.2-work-items.json"
IMPLEMENTATION_PLAN_PATH = (
    REPO_ROOT / "docs" / "plans" / "orchestrator-implementation-plan.md"
)
ACCEPTANCE_PATH = REPO_ROOT / "docs" / "specs" / "acceptance-and-gates.md"
PRD_PATH = REPO_ROOT / "docs" / "product" / "orchestrator-prd.md"
ARCHITECTURE_PATH = (
    REPO_ROOT / "docs" / "architecture" / "orchestrator-target-architecture.md"
)
ROADMAP_PATH = REPO_ROOT / "docs" / "roadmap" / "orchestrator-roadmap.md"
BACKLOG_PATH = REPO_ROOT / "docs" / "backlog" / "orchestrator-task-list.md"
HIGH_RISK_PROJECTION_TOKENS = frozenset(
    {
        "ProcessHandlePolicy",
        "ChildHandleManifest",
        "PROC_THREAD_ATTRIBUTE_HANDLE_LIST",
        "STARTF_USESTDHANDLES",
        "OrdinalIgnoreCase",
        "runtime_external_v1",
        "EvidenceProjectionAcceptance",
        "QuarantineKeyEnvelope",
        "RuntimeIntegrityKeyEnvelope",
        "BackupRestoreEligibility",
        "BackupPostActivity",
        "BackupRestoreIntent",
    }
)
HIGH_RISK_PROJECTION_PATHS = {
    "docs/plans/local-ai-runtime-0.2-work-items.json": WORK_ITEMS_PATH,
    "docs/plans/orchestrator-implementation-plan.md": IMPLEMENTATION_PLAN_PATH,
    "docs/specs/acceptance-and-gates.md": ACCEPTANCE_PATH,
}
SOURCE_LAYOUT_PROJECTION_TOKENS = frozenset(
    {
        "approved_root_files",
        "approved_subpackages",
        "required_source_owners",
    }
)
SOURCE_LAYOUT_PROJECTION_PATHS = {
    "docs/product/orchestrator-prd.md": PRD_PATH,
    "docs/architecture/orchestrator-target-architecture.md": ARCHITECTURE_PATH,
    "docs/roadmap/orchestrator-roadmap.md": ROADMAP_PATH,
    "docs/plans/orchestrator-implementation-plan.md": IMPLEMENTATION_PLAN_PATH,
    "docs/plans/local-ai-runtime-0.2-work-items.json": WORK_ITEMS_PATH,
    "docs/backlog/orchestrator-task-list.md": BACKLOG_PATH,
    "docs/specs/acceptance-and-gates.md": ACCEPTANCE_PATH,
}


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=60,
        check=False,
    )


def _write_status(tmp_path: Path, mutate) -> Path:
    payload = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    mutate(payload)
    path = tmp_path / "planning-status.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _copy_native_thin_path_evaluation_contracts(root: Path) -> None:
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    evaluation = status["native_thin_path_evaluation"]
    identity = evaluation["contract_identity"]
    assert isinstance(identity, dict)
    contracts = identity["contracts"]
    assert isinstance(contracts, list)
    for entry in contracts:
        assert isinstance(entry, dict)
        relative = entry["path"]
        assert isinstance(relative, str)
        source = REPO_ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


def _refresh_contract_identity_for_tmp_root(root: Path, evaluation: dict[str, object]) -> None:
    identity = evaluation["contract_identity"]
    assert isinstance(identity, dict)
    contracts = identity["contracts"]
    assert isinstance(contracts, list)
    for entry in contracts:
        assert isinstance(entry, dict)
        path = entry["path"]
        assert isinstance(path, str)
        raw = (root / path).read_bytes()
        entry["byte_count"] = len(raw)
        entry["sha256"] = hashlib.sha256(raw).hexdigest()


def _write_terminal_native_thin_path_evaluation_artifacts(
    root: Path,
    evaluation: dict[str, object],
    *,
    decision: str,
) -> dict[str, Path]:
    evidence_root = root / "docs" / "evaluations" / "local-ai-runtime-0.2"
    evidence_root.mkdir(parents=True, exist_ok=True)
    result_path = evidence_root / "results.json"
    decision_path = evidence_root / "decision.json"
    evidence_path = evidence_root / "evidence.json"
    result_ref = result_path.relative_to(root).as_posix()
    decision_ref = decision_path.relative_to(root).as_posix()
    evidence_ref = evidence_path.relative_to(root).as_posix()
    generation_sha256 = "a" * 64
    receipt_sha256 = "b" * 64

    evaluation.update(
        {
            "status": decision,
            "decision": decision,
            "result_ref": result_ref,
            "decision_ref": decision_ref,
            "evidence_ref": evidence_ref,
        }
    )
    result = {
        "schema_version": "NativeThinPathCapabilityResults.v1",
        "baseline_id": "local-ai-runtime-0.2-v3.23",
        "status": decision,
        "decision": decision,
        "contract_output_refs": evaluation["contract_output_refs"],
        "contract_identity": evaluation["contract_identity"],
        "decision_ref": decision_ref,
        "evidence_ref": evidence_ref,
        "execution_condition": {
            "core_generation_policy": "append_only_resume_after_new_generation_q0",
            "core_generation_count": 1,
            "core_generation_sha256": [generation_sha256],
            "q0_only_invalidated_generation_sha256": [],
            "current_qualified_cli_generation_sha256": generation_sha256,
        },
        "core_comparison": {
            "declared_trials": 1,
            "normalized_successes": 1,
            "normalized_failures": 0,
            "normalized_stops": 0,
            "pooled_across_generation_count": 1,
            "pooled_profile_promotion_eligible": False,
            "generation_strata": [
                {
                    "generation_sha256": generation_sha256,
                    "trials": 1,
                    "successes": 1,
                    "failures": 0,
                    "stops": 0,
                    "wall_time_total_seconds": 1.0,
                    "input_tokens": 1,
                    "output_tokens": 1,
                    "variants": [
                        {
                            "variant_id": "thin_codex_native",
                            "trials": 1,
                            "successes": 1,
                            "failures": 0,
                            "stops": 0,
                        }
                    ],
                }
            ],
            "generation_transition_summary": {
                "transition_records": 0,
                "q0_admitted_trial_generations": 1,
                "q0_only_invalidated_generations": 0,
            },
        },
    }
    decision_record = {
        "schema_version": "NativeThinPathCapabilityDecision.v1",
        "baseline_id": "local-ai-runtime-0.2-v3.23",
        "status": decision,
        "decision": decision,
        "contract_identity": evaluation["contract_identity"],
        "result_ref": result_ref,
        "evidence_ref": evidence_ref,
    }
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    decision_path.write_text(
        json.dumps(decision_record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    evidence = {
        "schema_version": "NativeThinPathCapabilityEvidence.v1",
        "baseline_id": "local-ai-runtime-0.2-v3.23",
        "status": decision,
        "decision": decision,
        "contract_identity": evaluation["contract_identity"],
        "result_ref": result_ref,
        "decision_ref": decision_ref,
        "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "decision_sha256": hashlib.sha256(decision_path.read_bytes()).hexdigest(),
        "supporting_records": {
            "generation_lock": {"path": "private-local/lock.json", "sha256": "c" * 64},
            "generation_q0": {"path": "private-local/q0.json", "sha256": "d" * 64},
        },
        "generation_record_projection": [
            {
                "generation_sha256": generation_sha256,
                "lock_record": "generation_lock",
                "q0_record": "generation_q0",
                "q0_state": "passed",
                "selected_for_core": True,
            }
        ],
        "trial_receipts": [
            {
                "path": "private-local/receipt.json",
                "sha256": receipt_sha256,
                "variant_id": "thin_codex_native",
                "normalized_outcome": "succeeded",
                "wall_seconds": 1.0,
                "input_tokens": 1,
                "output_tokens": 1,
            }
        ],
        "generation_trial_projection": [
            {
                "generation_sha256": generation_sha256,
                "receipt_sha256": [receipt_sha256],
            }
        ],
        "evidence_completeness": {
            "core_generation_count": 1,
            "generation_transition_records_present": 0,
            "generation_transition_records_expected": 0,
            "q0_only_invalidated_generation_count": 0,
            "cross_generation_strata_reported": False,
        },
    }
    evidence_path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "result": result_path,
        "decision": decision_path,
        "evidence": evidence_path,
    }


def _verifier_attestation(status_path: Path, current_work_item_id: str) -> dict[str, object]:
    return {
        "command": ["python", "verify-planning-status.py"],
        "exit_code": 0,
        "payload": {
            "status": "pass",
            "status_path": status_path.resolve().as_posix(),
            "status_sha256": hashlib.sha256(status_path.read_bytes()).hexdigest(),
            "selector_policy_path": POLICY_PATH.resolve().as_posix(),
            "selector_policy_sha256": hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest(),
            "baseline_id": "local-ai-runtime-0.2-v3.23",
            "current_work_item_id": current_work_item_id,
        },
        "stderr": "",
    }


def test_planning_verifier_accepts_truthful_candidate_state() -> None:
    completed = _run(str(VERIFIER_PATH))

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["status"] == "pass"
    assert payload["baseline_id"] == "local-ai-runtime-0.2-v3.23"
    assert payload["approval_active"] is False
    assert payload["missing_artifact_count"] == 13
    assert payload["current_work_item_id"] == "LAR-P0A-003"
    work_items = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))["work_items"]
    task_ids = {item["task_id"] for item in work_items}
    assert payload["work_item_count"] == len(work_items) == 65
    assert {
        "LAR-P0A-001",
        "LAR-P0A-REBASELINE-V322",
        "LAR-P0A-REBASELINE-V323",
        "LAR-P0A-EVAL-001",
        "LAR-P0A-EVAL-002",
        "LAR-P1C-007",
        "LAR-P1E-007",
        "LAR-P4-002",
        "LAR-P5-001",
    } <= task_ids


def test_planning_selector_returns_baseline_closure_without_preflight() -> None:
    completed = _run(str(SELECTOR_PATH))

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["next_action"] == "close_baseline_normative_package_first"
    assert payload["current_work_item_id"] == "LAR-P0A-003"
    assert payload["side_effects_performed"] is False
    assert payload["preflight_run"] is False


def test_native_thin_path_evaluation_preserves_v323_and_seals_artifacts() -> None:
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    evaluation = status["native_thin_path_evaluation"]

    assert evaluation["status"] == "preserve_v3_23_semantics"
    assert evaluation["decision"] == "preserve_v3_23_semantics"
    assert status["current_work_item"] == {
        "task_id": "LAR-P0A-003",
        "selector_action": "close_baseline_normative_package_first",
        "status": "ready",
        "reason": "LAR-P0A-002 revalidated the BaselineManifest contract against the frozen v3.23 source and BaselineLineage.v2 while keeping the final manifest absent. Close CanonicalizationPolicy.v1 and Git/Windows path identity contracts without advancing approval.",
    }
    assert evaluation["result_ref"].endswith("native-thin-path-capability-results.v1.json")
    assert evaluation["decision_ref"].endswith("native-thin-path-capability-decision.v1.json")
    assert evaluation["evidence_ref"].endswith("native-thin-path-capability-evidence.v1.json")
    result = json.loads((REPO_ROOT / evaluation["result_ref"]).read_text(encoding="utf-8"))
    assert result["execution_condition"]["core_generation_count"] == 3
    assert len(result["core_comparison"]["generation_strata"]) == 3
    assert result["core_comparison"]["pooled_profile_promotion_eligible"] is False
    assert evaluation["independent_capability_surfaces"] == [
        "codex_cli_execution_interface",
        "codex_app_server_client_protocol",
        "codex_sdk_execution_interface",
        "codex_managed_worktree_isolation",
        "codex_automations_scheduling",
    ]
    assert "sampled_downstream_outcome" in evaluation["required_metrics"]
    assert "censored_or_unknown_downstream_outcome_remains_in_denominator" in evaluation[
        "hard_promotion_rules"
    ]
    identity = evaluation["contract_identity"]
    assert identity["snapshot"] == {
        "commit": "6fd6cd54037f17e44192bc272306b137def7f8a4",
        "tree": "11c8ab770769b3aeff5c111063a316e712fa7241",
    }
    for contract in identity["contracts"]:
        path = REPO_ROOT / contract["path"]
        raw = path.read_bytes()
        assert len(raw) == contract["byte_count"]
        assert hashlib.sha256(raw).hexdigest() == contract["sha256"]


def test_terminal_generation_projection_covers_every_core_receipt() -> None:
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    evaluation = status["native_thin_path_evaluation"]
    result = json.loads(
        (REPO_ROOT / evaluation["result_ref"]).read_text(encoding="utf-8")
    )
    evidence = json.loads(
        (REPO_ROOT / evaluation["evidence_ref"]).read_text(encoding="utf-8")
    )
    verify_projection = runpy.run_path(str(VERIFIER_PATH))[
        "_verify_terminal_generation_projection"
    ]
    failures: list[str] = []

    verify_projection(result, evidence, failures)

    assert failures == []
    evidence["generation_trial_projection"][0]["receipt_sha256"].pop()
    verify_projection(result, evidence, failures)
    assert (
        "terminal native thin-path evidence generation projection must cover each trial receipt exactly once"
        in failures
    )
    evidence = json.loads(
        (REPO_ROOT / evaluation["evidence_ref"]).read_text(encoding="utf-8")
    )
    evidence["generation_trial_projection"][0]["receipt_sha256"][0] = {"bad": True}
    failures.clear()
    verify_projection(result, evidence, failures)
    assert (
        "terminal native thin-path evidence generation projection must bind a core generation to receipt hashes"
        in failures
    )

    evidence = json.loads(
        (REPO_ROOT / evaluation["evidence_ref"]).read_text(encoding="utf-8")
    )
    evidence["generation_trial_projection"].insert(
        0,
        {
            "generation_sha256": evidence["generation_trial_projection"][0][
                "generation_sha256"
            ],
            "receipt_sha256": [],
        },
    )
    failures.clear()
    verify_projection(result, evidence, failures)
    assert (
        "terminal native thin-path evidence generation projection must cover each core generation exactly once"
        in failures
    )

    evidence = json.loads(
        (REPO_ROOT / evaluation["evidence_ref"]).read_text(encoding="utf-8")
    )
    evidence["trial_receipts"][0]["wall_seconds"] = True
    failures.clear()
    verify_projection(result, evidence, failures)
    assert (
        "terminal native thin-path evidence trial receipts must contain private-local locators, typed non-negative metrics and SHA-256 identities"
        in failures
    )

    evidence = json.loads(
        (REPO_ROOT / evaluation["evidence_ref"]).read_text(encoding="utf-8")
    )
    evidence["supporting_records"]["generation_transition_001"]["path"] = (
        "../transition.json"
    )
    failures.clear()
    verify_projection(result, evidence, failures)
    assert (
        "terminal native thin-path supporting generation transition is invalid: generation_transition_001"
        in failures
    )


def test_terminal_native_thin_path_evaluation_requires_cross_referenced_json_artifacts(
    tmp_path: Path,
) -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    verify_evaluation = namespace["_verify_native_thin_path_evaluation"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    evaluation = status["native_thin_path_evaluation"]
    package = status["normative_package"]
    assert isinstance(evaluation, dict)
    assert isinstance(package, dict)
    _copy_native_thin_path_evaluation_contracts(tmp_path)
    _write_terminal_native_thin_path_evaluation_artifacts(
        tmp_path,
        evaluation,
        decision="preserve_v3_23_semantics",
    )
    failures: list[str] = []

    verify_evaluation(
        root=tmp_path,
        evaluation=evaluation,
        package_state=package,
        current_work={
            "task_id": "LAR-P0A-002",
            "selector_action": "close_baseline_normative_package_first",
        },
        failures=failures,
    )

    assert not failures


def test_terminal_native_thin_path_evaluation_rejects_missing_or_mismatched_artifacts(
    tmp_path: Path,
) -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    verify_evaluation = namespace["_verify_native_thin_path_evaluation"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    evaluation = status["native_thin_path_evaluation"]
    package = status["normative_package"]
    assert isinstance(evaluation, dict)
    assert isinstance(package, dict)
    _copy_native_thin_path_evaluation_contracts(tmp_path)
    artifacts = _write_terminal_native_thin_path_evaluation_artifacts(
        tmp_path,
        evaluation,
        decision="preserve_v3_23_semantics",
    )
    decision_record = json.loads(artifacts["decision"].read_text(encoding="utf-8"))
    decision_record["decision"] = "supersede_required"
    artifacts["decision"].write_text(
        json.dumps(decision_record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    evidence = json.loads(artifacts["evidence"].read_text(encoding="utf-8"))
    evidence["decision_sha256"] = hashlib.sha256(
        artifacts["decision"].read_bytes()
    ).hexdigest()
    artifacts["evidence"].write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    failures: list[str] = []

    verify_evaluation(
        root=tmp_path,
        evaluation=evaluation,
        package_state=package,
        current_work={
            "task_id": "LAR-P0A-002",
            "selector_action": "close_baseline_normative_package_first",
        },
        failures=failures,
    )

    assert (
        "terminal native thin-path decision artifact must match planning status and decision"
        in failures
    )
    artifacts["result"].unlink()
    failures.clear()

    verify_evaluation(
        root=tmp_path,
        evaluation=evaluation,
        package_state=package,
        current_work={
            "task_id": "LAR-P0A-002",
            "selector_action": "close_baseline_normative_package_first",
        },
        failures=failures,
    )

    assert "terminal native_thin_path_evaluation.result_ref artifact does not exist" in failures
    artifacts["result"].write_text("[]\n", encoding="utf-8")
    failures.clear()

    verify_evaluation(
        root=tmp_path,
        evaluation=evaluation,
        package_state=package,
        current_work={
            "task_id": "LAR-P0A-002",
            "selector_action": "close_baseline_normative_package_first",
        },
        failures=failures,
    )

    assert any(
        "terminal native_thin_path_evaluation.result_ref must be a readable JSON object"
        in failure
        for failure in failures
    )
    _write_terminal_native_thin_path_evaluation_artifacts(
        tmp_path,
        evaluation,
        decision="preserve_v3_23_semantics",
    )
    evidence = json.loads(artifacts["evidence"].read_text(encoding="utf-8"))
    evidence["result_sha256"] = "0" * 64
    artifacts["evidence"].write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    failures.clear()

    verify_evaluation(
        root=tmp_path,
        evaluation=evaluation,
        package_state=package,
        current_work={
            "task_id": "LAR-P0A-002",
            "selector_action": "close_baseline_normative_package_first",
        },
        failures=failures,
    )

    assert (
        "terminal native thin-path evidence artifact result_sha256 must match result bytes"
        in failures
    )


@pytest.mark.parametrize(
    ("mutate_contract", "expected_failure"),
    [
        (
            lambda root, evaluation: (root / evaluation["contract_output_refs"][0]).unlink(),
            "native_thin_path_evaluation sealed contract does not exist",
        ),
        (
            lambda root, evaluation: (root / evaluation["contract_output_refs"][1]).write_text(
                "[]\n", encoding="utf-8"
            ),
            "native_thin_path_evaluation sealed contract must be a readable JSON object",
        ),
        (
            lambda root, evaluation: (root / evaluation["contract_output_refs"][2]).write_text(
                '{"schema_version":"NativeThinPathEvidenceSchema.v1","schema_version":"duplicate"}\n',
                encoding="utf-8",
            ),
            "native_thin_path_evaluation sealed contract must be a readable JSON object",
        ),
    ],
)
def test_native_thin_path_evaluation_rejects_missing_or_malformed_sealed_contracts(
    tmp_path: Path,
    mutate_contract,
    expected_failure: str,
) -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    verify_evaluation = namespace["_verify_native_thin_path_evaluation"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    evaluation = status["native_thin_path_evaluation"]
    package = status["normative_package"]
    assert isinstance(evaluation, dict)
    assert isinstance(package, dict)
    _copy_native_thin_path_evaluation_contracts(tmp_path)
    mutate_contract(tmp_path, evaluation)
    failures: list[str] = []

    verify_evaluation(
        root=tmp_path,
        evaluation=evaluation,
        package_state=package,
        current_work={
            "task_id": "LAR-P0A-EVAL-002",
            "selector_action": "run_native_thin_path_evaluation_first",
        },
        failures=failures,
    )

    assert any(expected_failure in failure for failure in failures)


def test_native_thin_path_evaluation_rejects_contract_hash_drift_and_cross_reference_drift(
    tmp_path: Path,
) -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    verify_evaluation = namespace["_verify_native_thin_path_evaluation"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    evaluation = status["native_thin_path_evaluation"]
    package = status["normative_package"]
    assert isinstance(evaluation, dict)
    assert isinstance(package, dict)
    _copy_native_thin_path_evaluation_contracts(tmp_path)
    task_manifest_path = tmp_path / evaluation["contract_output_refs"][1]
    manifest = json.loads(task_manifest_path.read_text(encoding="utf-8"))
    manifest["contract_refs"]["evaluation_contract"] = "docs/evaluations/local-ai-runtime-0.2/wrong.json"
    task_manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    failures: list[str] = []

    verify_evaluation(
        root=tmp_path,
        evaluation=evaluation,
        package_state=package,
        current_work={
            "task_id": "LAR-P0A-EVAL-002",
            "selector_action": "run_native_thin_path_evaluation_first",
        },
        failures=failures,
    )

    assert "native_thin_path_evaluation.contract_identity contract byte_count must match file bytes" in failures
    assert any("sealed contract must preserve contract_refs" in failure for failure in failures)


def test_native_thin_path_evaluation_rejects_semantic_contract_drift_even_with_refreshed_identity(
    tmp_path: Path,
) -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    verify_evaluation = namespace["_verify_native_thin_path_evaluation"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    evaluation = status["native_thin_path_evaluation"]
    package = status["normative_package"]
    assert isinstance(evaluation, dict)
    assert isinstance(package, dict)
    _copy_native_thin_path_evaluation_contracts(tmp_path)
    capability_contract_path = tmp_path / evaluation["contract_output_refs"][0]
    capability_contract = json.loads(capability_contract_path.read_text(encoding="utf-8"))
    capability_contract["generation_and_q0_rules"]["new_generation_triggers"].remove(
        "automation_or_external_effect_change"
    )
    capability_contract_path.write_text(
        json.dumps(capability_contract, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _refresh_contract_identity_for_tmp_root(tmp_path, evaluation)
    failures: list[str] = []

    verify_evaluation(
        root=tmp_path,
        evaluation=evaluation,
        package_state=package,
        current_work={
            "task_id": "LAR-P0A-EVAL-002",
            "selector_action": "run_native_thin_path_evaluation_first",
        },
        failures=failures,
    )

    assert (
        "native thin-path evaluation contract must preserve capability-generation triggers and Q0 followup"
        in failures
    )


@pytest.mark.parametrize(
    ("artifact_key", "identity_error"),
    [
        (
            "result",
            "terminal native thin-path results artifact must bind the exact contract_identity",
        ),
        (
            "decision",
            "terminal native thin-path decision artifact must bind the exact contract_identity",
        ),
        (
            "evidence",
            "terminal native thin-path evidence artifact must bind the exact contract_identity",
        ),
    ],
)
def test_terminal_native_thin_path_evaluation_rejects_mismatched_contract_identity(
    tmp_path: Path,
    artifact_key: str,
    identity_error: str,
) -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    verify_evaluation = namespace["_verify_native_thin_path_evaluation"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    evaluation = status["native_thin_path_evaluation"]
    package = status["normative_package"]
    assert isinstance(evaluation, dict)
    assert isinstance(package, dict)
    _copy_native_thin_path_evaluation_contracts(tmp_path)
    artifacts = _write_terminal_native_thin_path_evaluation_artifacts(
        tmp_path,
        evaluation,
        decision="preserve_v3_23_semantics",
    )
    artifact = json.loads(artifacts[artifact_key].read_text(encoding="utf-8"))
    artifact["contract_identity"] = {"contract_set_id": "wrong"}
    artifacts[artifact_key].write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    evidence = json.loads(artifacts["evidence"].read_text(encoding="utf-8"))
    if artifact_key == "result":
        evidence["result_sha256"] = hashlib.sha256(artifacts["result"].read_bytes()).hexdigest()
    elif artifact_key == "decision":
        evidence["decision_sha256"] = hashlib.sha256(
            artifacts["decision"].read_bytes()
        ).hexdigest()
    artifacts["evidence"].write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    failures: list[str] = []

    verify_evaluation(
        root=tmp_path,
        evaluation=evaluation,
        package_state=package,
        current_work={
            "task_id": "LAR-P0A-002",
            "selector_action": "close_baseline_normative_package_first",
        },
        failures=failures,
    )

    assert identity_error in failures


@pytest.mark.parametrize(
    ("status_value", "contract_identity", "expected_failure"),
    [
        (
            "contract_pending",
            {"unexpected": "identity"},
            "contract_pending native_thin_path_evaluation.contract_identity must remain null",
        ),
        (
            "execution_pending",
            None,
            "execution or terminal native_thin_path_evaluation requires contract_identity",
        ),
    ],
)
def test_native_thin_path_evaluation_enforces_pending_contract_identity_state(
    status_value: str,
    contract_identity: object,
    expected_failure: str,
) -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    verify_evaluation = namespace["_verify_native_thin_path_evaluation"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    evaluation = status["native_thin_path_evaluation"]
    package = status["normative_package"]
    assert isinstance(evaluation, dict)
    assert isinstance(package, dict)
    evaluation["status"] = status_value
    evaluation["contract_identity"] = contract_identity
    failures: list[str] = []

    verify_evaluation(
        root=REPO_ROOT,
        evaluation=evaluation,
        package_state=package,
        current_work={
            "task_id": "LAR-P0A-EVAL-001"
            if status_value == "contract_pending"
            else "LAR-P0A-EVAL-002",
            "selector_action": "run_native_thin_path_evaluation_first",
        },
        failures=failures,
    )

    assert expected_failure in failures


def test_verifier_rejects_native_thin_path_semantic_change_without_successor_action(
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        evaluation = payload["native_thin_path_evaluation"]
        current = payload["current_work_item"]
        assert isinstance(evaluation, dict)
        assert isinstance(current, dict)
        evaluation.update(
            {
                "status": "supersede_required",
                "decision": "supersede_required",
                "result_ref": "docs/evaluations/local-ai-runtime-0.2/native-thin-path-capability-results.v1.json",
                "decision_ref": "docs/evaluations/local-ai-runtime-0.2/native-thin-path-capability-decision.v1.json",
                "evidence_ref": "docs/evaluations/local-ai-runtime-0.2/native-thin-path-capability-evidence.v1.json",
            }
        )
        current.update(
            {
                "task_id": "LAR-P0A-EVAL-002",
                "selector_action": "run_native_thin_path_evaluation_first",
                "status": "supersede_required",
            }
        )

    status_path = _write_status(tmp_path, mutate)
    completed = _run(str(VERIFIER_PATH), "--status-path", str(status_path))

    assert completed.returncode == 1
    assert "create_successor_candidate_first" in completed.stderr


def test_selector_routes_semantic_change_to_successor_candidate(tmp_path: Path) -> None:
    namespace = runpy.run_path(str(SELECTOR_PATH))
    select_next_work = namespace["select_next_work"]

    def mutate(payload: dict[str, object]) -> None:
        evaluation = payload["native_thin_path_evaluation"]
        current = payload["current_work_item"]
        assert isinstance(evaluation, dict)
        assert isinstance(current, dict)
        evaluation.update(
            {
                "status": "narrow_profile_or_adapter_candidate",
                "decision": "narrow_profile_or_adapter_candidate",
                "result_ref": "docs/evaluations/local-ai-runtime-0.2/native-thin-path-capability-results.v1.json",
                "decision_ref": "docs/evaluations/local-ai-runtime-0.2/native-thin-path-capability-decision.v1.json",
                "evidence_ref": "docs/evaluations/local-ai-runtime-0.2/native-thin-path-capability-evidence.v1.json",
            }
        )
        current.update(
            {
                "task_id": "LAR-P0A-EVAL-002",
                "selector_action": "create_successor_candidate_first",
                "status": "narrow_profile_or_adapter_candidate",
            }
        )

    status_path = _write_status(tmp_path, mutate)
    select_next_work.__globals__["_run_verifier"] = lambda _root, path, _verifier: {
        **_verifier_attestation(path, "LAR-P0A-EVAL-002"),
        "payload": {
            **_verifier_attestation(path, "LAR-P0A-EVAL-002")["payload"],
            "baseline_id": "local-ai-runtime-0.2-v3.23",
        },
    }

    payload = select_next_work(
        repo_root=REPO_ROOT,
        status_path=status_path,
        policy_path=POLICY_PATH,
        verifier_path=VERIFIER_PATH,
    )

    assert payload["next_action"] == "create_successor_candidate_first"
    assert payload["current_work_item_id"] == "LAR-P0A-EVAL-002"


def test_selector_policy_and_implementation_keep_semantic_change_priority_in_sync() -> None:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    selector = runpy.run_path(str(SELECTOR_PATH))

    expected = (
        "native_thin_path_semantic_change_requires_successor",
        "create_successor_candidate_first",
    )
    assert policy["selection_order"][1]["condition_id"] == expected[0]
    assert policy["selection_order"][1]["next_action"] == expected[1]
    assert selector["EXPECTED_SELECTOR_STEPS"][1] == expected


def test_baseline_manifest_component_self_test_is_green_without_final_manifest() -> None:
    completed = _run(
        str(BASELINE_PACKAGE_VERIFIER_PATH), "--component", "manifest", "--self-test"
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload == {
        "bound_artifact_count": 2,
        "byte_negative_fixture_count": 8,
        "component": "manifest",
        "final_manifest_exists": False,
        "narrative_specification_id": "local-ai-runtime-0.2-v3.23",
        "positive_fixture_count": 1,
        "schema_version": "BaselineManifest.v1",
        "status": "pass",
        "structural_negative_fixture_count": 7,
    }
    assert BASELINE_MANIFEST_SCHEMA_PATH.is_file()
    assert BASELINE_MANIFEST_FIXTURE_PATH.is_file()
    assert not (
        BASELINE_MANIFEST_SCHEMA_PATH.parent / "BaselineManifest.v1.json"
    ).exists()


def test_baseline_manifest_fixture_binding_rejects_identity_or_byte_drift(
    tmp_path: Path,
) -> None:
    namespace = runpy.run_path(str(BASELINE_PACKAGE_VERIFIER_PATH))
    verify_bindings = namespace["_verify_fixture_bindings"]
    failure_type = namespace["ValidationFailure"]
    fixture = json.loads(BASELINE_MANIFEST_FIXTURE_PATH.read_text(encoding="utf-8"))
    valid_manifest = fixture["valid_manifest"]

    for entry in valid_manifest["payload"]["artifacts"]:
        source = REPO_ROOT / entry["path"]
        target = tmp_path / entry["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    verify_bindings(valid_manifest, tmp_path)

    stale_manifest = json.loads(json.dumps(valid_manifest))
    stale_manifest["payload"]["narrative_specification_id"] = (
        "local-ai-runtime-0.2-v3.22"
    )
    with pytest.raises(failure_type) as stale_failure:
        verify_bindings(stale_manifest, tmp_path)
    assert stale_failure.value.reason == "fixture_binding_mismatch"

    source_entry = valid_manifest["payload"]["artifacts"][0]
    source_path = tmp_path / source_entry["path"]
    raw = source_path.read_bytes()
    source_path.write_bytes(raw[:-1] + b"x\n")
    with pytest.raises(failure_type) as byte_failure:
        verify_bindings(valid_manifest, tmp_path)
    assert byte_failure.value.reason == "bound_artifact_identity_mismatch"


def test_baseline_verifier_skeleton_fails_closed_for_full_package() -> None:
    completed = _run(str(BASELINE_PACKAGE_VERIFIER_PATH), "--json")

    assert completed.returncode == 3
    payload = json.loads(completed.stdout)
    assert payload["status"] == "incomplete"
    assert payload["reason"] == "standalone_verifier_not_frozen"
    assert payload["implemented_components"] == ["manifest_self_test"]


def test_baseline_manifest_validator_rejects_duplicate_and_cyclic_entries() -> None:
    namespace = runpy.run_path(str(BASELINE_PACKAGE_VERIFIER_PATH))
    validate_manifest = namespace["validate_manifest"]
    failure_type = namespace["ValidationFailure"]
    fixture = json.loads(BASELINE_MANIFEST_FIXTURE_PATH.read_text(encoding="utf-8"))
    mutations = namespace["_structural_mutations"]()

    for case in fixture["structural_negative_cases"]:
        candidate = json.loads(json.dumps(fixture["valid_manifest"]))
        mutations[case["mutation"]](candidate)
        with pytest.raises(failure_type) as captured:
            validate_manifest(candidate)
        assert captured.value.reason == case["expected_reason"], case["case_id"]


def test_baseline_byte_validator_rejects_every_declared_byte_mutation() -> None:
    namespace = runpy.run_path(str(BASELINE_PACKAGE_VERIFIER_PATH))
    validate_bytes = namespace["validate_normative_bytes"]
    mutate_bytes = namespace["_mutate_bytes"]
    failure_type = namespace["ValidationFailure"]
    fixture = json.loads(BASELINE_MANIFEST_FIXTURE_PATH.read_text(encoding="utf-8"))
    raw = BASELINE_MANIFEST_FIXTURE_PATH.read_bytes()

    for case in fixture["byte_negative_cases"]:
        with pytest.raises(failure_type) as captured:
            validate_bytes(mutate_bytes(raw, case["mutation"]), case["case_id"])
        assert captured.value.reason == case["expected_reason"], case["case_id"]


def test_baseline_bytes_match_planning_identity() -> None:
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    raw = BASELINE_PATH.read_bytes()

    assert len(raw) == status["baseline_candidate"]["byte_count"] == 188325
    assert hashlib.sha256(raw).hexdigest() == status["baseline_candidate"]["sha256"]
    assert hashlib.sha256(raw).hexdigest() == "80562322ebc744eda2a87a17c45f73a11982f4947c9d10e8628bb6f73ee9d5c6"
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
    assert b"\r" not in raw


def test_stable_baseline_entry_is_non_normative_and_targets_frozen_candidate() -> None:
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    entry = status["baseline_entry"]
    baseline = status["baseline_candidate"]
    raw = BASELINE_ENTRY_PATH.read_bytes()
    rendered = raw.decode("utf-8")

    assert entry == {
        "path": "docs/specs/local-ai-runtime-0.2-baseline-candidate.md",
        "role": "non_normative_navigation",
        "target_baseline_id": baseline["id"],
        "target_path": baseline["path"],
        "target_byte_count": baseline["byte_count"],
        "target_sha256": baseline["sha256"],
        "approval_input": False,
        "maximum_byte_count": 4096,
        "byte_count": 2873,
        "sha256": "843ce546d252a37f9622b330b51370968cb5a0b2339d94d90c2e836b1c187963",
    }
    assert len(raw) <= entry["maximum_byte_count"]
    assert len(raw) == entry["byte_count"]
    assert hashlib.sha256(raw).hexdigest() == entry["sha256"]
    for marker in (
        "role=non_normative_navigation",
        "approval_input=false",
        baseline["id"],
        baseline["path"],
        baseline["sha256"],
        "not a narrative specification",
        "BaselineManifest.v1",
        "BaselineApprovalRecord",
        "preserve_v3_23_semantics",
        "LAR-P0A-003",
        "close_baseline_normative_package_first",
    ):
        assert marker in rendered


def test_verifier_rejects_a_baseline_entry_as_an_approval_input(tmp_path: Path) -> None:
    def mutate(payload: dict[str, object]) -> None:
        entry = payload["baseline_entry"]
        assert isinstance(entry, dict)
        entry["approval_input"] = True

    status_path = _write_status(tmp_path, mutate)

    completed = _run(str(VERIFIER_PATH), "--status-path", str(status_path))

    assert completed.returncode == 1
    assert "baseline_entry.approval_input must remain false" in completed.stderr


def test_verifier_rejects_a_baseline_entry_with_a_drifted_target_hash(tmp_path: Path) -> None:
    def mutate(payload: dict[str, object]) -> None:
        entry = payload["baseline_entry"]
        assert isinstance(entry, dict)
        entry["target_sha256"] = "0" * 64

    status_path = _write_status(tmp_path, mutate)

    completed = _run(str(VERIFIER_PATH), "--status-path", str(status_path))

    assert completed.returncode == 1
    assert "baseline_entry.target_sha256 must match baseline_candidate.sha256" in completed.stderr


def test_verifier_rejects_an_oversized_baseline_entry(tmp_path: Path) -> None:
    verify_entry = runpy.run_path(str(VERIFIER_PATH))["_verify_baseline_entry"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    entry = status["baseline_entry"]
    entry = dict(entry)
    target = tmp_path / entry["path"]
    target.parent.mkdir(parents=True)
    oversized = b"x" * entry["maximum_byte_count"] + b"\n"
    target.write_bytes(oversized)
    entry["byte_count"] = len(oversized)
    entry["sha256"] = hashlib.sha256(oversized).hexdigest()
    failures: list[str] = []

    verify_entry(tmp_path, entry, status["baseline_candidate"], failures)

    assert "baseline entry exceeds its maximum_byte_count" in failures


def test_verifier_rejects_baseline_entry_byte_drift(tmp_path: Path) -> None:
    def mutate(payload: dict[str, object]) -> None:
        entry = payload["baseline_entry"]
        assert isinstance(entry, dict)
        entry["sha256"] = "0" * 64

    status_path = _write_status(tmp_path, mutate)

    completed = _run(str(VERIFIER_PATH), "--status-path", str(status_path))

    assert completed.returncode == 1
    assert "baseline entry SHA-256 mismatch" in completed.stderr


def test_baseline_entry_is_excluded_from_normative_inventory() -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    verify_exclusion = namespace["_verify_baseline_entry_inventory_exclusion"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    entry = status["baseline_entry"]
    failures: list[str] = []

    verify_exclusion(entry, inventory, failures)
    assert failures == []

    inventory["required_artifacts"][0]["path"] = entry["path"]
    verify_exclusion(entry, inventory, failures)
    assert any("must not be a normative artifact" in failure for failure in failures)

    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    inventory["candidate_source"]["path"] = entry["path"]
    failures = []
    verify_exclusion(entry, inventory, failures)
    assert "baseline entry must not be the inventory candidate source" in failures


def test_selector_policy_requires_the_stable_baseline_entry() -> None:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    assert policy["required_entrypoints"] == [
        "docs/architecture/planning-status.json",
        "docs/specs/local-ai-runtime-0.2-baseline-candidate.md",
        "docs/specs/local-ai-runtime-0.2-v3.23-baseline-candidate.md",
        "docs/specs/local-ai-runtime-0.2-normative-package.json",
        "docs/plans/local-ai-runtime-0.2-work-items.json",
        "scripts/verify-planning-status.py",
        "scripts/select-next-work.py",
        "scripts/governance/preflight.ps1",
    ]


def test_high_risk_contracts_are_projected_into_execution_plans() -> None:
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    doc_contracts = {
        item["path"]: set(item["required_strings"])
        for item in status["doc_contracts"]
    }

    for relative_path, path in HIGH_RISK_PROJECTION_PATHS.items():
        missing_requirements = HIGH_RISK_PROJECTION_TOKENS - doc_contracts.get(
            relative_path, set()
        )
        assert not missing_requirements, (
            f"{relative_path} doc contract omits: {sorted(missing_requirements)}"
        )

        rendered = path.read_text(encoding="utf-8")
        missing_projection = {
            token for token in HIGH_RISK_PROJECTION_TOKENS if token not in rendered
        }
        assert not missing_projection, (
            f"{relative_path} content omits: {sorted(missing_projection)}"
        )


def test_source_layout_contract_is_projected_into_all_execution_surfaces() -> None:
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    doc_contracts = {
        item["path"]: set(item["required_strings"])
        for item in status["doc_contracts"]
    }

    for relative_path, path in SOURCE_LAYOUT_PROJECTION_PATHS.items():
        missing_requirements = SOURCE_LAYOUT_PROJECTION_TOKENS - doc_contracts.get(
            relative_path, set()
        )
        assert not missing_requirements, (
            f"{relative_path} doc contract omits: {sorted(missing_requirements)}"
        )

        rendered = path.read_text(encoding="utf-8")
        missing_projection = {
            token for token in SOURCE_LAYOUT_PROJECTION_TOKENS if token not in rendered
        }
        assert not missing_projection, (
            f"{relative_path} content omits: {sorted(missing_projection)}"
        )


def test_work_item_graph_declares_closed_runtime_source_layout() -> None:
    payload = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "local_ai_runtime_work_items.v3"
    assert payload["runtime_source_layout"] == {
        "source_root": "runtime/local-ai-runtime/src/local_ai_runtime/",
        "approved_root_files": ["__init__.py", "__main__.py"],
        "approved_subpackages": [
            "contracts",
            "kernel",
            "qualification",
            "storage",
            "execution",
            "recovery",
            "git_local",
            "operations",
            "compat",
        ],
        "required_source_owners": {
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
        },
    }


def test_work_item_graph_rejects_unapproved_runtime_source_package() -> None:
    verify_work_items = runpy.run_path(str(VERIFIER_PATH))["_verify_work_items"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    work_items = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))
    evidence_task = next(
        item for item in work_items["work_items"] if item["task_id"] == "LAR-P1E-005"
    )
    evidence_task["scope"]["primary_files"][0] = (
        "runtime/local-ai-runtime/src/local_ai_runtime/evidence/artifacts.py"
    )
    failures: list[str] = []

    verify_work_items(
        work_items,
        status["baseline_candidate"],
        status["current_active_queue"],
        status["current_work_item"],
        failures,
    )

    assert "LAR-P1E-005 uses unapproved runtime source package: evidence" in failures


def test_work_item_graph_rejects_unapproved_runtime_source_root_module() -> None:
    verify_work_items = runpy.run_path(str(VERIFIER_PATH))["_verify_work_items"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    work_items = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))
    evidence_task = next(
        item for item in work_items["work_items"] if item["task_id"] == "LAR-P1E-005"
    )
    evidence_task["scope"]["primary_files"][0] = (
        "runtime/local-ai-runtime/src/local_ai_runtime/evidence.py"
    )
    failures: list[str] = []

    verify_work_items(
        work_items,
        status["baseline_candidate"],
        status["current_active_queue"],
        status["current_work_item"],
        failures,
    )

    assert "LAR-P1E-005 uses unapproved runtime source root file: evidence.py" in failures


def test_work_item_graph_rejects_duplicate_runtime_source_owner() -> None:
    verify_work_items = runpy.run_path(str(VERIFIER_PATH))["_verify_work_items"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    work_items = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))
    contracts_task = next(
        item for item in work_items["work_items"] if item["task_id"] == "LAR-P1A-002"
    )
    contracts_task["scope"]["primary_files"].append(
        "runtime/local-ai-runtime/src/local_ai_runtime/contracts/__init__.py"
    )
    failures: list[str] = []

    verify_work_items(
        work_items,
        status["baseline_candidate"],
        status["current_active_queue"],
        status["current_work_item"],
        failures,
    )

    assert any(
        "runtime source path must have exactly one owner" in failure
        and "contracts/__init__.py" in failure
        for failure in failures
    )


def test_runtime_source_tree_rejects_unapproved_root_module(tmp_path: Path) -> None:
    verify_source_tree = runpy.run_path(str(VERIFIER_PATH))[
        "_verify_runtime_source_tree"
    ]
    source_root = (
        tmp_path / "runtime" / "local-ai-runtime" / "src" / "local_ai_runtime"
    )
    source_root.mkdir(parents=True)
    (source_root / "__init__.py").write_text("", encoding="utf-8")
    (source_root / "evidence.py").write_text("", encoding="utf-8")
    failures: list[str] = []

    verify_source_tree(
        tmp_path,
        {
            "source_root": "runtime/local-ai-runtime/src/local_ai_runtime/",
            "approved_root_files": ["__init__.py", "__main__.py"],
            "approved_subpackages": [
                "contracts",
                "kernel",
                "qualification",
                "storage",
                "execution",
                "recovery",
                "git_local",
                "operations",
                "compat",
            ],
            "required_source_owners": {
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
            },
        },
        failures,
    )

    assert "runtime source tree contains unapproved root file: evidence.py" in failures


def test_work_item_graph_rejects_malformed_machine_fields() -> None:
    verify_work_items = runpy.run_path(str(VERIFIER_PATH))["_verify_work_items"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    work_items = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))
    work_items["schema_version"] = "unknown"
    work_items["verification_profiles"] = {"planning": []}
    current = work_items["work_items"][0]
    current["phase"] = "P9"
    current["priority"] = "zero"
    current["acceptance"].append(current["acceptance"][0])
    failures: list[str] = []

    verify_work_items(
        work_items,
        status["baseline_candidate"],
        status["current_active_queue"],
        status["current_work_item"],
        failures,
    )

    assert any("schema_version" in failure for failure in failures)
    assert any("exactly planning and new_runtime" in failure for failure in failures)
    assert any("phase must match its task ID" in failure for failure in failures)
    assert any("priority must be a non-negative integer" in failure for failure in failures)
    assert any("acceptance must not contain duplicates" in failure for failure in failures)


def test_normative_byte_validator_rejects_non_lf_unicode_boundaries() -> None:
    validator = runpy.run_path(str(VERIFIER_PATH))["_verify_normative_bytes"]

    for forbidden in ("\u2028", "\u2029", "\u200b", "\uffff"):
        failures: list[str] = []
        validator(f"# candidate{forbidden}\n".encode(), "candidate", failures)
        assert failures, f"U+{ord(forbidden):04X} unexpectedly passed"


def test_history_extractor_enforces_message_boundaries_and_no_replace(
    tmp_path: Path,
) -> None:
    namespace = runpy.run_path(str(HISTORY_EXTRACTOR_PATH))
    extract_body = namespace["_extract_body"]
    publish_or_verify = namespace["_publish_or_verify"]
    specs = namespace["SOURCE_SPECS"]

    wrapped = {
        "type": "response_item",
        "payload": {
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "output_text",
                    "text": "<proposed_plan>\nbody\n</proposed_plan>",
                }
            ],
        },
    }
    body, source = extract_body(wrapped, specs[0])
    assert body == "body\n"
    assert source["excluded_prefix_utf8_bytes"] == len("<proposed_plan>\n")
    assert source["excluded_suffix_utf8_bytes"] == len("</proposed_plan>")

    path = tmp_path / "archive.md"
    publish_or_verify(path, b"body\n", False)
    publish_or_verify(path, b"body\n", False)
    with pytest.raises(ValueError, match="will not be overwritten"):
        publish_or_verify(path, b"changed\n", False)


def test_history_extractor_rejects_ambiguous_or_changed_source_shape() -> None:
    namespace = runpy.run_path(str(HISTORY_EXTRACTOR_PATH))
    extract_body = namespace["_extract_body"]
    specs = namespace["SOURCE_SPECS"]

    malformed = {
        "type": "response_item",
        "payload": {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "body\n"}],
        },
    }
    with pytest.raises(ValueError, match="exact plan envelope"):
        extract_body(malformed, specs[0])

    duplicate_title = {
        "type": "response_item",
        "payload": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": namespace["V318_TITLE"] + "\n" + namespace["V318_TITLE"] + "\n",
                }
            ],
        },
    }
    with pytest.raises(ValueError, match="exactly one v3.18 title"):
        extract_body(duplicate_title, specs[2])


def test_historical_archives_match_source_record_and_planning_verifier() -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    verify_record = namespace["_verify_historical_source_record"]
    record_path = (
        REPO_ROOT
        / "docs"
        / "specs"
        / "local-ai-runtime-0.2"
        / "history"
        / "HistoricalSourceArchive.v1.json"
    )
    record = json.loads(record_path.read_text(encoding="utf-8"))
    failures: list[str] = []

    verify_record(REPO_ROOT, record, failures)

    assert failures == []
    assert [item["byte_count"] for item in record["archives"]] == [32825, 66328, 43908]
    assert [item["sha256"] for item in record["archives"]] == [
        "a285f5f421a8ccd4debd8794609a2aa0eb07bb1bf651c2467a95f7cad25a5f81",
        "6924ba562dda8e69274eb80fef9e3a9699eb493570ee08330fcad5ec4bc3baa5",
        "8da5aa20fb44d95503e443822163397a2aa1df590e1916d1a5a10a6c24ea06b7",
    ]


def test_superseded_v319_archive_matches_declared_lineage() -> None:
    verifier = runpy.run_path(str(VERIFIER_PATH))["_verify_lineage_archives"]
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    failures: list[str] = []

    verifier(REPO_ROOT, inventory["lineage"], failures)

    assert failures == []

    archived = next(
        item
        for item in inventory["lineage"]["superseded_candidates"]
        if item["id"] == "local-ai-runtime-0.2-v3.19"
    )
    archived["sha256"] = "0" * 64
    verifier(REPO_ROOT, inventory["lineage"], failures)
    assert any("v3.19 archive SHA-256 mismatch" in failure for failure in failures)


def test_superseded_v320_archive_matches_declared_lineage() -> None:
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    archived = next(
        item
        for item in inventory["lineage"]["superseded_candidates"]
        if item["id"] == "local-ai-runtime-0.2-v3.20"
    )
    raw = V320_PATH.read_bytes()

    assert len(raw) == archived["byte_count"] == 130890
    assert hashlib.sha256(raw).hexdigest() == archived["sha256"]
    assert archived["sha256"] == "43cb98737daa5d171a9cda2dca49c8f118fb8be92745b4076948d9178e56a130"


def test_inventory_versions_and_manifest_review_order_are_closed() -> None:
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    artifacts = inventory["required_artifacts"]
    by_id = {item["artifact_id"]: item for item in artifacts}
    artifact_ids = [item["artifact_id"] for item in artifacts]

    assert len(artifacts) == 15
    assert all(item["artifact_version"] for item in artifacts)
    assert by_id["P0A-SOURCE"]["artifact_version"] == "local-ai-runtime-0.2-v3.23"
    assert by_id["P0A-SOURCE"]["byte_count"] == 188325
    assert by_id["P0A-LINEAGE"]["artifact_version"] == "BaselineLineage.v2"
    assert by_id["P0A-LINEAGE"]["producer_task_id"] == "LAR-P0A-REBASELINE-V323"
    assert by_id["P0A-MANIFEST"]["producer_task_id"] == "LAR-P0A-013"
    assert by_id["P0A-REVIEW"]["producer_task_id"] == "LAR-P0A-013"
    assert artifact_ids.index("P0A-VERIFIER") < artifact_ids.index("P0A-MANIFEST")
    assert artifact_ids.index("P0A-MANIFEST") < artifact_ids.index("P0A-REVIEW")


def test_machine_work_items_are_a_deterministic_v323_dag() -> None:
    work_items = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))["work_items"]
    by_id = {item["task_id"]: item for item in work_items}
    phase_counts = {
        phase: sum(item["phase"] == phase for item in work_items)
        for phase in ("P1A", "P1B", "P1C", "P1D", "P1E", "P1F")
    }

    assert len(work_items) == 65
    assert phase_counts == {
        "P1A": 4,
        "P1B": 5,
        "P1C": 7,
        "P1D": 6,
        "P1E": 7,
        "P1F": 6,
    }
    assert by_id["LAR-P1A-004"]["next_task_ids"] == [
        "LAR-P1B-001",
        "LAR-P1F-001",
    ]
    assert by_id["LAR-P1C-007"]["depends_on"] == [
        "LAR-P1C-006",
        "LAR-P1D-004",
    ]
    assert by_id["LAR-P1F-002"]["depends_on"] == [
        "LAR-P1E-007",
        "LAR-P1F-001",
    ]
    assert by_id["LAR-P1F-006"]["next_task_ids"] == ["LAR-P1G-001"]
    assert by_id["LAR-P1G-001"]["depends_on"] == ["LAR-P1F-006"]
    assert by_id["LAR-P0A-001"]["next_task_ids"] == ["LAR-P0A-REBASELINE-V322"]
    assert by_id["LAR-P0A-REBASELINE-V322"]["depends_on"] == ["LAR-P0A-001"]
    assert by_id["LAR-P0A-REBASELINE-V323"]["depends_on"] == ["LAR-P0A-REBASELINE-V322"]
    assert by_id["LAR-P0A-EVAL-001"]["depends_on"] == ["LAR-P0A-REBASELINE-V323"]
    assert by_id["LAR-P0A-EVAL-002"]["depends_on"] == ["LAR-P0A-EVAL-001"]
    assert by_id["LAR-P0A-EVAL-002"]["status"] == "completed"
    assert by_id["LAR-P0A-EVAL-002"]["next_task_ids"] == ["LAR-P0A-002"]
    evaluation_acceptance = "\n".join(by_id["LAR-P0A-EVAL-002"]["acceptance"])
    assert "releases LAR-P0A-002" in evaluation_acceptance
    assert "releases LAR-P0A-003" not in evaluation_acceptance
    assert by_id["LAR-P0A-002"]["depends_on"] == ["LAR-P0A-EVAL-002"]
    assert by_id["LAR-P4-001"]["next_task_ids"] == ["LAR-P4-002", "LAR-P5-001"]
    assert by_id["LAR-P4-002"]["depends_on"] == ["LAR-P4-001"]
    assert by_id["LAR-P5-001"]["depends_on"] == ["LAR-P4-001"]
    assert "LAR-P4-002" not in by_id["LAR-P5-001"]["depends_on"]

    final_manifest = (
        "docs/specs/local-ai-runtime-0.2/normative/BaselineManifest.v1.json"
    )
    assert final_manifest not in by_id["LAR-P0A-002"]["scope"]["primary_files"]
    assert final_manifest in by_id["LAR-P0A-013"]["scope"]["primary_files"]

    required_tokens = {
        "LAR-P0A-004": {"volatile existing-family lookup", "Existing-family replay remains stable"},
        "LAR-P0A-006": {"SafetyOnlyExecutionRecord", "execution_authority_kind"},
        "LAR-P0A-010": {"accounting_kill_audit", "EmergencyDiskReserve", "OrdinalIgnoreCase"},
        "LAR-P0A-013": {"package_review_head", "approval_review_head"},
    }
    for task_id, tokens in required_tokens.items():
        rendered = json.dumps(by_id[task_id], ensure_ascii=False, sort_keys=True)
        assert all(token in rendered for token in tokens)

    for task_id, item in by_id.items():
        if task_id.startswith(("LAR-P1A-", "LAR-P1B-", "LAR-P1C-", "LAR-P1D-", "LAR-P1E-", "LAR-P1F-")):
            assert all(
                not path.endswith(("/", "\\"))
                for path in item["scope"]["primary_files"]
            )
            assert "python -m pytest tests/" not in "\n".join(item["verification"])


def test_planning_optimization_policy_is_bounded_and_qualification_driven() -> None:
    payload = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))
    policy = payload["planning_optimization_policy"]

    assert policy["kind"] == "bounded_minimum_operator_planning_v1"
    assert set(policy) == {
        "kind",
        "execution",
        "complexity",
        "model_routing",
        "outcome_metrics",
    }

    execution = policy["execution"]
    assert execution["atomic_closeout_unit"] == "one_selector_selected_work_item"
    assert execution["selector_cardinality"] == 1
    assert execution["continuation_mode"] == (
        "same_run_reselect_after_verified_atomic_closeout"
    )
    assert execution["default_budget"] == {
        "max_completed_work_items": 3,
        "max_elapsed_minutes": 180,
        "stop_after_failed_closeout": True,
    }
    assert execution["cross_phase_continuation"] is False
    assert {
        "budget_exhausted",
        "selector_not_unique_or_gate_red",
        "approval_or_phase_transition_boundary",
        "baseline_successor_or_frozen_semantic_change_required",
        "live_auth_provider_remote_destructive_or_external_write_boundary",
    }.issubset(execution["hard_stop_conditions"])

    complexity = policy["complexity"]
    assert complexity["warning_ratio"] == 0.8
    assert complexity["hard_caps"] == {
        "authoritative_docs": 14,
        "work_items": 65,
        "contract_projections": 11,
        "normative_artifacts": 15,
        "root_agents_bytes": 8192,
        "machine_plan_bytes": 230000,
        "planning_verifier_lines": 4200,
        "planning_governance_test_lines": 2600,
    }
    assert complexity["new_surface_rule"] == (
        "replace_an_existing_surface_or_create_a_successor_baseline"
    )

    routing = policy["model_routing"]
    assert routing["scope"] == "repo_agent_work_not_v323_runtime_authority"
    assert routing["active_profile_change"] == "none"
    assert routing["fallback_policy"] == (
        "fail_closed_no_silent_dynamic_model_effort_or_provider_fallback"
    )
    assert routing["candidate_roles"] == {
        "controller_high_risk_writer": "flagship_capability_candidate",
        "independent_reviewer": "high_reasoning_candidate",
        "read_heavy_explorer": "fast_efficient_candidate",
        "closed_repeatable_transform": "high_volume_candidate",
    }
    assert {
        "representative_paired_cohort",
        "quality_security_evidence_hard_floors",
        "task_success_and_downstream_outcome",
        "human_minutes_p50_p95_tokens_cost_and_rework",
        "surface_and_generation_qualification",
    } == set(routing["promotion_requirements"])

    metrics = policy["outcome_metrics"]
    assert metrics["missing_value_rule"] == "unknown_or_unavailable_never_zero"
    assert metrics["optimality_scope"] == (
        "declared_role_task_family_surface_profile_generation_and_cohort_only"
    )
    assert set(metrics["required_metrics"]) == {
        "completed_work_items_per_operator_kickoff",
        "unattended_verified_closeout_rate",
        "net_operator_minutes_per_success",
        "native_latency_p50_p95",
        "batch_verified_cycle_time_p50_p95",
        "task_success_and_downstream_outcome_rate",
        "token_cost_and_rework_per_success",
        "recovery_and_rollback_success_rate",
    }

    by_id = {item["task_id"]: item for item in payload["work_items"]}
    p0a004 = json.dumps(by_id["LAR-P0A-004"], ensure_ascii=False, sort_keys=True)
    assert "WorkRoutingPolicy routes work class only" in p0a004
    assert "no second planner or runtime model-router service" in p0a004


def test_planning_optimization_verifiers_reject_policy_drift() -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    verify_work_items = namespace["_verify_work_items"]
    verify_complexity_budget = namespace["_verify_planning_complexity_budget"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))

    mutations = [
        (
            lambda policy: policy["execution"]["default_budget"].__setitem__(
                "max_completed_work_items", 0
            ),
            "planning_optimization_policy canonical contract",
        ),
        (
            lambda policy: policy["complexity"]["hard_caps"].__setitem__(
                "authoritative_docs", 15
            ),
            "planning_optimization_policy canonical contract",
        ),
        (
            lambda policy: policy["model_routing"].__setitem__(
                "fallback_policy", "best_effort_dynamic_fallback"
            ),
            "planning_optimization_policy canonical contract",
        ),
        (
            lambda policy: policy["outcome_metrics"].__setitem__(
                "missing_value_rule", "missing_is_zero"
            ),
            "planning_optimization_policy canonical contract",
        ),
    ]

    for mutate, expected_failure in mutations:
        payload = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))
        mutate(payload["planning_optimization_policy"])
        failures: list[str] = []
        verify_work_items(
            payload,
            status["baseline_candidate"],
            status["current_active_queue"],
            status["current_work_item"],
            failures,
        )
        assert any(expected_failure in failure for failure in failures), failures

    payload = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))
    payload["planning_optimization_policy"]["complexity"]["hard_caps"].pop(
        "work_items"
    )
    failures = []
    verify_complexity_budget(
        REPO_ROOT,
        WORK_ITEMS_PATH,
        payload,
        status,
        json.loads(INVENTORY_PATH.read_text(encoding="utf-8")),
        failures,
    )
    assert failures == [
        "planning complexity hard_caps keys must match measured dimensions"
    ]


def test_planning_optimization_status_and_doc_projections_are_closed() -> None:
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    assert status["planning_optimization"] == {
        "status": "active",
        "policy_ref": "docs/plans/local-ai-runtime-0.2-work-items.json",
        "policy_kind": "bounded_minimum_operator_planning_v1",
        "complexity_health": "warning_all_dimensions",
        "frozen_v323_semantics_changed": False,
        "active_profile_change": "none",
    }

    expected_tokens = {
        "AGENTS.md": {"planning_optimization_policy", "同一 session"},
        "README.md": {"planning_optimization_policy", "最多 3 个"},
        "docs/README.md": {"planning_optimization_policy", "最多 3 个"},
        "docs/product/orchestrator-prd.md": {
            "completed_work_items_per_operator_kickoff",
            "declared role/task family/surface/profile generation/cohort",
        },
        "docs/architecture/orchestrator-target-architecture.md": {
            "planning_optimization_policy",
            "第二个 planner/router",
        },
        "docs/roadmap/orchestrator-roadmap.md": {
            "same_run_reselect_after_verified_atomic_closeout"
        },
        "docs/plans/orchestrator-implementation-plan.md": {
            "one_selector_selected_work_item",
            "unknown_or_unavailable_never_zero",
            "fail_closed_no_silent_dynamic_model_effort_or_provider_fallback",
        },
        "docs/backlog/orchestrator-task-list.md": {"bounded continuation"},
        "docs/specs/acceptance-and-gates.md": {
            "unknown_or_unavailable_never_zero",
            "declared role/task family/surface/profile generation/cohort",
        },
    }
    doc_contracts = {
        item["path"]: set(item["required_strings"])
        for item in status["doc_contracts"]
    }
    for relative_path, tokens in expected_tokens.items():
        assert tokens.issubset(doc_contracts[relative_path]), relative_path
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert all(token in text for token in tokens), relative_path


def test_human_readable_roadmap_projects_machine_work_item_count() -> None:
    work_items = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))["work_items"]
    expected_projection = f"机器图总计 {len(work_items)} 项"
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    doc_contracts = {
        item["path"]: set(item["required_strings"])
        for item in status["doc_contracts"]
    }

    assert expected_projection in ROADMAP_PATH.read_text(encoding="utf-8")
    assert expected_projection in doc_contracts[
        "docs/roadmap/orchestrator-roadmap.md"
    ]


def test_v323_lineage_binds_candidate_history_and_superseded_plan() -> None:
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    lineage_raw = LINEAGE_PATH.read_bytes()
    lineage = json.loads(lineage_raw)
    work_items = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))
    superseded = work_items["supersedes_plan"]

    assert len(lineage_raw) == 3495
    assert hashlib.sha256(lineage_raw).hexdigest() == (
        "49141a69c9aed6065ba063714fb2349750e500199ed8dfaf64fa6e2b198b9043"
    )
    assert lineage["domain"] == "local-ai-runtime/BaselineLineage/v2"
    assert lineage["schema_version"] == 2
    assert lineage["payload"]["candidate"] == {
        "byte_count": 188325,
        "id": "local-ai-runtime-0.2-v3.23",
        "path": "docs/specs/local-ai-runtime-0.2-v3.23-baseline-candidate.md",
        "role": "baseline_candidate",
        "sha256": status["baseline_candidate"]["sha256"],
    }
    v322 = next(
        entry
        for entry in lineage["payload"]["entries"]
        if entry["id"] == "local-ai-runtime-0.2-v3.22"
    )
    assert v322 == {
        "byte_count": 178330,
        "id": "local-ai-runtime-0.2-v3.22",
        "path": "docs/specs/local-ai-runtime-0.2-v3.22-baseline-candidate.md",
        "role": "superseded_candidate",
        "sha256": "8338a9dcf4bbbb40ca28f4f2ec6dca37587ee94fbfbbc6e3a0063c4de379569c",
    }
    assert superseded == {
        "plan_id": "local-ai-runtime-0.2-v3.22-implementation-work-items",
        "terminal_status": "superseded",
        "last_commit": "6fd6cd54037f17e44192bc272306b137def7f8a4",
        "byte_count": 202002,
        "sha256": "acabe34f188d73015536a141a8990c333ce6643dc28347671c2523adcaf7d2cc",
    }


def test_current_lineage_rejects_inventory_projection_drift() -> None:
    verify_lineage = runpy.run_path(str(VERIFIER_PATH))["_verify_current_lineage"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    inventory["lineage"]["canonical_predecessor"]["sha256"] = "0" * 64
    failures: list[str] = []

    verify_lineage(
        REPO_ROOT,
        status["baseline_candidate"],
        inventory,
        failures,
    )

    assert "inventory lineage must exactly project BaselineLineage.v2" in failures


def test_work_item_verifier_rejects_nonreciprocal_or_unreachable_dag_edges() -> None:
    verify_work_items = runpy.run_path(str(VERIFIER_PATH))["_verify_work_items"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    work_items = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))
    by_id = {item["task_id"]: item for item in work_items["work_items"]}
    by_id["LAR-P1D-006"]["next_task_ids"].remove("LAR-P1E-001")
    failures: list[str] = []

    verify_work_items(
        work_items,
        status["baseline_candidate"],
        status["current_active_queue"],
        status["current_work_item"],
        failures,
    )

    assert any(
        "LAR-P1E-001 dependency LAR-P1D-006 must list it as successor" in failure
        for failure in failures
    )
    assert any("not reachable from the declared graph roots" in failure for failure in failures)


def test_contract_projection_policy_is_bidirectional_and_token_closed() -> None:
    verify_work_items = runpy.run_path(str(VERIFIER_PATH))["_verify_work_items"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))

    missing_reverse = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))
    by_id = {item["task_id"]: item for item in missing_reverse["work_items"]}
    by_id["LAR-P1E-003"]["contract_projections"]["implements"].remove(
        "git_hybrid_materialization_v1"
    )
    failures: list[str] = []
    verify_work_items(
        missing_reverse,
        status["baseline_candidate"],
        status["current_active_queue"],
        status["current_work_item"],
        failures,
    )
    assert any(
        "git_hybrid_materialization_v1 implementation reverse projection mismatch"
        in failure
        for failure in failures
    )

    missing_token = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))
    by_id = {item["task_id"]: item for item in missing_token["work_items"]}
    by_id["LAR-P0A-010"]["contract_projection_tokens"].remove(
        "architecture_epoch"
    )
    failures = []
    verify_work_items(
        missing_token,
        status["baseline_candidate"],
        status["current_active_queue"],
        status["current_work_item"],
        failures,
    )
    assert any(
        "three_level_evolution_v1 task LAR-P0A-010 missing required contract token"
        in failure
        and "architecture_epoch" in failure
        for failure in failures
    )

    extra_token = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))
    by_id = {item["task_id"]: item for item in extra_token["work_items"]}
    by_id["LAR-P0A-010"]["contract_projection_tokens"].append("unapproved_token")
    failures = []
    verify_work_items(
        extra_token,
        status["baseline_candidate"],
        status["current_active_queue"],
        status["current_work_item"],
        failures,
    )
    assert any(
        "LAR-P0A-010 contract projection tokens must exactly match policy" in failure
        for failure in failures
    )

    extra_key = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))
    by_id = {item["task_id"]: item for item in extra_key["work_items"]}
    by_id["LAR-P0A-010"]["contract_projections"]["observes"] = [
        "three_level_evolution_v1"
    ]
    failures = []
    verify_work_items(
        extra_key,
        status["baseline_candidate"],
        status["current_active_queue"],
        status["current_work_item"],
        failures,
    )
    assert any(
        "LAR-P0A-010.contract_projections must contain exactly" in failure
        for failure in failures
    )

    extra_projection = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))
    by_id = {item["task_id"]: item for item in extra_projection["work_items"]}
    by_id["LAR-P0A-004"]["contract_projections"]["implements"].append(
        "unapproved_projection_v1"
    )
    failures = []
    verify_work_items(
        extra_projection,
        status["baseline_candidate"],
        status["current_active_queue"],
        status["current_work_item"],
        failures,
    )
    assert any(
        "LAR-P0A-004.implements projections must exactly match policy" in failure
        for failure in failures
    )


def test_work_item_verifier_requires_locked_offline_gate_profile() -> None:
    verify_work_items = runpy.run_path(str(VERIFIER_PATH))["_verify_work_items"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    work_items = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))
    commands = work_items["verification_profiles"]["new_runtime"]

    assert commands[0] == "uv lock --check --offline --project runtime/local-ai-runtime"
    assert all("--frozen" not in command for command in commands)
    assert all(
        "--locked --offline" in command
        for command in commands
        if command.startswith("uv run ")
    )

    commands[2] = commands[2].replace("--locked", "--frozen")
    failures: list[str] = []
    verify_work_items(
        work_items,
        status["baseline_candidate"],
        status["current_active_queue"],
        status["current_work_item"],
        failures,
    )
    assert any("locked offline command set" in failure for failure in failures)


def test_work_item_verifier_rejects_b3_before_p4_or_as_p5_dependency() -> None:
    verify_work_items = runpy.run_path(str(VERIFIER_PATH))["_verify_work_items"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    work_items = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))
    by_id = {item["task_id"]: item for item in work_items["work_items"]}
    by_id["LAR-P5-001"]["depends_on"] = ["LAR-P4-002"]
    by_id["LAR-P4-001"]["next_task_ids"].remove("LAR-P5-001")
    by_id["LAR-P4-002"]["next_task_ids"].append("LAR-P5-001")
    failures: list[str] = []

    verify_work_items(
        work_items,
        status["baseline_candidate"],
        status["current_active_queue"],
        status["current_work_item"],
        failures,
    )

    assert "P5 must depend on the green P4 cohort, not B3 activation" in failures


def test_selector_policy_rejects_completed_history_actions() -> None:
    verify_policy = runpy.run_path(str(VERIFIER_PATH))["_verify_selector_policy"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    policy["allowed_next_actions"].append("draft_v3_22_candidate_first")
    failures: list[str] = []

    verify_policy(
        REPO_ROOT,
        policy,
        status["normative_package"],
        status["current_work_item"],
        failures,
    )

    assert any("completed historical selector action" in failure for failure in failures)


def test_selector_rejects_unknown_action_even_when_policy_is_structurally_valid(
    tmp_path: Path,
) -> None:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    policy["allowed_next_actions"].append("invent_unapproved_work_first")
    policy["selection_order"].append(
        {
            "priority": 16,
            "condition_id": "invented_condition",
            "next_action": "invent_unapproved_work_first",
            "why": "Structurally valid but not part of the reviewed v3.23 stage graph.",
        }
    )
    policy_path = tmp_path / "unknown-action-policy.json"
    policy_path.write_text(
        json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    completed = _run(str(SELECTOR_PATH), "--policy-path", str(policy_path))

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["next_action"] == "repair_gate_first"
    assert payload["verifier_status"] is None
    assert any(
        "v3.23 action catalog" in issue for issue in payload["governance_issues"]
    )


def test_selector_rejects_duplicate_policy_key(tmp_path: Path) -> None:
    raw = POLICY_PATH.read_text(encoding="utf-8")
    policy_path = tmp_path / "duplicate-policy.json"
    policy_path.write_text(
        '{"schema_version":"duplicate",' + raw.lstrip()[1:], encoding="utf-8"
    )

    completed = _run(str(SELECTOR_PATH), "--policy-path", str(policy_path))

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["next_action"] == "repair_gate_first"
    assert any("duplicate JSON key" in issue for issue in payload["governance_issues"])


def test_selector_rejects_malformed_policy_collection(tmp_path: Path) -> None:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    policy["required_doc_refs"] = {"path": "README.md"}
    policy_path = tmp_path / "malformed-policy.json"
    policy_path.write_text(
        json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    completed = _run(str(SELECTOR_PATH), "--policy-path", str(policy_path))

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["next_action"] == "repair_gate_first"
    assert payload["verifier_status"] is None


def test_selector_rejects_an_unattested_policy_copy(tmp_path: Path) -> None:
    policy_path = tmp_path / "structurally-valid-policy-copy.json"
    policy_path.write_bytes(POLICY_PATH.read_bytes())

    completed = _run(str(SELECTOR_PATH), "--policy-path", str(policy_path))

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["next_action"] == "repair_gate_first"
    assert any(
        "selector policy identity" in issue for issue in payload["governance_issues"]
    )


def test_selector_rejects_status_drift_after_verifier_attestation(
    tmp_path: Path,
) -> None:
    namespace = runpy.run_path(str(SELECTOR_PATH))
    select_next_work = namespace["select_next_work"]
    status_path = _write_status(tmp_path, lambda _payload: None)

    def attest_then_drift(_root: Path, path: Path, _verifier: Path) -> dict[str, object]:
        attestation = _verifier_attestation(path, "LAR-P0A-002")
        with path.open("a", encoding="utf-8") as stream:
            stream.write("\n")
        return attestation

    select_next_work.__globals__["_run_verifier"] = attest_then_drift
    payload = select_next_work(
        repo_root=REPO_ROOT,
        status_path=status_path,
        policy_path=POLICY_PATH,
        verifier_path=VERIFIER_PATH,
    )

    assert payload["next_action"] == "repair_gate_first"
    assert any(
        "planning status identity" in issue
        for issue in payload["governance_issues"]
    )


def test_selector_repairs_verifier_timeout() -> None:
    namespace = runpy.run_path(str(SELECTOR_PATH))
    select_next_work = namespace["select_next_work"]
    select_next_work.__globals__["_run_verifier"] = lambda *args, **kwargs: {
        "command": ["python", "verify-planning-status.py"],
        "exit_code": 124,
        "payload": None,
        "stderr": "planning verifier timed out after 60 seconds",
    }

    payload = select_next_work(
        repo_root=REPO_ROOT,
        status_path=STATUS_PATH,
        policy_path=POLICY_PATH,
        verifier_path=VERIFIER_PATH,
    )

    assert payload["next_action"] == "repair_gate_first"
    assert payload["verifier_status"]["exit_code"] == 124


def test_selector_runs_final_baseline_review_for_exact_closure_state(
    tmp_path: Path,
) -> None:
    namespace = runpy.run_path(str(SELECTOR_PATH))
    select_next_work = namespace["select_next_work"]
    select_next_work.__globals__["_run_verifier"] = (
        lambda _root, status_path, _verifier: _verifier_attestation(
            status_path, "LAR-P0A-013"
        )
    )

    def mutate(payload: dict[str, object]) -> None:
        current = payload["current_work_item"]
        package = payload["normative_package"]
        evaluation = payload["native_thin_path_evaluation"]
        assert isinstance(current, dict)
        assert isinstance(package, dict)
        assert isinstance(evaluation, dict)
        evaluation.update(
            {
                "status": "preserve_v3_23_semantics",
                "decision": "preserve_v3_23_semantics",
                "result_ref": "docs/evaluations/local-ai-runtime-0.2/native-thin-path-capability-results.v1.json",
                "decision_ref": "docs/evaluations/local-ai-runtime-0.2/native-thin-path-capability-decision.v1.json",
                "evidence_ref": "docs/evaluations/local-ai-runtime-0.2/native-thin-path-capability-evidence.v1.json",
            }
        )
        current["task_id"] = "LAR-P0A-013"
        package["missing_artifact_ids"] = ["P0A-MANIFEST", "P0A-REVIEW"]

    status_path = _write_status(tmp_path, mutate)
    payload = select_next_work(
        repo_root=REPO_ROOT,
        status_path=status_path,
        policy_path=POLICY_PATH,
        verifier_path=VERIFIER_PATH,
    )

    assert not payload["governance_issues"], payload["governance_issues"]
    assert payload["next_action"] == "run_baseline_consistency_review", payload
    assert payload["current_work_item_id"] == "LAR-P0A-013"


def test_selector_repairs_malformed_final_review_artifact_set(tmp_path: Path) -> None:
    namespace = runpy.run_path(str(SELECTOR_PATH))
    select_next_work = namespace["select_next_work"]
    select_next_work.__globals__["_run_verifier"] = (
        lambda _root, status_path, _verifier: _verifier_attestation(
            status_path, "LAR-P0A-013"
        )
    )

    def mutate(payload: dict[str, object]) -> None:
        current = payload["current_work_item"]
        package = payload["normative_package"]
        evaluation = payload["native_thin_path_evaluation"]
        assert isinstance(current, dict)
        assert isinstance(package, dict)
        assert isinstance(evaluation, dict)
        evaluation.update(
            {
                "status": "preserve_v3_23_semantics",
                "decision": "preserve_v3_23_semantics",
                "result_ref": "docs/evaluations/local-ai-runtime-0.2/native-thin-path-capability-results.v1.json",
                "decision_ref": "docs/evaluations/local-ai-runtime-0.2/native-thin-path-capability-decision.v1.json",
                "evidence_ref": "docs/evaluations/local-ai-runtime-0.2/native-thin-path-capability-evidence.v1.json",
            }
        )
        current["task_id"] = "LAR-P0A-013"
        package["missing_artifact_ids"] = ["P0A-REVIEW", "P0A-MANIFEST"]

    status_path = _write_status(tmp_path, mutate)
    payload = select_next_work(
        repo_root=REPO_ROOT,
        status_path=status_path,
        policy_path=POLICY_PATH,
        verifier_path=VERIFIER_PATH,
    )

    assert payload["next_action"] == "repair_gate_first"
    assert any(
        "baseline review closure state" in issue
        for issue in payload["governance_issues"]
    ), payload


def _write_post_p4_status(
    tmp_path: Path, *, current_work_item_id: str, b3_active: bool = False
) -> Path:
    def mutate(payload: dict[str, object]) -> None:
        package = payload["normative_package"]
        evaluation = payload["native_thin_path_evaluation"]
        approval = payload["approval_state"]
        truth_reset = payload["truth_reset"]
        legacy = payload["legacy_runtime_posture"]
        implementation = payload["implementation"]
        p2 = payload["p2_admission"]
        rollout = payload["rollout"]
        current = payload["current_work_item"]
        assert all(
            isinstance(value, dict)
            for value in (
                package,
                evaluation,
                approval,
                truth_reset,
                legacy,
                implementation,
                p2,
                rollout,
                current,
            )
        )
        evaluation.update(
            {
                "status": "preserve_v3_23_semantics",
                "decision": "preserve_v3_23_semantics",
                "result_ref": "docs/evaluations/local-ai-runtime-0.2/native-thin-path-capability-results.v1.json",
                "decision_ref": "docs/evaluations/local-ai-runtime-0.2/native-thin-path-capability-decision.v1.json",
                "evidence_ref": "docs/evaluations/local-ai-runtime-0.2/native-thin-path-capability-evidence.v1.json",
            }
        )
        package.update(
            {"status": "complete", "approval_eligible": True, "missing_artifact_ids": []}
        )
        approval["active"] = True
        truth_reset.update({"performed": True, "permitted": True})
        legacy.update(
            {
                "new_package_exists": True,
                "legacy_guard_complete": True,
                "new_batch_claims_allowed": True,
            }
        )
        implementation.update(
            {
                "started": True,
                "package_created": True,
                "code_complete": True,
                "implementation_acceptance_active": True,
                "full_q0_passed": True,
            }
        )
        p2["admitted"] = True
        rollout.update(
            {
                "p2_pilot_complete": True,
                "p3_scheduled_self_host_complete": True,
                "p4_cohort_complete": True,
                "b3_portfolio_generation_active": b3_active,
            }
        )
        current["task_id"] = current_work_item_id

    return _write_status(tmp_path, mutate)


def test_selector_routes_selected_b3_work_item_after_green_p4(tmp_path: Path) -> None:
    namespace = runpy.run_path(str(SELECTOR_PATH))
    select_next_work = namespace["select_next_work"]
    status_path = _write_post_p4_status(
        tmp_path, current_work_item_id="LAR-P4-002"
    )
    select_next_work.__globals__["_run_verifier"] = (
        lambda _root, path, _verifier: _verifier_attestation(path, "LAR-P4-002")
    )

    payload = select_next_work(
        repo_root=REPO_ROOT,
        status_path=status_path,
        policy_path=POLICY_PATH,
        verifier_path=VERIFIER_PATH,
    )

    assert payload["next_action"] == "activate_b3_portfolio_generation_first"
    assert payload["stage_snapshot"]["b3_portfolio_generation_active"] is False


def test_selector_routes_p5_without_requiring_b3_activation(tmp_path: Path) -> None:
    namespace = runpy.run_path(str(SELECTOR_PATH))
    select_next_work = namespace["select_next_work"]
    status_path = _write_post_p4_status(
        tmp_path, current_work_item_id="LAR-P5-001"
    )
    select_next_work.__globals__["_run_verifier"] = (
        lambda _root, path, _verifier: _verifier_attestation(path, "LAR-P5-001")
    )

    payload = select_next_work(
        repo_root=REPO_ROOT,
        status_path=status_path,
        policy_path=POLICY_PATH,
        verifier_path=VERIFIER_PATH,
    )

    assert payload["next_action"] == "cut_over_repositories_first"
    assert payload["stage_snapshot"]["b3_portfolio_generation_active"] is False


def test_work_item_verifier_reports_malformed_nested_collections() -> None:
    verify_work_items = runpy.run_path(str(VERIFIER_PATH))["_verify_work_items"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    work_items = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))
    by_id = {item["task_id"]: item for item in work_items["work_items"]}
    by_id["LAR-P0A-002"]["scope"] = "not-an-object"
    by_id["LAR-P0A-003"]["next_task_ids"] = 7
    failures: list[str] = []

    verify_work_items(
        work_items,
        status["baseline_candidate"],
        status["current_active_queue"],
        status["current_work_item"],
        failures,
    )

    assert "LAR-P0A-002.scope must be an object" in failures
    assert "LAR-P0A-003.next_task_ids must be an array" in failures


def test_selector_repairs_invalid_successful_verifier_output(tmp_path: Path) -> None:
    fake_verifier = tmp_path / "invalid-success-verifier.py"
    fake_verifier.write_text("print('not-json')\n", encoding="utf-8")

    completed = _run(
        str(SELECTOR_PATH), "--verifier-path", str(fake_verifier)
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["next_action"] == "repair_gate_first"
    assert payload["verifier_status"]["exit_code"] == 0
    assert payload["verifier_status"]["payload"] is None


def test_present_inventory_artifact_requires_exact_identity() -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    verify_inventory = namespace["_verify_inventory"]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    inventory["required_artifacts"][0]["sha256"] = "0" * 64
    failures: list[str] = []

    verify_inventory(
        root=REPO_ROOT,
        inventory_path=INVENTORY_PATH,
        baseline=status["baseline_candidate"],
        package_state=status["normative_package"],
        inventory=inventory,
        failures=failures,
    )

    assert any("sha256 must match present artifact bytes" in item for item in failures)


def test_complete_package_requires_structured_standalone_verifier(tmp_path: Path) -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    verify_package = namespace["_verify_standalone_package"]
    fake_verifier = tmp_path / "fake-verifier.py"
    fake_verifier.write_text("print('not-json')\n", encoding="utf-8")
    failures: list[str] = []

    verified = verify_package(
        root=REPO_ROOT,
        inventory_path=INVENTORY_PATH,
        verifier_path=fake_verifier,
        baseline_id="local-ai-runtime-0.2-v3.23",
        failures=failures,
    )

    assert verified is False
    assert any("standalone normative package verifier output" in item for item in failures)


def test_verifier_rejects_forged_active_approval(tmp_path: Path) -> None:
    status_path = _write_status(
        tmp_path,
        lambda payload: payload["approval_state"].update(
            {
                "active": True,
                "generation": 1,
                "approval_record": "docs/acceptance/forged.json",
            }
        ),
    )

    completed = _run(str(VERIFIER_PATH), "--status-path", str(status_path))

    assert completed.returncode == 1
    assert "approval-eligible package" in completed.stderr
    assert "BaselineApprovalRecord" in completed.stderr


def test_verifier_rejects_implementation_before_truth_reset(tmp_path: Path) -> None:
    def mutate(payload: dict[str, object]) -> None:
        implementation = payload["implementation"]
        assert isinstance(implementation, dict)
        implementation["started"] = True
        implementation["package_created"] = True

    status_path = _write_status(tmp_path, mutate)

    completed = _run(str(VERIFIER_PATH), "--status-path", str(status_path))

    assert completed.returncode == 1
    assert "implementation cannot start before Truth Reset" in completed.stderr
    assert "Legacy Ownership Guard" in completed.stderr


def test_verifier_rejects_b3_activation_before_green_p4(tmp_path: Path) -> None:
    def mutate(payload: dict[str, object]) -> None:
        rollout = payload["rollout"]
        assert isinstance(rollout, dict)
        rollout["b3_portfolio_generation_active"] = True

    status_path = _write_status(tmp_path, mutate)
    completed = _run(str(VERIFIER_PATH), "--status-path", str(status_path))

    assert completed.returncode == 1
    assert "B3 portfolio activation requires the green P4 cohort" in completed.stderr


def test_selector_repairs_hash_drift_before_selecting_work(tmp_path: Path) -> None:
    def mutate(payload: dict[str, object]) -> None:
        baseline = payload["baseline_candidate"]
        assert isinstance(baseline, dict)
        baseline["sha256"] = "0" * 64

    status_path = _write_status(tmp_path, mutate)

    completed = _run(str(SELECTOR_PATH), "--status-path", str(status_path))

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["next_action"] == "repair_gate_first"
    assert payload["current_work_item_id"] is None
    assert payload["verifier_status"]["exit_code"] == 1
