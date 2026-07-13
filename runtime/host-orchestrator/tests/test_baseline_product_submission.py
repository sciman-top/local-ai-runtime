from __future__ import annotations

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
PRODUCT_ROOT = REPO_ROOT / "docs" / "specs" / "local-ai-runtime-0.2"
POLICY_PATH = PRODUCT_ROOT / "normative" / "ProductContract.v1.json"
TEMPLATE_SCHEMA_PATH = PRODUCT_ROOT / "schemas" / "TaskTemplate.v1.schema.json"
SUBMISSION_SCHEMA_PATH = PRODUCT_ROOT / "schemas" / "BatchSubmission.v1.schema.json"
FIXTURE_PATH = PRODUCT_ROOT / "fixtures" / "submission" / "manifest.json"


def _run_component(repo_root: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VERIFIER_PATH),
            "--repo-root",
            str(repo_root),
            "--component",
            "product-submission",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _copy_bundle(tmp_path: Path) -> None:
    for source in (POLICY_PATH, TEMPLATE_SCHEMA_PATH, SUBMISSION_SCHEMA_PATH, FIXTURE_PATH):
        target = tmp_path / source.relative_to(REPO_ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


def test_product_submission_component_closes_declared_contracts() -> None:
    completed = _run_component()
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["status"] == "pass"
    assert payload["component"] == "product-submission"
    assert payload["artifact_version"] == "ProductContract.v1"
    assert payload["artifact_byte_count"] == 5003
    assert payload["artifact_sha256"] == (
        "b239cee308681ac5972e494ad4ff76958623fbd558a47e03b95e0be4159fb1ef"
    )
    assert payload["fixture_counts"] == {
        "family_replay": 4,
        "resubmission": 5,
        "routing": 6,
        "submission_negative": 5,
        "submission_positive": 1,
        "template_negative": 4,
        "template_positive": 1,
    }
    assert hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest() == payload[
        "artifact_sha256"
    ]


@pytest.mark.parametrize(
    ("target_name", "mutation", "expected_reason"),
    [
        (
            "policy",
            lambda value: value["payload"]["work_routing_policy"].__setitem__(
                "runtime_model_router_service", "present"
            ),
            "product_policy_identity",
        ),
        (
            "template_schema",
            lambda value: value.__setitem__("additionalProperties", True),
            "product_schema_drift",
        ),
        (
            "submission_schema",
            lambda value: value["properties"].__setitem__("model", {"type": "string"}),
            "product_schema_drift",
        ),
        (
            "fixture",
            lambda value: value.__setitem__("routing_cases", None),
            "product_fixture_drift",
        ),
        (
            "fixture",
            lambda value: value.__setitem__("task_template_positive", None),
            "product_fixture_drift",
        ),
        (
            "fixture",
            lambda value: value["submission_positive"].__setitem__("parameters", None),
            "product_fixture_drift",
        ),
        (
            "fixture",
            lambda value: value["family_replay_cases"].__setitem__(0, []),
            "product_fixture_drift",
        ),
    ],
)
def test_product_submission_component_fails_closed_on_bundle_drift(
    tmp_path: Path,
    target_name: str,
    mutation: Callable[[dict[str, object]], None],
    expected_reason: str,
) -> None:
    _copy_bundle(tmp_path)
    targets = {
        "policy": POLICY_PATH,
        "template_schema": TEMPLATE_SCHEMA_PATH,
        "submission_schema": SUBMISSION_SCHEMA_PATH,
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
    verify_component = namespace["verify_product_submission_component"]
    with pytest.raises(failure_type) as captured:
        verify_component(tmp_path)
    assert captured.value.reason == expected_reason


@pytest.mark.parametrize(
    ("target_name", "mutation", "expected_reason"),
    [
        ("template", "invert_integer_bounds", "template_schema"),
        ("submission", "replace_parameters_array", "submission_schema"),
        ("submission", "add_model_parameter", "submission_parameter_influence"),
    ],
)
def test_closed_template_and_submission_validators_reject_boundary_drift(
    target_name: str,
    mutation: str,
    expected_reason: str,
) -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    namespace = runpy.run_path(str(VERIFIER_PATH))
    failure_type = namespace["ValidationFailure"]
    if target_name == "template":
        candidate = fixture["task_template_positive"]
        integer_spec = next(
            definition["value_spec"]
            for definition in candidate["parameter_definitions"]
            if definition["parameter_id"] == "max_files"
        )
        integer_spec.update({"minimum": 11, "maximum": 10})
        validator = namespace["_validate_task_template"]
    else:
        candidate = fixture["submission_positive"]
        if mutation == "replace_parameters_array":
            candidate["parameters"] = []
        else:
            candidate["parameters"]["model"] = "gpt"
        validator = namespace["_validate_batch_submission"]

    with pytest.raises(failure_type) as captured:
        validator(candidate)
    assert captured.value.reason == expected_reason
