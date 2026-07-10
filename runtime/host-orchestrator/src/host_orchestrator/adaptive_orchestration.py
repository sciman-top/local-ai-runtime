from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from fnmatch import fnmatchcase
import hashlib
import json
from pathlib import Path
import subprocess
import sqlite3
from typing import Any

from host_orchestrator.agent_work_assets import (
    load_mapping_file,
    normalize_manifest_payload,
    validate_manifest_payload,
)
from host_orchestrator.config_runtime import (
    ModelRoute,
    OrchestrationProfile,
    RuntimeConfigBundle,
)
from host_orchestrator.paths import RuntimeLayout


DECISION_SCHEMA_VERSION = "orchestration_decision.v1"

WorktreeInspector = Callable[[Mapping[str, Any], Path], dict[str, Any]]


class AdaptiveOrchestrationError(ValueError):
    """Raised when an orchestration manifest cannot produce a safe decision."""


def evaluate_orchestration_manifest(
    manifest_path: Path,
    *,
    repo_root: Path,
    runtime_config: RuntimeConfigBundle,
    active_leases: Mapping[str, int] | None = None,
    worktree_inspector: WorktreeInspector | None = None,
    evaluated_at: str | None = None,
) -> dict[str, Any]:
    payload = load_mapping_file(manifest_path)
    return evaluate_orchestration_payload(
        payload,
        repo_root=repo_root,
        runtime_config=runtime_config,
        active_leases=active_leases,
        worktree_inspector=worktree_inspector,
        evaluated_at=evaluated_at,
    )


def evaluate_orchestration_payload(
    payload: Mapping[str, Any],
    *,
    repo_root: Path,
    runtime_config: RuntimeConfigBundle,
    active_leases: Mapping[str, int] | None = None,
    worktree_inspector: WorktreeInspector | None = None,
    evaluated_at: str | None = None,
) -> dict[str, Any]:
    payload = normalize_manifest_payload(payload)
    validate_manifest_payload(payload)
    declared_repo_root = Path(str(payload["repo_root"]))
    if not declared_repo_root.is_absolute():
        declared_repo_root = repo_root / declared_repo_root
    if declared_repo_root.resolve(strict=False) != repo_root.resolve(strict=False):
        raise AdaptiveOrchestrationError(
            "manifest_repo_root_mismatch: manifest.repo_root must resolve to the evaluated repo root"
        )
    constraints = _mapping(payload["orchestration_constraints"], "orchestration_constraints")
    orchestration = runtime_config.policies.adaptive_orchestration
    profile = orchestration.profile(str(constraints["profile"]))
    effective_conflict_policy = (
        "reject"
        if "reject" in {profile.write_conflict_policy, str(constraints["write_conflict_policy"])}
        else "serialize"
    )
    effective_stop_policy = (
        "stop_on_scope_or_contract_conflict"
        if "stop_on_scope_or_contract_conflict"
        in {profile.stop_policy, str(constraints["stop_policy"])}
        else "finish_independent_workstreams"
    )
    budgets = _effective_budgets(profile, constraints)
    manifest_digest = _payload_digest(payload)
    decision_id = _decision_id(
        manifest_digest=manifest_digest,
        policy_version=orchestration.policy_version,
        profile=profile.name,
        constraints=constraints,
    )
    inspected_at = evaluated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    active_leases = dict(active_leases or {})
    inspector = worktree_inspector or inspect_worktree

    raw_tasks = [_mapping(item, "manifest.tasks[]") for item in _list(payload["tasks"], "tasks")]
    task_map = {str(task["task_id"]): task for task in raw_tasks}
    if len(task_map) != len(raw_tasks):
        raise AdaptiveOrchestrationError("manifest task_id values must be unique")

    dependency_layers, dependency_issues = _dependency_layers(task_map)
    worktree_statuses = {
        task_id: inspector(task, repo_root)
        for task_id, task in sorted(task_map.items())
    }
    task_routes = [
        _task_route(
            task=task,
            runtime_config=runtime_config,
            profile=profile,
            worktree_status=worktree_statuses[task_id],
            active_leases=active_leases,
        )
        for task_id, task in sorted(task_map.items())
    ]
    task_route_map = {route["task_id"]: route for route in task_routes}
    conflicts = _conflict_matrix(
        task_map=task_map,
        truth_sources=[str(value) for value in _list(payload["truth_sources"], "truth_sources")],
        policy_surface_globs=runtime_config.policies.policy_surface_globs,
    )
    conflict_pairs = {
        frozenset((entry["left_task_id"], entry["right_task_id"])): entry
        for entry in conflicts
    }

    mode_preference = str(constraints["mode_preference"])
    waves, delegated_task_count = _build_waves(
        dependency_layers=dependency_layers,
        task_map=task_map,
        task_route_map=task_route_map,
        conflict_pairs=conflict_pairs,
        profile=profile,
        mode_preference=mode_preference,
        max_concurrent=budgets["max_concurrent_subagents"],
        max_total=budgets["max_total_subagents"],
    )
    selected_mode = (
        "multi_agent" if any(bool(wave["parallel"]) for wave in waves) else "single_agent"
    )

    reason_codes: set[str] = set()
    if selected_mode == "multi_agent":
        reason_codes.add("independent_workstreams_available")
    else:
        reason_codes.add("single_agent_default")
    if len(task_map) == 1:
        reason_codes.add("single_task")
    if mode_preference == "single_agent":
        reason_codes.add("single_agent_preference")
    if mode_preference == "multi_agent" and selected_mode != "multi_agent":
        reason_codes.add("multi_agent_preference_downgraded")
    if conflicts:
        reason_codes.add("conflicts_require_serialization")
    if any(not status["verified"] and task_map[task_id]["write_access"] for task_id, status in worktree_statuses.items()):
        reason_codes.add("writer_isolation_unverified")
    if dependency_issues:
        reason_codes.update(issue["reason_code"] for issue in dependency_issues)
    if conflicts and effective_conflict_policy == "reject":
        reason_codes.add("write_conflict_rejected")
    planned_worker_count = len(task_map)
    worker_budget_exceeded = (
        profile.effect == "guarded"
        and planned_worker_count > budgets["max_total_subagents"]
    )
    if budgets["max_total_subagents"] == 0:
        reason_codes.add("subagent_budget_disabled")
    if worker_budget_exceeded:
        reason_codes.add("total_subagent_budget_exceeded")

    route_blockers = [
        reason
        for route in task_routes
        for reason in route["blocking_reason_codes"]
    ]
    blocking_reason_codes = sorted(set(route_blockers))
    blocking_reason_codes.extend(
        reason
        for reason in sorted({issue["reason_code"] for issue in dependency_issues})
        if reason not in blocking_reason_codes
    )
    if conflicts and effective_conflict_policy == "reject":
        blocking_reason_codes.append("write_conflict_rejected")
    if worker_budget_exceeded:
        blocking_reason_codes.append("total_subagent_budget_exceeded")
    blocking_reason_codes = sorted(set(blocking_reason_codes))
    if dependency_issues or blocking_reason_codes:
        decision_status = "blocked"
    elif profile.effect == "observe":
        decision_status = "observed"
    else:
        decision_status = "guarded_ready"

    payload_out = {
        "schema_version": DECISION_SCHEMA_VERSION,
        "decision_id": decision_id,
        "run_id": str(payload["run_id"]),
        "policy_version": orchestration.policy_version,
        "profile": profile.name,
        "effect": profile.effect,
        "decision_status": decision_status,
        "selected_mode": selected_mode,
        "mode_preference": mode_preference,
        "reason_codes": sorted(reason_codes),
        "blocking_reason_codes": blocking_reason_codes,
        "evaluated_at": inspected_at,
        "manifest_digest": manifest_digest,
        "manifest_schema_version": str(payload["schema_version"]),
        "evaluation_context": dict(payload["evaluation_context"])
        if isinstance(payload.get("evaluation_context"), Mapping)
        else None,
        "budgets": {
            **budgets,
            "delegated_task_count": delegated_task_count,
            "planned_worker_count": planned_worker_count,
            "nested_subagents_allowed": False,
        },
        "conflict_policy": effective_conflict_policy,
        "stop_policy": effective_stop_policy,
        "waves": waves,
        "conflicts": conflicts,
        "dependency_issues": dependency_issues,
        "task_routes": task_routes,
        "source_evidence_refs": [
            str(value) for value in _list(payload["truth_sources"], "truth_sources")
        ],
        "runtime_boundaries": {
            "default_entrypoint_changed": False,
            "active_queue_changed": False,
            "live_accepted": False,
        },
    }
    validate_orchestration_decision_payload(payload_out)
    return payload_out


def write_orchestration_decision(
    *,
    layout: RuntimeLayout,
    decision: Mapping[str, Any],
) -> Path:
    validate_orchestration_decision_payload(decision)
    path = (
        layout.runs_v2_root
        / str(decision["run_id"])
        / "_orchestration"
        / str(decision["decision_id"])
        / "orchestration-decision.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(decision), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def read_active_leases(
    *,
    db_path: Path,
    worker_profiles: list[str],
) -> dict[str, int]:
    if not db_path.exists():
        return {profile: 0 for profile in worker_profiles}
    try:
        with sqlite3.connect(db_path) as connection:
            rows = connection.execute(
                """
                SELECT worker_profile, COUNT(*)
                FROM leases
                WHERE released_at IS NULL
                GROUP BY worker_profile
                """
            ).fetchall()
    except sqlite3.Error as exc:
        raise AdaptiveOrchestrationError(
            f"lease_state_unavailable: cannot read active leases from {db_path}: {exc}"
        ) from exc
    counts = {str(profile): int(count) for profile, count in rows}
    return {profile: counts.get(profile, 0) for profile in worker_profiles}


def validate_orchestration_decision_payload(payload: Mapping[str, Any]) -> None:
    required = {
        "schema_version",
        "decision_id",
        "run_id",
        "policy_version",
        "profile",
        "effect",
        "decision_status",
        "selected_mode",
        "mode_preference",
        "reason_codes",
        "blocking_reason_codes",
        "evaluated_at",
        "manifest_digest",
        "manifest_schema_version",
        "evaluation_context",
        "budgets",
        "conflict_policy",
        "stop_policy",
        "waves",
        "conflicts",
        "dependency_issues",
        "task_routes",
        "source_evidence_refs",
        "runtime_boundaries",
    }
    missing = sorted(required - payload.keys())
    if missing:
        raise AdaptiveOrchestrationError(
            "orchestration decision missing required fields: " + ", ".join(missing)
        )
    if payload["schema_version"] != DECISION_SCHEMA_VERSION:
        raise AdaptiveOrchestrationError(
            f"orchestration decision schema_version must be {DECISION_SCHEMA_VERSION}"
        )
    if payload["effect"] not in {"observe", "guarded"}:
        raise AdaptiveOrchestrationError("orchestration decision effect is invalid")
    if payload["selected_mode"] not in {"single_agent", "multi_agent"}:
        raise AdaptiveOrchestrationError("orchestration decision selected_mode is invalid")
    if payload["decision_status"] not in {"observed", "guarded_ready", "blocked"}:
        raise AdaptiveOrchestrationError("orchestration decision status is invalid")
    boundaries = _mapping(payload["runtime_boundaries"], "runtime_boundaries")
    if any(boundaries.get(key) is not False for key in (
        "default_entrypoint_changed",
        "active_queue_changed",
        "live_accepted",
    )):
        raise AdaptiveOrchestrationError(
            "orchestration decision must preserve default entrypoint, active queue, and live acceptance"
        )


def validate_orchestration_execution_payload(payload: Mapping[str, Any]) -> None:
    required = {
        "schema_version",
        "decision_id",
        "orchestration_decision_ref",
        "run_id",
        "policy_version",
        "profile",
        "selected_mode",
        "status",
        "worker_execution_attempted",
        "result_count",
        "status_counts",
        "parallel_wave_count",
        "serial_wave_count",
        "skipped_task_ids",
        "wall_time_ms",
        "results",
        "default_entrypoint_changed",
        "active_queue_changed",
        "live_accepted",
    }
    missing = sorted(required - payload.keys())
    if missing:
        raise AdaptiveOrchestrationError(
            "orchestration execution missing required fields: " + ", ".join(missing)
        )
    if payload["schema_version"] != "orchestration_execution.v1":
        raise AdaptiveOrchestrationError(
            "orchestration execution schema_version must be orchestration_execution.v1"
        )
    if payload["status"] not in {"completed", "partial", "blocked"}:
        raise AdaptiveOrchestrationError("orchestration execution status is invalid")
    if any(
        payload.get(field) is not False
        for field in ("default_entrypoint_changed", "active_queue_changed", "live_accepted")
    ):
        raise AdaptiveOrchestrationError(
            "orchestration execution must preserve default entrypoint, active queue, and live acceptance"
        )


def inspect_worktree(task: Mapping[str, Any], repo_root: Path) -> dict[str, Any]:
    if not bool(task["write_access"]):
        return {
            "required": False,
            "verified": True,
            "reason_code": "read_only_worktree_not_required",
            "resolved_path": None,
            "branch": None,
        }

    raw_path = str(task["worktree_path"])
    candidate = Path(raw_path)
    if candidate.is_absolute() or candidate.drive:
        return _worktree_failure(candidate, "worktree_path_not_repo_relative")
    repo_root = repo_root.resolve(strict=False)
    resolved = (repo_root / candidate).resolve(strict=False)
    if not resolved.is_relative_to(repo_root):
        return _worktree_failure(resolved, "worktree_path_outside_repo")
    if not resolved.exists() or not (resolved / ".git").is_file():
        return _worktree_failure(resolved, "worktree_missing_or_not_git")
    if resolved == repo_root:
        return _worktree_failure(resolved, "worktree_not_isolated")

    try:
        top_level = subprocess.run(
            ["git", "-C", str(resolved), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
        branch = subprocess.run(
            ["git", "-C", str(resolved), "branch", "--show-current"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
        worktree_common_dir = subprocess.run(
            ["git", "-C", str(resolved), "rev-parse", "--git-common-dir"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
        repo_common_dir = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--git-common-dir"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return _worktree_failure(resolved, "worktree_git_inspection_failed")

    if Path(top_level).resolve() != resolved:
        return _worktree_failure(resolved, "worktree_root_mismatch")
    if _resolve_git_path(worktree_common_dir, resolved) != _resolve_git_path(
        repo_common_dir,
        repo_root,
    ):
        return _worktree_failure(resolved, "worktree_not_linked_to_repo")
    if branch != str(task["branch_name"]):
        return {
            **_worktree_failure(resolved, "worktree_branch_mismatch"),
            "branch": branch,
        }
    return {
        "required": True,
        "verified": True,
        "reason_code": "worktree_verified",
        "resolved_path": str(resolved),
        "branch": branch,
    }


def _worktree_failure(path: Path, reason_code: str) -> dict[str, Any]:
    return {
        "required": True,
        "verified": False,
        "reason_code": reason_code,
        "resolved_path": str(path),
        "branch": None,
    }


def _resolve_git_path(value: str, cwd: Path) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = cwd / candidate
    return candidate.resolve(strict=False)


def _effective_budgets(
    profile: OrchestrationProfile,
    constraints: Mapping[str, Any],
) -> dict[str, int]:
    concurrent = min(
        profile.max_concurrent_subagents,
        int(constraints["max_concurrent_subagents"]),
    )
    total = min(profile.max_total_subagents, int(constraints["max_total_subagents"]))
    depth = min(profile.max_tree_depth, int(constraints["max_tree_depth"]))
    if concurrent == 0 or total == 0 or depth == 0:
        return {
            "max_concurrent_subagents": 0,
            "max_total_subagents": 0,
            "max_tree_depth": 0,
        }
    return {
        "max_concurrent_subagents": min(concurrent, total),
        "max_total_subagents": total,
        "max_tree_depth": depth,
    }


def _dependency_layers(
    task_map: Mapping[str, Mapping[str, Any]],
) -> tuple[list[list[str]], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    dependencies: dict[str, set[str]] = {}
    for task_id, task in task_map.items():
        declared = {str(value) for value in _list(task["depends_on"], f"{task_id}.depends_on")}
        unknown = sorted(declared - task_map.keys())
        for dependency in unknown:
            issues.append(
                {
                    "task_id": task_id,
                    "dependency_ref": dependency,
                    "reason_code": "unknown_dependency",
                }
            )
        dependencies[task_id] = declared & task_map.keys()

    remaining = {task_id: set(refs) for task_id, refs in dependencies.items()}
    layers: list[list[str]] = []
    while remaining:
        ready = sorted(task_id for task_id, refs in remaining.items() if not refs)
        if not ready:
            for task_id in sorted(remaining):
                issues.append(
                    {
                        "task_id": task_id,
                        "dependency_ref": None,
                        "reason_code": "dependency_cycle",
                    }
                )
            break
        layers.append(ready)
        for task_id in ready:
            remaining.pop(task_id)
        for refs in remaining.values():
            refs.difference_update(ready)
    return layers, issues


def _task_route(
    *,
    task: Mapping[str, Any],
    runtime_config: RuntimeConfigBundle,
    profile: OrchestrationProfile,
    worktree_status: Mapping[str, Any],
    active_leases: Mapping[str, int],
) -> dict[str, Any]:
    task_id = str(task["task_id"])
    intent = str(task.get("intent") or "general")
    role = _agent_role(str(task["kind"]))
    risk_level = str(task["risk_level"])
    model_route = _select_model_route(
        runtime_config.policies.adaptive_orchestration.model_routes,
        role=role,
        intent=intent,
        risk_level=risk_level,
    )
    requested_capabilities = list(
        runtime_config.policies.adaptive_orchestration.capability_routes.get(intent, ())
    )
    if role == "explorer" and "exploration" not in requested_capabilities:
        requested_capabilities.append("exploration")
    if role == "quality_reviewer":
        for capability in ("spec_review", "quality_review"):
            if capability not in requested_capabilities:
                requested_capabilities.append(capability)
    if bool(task.get("user_forced_planner")) and "clarification" not in requested_capabilities:
        requested_capabilities.append("clarification")
    if bool(task["write_access"]) and bool(worktree_status["verified"]):
        requested_capabilities.append("worktree_isolation")
    requested_capabilities = list(dict.fromkeys(requested_capabilities))
    available = set(runtime_config.policies.adaptive_orchestration.available_capabilities)
    unavailable = sorted(capability for capability in requested_capabilities if capability not in available)

    worker_profile_name = str(
        task.get("worker_profile")
        or model_route.worker_profile
        or runtime_config.orchestrator.default_worker_profile
    )
    blocking_reasons: list[str] = []
    worker_profile = runtime_config.workers.get(worker_profile_name)
    if worker_profile is None:
        blocking_reasons.append("unknown_worker_profile")
        available_slots = 0
    else:
        available_slots = max(
            0,
            worker_profile.max_active_leases - active_leases.get(worker_profile_name, 0),
        )
        if str(task["execution_lane"]) != worker_profile.lane:
            blocking_reasons.append("execution_lane_profile_mismatch")
        if bool(task["requires_network"]) and worker_profile.network_profile == "off":
            blocking_reasons.append("requires_network_with_offline_profile")
        if bool(task["requires_gui"]):
            blocking_reasons.append("requires_gui_boundary")
        if worker_profile.lane != "host_local" and not worker_profile.runner_wired:
            blocking_reasons.append("selected_lane_runner_not_wired")
        if active_leases.get(worker_profile_name, 0) >= worker_profile.max_active_leases:
            blocking_reasons.append("lease_quota_exhausted")
        if not bool(task["write_access"]) and worker_profile.sandbox_profile != "read_only":
            blocking_reasons.append("read_only_task_requires_read_only_profile")
        if bool(task["write_access"]) and worker_profile.sandbox_profile == "read_only":
            blocking_reasons.append("write_task_requires_write_profile")
    if unavailable:
        blocking_reasons.append("capability_unavailable")
    if (
        bool(task["write_access"])
        and profile.require_isolated_worktree_for_writers
        and not bool(worktree_status["verified"])
    ):
        blocking_reasons.append("writer_isolation_unverified")

    planner_required = bool(task.get("user_forced_planner")) or risk_level in {
        "high",
        "critical",
    }
    if profile.effect == "guarded" and planner_required:
        blocking_reasons.append("planner_sidecar_required")

    return {
        "task_id": task_id,
        "kind": str(task["kind"]),
        "intent": intent,
        "role": role,
        "risk_level": risk_level,
        "worker_profile": worker_profile_name,
        "available_slots": available_slots,
        "write_access": bool(task["write_access"]),
        "planner_required": planner_required or bool(task["depends_on"]),
        "review_required": bool(task.get("user_forced_review"))
        or risk_level in {"medium", "high", "critical"},
        "model_policy": {
            "route": model_route.name,
            "model": model_route.model,
            "reasoning_effort": model_route.reasoning_effort,
        },
        "capabilities": requested_capabilities,
        "unavailable_capabilities": unavailable,
        "worktree": dict(worktree_status),
        "blocking_reason_codes": sorted(set(blocking_reasons)),
    }


def _select_model_route(
    routes: tuple[ModelRoute, ...],
    *,
    role: str,
    intent: str,
    risk_level: str,
) -> ModelRoute:
    for route in routes:
        if route.roles and role not in route.roles:
            continue
        if route.intents and intent not in route.intents:
            continue
        if route.risk_levels and risk_level not in route.risk_levels:
            continue
        return route
    raise AdaptiveOrchestrationError(
        f"no model route matches role={role}, intent={intent}, risk_level={risk_level}"
    )


def _agent_role(kind: str) -> str:
    if kind in {"explore", "docs_sync"}:
        return "explorer"
    if kind == "review":
        return "quality_reviewer"
    if kind == "closeout":
        return "closeout"
    return "worker"


def _conflict_matrix(
    *,
    task_map: Mapping[str, Mapping[str, Any]],
    truth_sources: list[str],
    policy_surface_globs: tuple[str, ...],
) -> list[dict[str, Any]]:
    task_ids = sorted(task_map)
    conflicts: list[dict[str, Any]] = []
    for index, left_id in enumerate(task_ids):
        for right_id in task_ids[index + 1 :]:
            reasons, path_refs = _task_conflicts(
                task_map[left_id],
                task_map[right_id],
                truth_sources=truth_sources,
                policy_surface_globs=policy_surface_globs,
            )
            if reasons:
                conflicts.append(
                    {
                        "left_task_id": left_id,
                        "right_task_id": right_id,
                        "reason_codes": sorted(reasons),
                        "path_refs": sorted(path_refs),
                    }
                )
    return conflicts


def _task_conflicts(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    *,
    truth_sources: list[str],
    policy_surface_globs: tuple[str, ...],
) -> tuple[set[str], set[str]]:
    if not bool(left["write_access"]) and not bool(right["write_access"]):
        return set(), set()

    left_reads = _patterns(left["read_set"])
    right_reads = _patterns(right["read_set"])
    left_writes = _patterns(left["write_set"])
    right_writes = _patterns(right["write_set"])
    reasons: set[str] = set()
    path_refs: set[str] = set()

    if bool(left["write_access"]) and not left_writes:
        reasons.add("unbounded_write_set")
    if bool(right["write_access"]) and not right_writes:
        reasons.add("unbounded_write_set")
    for left_pattern in left_writes:
        for right_pattern in right_writes:
            if _patterns_overlap(left_pattern, right_pattern):
                reasons.add("write_write_conflict")
                path_refs.update((left_pattern, right_pattern))
        for right_pattern in right_reads:
            if _patterns_overlap(left_pattern, right_pattern):
                reasons.add("write_read_conflict")
                path_refs.update((left_pattern, right_pattern))
    for right_pattern in right_writes:
        for left_pattern in left_reads:
            if _patterns_overlap(right_pattern, left_pattern):
                reasons.add("write_read_conflict")
                path_refs.update((right_pattern, left_pattern))

    left_write_scope = left_writes or _patterns(left["allowed_paths"])
    right_write_scope = right_writes or _patterns(right["allowed_paths"])
    if bool(left["write_access"]) and bool(right["write_access"]):
        if _touches_any(left_write_scope, policy_surface_globs) and _touches_any(
            right_write_scope, policy_surface_globs
        ):
            reasons.add("policy_surface_competition")
        if _touches_any(left_write_scope, tuple(truth_sources)) and _touches_any(
            right_write_scope, tuple(truth_sources)
        ):
            reasons.add("authoritative_truth_competition")
        if str(left["worktree_path"]) == str(right["worktree_path"]):
            reasons.add("shared_worktree")
    return reasons, path_refs


def _build_waves(
    *,
    dependency_layers: list[list[str]],
    task_map: Mapping[str, Mapping[str, Any]],
    task_route_map: Mapping[str, Mapping[str, Any]],
    conflict_pairs: Mapping[frozenset[str], Mapping[str, Any]],
    profile: OrchestrationProfile,
    mode_preference: str,
    max_concurrent: int,
    max_total: int,
) -> tuple[list[dict[str, Any]], int]:
    waves: list[dict[str, Any]] = []
    delegated_total = 0
    force_serial = mode_preference == "single_agent" or max_concurrent < 2

    for layer in dependency_layers:
        pending = list(layer)
        while pending:
            first = pending.pop(0)
            batch = [first]
            if not force_serial and _parallel_eligible(
                task_map[first], task_route_map[first], profile
            ):
                for candidate in list(pending):
                    if len(batch) >= max_concurrent:
                        break
                    if delegated_total + len(batch) + 1 > max_total:
                        break
                    if not _parallel_eligible(
                        task_map[candidate], task_route_map[candidate], profile
                    ):
                        continue
                    candidate_profile = str(task_route_map[candidate]["worker_profile"])
                    same_profile_count = sum(
                        1
                        for existing in batch
                        if str(task_route_map[existing]["worker_profile"])
                        == candidate_profile
                    )
                    if same_profile_count >= int(task_route_map[candidate]["available_slots"]):
                        continue
                    if any(
                        frozenset((candidate, existing)) in conflict_pairs
                        for existing in batch
                    ):
                        continue
                    batch.append(candidate)
                    pending.remove(candidate)

            parallel = (
                len(batch) >= profile.min_independent_workstreams
                and delegated_total + len(batch) <= max_total
            )
            if parallel:
                delegated_total += len(batch)
            else:
                if len(batch) > 1:
                    pending = batch[1:] + pending
                    batch = batch[:1]
            waves.append(
                {
                    "wave_id": f"wave-{len(waves) + 1:03d}",
                    "task_ids": batch,
                    "parallel": parallel,
                    "execution_kind": _execution_kind(
                        [task_map[task_id] for task_id in batch], parallel=parallel
                    ),
                }
            )
    return waves, delegated_total


def _parallel_eligible(
    task: Mapping[str, Any],
    route: Mapping[str, Any],
    profile: OrchestrationProfile,
) -> bool:
    if route["blocking_reason_codes"]:
        return False
    if not bool(task["write_access"]):
        return profile.parallel_read_only
    if not profile.parallel_writers:
        return False
    if profile.require_isolated_worktree_for_writers:
        return bool(_mapping(route["worktree"], "task_route.worktree")["verified"])
    return True


def _execution_kind(tasks: list[Mapping[str, Any]], *, parallel: bool) -> str:
    if not parallel:
        return "serial"
    write_count = sum(1 for task in tasks if bool(task["write_access"]))
    if write_count == 0:
        return "parallel_read_only"
    if write_count == len(tasks):
        return "parallel_isolated_writers"
    return "parallel_mixed"


def _touches_any(patterns: list[str], targets: tuple[str, ...]) -> bool:
    return any(
        _patterns_overlap(pattern, target)
        for pattern in patterns
        for target in targets
    )


def _patterns(value: Any) -> list[str]:
    return [_normalize_pattern(str(item)) for item in _list(value, "path patterns")]


def _normalize_pattern(value: str) -> str:
    normalized = value.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.rstrip("/")


def _patterns_overlap(left: str, right: str) -> bool:
    left = _normalize_pattern(left)
    right = _normalize_pattern(right)
    if not left or not right:
        return False
    if left == right or fnmatchcase(left, right) or fnmatchcase(right, left):
        return True
    left_prefix = _static_prefix(left)
    right_prefix = _static_prefix(right)
    if not left_prefix or not right_prefix:
        return True
    return left_prefix.startswith(right_prefix) or right_prefix.startswith(left_prefix)


def _static_prefix(pattern: str) -> str:
    wildcard_positions = [
        position for token in ("*", "?", "[") if (position := pattern.find(token)) >= 0
    ]
    prefix = pattern[: min(wildcard_positions)] if wildcard_positions else pattern
    return prefix.rstrip("/")


def _payload_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _decision_id(
    *,
    manifest_digest: str,
    policy_version: str,
    profile: str,
    constraints: Mapping[str, Any],
) -> str:
    seed = json.dumps(
        {
            "manifest_digest": manifest_digest,
            "policy_version": policy_version,
            "profile": profile,
            "constraints": constraints,
        },
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return "orch-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def _mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AdaptiveOrchestrationError(f"{context} must be an object")
    return value


def _list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise AdaptiveOrchestrationError(f"{context} must be a list")
    return value
