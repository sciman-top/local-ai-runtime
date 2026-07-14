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
EXECUTION_ROOT = REPO_ROOT / "docs" / "specs" / "local-ai-runtime-0.2"
POLICY_PATH = EXECUTION_ROOT / "normative" / "ExecutionSafetyContractSet.v1.json"
JOB_SCHEMA_PATH = EXECUTION_ROOT / "schemas" / "JobIdentity.v1.schema.json"
ADOPTION_SCHEMA_PATH = (
    EXECUTION_ROOT / "schemas" / "FencedActionAdoption.v1.schema.json"
)
FIXTURE_PATH = EXECUTION_ROOT / "fixtures" / "execution-safety" / "manifest.json"


def _run_component(repo_root: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VERIFIER_PATH),
            "--repo-root",
            str(repo_root),
            "--component",
            "execution-safety",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _copy_bundle(tmp_path: Path) -> None:
    for source in (POLICY_PATH, JOB_SCHEMA_PATH, ADOPTION_SCHEMA_PATH, FIXTURE_PATH):
        target = tmp_path / source.relative_to(REPO_ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


def test_execution_safety_component_closes_declared_contracts() -> None:
    completed = _run_component()

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload == {
        "status": "pass",
        "component": "execution-safety",
        "artifact_version": "ExecutionSafetyContractSet.v1",
        "artifact_byte_count": 7985,
        "artifact_sha256": (
            "a3e8692e691cfa90fba7fc945f4bb0fa55e5380cb9cbe9550857a053cd25cb12"
        ),
        "job_identity_fingerprint": (
            "7772f4a67c399140f7e31e3f950d0e88434eaf4871a952335c7253e50e5a1d6e"
        ),
        "adoption_fingerprint": (
            "b985e15ade2b0bbeb4cfbbe9fd33e2c48785d8314bd6cd0f7a22cdc4dd0e7002"
        ),
        "fixture_counts": {
            "writer_identity": 4,
            "process_handle": 9,
            "execution_authority": 6,
            "adoption": 7,
            "crash_window": 7,
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
            lambda value: value["payload"]["process_handle_policy"].__setitem__(
                "bInheritHandles", False
            ),
            "execution_safety_policy_identity",
        ),
        (
            "job_schema",
            lambda value: value.__setitem__("additionalProperties", True),
            "execution_safety_schema_drift",
        ),
        (
            "adoption_schema",
            lambda value: value["properties"].__setitem__(
                "new_effect", {"type": "string"}
            ),
            "execution_safety_schema_drift",
        ),
        (
            "fixture",
            lambda value: value.__setitem__("crash_window_cases", None),
            "execution_safety_fixture_drift",
        ),
    ],
)
def test_execution_safety_component_fails_closed_on_bundle_drift(
    tmp_path: Path,
    target_name: str,
    mutation: Callable[[dict[str, object]], None],
    expected_reason: str,
) -> None:
    _copy_bundle(tmp_path)
    targets = {
        "policy": POLICY_PATH,
        "job_schema": JOB_SCHEMA_PATH,
        "adoption_schema": ADOPTION_SCHEMA_PATH,
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
    verify_component = namespace["verify_execution_safety_component"]
    with pytest.raises(failure_type) as captured:
        verify_component(tmp_path)
    assert captured.value.reason == expected_reason


@pytest.mark.parametrize(
    ("target_name", "mutation", "expected_reason"),
    [
        (
            "job_identity_positive",
            lambda value: value.__setitem__(
                "run_uuid", "22222222-2222-4222-8222-222222222222"
            ),
            "job_identity_schema",
        ),
        (
            "job_identity_positive",
            lambda value: value.__setitem__("process_kind", "gate"),
            "job_identity_schema",
        ),
        (
            "job_identity_positive",
            lambda value: value.__setitem__("job_identity_id", "0" * 64),
            "execution_record_fingerprint",
        ),
        (
            "fenced_action_adoption_positive",
            lambda value: value.__setitem__("prior_head_hash", None),
            "fenced_adoption_schema",
        ),
        (
            "fenced_action_adoption_positive",
            lambda value: value.__setitem__("new_fence", value["prior_fence"] + 2),
            "fenced_adoption_schema",
        ),
        (
            "fenced_action_adoption_positive",
            lambda value: value.__setitem__("adoption_hash", "0" * 64),
            "execution_record_fingerprint",
        ),
    ],
)
def test_execution_safety_validators_reject_identity_or_fence_expansion(
    target_name: str,
    mutation: Callable[[dict[str, object]], None],
    expected_reason: str,
) -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    candidate = copy.deepcopy(fixture[target_name])
    mutation(candidate)
    namespace = runpy.run_path(str(VERIFIER_PATH))
    validators = {
        "job_identity_positive": namespace["_validate_job_identity"],
        "fenced_action_adoption_positive": namespace[
            "_validate_fenced_action_adoption"
        ],
    }
    failure_type = namespace["ValidationFailure"]
    with pytest.raises(failure_type) as captured:
        validators[target_name](candidate)
    assert captured.value.reason == expected_reason


def test_execution_safety_rejects_resume_before_execution_commit() -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    case = {
        "case_id": "resume_before_commit",
        "exit_kind": "pre_resume_crash",
        "process_created_suspended": True,
        "execution_committed": False,
        "resume_attempted": True,
        "same_name_error": False,
        "stdout_eof": False,
        "stderr_eof": False,
        "expected_result": "resume_before_commit_forbidden",
    }

    assert namespace["_evaluate_crash_window"](case) == (
        "resume_before_commit_forbidden"
    )
