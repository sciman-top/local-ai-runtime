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
V2_POLICY_PATH = PRODUCT_ROOT / "normative" / "ProductContract.v2.json"
FIRST_RUN_SCHEMA_PATH = PRODUCT_ROOT / "schemas" / "FirstRunExperience.v1.schema.json"
LAUNCH_TEMPLATE_CATALOG_PATH = (
    PRODUCT_ROOT / "catalogs" / "LaunchTemplateCatalog.v1.json"
)
OPERATOR_PRESENTATION_CATALOG_PATH = (
    PRODUCT_ROOT / "catalogs" / "OperatorPresentationCatalog.v1.json"
)
V2_FIXTURE_PATH = PRODUCT_ROOT / "fixtures" / "product-v2" / "manifest.json"


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
    for source in (
        POLICY_PATH,
        TEMPLATE_SCHEMA_PATH,
        SUBMISSION_SCHEMA_PATH,
        FIXTURE_PATH,
        V2_POLICY_PATH,
        FIRST_RUN_SCHEMA_PATH,
        LAUNCH_TEMPLATE_CATALOG_PATH,
        OPERATOR_PRESENTATION_CATALOG_PATH,
        V2_FIXTURE_PATH,
    ):
        target = tmp_path / source.relative_to(REPO_ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


def test_product_submission_component_closes_declared_contracts() -> None:
    completed = _run_component()
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["status"] == "pass"
    assert payload["component"] == "product-submission"
    assert payload["artifact_version"] == "ProductContract.v2"
    assert payload["artifact_byte_count"] == 14902
    assert payload["artifact_sha256"] == (
        "ef93061279accfd6af7a580d1eafbb3352bf8a8a4f610f7bcd86006643a9bcae"
    )
    assert payload["legacy_artifact_version"] == "ProductContract.v1"
    assert payload["legacy_artifact_byte_count"] == 5003
    assert payload["legacy_artifact_sha256"] == (
        "b239cee308681ac5972e494ad4ff76958623fbd558a47e03b95e0be4159fb1ef"
    )
    assert payload["fixture_counts"] == {
        "first_run_steps": 10,
        "launch_templates": 4,
        "negative": 12,
        "operator_reasons": 8,
        "operator_views": 5,
        "positive": 5,
        "product_metrics": 8,
    }
    assert hashlib.sha256(V2_POLICY_PATH.read_bytes()).hexdigest() == payload[
        "artifact_sha256"
    ]


@pytest.mark.parametrize(
    ("target", "mutation", "expected_reason"),
    [
        (
            V2_POLICY_PATH,
            lambda value: value["payload"].__setitem__(
                "baseline_id", "local-ai-runtime-0.2-v3.25"
            ),
            "product_v2_policy_identity",
        ),
        (
            FIRST_RUN_SCHEMA_PATH,
            lambda value: value.__setitem__("additionalProperties", True),
            "product_v2_first_run_schema_identity",
        ),
        (
            LAUNCH_TEMPLATE_CATALOG_PATH,
            lambda value: value.__setitem__("template_count", 5),
            "product_v2_launch_template_catalog_identity",
        ),
        (
            OPERATOR_PRESENTATION_CATALOG_PATH,
            lambda value: value["render_policy"].__setitem__(
                "human_source", "raw_model_output"
            ),
            "product_v2_operator_presentation_catalog_identity",
        ),
        (
            V2_FIXTURE_PATH,
            lambda value: value.__setitem__("negative_mutations", []),
            "product_v2_fixture_identity",
        ),
    ],
)
def test_product_v2_bundle_fails_closed_on_member_identity_drift(
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
