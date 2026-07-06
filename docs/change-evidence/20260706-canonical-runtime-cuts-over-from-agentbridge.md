# 2026-07-06 Canonical Runtime Cuts Over From AgentBridge

## Slice

- `HostLocalRunner` 主协议切到 canonical `task.json` / `task.yaml`
- 正式结果改为 `.ai/runs/<run_id>/<task_id>/result.json`
- markdown `results/*.md` 只保留为 compatibility projection

## Evidence

- `runtime/host-orchestrator/tests/test_wave1_execution.py`
- `runtime/host-orchestrator/src/host_orchestrator/host_local.py`
- `runtime/host-orchestrator/src/host_orchestrator/agentbridge.py`

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_wave1_execution.py -q`

## Boundary

这次切片只证明 repo-side canonical runtime 已取代 AgentBridge markdown 主协议；不等于 live accepted。
