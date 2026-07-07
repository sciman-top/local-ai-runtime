from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import yaml


REQUIRED_FIELDS = {
    "task_id",
    "title",
    "description",
    "target_repo",
    "base_branch",
    "branch_name",
    "worktree_path",
    "allowed_paths",
    "forbidden_paths",
    "write_access",
    "risk_level",
    "merge_policy",
    "requires_network",
    "requires_gui",
    "dependency_refs",
    "artifacts_out",
    "verification_profile",
    "continuation_policy",
}

FORBIDDEN_LEGACY_FIELDS = {
    "depends_on",
    "verification_commands",
    "handoff_policy",
    "planner_required",
    "review_required",
    "touches_policy_surface",
}


class RuntimeV2TaskError(ValueError):
    """Raised when a v2 canonical task payload is invalid."""


@dataclass(frozen=True)
class RuntimeV2Task:
    path: Path
    task_id: str
    title: str
    description: str
    target_repo: str
    base_branch: str
    branch_name: str
    worktree_path: str
    allowed_paths: tuple[str, ...]
    forbidden_paths: tuple[str, ...]
    write_access: bool
    risk_level: str
    merge_policy: str
    requires_network: bool
    requires_gui: bool
    dependency_refs: tuple[str, ...]
    artifacts_out: tuple[str, ...]
    verification_profile: str
    continuation_policy: str
    worker_profile: str | None = None

    def render_worker_prompt(self) -> str:
        lines = [
            f"task_id: {self.task_id}",
            f"title: {self.title}",
            f"target_repo: {self.target_repo}",
            f"risk_level: {self.risk_level}",
            f"verification_profile: {self.verification_profile}",
            f"continuation_policy: {self.continuation_policy}",
            f"write_access: {str(self.write_access).lower()}",
        ]
        if self.worker_profile is not None:
            lines.append(f"worker_profile: {self.worker_profile}")
        if self.dependency_refs:
            lines.append("dependency_refs:")
            lines.extend(f"  - {item}" for item in self.dependency_refs)
        lines.extend(
            [
                "allowed_paths:",
                *[f"  - {item}" for item in self.allowed_paths],
                "forbidden_paths:",
                *[f"  - {item}" for item in self.forbidden_paths],
                "",
                "description:",
                self.description,
            ]
        )
        return "\n".join(lines).strip()


def load_task(path: Path) -> RuntimeV2Task:
    return task_from_payload(path, _load_payload(path))


def task_from_payload(path: Path, payload: dict[str, Any]) -> RuntimeV2Task:
    authored_legacy = sorted(field for field in FORBIDDEN_LEGACY_FIELDS if field in payload)
    if authored_legacy:
        raise RuntimeV2TaskError(
            "v2 canonical task must not author legacy/derived fields: "
            + ", ".join(authored_legacy)
        )

    missing = sorted(REQUIRED_FIELDS - payload.keys())
    if missing:
        raise RuntimeV2TaskError(
            "Missing required v2 canonical task fields: " + ", ".join(missing)
        )

    return RuntimeV2Task(
        path=path,
        task_id=_require_string(payload, "task_id"),
        title=_require_string(payload, "title"),
        description=_require_string(payload, "description"),
        target_repo=_require_string(payload, "target_repo"),
        base_branch=_require_string(payload, "base_branch"),
        branch_name=_require_string(payload, "branch_name"),
        worktree_path=_require_string(payload, "worktree_path"),
        allowed_paths=tuple(_require_string_list(payload, "allowed_paths")),
        forbidden_paths=tuple(_require_string_list(payload, "forbidden_paths")),
        write_access=_require_bool(payload, "write_access"),
        risk_level=_require_string(payload, "risk_level"),
        merge_policy=_require_string(payload, "merge_policy"),
        requires_network=_require_bool(payload, "requires_network"),
        requires_gui=_require_bool(payload, "requires_gui"),
        dependency_refs=tuple(_require_string_list(payload, "dependency_refs")),
        artifacts_out=tuple(_require_string_list(payload, "artifacts_out")),
        verification_profile=_require_string(payload, "verification_profile"),
        continuation_policy=_require_string(payload, "continuation_policy"),
        worker_profile=_optional_string(payload, "worker_profile"),
    )


def write_task(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix == ".json":
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path
    if suffix in {".yaml", ".yml"}:
        path.write_text(
            yaml.safe_dump(payload, allow_unicode=False, sort_keys=False),
            encoding="utf-8",
        )
        return path
    raise RuntimeV2TaskError(f"Unsupported v2 canonical task file type: {path}")


def _load_payload(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        payload = json.loads(text)
    elif suffix in {".yaml", ".yml"}:
        payload = yaml.safe_load(text)
    else:
        raise RuntimeV2TaskError(f"Unsupported v2 canonical task file type: {path}")
    if not isinstance(payload, dict):
        raise RuntimeV2TaskError(f"v2 canonical task must be an object: {path}")
    return payload


def _require_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeV2TaskError(f"{key} must be a non-empty string")
    return value.strip()


def _optional_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise RuntimeV2TaskError(f"{key} must be a non-empty string when present")
    return value.strip()


def _require_string_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RuntimeV2TaskError(f"{key} must be a list of strings")
    return [item.strip() for item in value if item.strip()]


def _require_bool(payload: dict[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise RuntimeV2TaskError(f"{key} must be a boolean")
    return value
