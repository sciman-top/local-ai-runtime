from __future__ import annotations

from host_orchestrator.config_runtime import ContinuationPolicy

from host_orchestrator.runtime_v2.contracts import RuntimeV2Task


def determine_execution_profile(task: RuntimeV2Task) -> str:
    if task.write_access and task.risk_level in {"high", "critical"}:
        return "sandbox_write"
    if task.write_access:
        return "local_write"
    return "local_read"


def should_enter_review(
    *,
    task: RuntimeV2Task,
    continuation_policy: ContinuationPolicy,
    policy_surface_touched: bool,
    gate_failed: bool,
) -> bool:
    if gate_failed and continuation_policy.pause_on_verification_failure:
        return False
    if policy_surface_touched and continuation_policy.pause_on_policy_surface:
        return True
    return task.risk_level in continuation_policy.review_on_risk_levels


def should_pause_for_policy(
    *,
    continuation_policy: ContinuationPolicy,
    policy_surface_touched: bool,
    gate_failed: bool,
) -> bool:
    if gate_failed and continuation_policy.pause_on_verification_failure:
        return True
    if policy_surface_touched and continuation_policy.pause_on_policy_surface:
        return True
    return not continuation_policy.auto_continue
