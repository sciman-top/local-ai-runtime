from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from openai_codex import ApprovalMode, Sandbox

from host_orchestrator.runner_acceptance import (
    RunnerAcceptanceError,
    validate_runner_acceptance_file,
)


ORCHESTRATION_CAPABILITIES = {
    "clarification",
    "systematic_debugging",
    "test_first",
    "exploration",
    "spec_review",
    "quality_review",
    "worktree_isolation",
}
ORCHESTRATION_ROLES = {
    "master",
    "explorer",
    "worker",
    "spec_reviewer",
    "quality_reviewer",
    "closeout",
}
ORCHESTRATION_INTENTS = {
    "general",
    "bugfix",
    "feature",
    "refactor",
    "research",
    "docs",
    "review",
    "migration",
    "operations",
}
RISK_LEVELS = {"low", "medium", "high", "critical"}


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
class OrchestrationProfile:
    name: str
    effect: str
    default_mode: str
    max_concurrent_subagents: int
    max_total_subagents: int
    max_tree_depth: int
    min_independent_workstreams: int
    parallel_read_only: bool
    parallel_writers: bool
    require_isolated_worktree_for_writers: bool
    write_conflict_policy: str
    stop_policy: str


@dataclass(frozen=True)
class ModelRoute:
    name: str
    roles: tuple[str, ...]
    intents: tuple[str, ...]
    risk_levels: tuple[str, ...]
    worker_profile: str | None
    model: str
    reasoning_effort: str


@dataclass(frozen=True)
class AdaptiveOrchestrationSettings:
    policy_version: str
    active_profile: str
    profiles: dict[str, OrchestrationProfile]
    model_routes: tuple[ModelRoute, ...]
    capability_routes: dict[str, tuple[str, ...]]
    available_capabilities: tuple[str, ...]

    def profile(self, name: str | None = None) -> OrchestrationProfile:
        profile_name = name or self.active_profile
        try:
            return self.profiles[profile_name]
        except KeyError as exc:
            raise RuntimeConfigError(
                f"Unknown adaptive orchestration profile: {profile_name}"
            ) from exc


@dataclass(frozen=True)
class PolicySettings:
    policy_surface_globs: tuple[str, ...]
    sensitive_paths: tuple[str, ...]
    verification_profiles: dict[str, VerificationProfile]
    continuation_policies: dict[str, ContinuationPolicy]
    retry_policies: dict[str, RetryPolicy]
    adaptive_orchestration: AdaptiveOrchestrationSettings


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
    adaptive_orchestration_payload = _require_mapping(
        policies_payload,
        "adaptive_orchestration",
        "policies.yaml",
    )
    orchestration_profiles_payload = _require_mapping(
        adaptive_orchestration_payload,
        "profiles",
        "policies.yaml:adaptive_orchestration",
    )
    model_routes_payload = _require_mapping(
        adaptive_orchestration_payload,
        "model_routes",
        "policies.yaml:adaptive_orchestration",
    )
    capability_routes_payload = _require_mapping(
        adaptive_orchestration_payload,
        "capability_routes",
        "policies.yaml:adaptive_orchestration",
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

    orchestration_profiles: dict[str, OrchestrationProfile] = {}
    for name, raw in orchestration_profiles_payload.items():
        if not isinstance(name, str):
            raise RuntimeConfigError(
                "policies.yaml:adaptive_orchestration.profiles keys must be strings"
            )
        values = _require_mapping(
            {"entry": raw},
            "entry",
            "policies.yaml:adaptive_orchestration.profiles",
        )
        profile = OrchestrationProfile(
            name=name,
            effect=_require_choice(
                values,
                "effect",
                {"observe", "guarded"},
                "policies.yaml:adaptive_orchestration.profiles",
            ),
            default_mode=_require_choice(
                values,
                "default_mode",
                {"single_agent"},
                "policies.yaml:adaptive_orchestration.profiles",
            ),
            max_concurrent_subagents=_require_non_negative_int(
                values,
                "max_concurrent_subagents",
                "policies.yaml:adaptive_orchestration.profiles",
            ),
            max_total_subagents=_require_non_negative_int(
                values,
                "max_total_subagents",
                "policies.yaml:adaptive_orchestration.profiles",
            ),
            max_tree_depth=_require_non_negative_int(
                values,
                "max_tree_depth",
                "policies.yaml:adaptive_orchestration.profiles",
            ),
            min_independent_workstreams=_require_positive_int(
                values,
                "min_independent_workstreams",
                "policies.yaml:adaptive_orchestration.profiles",
            ),
            parallel_read_only=_require_bool(
                values,
                "parallel_read_only",
                "policies.yaml:adaptive_orchestration.profiles",
            ),
            parallel_writers=_require_bool(
                values,
                "parallel_writers",
                "policies.yaml:adaptive_orchestration.profiles",
            ),
            require_isolated_worktree_for_writers=_require_bool(
                values,
                "require_isolated_worktree_for_writers",
                "policies.yaml:adaptive_orchestration.profiles",
            ),
            write_conflict_policy=_require_choice(
                values,
                "write_conflict_policy",
                {"serialize", "reject"},
                "policies.yaml:adaptive_orchestration.profiles",
            ),
            stop_policy=_require_choice(
                values,
                "stop_policy",
                {
                    "stop_on_scope_or_contract_conflict",
                    "finish_independent_workstreams",
                },
                "policies.yaml:adaptive_orchestration.profiles",
            ),
        )
        _validate_orchestration_profile(profile)
        orchestration_profiles[name] = profile

    active_profile = _require_string(
        adaptive_orchestration_payload,
        "active_profile",
        "policies.yaml:adaptive_orchestration",
    )
    if active_profile not in orchestration_profiles:
        raise RuntimeConfigError(
            "policies.yaml:adaptive_orchestration.active_profile must reference a defined profile"
        )

    model_routes: list[ModelRoute] = []
    for name, raw in model_routes_payload.items():
        if not isinstance(name, str):
            raise RuntimeConfigError(
                "policies.yaml:adaptive_orchestration.model_routes keys must be strings"
            )
        values = _require_mapping(
            {"entry": raw},
            "entry",
            "policies.yaml:adaptive_orchestration.model_routes",
        )
        model_routes.append(
            ModelRoute(
                name=name,
                roles=tuple(
                    _require_string_list(
                        values,
                        "roles",
                        "policies.yaml:adaptive_orchestration.model_routes",
                    )
                ),
                intents=tuple(
                    _require_string_list(
                        values,
                        "intents",
                        "policies.yaml:adaptive_orchestration.model_routes",
                    )
                ),
                risk_levels=tuple(
                    _require_string_list(
                        values,
                        "risk_levels",
                        "policies.yaml:adaptive_orchestration.model_routes",
                    )
                ),
                worker_profile=_optional_string(
                    values,
                    "worker_profile",
                    "policies.yaml:adaptive_orchestration.model_routes",
                ),
                model=_require_string(
                    values,
                    "model",
                    "policies.yaml:adaptive_orchestration.model_routes",
                ),
                reasoning_effort=_require_choice(
                    values,
                    "reasoning_effort",
                    {"low", "medium", "high", "xhigh", "max"},
                    "policies.yaml:adaptive_orchestration.model_routes",
                ),
            )
        )
    for route in model_routes:
        if route.worker_profile is not None and route.worker_profile not in workers:
            raise RuntimeConfigError(
                "policies.yaml:adaptive_orchestration.model_routes."
                f"{route.name}.worker_profile must reference a defined worker profile"
            )
        _reject_unknown_values(
            route.roles,
            ORCHESTRATION_ROLES,
            f"model route {route.name} roles",
        )
        _reject_unknown_values(
            route.intents,
            ORCHESTRATION_INTENTS,
            f"model route {route.name} intents",
        )
        _reject_unknown_values(
            route.risk_levels,
            RISK_LEVELS,
            f"model route {route.name} risk_levels",
        )
    if not model_routes:
        raise RuntimeConfigError(
            "policies.yaml:adaptive_orchestration.model_routes must not be empty"
        )

    capability_routes: dict[str, tuple[str, ...]] = {}
    for intent, raw in capability_routes_payload.items():
        if not isinstance(intent, str) or not isinstance(raw, list):
            raise RuntimeConfigError(
                "policies.yaml:adaptive_orchestration.capability_routes must map strings to string lists"
            )
        values = _require_string_list(
            {"capabilities": raw},
            "capabilities",
            "policies.yaml:adaptive_orchestration.capability_routes",
        )
        if intent not in ORCHESTRATION_INTENTS:
            raise RuntimeConfigError(
                f"unknown adaptive orchestration capability intent: {intent}"
            )
        _reject_unknown_values(
            values,
            ORCHESTRATION_CAPABILITIES,
            f"capability route {intent}",
        )
        capability_routes[intent] = tuple(values)

    available_capabilities = tuple(
        _require_string_list(
            adaptive_orchestration_payload,
            "available_capabilities",
            "policies.yaml:adaptive_orchestration",
        )
    )
    _reject_unknown_values(
        available_capabilities,
        ORCHESTRATION_CAPABILITIES,
        "available adaptive orchestration capabilities",
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
            adaptive_orchestration=AdaptiveOrchestrationSettings(
                policy_version=_require_string(
                    adaptive_orchestration_payload,
                    "policy_version",
                    "policies.yaml:adaptive_orchestration",
                ),
                active_profile=active_profile,
                profiles=orchestration_profiles,
                model_routes=tuple(model_routes),
                capability_routes=capability_routes,
                available_capabilities=available_capabilities,
            ),
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


def _require_non_negative_int(payload: dict[str, Any], key: str, source_name: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise RuntimeConfigError(f"{source_name}:{key} must be a non-negative integer")
    return value


def _require_choice(
    payload: dict[str, Any],
    key: str,
    allowed: set[str],
    source_name: str,
) -> str:
    value = _require_string(payload, key, source_name)
    if value not in allowed:
        raise RuntimeConfigError(
            f"{source_name}:{key} must be one of {sorted(allowed)}, got '{value}'"
        )
    return value


def _validate_orchestration_profile(profile: OrchestrationProfile) -> None:
    if profile.max_concurrent_subagents > 3:
        raise RuntimeConfigError(
            f"orchestration profile {profile.name} exceeds max_concurrent_subagents=3"
        )
    if profile.max_total_subagents > 6:
        raise RuntimeConfigError(
            f"orchestration profile {profile.name} exceeds max_total_subagents=6"
        )
    if profile.max_concurrent_subagents > profile.max_total_subagents:
        raise RuntimeConfigError(
            f"orchestration profile {profile.name} concurrency exceeds total budget"
        )
    if profile.max_concurrent_subagents == 0:
        if profile.max_total_subagents != 0 or profile.max_tree_depth != 0:
            raise RuntimeConfigError(
                f"orchestration profile {profile.name} zero concurrency requires zero total budget and depth"
            )
    elif profile.max_tree_depth != 1:
        raise RuntimeConfigError(
            f"orchestration profile {profile.name} must keep max_tree_depth=1"
        )


def _reject_unknown_values(
    values: list[str] | tuple[str, ...],
    allowed: set[str],
    context: str,
) -> None:
    unknown = sorted(set(values) - allowed)
    if unknown:
        raise RuntimeConfigError(f"{context} contains unknown values: {unknown}")


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
    try:
        validate_runner_acceptance_file(
            acceptance_path=acceptance_path,
            acceptance_ref=acceptance_ref,
            worker_profile=worker_profile.name,
            lane=worker_profile.lane,
            runner_kind=worker_profile.worker_kind,
        )
    except RunnerAcceptanceError as exc:
        raise RuntimeConfigError(str(exc)) from exc
