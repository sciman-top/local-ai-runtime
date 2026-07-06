from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from openai_codex import ApprovalMode, Sandbox


class RuntimeConfigError(ValueError):
    """Raised when repo-owned runtime config is missing or invalid."""


@dataclass(frozen=True)
class WorkerProfile:
    name: str
    worker_kind: str
    lane: str
    model: str
    provider: str
    sandbox_profile: str
    approval_policy: str
    network_profile: str
    projection_mode: str

    def sandbox(self) -> Sandbox:
        if self.sandbox_profile == "workspace_write":
            return Sandbox.workspace_write
        if self.sandbox_profile == "read_only":
            return Sandbox.read_only
        if self.sandbox_profile == "danger_full_access":
            return Sandbox.danger_full_access
        raise RuntimeConfigError(f"Unsupported sandbox_profile: {self.sandbox_profile}")

    def approval_mode(self) -> ApprovalMode:
        if self.approval_policy == "never":
            return ApprovalMode.deny_all
        if self.approval_policy == "on_request":
            return ApprovalMode.auto_review
        raise RuntimeConfigError(f"Unsupported approval_policy: {self.approval_policy}")


@dataclass(frozen=True)
class OrchestratorSettings:
    default_worker_profile: str
    run_id_prefix: str
    projection_required: bool


@dataclass(frozen=True)
class PolicySettings:
    policy_surface_globs: tuple[str, ...]
    sensitive_paths: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeConfigBundle:
    repo_root: Path
    orchestrator: OrchestratorSettings
    policies: PolicySettings
    workers: dict[str, WorkerProfile]

    def worker_profile(self, name: str | None = None) -> WorkerProfile:
        profile_name = name or self.orchestrator.default_worker_profile
        try:
            return self.workers[profile_name]
        except KeyError as exc:
            raise RuntimeConfigError(f"Unknown worker profile: {profile_name}") from exc


def load_runtime_config(repo_root: Path) -> RuntimeConfigBundle:
    config_root = repo_root / ".ai" / "config"
    if not config_root.exists():
        raise RuntimeConfigError(
            "Missing repo-owned runtime config directory: "
            f"{config_root}. Expected .ai/config/orchestrator.yaml, workers.yaml, and policies.yaml."
        )

    orchestrator_payload = _load_yaml_file(config_root / "orchestrator.yaml")
    workers_payload = _load_yaml_file(config_root / "workers.yaml")
    policies_payload = _load_yaml_file(config_root / "policies.yaml")

    run_payload = _require_mapping(orchestrator_payload, "run", "orchestrator.yaml")
    acceptance_payload = _optional_mapping(orchestrator_payload.get("acceptance"), "acceptance", "orchestrator.yaml")
    worker_map = _require_mapping(workers_payload, "workers", "workers.yaml")

    workers: dict[str, WorkerProfile] = {}
    for name, raw in worker_map.items():
        if not isinstance(name, str):
            raise RuntimeConfigError("workers.yaml keys must be strings")
        values = _require_mapping({"entry": raw}, "entry", "workers.yaml")
        workers[name] = WorkerProfile(
            name=name,
            worker_kind=_require_string(values, "worker_kind", "workers.yaml"),
            lane=_require_string(values, "lane", "workers.yaml"),
            model=_require_string(values, "model", "workers.yaml"),
            provider=_require_string(values, "provider", "workers.yaml"),
            sandbox_profile=_require_string(values, "sandbox_profile", "workers.yaml"),
            approval_policy=_require_string(values, "approval_policy", "workers.yaml"),
            network_profile=_require_string(values, "network_profile", "workers.yaml"),
            projection_mode=_require_string(values, "projection_mode", "workers.yaml"),
        )

    default_worker_profile = _require_string(run_payload, "default_worker_profile", "orchestrator.yaml")
    if default_worker_profile not in workers:
        raise RuntimeConfigError(
            "orchestrator.yaml:run.default_worker_profile must reference a defined worker profile"
        )

    return RuntimeConfigBundle(
        repo_root=repo_root,
        orchestrator=OrchestratorSettings(
            default_worker_profile=default_worker_profile,
            run_id_prefix=_require_string(run_payload, "run_id_prefix", "orchestrator.yaml"),
            projection_required=bool(acceptance_payload.get("projection_required", True)),
        ),
        policies=PolicySettings(
            policy_surface_globs=tuple(_require_string_list(policies_payload, "policy_surface_globs", "policies.yaml")),
            sensitive_paths=tuple(_require_string_list(policies_payload, "sensitive_paths", "policies.yaml")),
        ),
        workers=workers,
    )


def _load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeConfigError(f"Missing runtime config file: {path}")
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RuntimeConfigError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeConfigError(f"Runtime config file must contain a mapping: {path}")
    return payload


def _require_mapping(payload: dict[str, Any], key: str, source_name: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise RuntimeConfigError(f"{source_name}:{key} must be a mapping")
    return value


def _optional_mapping(value: Any, key: str, source_name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise RuntimeConfigError(f"{source_name}:{key} must be a mapping when present")
    return value


def _require_string(payload: dict[str, Any], key: str, source_name: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeConfigError(f"{source_name}:{key} must be a non-empty string")
    return value.strip()


def _require_string_list(payload: dict[str, Any], key: str, source_name: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RuntimeConfigError(f"{source_name}:{key} must be a list of strings")
    return [item.strip() for item in value if item.strip()]
