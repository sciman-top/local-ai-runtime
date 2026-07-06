from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ArtifactDigest:
    relative_path: str
    sha256: str
    byte_count: int


@dataclass(frozen=True)
class EvidenceValidationEntry:
    relative_path: str
    expected_sha256: str
    actual_sha256: str | None
    expected_byte_count: int
    actual_byte_count: int | None
    status: str


@dataclass(frozen=True)
class EvidenceIndexValidationResult:
    evidence_index_path: str
    task_id: str | None
    run_id: str | None
    ok: bool
    checked_entry_count: int
    issue_count: int
    issues: list[str]
    entries: list[EvidenceValidationEntry]

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_index_path": self.evidence_index_path,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "ok": self.ok,
            "checked_entry_count": self.checked_entry_count,
            "issue_count": self.issue_count,
            "issues": list(self.issues),
            "entries": [asdict(entry) for entry in self.entries],
        }


def build_evidence_index_payload(
    *,
    repo_root: Path,
    task_id: str,
    run_id: str,
    indexed_paths: list[Path],
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "run_id": run_id,
        "entries": [asdict(digest_file(repo_root, path)) for path in indexed_paths],
    }


def digest_file(repo_root: Path, path: Path) -> ArtifactDigest:
    payload = path.read_bytes()
    return ArtifactDigest(
        relative_path=render_relative_path(repo_root, path),
        sha256=hashlib.sha256(payload).hexdigest(),
        byte_count=len(payload),
    )


def render_relative_path(repo_root: Path, path: Path) -> str:
    return str(path.relative_to(repo_root)).replace("\\", "/")


def revalidate_evidence_index(
    *,
    repo_root: Path,
    evidence_index_path: Path,
) -> EvidenceIndexValidationResult:
    payload = load_evidence_index_payload(evidence_index_path)
    entries_payload = payload["entries"]

    issues: list[str] = []
    validation_entries: list[EvidenceValidationEntry] = []
    seen_paths: set[str] = set()

    for index, raw_entry in enumerate(entries_payload):
        entry_prefix = f"entries[{index}]"
        if not isinstance(raw_entry, dict):
            issues.append(f"{entry_prefix} must be an object")
            continue

        relative_path = raw_entry.get("relative_path")
        expected_sha256 = raw_entry.get("sha256")
        expected_byte_count = raw_entry.get("byte_count")

        if not isinstance(relative_path, str) or not relative_path.strip():
            issues.append(f"{entry_prefix}.relative_path must be a non-empty string")
            continue
        if not isinstance(expected_sha256, str) or not expected_sha256.strip():
            issues.append(f"{entry_prefix}.sha256 must be a non-empty string")
            continue
        if not isinstance(expected_byte_count, int) or expected_byte_count < 0:
            issues.append(f"{entry_prefix}.byte_count must be a non-negative integer")
            continue

        normalized_relative_path = _normalize_relative_path(relative_path)
        if normalized_relative_path in seen_paths:
            issues.append(f"duplicate evidence entry: {normalized_relative_path}")
        else:
            seen_paths.add(normalized_relative_path)

        target_path = repo_root / Path(normalized_relative_path)
        if not target_path.exists():
            issues.append(f"missing artifact: {normalized_relative_path}")
            validation_entries.append(
                EvidenceValidationEntry(
                    relative_path=normalized_relative_path,
                    expected_sha256=expected_sha256,
                    actual_sha256=None,
                    expected_byte_count=expected_byte_count,
                    actual_byte_count=None,
                    status="missing",
                )
            )
            continue

        actual_digest = digest_file(repo_root, target_path)
        status = "ok"
        if actual_digest.byte_count != expected_byte_count and actual_digest.sha256 != expected_sha256:
            status = "sha256_and_byte_count_mismatch"
            issues.append(
                f"digest mismatch: {normalized_relative_path} "
                f"(expected sha256={expected_sha256}, actual sha256={actual_digest.sha256}, "
                f"expected bytes={expected_byte_count}, actual bytes={actual_digest.byte_count})"
            )
        elif actual_digest.byte_count != expected_byte_count:
            status = "byte_count_mismatch"
            issues.append(
                f"byte_count mismatch: {normalized_relative_path} "
                f"(expected {expected_byte_count}, actual {actual_digest.byte_count})"
            )
        elif actual_digest.sha256 != expected_sha256:
            status = "sha256_mismatch"
            issues.append(
                f"sha256 mismatch: {normalized_relative_path} "
                f"(expected {expected_sha256}, actual {actual_digest.sha256})"
            )

        validation_entries.append(
            EvidenceValidationEntry(
                relative_path=normalized_relative_path,
                expected_sha256=expected_sha256,
                actual_sha256=actual_digest.sha256,
                expected_byte_count=expected_byte_count,
                actual_byte_count=actual_digest.byte_count,
                status=status,
            )
        )

    return EvidenceIndexValidationResult(
        evidence_index_path=render_relative_path(repo_root, evidence_index_path),
        task_id=_read_optional_string(payload, "task_id"),
        run_id=_read_optional_string(payload, "run_id"),
        ok=not issues,
        checked_entry_count=len(validation_entries),
        issue_count=len(issues),
        issues=issues,
        entries=validation_entries,
    )


def load_evidence_index_payload(evidence_index_path: Path) -> dict[str, Any]:
    try:
        text = evidence_index_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Evidence index is not readable: {evidence_index_path} ({exc})") from exc

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Evidence index is invalid JSON: {evidence_index_path} ({exc.msg})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"Evidence index must be a JSON object: {evidence_index_path}")

    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError(f"Evidence index entries must be an array: {evidence_index_path}")

    return payload


def _normalize_relative_path(relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/").strip()
    candidate = Path(normalized)
    if candidate.is_absolute():
        raise ValueError(f"Evidence index relative_path must stay repo-relative: {relative_path}")
    if any(part == ".." for part in candidate.parts):
        raise ValueError(f"Evidence index relative_path cannot traverse upward: {relative_path}")
    return normalized


def _read_optional_string(payload: dict[str, Any], field_name: str) -> str | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Evidence index field must be a string when present: {field_name}")
    return value
