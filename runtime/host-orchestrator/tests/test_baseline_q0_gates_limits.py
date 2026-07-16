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
CATALOG_PATH = SPEC_ROOT / "normative" / "QualificationGateCatalog.v1.json"
FEATURE_PATH = SPEC_ROOT / "catalogs" / "CodexFeaturePolicy.v1.json"
LIMIT_PATH = SPEC_ROOT / "catalogs" / "ResourceLimitPolicy.v1.json"
FIXTURE_PATH = SPEC_ROOT / "fixtures" / "q0" / "manifest.json"


def _run_component(repo_root: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VERIFIER_PATH),
            "--repo-root",
            str(repo_root),
            "--component",
            "q0-gates-limits",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _copy_bundle(tmp_path: Path) -> None:
    for source in (CATALOG_PATH, FEATURE_PATH, LIMIT_PATH, FIXTURE_PATH):
        target = tmp_path / source.relative_to(REPO_ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


def test_q0_gate_limit_component_closes_declared_contracts() -> None:
    completed = _run_component()

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["status"] == "pass"
    assert payload["component"] == "q0-gates-limits"
    assert payload["artifact_version"] == "QualificationGateCatalog.v1"
    assert payload["validation_class_count"] == 3
    assert payload["q0_probe_set_count"] == 13
    assert payload["resource_limit_count"] == 28
    assert payload["resource_boundary_case_count"] == 84
    assert payload["process_input_limit_count"] == 6
    assert payload["process_input_boundary_case_count"] == 18
    assert payload["environment_fixture_count"] == 9
    assert payload["negative_fixture_count"] == 12
    assert hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest() == payload[
        "artifact_sha256"
    ]


@pytest.mark.parametrize(
    ("target", "mutation", "expected_reason"),
    [
        (
            CATALOG_PATH,
            lambda value: value["payload"]["process_environment_policy"][
                "two_stage_proof"
            ]["pre_resume_parent_environment_proof"].__setitem__(
                "claim_scope", "child_observed_before_resume"
            ),
            "q0_environment_proof",
        ),
        (
            FEATURE_PATH,
            lambda value: value.__setitem__(
                "unknown_effective_capability", "ignore"
            ),
            "q0_feature_policy",
        ),
        (
            LIMIT_PATH,
            lambda value: value["limits"][0].__setitem__(
                "enforcement_class", "hard_quota"
            ),
            "q0_resource_limits",
        ),
        (
            FIXTURE_PATH,
            lambda value: value["resource_boundary_cases"].pop(),
            "q0_fixture_resource_boundaries",
        ),
        (
            FIXTURE_PATH,
            lambda value: value["process_input_boundary_cases"].pop(),
            "q0_fixture_resource_boundaries",
        ),
    ],
)
def test_q0_gate_limit_bundle_fails_closed_on_member_drift(
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
