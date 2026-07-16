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
README_PATH = REPO_ROOT / "README.md"
VERIFIER_PATH = REPO_ROOT / "scripts" / "verify-local-ai-runtime-baseline.py"
QUALIFICATION_ROOT = REPO_ROOT / "docs" / "specs" / "local-ai-runtime-0.2"
POLICY_PATH = QUALIFICATION_ROOT / "normative" / "QualificationContractSet.v1.json"
SENSITIVE_SCHEMA_PATH = (
    QUALIFICATION_ROOT / "schemas" / "QualificationSensitiveInputSet.v1.schema.json"
)
AUTHORIZATION_SCHEMA_PATH = QUALIFICATION_ROOT / "schemas" / "Authorization.v1.schema.json"
FIXTURE_PATH = QUALIFICATION_ROOT / "fixtures" / "qualification" / "manifest.json"
V2_POLICY_PATH = (
    QUALIFICATION_ROOT / "normative" / "QualificationContractSet.v2.json"
)
TOOLCHAIN_SCHEMA_PATH = (
    QUALIFICATION_ROOT / "schemas" / "RuntimeToolchainManifest.v1.schema.json"
)
EXECUTION_PROFILE_PATH = (
    QUALIFICATION_ROOT / "catalogs" / "VerificationExecutionProfile.v1.json"
)
V2_FIXTURE_PATH = QUALIFICATION_ROOT / "fixtures" / "toolchain-v2" / "manifest.json"
ACTIVE_TOOLCHAIN_SURFACE_PATHS = (
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "README.md",
    REPO_ROOT / "docs" / "architecture" / "orchestrator-target-architecture.md",
    REPO_ROOT / "docs" / "architecture" / "planning-status.json",
    REPO_ROOT / "docs" / "architecture" / "next-work-selection-policy.json",
    REPO_ROOT / "docs" / "backlog" / "orchestrator-task-list.md",
    REPO_ROOT / "docs" / "plans" / "local-ai-runtime-0.2-work-items.json",
    REPO_ROOT / "docs" / "plans" / "orchestrator-implementation-plan.md",
    REPO_ROOT / "docs" / "product" / "orchestrator-prd.md",
    REPO_ROOT / "docs" / "roadmap" / "orchestrator-roadmap.md",
    REPO_ROOT / "docs" / "specs" / "acceptance-and-gates.md",
    REPO_ROOT / "docs" / "specs" / "local-ai-runtime-0.2-baseline-candidate.md",
    REPO_ROOT / "docs" / "specs" / "local-ai-runtime-0.2-normative-package.json",
)


def _run_component(repo_root: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VERIFIER_PATH),
            "--repo-root",
            str(repo_root),
            "--component",
            "qualification",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _copy_bundle(tmp_path: Path) -> None:
    for source in (
        POLICY_PATH,
        SENSITIVE_SCHEMA_PATH,
        AUTHORIZATION_SCHEMA_PATH,
        FIXTURE_PATH,
        V2_POLICY_PATH,
        TOOLCHAIN_SCHEMA_PATH,
        EXECUTION_PROFILE_PATH,
        V2_FIXTURE_PATH,
        *ACTIVE_TOOLCHAIN_SURFACE_PATHS,
    ):
        target = tmp_path / source.relative_to(REPO_ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


def test_qualification_component_closes_declared_contracts() -> None:
    completed = _run_component()

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["status"] == "pass"
    assert payload["component"] == "qualification"
    assert payload["artifact_version"] == "QualificationContractSet.v2"
    assert payload["artifact_byte_count"] == 7936
    assert payload["artifact_sha256"] == (
        "4c873185b2eb293c23099d616fb1e754ce073e89491200dcc4e4ac0bb6fc4dac"
    )
    assert payload["legacy_artifact_version"] == "QualificationContractSet.v1"
    assert payload["legacy_artifact_byte_count"] == 7336
    assert payload["legacy_artifact_sha256"] == (
        "089a60664188fdc86c0de56496c493339246c5b423ddc3271450fb01e4fd6a80"
    )
    assert payload["legacy_authorization_fingerprint"] == (
        "a166aedb3c65e4bcf3d0e2cde0d798f6d646b44df50b2d5cd45386841d84b1eb"
    )
    assert payload["legacy_sensitive_entry_kind_count"] == 4
    assert payload["profile_id"] == "new_runtime_exact_v1"
    assert payload["fixed_gate_order"] == [
        "supply_chain_identity",
        "build",
        "test",
        "contract_invariant",
        "hotspot",
    ]
    assert payload["fixture_counts"] == {
        "active_surfaces": 14,
        "backend_requirements": 2,
        "distributions": 2,
        "negative": 12,
        "preparation_commands": 1,
        "pytest_plugins": 1,
        "validation_commands": 10,
    }
    profile = json.loads(EXECUTION_PROFILE_PATH.read_text(encoding="utf-8"))
    preparation = profile["environment_preparation"][0]
    assert "sync --locked --offline --no-python-downloads" in preparation
    assert "sync --exact" not in preparation and "sync --inexact" not in preparation
    assert profile["environment_preparation_semantics"] == (
        "uv_sync_default_exact_and_inexact_forbidden"
    )
    assert {"uv sync --exact", "uv sync --inexact"}.issubset(
        profile["prohibited_active_forms"]
    )
    assert hashlib.sha256(V2_POLICY_PATH.read_bytes()).hexdigest() == payload[
        "artifact_sha256"
    ]


def test_qualification_v2_rejects_unsupported_sync_form_on_active_surface(
    tmp_path: Path,
) -> None:
    _copy_bundle(tmp_path)
    active_readme = tmp_path / README_PATH.relative_to(REPO_ROOT)
    active_readme.write_text(
        active_readme.read_text(encoding="utf-8")
        + "\nuv sync --exact --locked --offline\n",
        encoding="utf-8",
        newline="\n",
    )

    completed = _run_component(tmp_path)

    assert completed.returncode == 4
    failure = json.loads(completed.stdout)
    assert failure["status"] == "fail"
    assert failure["reason"] == "toolchain_prohibited_active_surface"


@pytest.mark.parametrize(
    ("target", "mutation", "expected_reason"),
    [
        (
            V2_POLICY_PATH,
            lambda value: value["payload"].__setitem__(
                "baseline_id", "local-ai-runtime-0.2-v3.25"
            ),
            "qualification_v2_policy_identity",
        ),
        (
            TOOLCHAIN_SCHEMA_PATH,
            lambda value: value.__setitem__("additionalProperties", True),
            "qualification_v2_toolchain_schema_identity",
        ),
        (
            EXECUTION_PROFILE_PATH,
            lambda value: value.__setitem__("environment_preparation_is_gate", True),
            "qualification_v2_execution_profile_identity",
        ),
        (
            V2_FIXTURE_PATH,
            lambda value: value.__setitem__("negative_mutations", []),
            "qualification_v2_fixture_identity",
        ),
    ],
)
def test_qualification_v2_bundle_fails_closed_on_member_identity_drift(
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


@pytest.mark.parametrize(
    ("target_name", "mutation", "expected_reason"),
    [
        (
            "policy",
            lambda value: value["payload"]["auth_state"].__setitem__(
                "allowed_store", "auto"
            ),
            "qualification_policy_identity",
        ),
        (
            "sensitive_schema",
            lambda value: value.__setitem__("additionalProperties", True),
            "qualification_schema_drift",
        ),
        (
            "authorization_schema",
            lambda value: value["properties"].__setitem__(
                "expected_base_commit", {"type": "string"}
            ),
            "qualification_schema_drift",
        ),
        (
            "fixture",
            lambda value: value.__setitem__("sandbox_projection_cases", None),
            "qualification_fixture_drift",
        ),
        (
            "fixture",
            lambda value: value.__setitem__("authorization_positive", None),
            "qualification_fixture_drift",
        ),
    ],
)
def test_qualification_component_fails_closed_on_bundle_drift(
    tmp_path: Path,
    target_name: str,
    mutation: Callable[[dict[str, object]], None],
    expected_reason: str,
) -> None:
    _copy_bundle(tmp_path)
    targets = {
        "policy": POLICY_PATH,
        "sensitive_schema": SENSITIVE_SCHEMA_PATH,
        "authorization_schema": AUTHORIZATION_SCHEMA_PATH,
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
    verify_component = namespace["verify_qualification_component"]
    with pytest.raises(failure_type) as captured:
        verify_component(tmp_path)
    assert captured.value.reason == expected_reason


@pytest.mark.parametrize(
    ("target_name", "mutation", "expected_reason"),
    [
        (
            "sensitive_input_set_positive",
            lambda value: value.__setitem__(
                "expected_base_commit", "1" * 40
            ),
            "sensitive_set_schema",
        ),
        (
            "sensitive_input_set_positive",
            lambda value: value["entries"].reverse(),
            "sensitive_set_order",
        ),
        (
            "sensitive_input_set_positive",
            lambda value: value.__setitem__("local_base_ref", "refs/heads/main.lock"),
            "sensitive_set_schema",
        ),
        (
            "sensitive_input_set_positive",
            lambda value: value.__setitem__("local_base_ref", "refs/heads/a..b"),
            "sensitive_set_schema",
        ),
        (
            "sensitive_input_set_positive",
            lambda value: value.__setitem__("negative_discovery_result", "unknown"),
            "sensitive_set_schema",
        ),
        (
            "authorization_positive",
            lambda value: value.__setitem__(
                "expected_base_commit", "1" * 40
            ),
            "authorization_schema",
        ),
        (
            "authorization_positive",
            lambda value: value.__setitem__("authorization_id", "0" * 64),
            "authorization_fingerprint",
        ),
        (
            "authorization_positive",
            lambda value: value.__setitem__("expires_at_utc", "2026-99-99T00:00:00.000000Z"),
            "authorization_schema",
        ),
        (
            "sandbox_binding_positive",
            lambda value: value.__setitem__("sandbox_secrets_size", 12),
            "sandbox_binding_schema",
        ),
        (
            "environment_binding_positive",
            lambda value: value["batch_setup_actions"].append("install"),
            "environment_binding_schema",
        ),
    ],
)
def test_qualification_validators_reject_identity_or_authority_expansion(
    target_name: str,
    mutation: Callable[[dict[str, object]], None],
    expected_reason: str,
) -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    candidate = copy.deepcopy(fixture[target_name])
    mutation(candidate)
    namespace = runpy.run_path(str(VERIFIER_PATH))
    validators = {
        "sensitive_input_set_positive": namespace["_validate_sensitive_input_set"],
        "authorization_positive": namespace["_validate_authorization"],
        "sandbox_binding_positive": namespace["_validate_sandbox_binding"],
        "environment_binding_positive": namespace["_validate_environment_binding"],
    }
    failure_type = namespace["ValidationFailure"]
    with pytest.raises(failure_type) as captured:
        validators[target_name](candidate)
    assert captured.value.reason == expected_reason
