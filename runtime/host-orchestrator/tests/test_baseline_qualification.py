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
QUALIFICATION_ROOT = REPO_ROOT / "docs" / "specs" / "local-ai-runtime-0.2"
POLICY_PATH = QUALIFICATION_ROOT / "normative" / "QualificationContractSet.v1.json"
SENSITIVE_SCHEMA_PATH = (
    QUALIFICATION_ROOT / "schemas" / "QualificationSensitiveInputSet.v1.schema.json"
)
AUTHORIZATION_SCHEMA_PATH = QUALIFICATION_ROOT / "schemas" / "Authorization.v1.schema.json"
FIXTURE_PATH = QUALIFICATION_ROOT / "fixtures" / "qualification" / "manifest.json"


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
    assert payload["artifact_version"] == "QualificationContractSet.v1"
    assert payload["artifact_byte_count"] == 7336
    assert payload["artifact_sha256"] == (
        "089a60664188fdc86c0de56496c493339246c5b423ddc3271450fb01e4fd6a80"
    )
    assert payload["authorization_fingerprint"] == (
        "a166aedb3c65e4bcf3d0e2cde0d798f6d646b44df50b2d5cd45386841d84b1eb"
    )
    assert payload["sensitive_entry_kind_count"] == 4
    assert payload["fixture_counts"] == {
        "auth_store": 4,
        "continuation": 5,
        "grant_revoke": 5,
        "observation_refresh": 4,
        "sandbox_projection": 6,
        "working_tree": 4,
    }
    assert hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest() == payload[
        "artifact_sha256"
    ]


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
