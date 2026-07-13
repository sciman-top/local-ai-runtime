#!/usr/bin/env python3
"""Fail-closed verifier for the Local AI Runtime normative package.

LAR-P0A-002 implements only the BaselineManifest contract self-test. Later
P0A tasks extend the component catalog; full-package verification remains
incomplete until every required component is implemented and frozen.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from typing import Any, Callable


MANIFEST_DOMAIN = "local-ai-runtime/BaselineManifest/v1"
MANIFEST_VERSION = "BaselineManifest.v1"
MANIFEST_SCHEMA_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/normative/BaselineManifest.v1.schema.json"
)
MANIFEST_FIXTURE_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/fixtures/baseline-bytes/manifest.json"
)
FINAL_MANIFEST_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/normative/BaselineManifest.v1.json"
)
CANONICAL_POLICY_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/normative/CanonicalizationPolicy.v1.json"
)
CANONICAL_SCHEMA_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/schemas/CanonicalEnvelope.v1.schema.json"
)
CANONICAL_FIXTURE_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/fixtures/canonicalization/manifest.json"
)
PRODUCT_POLICY_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/normative/ProductContract.v1.json"
)
TASK_TEMPLATE_SCHEMA_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/schemas/TaskTemplate.v1.schema.json"
)
BATCH_SUBMISSION_SCHEMA_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/schemas/BatchSubmission.v1.schema.json"
)
PRODUCT_FIXTURE_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/fixtures/submission/manifest.json"
)
BASELINE_SPECIFICATION_ID = "local-ai-runtime-0.2-v3.23"
BASELINE_FIXTURE_MANIFEST_ID = f"{BASELINE_SPECIFICATION_ID}-fixture"
BOUND_ARTIFACTS = {
    "P0A-SOURCE": {
        "artifact_id": "P0A-SOURCE",
        "artifact_version": BASELINE_SPECIFICATION_ID,
        "artifact_role": "narrative_specification",
        "path": "docs/specs/local-ai-runtime-0.2-v3.23-baseline-candidate.md",
        "byte_count": 188325,
        "sha256": "80562322ebc744eda2a87a17c45f73a11982f4947c9d10e8628bb6f73ee9d5c6",
        "schema_version": "narrative.v1",
        "verifier_id": "SpecificationBytePolicy.v1",
    },
    "P0A-LINEAGE": {
        "artifact_id": "P0A-LINEAGE",
        "artifact_version": "BaselineLineage.v2",
        "artifact_role": "lineage",
        "path": "docs/specs/local-ai-runtime-0.2/normative/BaselineLineage.v2.json",
        "byte_count": 3495,
        "sha256": "49141a69c9aed6065ba063714fb2349750e500199ed8dfaf64fa6e2b198b9043",
        "schema_version": "BaselineLineage.v2",
        "verifier_id": "LocalAIRuntimeBaselineVerifier.v1",
    },
}
FORBIDDEN_ARTIFACT_IDS = {
    "P0A-MANIFEST",
    "P0A-REVIEW",
    "BaselineApprovalRecord.v1",
}
REQUIRED_ENTRY_FIELDS = {
    "artifact_id",
    "artifact_version",
    "artifact_role",
    "path",
    "byte_count",
    "sha256",
    "schema_version",
    "verifier_id",
}
REQUIRED_PAYLOAD_FIELDS = {
    "manifest_id",
    "manifest_version",
    "narrative_specification_id",
    "artifacts",
    "package_review_head",
}
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
PUBLIC_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,62}$")
PUBLIC_VALUE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,255}$")
SHA1_PATTERN = re.compile(r"^[0-9a-f]{40}$")
CANONICAL_DOMAIN_PATTERN = re.compile(
    r"^local-ai-runtime/[A-Za-z0-9][A-Za-z0-9._-]{0,95}/v1$"
)
SID_PATTERN = re.compile(r"^S-[0-9]+(?:-[0-9]+)+$")
UUID_V4_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
ALLOWED_UNICODE_CATEGORIES = {
    "Ll",
    "Lm",
    "Lo",
    "Lt",
    "Lu",
    "Mc",
    "Me",
    "Mn",
    "Nd",
    "Nl",
    "No",
    "Pc",
    "Pd",
    "Pe",
    "Pf",
    "Pi",
    "Po",
    "Ps",
    "Sc",
    "Sk",
    "Sm",
    "So",
    "Zs",
}
EXPECTED_CANONICAL_BOUNDS = {
    "array_items": 256,
    "depth": 32,
    "git_path_components": 64,
    "git_path_utf8_bytes": 1024,
    "identifier_utf8_bytes": 128,
    "integer_max": 9223372036854775807,
    "integer_min": -9223372036854775808,
    "json_input_bytes": 65536,
    "named_object_ascii_bytes": 260,
    "object_members": 256,
    "set_items": 256,
    "sid_ascii_bytes": 184,
    "string_utf8_bytes": 4096,
}
EXPECTED_DOS_DEVICE_CATALOG = [
    "AUX",
    "CLOCK$",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "COM\u00b9",
    "COM\u00b2",
    "COM\u00b3",
    "CON",
    "CONIN$",
    "CONOUT$",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
    "LPT\u00b9",
    "LPT\u00b2",
    "LPT\u00b3",
    "NUL",
    "PRN",
]
EXPECTED_NAMED_OBJECT_TEMPLATES = [
    "Global\\LocalAIRuntime.BatchDrain.<SIDHash>.v1",
    "Global\\LocalAIRuntime.OwnershipRegistry.<SIDHash>.v1",
    "Global\\LocalAIRuntime.RepoOwnership.<SIDHash>.<RepoIdentityHash>.v1",
    "Global\\LocalAIRuntime.Attempt.<SIDHash>.<attempt_uuid>.v1",
    "Global\\LocalAIRuntime.Job.<SIDHash>.<attempt_uuid>.v1",
    "Global\\LocalAIRuntime.StageJob.<SIDHash>.<attempt_uuid>.<run_uuid>.v1",
]
EXPECTED_GIT_PATH_REJECTIONS = [
    "invalid_utf8",
    "non_nfc",
    "absolute",
    "drive_absolute",
    "empty_component",
    "dot_component",
    "dotdot_component",
    "backslash",
    "alternate_data_stream",
    "dos_device",
    "unicode_disallowed",
    "trailing_dot_or_space",
    "windows_case_collision",
]
EXPECTED_WINDOWS_AUTHORIZATION_BASIS = [
    "no_follow_handle",
    "volume_identity",
    "file_id_128",
    "expected_root_ancestry",
    "owner_dacl",
    "reparse_hardlink_policy",
]
EXPECTED_UPPERCASE_CATALOG = {
    "algorithm_id": "unicode_default_uppercase_v15.1.0_invariant",
    "conditional_special_casing": "excluded",
    "input_units": "unicode_scalar_values",
    "locale": "invariant",
    "mapping_order": "unicode_data_simple_uppercase_then_unconditional_special_casing",
    "normalization": "none",
    "output_units": "full_uppercase_scalar_sequence",
    "special_casing": {
        "byte_count": 16832,
        "sha256": "55a477efd933a52cd27e6a9bf70265bb2d8814af31aab07767abc8eb421f27ef",
        "url": "https://www.unicode.org/Public/15.1.0/ucd/SpecialCasing.txt",
    },
    "unicode_data": {
        "byte_count": 1914200,
        "sha256": "2fc713e6a31a87c4850a37fe2caffa4218180fadb5de86b43a143ddb4581fb86",
        "url": "https://www.unicode.org/Public/15.1.0/ucd/UnicodeData.txt",
    },
    "unicode_version": "15.1.0",
}
EXPECTED_PRODUCT_IDENTITIES = {
    "policy": {
        "byte_count": 5003,
        "sha256": "b239cee308681ac5972e494ad4ff76958623fbd558a47e03b95e0be4159fb1ef",
    },
    "task_template_schema": {
        "byte_count": 3956,
        "sha256": "a9332c772cc64b4e3530ff52afa1f4137c696d500bf2a35cf9c02af58d489ab3",
    },
    "batch_submission_schema": {
        "byte_count": 1424,
        "sha256": "4b7285427ac4878bca9e20a84f2774a31783a8499cccb71d1ebeac8e60c5b3fd",
    },
    "fixture": {
        "byte_count": 7411,
        "sha256": "cd9787660be95db2e1ce8ff8b303eee8e819f8567582cbc5f406e32cce715cf1",
    },
}
FORBIDDEN_PARAMETER_IDS = {
    "argv",
    "authorization",
    "command",
    "contract_generation",
    "environment",
    "executable",
    "feature",
    "gate_set",
    "git_policy",
    "git_ref",
    "model",
    "permission_root",
    "prompt",
    "provider",
    "sandbox",
}


class ValidationFailure(ValueError):
    """A stable, expected contract rejection."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationFailure("duplicate_json_key", f"duplicate JSON key: {key!a}")
        result[key] = value
    return result


def _load_json_object(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValidationFailure("unreadable_file", f"cannot read {path}: {exc}") from exc
    validate_normative_bytes(raw, str(path))
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicates)
    except (json.JSONDecodeError, RecursionError) as exc:
        detail = getattr(exc, "msg", "maximum JSON nesting exceeded")
        raise ValidationFailure("invalid_json", f"invalid JSON in {path}: {detail}") from exc
    if not isinstance(value, dict):
        raise ValidationFailure("invalid_json_root", f"JSON root must be an object: {path}")
    return value, raw


def _is_noncharacter(codepoint: int) -> bool:
    return 0xFDD0 <= codepoint <= 0xFDEF or codepoint & 0xFFFF in {0xFFFE, 0xFFFF}


def validate_normative_bytes(raw: bytes, label: str) -> None:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValidationFailure("utf8_bom", f"{label} contains a UTF-8 BOM")
    if b"\r" in raw:
        raise ValidationFailure("cr", f"{label} contains CR")
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        raise ValidationFailure("terminal_lf", f"{label} must end with exactly one LF")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValidationFailure("invalid_utf8", f"{label} is not valid UTF-8") from exc
    if text != unicodedata.normalize("NFC", text):
        raise ValidationFailure("non_nfc", f"{label} is not Unicode NFC")
    for line_number, line in enumerate(text.split("\n"), start=1):
        if line.endswith((" ", "\t")):
            raise ValidationFailure(
                "trailing_whitespace",
                f"{label} has trailing SP/HTAB at line {line_number}",
            )
    for character in text:
        if character == "\n":
            continue
        category = unicodedata.category(character)
        if category == "Cc":
            raise ValidationFailure(
                "control_character", f"{label} contains disallowed Unicode Cc"
            )
        if category == "Cf":
            raise ValidationFailure(
                "format_character", f"{label} contains disallowed Unicode Cf"
            )
        if category in {"Zl", "Zp"}:
            raise ValidationFailure(
                "line_separator", f"{label} contains a non-LF separator"
            )
        if _is_noncharacter(ord(character)):
            raise ValidationFailure(
                "unicode_noncharacter", f"{label} contains a Unicode noncharacter"
            )


def _require_object(
    value: Any, label: str, *, reason: str = "schema_violation"
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationFailure(reason, f"{label} must be an object")
    return value


def _require_array(
    value: Any, label: str, *, reason: str = "schema_violation"
) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationFailure(reason, f"{label} must be an array")
    return value


def _require_string_array(
    value: Any, label: str, *, reason: str = "schema_violation"
) -> list[str]:
    items = _require_array(value, label, reason=reason)
    if not all(isinstance(item, str) for item in items):
        raise ValidationFailure(reason, f"{label} must contain only strings")
    return items


def _require_exact_fields(
    value: Any,
    required: set[str],
    label: str,
    *,
    reason: str = "schema_violation",
) -> dict[str, Any]:
    value = _require_object(value, label, reason=reason)
    actual = set(value)
    if actual != required:
        unknown = sorted(actual - required)
        missing = sorted(required - actual)
        failure_reason = (
            "unknown_payload_field"
            if reason == "schema_violation" and label == "payload" and unknown
            else reason
        )
        raise ValidationFailure(
            failure_reason,
            f"{label} fields mismatch: missing={missing}, unknown={unknown}",
        )
    return value


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _json_values_equal(actual: Any, expected: Any) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(actual) == set(expected) and all(
            _json_values_equal(actual[key], expected[key]) for key in expected
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            _json_values_equal(actual_item, expected_item)
            for actual_item, expected_item in zip(actual, expected)
        )
    return actual == expected


def _validate_identifier(value: Any, label: str) -> None:
    if not isinstance(value, str) or IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValidationFailure("schema_violation", f"{label} is not a valid identifier")


def _validate_repo_relative_path(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise ValidationFailure("schema_violation", f"{label} is not a bounded path")
    if value.startswith("/") or ":" in value or "\\" in value or "//" in value:
        raise ValidationFailure("schema_violation", f"{label} is not repo-relative")
    components = value.split("/")
    if any(component in {"", ".", ".."} for component in components):
        raise ValidationFailure("schema_violation", f"{label} contains a traversal component")
    if any(unicodedata.category(character) in {"Cc", "Cf", "Zl", "Zp"} for character in value):
        raise ValidationFailure("schema_violation", f"{label} contains disallowed characters")


def validate_manifest(value: Any) -> None:
    envelope = _require_exact_fields(value, {"domain", "schema_version", "payload"}, "manifest")
    if envelope["domain"] != MANIFEST_DOMAIN or envelope["schema_version"] != 1:
        raise ValidationFailure("schema_violation", "manifest envelope identity mismatch")
    payload = _require_exact_fields(envelope["payload"], REQUIRED_PAYLOAD_FIELDS, "payload")
    if payload["manifest_version"] != MANIFEST_VERSION:
        raise ValidationFailure("schema_violation", "manifest_version mismatch")
    for field in ("manifest_id", "narrative_specification_id"):
        _validate_identifier(payload[field], field)

    artifacts = payload["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        raise ValidationFailure("schema_violation", "artifacts must be a non-empty array")
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for index, raw_entry in enumerate(artifacts):
        entry = _require_exact_fields(raw_entry, REQUIRED_ENTRY_FIELDS, f"artifacts[{index}]")
        artifact_id = entry["artifact_id"]
        path = entry["path"]
        if artifact_id in seen_ids:
            raise ValidationFailure("duplicate_artifact_id", f"duplicate artifact ID: {artifact_id}")
        if path in seen_paths:
            raise ValidationFailure("duplicate_artifact_path", f"duplicate artifact path: {path}")
        seen_ids.add(artifact_id)
        seen_paths.add(path)
        if artifact_id in FORBIDDEN_ARTIFACT_IDS or path.endswith(
            ("/BaselineManifest.v1.json", "/ReviewEvidenceIndex.v1.json", "/BaselineApprovalRecord.v1.json")
        ):
            raise ValidationFailure(
                "forbidden_artifact_role", f"manifest closure self-reference: {artifact_id}"
            )
        for field in ("artifact_id", "artifact_version", "schema_version", "verifier_id"):
            _validate_identifier(entry[field], f"artifacts[{index}].{field}")
        _validate_repo_relative_path(entry["path"], f"artifacts[{index}].path")
        if entry["artifact_role"] not in {
            "narrative_specification",
            "lineage",
            "schema",
            "catalog",
            "policy",
            "transition_table",
            "example",
            "negative_fixture",
            "migration_specification",
            "verifier",
        }:
            raise ValidationFailure("schema_violation", f"artifacts[{index}].artifact_role is invalid")
        if not isinstance(entry["byte_count"], int) or isinstance(entry["byte_count"], bool) or entry["byte_count"] < 1:
            raise ValidationFailure("schema_violation", f"artifacts[{index}].byte_count is invalid")
        if not _is_sha256(entry["sha256"]):
            raise ValidationFailure("schema_violation", f"artifacts[{index}].sha256 is invalid")

    review_head = _require_exact_fields(
        payload["package_review_head"],
        {"index_id", "sequence", "entry_sha256", "frozen"},
        "package_review_head",
    )
    if review_head["index_id"] != "ReviewEvidenceIndex.v1":
        raise ValidationFailure("schema_violation", "package_review_head index mismatch")
    if review_head["frozen"] is not True:
        raise ValidationFailure("package_review_head_not_frozen", "package_review_head must be frozen")
    if not isinstance(review_head["sequence"], int) or isinstance(review_head["sequence"], bool) or review_head["sequence"] < 1:
        raise ValidationFailure("schema_violation", "package_review_head sequence is invalid")
    if not _is_sha256(review_head["entry_sha256"]):
        raise ValidationFailure("schema_violation", "package_review_head hash is invalid")


def _verify_schema_contract(schema: dict[str, Any]) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValidationFailure("schema_contract_drift", "schema dialect mismatch")
    payload = schema.get("$defs", {}).get("payload", {})
    entry = schema.get("$defs", {}).get("artifact_entry", {})
    review = schema.get("$defs", {}).get("review_head", {})
    if payload.get("additionalProperties") is not False or set(payload.get("required", [])) != REQUIRED_PAYLOAD_FIELDS:
        raise ValidationFailure("schema_contract_drift", "payload closure mismatch")
    if entry.get("additionalProperties") is not False or set(entry.get("required", [])) != REQUIRED_ENTRY_FIELDS:
        raise ValidationFailure("schema_contract_drift", "artifact entry closure mismatch")
    if review.get("properties", {}).get("frozen", {}).get("const") is not True:
        raise ValidationFailure("schema_contract_drift", "review head is not frozen by schema")
    if "manifest_sha256" in payload.get("properties", {}):
        raise ValidationFailure("schema_contract_drift", "schema embeds manifest self-hash")


def _verify_fixture_bindings(valid_manifest: dict[str, Any], repo_root: Path) -> None:
    payload = valid_manifest["payload"]
    if payload["manifest_id"] != BASELINE_FIXTURE_MANIFEST_ID:
        raise ValidationFailure("fixture_binding_mismatch", "manifest_id is not v3.23-bound")
    if payload["narrative_specification_id"] != BASELINE_SPECIFICATION_ID:
        raise ValidationFailure(
            "fixture_binding_mismatch", "narrative_specification_id is not v3.23-bound"
        )

    artifacts = {entry["artifact_id"]: entry for entry in payload["artifacts"]}
    if set(artifacts) != set(BOUND_ARTIFACTS):
        raise ValidationFailure(
            "fixture_binding_mismatch",
            f"bound artifact IDs mismatch: {sorted(artifacts)}",
        )
    for artifact_id, expected in BOUND_ARTIFACTS.items():
        entry = artifacts[artifact_id]
        if entry != expected:
            raise ValidationFailure(
                "fixture_binding_mismatch", f"{artifact_id} fixture identity mismatch"
            )
        artifact_path = repo_root / expected["path"]
        try:
            raw = artifact_path.read_bytes()
        except OSError as exc:
            raise ValidationFailure(
                "unreadable_file", f"cannot read bound artifact {artifact_path}: {exc}"
            ) from exc
        validate_normative_bytes(raw, str(artifact_path))
        if (
            len(raw) != expected["byte_count"]
            or hashlib.sha256(raw).hexdigest() != expected["sha256"]
        ):
            raise ValidationFailure(
                "bound_artifact_identity_mismatch",
                f"{artifact_id} bytes do not match the frozen v3.23 identity",
            )


def _structural_mutations() -> dict[str, Callable[[dict[str, Any]], None]]:
    def duplicate_id(value: dict[str, Any]) -> None:
        entry = copy.deepcopy(value["payload"]["artifacts"][0])
        entry["path"] = "docs/specs/duplicate-source.md"
        value["payload"]["artifacts"].append(entry)

    def duplicate_path(value: dict[str, Any]) -> None:
        entry = copy.deepcopy(value["payload"]["artifacts"][0])
        entry["artifact_id"] = "P0A-DUPLICATE"
        value["payload"]["artifacts"].append(entry)

    def append_forbidden(value: dict[str, Any], artifact_id: str, path: str) -> None:
        entry = copy.deepcopy(value["payload"]["artifacts"][0])
        entry["artifact_id"] = artifact_id
        entry["artifact_version"] = artifact_id
        entry["path"] = path
        value["payload"]["artifacts"].append(entry)

    return {
        "duplicate_first_artifact_with_new_path": duplicate_id,
        "duplicate_first_artifact_with_new_id": duplicate_path,
        "add_payload_manifest_sha256": lambda value: value["payload"].__setitem__("manifest_sha256", "0" * 64),
        "append_manifest_artifact": lambda value: append_forbidden(value, "P0A-MANIFEST", "docs/specs/local-ai-runtime-0.2/normative/BaselineManifest.v1.json"),
        "append_review_index_artifact": lambda value: append_forbidden(value, "P0A-REVIEW", "docs/reviews/local-ai-runtime-0.2/ReviewEvidenceIndex.v1.json"),
        "append_approval_record_artifact": lambda value: append_forbidden(value, "BaselineApprovalRecord.v1", "docs/specs/local-ai-runtime-0.2/normative/BaselineApprovalRecord.v1.json"),
        "set_package_review_head_unfrozen": lambda value: value["payload"]["package_review_head"].__setitem__("frozen", False),
    }


def _mutate_bytes(raw: bytes, mutation: str) -> bytes:
    mutations = {
        "prefix_utf8_bom": lambda: b"\xef\xbb\xbf" + raw,
        "replace_lf_with_crlf": lambda: raw.replace(b"\n", b"\r\n", 1),
        "insert_decomposed_character": lambda: raw[:-1] + "e\u0301".encode("utf-8") + b"\n",
        "add_trailing_space_before_lf": lambda: raw[:-1] + b" \n",
        "insert_horizontal_tab": lambda: raw.replace(
            b'"fixture_id"', b'"fixture\t_id"', 1
        ),
        "insert_bidi_control": lambda: raw[:-1] + "\u202e".encode("utf-8") + b"\n",
        "remove_terminal_lf": lambda: raw[:-1],
        "append_terminal_lf": lambda: raw + b"\n",
    }
    try:
        return mutations[mutation]()
    except KeyError as exc:
        raise ValidationFailure("unknown_fixture_mutation", f"unknown byte mutation: {mutation}") from exc


def verify_manifest_component(repo_root: Path) -> dict[str, Any]:
    schema, _ = _load_json_object(repo_root / MANIFEST_SCHEMA_RELATIVE)
    fixture, fixture_raw = _load_json_object(repo_root / MANIFEST_FIXTURE_RELATIVE)
    _verify_schema_contract(schema)
    valid_manifest = fixture.get("valid_manifest")
    validate_manifest(valid_manifest)
    _verify_fixture_bindings(valid_manifest, repo_root)

    structural_count = 0
    mutations = _structural_mutations()
    for case in fixture.get("structural_negative_cases", []):
        candidate = copy.deepcopy(valid_manifest)
        mutation = mutations.get(case.get("mutation"))
        if mutation is None:
            raise ValidationFailure("unknown_fixture_mutation", str(case.get("mutation")))
        mutation(candidate)
        try:
            validate_manifest(candidate)
        except ValidationFailure as exc:
            if exc.reason != case.get("expected_reason"):
                raise ValidationFailure(
                    "fixture_reason_mismatch",
                    f"{case.get('case_id')}: expected {case.get('expected_reason')}, got {exc.reason}",
                ) from exc
        else:
            raise ValidationFailure("negative_fixture_accepted", str(case.get("case_id")))
        structural_count += 1

    byte_count = 0
    for case in fixture.get("byte_negative_cases", []):
        candidate = _mutate_bytes(fixture_raw, str(case.get("mutation")))
        try:
            validate_normative_bytes(candidate, str(case.get("case_id")))
        except ValidationFailure as exc:
            if exc.reason != case.get("expected_reason"):
                raise ValidationFailure(
                    "fixture_reason_mismatch",
                    f"{case.get('case_id')}: expected {case.get('expected_reason')}, got {exc.reason}",
                ) from exc
        else:
            raise ValidationFailure("negative_fixture_accepted", str(case.get("case_id")))
        byte_count += 1

    if (repo_root / FINAL_MANIFEST_RELATIVE).exists():
        raise ValidationFailure(
            "premature_final_manifest", "LAR-P0A-002 must not create BaselineManifest.v1.json"
        )
    return {
        "status": "pass",
        "component": "manifest",
        "schema_version": MANIFEST_VERSION,
        "narrative_specification_id": BASELINE_SPECIFICATION_ID,
        "bound_artifact_count": len(BOUND_ARTIFACTS),
        "positive_fixture_count": 1,
        "structural_negative_fixture_count": structural_count,
        "byte_negative_fixture_count": byte_count,
        "final_manifest_exists": False,
    }


def _verify_canonical_policy(policy: dict[str, Any], raw: bytes) -> dict[str, Any]:
    try:
        canonical = (
            json.dumps(
                policy,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
    except (RecursionError, TypeError, UnicodeEncodeError) as exc:
        raise ValidationFailure(
            "canonical_policy_bytes", "CanonicalizationPolicy is not canonical UTF-8 JSON"
        ) from exc
    if raw != canonical:
        raise ValidationFailure(
            "canonical_policy_bytes", "CanonicalizationPolicy must use canonical JSON bytes"
        )
    envelope = _require_exact_fields(
        policy, {"domain", "payload", "schema_version"}, "canonical policy"
    )
    if (
        envelope["domain"] != "local-ai-runtime/CanonicalizationPolicy/v1"
        or type(envelope["schema_version"]) is not int
        or envelope["schema_version"] != 1
    ):
        raise ValidationFailure(
            "canonical_policy_identity", "CanonicalizationPolicy envelope mismatch"
        )
    payload = _require_exact_fields(
        envelope["payload"],
        {
            "artifact_id",
            "artifact_version",
            "baseline_id",
            "bounds",
            "canonical_json",
            "git_path",
            "named_object_identity",
            "sid_identity",
            "windows_identity",
        },
        "canonical policy payload",
    )
    if (
        payload["artifact_id"] != "P0A-CANONICAL"
        or payload["artifact_version"] != "CanonicalizationPolicy.v1"
        or payload["baseline_id"] != BASELINE_SPECIFICATION_ID
    ):
        raise ValidationFailure(
            "canonical_policy_identity", "canonical artifact binding mismatch"
        )
    if not _json_values_equal(payload["bounds"], EXPECTED_CANONICAL_BOUNDS):
        raise ValidationFailure("canonical_bounds_drift", "canonical bounds mismatch")
    canonical_json = _require_object(
        payload["canonical_json"],
        "canonical JSON policy",
        reason="canonical_policy_drift",
    )
    _require_exact_fields(
        canonical_json,
        {
            "array_default",
            "domain_envelope",
            "duplicate_keys",
            "float",
            "hash",
            "integer",
            "nullable_optional",
            "object_key_order",
            "serialization",
            "set_semantics",
            "strings",
            "unknown_fields",
        },
        "canonical JSON policy",
        reason="canonical_policy_drift",
    )
    domain_envelope = _require_exact_fields(
        canonical_json["domain_envelope"],
        {"exact_fields", "pattern", "schema_version"},
        "domain envelope policy",
        reason="canonical_policy_drift",
    )
    if {
        "duplicate_keys": canonical_json.get("duplicate_keys"),
        "float": canonical_json.get("float"),
        "object_key_order": canonical_json.get("object_key_order"),
        "array_default": canonical_json.get("array_default"),
    } != {
        "duplicate_keys": "reject",
        "float": "reject",
        "object_key_order": "utf8_byte_lexicographic",
        "array_default": "preserve_input_order",
    } or not _json_values_equal(domain_envelope, {
        "exact_fields": ["domain", "payload", "schema_version"],
        "pattern": "local-ai-runtime/<object-type>/v1",
        "schema_version": 1,
    }) or {
        "hash": canonical_json.get("hash"),
        "integer": canonical_json.get("integer"),
        "nullable_optional": canonical_json.get("nullable_optional"),
        "serialization": canonical_json.get("serialization"),
        "unknown_fields": canonical_json.get("unknown_fields"),
    } != {
        "hash": "lowercase_sha256_of_canonical_utf8_envelope_excluding_self_hash_fields",
        "integer": "schema_bounded_signed_integer_only",
        "nullable_optional": "reject_use_absent_field",
        "serialization": (
            "utf8_no_bom_no_extra_whitespace_minimal_json_escaping_terminal_lf"
        ),
        "unknown_fields": "reject_by_object_schema",
    }:
        raise ValidationFailure(
            "canonical_policy_drift", "canonical JSON behavior mismatch"
        )
    set_policy = _require_exact_fields(
        canonical_json.get("set_semantics"),
        {"declaration", "duplicate_sort_key", "sort"},
        "set policy",
        reason="canonical_policy_drift",
    )
    if not _json_values_equal(set_policy, {
        "declaration": "schema_keyword_x-local-ai-runtime-set-semantics",
        "duplicate_sort_key": "reject",
        "sort": "canonical_utf8_bytes_of_declared_unique_sort_key",
    }):
        raise ValidationFailure("canonical_policy_drift", "set semantics mismatch")
    string_policy = _require_exact_fields(
        canonical_json.get("strings"),
        {
            "allowed_general_categories",
            "noncharacters",
            "normalization",
            "rewrite",
            "unapproved_general_categories",
        },
        "string policy",
        reason="canonical_policy_drift",
    )
    allowed_categories = _require_string_array(
        string_policy.get("allowed_general_categories"),
        "allowed Unicode categories",
        reason="canonical_policy_drift",
    )
    unapproved_categories = _require_string_array(
        string_policy.get("unapproved_general_categories"),
        "unapproved Unicode categories",
        reason="canonical_policy_drift",
    )
    if (
        set(allowed_categories) != ALLOWED_UNICODE_CATEGORIES
        or set(unapproved_categories) != {"Cc", "Cf", "Cn", "Co", "Cs", "Zl", "Zp"}
        or string_policy.get("normalization") != "already_nfc"
        or string_policy.get("rewrite") != "none"
        or string_policy.get("noncharacters") != "reject"
    ):
        raise ValidationFailure("canonical_policy_drift", "string allowlist mismatch")
    git_policy = _require_exact_fields(
        payload["git_path"],
        {
            "collision_detection",
            "dos_device_catalog",
            "preserve",
            "reject",
            "windows_collision_key",
        },
        "Git path policy",
        reason="canonical_policy_drift",
    )
    dos_devices = _require_string_array(
        git_policy.get("dos_device_catalog"),
        "DOS device catalog",
        reason="canonical_policy_drift",
    )
    rejection_catalog = _require_string_array(
        git_policy.get("reject"),
        "Git rejection catalog",
        reason="canonical_policy_drift",
    )
    if (
        git_policy.get("collision_detection")
        != "reject_duplicate_windows_collision_key_within_closed_path_set"
        or dos_devices != EXPECTED_DOS_DEVICE_CATALOG
        or git_policy.get("preserve")
        != "original_utf8_spelling_case_and_forward_slash"
        or rejection_catalog != EXPECTED_GIT_PATH_REJECTIONS
        or git_policy.get("windows_collision_key")
        != "separate_derived_value_never_replaces_git_path"
    ):
        raise ValidationFailure("canonical_policy_drift", "Git path policy mismatch")
    windows_policy = _require_exact_fields(
        payload["windows_identity"],
        {
            "alias_authority",
            "alias_mapping_drift",
            "authorization_basis",
            "global_8dot3_disable_required",
            "policy_query_denied",
            "short_alias_acceptance",
            "uppercase_catalog",
        },
        "Windows identity policy",
        reason="canonical_policy_drift",
    )
    query_denied = _require_exact_fields(
        windows_policy.get("policy_query_denied"),
        {"record", "required_fallback"},
        "policy_query_denied policy",
        reason="canonical_policy_drift",
    )
    authorization_basis = _require_string_array(
        windows_policy.get("authorization_basis"),
        "Windows authorization basis",
        reason="canonical_policy_drift",
    )
    if (
        windows_policy.get("alias_authority")
        != "original_request_class_and_approved_path_id_only"
        or windows_policy.get("alias_mapping_drift") != "requalification_required"
        or authorization_basis != EXPECTED_WINDOWS_AUTHORIZATION_BASIS
        or windows_policy.get("global_8dot3_disable_required") is not False
        or not _json_values_equal(query_denied, {
            "record": "policy_query_denied",
            "required_fallback": "non_elevated_alias_and_handle_identity_probe",
        })
        or windows_policy.get("short_alias_acceptance")
        != "same_managed_root_same_expected_file_id_128_no_policy_bypass"
        or not _json_values_equal(
            windows_policy.get("uppercase_catalog"), EXPECTED_UPPERCASE_CATALOG
        )
    ):
        raise ValidationFailure("canonical_policy_drift", "Windows identity policy mismatch")

    named_object_policy = _require_exact_fields(
        payload["named_object_identity"],
        {"inputs", "name_encoding", "templates", "user_supplied_name"},
        "named object identity policy",
        reason="canonical_policy_drift",
    )
    named_object_inputs = _require_string_array(
        named_object_policy.get("inputs"),
        "named object identity inputs",
        reason="canonical_policy_drift",
    )
    named_object_templates = _require_string_array(
        named_object_policy.get("templates"),
        "named object templates",
        reason="canonical_policy_drift",
    )
    if (
        named_object_inputs
        != [
            "canonical_sid_hash",
            "repo_identity_hash_when_scoped",
            "attempt_uuid_when_scoped",
            "run_uuid_when_scoped",
        ]
        or named_object_policy.get("name_encoding") != "ascii"
        or named_object_templates != EXPECTED_NAMED_OBJECT_TEMPLATES
        or named_object_policy.get("user_supplied_name") != "reject"
    ):
        raise ValidationFailure("canonical_policy_drift", "named object policy mismatch")
    sid_policy = _require_exact_fields(
        payload["sid_identity"],
        {"canonical_source", "sid_hash", "string_rewrite"},
        "SID identity policy",
        reason="canonical_policy_drift",
    )
    if not _json_values_equal(sid_policy, {
        "canonical_source": "ConvertSidToStringSidW",
        "sid_hash": "lowercase_sha256_of_full_ascii_sid",
        "string_rewrite": "none",
    }):
        raise ValidationFailure("canonical_policy_drift", "SID identity policy mismatch")
    return payload


def _verify_canonical_schema(schema: dict[str, Any], bounds: dict[str, int]) -> None:
    if not _json_values_equal(bounds, EXPECTED_CANONICAL_BOUNDS):
        raise ValidationFailure("canonical_schema_drift", "canonical bounds mismatch")
    value_ref = {"$ref": "#/$defs/canonical_value"}
    expected = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": (
            "https://local-ai-runtime.invalid/schemas/"
            "CanonicalEnvelope.v1.schema.json"
        ),
        "title": "CanonicalEnvelope.v1",
        "type": "object",
        "additionalProperties": False,
        "required": ["domain", "payload", "schema_version"],
        "properties": {
            "domain": {
                "type": "string",
                "minLength": 1,
                "maxLength": bounds["identifier_utf8_bytes"],
                "pattern": r"^local-ai-runtime/[A-Za-z0-9][A-Za-z0-9._-]{0,95}/v1$",
            },
            "payload": value_ref,
            "schema_version": {"const": 1},
        },
        "$defs": {
            "canonical_value": {
                "x-local-ai-runtime-maxDepth": bounds["depth"],
                "oneOf": [
                    {"type": "boolean"},
                    {
                        "type": "integer",
                        "minimum": bounds["integer_min"],
                        "maximum": bounds["integer_max"],
                    },
                    {
                        "type": "string",
                        "maxLength": bounds["string_utf8_bytes"],
                        "x-local-ai-runtime-maxUtf8Bytes": bounds[
                            "string_utf8_bytes"
                        ],
                    },
                    {
                        "type": "array",
                        "maxItems": bounds["array_items"],
                        "items": value_ref,
                    },
                    {
                        "type": "object",
                        "maxProperties": bounds["object_members"],
                        "additionalProperties": value_ref,
                    },
                ],
            }
        },
    }
    if not _json_values_equal(schema, expected):
        raise ValidationFailure(
            "canonical_schema_drift", "CanonicalEnvelope schema mismatch"
        )


def _validate_contract_string(value: Any, bounds: dict[str, int], label: str) -> bytes:
    if not isinstance(value, str):
        raise ValidationFailure("invalid_utf8_string", f"{label} must be a string")
    if value != unicodedata.normalize("NFC", value):
        raise ValidationFailure("non_nfc_string", f"{label} is not NFC")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValidationFailure("invalid_utf8_string", f"{label} is not valid UTF-8") from exc
    if len(encoded) > bounds["string_utf8_bytes"]:
        raise ValidationFailure("string_limit", f"{label} exceeds UTF-8 bound")
    for character in value:
        category = unicodedata.category(character)
        if category not in ALLOWED_UNICODE_CATEGORIES or _is_noncharacter(ord(character)):
            raise ValidationFailure(
                "disallowed_unicode", f"{label} contains disallowed Unicode"
            )
    return encoded


def _pointer_child(path: str, key: str) -> str:
    escaped = key.replace("~", "~0").replace("/", "~1")
    return f"{path}/{escaped}"


def _canonicalize_value(
    value: Any,
    bounds: dict[str, int],
    set_specs: dict[str, str],
    used_set_paths: set[str],
    *,
    path: str,
    depth: int,
) -> Any:
    if depth > bounds["depth"]:
        raise ValidationFailure("depth_limit", f"canonical depth exceeded at {path}")
    if value is None:
        raise ValidationFailure("null_not_allowed", f"null is not allowed at {path}")
    if isinstance(value, bool):
        return value
    if type(value) is int:
        if not bounds["integer_min"] <= value <= bounds["integer_max"]:
            raise ValidationFailure("integer_limit", f"integer out of bounds at {path}")
        return value
    if isinstance(value, float):
        raise ValidationFailure("float_not_allowed", f"float is not allowed at {path}")
    if isinstance(value, str):
        _validate_contract_string(value, bounds, path)
        return value
    if isinstance(value, list):
        if len(value) > bounds["array_items"]:
            raise ValidationFailure("array_limit", f"array exceeds bound at {path}")
        ordered = value
        if path in set_specs:
            used_set_paths.add(path)
            if len(value) > bounds["set_items"]:
                raise ValidationFailure("set_limit", f"set exceeds bound at {path}")
            sort_key = set_specs[path]
            keyed: list[tuple[bytes, Any]] = []
            seen: set[bytes] = set()
            for item in value:
                if not isinstance(item, dict) or sort_key not in item:
                    raise ValidationFailure(
                        "set_sort_key_missing", f"set item lacks {sort_key} at {path}"
                    )
                key_value = item[sort_key]
                if isinstance(key_value, bool) or not isinstance(key_value, (int, str)):
                    raise ValidationFailure(
                        "set_sort_key_type", f"set sort key is not scalar at {path}"
                    )
                canonical_key = json.dumps(
                    _canonicalize_value(
                        key_value,
                        bounds,
                        {},
                        set(),
                        path=f"{path}/@sort-key",
                        depth=depth + 1,
                    ),
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
                if canonical_key in seen:
                    raise ValidationFailure(
                        "duplicate_set_key", f"duplicate set key at {path}"
                    )
                seen.add(canonical_key)
                keyed.append((canonical_key, item))
            ordered = [item for _, item in sorted(keyed, key=lambda entry: entry[0])]
        return [
            _canonicalize_value(
                item,
                bounds,
                set_specs,
                used_set_paths,
                path=_pointer_child(path, str(index)),
                depth=depth + 1,
            )
            for index, item in enumerate(ordered)
        ]
    if isinstance(value, dict):
        if len(value) > bounds["object_members"]:
            raise ValidationFailure("object_limit", f"object exceeds bound at {path}")
        result: dict[str, Any] = {}
        encoded_keys = [
            (_validate_contract_string(key, bounds, f"{path}/@key"), key)
            for key in value
        ]
        for _, key in sorted(encoded_keys, key=lambda item: item[0]):
            result[key] = _canonicalize_value(
                value[key],
                bounds,
                set_specs,
                used_set_paths,
                path=_pointer_child(path, key),
                depth=depth + 1,
            )
        return result
    raise ValidationFailure("unsupported_json_type", f"unsupported value at {path}")


def _canonicalize_fixture_case(case: dict[str, Any], bounds: dict[str, int]) -> str:
    case = _require_object(case, "canonical fixture case", reason="fixture_schema")
    raw_json = case.get("raw_json")
    if not isinstance(raw_json, str):
        raise ValidationFailure("fixture_schema", "raw_json must be a string")
    try:
        raw = raw_json.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValidationFailure(
            "invalid_utf8_string", "raw_json is not valid UTF-8"
        ) from exc
    if len(raw) > bounds["json_input_bytes"]:
        raise ValidationFailure("json_input_limit", "canonical input exceeds byte bound")
    try:
        value = json.loads(raw_json, object_pairs_hook=_reject_duplicates)
    except (json.JSONDecodeError, RecursionError) as exc:
        detail = getattr(exc, "msg", "maximum JSON nesting exceeded")
        raise ValidationFailure("invalid_json", detail) from exc
    if not isinstance(value, dict) or set(value) != {"domain", "payload", "schema_version"}:
        raise ValidationFailure("canonical_envelope", "canonical envelope fields mismatch")
    if (
        not isinstance(value["domain"], str)
        or CANONICAL_DOMAIN_PATTERN.fullmatch(value["domain"]) is None
        or len(value["domain"].encode("utf-8")) > bounds["identifier_utf8_bytes"]
        or type(value["schema_version"]) is not int
        or value["schema_version"] != 1
    ):
        raise ValidationFailure("canonical_envelope", "canonical envelope identity mismatch")
    specs: dict[str, str] = {}
    set_semantics = _require_array(
        case.get("set_semantics", []), "set_semantics", reason="fixture_schema"
    )
    for spec in set_semantics:
        if not isinstance(spec, dict) or set(spec) != {"json_pointer", "sort_key"}:
            raise ValidationFailure("fixture_schema", "set semantics fixture mismatch")
        pointer, sort_key = spec["json_pointer"], spec["sort_key"]
        if not isinstance(pointer, str) or not isinstance(sort_key, str) or pointer in specs:
            raise ValidationFailure("fixture_schema", "set semantics declaration mismatch")
        specs[pointer] = sort_key
    used: set[str] = set()
    canonical_value = _canonicalize_value(
        value, bounds, specs, used, path="", depth=0
    )
    if used != set(specs):
        raise ValidationFailure(
            "set_semantics_pointer_missing", "declared set pointer did not resolve"
        )
    return (
        json.dumps(
            canonical_value,
            ensure_ascii=False,
            sort_keys=False,
            separators=(",", ":"),
        )
        + "\n"
    )


def _validate_git_path(value: str, policy: dict[str, Any]) -> tuple[str, str]:
    policy = _require_object(policy, "canonical policy", reason="canonical_policy_drift")
    if policy.get("bounds") != EXPECTED_CANONICAL_BOUNDS:
        raise ValidationFailure("canonical_policy_drift", "canonical bounds mismatch")
    bounds = policy["bounds"]
    git_policy = _require_object(
        policy.get("git_path"), "Git path policy", reason="canonical_policy_drift"
    )
    device_catalog = _require_string_array(
        git_policy.get("dos_device_catalog"),
        "DOS device catalog",
        reason="canonical_policy_drift",
    )
    if not isinstance(value, str):
        raise ValidationFailure("invalid_utf8", "Git path must decode to a string")
    if value != unicodedata.normalize("NFC", value):
        raise ValidationFailure("non_nfc_path", "Git path is not NFC")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValidationFailure("invalid_utf8", "Git path is not valid UTF-8") from exc
    if len(encoded) > bounds["git_path_utf8_bytes"]:
        raise ValidationFailure("git_path_limit", "Git path exceeds byte bound")
    if value.startswith("/"):
        raise ValidationFailure("absolute_path", "Git path is absolute")
    if re.match(r"^[A-Za-z]:", value):
        raise ValidationFailure("drive_absolute_path", "Git path has a drive prefix")
    if "\\" in value:
        raise ValidationFailure("backslash_path", "Git path contains backslash")
    if ":" in value:
        raise ValidationFailure("alternate_data_stream", "Git path contains colon")
    components = value.split("/")
    if len(components) > bounds["git_path_components"]:
        raise ValidationFailure("git_path_component_limit", "too many path components")
    if "" in components:
        raise ValidationFailure("empty_path_component", "Git path has empty component")
    if "." in components:
        raise ValidationFailure("dot_path_component", "Git path has dot component")
    if ".." in components:
        raise ValidationFailure("dotdot_path_component", "Git path has dotdot component")
    devices = set(device_catalog)
    for component in components:
        if component.endswith((".", " ")):
            raise ValidationFailure(
                "trailing_dot_or_space", "Git path has trailing dot or space"
            )
        for character in component:
            category = unicodedata.category(character)
            if category not in ALLOWED_UNICODE_CATEGORIES or _is_noncharacter(
                ord(character)
            ):
                raise ValidationFailure(
                    "disallowed_path_unicode", "Git path contains disallowed Unicode"
                )
        if component.split(".", 1)[0].upper() in devices:
            raise ValidationFailure("dos_device_path", "Git path uses DOS device name")
    if unicodedata.unidata_version != EXPECTED_UPPERCASE_CATALOG["unicode_version"]:
        raise ValidationFailure(
            "uppercase_catalog_unavailable", "Unicode uppercase catalog version mismatch"
        )
    return value, value.upper()


def _validate_git_path_set(values: list[str], policy: dict[str, Any]) -> None:
    values = _require_array(values, "Git path set", reason="fixture_schema")
    seen: set[str] = set()
    for value in values:
        _, collision_key = _validate_git_path(value, policy)
        if collision_key in seen:
            raise ValidationFailure(
                "windows_case_collision", "Git paths share a Windows collision key"
            )
        seen.add(collision_key)


def _evaluate_alias_probe(case: dict[str, Any]) -> str:
    required = {
        "case_id",
        "policy_observation",
        "probe_attempted",
        "handle_open_mode",
        "long_handle_identity",
        "alias_handle_identity",
        "original_approved_path_id",
        "resolved_approved_path_id",
        "bypass_observed",
        "link_policy_passed",
        "mapping_generation_unchanged",
        "expected_result",
    }
    case = _require_exact_fields(
        case, required, "alias probe case", reason="fixture_schema"
    )
    if not isinstance(case["policy_observation"], str) or case[
        "policy_observation"
    ] not in {
        "disabled",
        "enabled",
        "policy_query_denied",
    }:
        raise ValidationFailure("fixture_schema", "unknown 8.3 policy observation")
    for field in {
        "probe_attempted",
        "bypass_observed",
        "link_policy_passed",
        "mapping_generation_unchanged",
    }:
        if not isinstance(case[field], bool):
            raise ValidationFailure("fixture_schema", f"{field} must be boolean")
    if case["handle_open_mode"] != "no_follow":
        raise ValidationFailure("fixture_schema", "alias probe must use no-follow handles")
    identity_fields = {"volume_id", "root_file_id_128", "file_id_128"}
    long_identity = _require_exact_fields(
        case["long_handle_identity"], identity_fields, "long handle identity"
    )
    alias_identity = case["alias_handle_identity"]
    if alias_identity is not None:
        alias_identity = _require_exact_fields(
            alias_identity, identity_fields, "alias handle identity"
        )
    for identity in (long_identity, alias_identity):
        if identity is None:
            continue
        if not isinstance(identity["volume_id"], str) or not identity["volume_id"]:
            raise ValidationFailure("fixture_schema", "volume identity must be non-empty")
        for field in ("root_file_id_128", "file_id_128"):
            value = identity[field]
            if (
                not isinstance(value, str)
                or len(value) != 32
                or any(character not in "0123456789abcdef" for character in value)
            ):
                raise ValidationFailure("fixture_schema", f"{field} must be lowercase hex")
    for field in ("original_approved_path_id", "resolved_approved_path_id"):
        if not isinstance(case[field], str) or not case[field]:
            raise ValidationFailure("fixture_schema", f"{field} must be non-empty")
    if not case["mapping_generation_unchanged"]:
        return "requalification_required"
    if not case["link_policy_passed"]:
        return "identity_policy_violation"
    if case["policy_observation"] == "policy_query_denied" and not case[
        "probe_attempted"
    ]:
        return "policy_query_denied_without_probe"
    if alias_identity is not None and alias_identity != long_identity:
        return "alias_identity_collision"
    if (
        case["bypass_observed"]
        or case["resolved_approved_path_id"] != case["original_approved_path_id"]
    ):
        return "alias_bypass"
    if case["policy_observation"] == "policy_query_denied":
        return "qualified_by_probe"
    return "qualified"


def _verify_boundary_fixtures(fixture: dict[str, Any], bounds: dict[str, int]) -> int:
    fixture = _require_object(fixture, "canonical fixture", reason="fixture_schema")
    dimensions = _require_array(
        fixture.get("boundary_dimensions"),
        "boundary_dimensions",
        reason="fixture_schema",
    )
    by_id: dict[str, dict[str, Any]] = {}
    for raw_entry in dimensions:
        entry = _require_exact_fields(
            raw_entry,
            {"bound_id", "kind", "limit"},
            "boundary dimension",
            reason="fixture_schema",
        )
        if not isinstance(entry["bound_id"], str) or not isinstance(entry["kind"], str):
            raise ValidationFailure(
                "fixture_schema", "boundary identifiers must be strings"
            )
        if entry["bound_id"] in by_id:
            raise ValidationFailure("fixture_schema", "duplicate boundary identifier")
        by_id[entry["bound_id"]] = entry
    if set(by_id) != set(bounds) or len(by_id) != len(dimensions):
        raise ValidationFailure("boundary_fixture_gap", "bounded field coverage mismatch")
    expectations = fixture.get("boundary_expectations")
    expected_matrix = {
        "maximum": {
            "limit_minus_one": "accept",
            "limit": "accept",
            "limit_plus_one": "reject",
        },
        "minimum": {
            "limit_minus_one": "reject",
            "limit": "accept",
            "limit_plus_one": "accept",
        },
    }
    if expectations != expected_matrix:
        raise ValidationFailure("boundary_fixture_gap", "boundary matrix mismatch")
    for bound_id, entry in by_id.items():
        if entry["limit"] != bounds[bound_id]:
            raise ValidationFailure("boundary_fixture_gap", f"{bound_id} fixture mismatch")
        if entry["kind"] not in expected_matrix:
            raise ValidationFailure("boundary_fixture_gap", f"{bound_id} kind mismatch")
    return len(dimensions)


def _verify_sid_named_objects(
    fixture: dict[str, Any], policy: dict[str, Any]
) -> int:
    fixture = _require_object(fixture, "canonical fixture", reason="fixture_schema")
    policy = _require_object(policy, "canonical policy", reason="canonical_policy_drift")
    if policy.get("bounds") != EXPECTED_CANONICAL_BOUNDS:
        raise ValidationFailure("canonical_policy_drift", "canonical bounds mismatch")
    value = _require_exact_fields(
        fixture.get("sid_named_object_fixture"),
        {
            "canonical_sid",
            "expected_sid_hash",
            "repo_identity_hash",
            "attempt_uuid",
            "run_uuid",
        },
        "SID/named-object fixture",
    )
    sid = value["canonical_sid"]
    if (
        not isinstance(sid, str)
        or SID_PATTERN.fullmatch(sid) is None
        or len(sid.encode("ascii")) > policy["bounds"]["sid_ascii_bytes"]
        or any(
            len(component) > 1 and component.startswith("0")
            for component in sid.split("-")[1:]
        )
    ):
        raise ValidationFailure("sid_identity", "canonical SID fixture is invalid")
    for field in (
        "expected_sid_hash",
        "repo_identity_hash",
        "attempt_uuid",
        "run_uuid",
    ):
        if not isinstance(value[field], str):
            raise ValidationFailure("named_object_identity", f"{field} must be a string")
    if not _is_sha256(value["expected_sid_hash"]) or not _is_sha256(
        value["repo_identity_hash"]
    ):
        raise ValidationFailure("named_object_identity", "fixture hashes are invalid")
    if UUID_V4_PATTERN.fullmatch(value["attempt_uuid"]) is None or UUID_V4_PATTERN.fullmatch(
        value["run_uuid"]
    ) is None:
        raise ValidationFailure("named_object_identity", "fixture UUIDs are not canonical v4")
    sid_hash = hashlib.sha256(sid.encode("ascii")).hexdigest()
    if sid_hash != value["expected_sid_hash"]:
        raise ValidationFailure("sid_identity", "SID hash fixture mismatch")
    named_object_policy = _require_object(
        policy.get("named_object_identity"),
        "named object identity policy",
        reason="canonical_policy_drift",
    )
    templates = _require_string_array(
        named_object_policy.get("templates"),
        "named object templates",
        reason="canonical_policy_drift",
    )
    for template in templates:
        rendered = (
            template.replace("<SIDHash>", sid_hash)
            .replace("<RepoIdentityHash>", value["repo_identity_hash"])
            .replace("<attempt_uuid>", value["attempt_uuid"])
            .replace("<run_uuid>", value["run_uuid"])
        )
        try:
            encoded = rendered.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValidationFailure("named_object_identity", "name is not ASCII") from exc
        if len(encoded) > policy["bounds"]["named_object_ascii_bytes"] or "<" in rendered:
            raise ValidationFailure("named_object_identity", "name fixture is not closed")
    return len(templates)


def verify_canonicalization_component(repo_root: Path) -> dict[str, Any]:
    policy, policy_raw = _load_json_object(repo_root / CANONICAL_POLICY_RELATIVE)
    schema, _ = _load_json_object(repo_root / CANONICAL_SCHEMA_RELATIVE)
    fixture, _ = _load_json_object(repo_root / CANONICAL_FIXTURE_RELATIVE)
    policy_payload = _verify_canonical_policy(policy, policy_raw)
    bounds = policy_payload["bounds"]
    _verify_canonical_schema(schema, bounds)
    fixture = _require_exact_fields(
        fixture,
        {
            "alias_probe_cases",
            "boundary_dimensions",
            "boundary_expectations",
            "canonical_negative_cases",
            "canonical_positive_cases",
            "fixture_id",
            "git_negative_cases",
            "git_positive_cases",
            "policy_path",
            "schema_path",
            "schema_version",
            "sid_named_object_fixture",
        },
        "canonical fixture",
        reason="fixture_schema",
    )
    if (
        fixture["fixture_id"] != "CanonicalizationPolicy.v1.contract-fixtures"
        or type(fixture["schema_version"]) is not int
        or fixture["schema_version"] != 1
    ):
        raise ValidationFailure("fixture_schema", "canonical fixture identity mismatch")
    if fixture.get("policy_path") != str(CANONICAL_POLICY_RELATIVE).replace("\\", "/"):
        raise ValidationFailure("fixture_binding_mismatch", "fixture policy path mismatch")
    if fixture.get("schema_path") != str(CANONICAL_SCHEMA_RELATIVE).replace("\\", "/"):
        raise ValidationFailure("fixture_binding_mismatch", "fixture schema path mismatch")

    positive = _require_array(
        fixture["canonical_positive_cases"],
        "canonical_positive_cases",
        reason="fixture_schema",
    )
    for raw_case in positive:
        case = _require_object(raw_case, "canonical positive case", reason="fixture_schema")
        actual = _canonicalize_fixture_case(case, bounds)
        if actual != case.get("expected_canonical_json"):
            raise ValidationFailure(
                "canonical_fixture_mismatch", f"{case.get('case_id')} output mismatch"
            )
    canonical_negative = _require_array(
        fixture["canonical_negative_cases"],
        "canonical_negative_cases",
        reason="fixture_schema",
    )
    for raw_case in canonical_negative:
        case = _require_object(raw_case, "canonical negative case", reason="fixture_schema")
        try:
            _canonicalize_fixture_case(case, bounds)
        except ValidationFailure as exc:
            if exc.reason != case.get("expected_reason"):
                raise ValidationFailure(
                    "fixture_reason_mismatch",
                    f"{case.get('case_id')}: expected {case.get('expected_reason')}, got {exc.reason}",
                ) from exc
        else:
            raise ValidationFailure("negative_fixture_accepted", str(case.get("case_id")))

    git_positive = _require_array(
        fixture["git_positive_cases"], "git_positive_cases", reason="fixture_schema"
    )
    for raw_case in git_positive:
        case = _require_exact_fields(
            raw_case,
            {
                "case_id",
                "expected_git_path",
                "expected_windows_collision_key",
                "git_path",
            },
            "Git positive case",
            reason="fixture_schema",
        )
        git_path, collision_key = _validate_git_path(case["git_path"], policy_payload)
        if (
            git_path != case.get("expected_git_path")
            or collision_key != case.get("expected_windows_collision_key")
        ):
            raise ValidationFailure("git_fixture_mismatch", str(case.get("case_id")))
    git_negative = _require_array(
        fixture["git_negative_cases"], "git_negative_cases", reason="fixture_schema"
    )
    for raw_case in git_negative:
        case = _require_object(raw_case, "Git negative case", reason="fixture_schema")
        input_fields = {"git_path", "git_paths", "raw_utf8_hex"}.intersection(case)
        if (
            len(input_fields) != 1
            or set(case) != {"case_id", "expected_reason"}.union(input_fields)
            or not isinstance(case["case_id"], str)
            or not isinstance(case["expected_reason"], str)
        ):
            raise ValidationFailure(
                "fixture_schema", "Git negative case shape mismatch"
            )
        if "raw_utf8_hex" in case and not isinstance(case["raw_utf8_hex"], str):
            raise ValidationFailure("fixture_schema", "raw_utf8_hex must be a string")
        if "git_paths" in case:
            _require_array(case["git_paths"], "git_paths", reason="fixture_schema")
        try:
            if "raw_utf8_hex" in case:
                try:
                    value = bytes.fromhex(case["raw_utf8_hex"]).decode("utf-8")
                except (UnicodeDecodeError, ValueError) as exc:
                    raise ValidationFailure("invalid_utf8", "Git path bytes are invalid") from exc
                _validate_git_path(value, policy_payload)
            elif "git_paths" in case:
                _validate_git_path_set(case["git_paths"], policy_payload)
            else:
                _validate_git_path(case["git_path"], policy_payload)
        except ValidationFailure as exc:
            if exc.reason != case.get("expected_reason"):
                raise ValidationFailure(
                    "fixture_reason_mismatch",
                    f"{case.get('case_id')}: expected {case.get('expected_reason')}, got {exc.reason}",
                ) from exc
        else:
            raise ValidationFailure("negative_fixture_accepted", str(case.get("case_id")))

    alias_cases = _require_array(
        fixture["alias_probe_cases"], "alias_probe_cases", reason="fixture_schema"
    )
    for raw_case in alias_cases:
        case = _require_object(raw_case, "alias probe case", reason="fixture_schema")
        actual = _evaluate_alias_probe(case)
        if actual != case.get("expected_result"):
            raise ValidationFailure("alias_fixture_mismatch", str(case.get("case_id")))
    boundary_count = _verify_boundary_fixtures(fixture, bounds)
    named_object_count = _verify_sid_named_objects(fixture, policy_payload)
    return {
        "status": "pass",
        "component": "canonicalization",
        "artifact_version": "CanonicalizationPolicy.v1",
        "artifact_byte_count": len(policy_raw),
        "artifact_sha256": hashlib.sha256(policy_raw).hexdigest(),
        "fixture_counts": {
            "alias_probe": len(alias_cases),
            "boundary_dimension": boundary_count,
            "canonical_negative": len(canonical_negative),
            "canonical_positive": len(positive),
            "git_negative": len(git_negative),
            "git_positive": len(git_positive),
            "named_object_template": named_object_count,
        },
    }


def _verify_product_policy(policy: dict[str, Any], raw: bytes) -> dict[str, Any]:
    identity = EXPECTED_PRODUCT_IDENTITIES["policy"]
    try:
        canonical = (
            json.dumps(
                policy,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
    except (RecursionError, TypeError, UnicodeEncodeError) as exc:
        raise ValidationFailure(
            "product_policy_bytes", "ProductContract is not canonical UTF-8 JSON"
        ) from exc
    if (
        raw != canonical
        or len(raw) != identity["byte_count"]
        or hashlib.sha256(raw).hexdigest() != identity["sha256"]
    ):
        raise ValidationFailure(
            "product_policy_identity", "ProductContract bytes or identity mismatch"
        )
    envelope = _require_exact_fields(
        policy, {"domain", "payload", "schema_version"}, "product policy"
    )
    if (
        envelope["domain"] != "local-ai-runtime/ProductContract/v1"
        or type(envelope["schema_version"]) is not int
        or envelope["schema_version"] != 1
    ):
        raise ValidationFailure("product_policy_drift", "product envelope mismatch")
    payload = _require_exact_fields(
        envelope["payload"],
        {
            "artifact_id",
            "artifact_version",
            "baseline_id",
            "batch_submission",
            "product",
            "resubmission_policy",
            "submission_family",
            "task_template",
            "work_routing_policy",
        },
        "product policy payload",
        reason="product_policy_drift",
    )
    if (
        payload["artifact_id"] != "P0A-PRODUCT"
        or payload["artifact_version"] != "ProductContract.v1"
        or payload["baseline_id"] != BASELINE_SPECIFICATION_ID
    ):
        raise ValidationFailure("product_policy_drift", "product artifact binding mismatch")
    routing = _require_object(
        payload["work_routing_policy"],
        "work routing policy",
        reason="product_policy_drift",
    )
    profile_boundary = _require_object(
        routing.get("execution_profile_boundary"),
        "execution profile boundary",
        reason="product_policy_drift",
    )
    if (
        routing.get("output_work_classes")
        != ["native_direct", "native_spec", "native_program", "batch"]
        or routing.get("runtime_model_router_service") != "absent"
        or profile_boundary.get("owner")
        != "qualified_ExecutionProfile_and_profile_generation"
        or profile_boundary.get("work_routing_output") != "work_class_only"
    ):
        raise ValidationFailure("product_policy_drift", "work routing boundary mismatch")
    submission = _require_object(
        payload["batch_submission"],
        "batch submission policy",
        reason="product_policy_drift",
    )
    resubmission = _require_object(
        payload["resubmission_policy"],
        "resubmission policy",
        reason="product_policy_drift",
    )
    if (
        submission.get("exact_fields")
        != ["repo_id", "template_id", "parameters", "expected_base_commit"]
        or resubmission.get("no_resubmission_permit") is not True
        or resubmission.get("command")
        != "batch resolve <source_task_id> --code create_resubmission_v1"
    ):
        raise ValidationFailure("product_policy_drift", "submission policy mismatch")
    return payload


def _verify_product_schema_identity(raw: bytes, identity_key: str, label: str) -> None:
    identity = EXPECTED_PRODUCT_IDENTITIES[identity_key]
    if (
        len(raw) != identity["byte_count"]
        or hashlib.sha256(raw).hexdigest() != identity["sha256"]
    ):
        raise ValidationFailure("product_schema_drift", f"{label} identity mismatch")


def _verify_product_fixture_identity(raw: bytes) -> None:
    identity = EXPECTED_PRODUCT_IDENTITIES["fixture"]
    if (
        len(raw) != identity["byte_count"]
        or hashlib.sha256(raw).hexdigest() != identity["sha256"]
    ):
        raise ValidationFailure("product_fixture_drift", "product fixture identity mismatch")


def _validate_value_spec(spec: Any, *, allow_array: bool) -> dict[str, Any]:
    spec = _require_object(spec, "template value_spec", reason="template_schema")
    kind = spec.get("kind")
    if kind == "boolean":
        _require_exact_fields(spec, {"kind"}, "boolean value_spec", reason="template_schema")
    elif kind == "integer":
        _require_exact_fields(
            spec, {"kind", "minimum", "maximum"}, "integer value_spec", reason="template_schema"
        )
        if (
            type(spec["minimum"]) is not int
            or type(spec["maximum"]) is not int
            or spec["minimum"] > spec["maximum"]
        ):
            raise ValidationFailure("template_schema", "integer bounds are invalid")
    elif kind == "enum":
        _require_exact_fields(spec, {"kind", "values"}, "enum value_spec", reason="template_schema")
        values = _require_string_array(spec["values"], "enum values", reason="template_schema")
        if (
            not values
            or len(values) > 64
            or len(values) != len(set(values))
            or any(PUBLIC_VALUE_PATTERN.fullmatch(value) is None for value in values)
        ):
            raise ValidationFailure("template_schema", "enum values are invalid")
    elif kind == "public_id":
        _require_exact_fields(
            spec, {"kind", "max_utf8_bytes"}, "public ID value_spec", reason="template_schema"
        )
        maximum = spec["max_utf8_bytes"]
        if type(maximum) is not int or not 1 <= maximum <= 256:
            raise ValidationFailure("template_schema", "public ID bound is invalid")
    elif kind == "approved_relative_path_id":
        _require_exact_fields(
            spec,
            {"kind", "allowed_path_ids"},
            "path ID value_spec",
            reason="template_schema",
        )
        values = _require_string_array(
            spec["allowed_path_ids"], "allowed path IDs", reason="template_schema"
        )
        if (
            not values
            or len(values) > 64
            or len(values) != len(set(values))
            or any(PUBLIC_ID_PATTERN.fullmatch(value) is None for value in values)
        ):
            raise ValidationFailure("template_schema", "allowed path IDs are invalid")
    elif kind == "array" and allow_array:
        _require_exact_fields(
            spec,
            {"kind", "minimum_items", "maximum_items", "items"},
            "array value_spec",
            reason="template_schema",
        )
        minimum, maximum = spec["minimum_items"], spec["maximum_items"]
        if (
            type(minimum) is not int
            or type(maximum) is not int
            or not 0 <= minimum <= maximum <= 256
            or maximum < 1
        ):
            raise ValidationFailure("template_schema", "array bounds are invalid")
        _validate_value_spec(spec["items"], allow_array=False)
    else:
        raise ValidationFailure("template_parameter_kind", f"unsupported parameter kind: {kind!r}")
    return spec


def _validate_task_template(template: Any) -> None:
    template = _require_exact_fields(
        template,
        {
            "host_scope",
            "parameter_definitions",
            "prompt_template_sha256",
            "risk_class",
            "schema_version",
            "template_id",
            "template_version",
            "work_class",
        },
        "TaskTemplate",
        reason="template_schema",
    )
    if (
        type(template["schema_version"]) is not int
        or template["schema_version"] != 1
        or not isinstance(template["template_id"], str)
        or PUBLIC_ID_PATTERN.fullmatch(template["template_id"]) is None
        or not isinstance(template["template_version"], str)
        or PUBLIC_ID_PATTERN.fullmatch(template["template_version"]) is None
        or template["work_class"] != "batch"
        or template["risk_class"] != "low"
        or template["host_scope"] != "host_local"
        or not _is_sha256(template["prompt_template_sha256"])
    ):
        raise ValidationFailure("template_schema", "TaskTemplate identity or boundary mismatch")
    definitions = _require_array(
        template["parameter_definitions"], "parameter_definitions", reason="template_schema"
    )
    if len(definitions) > 64:
        raise ValidationFailure("template_schema", "too many parameter definitions")
    seen: set[str] = set()
    for raw_definition in definitions:
        definition = _require_exact_fields(
            raw_definition,
            {"parameter_id", "required", "value_spec"},
            "parameter definition",
            reason="template_schema",
        )
        parameter_id = definition["parameter_id"]
        if not isinstance(parameter_id, str) or PUBLIC_ID_PATTERN.fullmatch(parameter_id) is None:
            raise ValidationFailure("template_schema", "parameter ID is invalid")
        if parameter_id in FORBIDDEN_PARAMETER_IDS:
            raise ValidationFailure(
                "template_parameter_influence", "parameter ID controls an execution surface"
            )
        if parameter_id in seen:
            raise ValidationFailure("template_parameter_duplicate", "duplicate parameter ID")
        seen.add(parameter_id)
        if not isinstance(definition["required"], bool):
            raise ValidationFailure("template_schema", "required must be boolean")
        _validate_value_spec(definition["value_spec"], allow_array=True)


def _validate_generic_parameter_value(value: Any, *, allow_array: bool = True) -> None:
    if isinstance(value, bool):
        return
    if type(value) is int:
        if not EXPECTED_CANONICAL_BOUNDS["integer_min"] <= value <= EXPECTED_CANONICAL_BOUNDS[
            "integer_max"
        ]:
            raise ValidationFailure("submission_parameter_value", "integer is out of bounds")
        return
    if isinstance(value, str) and PUBLIC_VALUE_PATTERN.fullmatch(value) is not None:
        return
    if isinstance(value, list) and allow_array and len(value) <= 256:
        for item in value:
            _validate_generic_parameter_value(item, allow_array=False)
        return
    raise ValidationFailure("submission_parameter_value", "parameter value is not closed")


def _validate_batch_submission(submission: Any) -> str:
    submission = _require_exact_fields(
        submission,
        {"expected_base_commit", "parameters", "repo_id", "template_id"},
        "BatchSubmission",
        reason="submission_schema",
    )
    for field in ("repo_id", "template_id"):
        value = submission[field]
        if not isinstance(value, str) or PUBLIC_ID_PATTERN.fullmatch(value) is None:
            raise ValidationFailure("submission_public_id", f"{field} is invalid")
    base = submission["expected_base_commit"]
    if not isinstance(base, str) or SHA1_PATTERN.fullmatch(base) is None:
        raise ValidationFailure("submission_base_commit", "expected base commit is invalid")
    parameters = _require_object(
        submission["parameters"], "submission parameters", reason="submission_schema"
    )
    if len(parameters) > 64:
        raise ValidationFailure("submission_schema", "too many parameters")
    for parameter_id, value in parameters.items():
        if PUBLIC_ID_PATTERN.fullmatch(parameter_id) is None:
            raise ValidationFailure("submission_schema", "parameter ID is invalid")
        if parameter_id in FORBIDDEN_PARAMETER_IDS:
            raise ValidationFailure(
                "submission_parameter_influence", "parameter controls an execution surface"
            )
        _validate_generic_parameter_value(value)
    canonical_parameters = json.dumps(
        parameters, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    if len(canonical_parameters) > 65536:
        raise ValidationFailure("submission_schema", "canonical parameters exceed byte bound")
    envelope = {
        "domain": "local-ai-runtime/BatchSubmission/v1",
        "payload": submission,
        "schema_version": 1,
    }
    raw = (
        json.dumps(envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _value_matches_spec(value: Any, spec: dict[str, Any]) -> bool:
    kind = spec["kind"]
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "integer":
        return type(value) is int and spec["minimum"] <= value <= spec["maximum"]
    if kind == "enum":
        return isinstance(value, str) and value in spec["values"]
    if kind == "public_id":
        return (
            isinstance(value, str)
            and PUBLIC_VALUE_PATTERN.fullmatch(value) is not None
            and len(value.encode("utf-8")) <= spec["max_utf8_bytes"]
        )
    if kind == "approved_relative_path_id":
        return isinstance(value, str) and value in spec["allowed_path_ids"]
    if kind == "array":
        return (
            isinstance(value, list)
            and spec["minimum_items"] <= len(value) <= spec["maximum_items"]
            and all(_value_matches_spec(item, spec["items"]) for item in value)
        )
    return False


def _validate_submission_against_template(
    submission: dict[str, Any], template: dict[str, Any]
) -> None:
    definitions = {
        definition["parameter_id"]: definition
        for definition in template["parameter_definitions"]
    }
    parameters = submission["parameters"]
    required = {
        parameter_id
        for parameter_id, definition in definitions.items()
        if definition["required"]
    }
    if not required.issubset(parameters) or not set(parameters).issubset(definitions):
        raise ValidationFailure("submission_template_schema", "template parameter set mismatch")
    for parameter_id, value in parameters.items():
        if not _value_matches_spec(value, definitions[parameter_id]["value_spec"]):
            raise ValidationFailure(
                "submission_template_schema", f"parameter does not match template: {parameter_id}"
            )


def _evaluate_work_routing(case: dict[str, Any]) -> str:
    if (
        case["batch_template_eligible"]
        and case["decision_complete"]
        and not case["free_prompt"]
        and not case["high_risk_or_external"]
    ):
        return "batch"
    if not case["decision_complete"] or (
        case["independent_write_set_count"] >= 2
        and not case["integration_order_fixed"]
    ):
        return "native_spec"
    if case["independent_write_set_count"] >= 2:
        return "native_program"
    return "native_direct"


def _evaluate_family_replay(case: dict[str, Any]) -> str:
    if case["family_exists"]:
        if not case["read_permitted"]:
            return "replay_read_denied"
        if not case["record_integrity"]:
            return "replay_integrity_failure"
        return "return_generation_zero_root_task_id"
    if case["absent_family_guards_pass"]:
        return "begin_immediate_create_or_replay"
    return "reject_without_input_derived_retention"


def _evaluate_resubmission(case: dict[str, Any]) -> str:
    if case["relation_exists"]:
        if not case["read_permitted"]:
            return "relation_read_denied"
        if not case["record_integrity"]:
            return "relation_integrity_failure"
        return "return_existing_successor"
    if not case["source_current"]:
        return "source_not_current"
    if case["terminal_state"] not in {"failed", "cancelled"}:
        return "source_not_failed_or_cancelled"
    if not case["terminal_snapshot_unchanged"]:
        return "terminal_snapshot_changed"
    if not case["closure_complete"]:
        return "source_closure_incomplete"
    if case["historical_task_ref_success"]:
        return "historical_task_ref_success_blocks"
    if not case["current_guards_pass"]:
        return "current_guards_failed"
    return "atomic_create_generation_plus_one"


def _fixture_cases(
    fixture: dict[str, Any], field: str, expected_ids: set[str]
) -> list[dict[str, Any]]:
    values = _require_array(fixture[field], field, reason="fixture_schema")
    cases: list[dict[str, Any]] = []
    ids: list[str] = []
    for raw_case in values:
        case = _require_object(raw_case, f"{field} case", reason="fixture_schema")
        case_id = case.get("case_id")
        if not isinstance(case_id, str):
            raise ValidationFailure("fixture_schema", f"{field} case_id must be a string")
        cases.append(case)
        ids.append(case_id)
    if len(ids) != len(set(ids)) or set(ids) != expected_ids:
        raise ValidationFailure("fixture_schema", f"{field} case IDs mismatch")
    return cases


def verify_product_submission_component(repo_root: Path) -> dict[str, Any]:
    policy, policy_raw = _load_json_object(repo_root / PRODUCT_POLICY_RELATIVE)
    _, template_schema_raw = _load_json_object(repo_root / TASK_TEMPLATE_SCHEMA_RELATIVE)
    _, submission_schema_raw = _load_json_object(repo_root / BATCH_SUBMISSION_SCHEMA_RELATIVE)
    fixture, fixture_raw = _load_json_object(repo_root / PRODUCT_FIXTURE_RELATIVE)
    _verify_product_policy(policy, policy_raw)
    _verify_product_schema_identity(
        template_schema_raw, "task_template_schema", "TaskTemplate schema"
    )
    _verify_product_schema_identity(
        submission_schema_raw, "batch_submission_schema", "BatchSubmission schema"
    )
    _verify_product_fixture_identity(fixture_raw)
    fixture = _require_exact_fields(
        fixture,
        {
            "batch_submission_schema_path",
            "family_replay_cases",
            "fixture_id",
            "policy_path",
            "resubmission_cases",
            "routing_cases",
            "schema_version",
            "submission_expected_fingerprint",
            "submission_negative_mutations",
            "submission_positive",
            "task_template_negative_mutations",
            "task_template_positive",
            "task_template_schema_path",
        },
        "product fixture",
        reason="fixture_schema",
    )
    if (
        fixture["fixture_id"] != "ProductContract.v1.contract-fixtures"
        or type(fixture["schema_version"]) is not int
        or fixture["schema_version"] != 1
        or fixture["policy_path"] != str(PRODUCT_POLICY_RELATIVE).replace("\\", "/")
        or fixture["task_template_schema_path"]
        != str(TASK_TEMPLATE_SCHEMA_RELATIVE).replace("\\", "/")
        or fixture["batch_submission_schema_path"]
        != str(BATCH_SUBMISSION_SCHEMA_RELATIVE).replace("\\", "/")
    ):
        raise ValidationFailure("fixture_schema", "product fixture identity mismatch")

    template = fixture["task_template_positive"]
    _validate_task_template(template)
    template_cases = _fixture_cases(
        fixture,
        "task_template_negative_mutations",
        {"duplicate_parameter", "free_text_kind", "model_control", "reserved_parameter"},
    )
    template_mutations: dict[str, Callable[[dict[str, Any]], None]] = {
        "replace_first_kind_free_text": lambda value: value["parameter_definitions"][0][
            "value_spec"
        ].__setitem__("kind", "free_text"),
        "add_model_top_field": lambda value: value.__setitem__("model", "gpt"),
        "replace_first_parameter_id_provider": lambda value: value["parameter_definitions"][
            0
        ].__setitem__("parameter_id", "provider"),
        "duplicate_first_parameter": lambda value: value["parameter_definitions"].append(
            copy.deepcopy(value["parameter_definitions"][0])
        ),
    }
    for case in template_cases:
        candidate = copy.deepcopy(template)
        mutation = template_mutations.get(case.get("mutation"))
        if mutation is None:
            raise ValidationFailure("fixture_schema", "unknown template mutation")
        mutation(candidate)
        try:
            _validate_task_template(candidate)
        except ValidationFailure as exc:
            if exc.reason != case.get("expected_reason"):
                raise ValidationFailure("fixture_reason_mismatch", case["case_id"]) from exc
        else:
            raise ValidationFailure("negative_fixture_accepted", case["case_id"])

    submission = fixture["submission_positive"]
    fingerprint = _validate_batch_submission(submission)
    _validate_submission_against_template(submission, template)
    if fingerprint != fixture["submission_expected_fingerprint"]:
        raise ValidationFailure("submission_fingerprint", "submission fingerprint mismatch")
    submission_cases = _fixture_cases(
        fixture,
        "submission_negative_mutations",
        {"float_value", "free_prompt_value", "nested_object", "unknown_model_field", "uppercase_base"},
    )
    submission_mutations: dict[str, Callable[[dict[str, Any]], None]] = {
        "add_model_top_field": lambda value: value.__setitem__("model", "gpt"),
        "add_free_prompt_parameter": lambda value: value["parameters"].__setitem__(
            "notes", "free prompt text"
        ),
        "replace_max_files_float": lambda value: value["parameters"].__setitem__(
            "max_files", 1.5
        ),
        "replace_max_files_object": lambda value: value["parameters"].__setitem__(
            "max_files", {"value": 10}
        ),
        "uppercase_base": lambda value: value.__setitem__(
            "expected_base_commit", value["expected_base_commit"].upper()
        ),
    }
    for case in submission_cases:
        candidate = copy.deepcopy(submission)
        mutation = submission_mutations.get(case.get("mutation"))
        if mutation is None:
            raise ValidationFailure("fixture_schema", "unknown submission mutation")
        mutation(candidate)
        try:
            _validate_batch_submission(candidate)
        except ValidationFailure as exc:
            if exc.reason != case.get("expected_reason"):
                raise ValidationFailure("fixture_reason_mismatch", case["case_id"]) from exc
        else:
            raise ValidationFailure("negative_fixture_accepted", case["case_id"])

    routing_cases = _fixture_cases(
        fixture,
        "routing_cases",
        {
            "eligible_batch",
            "free_prompt_native",
            "high_risk_human_native",
            "native_program",
            "needs_spec",
            "unfixed_program_needs_spec",
        },
    )
    family_cases = _fixture_cases(
        fixture,
        "family_replay_cases",
        {
            "absent_family_rejected",
            "absent_family_transaction",
            "existing_family_before_later_guards",
            "existing_family_read_denied",
        },
    )
    resubmission_cases = _fixture_cases(
        fixture,
        "resubmission_cases",
        {
            "completed_blocks",
            "existing_relation_before_current_guards",
            "historical_ref_blocks",
            "non_current_blocks",
            "valid_resubmission",
        },
    )
    for cases, evaluator in (
        (routing_cases, _evaluate_work_routing),
        (family_cases, _evaluate_family_replay),
        (resubmission_cases, _evaluate_resubmission),
    ):
        for case in cases:
            try:
                actual = evaluator(case)
            except (KeyError, TypeError) as exc:
                raise ValidationFailure("fixture_schema", f"malformed case: {case['case_id']}") from exc
            expected = case.get("expected_work_class", case.get("expected_result"))
            if actual != expected:
                raise ValidationFailure("fixture_result_mismatch", case["case_id"])
    return {
        "status": "pass",
        "component": "product-submission",
        "artifact_version": "ProductContract.v1",
        "artifact_byte_count": len(policy_raw),
        "artifact_sha256": hashlib.sha256(policy_raw).hexdigest(),
        "submission_fingerprint": fingerprint,
        "fixture_counts": {
            "family_replay": len(family_cases),
            "resubmission": len(resubmission_cases),
            "routing": len(routing_cases),
            "submission_negative": len(submission_cases),
            "submission_positive": 1,
            "template_negative": len(template_cases),
            "template_positive": 1,
        },
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--inventory-path", type=Path)
    parser.add_argument(
        "--component",
        choices=["manifest", "canonicalization", "product-submission", "package"],
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    root = args.repo_root.resolve()
    try:
        if args.component == "manifest" and args.self_test:
            payload = verify_manifest_component(root)
            exit_code = 0
        elif args.component == "canonicalization":
            payload = verify_canonicalization_component(root)
            exit_code = 0
        elif args.component == "product-submission":
            payload = verify_product_submission_component(root)
            exit_code = 0
        else:
            payload = {
                "status": "incomplete",
                "reason": "standalone_verifier_not_frozen",
                "implemented_components": [
                    "manifest_self_test",
                    "canonicalization",
                    "product_submission",
                ],
                "requested_component": args.component or "package",
            }
            exit_code = 3
    except ValidationFailure as exc:
        payload = {"status": "fail", "reason": exc.reason, "detail": exc.detail}
        exit_code = 4
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    print(rendered)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
