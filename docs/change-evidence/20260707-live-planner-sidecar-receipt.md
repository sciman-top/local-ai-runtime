# 20260707 Live Planner Sidecar Receipt

## Scope

- land a repo-owned live planner sidecar receipt on `host_local`
- keep planner-gated tasks bounded at `waiting_handoff`
- add `planner_result.json` to the formal runtime artifact chain

## What Changed

- `HostLocalRunner` now separates true planner reasons from capability / quota / lane blockers
- planner-gated tasks on codex-backed `host_local` profiles now run a live planner sidecar, materialize `planner_result.json`, and still stop before primary worker execution
- pre-worker capability / quota blockers continue fail-closed without pretending planner already ran
- `result.json` / `dispatch_state.json` now carry `planner_result_ref` when the live planner receipt exists
- templates, schemas, and validations now include the planner receipt contract

## Truth Boundary

- current live planner sidecar only proves a codex-backed host_local planner receipt boundary
- current runtime still does not auto-continue from planner into worker execution
- this still does not mean live `Direct GPT-5.4 API` planner, live heterogeneous review sidecar, non-host_local runner, `platform compatibility green`, or `live accepted`

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_agent_work_assets.py runtime\host-orchestrator\tests\test_planner_adapter.py runtime\host-orchestrator\tests\test_agentbridge_intake.py runtime\host-orchestrator\tests\test_wave1_execution.py`
