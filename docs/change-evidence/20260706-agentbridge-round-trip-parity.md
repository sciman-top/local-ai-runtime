# 2026-07-06 AgentBridge Round-Trip Parity

## Slice

- `P2-T03` 这次只把 repo-side projection parity 闭环补齐
- `Wave 1 smoke` 现在直接走 `AgentBridge/tasks/*.md -> HostLocalRunner.run_task()` 主入口
- canonical normalization 仍只在内存中完成，不再为 smoke 额外落 `canonical-tasks/*.json` sidecar

## Code Points

- `runtime/host-orchestrator/src/host_orchestrator/wave1_smoke.py`
- `runtime/host-orchestrator/tests/test_agentbridge_intake.py`
- `runtime/host-orchestrator/tests/test_wave1_execution.py`

## Boundary

- 当前只证明 repo-side `result.json + projection markdown + artifact + evidence_index` parity 闭环
- 当前没有把仓库升级为 `platform compatibility green`
- 当前没有把仓库升级为 `live accepted`
- 当前没有改 `compatibility_projection_ref` / `lane` 字段名
- 当前没有让 execution-critical markdown override / `verification_commands` 驱动真实 host_local 行为
- 当前没有进入 Hermes parity、historical snapshot mapping、planner/review adapter、remote_non_gui、vm_gui

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_agentbridge_intake.py runtime/host-orchestrator/tests/test_wave1_execution.py`：pass
- `uv run --project .\runtime\host-orchestrator python -m pytest`：pass（29 passed）
- `python .\scripts\verify-planning-status.py`：pass
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit -Json`：pass
