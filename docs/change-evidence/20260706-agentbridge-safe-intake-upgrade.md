# 2026-07-06 AgentBridge Safe Intake Upgrade

## Slice

- `host_local` 主路径现在可直接接收合规 AgentBridge markdown task
- markdown intake 会先归一化到 repo-owned canonical 默认值
- execution-critical override 与 markdown 侧 `verification_commands` 输入保持 fail-closed

## Code Points

- `runtime/host-orchestrator/src/host_orchestrator/host_local.py`
- `runtime/host-orchestrator/src/host_orchestrator/canonical_task.py`
- `runtime/host-orchestrator/src/host_orchestrator/agentbridge.py`
- `runtime/host-orchestrator/tests/test_agentbridge_intake.py`

## Boundary

- 当前没有完成 AgentBridge round-trip parity
- 当前没有让 markdown front matter 直接驱动 `target_repo`、`write_access`、`execution_lane`、`requires_network` 等 live host_local 行为
- 当前没有让 markdown 侧 `verification_commands` 驱动真实 shell gate 执行
- 当前没有改 `compatibility_projection_ref` / `lane` 字段名

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_agentbridge_intake.py`：pass（5 passed）
- `uv run --project .\runtime\host-orchestrator python -m pytest`：pass（29 passed）
- `python .\scripts\verify-planning-status.py`：pass
- `python .\scripts\select-next-work.py`：pass（`next_action = promote_phase1_execution`）
