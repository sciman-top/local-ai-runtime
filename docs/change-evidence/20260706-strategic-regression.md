# 2026-07-06 Strategic Regression

## 为什么回调

本次落盘把仓库主叙事从“generic orchestrator 主线 + Hermes compatibility lane”回调为 `Hermes -> AgentBridge -> Codex` 三层闭环。

回调原因不是否认当前 repo 代码事实，而是把产品终态与当前 truth boundary 分层写清：

- Hermes 不再只被写成兼容残留
- AgentBridge 恢复为跨层主契约的目标态
- Codex 继续作为当前执行层主入口

## 本次同步改写的 authoritative files

- `README.md`
- `docs/README.md`
- `docs/product/orchestrator-prd.md`
- `docs/architecture/orchestrator-target-architecture.md`
- `docs/architecture/planning-status.json`
- `docs/roadmap/orchestrator-roadmap.md`
- `docs/plans/orchestrator-implementation-plan.md`
- `docs/backlog/orchestrator-task-list.md`
- `docs/specs/task-contract.md`
- `docs/specs/result-contract.md`
- `docs/specs/state-and-db.md`
- `docs/migrations/hermes-compatibility-demotion.md`
- `AGENTS.md`
- `docs/architecture/next-work-selection-policy.json`
- `scripts/verify-planning-status.py`

## 刻意保留的当前 truth

- canonical `JSON/YAML` intake 仍是当前运行主路径
- `.ai/runs/<run_id>/<task_id>/result.json` 仍是正式 task-level evidence 主体
- `AgentBridge results/*.md` 当前仍是 compatibility projection
- 当前只落地 `host_local` 内核；`remote_non_gui / vm_gui` 仍未实现 runner

## 刻意没有在本次落盘中反转或改名的内容

- 没有把 `AgentBridge-first intake` 写成已完成
- 没有把 `compatibility_projection_ref` 改成 `agentbridge_result_ref`
- 没有把 `lane` 改成 `execution_lane`
- 没有把 `resource_leases` / `worker_sessions` 写成当前已实现控制面

## 待验证设计

- `host_local` 正确性修复与最小 lease helpers
- verification runner
- AgentBridge-first intake 无损映射
- Hermes parity / container lifecycle
- `resource_leases` / `worker_sessions`
- `remote_non_gui` 与条件晋升后的 `vm_gui`

## 本次切片边界

本次只落 repo-side 文档、spec、policy、verifier 与 evidence 同步，不视为：

- Phase B/C/D runtime code 已完成
- live accepted 已达成
- parity green 已达成

## Verification

- `python .\scripts\verify-planning-status.py`：pass
- `python .\scripts\select-next-work.py`：pass，`next_action = promote_phase1_execution`
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`：pass
- 当前 `build` / `hotspot` 仍是 `gate_na`，但 `test`、`contract/invariant`、`Docs`、`Scripts`、`git diff --check` 全绿
