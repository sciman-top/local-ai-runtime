# 2026-07-06 Verification Runner Minimal Gates

## 变更内容

本次切片把 `verification_summary.json` 从硬编码默认成功路径升级为最小真实 gate executor。

当前行为：

- 固定 gate 顺序仍是 `build -> [lint -> typecheck] -> test -> contract -> hotspot`
- 当前只真实执行 `test` 与 `contract`
- `build / lint / typecheck / hotspot` 继续按 `gate_na` 留痕
- 若 `test` 与 `contract` 都未配置，则 `verification_summary.json.status = no_commands_configured`

## 代码落点

- `runtime/host-orchestrator/src/host_orchestrator/verification.py`
- `runtime/host-orchestrator/src/host_orchestrator/host_local.py`
- `runtime/host-orchestrator/src/host_orchestrator/canonical_result.py`
- `runtime/host-orchestrator/tests/test_verification.py`
- `runtime/host-orchestrator/tests/test_wave1_execution.py`

## 未改变的边界

- 当前没有把 `build / lint / typecheck / hotspot` 提升为真实 gate
- 当前没有实现 AgentBridge-first intake
- 当前没有改 `compatibility_projection_ref` / `lane` 字段名

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_verification.py -q`：pass
- `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_wave1_execution.py -q`：pass
- `uv run --project .\runtime\host-orchestrator python -m pytest`：pass（24 passed）
