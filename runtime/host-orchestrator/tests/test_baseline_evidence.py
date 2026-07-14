from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
from typing import Callable

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
VERIFIER_PATH = REPO_ROOT / "scripts" / "verify-local-ai-runtime-baseline.py"
EVIDENCE_ROOT = REPO_ROOT / "docs" / "specs" / "local-ai-runtime-0.2"
POLICY_PATH = EVIDENCE_ROOT / "normative" / "EvidenceContractSet.v1.json"
EVENT_SCHEMA_PATH = (
    EVIDENCE_ROOT / "schemas" / "NormalizedExecutionEvent.v1.schema.json"
)
EVENT_CATALOG_PATH = EVIDENCE_ROOT / "catalogs" / "EventStatusMatrix.v1.json"
FIXTURE_PATH = EVIDENCE_ROOT / "fixtures" / "evidence" / "manifest.json"


def _run_component(repo_root: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VERIFIER_PATH),
            "--repo-root",
            str(repo_root),
            "--component",
            "evidence",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _copy_bundle(tmp_path: Path) -> None:
    for source in (POLICY_PATH, EVENT_SCHEMA_PATH, EVENT_CATALOG_PATH, FIXTURE_PATH):
        target = tmp_path / source.relative_to(REPO_ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


def test_evidence_component_closes_declared_contracts() -> None:
    completed = _run_component()

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload == {
        "status": "pass",
        "component": "evidence",
        "artifact_version": "EvidenceContractSet.v1",
        "artifact_byte_count": 9656,
        "artifact_sha256": (
            "d9cea69a4680a0229b5680ea0de503e9d6f9d24eb6232893b727e11c1e52e9e0"
        ),
        "event_schema_sha256": (
            "45ab72fca886dca978473de0d9b43c3475a64bb0104a4f30bd8c4556f8b99591"
        ),
        "event_catalog_sha256": (
            "7508aa4061f9526d53b7e547125792016f08748078fb2cffbbcafb517fc6d7d7"
        ),
        "final_event_hash": (
            "fb3b095ad34f59ec134e9b6bf6c8928d208b1c95cd7b6935543c056d55a87909"
        ),
        "fixture_counts": {
            "event_pair": 16,
            "event_chain": 3,
            "pre_scan": 8,
            "journal_cursor": 4,
            "receipt": 7,
            "artifact_publish": 6,
            "external_evidence": 6,
            "key_envelope": 7,
            "backup_eligibility": 4,
            "post_activity": 5,
            "restore": 10,
        },
    }
    assert hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest() == payload[
        "artifact_sha256"
    ]


@pytest.mark.parametrize(
    ("target_name", "mutation", "expected_reason"),
    [
        (
            "policy",
            lambda value: value["payload"]["output_handling"].__setitem__(
                "raw_process_material_content_hash_persisted", True
            ),
            "evidence_policy_identity",
        ),
        (
            "event_schema",
            lambda value: value.__setitem__("unevaluatedProperties", True),
            "evidence_schema_drift",
        ),
        (
            "event_catalog",
            lambda value: value["matrix"].pop(),
            "event_catalog_drift",
        ),
        (
            "fixture",
            lambda value: value.__setitem__("restore_cases", None),
            "evidence_fixture_drift",
        ),
    ],
)
def test_evidence_component_fails_closed_on_bundle_drift(
    tmp_path: Path,
    target_name: str,
    mutation: Callable[[dict[str, object]], None],
    expected_reason: str,
) -> None:
    _copy_bundle(tmp_path)
    targets = {
        "policy": POLICY_PATH,
        "event_schema": EVENT_SCHEMA_PATH,
        "event_catalog": EVENT_CATALOG_PATH,
        "fixture": FIXTURE_PATH,
    }
    target = tmp_path / targets[target_name].relative_to(REPO_ROOT)
    value = json.loads(target.read_text(encoding="utf-8"))
    mutation(value)
    target.write_text(
        json.dumps(value, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    namespace = runpy.run_path(str(VERIFIER_PATH))
    failure_type = namespace["ValidationFailure"]
    with pytest.raises(failure_type) as captured:
        namespace["verify_evidence_component"](tmp_path)
    assert captured.value.reason == expected_reason


@pytest.mark.parametrize(
    ("event_index", "mutation", "expected_reason"),
    [
        (0, lambda value: value.__setitem__("raw_stdout", "forbidden"), "normalized_event_schema"),
        (1, lambda value: value.__setitem__("prev_hash", "0" * 64), "normalized_event_schema"),
        (2, lambda value: value.__setitem__("event_hash", "0" * 64), "normalized_event_hash"),
        (
            1,
            lambda value: value.__setitem__("canonical_relative_path", "secret.txt"),
            "normalized_event_schema",
        ),
        (
            1,
            lambda value: value.__setitem__("mutation_observation_id", "path-1"),
            "normalized_event_schema",
        ),
    ],
)
def test_normalized_event_validator_rejects_field_or_chain_expansion(
    event_index: int,
    mutation: Callable[[dict[str, object]], None],
    expected_reason: str,
) -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    catalog_value = json.loads(EVENT_CATALOG_PATH.read_text(encoding="utf-8"))
    catalog = namespace["_verify_event_catalog"](catalog_value)
    candidate = copy.deepcopy(fixture["event_chain_positive"][event_index])
    mutation(candidate)
    expected_prev = (
        "0" * 64
        if event_index == 0
        else fixture["event_chain_positive"][event_index - 1]["event_hash"]
    )

    with pytest.raises(namespace["ValidationFailure"]) as captured:
        namespace["_validate_normalized_event"](candidate, catalog, expected_prev)
    assert captured.value.reason == expected_reason


def test_receipt_is_exactly_the_six_condition_conjunction() -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    cases = fixture["receipt_cases"]

    assert namespace["_evaluate_receipt"](cases[0]) == "receipt_publish"
    assert all(
        namespace["_evaluate_receipt"](case) == "receipt_withheld"
        for case in cases[1:]
    )


def test_backup_response_loss_reuses_only_the_same_restore_intent() -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    cases = {case["case_id"]: case for case in fixture["restore_cases"]}

    assert (
        namespace["_evaluate_restore"](cases["response_loss_same_intent"])
        == "continue_same_intent"
    )
    assert (
        namespace["_evaluate_restore"](cases["response_loss_second_intent"])
        == "second_restore_forbidden"
    )


def test_post_activity_marker_must_precede_authoritative_mutation() -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    cases = {case["case_id"]: case for case in fixture["post_activity_cases"]}

    assert (
        namespace["_evaluate_post_activity"](cases["marker_before_mutation"])
        == "mutation_allowed"
    )
    assert (
        namespace["_evaluate_post_activity"](cases["mutation_first"])
        == "ordering_violation"
    )


@pytest.mark.parametrize("oracle_field", ["summary_present", "free_text_present"])
def test_pre_scan_projection_rejects_low_entropy_oracle_fields(
    oracle_field: str,
) -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    case = {
        "case_id": f"unknown_with_{oracle_field}",
        "path_class": "unknown",
        "approved_path_id_present": False,
        "path_text_present": False,
        "content_hash_present": False,
        "ordinary_digest_present": False,
        "summary_present": False,
        "free_text_present": False,
        "expected_result": "pre_scan_oracle_forbidden",
    }
    case[oracle_field] = True

    assert namespace["_evaluate_pre_scan_projection"](case) == (
        "pre_scan_oracle_forbidden"
    )


def test_partial_post_activity_marker_is_conservatively_stale() -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    case = {
        "case_id": "partial_marker_without_mutation",
        "create_new_write_through": True,
        "marker_flushed": False,
        "head_staled": True,
        "mutation_started": False,
        "mutation_started_before_marker": False,
        "expected_result": "conservative_stale",
    }

    assert namespace["_evaluate_post_activity"](case) == "conservative_stale"


def test_restore_marker_or_head_ambiguity_is_drill_only() -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    case = copy.deepcopy(fixture["restore_cases"][0])
    case["case_id"] = "marker_or_head_ambiguous"
    case["marker_or_head_ambiguous"] = True
    case["expected_result"] = "drill_only"

    assert namespace["_evaluate_restore"](case) == "drill_only"
