# 2026-07-06 Host Local Robustness And Lease Helpers

## 变更内容

本次切片实现了 strategic return 之后的第一个 runtime 落点：

- 在现有 `leases` 表上补齐 `acquire_lease / renew_lease / release_lease / reap_stale_leases`
- `HostLocalRunner` 现在会为任务获取 lease，并在成功或失败后释放 lease
- `HostLocalRunner` 现在会在 worker 或结果写盘异常时：
  - 把 `runtime_tasks.state` 置为 `failed`
  - 把 `workers.status` 恢复为 `idle`
  - 落一条 `task_failed` 事件
- `codex exec` fallback 的子进程执行现在走 `process_guard`，为 timeout 和子进程树残留回收提供统一入口

## 未改变的边界

- canonical `JSON/YAML` intake 仍是当前主路径
- `.ai/runs/<run_id>/<task_id>/result.json` 仍是正式 evidence 主体
- `AgentBridge results/*.md` 当前仍是 compatibility projection
- 当前并未实现 verification runner，也未接线 AgentBridge-first intake

## 代码落点

- `runtime/host-orchestrator/src/host_orchestrator/db.py`
- `runtime/host-orchestrator/src/host_orchestrator/host_local.py`
- `runtime/host-orchestrator/src/host_orchestrator/process_guard.py`
- `runtime/host-orchestrator/src/host_orchestrator/exec_fallback.py`
- `runtime/host-orchestrator/tests/test_db.py`
- `runtime/host-orchestrator/tests/test_crash_recovery.py`
- `runtime/host-orchestrator/tests/test_worker_exec.py`

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_db.py -q`：pass
- `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_crash_recovery.py -q`：pass
- `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_worker_exec.py -q`：pass
- `uv run --project .\runtime\host-orchestrator python -m pytest`：pass（21 passed）
