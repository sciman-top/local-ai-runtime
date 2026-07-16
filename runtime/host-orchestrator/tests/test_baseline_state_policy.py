from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Callable

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
VERIFIER_PATH = REPO_ROOT / "scripts" / "verify-local-ai-runtime-baseline.py"
SPEC_ROOT = REPO_ROOT / "docs" / "specs" / "local-ai-runtime-0.2"
STATE_POLICY_PATH = SPEC_ROOT / "normative" / "StatePolicyCatalog.v1.json"
GUARD_CATALOG_PATH = SPEC_ROOT / "catalogs" / "GuardCatalog.v1.json"
OPERATOR_CATALOG_PATH = SPEC_ROOT / "catalogs" / "OperatorActionCatalog.v1.json"
FIXTURE_PATH = SPEC_ROOT / "fixtures" / "state-policy" / "manifest.json"
BUNDLE_PATHS = (
    STATE_POLICY_PATH,
    GUARD_CATALOG_PATH,
    OPERATOR_CATALOG_PATH,
    FIXTURE_PATH,
)


def _run_component(repo_root: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VERIFIER_PATH),
            "--repo-root",
            str(repo_root),
            "--component",
            "state-policy",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _copy_bundle(tmp_path: Path) -> None:
    for source in BUNDLE_PATHS:
        target = tmp_path / source.relative_to(REPO_ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


def test_state_policy_component_closes_declared_contracts() -> None:
    completed = _run_component()

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["status"] == "pass"
    assert payload["component"] == "state-policy"
    assert payload["artifact_version"] == "StatePolicyCatalog.v1"
    assert payload["artifact_byte_count"] == 41279
    assert payload["artifact_sha256"] == (
        "423f90a0550630b0d413cc82a53f98b6602d05cd6b7a9072f2a65759e15189de"
    )
    assert payload["policy_table_count"] == 7
    assert payload["transition_row_count"] == 83
    assert payload["guard_count"] == 91
    assert payload["guard_dependency_edge_count"] == 17
    assert payload["guard_precedence_level_count"] == 13
    assert payload["operator_action_count"] == 16
    assert payload["fixture_counts"] == {"positive": 5, "negative": 18}
    assert payload["scheduler_priority_order"] == [
        "live_process_safety",
        "publication_recovery",
        "deterministic_closeout",
        "cleanup",
        "due_retry",
        "new_promoted_task",
    ]
    assert hashlib.sha256(STATE_POLICY_PATH.read_bytes()).hexdigest() == payload[
        "artifact_sha256"
    ]


@pytest.mark.parametrize(
    ("target", "mutation", "expected_reason"),
    [
        (
            STATE_POLICY_PATH,
            lambda value: value["payload"].__setitem__(
                "baseline_id", "local-ai-runtime-0.2-v3.25"
            ),
            "state_policy_state_policy_identity",
        ),
        (
            GUARD_CATALOG_PATH,
            lambda value: value["precedence_order"].reverse(),
            "state_policy_guard_catalog_identity",
        ),
        (
            OPERATOR_CATALOG_PATH,
            lambda value: value["actions"].pop(),
            "state_policy_operator_catalog_identity",
        ),
        (
            FIXTURE_PATH,
            lambda value: value["negative_mutations"].pop(),
            "state_policy_fixture_identity",
        ),
    ],
)
def test_state_policy_bundle_fails_closed_on_member_identity_drift(
    tmp_path: Path,
    target: Path,
    mutation: Callable[[dict[str, object]], None],
    expected_reason: str,
) -> None:
    _copy_bundle(tmp_path)
    copied = tmp_path / target.relative_to(REPO_ROOT)
    value = json.loads(copied.read_text(encoding="utf-8"))
    mutation(value)
    copied.write_text(
        json.dumps(value, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    completed = _run_component(tmp_path)

    assert completed.returncode == 4
    failure = json.loads(completed.stdout)
    assert failure["status"] == "fail"
    assert failure["reason"] == expected_reason
