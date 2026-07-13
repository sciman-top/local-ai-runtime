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
CANONICAL_ROOT = REPO_ROOT / "docs" / "specs" / "local-ai-runtime-0.2"
POLICY_PATH = CANONICAL_ROOT / "normative" / "CanonicalizationPolicy.v1.json"
SCHEMA_PATH = CANONICAL_ROOT / "schemas" / "CanonicalEnvelope.v1.schema.json"
FIXTURE_PATH = CANONICAL_ROOT / "fixtures" / "canonicalization" / "manifest.json"


def _clone(value: object) -> object:
    return json.loads(json.dumps(value))


def _policy_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def _assert_failure(
    failure_type: type[Exception], expected_reason: str, action: Callable[[], object]
) -> None:
    with pytest.raises(failure_type) as captured:
        action()
    assert getattr(captured.value, "reason") == expected_reason


def test_canonicalization_component_closes_declared_contracts() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(VERIFIER_PATH),
            "--component",
            "canonicalization",
            "--self-test",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["status"] == "pass"
    assert payload["component"] == "canonicalization"
    assert payload["artifact_version"] == "CanonicalizationPolicy.v1"
    assert payload["fixture_counts"] == {
        "alias_probe": 8,
        "boundary_dimension": 13,
        "canonical_negative": 13,
        "canonical_positive": 1,
        "git_negative": 15,
        "git_positive": 2,
        "named_object_template": 6,
    }
    raw = POLICY_PATH.read_bytes()
    policy = json.loads(raw.decode("utf-8"))
    assert raw == _policy_bytes(policy)
    assert payload["artifact_sha256"] == hashlib.sha256(raw).hexdigest()


def test_canonicalization_verifier_rejects_malformed_nested_inputs_fail_closed() -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    failure_type = namespace["ValidationFailure"]
    verify_policy = namespace["_verify_canonical_policy"]
    verify_schema = namespace["_verify_canonical_schema"]
    canonicalize_case = namespace["_canonicalize_fixture_case"]
    validate_git_path = namespace["_validate_git_path"]
    validate_git_path_set = namespace["_validate_git_path_set"]
    evaluate_alias_probe = namespace["_evaluate_alias_probe"]
    verify_boundaries = namespace["_verify_boundary_fixtures"]
    verify_named_objects = namespace["_verify_sid_named_objects"]

    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    bounds = policy["payload"]["bounds"]

    malformed_policy = _clone(policy)
    malformed_policy["payload"]["windows_identity"]["policy_query_denied"] = []
    malformed_schema = _clone(schema)
    malformed_schema["$defs"] = []
    malformed_alias = _clone(fixture["alias_probe_cases"][0])
    malformed_alias["policy_observation"] = []
    malformed_boundaries = _clone(fixture)
    malformed_boundaries["boundary_dimensions"][0]["bound_id"] = []
    malformed_named_objects = _clone(policy["payload"])
    malformed_named_objects["named_object_identity"]["templates"] = None
    malformed_git_policy = _clone(policy["payload"])
    malformed_git_policy["git_path"]["dos_device_catalog"] = [[]]

    cases: list[tuple[str, Callable[[], object]]] = [
        (
            "canonical_policy_drift",
            lambda: verify_policy(malformed_policy, _policy_bytes(malformed_policy)),
        ),
        ("canonical_schema_drift", lambda: verify_schema(malformed_schema, bounds)),
        (
            "invalid_utf8_string",
            lambda: canonicalize_case({"raw_json": "\ud800"}, bounds),
        ),
        (
            "invalid_utf8_string",
            lambda: canonicalize_case(
                {
                    "raw_json": (
                        '{"domain":"local-ai-runtime/Test/v1","payload":'
                        '{"\\ud800":"x"},"schema_version":1}'
                    )
                },
                bounds,
            ),
        ),
        (
            "invalid_json",
            lambda: canonicalize_case(
                {"raw_json": "[" * 20000 + "0" + "]" * 20000}, bounds
            ),
        ),
        (
            "canonical_envelope",
            lambda: canonicalize_case(
                {
                    "raw_json": (
                        '{"domain":"local-ai-runtime/Test/v1","payload":{},'
                        '"schema_version":true}'
                    )
                },
                bounds,
            ),
        ),
        (
            "fixture_schema",
            lambda: canonicalize_case(
                {
                    "raw_json": (
                        '{"domain":"local-ai-runtime/Test/v1","payload":{},'
                        '"schema_version":1}'
                    ),
                    "set_semantics": None,
                },
                bounds,
            ),
        ),
        ("fixture_schema", lambda: canonicalize_case(None, bounds)),
        ("fixture_schema", lambda: validate_git_path_set(None, malformed_git_policy)),
        ("fixture_schema", lambda: evaluate_alias_probe(malformed_alias)),
        ("fixture_schema", lambda: verify_boundaries(malformed_boundaries, bounds)),
        (
            "canonical_policy_drift",
            lambda: validate_git_path("src/main.py", malformed_git_policy),
        ),
        (
            "canonical_policy_drift",
            lambda: verify_named_objects(fixture, malformed_named_objects),
        ),
    ]
    for expected_reason, action in cases:
        _assert_failure(failure_type, expected_reason, action)


def test_canonicalization_policy_and_schema_reject_semantic_drift() -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    failure_type = namespace["ValidationFailure"]
    verify_policy = namespace["_verify_canonical_policy"]
    verify_schema = namespace["_verify_canonical_schema"]
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    bounds = policy["payload"]["bounds"]

    policy_mutations = [
        lambda value: value["payload"]["canonical_json"][
            "domain_envelope"
        ].__setitem__("schema_version", True),
        lambda value: value["payload"]["canonical_json"].__setitem__(
            "serialization", "implementation_defined"
        ),
        lambda value: value["payload"]["git_path"].__setitem__(
            "collision_detection", "allow"
        ),
        lambda value: value["payload"]["named_object_identity"].__setitem__(
            "templates", []
        ),
        lambda value: value["payload"]["sid_identity"].__setitem__(
            "sid_hash", "implementation_defined"
        ),
        lambda value: value["payload"]["windows_identity"][
            "policy_query_denied"
        ].__setitem__("required_fallback", "none"),
    ]
    for mutate in policy_mutations:
        candidate = _clone(policy)
        mutate(candidate)
        _assert_failure(
            failure_type,
            "canonical_policy_drift",
            lambda candidate=candidate: verify_policy(
                candidate, _policy_bytes(candidate)
            ),
        )

    schema_mutations = [
        lambda value: value.__setitem__("type", "array"),
        lambda value: value["properties"]["schema_version"].__setitem__(
            "const", True
        ),
        lambda value: value["properties"]["payload"].__setitem__(
            "$ref", "#/$defs/other"
        ),
        lambda value: value["properties"]["domain"].__setitem__("pattern", ".*"),
        lambda value: value["$defs"]["canonical_value"]["oneOf"][3][
            "items"
        ].__setitem__("$ref", "#/$defs/other"),
        lambda value: value["$defs"]["canonical_value"]["oneOf"][4].__setitem__(
            "additionalProperties", True
        ),
    ]
    for mutate in schema_mutations:
        candidate = _clone(schema)
        mutate(candidate)
        _assert_failure(
            failure_type,
            "canonical_schema_drift",
            lambda candidate=candidate: verify_schema(candidate, bounds),
        )


def test_canonicalization_component_rejects_malformed_git_fixture_fail_closed(
    tmp_path: Path,
) -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    failure_type = namespace["ValidationFailure"]
    verify_component = namespace["verify_canonicalization_component"]
    for source in (POLICY_PATH, SCHEMA_PATH, FIXTURE_PATH):
        relative = source.relative_to(REPO_ROOT)
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())

    fixture_target = tmp_path / FIXTURE_PATH.relative_to(REPO_ROOT)
    fixture = json.loads(fixture_target.read_text(encoding="utf-8"))
    fixture["git_negative_cases"][0]["raw_utf8_hex"] = []
    fixture_target.write_text(
        json.dumps(fixture, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    _assert_failure(
        failure_type,
        "fixture_schema",
        lambda: verify_component(tmp_path),
    )
