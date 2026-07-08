# 20260708 Runtime V2 K2-T04 Scheduling Review Policy Gates

## Goal

把 `runtime_v2` 的 `K2-T04` autonomous scheduling、review / policy receipt、bounded review sidecar hook、pre-worker policy guard 深化落到代码、CLI、测试、spec 与证据面。

## Repo-Side Done

- `tasks.task_path` 已成为 v2 control plane 的一等字段，并通过初始化时补列兼容既有 DB
- `RuntimeV2Runner.run_task()` 会在注册/运行路径持久化 repo-relative task path
- `storage.ready_blocked_task_paths()` 会筛选依赖已满足的 dependency-blocked task
- `RuntimeV2Runner.run_ready_blocked_tasks()` 会重新加载对应 canonical task 并创建新的 attempt
- `host-orchestrator --run-ready-blocked-v2` 已接线，并输出 `continued_count` 与续跑结果摘要
- 回归测试覆盖 runner 与 CLI 两层，并验证非依赖原因的 `blocked` 不会被自动续跑
- v2 `review_result.json` 已补 `blocking_reasons[] / changed_paths / gate_failed / policy_surface_touched`
- 回归测试覆盖 risk-level review receipt 与 policy-surface review receipt
- `RuntimeV2Runner` 已支持显式 `review_worker`，并能在配置了 review worker profile 时 materialize bounded sidecar receipt
- sidecar 缺失、无 primary worker summary、或 sidecar 失败时，v2 仍 fallback 到 repo-side blocking receipt
- pre-worker policy guard 已覆盖 network/profile、non-host-local lane、GUI requirement、sensitive write scope 四类 fail-closed blocked 条件
- policy guard 命中时不会执行 worker，不会占用 admission slot，并会在 `result.json` / `gate_report.json` 写出结构化 `policy_guard_reasons`
- `docs/architecture/planning-status.json` 已更新 proof_ref 与 Kernel V2 摘要，但 `current_active_queue` 与 selector 保持不变

## Still Open

- `K2-T04` 按当前 scoped deepening 已完成；后续进入 `K2-T05` trace / eval / regression fixture 与 `K2-T06` cutover drill
- `runtime_v2` 仍是 experimental dual-track，默认入口仍未从 v1 切换
- `planning-status.current_active_queue` 仍保持 `PHASE-1-VERTICAL-SLICE`
- 本次没有推进 `remote_non_gui` / `vm_gui` runner wiring，也不声明 `live accepted`

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_runtime_v2.py`
- `uv run --project .\runtime\host-orchestrator python -m pytest`
- `python .\scripts\verify-planning-status.py`
- `python .\scripts\select-next-work.py`
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`
- `git diff --check`

## Rollback

用 git 回滚本切片涉及的同批 diff：

- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/storage.py`
- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/runner.py`
- `runtime/host-orchestrator/src/host_orchestrator/cli.py`
- `runtime/host-orchestrator/tests/test_runtime_v2.py`
- `docs/specs/runtime-v2-kernel.md`
- `docs/roadmap/orchestrator-roadmap.md`
- `docs/plans/orchestrator-implementation-plan.md`
- `docs/backlog/orchestrator-task-list.md`
- `docs/architecture/planning-status.json`
- `docs/change-evidence/README.md`
- `docs/change-evidence/20260708-runtime-v2-k2-t04-scheduling-review-policy-gates.md`
