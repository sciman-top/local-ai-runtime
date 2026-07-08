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
    max_active_leases: int
    runner_wired: bool = False
    runner_acceptance_ref: str | None = None

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
    review_worker_profile: str | None
    run_id_prefix: str
    projection_required: bool


@dataclass(frozen=True)
class RuntimeSettings:
    active_version: str
    experimental_v2_enabled: bool
    control_plane_db_v2: str
    artifact_root_v2: str


@dataclass(frozen=True)
class VerificationProfile:
    name: str
    build: str | None
    lint: str | None
    typecheck: str | None
    test: str | None
    contract: str | None
    hotspot: str | None


@dataclass(frozen=True)
class ContinuationPolicy:
    name: str
    auto_continue: bool
    review_on_risk_levels: tuple[str, ...]
    pause_on_policy_surface: bool
    pause_on_verification_failure: bool


@dataclass(frozen=True)
class RetryPolicy:
    name: str
    retry_on_gate_failure: bool
    retry_on_worker_failure: bool
    max_attempts: int


@dataclass(frozen=True)
class PolicySettings:
    policy_surface_globs: tuple[str, ...]
    sensitive_paths: tuple[str, ...]
    verification_profiles: dict[str, VerificationProfile]
    continuation_policies: dict[str, ContinuationPolicy]
    retry_policies: dict[str, RetryPolicy]


@dataclass(frozen=True)
class RuntimeConfigBundle:
    repo_root: Path
    orchestrator: OrchestratorSettings
    runtime: RuntimeSettings
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
    runtime_payload = _optional_mapping(orchestrator_payload.get("runtime"), "runtime", "orchestrator.yaml")
    acceptance_payload = _optional_mapping(orchestrator_payload.get("acceptance"), "acceptance", "orchestrator.yaml")
    worker_map = _require_mapping(workers_payload, "workers", "workers.yaml")
    verification_profiles_payload = _optional_mapping(
        policies_payload.get("verification_profiles"),
        "verification_profiles",
        "policies.yaml",
    )
    continuation_policies_payload = _optional_mapping(
        policies_payload.get("continuation_policies"),
        "continuation_policies",
        "policies.yaml",
    )
    retry_policies_payload = _optional_mapping(
        policies_payload.get("retry_policies"),
        "retry_policies",
        "policies.yaml",
    )

    workers: dict[str, WorkerProfile] = {}
    for name, raw in worker_map.items():
        if not isinstance(name, str):
            raise RuntimeConfigError("workers.yaml keys must be strings")
        values = _require_mapping({"entry": raw}, "entry", "workers.yaml")
        worker_profile = WorkerProfile(
            name=name,
            worker_kind=_require_string(values, "worker_kind", "workers.yaml"),
            lane=_require_string(values, "lane", "workers.yaml"),
            model=_require_string(values, "model", "workers.yaml"),
            provider=_require_string(values, "provider", "workers.yaml"),
            sandbox_profile=_require_string(values, "sandbox_profile", "workers.yaml"),
            approval_policy=_require_string(values, "approval_policy", "workers.yaml"),
            network_profile=_require_string(values, "network_profile", "workers.yaml"),
            projection_mode=_require_string(values, "projection_mode", "workers.yaml"),
            max_active_leases=_require_positive_int(values, "max_active_leases", "workers.yaml"),
            runner_wired=_optional_bool_with_default(
                values,
                "runner_wired",
                "workers.yaml",
                default=False,
            ),
            runner_acceptance_ref=_optional_string(
                values,
                "runner_acceptance_ref",
                "workers.yaml",
            ),
        )
        _validate_runner_wiring(worker_profile, repo_root)
        workers[name] = worker_profile

    default_worker_profile = _require_string(run_payload, "default_worker_profile", "orchestrator.yaml")
    if default_worker_profile not in workers:
        raise RuntimeConfigError(
            "orchestrator.yaml:run.default_worker_profile must reference a defined worker profile"
        )
    review_worker_profile = _optional_string(run_payload, "review_worker_profile", "orchestrator.yaml")
    if review_worker_profile is not None and review_worker_profile not in workers:
        raise RuntimeConfigError(
            "orchestrator.yaml:run.review_worker_profile must reference a defined worker profile"
        )

    verification_profiles: dict[str, VerificationProfile] = {}
    for name, raw in verification_profiles_payload.items():
        if not isinstance(name, str):
            raise RuntimeConfigError("policies.yaml:verification_profiles keys must be strings")
        values = _require_mapping({"entry": raw}, "entry", "policies.yaml")
        verification_profiles[name] = VerificationProfile(
            name=name,
            build=_optional_command(values, "build", "policies.yaml"),
            lint=_optional_command(values, "lint", "policies.yaml"),
            typecheck=_optional_command(values, "typecheck", "policies.yaml"),
            test=_optional_command(values, "test", "policies.yaml"),
            contract=_optional_command(values, "contract", "policies.yaml"),
            hotspot=_optional_command(values, "hotspot", "policies.yaml"),
        )

    continuation_policies: dict[str, ContinuationPolicy] = {}
    for name, raw in continuation_policies_payload.items():
        if not isinstance(name, str):
            raise RuntimeConfigError("policies.yaml:continuation_policies keys must be strings")
        values = _require_mapping({"entry": raw}, "entry", "policies.yaml")
        continuation_policies[name] = ContinuationPolicy(
            name=name,
            auto_continue=_require_bool(values, "auto_continue", "policies.yaml"),
            review_on_risk_levels=tuple(
                _require_string_list(values, "review_on_risk_levels", "policies.yaml")
            ),
            pause_on_policy_surface=_require_bool(
                values, "pause_on_policy_surface", "policies.yaml"
            ),
            pause_on_verification_failure=_require_bool(
                values, "pause_on_verification_failure", "policies.yaml"
            ),
        )

    retry_policies: dict[str, RetryPolicy] = {}
    for name, raw in retry_policies_payload.items():
        if not isinstance(name, str):
            raise RuntimeConfigError("policies.yaml:retry_policies keys must be strings")
        values = _require_mapping({"entry": raw}, "entry", "policies.yaml")
        retry_policies[name] = RetryPolicy(
            name=name,
            retry_on_gate_failure=_require_bool(
                values, "retry_on_gate_failure", "policies.yaml"
            ),
            retry_on_worker_failure=_require_bool(
                values, "retry_on_worker_failure", "policies.yaml"
            ),
            max_attempts=_require_positive_int(values, "max_attempts", "policies.yaml"),
        )

    return RuntimeConfigBundle(
        repo_root=repo_root,
        orchestrator=OrchestratorSettings(
            default_worker_profile=default_worker_profile,
            review_worker_profile=review_worker_profile,
            run_id_prefix=_require_string(run_payload, "run_id_prefix", "orchestrator.yaml"),
            projection_required=bool(acceptance_payload.get("projection_required", True)),
        ),
        runtime=RuntimeSettings(
            active_version=_optional_string_with_default(
                runtime_payload,
                "active_version",
                "orchestrator.yaml",
                default="v1",
            ),
            experimental_v2_enabled=_optional_bool_with_default(
                runtime_payload,
                "experimental_v2_enabled",
                "orchestrator.yaml",
                default=False,
            ),
            control_plane_db_v2=_optional_string_with_default(
                runtime_payload,
                "control_plane_db_v2",
                "orchestrator.yaml",
                default=".ai/state/control-plane-v2.db",
            ),
            artifact_root_v2=_optional_string_with_default(
                runtime_payload,
                "artifact_root_v2",
                "orchestrator.yaml",
                default=".ai/runs-v2",
            ),
        ),
        policies=PolicySettings(
            policy_surface_globs=tuple(_require_string_list(policies_payload, "policy_surface_globs", "policies.yaml")),
            sensitive_paths=tuple(_require_string_list(policies_payload, "sensitive_paths", "policies.yaml")),
            verification_profiles=verification_profiles,
            continuation_policies=continuation_policies,
            retry_policies=retry_policies,
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


def _optional_string(payload: dict[str, Any], key: str, source_name: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise RuntimeConfigError(f"{source_name}:{key} must be a non-empty string when present")
    return value.strip()


def _optional_string_with_default(
    payload: dict[str, Any],
    key: str,
    source_name: str,
    *,
    default: str,
) -> str:
    value = payload.get(key)
    if value is None:
        return default
    if not isinstance(value, str) or not value.strip():
        raise RuntimeConfigError(f"{source_name}:{key} must be a non-empty string when present")
    return value.strip()


def _require_string_list(payload: dict[str, Any], key: str, source_name: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RuntimeConfigError(f"{source_name}:{key} must be a list of strings")
    return [item.strip() for item in value if item.strip()]


def _require_bool(payload: dict[str, Any], key: str, source_name: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise RuntimeConfigError(f"{source_name}:{key} must be a boolean")
    return value


def _optional_bool_with_default(
    payload: dict[str, Any],
    key: str,
    source_name: str,
    *,
    default: bool,
) -> bool:
    value = payload.get(key)
    if value is None:
        return default
    if not isinstance(value, bool):
        raise RuntimeConfigError(f"{source_name}:{key} must be a boolean when present")
    return value


def _optional_command(payload: dict[str, Any], key: str, source_name: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise RuntimeConfigError(f"{source_name}:{key} must be a string when present")
    stripped = value.strip()
    return stripped or None


def _require_positive_int(payload: dict[str, Any], key: str, source_name: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise RuntimeConfigError(f"{source_name}:{key} must be a positive integer")
    return value


def _validate_runner_wiring(worker_profile: WorkerProfile, repo_root: Path) -> None:
    if worker_profile.lane == "host_local" or not worker_profile.runner_wired:
        return
    acceptance_ref = worker_profile.runner_acceptance_ref
    if acceptance_ref is None:
        raise RuntimeConfigError(
            "workers.yaml:"
            f"{worker_profile.name}.runner_acceptance_ref is required when "
            "runner_wired=true for a non-host-local profile"
        )
    ref_path = Path(acceptance_ref)
    if ref_path.is_absolute():
        raise RuntimeConfigError(
            "workers.yaml:"
            f"{worker_profile.name}.runner_acceptance_ref must be repo-relative"
        )
    repo_root_resolved = repo_root.resolve()
    acceptance_path = (repo_root_resolved / ref_path).resolve()
    try:
        acceptance_path.relative_to(repo_root_resolved)
    except ValueError as exc:
        raise RuntimeConfigError(
            "workers.yaml:"
            f"{worker_profile.name}.runner_acceptance_ref must stay inside the repo"
        ) from exc
    if not acceptance_path.exists():
        raise RuntimeConfigError(
            "workers.yaml:"
            f"{worker_profile.name}.runner_acceptance_ref does not exist: {acceptance_ref}"
        )
