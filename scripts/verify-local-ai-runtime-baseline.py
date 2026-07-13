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
            raise ValidationFailure("duplicate_json_key", f"duplicate JSON key: {key}")
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
    except json.JSONDecodeError as exc:
        raise ValidationFailure("invalid_json", f"invalid JSON in {path}: {exc.msg}") from exc
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


def _require_exact_fields(value: Any, required: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationFailure("schema_violation", f"{label} must be an object")
    actual = set(value)
    if actual != required:
        unknown = sorted(actual - required)
        missing = sorted(required - actual)
        reason = "unknown_payload_field" if label == "payload" and unknown else "schema_violation"
        raise ValidationFailure(
            reason, f"{label} fields mismatch: missing={missing}, unknown={unknown}"
        )
    return value


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


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


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--inventory-path", type=Path)
    parser.add_argument("--component", choices=["manifest", "canonicalization", "package"])
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
        else:
            payload = {
                "status": "incomplete",
                "reason": "standalone_verifier_not_frozen",
                "implemented_components": ["manifest_self_test"],
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
