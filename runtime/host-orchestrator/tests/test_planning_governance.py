from __future__ import annotations

import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
STATUS_PATH = REPO_ROOT / "docs" / "architecture" / "planning-status.json"
BASELINE_PATH = (
    REPO_ROOT
    / "docs"
    / "specs"
    / "local-ai-runtime-0.2-v3.21-baseline-candidate.md"
)
V320_PATH = (
    REPO_ROOT
    / "docs"
    / "specs"
    / "local-ai-runtime-0.2-v3.20-baseline-candidate.md"
)
VERIFIER_PATH = REPO_ROOT / "scripts" / "verify-planning-status.py"
SELECTOR_PATH = REPO_ROOT / "scripts" / "select-next-work.py"
POLICY_PATH = REPO_ROOT / "docs" / "architecture" / "next-work-selection-policy.json"
INVENTORY_PATH = (
    REPO_ROOT / "docs" / "specs" / "local-ai-runtime-0.2-normative-package.json"
)
WORK_ITEMS_PATH = REPO_ROOT / "docs" / "plans" / "local-ai-runtime-0.2-work-items.json"
IMPLEMENTATION_PLAN_PATH = (
    REPO_ROOT / "docs" / "plans" / "orchestrator-implementation-plan.md"
)
ACCEPTANCE_PATH = REPO_ROOT / "docs" / "specs" / "acceptance-and-gates.md"
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


def test_planning_verifier_accepts_truthful_candidate_state() -> None:
    completed = _run(str(VERIFIER_PATH))

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["status"] == "pass"
    assert payload["baseline_id"] == "local-ai-runtime-0.2-v3.21"
    assert payload["approval_active"] is False
    assert payload["missing_artifact_count"] == 14
    assert payload["current_work_item_id"] == "LAR-P0A-001"
    work_items = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))["work_items"]
    task_ids = {item["task_id"] for item in work_items}
    assert payload["work_item_count"] == len(work_items) == 58
    assert {"LAR-P0A-001", "LAR-P5-001"} <= task_ids


def test_planning_selector_returns_baseline_closure_without_preflight() -> None:
    completed = _run(str(SELECTOR_PATH))

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["next_action"] == "close_baseline_normative_package_first"
    assert payload["current_work_item_id"] == "LAR-P0A-001"
    assert payload["side_effects_performed"] is False
    assert payload["preflight_run"] is False


def test_baseline_bytes_match_planning_identity() -> None:
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    raw = BASELINE_PATH.read_bytes()

    assert len(raw) == status["baseline_candidate"]["byte_count"] == 158485
    assert hashlib.sha256(raw).hexdigest() == status["baseline_candidate"]["sha256"]
    assert hashlib.sha256(raw).hexdigest() == "1bfb5cd2c92c036804a6005d5b36cdd5acc6bedc4d6bf4070ccfb7a70ce063fb"
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
    assert b"\r" not in raw


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
    assert by_id["P0A-SOURCE"]["artifact_version"] == "local-ai-runtime-0.2-v3.21"
    assert by_id["P0A-SOURCE"]["byte_count"] == 158485
    assert by_id["P0A-MANIFEST"]["producer_task_id"] == "LAR-P0A-013"
    assert by_id["P0A-REVIEW"]["producer_task_id"] == "LAR-P0A-013"
    assert artifact_ids.index("P0A-VERIFIER") < artifact_ids.index("P0A-MANIFEST")
    assert artifact_ids.index("P0A-MANIFEST") < artifact_ids.index("P0A-REVIEW")


def test_machine_work_items_are_fine_grained_and_project_v321_semantics() -> None:
    work_items = json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))["work_items"]
    by_id = {item["task_id"]: item for item in work_items}
    phase_counts = {
        phase: sum(item["phase"] == phase for item in work_items)
        for phase in ("P1A", "P1B", "P1C", "P1D", "P1E", "P1F")
    }

    assert len(work_items) == 58
    assert phase_counts == {
        "P1A": 4,
        "P1B": 5,
        "P1C": 6,
        "P1D": 6,
        "P1E": 6,
        "P1F": 6,
    }
    assert by_id["LAR-P1A-004"]["next_task_ids"] == ["LAR-P1B-001"]
    assert by_id["LAR-P1F-006"]["next_task_ids"] == ["LAR-P1G-001"]
    assert by_id["LAR-P1G-001"]["depends_on"] == ["LAR-P1F-006"]

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
    select_next_work.__globals__["_run_verifier"] = lambda *args, **kwargs: {
        "command": ["python", "verify-planning-status.py"],
        "exit_code": 0,
        "payload": {
            "status": "pass",
            "baseline_id": "local-ai-runtime-0.2-v3.21",
            "current_work_item_id": "LAR-P0A-013",
        },
        "stderr": "",
    }

    def mutate(payload: dict[str, object]) -> None:
        current = payload["current_work_item"]
        package = payload["normative_package"]
        assert isinstance(current, dict)
        assert isinstance(package, dict)
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
    select_next_work.__globals__["_run_verifier"] = lambda *args, **kwargs: {
        "command": ["python", "verify-planning-status.py"],
        "exit_code": 0,
        "payload": {
            "status": "pass",
            "baseline_id": "local-ai-runtime-0.2-v3.21",
            "current_work_item_id": "LAR-P0A-013",
        },
        "stderr": "",
    }

    def mutate(payload: dict[str, object]) -> None:
        current = payload["current_work_item"]
        package = payload["normative_package"]
        assert isinstance(current, dict)
        assert isinstance(package, dict)
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
        baseline_id="local-ai-runtime-0.2-v3.21",
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
