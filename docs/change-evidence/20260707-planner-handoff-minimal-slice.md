# 2026-07-07 Planner Handoff Minimal Slice

## Slice

- `P4-T01` 这次只把 repo-side planner gate 与 handoff result 补齐
- `planner_required` 当前只基于已 materialize 的 `risk_level in {high, critical}` 与非空 `depends_on` 派生
- 命中 planner gate 时，`host_local` 当前会在主 worker 前停在 `waiting_handoff`

## Code Points

- `runtime/host-orchestrator/src/host_orchestrator/canonical_task.py`
- `runtime/host-orchestrator/src/host_orchestrator/host_local.py`
- `runtime/host-orchestrator/src/host_orchestrator/canonical_result.py`
- `runtime/host-orchestrator/src/host_orchestrator/agentbridge.py`
- `runtime/host-orchestrator/tests/test_planner_adapter.py`
- `runtime/host-orchestrator/tests/test_agentbridge_intake.py`

## Boundary

- 当前只证明 repo-side `waiting_handoff` handoff result 已落地
- 当前没有宣称 live `Direct GPT-5.4 API` planner 已接线
- 当前没有进入 `P4-T02 review adapter`
- 当前没有改 `.ai/config/*.yaml`
- 当前没有改 `compatibility_projection_ref` / `lane` 字段名
- 当前没有进入 Hermes parity、remote_non_gui、vm_gui、execution-critical markdown override

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest`：pass（33 passed）
- `python .\scripts\verify-planning-status.py`：pass
- `python .\scripts\select-next-work.py`：pass（`next_action = promote_phase1_execution`）
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit -Json`：pass
