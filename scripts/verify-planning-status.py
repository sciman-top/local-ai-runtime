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
CURRENT_BASELINE_ID = "local-ai-runtime-0.2-v3.21"
CURRENT_BASELINE_PATH = "docs/specs/local-ai-runtime-0.2-v3.21-baseline-candidate.md"
CURRENT_WORK_ITEM_COUNT = 58
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
    *(f"LAR-P1C-{index:03d}" for index in range(1, 7)),
    *(f"LAR-P1D-{index:03d}" for index in range(1, 7)),
    *(f"LAR-P1E-{index:03d}" for index in range(1, 7)),
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
WORK_ITEM_SCHEMA_VERSION = "local_ai_runtime_work_items.v2"
EXPECTED_WORK_ITEM_STATUSES = [
    "ready",
    "pending",
    "blocked",
    "in_progress",
    "completed",
    "cancelled",
]
EXPECTED_VERIFICATION_PROFILES = {"planning", "new_runtime"}


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
    status = _load_json(status_path)
    failures: list[str] = []

    _require_fields(
        status,
        [
            "schema_version",
            "status_id",
            "updated_on",
            "baseline_candidate",
            "approval_state",
            "normative_package",
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
    approval = _as_dict(status.get("approval_state"), "approval_state", failures)
    package_state = _as_dict(status.get("normative_package"), "normative_package", failures)
    queue = _as_dict(status.get("current_active_queue"), "current_active_queue", failures)
    current_work = _as_dict(status.get("current_work_item"), "current_work_item", failures)
    legacy = _as_dict(status.get("legacy_runtime_posture"), "legacy_runtime_posture", failures)
    truth_reset = _as_dict(status.get("truth_reset"), "truth_reset", failures)
    implementation = _as_dict(status.get("implementation"), "implementation", failures)
    p2 = _as_dict(status.get("p2_admission"), "p2_admission", failures)
    rollout = _as_dict(status.get("rollout"), "rollout", failures)

    _verify_baseline(root, baseline, failures)

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

    try:
        policy_path = _resolve_repo_path(root, str(POLICY_PATH), "selector policy")
        policy = _load_json(policy_path)
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
        "baseline_id": baseline["id"],
        "baseline_status": baseline["status"],
        "baseline_byte_count": baseline["byte_count"],
        "baseline_sha256": baseline["sha256"],
        "blocking_stage": baseline["blocking_stage"],
        "approval_active": approval["active"],
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
        failures.append("inventory package_id must match the v3.21 package identity")
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
            "inventory artifact IDs/order must match the v3.21 closure sequence"
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
        failures.append("work-item plan_id must match the v3.21 implementation graph")
    if payload.get("baseline_id") != baseline.get("id"):
        failures.append("work-item baseline_id must match planning baseline")
    if payload.get("baseline_status") != baseline.get("status"):
        failures.append("work-item baseline_status must match planning baseline")
    if payload.get("blocking_stage") != baseline.get("blocking_stage"):
        failures.append("work-item blocking_stage must match planning baseline")
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
        failures.append("work-item status_catalog must match the v3.21 state set and order")

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
        if (
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

    _verify_acyclic_dependencies(items, failures)
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

    ready = [task_id for task_id, item in items.items() if item.get("status") == "ready"]
    current_id = current_work.get("task_id")
    if ready != [current_id]:
        failures.append(
            f"exactly the current work item must be ready: current={current_id!r}, ready={ready!r}"
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
                    f"ready current work item has incomplete dependency: {dependency}"
                )
    return items


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
        if current_work.get("task_id") != first_producer:
            failures.append(
                "current work item must produce the first missing normative artifact: "
                f"expected {first_producer}, got {current_work.get('task_id')}"
            )


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
    if current_work.get("selector_action") not in allowed:
        failures.append("current selector action is not allowed by selector policy")

    review_sets = policy.get("baseline_review_missing_artifact_sets")
    if review_sets != EXPECTED_REVIEW_MISSING_ARTIFACT_SETS:
        failures.append(
            "selector baseline_review_missing_artifact_sets must match the v3.21 manifest/review closure"
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

    for relative in policy.get("required_entrypoints", []):
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

    if package_state.get("status") == "incomplete":
        if queue.get("queue_id") != "LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE":
            failures.append("incomplete package requires baseline-closure queue")
        if current_work.get("selector_action") not in {
            "close_baseline_normative_package_first",
            "run_baseline_consistency_review",
        }:
            failures.append("incomplete package requires a normative-closure selector action")


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


def _load_json(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"JSON file is not readable: {path} ({exc})") from exc

    return _loads_json_object(text, str(path))


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
