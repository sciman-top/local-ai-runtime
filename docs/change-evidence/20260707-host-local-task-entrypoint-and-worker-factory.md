# 2026-07-07 Host-Local Task Entrypoint And Worker Factory

## Slice

- 本次切片把 repo-owned `host_local` task entrypoint 接回当前主运行时
- 目标是让现有 `CodexSdkWorker` 与 `CodexExecFallbackWorker` 真正进入 repo-owned live task entrypoint 的可消费范围，而不是继续停留在 repo-side helper / test-only 形态

## Changes

- 新增 `runtime/host-orchestrator/src/host_orchestrator/worker_factory.py`
  - 当前会按 selected `worker_profile.worker_kind` 物化 live task execution worker
  - 已接线：
    - `codex_sdk` -> `CodexSdkWorker`
    - `codex_exec` -> `CodexExecFallbackWorker`
  - 当前保持 fail-closed：
    - `scripted`
    - `gpt54_direct`
    - `claude_glm`
- 更新 `runtime/host-orchestrator/src/host_orchestrator/host_local.py`
  - `HostLocalRunner` 现在支持懒加载 `worker_factory`
  - planner/capability/quota handoff 仍在 worker 调用前触发，不会因为新增 live entrypoint 而伪装成已执行
- 更新 `runtime/host-orchestrator/src/host_orchestrator/cli.py`
  - 新增 `--run-task`
  - 新增 `--agentbridge-root`
  - 新增 `--worker-profile`
  - 新增 `--run-id`
- 新增 `runtime/host-orchestrator/scripts/run-host-task.ps1`
  - 提供 repo-owned PowerShell 入口包装 `host-orchestrator --run-task`
- 当前 built-in profile 口径：
  - `local_maint` 会直接走 `codex_sdk`
  - `remote_non_gui_probe / vm_gui_probe` 虽然 `worker_kind = codex_exec`，但仍会因为 non-host-local lane 在 worker 前 handoff

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_scaffold.py .\runtime\host-orchestrator\tests\test_wave1_execution.py`
  - `22 passed`
- 覆盖点包括：
  - `RuntimeWorkerFactory` 对 `codex_sdk` 的 client reuse
  - `RuntimeWorkerFactory` 对 `codex_exec` 的 worker materialization
  - unwired worker kinds 的 fail-closed
  - `cli --run-task` 走 repo-owned worker factory
  - pre-worker handoff 触发时不提前实例化 live worker

## Boundary

- 这不是 live planner sidecar 已接线
- 这不是 live heterogeneous review sidecar 已接线
- 这不是 non-host_local runner 已接线
- 这不是 `platform compatibility green`
- 这不是 `live accepted`
- 这只是当前主线 runtime 已具备 repo-owned `host_local` task entrypoint、已直接消费 `local_maint` 的 `codex_sdk` 路径、并在结构上支持 `codex_exec`；built-in non-host-local `codex_exec` profiles 与其他未接线 worker kinds 仍保持 fail-closed 或 handoff 边界
