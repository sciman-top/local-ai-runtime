#!/usr/bin/env python3
"""Fail-closed verifier for the Local AI Runtime normative package.

LAR-P0A-002 implements only the BaselineManifest contract self-test. Later
P0A tasks extend the component catalog; full-package verification remains
incomplete until every required component is implemented and frozen.
"""

from __future__ import annotations

import argparse
import copy
from datetime import datetime
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
QUALIFICATION_POLICY_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/normative/QualificationContractSet.v1.json"
)
SENSITIVE_INPUT_SCHEMA_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/schemas/QualificationSensitiveInputSet.v1.schema.json"
)
AUTHORIZATION_SCHEMA_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/schemas/Authorization.v1.schema.json"
)
QUALIFICATION_FIXTURE_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/fixtures/qualification/manifest.json"
)
EXECUTION_SAFETY_POLICY_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/normative/ExecutionSafetyContractSet.v1.json"
)
JOB_IDENTITY_SCHEMA_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/schemas/JobIdentity.v1.schema.json"
)
FENCED_ACTION_ADOPTION_SCHEMA_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/schemas/FencedActionAdoption.v1.schema.json"
)
EXECUTION_SAFETY_FIXTURE_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/fixtures/execution-safety/manifest.json"
)
EVIDENCE_POLICY_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/normative/EvidenceContractSet.v1.json"
)
NORMALIZED_EVENT_SCHEMA_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/schemas/NormalizedExecutionEvent.v1.schema.json"
)
EVENT_STATUS_CATALOG_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/catalogs/EventStatusMatrix.v1.json"
)
EVIDENCE_FIXTURE_RELATIVE = Path(
    "docs/specs/local-ai-runtime-0.2/fixtures/evidence/manifest.json"
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
EXPECTED_QUALIFICATION_IDENTITIES = {
    "policy": {
        "byte_count": 7336,
        "sha256": "089a60664188fdc86c0de56496c493339246c5b423ddc3271450fb01e4fd6a80",
    },
    "sensitive_input_schema": {
        "byte_count": 5043,
        "sha256": "e3a85cdec3ef2f1b2ed079366bbc12e490fa3d0015a2b18ca205fe6f724ba063",
    },
    "authorization_schema": {
        "byte_count": 3165,
        "sha256": "c911db9d05009c892bce01f4b241fd6cad2bb043a77279d7c73f2026407f8558",
    },
    "fixture": {
        "byte_count": 13387,
        "sha256": "8074b2fa4a529190d2bb9bc8cc0b5c8020adc878b899e6a2676824468d046b68",
    },
}
EXPECTED_EXECUTION_SAFETY_IDENTITIES = {
    "policy": {
        "byte_count": 7985,
        "sha256": "a3e8692e691cfa90fba7fc945f4bb0fa55e5380cb9cbe9550857a053cd25cb12",
    },
    "job_identity_schema": {
        "byte_count": 2426,
        "sha256": "1177012523fa82caaedd528d1b127bea920869818032d9941b94d67712aae58c",
    },
    "fenced_action_adoption_schema": {
        "byte_count": 1899,
        "sha256": "14022c997b0435a6a844125f9d5c4a38e62327ac6150560b9b82349985175787",
    },
    "fixture": {
        "byte_count": 11250,
        "sha256": "560974384c6038e980867eab577ba81bd921687614ca5f3224129942b713e70d",
    },
}
EXPECTED_EVIDENCE_IDENTITIES = {
    "policy": {
        "byte_count": 9656,
        "sha256": "d9cea69a4680a0229b5680ea0de503e9d6f9d24eb6232893b727e11c1e52e9e0",
    },
    "event_schema": {
        "byte_count": 10832,
        "sha256": "45ab72fca886dca978473de0d9b43c3475a64bb0104a4f30bd8c4556f8b99591",
    },
    "event_catalog": {
        "byte_count": 13212,
        "sha256": "7508aa4061f9526d53b7e547125792016f08748078fb2cffbbcafb517fc6d7d7",
    },
    "fixture": {
        "byte_count": 22916,
        "sha256": "92c649b58d25391c5968fc0f64e6344e40933a91fa5957dcd346f052d67461aa",
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


def _verify_qualification_identity(
    raw: bytes, identity_key: str, reason: str, label: str
) -> None:
    identity = EXPECTED_QUALIFICATION_IDENTITIES[identity_key]
    if (
        len(raw) != identity["byte_count"]
        or hashlib.sha256(raw).hexdigest() != identity["sha256"]
    ):
        raise ValidationFailure(reason, f"{label} identity mismatch")


def _verify_qualification_policy(policy: dict[str, Any], raw: bytes) -> dict[str, Any]:
    try:
        canonical = (
            json.dumps(policy, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
    except (RecursionError, TypeError, UnicodeEncodeError) as exc:
        raise ValidationFailure(
            "qualification_policy_bytes",
            "QualificationContractSet is not canonical UTF-8 JSON",
        ) from exc
    _verify_qualification_identity(
        raw, "policy", "qualification_policy_identity", "qualification policy"
    )
    if raw != canonical:
        raise ValidationFailure(
            "qualification_policy_identity", "qualification policy is not canonical"
        )
    envelope = _require_exact_fields(
        policy, {"domain", "payload", "schema_version"}, "qualification policy"
    )
    if (
        envelope["domain"] != "local-ai-runtime/QualificationContractSet/v1"
        or type(envelope["schema_version"]) is not int
        or envelope["schema_version"] != 1
    ):
        raise ValidationFailure("qualification_policy_drift", "policy envelope mismatch")
    payload = _require_exact_fields(
        envelope["payload"],
        {
            "artifact_id",
            "artifact_version",
            "attempt_authorization_continuation",
            "auth_state",
            "authorization",
            "authorization_execution_grant",
            "baseline_id",
            "codex_sandbox_state_binding",
            "qualified_environment_binding",
            "qualification_sensitive_input_set",
            "repo_template_qualification",
        },
        "qualification policy payload",
        reason="qualification_policy_drift",
    )
    sensitive = _require_object(
        payload["qualification_sensitive_input_set"],
        "qualification sensitive input policy",
        reason="qualification_policy_drift",
    )
    qualification = _require_object(
        payload["repo_template_qualification"],
        "repo template qualification policy",
        reason="qualification_policy_drift",
    )
    environment = _require_object(
        payload["qualified_environment_binding"],
        "qualified environment policy",
        reason="qualification_policy_drift",
    )
    auth = _require_object(
        payload["auth_state"], "auth state policy", reason="qualification_policy_drift"
    )
    authorization = _require_object(
        payload["authorization"],
        "authorization policy",
        reason="qualification_policy_drift",
    )
    grant = _require_object(
        payload["authorization_execution_grant"],
        "authorization grant policy",
        reason="qualification_policy_drift",
    )
    continuation = _require_object(
        payload["attempt_authorization_continuation"],
        "authorization continuation policy",
        reason="qualification_policy_drift",
    )
    sandbox = _require_object(
        payload["codex_sandbox_state_binding"],
        "sandbox binding policy",
        reason="qualification_policy_drift",
    )
    sandbox_log = _require_object(
        sandbox.get("sandbox_log"),
        "sandbox log policy",
        reason="qualification_policy_drift",
    )
    if (
        payload["artifact_id"] != "P0A-QUALIFICATION"
        or payload["artifact_version"] != "QualificationContractSet.v1"
        or payload["baseline_id"] != BASELINE_SPECIFICATION_ID
        or sensitive.get("canonical_entry_kinds")
        != ["present", "absent", "expanded", "blocked"]
        or sensitive.get("working_tree_hash_in_authorization") is not False
        or qualification.get("generation_change")
        != "only_safety_relevant_binding_hash_change"
        or environment.get("controller_actions") != ["verify", "attach"]
        or auth.get("allowed_store") != "keyring"
        or auth.get("forbidden_stores") != ["file", "auto"]
        or authorization.get("excluded_fields")
        != [
            "task_id",
            "submission_id",
            "expected_base_commit",
            "derived_commit",
            "git_ref",
            "evidence_id",
        ]
        or grant.get("root_basis") != "active_authorization"
        or continuation.get("writer_restart_allowed") is not False
        or sandbox.get("official_contract_boundary")
        != "sandbox_log_field_schema_not_assumed"
        or sandbox_log.get("field_schema") != "opaque_uncommitted"
        or sandbox_log.get("content_hash_in_ordinary_state") is not False
        or sandbox_log.get("task_process_read") != "deny"
    ):
        raise ValidationFailure(
            "qualification_policy_drift", "qualification boundary mismatch"
        )
    return payload


def _validate_local_base_ref(value: Any) -> None:
    if not isinstance(value, str):
        raise ValidationFailure("sensitive_set_schema", "local_base_ref must be a string")
    try:
        raw = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValidationFailure("sensitive_set_schema", "local_base_ref is not UTF-8") from exc
    prefix = "refs/heads/"
    components = value.removeprefix(prefix).split("/")
    if (
        not value.startswith(prefix)
        or not 11 <= len(raw) <= 255
        or any(
            not component
            or component in {".", ".."}
            or component.startswith(".")
            or component.endswith((".", ".lock"))
            for component in components
        )
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or any(character in value for character in "~^:?*[")
        or ".." in value
        or any(token in value for token in ("\\", "@{", "//"))
        or value.startswith("refs/heads/codex/batch/")
    ):
        raise ValidationFailure("sensitive_set_schema", "local_base_ref is invalid")


def _validate_qualification_path(value: Any, label: str) -> None:
    if not isinstance(value, str):
        raise ValidationFailure("sensitive_set_schema", f"{label} must be a string")
    try:
        raw = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValidationFailure("sensitive_set_schema", f"{label} is not UTF-8") from exc
    components = value.split("/")
    if (
        not raw
        or len(raw) > 4096
        or value.startswith(("/", "\\"))
        or "\\" in value
        or any(component in {"", ".", ".."} for component in components)
    ):
        raise ValidationFailure("sensitive_set_schema", f"{label} is not repo-relative")


def _validate_qualification_entry(entry: Any) -> dict[str, Any]:
    entry = _require_object(entry, "qualification entry", reason="sensitive_set_schema")
    kind = entry.get("entry_kind")
    common = {"entry_kind", "subject", "rule_id", "discovery_source"}
    if kind == "present":
        required = common | {
            "repo_path",
            "windows_collision_key",
            "object_type",
            "mode",
            "git_oid_sha1",
            "sensitivity_class",
        }
    elif kind == "absent":
        required = common | {"candidate_path", "absence_result", "sensitivity_class"}
    elif kind == "expanded":
        required = common | {"directory_or_glob", "child_entry_hashes", "sensitivity_class"}
    elif kind == "blocked":
        required = common | {"blocked_class", "reason_code"}
    else:
        raise ValidationFailure("sensitive_entry_kind", f"unknown entry kind: {kind!r}")
    entry = _require_exact_fields(
        entry, required, f"{kind} qualification entry", reason="sensitive_set_schema"
    )
    for field in ("rule_id", "discovery_source"):
        value = entry[field]
        if not isinstance(value, str) or PUBLIC_ID_PATTERN.fullmatch(value) is None:
            raise ValidationFailure("sensitive_set_schema", f"{field} is invalid")
    if entry["discovery_source"] not in {"controller", "repo_profile", "task_template"}:
        raise ValidationFailure("sensitive_set_schema", "discovery source is not allowed")
    if kind == "blocked":
        subject = entry["subject"]
        if not isinstance(subject, str) or not subject or len(subject) > 4096:
            raise ValidationFailure("sensitive_set_schema", "blocked subject is invalid")
    else:
        _validate_qualification_path(entry["subject"], "entry subject")
    if kind == "present":
        _validate_qualification_path(entry["repo_path"], "present repo_path")
        if entry["subject"] != entry["repo_path"]:
            raise ValidationFailure("sensitive_set_schema", "present subject mismatch")
        if (
            not isinstance(entry["windows_collision_key"], str)
            or not isinstance(entry["git_oid_sha1"], str)
            or SHA1_PATTERN.fullmatch(entry["git_oid_sha1"]) is None
            or entry["object_type"] not in {"blob", "tree"}
            or entry["mode"] not in {"100644", "100755", "040000"}
            or (entry["object_type"] == "tree") != (entry["mode"] == "040000")
        ):
            raise ValidationFailure("sensitive_set_schema", "present entry identity mismatch")
    elif kind == "absent":
        _validate_qualification_path(entry["candidate_path"], "absent candidate_path")
        if (
            entry["subject"] != entry["candidate_path"]
            or entry["absence_result"] != "absent_at_observed_base"
        ):
            raise ValidationFailure("sensitive_set_schema", "absence proof mismatch")
    elif kind == "expanded":
        _validate_qualification_path(entry["directory_or_glob"], "expanded path")
        hashes = _require_string_array(
            entry["child_entry_hashes"], "child entry hashes", reason="sensitive_set_schema"
        )
        if (
            entry["subject"] != entry["directory_or_glob"]
            or len(hashes) > 10000
            or hashes != sorted(set(hashes))
            or any(not _is_sha256(value) for value in hashes)
        ):
            raise ValidationFailure("sensitive_set_schema", "expanded entry mismatch")
    else:
        if entry["blocked_class"] not in {
            "path",
            "reference",
            "object",
            "dynamic_loading",
            "collision",
        } or not isinstance(entry["reason_code"], str):
            raise ValidationFailure("sensitive_set_schema", "blocked entry mismatch")
    if kind != "blocked":
        sensitivity = entry["sensitivity_class"]
        if not isinstance(sensitivity, str) or PUBLIC_ID_PATTERN.fullmatch(sensitivity) is None:
            raise ValidationFailure("sensitive_set_schema", "sensitivity class is invalid")
    return entry


def _validate_sensitive_input_set(value: Any) -> str:
    value = _require_exact_fields(
        value,
        {
            "schema_version",
            "repo_id",
            "local_base_ref",
            "resolver_catalog_id",
            "resolver_catalog_sha256",
            "collision_alias_policy_generation",
            "negative_discovery_result",
            "entries",
        },
        "QualificationSensitiveInputSet",
        reason="sensitive_set_schema",
    )
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ValidationFailure("sensitive_set_schema", "sensitive set version mismatch")
    for field in ("repo_id", "resolver_catalog_id", "collision_alias_policy_generation"):
        item = value[field]
        if not isinstance(item, str) or PUBLIC_ID_PATTERN.fullmatch(item) is None:
            raise ValidationFailure("sensitive_set_schema", f"{field} is invalid")
    _validate_local_base_ref(value["local_base_ref"])
    if not _is_sha256(value["resolver_catalog_sha256"]):
        raise ValidationFailure("sensitive_set_schema", "resolver catalog hash is invalid")
    entries = _require_array(value["entries"], "sensitive entries", reason="sensitive_set_schema")
    if len(entries) > 10000:
        raise ValidationFailure("sensitive_set_schema", "too many sensitive entries")
    validated = [_validate_qualification_entry(entry) for entry in entries]
    order = [(entry["entry_kind"], entry["subject"], entry["rule_id"]) for entry in validated]
    if order != sorted(order) or len(order) != len(set(order)):
        raise ValidationFailure("sensitive_set_order", "sensitive entries are not ordered/unique")
    negative_result = value["negative_discovery_result"]
    if negative_result not in {
        "closed_no_unknowns",
        "blocked_unknown_dynamic_loading",
        "blocked_external_reference",
        "blocked_incomplete_recursion",
    }:
        raise ValidationFailure("sensitive_set_schema", "negative discovery result is invalid")
    if negative_result != "closed_no_unknowns" or any(
        entry["entry_kind"] == "blocked" for entry in validated
    ):
        return "qualification_failed"
    return "qualification_eligible"


def _validate_environment_binding(value: Any) -> None:
    hash_fields = {
        "binding_id",
        "bundle_identity_sha256",
        "volume_file_identity_sha256",
        "owner_dacl_sha256",
        "reparse_hardlink_audit_sha256",
        "alias_policy_observation_sha256",
        "dependency_tree_sha256",
        "readonly_roots_sha256",
        "gate_catalog_sha256",
        "offline_qualification_evidence_sha256",
    }
    value = _require_exact_fields(
        value,
        {
            "schema_version",
            "qualification_generation",
            "lock_hashes",
            "attempt_local_writable_cache",
            "controller_actions",
            "batch_setup_actions",
        }
        | hash_fields,
        "QualifiedEnvironmentBinding",
        reason="environment_binding_schema",
    )
    locks = _require_string_array(
        value["lock_hashes"], "environment lock hashes", reason="environment_binding_schema"
    )
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] != 1
        or type(value["qualification_generation"]) is not int
        or value["qualification_generation"] < 1
        or any(not _is_sha256(value[field]) for field in hash_fields)
        or not locks
        or locks != sorted(set(locks))
        or any(not _is_sha256(item) for item in locks)
        or value["attempt_local_writable_cache"] is not True
        or value["controller_actions"] != ["verify", "attach"]
        or value["batch_setup_actions"] != []
    ):
        raise ValidationFailure("environment_binding_schema", "environment binding mismatch")


def _validate_sandbox_binding(value: Any) -> None:
    value = _require_exact_fields(
        value,
        {
            "schema_version",
            "binding_id",
            "codex_generation",
            "platform_setup_generation",
            "sandbox_principal_id",
            "config_projection_sha256",
            "config_root_identity_sha256",
            "sandbox_root_identity_sha256",
            "sandbox_acl_attestation_id",
            "allowed_profiles",
            "sandbox_log_policy",
            "q0_probe_ids",
        },
        "CodexSandboxStateBinding",
        reason="sandbox_binding_schema",
    )
    for field in (
        "binding_id",
        "codex_generation",
        "platform_setup_generation",
        "sandbox_principal_id",
        "sandbox_acl_attestation_id",
    ):
        item = value[field]
        if not isinstance(item, str) or PUBLIC_ID_PATTERN.fullmatch(item) is None:
            raise ValidationFailure("sandbox_binding_schema", f"{field} is invalid")
    for field in (
        "config_projection_sha256",
        "config_root_identity_sha256",
        "sandbox_root_identity_sha256",
    ):
        if not _is_sha256(value[field]):
            raise ValidationFailure("sandbox_binding_schema", f"{field} is invalid")
    profiles = _require_string_array(
        value["allowed_profiles"], "allowed sandbox profiles", reason="sandbox_binding_schema"
    )
    probes = _require_string_array(
        value["q0_probe_ids"], "sandbox Q0 probes", reason="sandbox_binding_schema"
    )
    log_policy = _require_exact_fields(
        value["sandbox_log_policy"],
        {
            "opaque",
            "file_max_bytes",
            "aggregate_max_bytes",
            "retention",
            "rotation_procedure_id",
            "task_process_read",
            "ordinary_evidence_projection",
        },
        "sandbox log policy",
        reason="sandbox_binding_schema",
    )
    if (
        profiles != ["batch-writer", "batch-gate", "batch-git"]
        or probes
        != [
            "sandbox-principal-isolation",
            "sandbox-secret-deny-read",
            "sandbox-log-rotation",
        ]
        or log_policy
        != {
            "opaque": True,
            "file_max_bytes": 8388608,
            "aggregate_max_bytes": 33554432,
            "retention": 4,
            "rotation_procedure_id": "sandbox-log-rotate-v1",
            "task_process_read": "deny",
            "ordinary_evidence_projection": "none",
        }
    ):
        raise ValidationFailure("sandbox_binding_schema", "sandbox boundary mismatch")


AUTHORIZATION_FIELDS = {
    "schema_version",
    "authorization_id",
    "generation",
    "active_map_generation",
    "revoke_head_sha256",
    "revoke_head_version",
    "issued_at_utc",
    "expires_at_utc",
    "active_runtime_identity_sha256",
    "operator_sid_sha256",
    "repo_id",
    "template_id",
    "execution_profile_id",
    "parameter_schema_sha256",
    "risk_class",
    "sensitive_set_sha256",
    "instruction_inventory_sha256",
    "skill_inventory_sha256",
    "qualification_generation",
    "environment_binding_sha256",
    "toolchain_generation",
    "model",
    "reasoning_effort",
    "permission_config_feature_tool_inventory_sha256",
    "gate_policy_sha256",
    "git_policy_sha256",
    "evidence_mode",
    "resource_limits_sha256",
}


def _validate_authorization(value: Any) -> str:
    value = _require_exact_fields(
        value, AUTHORIZATION_FIELDS, "Authorization", reason="authorization_schema"
    )
    hash_fields = {
        field
        for field in AUTHORIZATION_FIELDS
        if field.endswith("_sha256") or field == "authorization_id"
    }
    id_fields = {"repo_id", "template_id", "execution_profile_id", "toolchain_generation"}
    timestamp_pattern = re.compile(
        r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$"
    )
    timestamp_fields = ("issued_at_utc", "expires_at_utc")
    if any(
        not isinstance(value[field], str)
        or timestamp_pattern.fullmatch(value[field]) is None
        for field in timestamp_fields
    ):
        raise ValidationFailure("authorization_schema", "Authorization timestamp mismatch")
    try:
        issued_at = datetime.strptime(value["issued_at_utc"], "%Y-%m-%dT%H:%M:%S.%fZ")
        expires_at = datetime.strptime(value["expires_at_utc"], "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as exc:
        raise ValidationFailure("authorization_schema", "Authorization timestamp is invalid") from exc
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] != 1
        or any(type(value[field]) is not int or value[field] < 1 for field in (
            "generation",
            "active_map_generation",
            "qualification_generation",
        ))
        or type(value["revoke_head_version"]) is not int
        or value["revoke_head_version"] < 0
        or any(not _is_sha256(value[field]) for field in hash_fields)
        or any(
            not isinstance(value[field], str)
            or PUBLIC_ID_PATTERN.fullmatch(value[field]) is None
            for field in id_fields
        )
        or value["risk_class"] != "low"
        or value["reasoning_effort"] not in {"low", "medium", "high", "xhigh"}
        or value["evidence_mode"] not in {"standard", "restricted"}
        or not isinstance(value["model"], str)
        or PUBLIC_VALUE_PATTERN.fullmatch(value["model"]) is None
        or issued_at >= expires_at
    ):
        raise ValidationFailure("authorization_schema", "Authorization field mismatch")
    payload = dict(value)
    authorization_id = payload.pop("authorization_id")
    envelope = {
        "domain": "local-ai-runtime/Authorization/v1",
        "payload": payload,
        "schema_version": 1,
    }
    raw = (
        json.dumps(envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    expected = hashlib.sha256(raw).hexdigest()
    if authorization_id != expected:
        raise ValidationFailure("authorization_fingerprint", "Authorization ID mismatch")
    return expected


def _evaluate_observation_refresh(case: dict[str, Any]) -> str:
    case = _require_exact_fields(
        case,
        {
            "case_id",
            "binding_hashes_equal",
            "alias_evidence_equal",
            "fresh_observation",
            "expected_result",
        },
        "observation refresh case",
        reason="qualification_fixture_schema",
    )
    if not all(
        isinstance(case[field], bool)
        for field in ("binding_hashes_equal", "alias_evidence_equal", "fresh_observation")
    ):
        raise ValidationFailure("qualification_fixture_schema", "observation flags must be bool")
    if not case["fresh_observation"]:
        return "stale_observation_rejected"
    if not case["alias_evidence_equal"]:
        return "scope_requalification_required"
    if not case["binding_hashes_equal"]:
        return "new_generation_required"
    return "cas_refresh_without_generation_increment"


def _evaluate_working_tree(case: dict[str, Any]) -> str:
    case = _require_exact_fields(
        case,
        {
            "case_id",
            "sensitive_or_ancestor_dirty",
            "protected_or_approved_path_dirty",
            "unrelated_dirty_count",
            "expected_result",
        },
        "working tree case",
        reason="qualification_fixture_schema",
    )
    if (
        not isinstance(case["sensitive_or_ancestor_dirty"], bool)
        or not isinstance(case["protected_or_approved_path_dirty"], bool)
        or type(case["unrelated_dirty_count"]) is not int
        or case["unrelated_dirty_count"] < 0
    ):
        raise ValidationFailure("qualification_fixture_schema", "working tree case mismatch")
    if case["sensitive_or_ancestor_dirty"] or case["protected_or_approved_path_dirty"]:
        return "qualification_blocked"
    if case["unrelated_dirty_count"]:
        return "qualification_allowed_aggregate_only"
    return "qualification_allowed"


def _evaluate_auth_store(case: dict[str, Any]) -> str:
    case = _require_exact_fields(
        case,
        {"case_id", "store", "keyring_available", "expected_result"},
        "auth store case",
        reason="qualification_fixture_schema",
    )
    if not isinstance(case["store"], str) or not isinstance(case["keyring_available"], bool):
        raise ValidationFailure("qualification_fixture_schema", "auth store case mismatch")
    if case["store"] == "file":
        return "file_fallback_forbidden"
    if case["store"] == "auto":
        return "auto_fallback_forbidden"
    if case["store"] != "keyring":
        return "unknown_store_rejected"
    if not case["keyring_available"]:
        return "keyring_unavailable_q0_failure"
    return "auth_qualified"


def _evaluate_sandbox_projection(case: dict[str, Any]) -> str:
    case = _require_exact_fields(
        case,
        {
            "case_id",
            "secret_metadata_exported",
            "sandbox_log_content_or_hash_exported",
            "task_process_protected_read",
            "whole_code_home_immutable",
            "rotation_over_limit",
            "expected_result",
        },
        "sandbox projection case",
        reason="qualification_fixture_schema",
    )
    fields = (
        "secret_metadata_exported",
        "sandbox_log_content_or_hash_exported",
        "task_process_protected_read",
        "whole_code_home_immutable",
        "rotation_over_limit",
    )
    if not all(isinstance(case[field], bool) for field in fields):
        raise ValidationFailure("qualification_fixture_schema", "sandbox flags must be bool")
    if case["secret_metadata_exported"]:
        return "secret_metadata_projection_rejected"
    if case["sandbox_log_content_or_hash_exported"]:
        return "diagnostic_projection_rejected"
    if case["task_process_protected_read"]:
        return "platform_incompatible"
    if case["whole_code_home_immutable"]:
        return "whole_root_immutability_rejected"
    if case["rotation_over_limit"]:
        return "stop_new_claim_and_operator_action"
    return "binding_accepted"


def _evaluate_grant_revoke(case: dict[str, Any]) -> str:
    case = _require_exact_fields(
        case,
        {
            "case_id",
            "grant_exists",
            "basis_kind",
            "action_kind",
            "grant_effect_identity",
            "action_effect_identity",
            "grant_committed_before_revoke",
            "revoke_committed_before_grant",
            "resume_count",
            "expected_result",
        },
        "grant/revoke case",
        reason="qualification_fixture_schema",
    )
    if (
        not isinstance(case["grant_exists"], bool)
        or not isinstance(case["grant_committed_before_revoke"], bool)
        or not isinstance(case["revoke_committed_before_grant"], bool)
        or type(case["resume_count"]) is not int
        or case["resume_count"] < 0
    ):
        raise ValidationFailure("qualification_fixture_schema", "grant/revoke flags mismatch")
    if case["revoke_committed_before_grant"] or not case["grant_exists"]:
        return "block_new_effect"
    if case["grant_effect_identity"] != case["action_effect_identity"]:
        return "effect_identity_mismatch"
    if case["resume_count"] > 1:
        return "duplicate_process_effect_blocked"
    if case["basis_kind"] == "inherited_fenced_action" and case["action_kind"] in {
        "writer",
        "gate_run",
        "model_decision",
        "qualification",
        "auth_refresh",
        "arbitrary_command",
    }:
        return "inherited_basis_forbidden"
    if case["basis_kind"] != "active_authorization":
        raise ValidationFailure("qualification_fixture_schema", "unsupported grant basis")
    if not case["grant_committed_before_revoke"]:
        raise ValidationFailure("qualification_fixture_schema", "grant has no linearization")
    return "complete_exact_effect"


def _evaluate_continuation(case: dict[str, Any]) -> str:
    case = _require_exact_fields(
        case,
        {
            "case_id",
            "allowed_stages",
            "expands_contract",
            "prior_head_unique",
            "terminal_stage_reopened",
            "expected_result",
        },
        "continuation case",
        reason="qualification_fixture_schema",
    )
    stages = _require_string_array(
        case["allowed_stages"], "continuation stages", reason="qualification_fixture_schema"
    )
    if not all(
        isinstance(case[field], bool)
        for field in ("expands_contract", "prior_head_unique", "terminal_stage_reopened")
    ):
        raise ValidationFailure("qualification_fixture_schema", "continuation flags must be bool")
    if "writer" in stages:
        return "writer_restart_forbidden"
    if case["expands_contract"]:
        return "contract_expansion_forbidden"
    if not case["prior_head_unique"]:
        return "prior_head_conflict"
    if case["terminal_stage_reopened"]:
        return "terminal_stage_reopen_forbidden"
    allowed = {
        "gate_verify",
        "object_plan",
        "object_promote",
        "finalize_index",
        "finalize_head",
        "create_task_ref",
        "evidence_publish",
        "worktree_remove",
    }
    if not stages or not set(stages).issubset(allowed) or len(stages) != len(set(stages)):
        raise ValidationFailure("qualification_fixture_schema", "continuation stages mismatch")
    return "append_continuation"


def _verify_qualification_case_matrix(
    fixture: dict[str, Any],
    field: str,
    expected_ids: set[str],
    evaluator: Callable[[dict[str, Any]], str],
) -> int:
    cases = _fixture_cases(fixture, field, expected_ids)
    for case in cases:
        actual = evaluator(case)
        if actual != case.get("expected_result"):
            raise ValidationFailure("fixture_result_mismatch", str(case.get("case_id")))
    return len(cases)


def verify_qualification_component(repo_root: Path) -> dict[str, Any]:
    policy, policy_raw = _load_json_object(repo_root / QUALIFICATION_POLICY_RELATIVE)
    _, sensitive_schema_raw = _load_json_object(repo_root / SENSITIVE_INPUT_SCHEMA_RELATIVE)
    _, authorization_schema_raw = _load_json_object(repo_root / AUTHORIZATION_SCHEMA_RELATIVE)
    fixture, fixture_raw = _load_json_object(repo_root / QUALIFICATION_FIXTURE_RELATIVE)
    _verify_qualification_policy(policy, policy_raw)
    _verify_qualification_identity(
        sensitive_schema_raw,
        "sensitive_input_schema",
        "qualification_schema_drift",
        "sensitive input schema",
    )
    _verify_qualification_identity(
        authorization_schema_raw,
        "authorization_schema",
        "qualification_schema_drift",
        "Authorization schema",
    )
    _verify_qualification_identity(
        fixture_raw, "fixture", "qualification_fixture_drift", "qualification fixture"
    )
    fixture = _require_exact_fields(
        fixture,
        {
            "fixture_id",
            "schema_version",
            "policy_path",
            "sensitive_input_set_schema_path",
            "authorization_schema_path",
            "sensitive_input_set_positive",
            "blocked_entry_case",
            "environment_binding_positive",
            "sandbox_binding_positive",
            "authorization_positive",
            "observation_refresh_cases",
            "working_tree_cases",
            "auth_store_cases",
            "sandbox_projection_cases",
            "grant_revoke_cases",
            "continuation_cases",
        },
        "qualification fixture",
        reason="qualification_fixture_schema",
    )
    if (
        fixture["fixture_id"] != "QualificationContractSet.v1.contract-fixtures"
        or type(fixture["schema_version"]) is not int
        or fixture["schema_version"] != 1
        or fixture["policy_path"] != str(QUALIFICATION_POLICY_RELATIVE).replace("\\", "/")
        or fixture["sensitive_input_set_schema_path"]
        != str(SENSITIVE_INPUT_SCHEMA_RELATIVE).replace("\\", "/")
        or fixture["authorization_schema_path"]
        != str(AUTHORIZATION_SCHEMA_RELATIVE).replace("\\", "/")
    ):
        raise ValidationFailure("qualification_fixture_schema", "fixture identity mismatch")
    if _validate_sensitive_input_set(fixture["sensitive_input_set_positive"]) != "qualification_eligible":
        raise ValidationFailure("sensitive_set_result", "positive sensitive set is not eligible")
    blocked = dict(
        _require_object(
            fixture["blocked_entry_case"],
            "blocked entry case",
            reason="qualification_fixture_schema",
        )
    )
    expected_blocked_result = blocked.pop("expected_result", None)
    _validate_qualification_entry(blocked)
    if expected_blocked_result != "qualification_failed":
        raise ValidationFailure("sensitive_set_result", "blocked entry must fail qualification")
    _validate_environment_binding(fixture["environment_binding_positive"])
    _validate_sandbox_binding(fixture["sandbox_binding_positive"])
    authorization_id = _validate_authorization(fixture["authorization_positive"])
    counts = {
        "observation_refresh": _verify_qualification_case_matrix(
            fixture,
            "observation_refresh_cases",
            {
                "identical_bindings_new_base",
                "safety_binding_changed",
                "alias_evidence_changed",
                "observation_stale",
            },
            _evaluate_observation_refresh,
        ),
        "working_tree": _verify_qualification_case_matrix(
            fixture,
            "working_tree_cases",
            {
                "clean_relevant_paths",
                "sensitive_dirty",
                "approved_path_dirty",
                "unrelated_dirty_aggregate_only",
            },
            _evaluate_working_tree,
        ),
        "auth_store": _verify_qualification_case_matrix(
            fixture,
            "auth_store_cases",
            {"keyring_available", "file_forbidden", "auto_forbidden", "keyring_unavailable"},
            _evaluate_auth_store,
        ),
        "sandbox_projection": _verify_qualification_case_matrix(
            fixture,
            "sandbox_projection_cases",
            {
                "valid_public_binding",
                "secret_metadata_exported",
                "sandbox_log_hash_exported",
                "task_read_boundary_bypassed",
                "whole_code_home_marked_immutable",
                "sandbox_log_over_limit",
            },
            _evaluate_sandbox_projection,
        ),
        "grant_revoke": _verify_qualification_case_matrix(
            fixture,
            "grant_revoke_cases",
            {
                "grant_then_later_revoke",
                "revoke_before_grant",
                "effect_identity_mismatch",
                "duplicate_resume",
                "inherited_writer_forbidden",
            },
            _evaluate_grant_revoke,
        ),
        "continuation": _verify_qualification_case_matrix(
            fixture,
            "continuation_cases",
            {
                "valid_closeout_continuation",
                "writer_restart_forbidden",
                "contract_expansion_forbidden",
                "prior_head_conflict",
                "terminal_stage_reopen",
            },
            _evaluate_continuation,
        ),
    }
    return {
        "status": "pass",
        "component": "qualification",
        "artifact_version": "QualificationContractSet.v1",
        "artifact_byte_count": len(policy_raw),
        "artifact_sha256": hashlib.sha256(policy_raw).hexdigest(),
        "authorization_fingerprint": authorization_id,
        "sensitive_entry_kind_count": 4,
        "fixture_counts": counts,
    }


def _verify_execution_safety_identity(
    raw: bytes, identity_key: str, reason: str, label: str
) -> None:
    identity = EXPECTED_EXECUTION_SAFETY_IDENTITIES[identity_key]
    if (
        len(raw) != identity["byte_count"]
        or hashlib.sha256(raw).hexdigest() != identity["sha256"]
    ):
        raise ValidationFailure(reason, f"{label} identity mismatch")


def _verify_execution_safety_policy(
    policy: dict[str, Any], raw: bytes
) -> dict[str, Any]:
    try:
        canonical = (
            json.dumps(policy, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
    except (RecursionError, TypeError, UnicodeEncodeError) as exc:
        raise ValidationFailure(
            "execution_safety_policy_bytes",
            "ExecutionSafetyContractSet is not canonical UTF-8 JSON",
        ) from exc
    _verify_execution_safety_identity(
        raw, "policy", "execution_safety_policy_identity", "execution safety policy"
    )
    if raw != canonical:
        raise ValidationFailure(
            "execution_safety_policy_identity",
            "execution safety policy is not canonical",
        )
    envelope = _require_exact_fields(
        policy, {"domain", "payload", "schema_version"}, "execution safety policy"
    )
    if (
        envelope["domain"] != "local-ai-runtime/ExecutionSafetyContractSet/v1"
        or type(envelope["schema_version"]) is not int
        or envelope["schema_version"] != 1
    ):
        raise ValidationFailure(
            "execution_safety_policy_drift", "execution safety envelope mismatch"
        )
    payload = _require_exact_fields(
        envelope["payload"],
        {
            "artifact_id",
            "artifact_version",
            "baseline_id",
            "child_handle_manifest",
            "crash_recovery",
            "effect_plan",
            "execution_authority_union",
            "fenced_actions",
            "job_identity",
            "launch_protocol",
            "named_object_policy",
            "process_handle_policy",
            "safety_only",
            "stage_launch",
            "writer_identity",
        },
        "execution safety payload",
        reason="execution_safety_policy_drift",
    )
    if (
        payload["artifact_id"] != "P0A-EXECUTION"
        or payload["artifact_version"] != "ExecutionSafetyContractSet.v1"
        or payload["baseline_id"] != BASELINE_SPECIFICATION_ID
    ):
        raise ValidationFailure(
            "execution_safety_policy_drift", "execution safety identity mismatch"
        )
    effect_plan = _require_object(
        payload["effect_plan"], "EffectPlan policy", reason="execution_safety_policy_drift"
    )
    child_manifest = _require_object(
        payload["child_handle_manifest"],
        "child handle manifest policy",
        reason="execution_safety_policy_drift",
    )
    writer = _require_object(
        payload["writer_identity"],
        "writer identity policy",
        reason="execution_safety_policy_drift",
    )
    launch = _require_object(
        payload["launch_protocol"],
        "launch protocol",
        reason="execution_safety_policy_drift",
    )
    handles = _require_object(
        payload["process_handle_policy"],
        "process handle policy",
        reason="execution_safety_policy_drift",
    )
    authority = _require_object(
        payload["execution_authority_union"],
        "execution authority union",
        reason="execution_safety_policy_drift",
    )
    fenced = _require_object(
        payload["fenced_actions"],
        "fenced action policy",
        reason="execution_safety_policy_drift",
    )
    safety = _require_object(
        payload["safety_only"],
        "safety-only policy",
        reason="execution_safety_policy_drift",
    )
    named = _require_object(
        payload["named_object_policy"],
        "named object policy",
        reason="execution_safety_policy_drift",
    )
    crash = _require_object(
        payload["crash_recovery"],
        "crash recovery policy",
        reason="execution_safety_policy_drift",
    )
    job_identity = _require_object(
        payload["job_identity"],
        "JobIdentity policy",
        reason="execution_safety_policy_drift",
    )
    stage_launch = _require_object(
        payload["stage_launch"],
        "stage launch policy",
        reason="execution_safety_policy_drift",
    )
    if (
        effect_plan.get("effect_kinds") != ["file", "process", "git", "evidence"]
        or effect_plan.get("record_type") != "EffectPlan"
        or effect_plan.get("pre_execution_required") is not True
        or child_manifest.get("record_type") != "ChildHandleManifest.v1"
        or job_identity.get("record_type") != "JobIdentity.v1"
        or stage_launch.get("record_type") != "StageLaunchRecord.v1"
        or writer.get("effect_formula")
        != "stable(task_generation,resolved_writer_intent)"
        or writer.get("effect_id_field") != "writer_effect_id"
        or writer.get("launch_formula") != "unique(writer_effect_id,attempt_id)"
        or writer.get("launch_id_field") != "writer_launch_id"
        or writer.get("restart_after_execution_commit") is not False
        or launch.get("mandatory_attributes")
        != ["PROC_THREAD_ATTRIBUTE_JOB_LIST", "PROC_THREAD_ATTRIBUTE_HANDLE_LIST"]
        or launch.get("resume_before_flush") is not False
        or launch.get("db_transaction_during_create_process") is not False
        or launch.get("writer_record_type") != "WriterLaunchRecord.v1"
        or handles.get("policy_id") != "ProcessHandlePolicy.v1"
        or handles.get("bInheritHandles") is not True
        or handles.get("STARTF_USESTDHANDLES") is not True
        or handles.get("stdio_must_exactly_match_handle_list") is not True
        or authority.get("kinds")
        != ["authorization_execution_grant", "safety_only_execution_record"]
        or authority.get("record_types")
        != {
            "authorization_execution_grant": "AuthorizationExecutionGrant.v1",
            "safety_only_execution_record": "SafetyOnlyExecutionRecord.v1",
        }
        or authority.get("single_authority_per_effect") is not True
        or fenced.get("initial_head_kind") != "intent"
        or fenced.get("record_types")
        != {
            "adoption": "FencedActionAdoption.v1",
            "head": "FencedActionHead.v1",
            "intent": "FencedActionIntent.v1",
            "result": "FencedActionResult.v1",
        }
        or fenced.get("terminal_adoption_allowed") is not False
        or safety.get("record_type") != "SafetyOnlyExecutionRecord.v1"
        or safety.get("reserve_generation_exact") is not True
        or named.get("policy_id") != "NamedObjectPolicy.v1"
        or named.get("zero_process_reuse_allowed") is not False
        or crash.get("authority_commit_before_resume") is not True
        or crash.get("same_name_error_already_exists")
        != "close_inspection_handle_and_park_job_handle_still_open"
    ):
        raise ValidationFailure(
            "execution_safety_policy_drift", "execution safety boundary mismatch"
        )
    required_actions = {
        "create_worktree",
        "checkout_base",
        "materialize_object_set",
        "artifact_publish",
        "promote_objects",
        "finalize_worktree_index",
        "finalize_worktree_head",
        "create_task_ref",
        "remove_worktree",
        "terminate_job",
        "release_emergency_reserve",
        "rebuild_emergency_reserve",
    }
    if set(fenced.get("allowlist", [])) != required_actions:
        raise ValidationFailure(
            "execution_safety_policy_drift", "fenced action allowlist mismatch"
        )
    return payload


def _content_addressed_record_id(
    value: dict[str, Any], id_field: str, domain: str
) -> str:
    payload = dict(value)
    actual = payload.pop(id_field)
    envelope = {"domain": domain, "payload": payload, "schema_version": 1}
    raw = (
        json.dumps(envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    expected = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise ValidationFailure(
            "execution_record_fingerprint", f"{id_field} does not match canonical record"
        )
    return expected


JOB_IDENTITY_REQUIRED_FIELDS = {
    "schema_version",
    "job_identity_id",
    "job_name",
    "process_kind",
    "security_policy_sha256",
    "limit_policy_sha256",
    "controller_pid",
    "controller_creation_time_100ns",
    "process_pid",
    "process_creation_time_100ns",
    "executable_identity_sha256",
    "attempt_id",
    "task_generation",
    "fence",
    "boot_identity_sha256",
}


def _validate_job_identity(value: Any) -> str:
    if not isinstance(value, dict):
        raise ValidationFailure("job_identity_schema", "JobIdentity must be an object")
    fields = set(value)
    if fields != JOB_IDENTITY_REQUIRED_FIELDS and fields != JOB_IDENTITY_REQUIRED_FIELDS | {
        "run_uuid"
    }:
        raise ValidationFailure("job_identity_schema", "JobIdentity fields mismatch")
    process_kinds = {
        "writer",
        "gate",
        "git",
        "probe",
        "recovery_helper",
        "controller_action_helper",
        "safety_helper",
    }
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] != 1
        or value["process_kind"] not in process_kinds
        or any(
            type(value[field]) is not int or value[field] < 1
            for field in (
                "controller_pid",
                "controller_creation_time_100ns",
                "process_pid",
                "process_creation_time_100ns",
                "task_generation",
                "fence",
            )
        )
        or any(
            not _is_sha256(value[field])
            for field in (
                "job_identity_id",
                "security_policy_sha256",
                "limit_policy_sha256",
                "executable_identity_sha256",
                "boot_identity_sha256",
            )
        )
        or not isinstance(value["attempt_id"], str)
        or UUID_V4_PATTERN.fullmatch(value["attempt_id"]) is None
    ):
        raise ValidationFailure("job_identity_schema", "JobIdentity value mismatch")
    sid_hash = r"[0-9a-f]{64}"
    if value["process_kind"] == "writer":
        if "run_uuid" in value:
            raise ValidationFailure("job_identity_schema", "writer Job cannot have run UUID")
        expected_name = re.compile(
            rf"^Global\\LocalAIRuntime\.Job\.{sid_hash}\.{re.escape(value['attempt_id'])}\.v1$"
        )
    else:
        run_uuid = value.get("run_uuid")
        if not isinstance(run_uuid, str) or UUID_V4_PATTERN.fullmatch(run_uuid) is None:
            raise ValidationFailure("job_identity_schema", "StageJob run UUID mismatch")
        expected_name = re.compile(
            rf"^Global\\LocalAIRuntime\.StageJob\.{sid_hash}\.{re.escape(value['attempt_id'])}\.{re.escape(run_uuid)}\.v1$"
        )
    if not isinstance(value["job_name"], str) or expected_name.fullmatch(value["job_name"]) is None:
        raise ValidationFailure("job_identity_schema", "JobIdentity name mismatch")
    return _content_addressed_record_id(
        value, "job_identity_id", "local-ai-runtime/JobIdentity/v1"
    )


FENCED_ADOPTION_FIELDS = {
    "schema_version",
    "action_id",
    "prior_head_kind",
    "prior_head_hash",
    "prior_fence",
    "new_fence",
    "takeover_proof_hash",
    "effect_spec_hash",
    "postcondition_verifier_id",
    "created_at_utc",
    "inherited_authority_kind",
    "inherited_authority_id",
    "inherited_authority_sha256",
    "adoption_hash",
}


def _validate_fenced_action_adoption(value: Any) -> str:
    value = _require_exact_fields(
        value,
        FENCED_ADOPTION_FIELDS,
        "FencedActionAdoption",
        reason="fenced_adoption_schema",
    )
    timestamp_pattern = re.compile(
        r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$"
    )
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] != 1
        or value["prior_head_kind"] not in {"intent", "adoption"}
        or type(value["prior_fence"]) is not int
        or type(value["new_fence"]) is not int
        or value["prior_fence"] < 1
        or value["new_fence"] != value["prior_fence"] + 1
        or value["inherited_authority_kind"]
        not in {"authorization_execution_grant", "safety_only_execution_record"}
        or any(
            not isinstance(value[field], str)
            or PUBLIC_ID_PATTERN.fullmatch(value[field]) is None
            for field in (
                "action_id",
                "postcondition_verifier_id",
                "inherited_authority_id",
            )
        )
        or any(
            not _is_sha256(value[field])
            for field in (
                "prior_head_hash",
                "takeover_proof_hash",
                "effect_spec_hash",
                "inherited_authority_sha256",
                "adoption_hash",
            )
        )
        or not isinstance(value["created_at_utc"], str)
        or timestamp_pattern.fullmatch(value["created_at_utc"]) is None
    ):
        raise ValidationFailure("fenced_adoption_schema", "adoption value mismatch")
    try:
        datetime.strptime(value["created_at_utc"], "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as exc:
        raise ValidationFailure(
            "fenced_adoption_schema", "adoption timestamp is invalid"
        ) from exc
    return _content_addressed_record_id(
        value, "adoption_hash", "local-ai-runtime/FencedActionAdoption/v1"
    )


def _evaluate_writer_identity(case: dict[str, Any]) -> str:
    case = _require_exact_fields(
        case,
        {
            "case_id",
            "same_task_generation",
            "same_resolved_intent",
            "writer_execution_committed",
            "fresh_attempt",
            "prior_suspended_terminal",
            "expected_result",
        },
        "writer identity case",
        reason="execution_safety_fixture_schema",
    )
    flags = (
        "same_task_generation",
        "same_resolved_intent",
        "writer_execution_committed",
        "fresh_attempt",
        "prior_suspended_terminal",
    )
    if not all(isinstance(case[field], bool) for field in flags):
        raise ValidationFailure(
            "execution_safety_fixture_schema", "writer identity flags must be bool"
        )
    if not case["same_task_generation"] or not case["same_resolved_intent"]:
        return "new_effect_identity_required"
    if case["writer_execution_committed"]:
        return "writer_restart_forbidden"
    if not case["fresh_attempt"]:
        return "duplicate_launch_forbidden"
    if not case["prior_suspended_terminal"]:
        return "prior_process_unresolved"
    return "reuse_effect_new_launch"


def _evaluate_process_handles(case: dict[str, Any]) -> str:
    case = _require_exact_fields(
        case,
        {
            "case_id",
            "create_suspended",
            "inherit_handles",
            "startf_use_std_handles",
            "job_list_count",
            "handle_roles",
            "stdio_matches",
            "parent_child_ends_closed",
            "extra_handle_count",
            "expected_result",
        },
        "process handle case",
        reason="execution_safety_fixture_schema",
    )
    roles = _require_string_array(
        case["handle_roles"],
        "process handle roles",
        reason="execution_safety_fixture_schema",
    )
    if (
        not isinstance(case["create_suspended"], bool)
        or not isinstance(case["inherit_handles"], bool)
        or not isinstance(case["startf_use_std_handles"], bool)
        or not isinstance(case["stdio_matches"], bool)
        or not isinstance(case["parent_child_ends_closed"], bool)
        or type(case["job_list_count"]) is not int
        or type(case["extra_handle_count"]) is not int
        or case["job_list_count"] < 0
        or case["extra_handle_count"] < 0
    ):
        raise ValidationFailure(
            "execution_safety_fixture_schema", "process handle case mismatch"
        )
    if not case["create_suspended"]:
        return "create_suspended_required"
    if case["job_list_count"] != 1:
        return "atomic_job_join_required"
    if not roles:
        return "handle_list_required"
    if not case["inherit_handles"]:
        return "inherit_handles_required"
    if not case["startf_use_std_handles"]:
        return "startf_use_stdhandles_required"
    if case["extra_handle_count"]:
        return "ambient_handle_rejected"
    if roles != ["stdin_read", "stdout_write", "stderr_write"] or not case[
        "stdio_matches"
    ]:
        return "exact_stdio_rejected"
    if not case["parent_child_ends_closed"]:
        return "pre_resume_close_required"
    return "launch_ready"


def _evaluate_execution_authority(case: dict[str, Any]) -> str:
    case = _require_exact_fields(
        case,
        {
            "case_id",
            "subject_kind",
            "authority_kind",
            "basis_kind",
            "effect_exact",
            "expected_result",
        },
        "execution authority case",
        reason="execution_safety_fixture_schema",
    )
    if not isinstance(case["effect_exact"], bool):
        raise ValidationFailure(
            "execution_safety_fixture_schema", "authority effect_exact must be bool"
        )
    if case["authority_kind"] == "none":
        return "unauthorized_side_effect"
    if not case["effect_exact"]:
        return "effect_identity_mismatch"
    inherited_forbidden = {
        "writer",
        "gate_run",
        "model_decision",
        "qualification",
        "auth_refresh",
        "arbitrary_command",
    }
    if (
        case["authority_kind"] == "authorization_execution_grant"
        and case["basis_kind"] == "inherited_fenced_action"
        and case["subject_kind"] in inherited_forbidden
    ):
        return "inherited_basis_forbidden"
    safety_allowed = {
        "terminate_job",
        "drain_pipe",
        "seal_journal",
        "readonly_reconcile",
        "durable_recovery_handoff",
        "release_emergency_reserve",
        "rebuild_emergency_reserve",
        "host_preserving_helper",
    }
    if case["authority_kind"] == "safety_only_execution_record":
        if case["basis_kind"] != "safety_only":
            return "authority_basis_mismatch"
        if case["subject_kind"] not in safety_allowed:
            return "safety_effect_forbidden"
        return "authority_accepted"
    if case["authority_kind"] != "authorization_execution_grant" or case[
        "basis_kind"
    ] not in {"active_authorization", "inherited_fenced_action"}:
        return "authority_basis_mismatch"
    return "authority_accepted"


def _evaluate_adoption(case: dict[str, Any]) -> str:
    case = _require_exact_fields(
        case,
        {
            "case_id",
            "prior_head_kind",
            "prior_head_present",
            "head_matches",
            "effect_matches",
            "authority_matches",
            "terminal",
            "expected_result",
        },
        "adoption case",
        reason="execution_safety_fixture_schema",
    )
    flags = (
        "prior_head_present",
        "head_matches",
        "effect_matches",
        "authority_matches",
        "terminal",
    )
    if (
        case["prior_head_kind"] not in {"intent", "adoption"}
        or not all(isinstance(case[field], bool) for field in flags)
    ):
        raise ValidationFailure(
            "execution_safety_fixture_schema", "adoption case mismatch"
        )
    if not case["prior_head_present"]:
        return "prior_head_required"
    if case["terminal"]:
        return "terminal_adoption_forbidden"
    if not case["head_matches"]:
        return "head_cas_conflict"
    if not case["effect_matches"]:
        return "effect_mismatch_park"
    if not case["authority_matches"]:
        return "authority_mismatch_park"
    return "adoption_cas_append"


def _evaluate_crash_window(case: dict[str, Any]) -> str:
    case = _require_exact_fields(
        case,
        {
            "case_id",
            "exit_kind",
            "process_created_suspended",
            "execution_committed",
            "resume_attempted",
            "same_name_error",
            "stdout_eof",
            "stderr_eof",
            "expected_result",
        },
        "crash window case",
        reason="execution_safety_fixture_schema",
    )
    flags = (
        "process_created_suspended",
        "execution_committed",
        "resume_attempted",
        "same_name_error",
        "stdout_eof",
        "stderr_eof",
    )
    if not all(isinstance(case[field], bool) for field in flags):
        raise ValidationFailure(
            "execution_safety_fixture_schema", "crash flags must be bool"
        )
    if case["exit_kind"] not in {
        "pre_resume_crash",
        "normal_exit",
        "kill",
        "response_loss",
        "not_started",
        "controller_crash",
    }:
        raise ValidationFailure(
            "execution_safety_fixture_schema", "crash exit kind mismatch"
        )
    if case["same_name_error"]:
        return "close_handle_and_park"
    if case["process_created_suspended"] and not case["execution_committed"]:
        if case["resume_attempted"]:
            return "resume_before_commit_forbidden"
        return "terminate_suspended_record_not_executed"
    if case["execution_committed"] and case["resume_attempted"]:
        if not case["stdout_eof"] or not case["stderr_eof"]:
            return "recovery_pending_eof"
        if case["exit_kind"] in {"normal_exit", "kill", "controller_crash"}:
            return "terminal_eof_observed"
        return "track_exact_process_no_restart"
    return "park_ambiguous_launch"


def _verify_execution_case_matrix(
    fixture: dict[str, Any],
    field: str,
    expected_ids: set[str],
    evaluator: Callable[[dict[str, Any]], str],
) -> int:
    cases = _fixture_cases(fixture, field, expected_ids)
    for case in cases:
        actual = evaluator(case)
        if actual != case.get("expected_result"):
            raise ValidationFailure("fixture_result_mismatch", str(case.get("case_id")))
    return len(cases)


def verify_execution_safety_component(repo_root: Path) -> dict[str, Any]:
    policy, policy_raw = _load_json_object(repo_root / EXECUTION_SAFETY_POLICY_RELATIVE)
    _, job_schema_raw = _load_json_object(repo_root / JOB_IDENTITY_SCHEMA_RELATIVE)
    _, adoption_schema_raw = _load_json_object(
        repo_root / FENCED_ACTION_ADOPTION_SCHEMA_RELATIVE
    )
    fixture, fixture_raw = _load_json_object(repo_root / EXECUTION_SAFETY_FIXTURE_RELATIVE)
    _verify_execution_safety_policy(policy, policy_raw)
    _verify_execution_safety_identity(
        job_schema_raw,
        "job_identity_schema",
        "execution_safety_schema_drift",
        "JobIdentity schema",
    )
    _verify_execution_safety_identity(
        adoption_schema_raw,
        "fenced_action_adoption_schema",
        "execution_safety_schema_drift",
        "FencedActionAdoption schema",
    )
    _verify_execution_safety_identity(
        fixture_raw,
        "fixture",
        "execution_safety_fixture_drift",
        "execution safety fixture",
    )
    fixture = _require_exact_fields(
        fixture,
        {
            "fixture_id",
            "schema_version",
            "policy_path",
            "job_identity_schema_path",
            "fenced_action_adoption_schema_path",
            "job_identity_positive",
            "fenced_action_adoption_positive",
            "writer_identity_cases",
            "process_handle_cases",
            "execution_authority_cases",
            "adoption_cases",
            "crash_window_cases",
        },
        "execution safety fixture",
        reason="execution_safety_fixture_schema",
    )
    if (
        fixture["fixture_id"] != "ExecutionSafetyContractSet.v1.contract-fixtures"
        or type(fixture["schema_version"]) is not int
        or fixture["schema_version"] != 1
        or fixture["policy_path"]
        != str(EXECUTION_SAFETY_POLICY_RELATIVE).replace("\\", "/")
        or fixture["job_identity_schema_path"]
        != str(JOB_IDENTITY_SCHEMA_RELATIVE).replace("\\", "/")
        or fixture["fenced_action_adoption_schema_path"]
        != str(FENCED_ACTION_ADOPTION_SCHEMA_RELATIVE).replace("\\", "/")
    ):
        raise ValidationFailure(
            "execution_safety_fixture_schema", "execution fixture identity mismatch"
        )
    job_identity_id = _validate_job_identity(fixture["job_identity_positive"])
    adoption_hash = _validate_fenced_action_adoption(
        fixture["fenced_action_adoption_positive"]
    )
    counts = {
        "writer_identity": _verify_execution_case_matrix(
            fixture,
            "writer_identity_cases",
            {
                "first_writer_launch",
                "execution_committed_restart",
                "same_attempt_second_launch",
                "prior_suspended_unresolved",
            },
            _evaluate_writer_identity,
        ),
        "process_handle": _verify_execution_case_matrix(
            fixture,
            "process_handle_cases",
            {
                "exact_stdio",
                "missing_create_suspended",
                "missing_job_list",
                "missing_handle_list",
                "inherit_handles_false",
                "startf_missing",
                "duplicate_stdio_role",
                "ambient_extra_handle",
                "parent_child_end_open",
            },
            _evaluate_process_handles,
        ),
        "execution_authority": _verify_execution_case_matrix(
            fixture,
            "execution_authority_cases",
            {
                "writer_active_authorization",
                "controller_inherited_grant",
                "writer_inherited_forbidden",
                "terminate_safety_record",
                "cleanup_safety_forbidden",
                "missing_authority",
            },
            _evaluate_execution_authority,
        ),
        "adoption": _verify_execution_case_matrix(
            fixture,
            "adoption_cases",
            {
                "first_adoption_from_intent",
                "later_adoption_from_adoption",
                "null_prior_head",
                "forked_prior_head",
                "effect_mismatch",
                "authority_mismatch",
                "terminal_action",
            },
            _evaluate_adoption,
        ),
        "crash_window": _verify_execution_case_matrix(
            fixture,
            "crash_window_cases",
            {
                "crash_before_authority_commit",
                "normal_exit_eof",
                "kill_exit_eof",
                "response_lost_after_resume",
                "same_name_job_collision",
                "controller_crash_eof",
                "controller_crash_pipe_not_drained",
            },
            _evaluate_crash_window,
        ),
    }
    return {
        "status": "pass",
        "component": "execution-safety",
        "artifact_version": "ExecutionSafetyContractSet.v1",
        "artifact_byte_count": len(policy_raw),
        "artifact_sha256": hashlib.sha256(policy_raw).hexdigest(),
        "job_identity_fingerprint": job_identity_id,
        "adoption_fingerprint": adoption_hash,
        "fixture_counts": counts,
    }


EVIDENCE_COMMON_EVENT_FIELDS = {
    "schema_version",
    "attempt_uuid",
    "fence",
    "seq",
    "observed_at_utc",
    "event_type",
    "status",
    "prev_hash",
    "event_hash",
}
EVIDENCE_EVENT_PAIRS = [
    ("process_started", "started"),
    ("tool_started", "started"),
    ("mutation_observed", "observed"),
    ("stream_eof", "observed"),
    ("content_validated", "completed"),
    ("tool_completed", "completed"),
    ("turn_completed", "completed"),
    ("final_result", "completed"),
    ("journal_sealed", "completed"),
    ("tool_failed", "failed"),
    ("turn_failed", "failed"),
    ("resource_limit_exceeded", "failed"),
    ("process_terminated", "failed"),
    ("adapter_rejected", "rejected"),
    ("process_exited", "completed"),
    ("process_exited", "failed"),
]
EVIDENCE_EVENT_SPECIFIC_FIELDS = {
    "accepted_end_offset",
    "approved_path_id",
    "bounded_usage",
    "byte_count",
    "canonical_relative_path",
    "configured_limit",
    "content_sha256",
    "exit_code",
    "final_state",
    "framing_class",
    "item_id",
    "job_identity_id",
    "mutation_observation_id",
    "observed_at_least",
    "partial_byte_count",
    "path_class",
    "process_kind",
    "reason_code",
    "report_projection_hash",
    "resource_kind",
    "run_id",
    "segment_no",
    "stream_kind",
    "termination_class",
    "tool_kind",
    "validated_result_projection_hash",
}


def _verify_evidence_identity(
    raw: bytes, identity_key: str, reason: str, label: str
) -> None:
    identity = EXPECTED_EVIDENCE_IDENTITIES[identity_key]
    if (
        len(raw) != identity["byte_count"]
        or hashlib.sha256(raw).hexdigest() != identity["sha256"]
    ):
        raise ValidationFailure(reason, f"{label} identity mismatch")


def _verify_evidence_policy(policy: dict[str, Any], raw: bytes) -> dict[str, Any]:
    canonical = (
        json.dumps(policy, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    _verify_evidence_identity(
        raw, "policy", "evidence_policy_identity", "evidence policy"
    )
    if raw != canonical:
        raise ValidationFailure(
            "evidence_policy_identity", "evidence policy is not canonical"
        )
    envelope = _require_exact_fields(
        policy, {"domain", "payload", "schema_version"}, "evidence policy"
    )
    if (
        envelope["domain"] != "local-ai-runtime/EvidenceContractSet/v1"
        or envelope["schema_version"] != 1
    ):
        raise ValidationFailure("evidence_policy_drift", "policy envelope mismatch")
    payload = _require_exact_fields(
        envelope["payload"],
        {
            "artifact_id",
            "artifact_publish",
            "artifact_version",
            "backup_restore",
            "baseline_id",
            "execution_receipt",
            "external_evidence",
            "journal",
            "normalized_event",
            "output_handling",
            "quarantine_crypto",
            "secret_safe_projection",
        },
        "evidence policy payload",
        reason="evidence_policy_drift",
    )
    normalized = _require_object(
        payload["normalized_event"],
        "normalized event policy",
        reason="evidence_policy_drift",
    )
    projection = _require_object(
        payload["secret_safe_projection"],
        "secret-safe projection policy",
        reason="evidence_policy_drift",
    )
    journal = _require_object(
        payload["journal"], "journal policy", reason="evidence_policy_drift"
    )
    receipt = _require_object(
        payload["execution_receipt"],
        "execution receipt policy",
        reason="evidence_policy_drift",
    )
    artifact = _require_object(
        payload["artifact_publish"],
        "artifact policy",
        reason="evidence_policy_drift",
    )
    crypto = _require_object(
        payload["quarantine_crypto"],
        "quarantine crypto policy",
        reason="evidence_policy_drift",
    )
    external = _require_object(
        payload["external_evidence"],
        "external evidence policy",
        reason="evidence_policy_drift",
    )
    backup = _require_object(
        payload["backup_restore"],
        "backup restore policy",
        reason="evidence_policy_drift",
    )
    key_envelopes = _require_object(
        crypto.get("key_envelopes"),
        "key envelope policy",
        reason="evidence_policy_drift",
    )
    quarantine_key = _require_object(
        key_envelopes.get("quarantine"),
        "quarantine key envelope",
        reason="evidence_policy_drift",
    )
    integrity_key = _require_object(
        key_envelopes.get("runtime_integrity"),
        "runtime integrity key envelope",
        reason="evidence_policy_drift",
    )
    eligibility = _require_object(
        backup.get("eligibility"),
        "backup eligibility policy",
        reason="evidence_policy_drift",
    )
    post_activity = _require_object(
        backup.get("post_activity"),
        "backup post-activity policy",
        reason="evidence_policy_drift",
    )
    production_restore = _require_object(
        backup.get("production_restore"),
        "production restore policy",
        reason="evidence_policy_drift",
    )
    fail_closed = _require_object(
        backup.get("fail_closed"),
        "backup fail-closed policy",
        reason="evidence_policy_drift",
    )
    if (
        payload["artifact_id"] != "P0A-EVIDENCE"
        or payload["artifact_version"] != "EvidenceContractSet.v1"
        or payload["baseline_id"] != BASELINE_SPECIFICATION_ID
        or normalized.get("record_type") != "NormalizedExecutionEvent.v1"
        or normalized.get("event_hash_domain")
        != "local-ai-runtime/NormalizedExecutionEvent/v1"
        or normalized.get("immutable_append_only") is not True
        or normalized.get("optional_null_allowed") is not False
        or projection.get("prior_event_mutation_allowed") is not False
        or projection.get("mutation_pre_scan_fields")
        != [
            "mutation_observation_id",
            "byte_count",
            "path_class",
            "approved_path_id_if_successfully_mapped",
        ]
        or journal.get("append_order")
        != [
            "append_NormalizedExecutionEvent",
            "FlushFileBuffers",
            "short_sqlite_cursor_transaction",
        ]
        or journal.get("cursor_relation")
        != "database_may_lag_flushed_journal_never_lead"
        or journal.get("segment_record_type") != "JournalSegmentManifest.v1"
        or receipt.get("record_type") != "ExecutionReceipt.v1"
        or receipt.get("terminal_conditions")
        != [
            "process_exited",
            "stdout_jsonl_eof",
            "final_schema_passed",
            "no_output_or_resource_overflow",
            "normalized_chain_and_segments_sealed",
            "job_zero_process",
        ]
        or artifact.get("no_replace") is not True
        or artifact.get("replace_api_forbidden") != "os.replace"
        or external.get("evidence_mode") != "runtime_external_v1"
        or external.get("operator_absolute_root_allowed") is not False
        or external.get("repo_fallback_allowed") is not False
        or external.get("task_payload_access") != "deny_read_write"
        or crypto.get("keys_independent") is not True
        or crypto.get("key_plaintext_or_hash_persisted") is not False
        or quarantine_key.get("record_type") != "QuarantineKeyEnvelope.v1"
        or quarantine_key.get("purpose") != "quarantine_encryption"
        or quarantine_key.get("dpapi_scope") != "current_user"
        or integrity_key.get("record_type") != "RuntimeIntegrityKeyEnvelope.v1"
        or integrity_key.get("purpose") != "runtime_integrity_and_backup_wrapper"
        or integrity_key.get("dpapi_scope") != "current_user"
        or eligibility.get("record_type") != "BackupRestoreEligibility.v1"
        or eligibility.get("online_backup_initial_state") != "stale"
        or post_activity.get("record_type") != "BackupPostActivity.v1"
        or production_restore.get("record_type") != "BackupRestoreIntent.v1"
        or production_restore.get("single_intent") is not True
        or production_restore.get("cas_chain")
        != ["eligible", "restoring", "consumed"]
        or production_restore.get("response_loss")
        != "continue_only_same_immutable_intent"
        or fail_closed.get("production_restore_result") != "restore_drill_only"
    ):
        raise ValidationFailure(
            "evidence_policy_drift", "evidence policy boundary mismatch"
        )
    required_fail_closed = {
        "missing_eligibility_sidecar",
        "copied_or_exported_old_backup",
        "post_activity_marker_present",
        "control_generation_drift",
        "manifest_or_envelope_identity_mismatch",
        "owner_sid_or_installation_mismatch",
        "ambiguous_marker_or_head_state",
        "response_loss_with_different_intent",
    }
    if set(fail_closed.get("conditions", [])) != required_fail_closed:
        raise ValidationFailure(
            "evidence_policy_drift", "backup fail-closed set mismatch"
        )
    return payload


def _verify_event_schema_shape(schema: dict[str, Any]) -> None:
    expected_refs = {
        f"#/$defs/{name}"
        for name in (
            "process_started",
            "tool_started",
            "mutation_observed",
            "stream_eof",
            "content_validated",
            "tool_completed",
            "turn_completed",
            "final_result",
            "journal_sealed",
            "tool_failed",
            "turn_failed",
            "resource_limit_exceeded",
            "process_terminated",
            "adapter_rejected",
            "process_exited_completed",
            "process_exited_failed",
        )
    }
    one_of = schema.get("oneOf")
    defs = schema.get("$defs")
    if (
        schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
        or schema.get("title") != "NormalizedExecutionEvent.v1"
        or schema.get("unevaluatedProperties") is not False
        or not isinstance(one_of, list)
        or {item.get("$ref") for item in one_of if isinstance(item, dict)}
        != expected_refs
        or not isinstance(defs, dict)
        or set(defs.get("common", {}).get("required", []))
        != EVIDENCE_COMMON_EVENT_FIELDS
    ):
        raise ValidationFailure(
            "evidence_schema_drift", "normalized event schema boundary mismatch"
        )


def _verify_event_catalog(catalog: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    catalog = _require_exact_fields(
        catalog,
        {
            "catalog_id",
            "schema_version",
            "event_schema_path",
            "common_required_fields",
            "event_specific_field_universe",
            "matrix",
        },
        "event status catalog",
        reason="event_catalog_schema",
    )
    matrix = _require_array(
        catalog["matrix"], "event status matrix", reason="event_catalog_schema"
    )
    if (
        catalog["catalog_id"] != "EventStatusMatrix.v1"
        or catalog["schema_version"] != 1
        or catalog["event_schema_path"]
        != str(NORMALIZED_EVENT_SCHEMA_RELATIVE).replace("\\", "/")
        or set(catalog["common_required_fields"]) != EVIDENCE_COMMON_EVENT_FIELDS
        or set(catalog["event_specific_field_universe"])
        != EVIDENCE_EVENT_SPECIFIC_FIELDS
        or len(matrix) != len(EVIDENCE_EVENT_PAIRS)
    ):
        raise ValidationFailure("event_catalog_drift", "event catalog identity mismatch")
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in matrix:
        entry = _require_exact_fields(
            entry,
            {
                "matrix_id",
                "event_type",
                "status",
                "required_fields",
                "optional_fields",
                "forbidden_fields",
                "conditional_constraints",
            },
            "event status entry",
            reason="event_catalog_schema",
        )
        pair = (entry["event_type"], entry["status"])
        required = set(
            _require_string_array(
                entry["required_fields"],
                "event required fields",
                reason="event_catalog_schema",
            )
        )
        optional = set(
            _require_string_array(
                entry["optional_fields"],
                "event optional fields",
                reason="event_catalog_schema",
            )
        )
        forbidden = set(
            _require_string_array(
                entry["forbidden_fields"],
                "event forbidden fields",
                reason="event_catalog_schema",
            )
        )
        _require_string_array(
            entry["conditional_constraints"],
            "event conditional constraints",
            reason="event_catalog_schema",
        )
        if (
            pair in index
            or entry["matrix_id"] != f"{pair[0]}.{pair[1]}"
            or required & optional
            or required & forbidden
            or optional & forbidden
            or required | optional | forbidden != EVIDENCE_EVENT_SPECIFIC_FIELDS
        ):
            raise ValidationFailure(
                "event_catalog_drift", f"event field partition mismatch: {pair}"
            )
        index[pair] = entry
    if set(index) != set(EVIDENCE_EVENT_PAIRS):
        raise ValidationFailure(
            "event_catalog_drift", "event/status pair set is not exhaustive"
        )
    return index


def _normalized_event_hash(value: dict[str, Any]) -> str:
    payload = dict(value)
    payload.pop("event_hash", None)
    envelope = {
        "domain": "local-ai-runtime/NormalizedExecutionEvent/v1",
        "payload": payload,
        "schema_version": 1,
    }
    raw = (
        json.dumps(envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _validate_normalized_event(
    value: Any,
    catalog: dict[tuple[str, str], dict[str, Any]],
    expected_prev_hash: str,
) -> str:
    if not isinstance(value, dict) or any(item is None for item in value.values()):
        raise ValidationFailure(
            "normalized_event_schema", "event must be a non-null object"
        )
    if not EVIDENCE_COMMON_EVENT_FIELDS <= set(value):
        raise ValidationFailure(
            "normalized_event_schema", "event common fields mismatch"
        )
    pair = (value["event_type"], value["status"])
    entry = catalog.get(pair)
    if entry is None:
        raise ValidationFailure(
            "normalized_event_schema", "event/status pair is not catalogued"
        )
    required = set(entry["required_fields"])
    optional = set(entry["optional_fields"])
    specific = set(value) - EVIDENCE_COMMON_EVENT_FIELDS
    if not required <= specific or not specific <= required | optional:
        raise ValidationFailure(
            "normalized_event_schema", "event-specific fields mismatch"
        )
    timestamp_pattern = re.compile(
        r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$"
    )
    if (
        value["schema_version"] != 1
        or not isinstance(value["attempt_uuid"], str)
        or UUID_V4_PATTERN.fullmatch(value["attempt_uuid"]) is None
        or type(value["fence"]) is not int
        or value["fence"] < 1
        or type(value["seq"]) is not int
        or value["seq"] < 1
        or not isinstance(value["observed_at_utc"], str)
        or timestamp_pattern.fullmatch(value["observed_at_utc"]) is None
        or not _is_sha256(value["prev_hash"])
        or not _is_sha256(value["event_hash"])
        or value["prev_hash"] != expected_prev_hash
    ):
        raise ValidationFailure(
            "normalized_event_schema", "event common value mismatch"
        )
    try:
        datetime.strptime(value["observed_at_utc"], "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as exc:
        raise ValidationFailure(
            "normalized_event_schema", "event timestamp is invalid"
        ) from exc
    if value["event_type"] == "mutation_observed":
        path_classes = {
            "approved_mapped",
            "unknown",
            "denied",
            "out_of_bound",
            "reparse_or_alias",
        }
        approved_path_id = value.get("approved_path_id")
        if (
            not isinstance(value["mutation_observation_id"], str)
            or UUID_V4_PATTERN.fullmatch(value["mutation_observation_id"]) is None
            or type(value["byte_count"]) is not int
            or not 0 <= value["byte_count"] <= 9223372036854775807
            or value["path_class"] not in path_classes
            or (
                approved_path_id is not None
                and (
                    not isinstance(approved_path_id, str)
                    or IDENTIFIER_PATTERN.fullmatch(approved_path_id) is None
                )
            )
        ):
            raise ValidationFailure(
                "normalized_event_schema", "mutation observation value mismatch"
            )
        approved = value["path_class"] == "approved_mapped"
        if approved != ("approved_path_id" in value):
            raise ValidationFailure(
                "pre_scan_projection", "approved path mapping mismatch"
            )
    if value["event_type"] == "final_result":
        blocked = value["final_state"] == "blocked"
        if blocked != ("reason_code" in value):
            raise ValidationFailure(
                "normalized_event_schema", "final result reason mismatch"
            )
    if value["event_type"] == "process_exited":
        if value["status"] == "completed" and (
            value["exit_code"] != 0 or "reason_code" in value
        ):
            raise ValidationFailure(
                "normalized_event_schema", "completed process exit mismatch"
            )
        if value["status"] == "failed" and "reason_code" not in value:
            raise ValidationFailure(
                "normalized_event_schema", "failed process exit reason missing"
            )
    expected_hash = _normalized_event_hash(value)
    if value["event_hash"] != expected_hash:
        raise ValidationFailure(
            "normalized_event_hash", "event hash does not match canonical event"
        )
    return expected_hash


def _evidence_case(
    value: Any, fields: set[str], bool_fields: set[str], label: str
) -> dict[str, Any]:
    case = _require_exact_fields(
        value,
        fields | {"case_id", "expected_result"},
        label,
        reason="evidence_fixture_schema",
    )
    if (
        not isinstance(case["case_id"], str)
        or not isinstance(case["expected_result"], str)
        or not all(isinstance(case[field], bool) for field in bool_fields)
    ):
        raise ValidationFailure(
            "evidence_fixture_schema", f"{label} value mismatch"
        )
    return case


def _evaluate_pre_scan_projection(case: dict[str, Any]) -> str:
    flags = {
        "approved_path_id_present",
        "path_text_present",
        "content_hash_present",
        "ordinary_digest_present",
        "summary_present",
        "free_text_present",
    }
    case = _evidence_case(case, flags | {"path_class"}, flags, "pre-scan case")
    if case["path_class"] not in {
        "approved_mapped",
        "unknown",
        "denied",
        "out_of_bound",
        "reparse_or_alias",
    }:
        raise ValidationFailure("evidence_fixture_schema", "path class mismatch")
    if (
        case["path_text_present"]
        or case["content_hash_present"]
        or case["ordinary_digest_present"]
        or case["summary_present"]
        or case["free_text_present"]
    ):
        return "pre_scan_oracle_forbidden"
    if case["path_class"] != "approved_mapped" and case["approved_path_id_present"]:
        return "approved_path_mapping_forbidden"
    if case["path_class"] == "approved_mapped" and not case["approved_path_id_present"]:
        return "approved_path_mapping_required"
    return "projection_accepted"


def _evaluate_journal_cursor(case: dict[str, Any]) -> str:
    flags = {
        "event_appended",
        "journal_flushed",
        "cursor_advanced",
        "cursor_at_or_before_flushed_offset",
    }
    case = _evidence_case(case, flags, flags, "journal cursor case")
    if case["cursor_advanced"] and (
        not case["event_appended"]
        or not case["journal_flushed"]
        or not case["cursor_at_or_before_flushed_offset"]
    ):
        return "cursor_lead_forbidden"
    if case["journal_flushed"] and not case["cursor_advanced"]:
        return "journal_ahead_recoverable"
    return "cursor_commit_allowed"


def _evaluate_receipt(case: dict[str, Any]) -> str:
    flags = {
        "process_exited",
        "stdout_jsonl_eof",
        "final_schema_passed",
        "no_output_or_resource_overflow",
        "normalized_chain_and_segments_sealed",
        "job_zero_process",
    }
    case = _evidence_case(case, flags, flags, "receipt case")
    return "receipt_publish" if all(case[field] for field in flags) else "receipt_withheld"


def _evaluate_artifact_publish(case: dict[str, Any]) -> str:
    flags = {
        "spool_flushed",
        "intent_durable",
        "destination_exists",
        "same_identity",
        "no_replace_api",
        "readback_matches",
    }
    case = _evidence_case(case, flags, flags, "artifact publish case")
    if not case["no_replace_api"]:
        return "replace_forbidden"
    if not case["spool_flushed"]:
        return "spool_flush_required"
    if not case["intent_durable"]:
        return "intent_required"
    if case["destination_exists"]:
        return "confirm_existing" if case["same_identity"] else "destination_conflict"
    if not case["readback_matches"]:
        return "readback_integrity_failure"
    return "publish_new"


def _evaluate_external_evidence(case: dict[str, Any]) -> str:
    flags = {
        "activation_bound",
        "managed_root_exact",
        "identity_disjoint",
        "no_follow_verified",
        "current_fence",
        "controller_publisher",
        "target_accepts",
        "identity_drift",
    }
    case = _evidence_case(case, flags, flags, "external evidence case")
    if case["identity_drift"]:
        return "requalification_required"
    if not case["activation_bound"] or not case["managed_root_exact"]:
        return "managed_root_required"
    if not case["identity_disjoint"] or not case["no_follow_verified"]:
        return "identity_overlap_forbidden"
    if not case["current_fence"] or not case["controller_publisher"]:
        return "publisher_forbidden"
    if not case["target_accepts"]:
        return "target_contract_required"
    return "publish_allowed"


def _evaluate_key_envelope(case: dict[str, Any]) -> str:
    flags = {
        "domain_matches",
        "plaintext_present",
        "key_hash_present",
        "shares_other_key",
    }
    case = _evidence_case(
        case,
        flags | {"envelope_kind", "purpose", "dpapi_scope"},
        flags,
        "key envelope case",
    )
    purposes = {
        "quarantine": "quarantine_encryption",
        "runtime_integrity": "runtime_integrity_and_backup_wrapper",
    }
    if case["envelope_kind"] not in purposes or not case["domain_matches"]:
        return "envelope_domain_mismatch"
    if case["purpose"] != purposes[case["envelope_kind"]]:
        return "purpose_mismatch"
    if case["dpapi_scope"] != "current_user":
        return "current_user_scope_required"
    if case["plaintext_present"] or case["key_hash_present"]:
        return "key_material_forbidden"
    if case["shares_other_key"]:
        return "independent_keys_required"
    return "envelope_accepted"


def _evaluate_backup_eligibility(case: dict[str, Any]) -> str:
    flags = {
        "already_suspended",
        "control_generation_unchanged",
        "resumed_after_publish",
    }
    case = _evidence_case(case, flags, flags, "backup eligibility case")
    if (
        case["already_suspended"]
        and case["control_generation_unchanged"]
        and not case["resumed_after_publish"]
    ):
        return "eligible"
    return "stale_drill_only"


def _evaluate_post_activity(case: dict[str, Any]) -> str:
    flags = {
        "create_new_write_through",
        "marker_flushed",
        "head_staled",
        "mutation_started",
        "mutation_started_before_marker",
    }
    case = _evidence_case(case, flags, flags, "post-activity case")
    if case["mutation_started_before_marker"]:
        return "ordering_violation"
    marker_complete = (
        case["create_new_write_through"]
        and case["marker_flushed"]
        and case["head_staled"]
    )
    marker_partial = (
        case["create_new_write_through"]
        or case["marker_flushed"]
        or case["head_staled"]
    ) and not marker_complete
    if case["mutation_started"] and not marker_complete:
        return "mutation_forbidden"
    if not case["mutation_started"] and (marker_complete or marker_partial):
        return "conservative_stale"
    return "mutation_allowed"


def _evaluate_restore(case: dict[str, Any]) -> str:
    bool_fields = {
        "sidecar_present",
        "copied_backup",
        "same_suspended_generation",
        "post_activity_present",
        "marker_or_head_ambiguous",
        "identity_matches",
        "intent_present",
        "intent_flushed",
        "intent_unique",
        "expected_head_matches",
        "cas_to_restoring",
        "response_lost",
        "same_intent_replay",
        "cas_to_consumed",
    }
    case = _evidence_case(
        case, bool_fields | {"head_state"}, bool_fields, "restore case"
    )
    if case["head_state"] not in {"eligible", "stale", "restoring", "consumed"}:
        raise ValidationFailure("evidence_fixture_schema", "restore head state mismatch")
    if (
        not case["sidecar_present"]
        or case["copied_backup"]
        or not case["same_suspended_generation"]
        or case["post_activity_present"]
        or case["marker_or_head_ambiguous"]
        or not case["identity_matches"]
    ):
        return "drill_only"
    if case["response_lost"]:
        if not case["intent_unique"] or not case["same_intent_replay"]:
            return "second_restore_forbidden"
        if case["head_state"] == "restoring" and case["intent_flushed"]:
            return "continue_same_intent"
        return "head_conflict_stale"
    if not case["intent_present"] or not case["intent_flushed"]:
        return "restore_intent_not_durable"
    if not case["intent_unique"]:
        return "second_restore_forbidden"
    if (
        case["head_state"] != "eligible"
        or not case["expected_head_matches"]
        or not case["cas_to_restoring"]
    ):
        return "head_conflict_stale"
    return "restore_consumed" if case["cas_to_consumed"] else "restore_incomplete_park"


def _verify_evidence_case_matrix(
    fixture: dict[str, Any],
    field: str,
    expected_ids: set[str],
    evaluator: Callable[[dict[str, Any]], str],
) -> int:
    cases = _fixture_cases(fixture, field, expected_ids)
    for case in cases:
        if evaluator(case) != case.get("expected_result"):
            raise ValidationFailure("fixture_result_mismatch", str(case.get("case_id")))
    return len(cases)


def verify_evidence_component(repo_root: Path) -> dict[str, Any]:
    policy, policy_raw = _load_json_object(repo_root / EVIDENCE_POLICY_RELATIVE)
    event_schema, schema_raw = _load_json_object(
        repo_root / NORMALIZED_EVENT_SCHEMA_RELATIVE
    )
    event_catalog, catalog_raw = _load_json_object(
        repo_root / EVENT_STATUS_CATALOG_RELATIVE
    )
    fixture, fixture_raw = _load_json_object(repo_root / EVIDENCE_FIXTURE_RELATIVE)
    _verify_evidence_policy(policy, policy_raw)
    _verify_evidence_identity(
        schema_raw, "event_schema", "evidence_schema_drift", "event schema"
    )
    _verify_evidence_identity(
        catalog_raw, "event_catalog", "event_catalog_drift", "event catalog"
    )
    _verify_evidence_identity(
        fixture_raw, "fixture", "evidence_fixture_drift", "evidence fixture"
    )
    _verify_event_schema_shape(event_schema)
    catalog = _verify_event_catalog(event_catalog)
    fixture = _require_exact_fields(
        fixture,
        {
            "fixture_id",
            "schema_version",
            "policy_path",
            "event_schema_path",
            "event_catalog_path",
            "event_pair_examples",
            "event_chain_positive",
            "pre_scan_projection_cases",
            "journal_cursor_cases",
            "receipt_cases",
            "artifact_publish_cases",
            "external_evidence_cases",
            "key_envelope_cases",
            "backup_eligibility_cases",
            "post_activity_cases",
            "restore_cases",
        },
        "evidence fixture",
        reason="evidence_fixture_schema",
    )
    if (
        fixture["fixture_id"] != "EvidenceContractSet.v1.contract-fixtures"
        or fixture["schema_version"] != 1
        or fixture["policy_path"]
        != str(EVIDENCE_POLICY_RELATIVE).replace("\\", "/")
        or fixture["event_schema_path"]
        != str(NORMALIZED_EVENT_SCHEMA_RELATIVE).replace("\\", "/")
        or fixture["event_catalog_path"]
        != str(EVENT_STATUS_CATALOG_RELATIVE).replace("\\", "/")
    ):
        raise ValidationFailure(
            "evidence_fixture_schema", "evidence fixture identity mismatch"
        )
    pair_examples = _require_array(
        fixture["event_pair_examples"],
        "event pair examples",
        reason="evidence_fixture_schema",
    )
    observed_pairs: list[tuple[str, str]] = []
    for index, example in enumerate(pair_examples, start=1):
        example = _require_exact_fields(
            example,
            {"event_type", "status", "event_fields"},
            "event pair example",
            reason="evidence_fixture_schema",
        )
        event_fields = _require_object(
            example["event_fields"],
            "event pair fields",
            reason="evidence_fixture_schema",
        )
        event = {
            "schema_version": 1,
            "attempt_uuid": "11111111-1111-4111-8111-111111111111",
            "fence": 3,
            "seq": index,
            "observed_at_utc": f"2026-07-14T02:00:00.{index:06d}Z",
            "event_type": example["event_type"],
            "status": example["status"],
            "prev_hash": "0" * 64,
            "event_hash": "0" * 64,
            **event_fields,
        }
        event["event_hash"] = _normalized_event_hash(event)
        _validate_normalized_event(event, catalog, "0" * 64)
        observed_pairs.append((example["event_type"], example["status"]))
    if observed_pairs != EVIDENCE_EVENT_PAIRS:
        raise ValidationFailure(
            "evidence_fixture_schema", "event pair examples are not exhaustive"
        )
    event_chain = _require_array(
        fixture["event_chain_positive"],
        "event hash chain",
        reason="evidence_fixture_schema",
    )
    previous_hash = "0" * 64
    for index, event in enumerate(event_chain, start=1):
        if not isinstance(event, dict) or event.get("seq") != index:
            raise ValidationFailure(
                "evidence_fixture_schema", "event chain sequence mismatch"
            )
        previous_hash = _validate_normalized_event(event, catalog, previous_hash)
    counts = {
        "event_pair": len(pair_examples),
        "event_chain": len(event_chain),
        "pre_scan": _verify_evidence_case_matrix(
            fixture,
            "pre_scan_projection_cases",
            {
                "approved_mapping",
                "unknown_random_id_only",
                "unknown_with_path",
                "denied_with_digest",
                "unmapped_approved_id",
                "content_hash_before_scan",
                "unknown_with_summary",
                "denied_with_free_text",
            },
            _evaluate_pre_scan_projection,
        ),
        "journal_cursor": _verify_evidence_case_matrix(
            fixture,
            "journal_cursor_cases",
            {
                "flushed_then_cursor",
                "cursor_before_flush",
                "cursor_beyond_flush",
                "journal_may_lead",
            },
            _evaluate_journal_cursor,
        ),
        "receipt": _verify_evidence_case_matrix(
            fixture,
            "receipt_cases",
            {
                "all_terminal",
                "process_running",
                "stdout_not_eof",
                "schema_failed",
                "overflow",
                "journal_unsealed",
                "job_has_process",
            },
            _evaluate_receipt,
        ),
        "artifact_publish": _verify_evidence_case_matrix(
            fixture,
            "artifact_publish_cases",
            {
                "new_destination",
                "response_loss_same_identity",
                "existing_conflict",
                "replace_api",
                "intent_missing",
                "readback_mismatch",
            },
            _evaluate_artifact_publish,
        ),
        "external_evidence": _verify_evidence_case_matrix(
            fixture,
            "external_evidence_cases",
            {
                "managed_controller_publish",
                "operator_root",
                "repo_ancestor_overlap",
                "writer_publish",
                "target_not_accepting",
                "publish_identity_drift",
            },
            _evaluate_external_evidence,
        ),
        "key_envelope": _verify_evidence_case_matrix(
            fixture,
            "key_envelope_cases",
            {
                "quarantine_envelope",
                "integrity_envelope",
                "purpose_mixed",
                "machine_scope",
                "plaintext_persisted",
                "ordinary_key_hash",
                "shared_key",
            },
            _evaluate_key_envelope,
        ),
        "backup_eligibility": _verify_evidence_case_matrix(
            fixture,
            "backup_eligibility_cases",
            {
                "suspended_stable",
                "online_backup",
                "generation_drift",
                "resumed_after_publish",
            },
            _evaluate_backup_eligibility,
        ),
        "post_activity": _verify_evidence_case_matrix(
            fixture,
            "post_activity_cases",
            {
                "marker_before_mutation",
                "mutation_first",
                "marker_not_flushed",
                "marker_only",
                "partial_marker_without_mutation",
            },
            _evaluate_post_activity,
        ),
        "restore": _verify_evidence_case_matrix(
            fixture,
            "restore_cases",
            {
                "single_restore",
                "missing_sidecar",
                "copied_backup",
                "post_activity_marker",
                "generation_drift",
                "intent_not_flushed",
                "response_loss_same_intent",
                "response_loss_second_intent",
                "head_cas_conflict",
                "marker_or_head_ambiguous",
            },
            _evaluate_restore,
        ),
    }
    return {
        "status": "pass",
        "component": "evidence",
        "artifact_version": "EvidenceContractSet.v1",
        "artifact_byte_count": len(policy_raw),
        "artifact_sha256": hashlib.sha256(policy_raw).hexdigest(),
        "event_schema_sha256": hashlib.sha256(schema_raw).hexdigest(),
        "event_catalog_sha256": hashlib.sha256(catalog_raw).hexdigest(),
        "final_event_hash": previous_hash,
        "fixture_counts": counts,
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--inventory-path", type=Path)
    parser.add_argument(
        "--component",
        choices=[
            "manifest",
            "canonicalization",
            "product-submission",
            "qualification",
            "execution-safety",
            "evidence",
            "package",
        ],
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
        elif args.component == "qualification":
            payload = verify_qualification_component(root)
            exit_code = 0
        elif args.component == "execution-safety":
            payload = verify_execution_safety_component(root)
            exit_code = 0
        elif args.component == "evidence":
            payload = verify_evidence_component(root)
            exit_code = 0
        else:
            payload = {
                "status": "incomplete",
                "reason": "standalone_verifier_not_frozen",
                "implemented_components": [
                    "manifest_self_test",
                    "canonicalization",
                    "product_submission",
                    "qualification",
                    "execution_safety",
                    "evidence",
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
