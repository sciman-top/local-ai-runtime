from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import yaml


DERIVED_FIELDS = {
    "planner_required",
    "review_required",
    "touches_policy_surface",
}

REQUIRED_FIELDS = {
    "task_id",
    "title",
    "target_repo",
    "base_branch",
    "branch_name",
    "worktree_path",
    "allowed_paths",
    "forbidden_paths",
    "write_access",
    "risk_level",
    "merge_policy",
    "execution_lane",
    "requires_network",
    "requires_gui",
    "depends_on",
    "artifacts_out",
    "handoff_policy",
    "verification_commands",
}
REQUIRED_VERIFICATION_COMMAND_KEYS = {
    "build",
    "test",
    "lint",
    "typecheck",
    "contract",
    "hotspot",
}
PLANNER_REQUIRED_RISK_LEVELS = {"high", "critical"}
REVIEW_REQUIRED_RISK_LEVELS = {"medium", "high", "critical"}


class CanonicalTaskError(ValueError):
    """Raised when a canonical task payload is invalid."""


@dataclass(frozen=True)
class VerificationCommands:
    build: str | None
    test: str | None
    lint: str | None
    typecheck: str | None
    contract: str | None
    hotspot: str | None


@dataclass(frozen=True)
class CanonicalTask:
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
    execution_lane: str
    requires_network: bool
    requires_gui: bool
    depends_on: tuple[str, ...]
    artifacts_out: tuple[str, ...]
    handoff_policy: str
    verification_commands: VerificationCommands
    user_forced_planner: bool = False
    user_forced_review: bool = False

    @property
    def planner_required(self) -> bool:
        return (
            self.risk_level in PLANNER_REQUIRED_RISK_LEVELS
            or bool(self.depends_on)
            or self.user_forced_planner
        )

    @property
    def review_required(self) -> bool:
        return (
            self.risk_level in REVIEW_REQUIRED_RISK_LEVELS
            or self.write_access
            or self.user_forced_review
        )

    def render_worker_prompt(self) -> str:
        lines = [
            f"task_id: {self.task_id}",
            f"title: {self.title}",
            f"target_repo: {self.target_repo}",
            f"risk_level: {self.risk_level}",
            f"merge_policy: {self.merge_policy}",
            f"execution_lane: {self.execution_lane}",
            "allowed_paths:",
            *[f"  - {item}" for item in self.allowed_paths],
            "forbidden_paths:",
            *[f"  - {item}" for item in self.forbidden_paths],
            "",
            "description:",
            self.description or "(no description provided)",
        ]
        return "\n".join(lines).strip()


def load_task(path: Path) -> CanonicalTask:
    return task_from_payload(path, _load_payload(path))


def task_from_payload(path: Path, payload: dict[str, Any]) -> CanonicalTask:
    if unexpected := [field for field in DERIVED_FIELDS if field in payload]:
        raise CanonicalTaskError(
            "Derived fields must not be authored in canonical task input: " + ", ".join(sorted(unexpected))
        )

    missing = sorted(REQUIRED_FIELDS - payload.keys())
    if missing:
        raise CanonicalTaskError(f"Missing required canonical task fields: {', '.join(missing)}")

    commands_payload = payload.get("verification_commands")
    if not isinstance(commands_payload, dict):
        raise CanonicalTaskError("verification_commands must be a mapping")
    missing_command_keys = sorted(REQUIRED_VERIFICATION_COMMAND_KEYS - commands_payload.keys())
    if missing_command_keys:
        raise CanonicalTaskError(
            "verification_commands is missing required keys: " + ", ".join(missing_command_keys)
        )

    return CanonicalTask(
        path=path,
        task_id=_require_string(payload, "task_id"),
        title=_require_string(payload, "title"),
        description=_optional_string(payload, "description"),
        target_repo=_require_string(payload, "target_repo"),
        base_branch=_require_string(payload, "base_branch"),
        branch_name=_require_string(payload, "branch_name"),
        worktree_path=_require_string(payload, "worktree_path"),
        allowed_paths=tuple(_require_string_list(payload, "allowed_paths")),
        forbidden_paths=tuple(_require_string_list(payload, "forbidden_paths")),
        write_access=_require_bool(payload, "write_access"),
        risk_level=_require_string(payload, "risk_level"),
        merge_policy=_require_string(payload, "merge_policy"),
        execution_lane=_require_string(payload, "execution_lane"),
        requires_network=_require_bool(payload, "requires_network"),
        requires_gui=_require_bool(payload, "requires_gui"),
        user_forced_planner=_optional_force_on(payload, "user_forced_planner"),
        user_forced_review=_optional_force_on(payload, "user_forced_review"),
        depends_on=tuple(_require_string_list(payload, "depends_on")),
        artifacts_out=tuple(_require_string_list(payload, "artifacts_out")),
        handoff_policy=_require_string(payload, "handoff_policy"),
        verification_commands=VerificationCommands(
            build=_optional_command(commands_payload, "build"),
            test=_optional_command(commands_payload, "test"),
            lint=_optional_command(commands_payload, "lint"),
            typecheck=_optional_command(commands_payload, "typecheck"),
            contract=_optional_command(commands_payload, "contract"),
            hotspot=_optional_command(commands_payload, "hotspot"),
        ),
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
    raise CanonicalTaskError(f"Unsupported canonical task file type: {path}")


def _load_payload(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        payload = json.loads(text)
    elif suffix in {".yaml", ".yml"}:
        payload = yaml.safe_load(text)
    else:
        raise CanonicalTaskError(f"Unsupported canonical task file type: {path}")
    if not isinstance(payload, dict):
        raise CanonicalTaskError(f"Canonical task must be an object: {path}")
    return payload


def _require_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CanonicalTaskError(f"{key} must be a non-empty string")
    return value.strip()


def _optional_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if value is None:
        return ""
    if not isinstance(value, str):
        raise CanonicalTaskError(f"{key} must be a string when present")
    return value.strip()


def _require_string_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise CanonicalTaskError(f"{key} must be a list of strings")
    return [item.strip() for item in value]


def _require_bool(payload: dict[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise CanonicalTaskError(f"{key} must be a boolean")
    return value


def _optional_command(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise CanonicalTaskError(f"verification_commands.{key} must be a string or null")
    stripped = value.strip()
    return stripped or None


def _optional_force_on(payload: dict[str, Any], key: str) -> bool:
    if key not in payload:
        return False

    value = payload.get(key)
    if not isinstance(value, bool):
        raise CanonicalTaskError(f"{key} must be a boolean when present")
    if value is not True:
        raise CanonicalTaskError(f"{key} only allows true when present; omit the field instead")
    return True
