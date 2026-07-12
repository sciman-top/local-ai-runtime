from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = (
    ROOT / "docs" / "specs" / "local-ai-runtime-0.2" / "history"
)
SESSION_ID = "019f5081-9022-7681-9378-fa14e695131b"
SESSION_BASENAME = (
    "rollout-2026-07-11T17-28-21-019f5081-9022-7681-9378-fa14e695131b.jsonl"
)
V318_TITLE = (
    "# Local AI Runtime 0.2 v3.18：Unified Native + Batch Deterministic "
    "Minimum-Operator Implementation Baseline Candidate"
)


@dataclass(frozen=True)
class SourceSpec:
    archive_id: str
    output_name: str
    jsonl_line: int
    role: Literal["assistant", "user"]
    content_type: Literal["output_text", "input_text"]
    extraction: Literal["unwrap_proposed_plan", "from_unique_title"]
    expected_byte_count: int
    expected_sha256: str


SOURCE_SPECS = (
    SourceSpec(
        archive_id="local-ai-runtime-0.2-v3.17",
        output_name="local-ai-runtime-0.2-v3.17.md",
        jsonl_line=7409,
        role="assistant",
        content_type="output_text",
        extraction="unwrap_proposed_plan",
        expected_byte_count=32825,
        expected_sha256=(
            "a285f5f421a8ccd4debd8794609a2aa0eb07bb1bf651c2467a95f7cad25a5f81"
        ),
    ),
    SourceSpec(
        archive_id="local-ai-runtime-0.2-v3.18-a",
        output_name="local-ai-runtime-0.2-v3.18-a.md",
        jsonl_line=8408,
        role="assistant",
        content_type="output_text",
        extraction="unwrap_proposed_plan",
        expected_byte_count=66328,
        expected_sha256=(
            "6924ba562dda8e69274eb80fef9e3a9699eb493570ee08330fcad5ec4bc3baa5"
        ),
    ),
    SourceSpec(
        archive_id="local-ai-runtime-0.2-v3.18-b",
        output_name="local-ai-runtime-0.2-v3.18-b.md",
        jsonl_line=8429,
        role="user",
        content_type="input_text",
        extraction="from_unique_title",
        expected_byte_count=43908,
        expected_sha256=(
            "8da5aa20fb44d95503e443822163397a2aa1df590e1916d1a5a10a6c24ea06b7"
        ),
    ),
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Archive exact Local AI Runtime historical candidate message bodies."
    )
    parser.add_argument("--session-path", required=True)
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify existing archives and the source boundaries without creating files.",
    )
    args = parser.parse_args()

    try:
        result = extract_history(
            session_path=Path(args.session_path),
            output_root=Path(args.output_root),
            verify_only=args.verify_only,
        )
    except (OSError, UnicodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def extract_history(
    *, session_path: Path, output_root: Path, verify_only: bool
) -> dict[str, Any]:
    if session_path.name != SESSION_BASENAME:
        raise ValueError(
            f"session basename must be {SESSION_BASENAME}, got {session_path.name}"
        )

    requested_lines = {spec.jsonl_line for spec in SOURCE_SPECS}
    records = _read_jsonl_lines(session_path, requested_lines)
    if set(records) != requested_lines:
        missing = sorted(requested_lines - set(records))
        raise ValueError(f"source session is missing required JSONL lines: {missing}")

    archives: list[dict[str, Any]] = []
    extracted: list[tuple[SourceSpec, bytes]] = []
    for spec in SOURCE_SPECS:
        body, source = _extract_body(records[spec.jsonl_line], spec)
        raw = body.encode("utf-8", errors="strict")
        _validate_normative_bytes(raw, spec.archive_id)
        actual_hash = hashlib.sha256(raw).hexdigest()
        if len(raw) != spec.expected_byte_count:
            raise ValueError(
                f"{spec.archive_id} byte count mismatch: "
                f"expected {spec.expected_byte_count}, got {len(raw)}"
            )
        if actual_hash != spec.expected_sha256:
            raise ValueError(
                f"{spec.archive_id} SHA-256 mismatch: "
                f"expected {spec.expected_sha256}, got {actual_hash}"
            )
        extracted.append((spec, raw))
        archives.append(
            {
                "archive_id": spec.archive_id,
                "path": f"docs/specs/local-ai-runtime-0.2/history/{spec.output_name}",
                "byte_count": len(raw),
                "sha256": actual_hash,
                "source": source,
            }
        )

    record = {
        "schema_version": "HistoricalSourceArchive.v1",
        "record_kind": "exact_message_content_archive",
        "normative": False,
        "session_id": SESSION_ID,
        "session_basename": SESSION_BASENAME,
        "byte_policy": "SpecificationBytePolicy.v1",
        "required_independent_hash_methods": [
            "python_hashlib_sha256",
            "powershell_get_file_hash_sha256",
        ],
        "archives": archives,
        "invariants": [
            "No encoding, newline, Unicode, whitespace or Markdown normalization is permitted.",
            "The original session remains read-only and is not copied into the repository.",
            "Existing archive paths are verified byte-for-byte and never overwritten.",
            "This record is source provenance, not BaselineLineage.v1 or Baseline Approval.",
        ],
    }
    record_raw = (
        json.dumps(record, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")

    output_root.mkdir(parents=True, exist_ok=True)
    for spec, raw in extracted:
        _publish_or_verify(output_root / spec.output_name, raw, verify_only)
    _publish_or_verify(
        output_root / "HistoricalSourceArchive.v1.json", record_raw, verify_only
    )

    return {
        "status": "pass",
        "mode": "verify_only" if verify_only else "publish_or_verify",
        "record_path": str(
            (output_root / "HistoricalSourceArchive.v1.json").resolve()
        ),
        "archives": [
            {
                "archive_id": item["archive_id"],
                "byte_count": item["byte_count"],
                "sha256": item["sha256"],
            }
            for item in archives
        ],
    }


def _read_jsonl_lines(path: Path, requested: set[int]) -> dict[int, dict[str, Any]]:
    records: dict[int, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8", errors="strict", newline="") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line_no not in requested:
                continue
            try:
                value = json.loads(line, object_pairs_hook=_reject_duplicate_keys)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at source line {line_no}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"source line {line_no} must contain a JSON object")
            records[line_no] = value
            if len(records) == len(requested):
                break
    return records


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"source JSON contains duplicate key: {key!r}")
        result[key] = value
    return result


def _extract_body(
    record: dict[str, Any], spec: SourceSpec
) -> tuple[str, dict[str, Any]]:
    if record.get("type") != "response_item":
        raise ValueError(f"source line {spec.jsonl_line} must be response_item")
    payload = record.get("payload")
    if not isinstance(payload, dict) or payload.get("type") != "message":
        raise ValueError(f"source line {spec.jsonl_line} must contain a message payload")
    if payload.get("role") != spec.role:
        raise ValueError(
            f"source line {spec.jsonl_line} role must be {spec.role!r}"
        )
    content = payload.get("content")
    if not isinstance(content, list) or len(content) != 1:
        raise ValueError(
            f"source line {spec.jsonl_line} must contain exactly one content item"
        )
    item = content[0]
    if not isinstance(item, dict) or item.get("type") != spec.content_type:
        raise ValueError(
            f"source line {spec.jsonl_line} content type must be {spec.content_type!r}"
        )
    text = item.get("text")
    if not isinstance(text, str):
        raise ValueError(f"source line {spec.jsonl_line} content text must be a string")

    excluded_prefix: str
    excluded_suffix: str
    if spec.extraction == "unwrap_proposed_plan":
        excluded_prefix = "<proposed_plan>\n"
        excluded_suffix = "</proposed_plan>"
        if not text.startswith(excluded_prefix) or not text.endswith(excluded_suffix):
            raise ValueError(
                f"source line {spec.jsonl_line} does not match the exact plan envelope"
            )
        body = text[len(excluded_prefix) : -len(excluded_suffix)]
    else:
        if text.count(V318_TITLE) != 1:
            raise ValueError(
                f"source line {spec.jsonl_line} must contain exactly one v3.18 title"
            )
        title_index = text.index(V318_TITLE)
        excluded_prefix = text[:title_index]
        excluded_suffix = ""
        if excluded_prefix != (
            "这是对方的新方案，是否有值得吸收/参考的？并生成新的完整/自包含方案。：\n"
        ):
            raise ValueError(
                f"source line {spec.jsonl_line} has an unexpected pre-title prefix"
            )
        body = text[title_index:]

    source = {
        "jsonl_line": spec.jsonl_line,
        "outer_record_type": "response_item",
        "payload_type": "message",
        "role": spec.role,
        "content_index": 0,
        "content_type": spec.content_type,
        "text_field": "payload.content[0].text",
        "extraction": spec.extraction,
        "excluded_prefix_utf8_bytes": len(excluded_prefix.encode("utf-8")),
        "excluded_suffix_utf8_bytes": len(excluded_suffix.encode("utf-8")),
    }
    return body, source


def _validate_normative_bytes(raw: bytes, label: str) -> None:
    failures: list[str] = []
    if raw.startswith(b"\xef\xbb\xbf"):
        failures.append("UTF-8 BOM")
    if b"\r" in raw:
        failures.append("CR")
    if b"\x00" in raw:
        failures.append("NUL")
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        failures.append("not exactly one terminal LF")
    text = raw.decode("utf-8", errors="strict")
    if text != unicodedata.normalize("NFC", text):
        failures.append("non-NFC text")
    if any(line.endswith((" ", "\t")) for line in text.split("\n")):
        failures.append("trailing SP/HTAB")
    if any(
        character != "\n" and unicodedata.category(character) in {"Cc", "Cf"}
        for character in text
    ):
        failures.append("disallowed Cc/Cf character")
    if any(unicodedata.category(character) in {"Zl", "Zp"} for character in text):
        failures.append("Unicode line/paragraph separator")
    if any(_is_unicode_noncharacter(ord(character)) for character in text):
        failures.append("Unicode noncharacter")
    if failures:
        raise ValueError(f"{label} violates SpecificationBytePolicy.v1: {failures}")


def _is_unicode_noncharacter(value: int) -> bool:
    return 0xFDD0 <= value <= 0xFDEF or value & 0xFFFF in {0xFFFE, 0xFFFF}


def _publish_or_verify(path: Path, raw: bytes, verify_only: bool) -> None:
    if path.exists():
        if not path.is_file() or path.read_bytes() != raw:
            raise ValueError(f"existing archive differs and will not be overwritten: {path}")
        return
    if verify_only:
        raise ValueError(f"required archive does not exist: {path}")

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            path.unlink(missing_ok=True)
        finally:
            raise


if __name__ == "__main__":
    raise SystemExit(main())
