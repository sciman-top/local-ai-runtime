# State And DB Contract

## 目的

定义 `.ai/state/control-plane.db` 的角色与演进方式。

## 当前保留的 5 表

现有实现已经有 5 表，后续继续演进，不推倒重建：

- `runtime_tasks`
- `leases`
- `workers`
- `route_decisions`
- `events`

## 设计原则

- `queue` 从 `runtime_tasks.state` 派生，不建平行 queue 表
- 不新增 `claims` 表；`leases` 承担 claim / renew / expire 语义
- 如果保留 `claimed`，它只能表示 `leases` 的观察态，不得演变成新的 claims 子系统
- 所有状态演进都通过 canonical contract 与 verifier 驱动
- DB 只承载调度态 / 索引态，不承载 task-level evidence 正文

## 新增 4 表

### task_attempts

职责：

- 记录任务重试历史
- 区分同一 `task_id` 的不同运行 attempt

### review_outcomes

职责：

- 记录 review 结论
- 区分 advisory/blocking

### handoff_records

职责：

- 记录 `waiting_handoff` / `needs_review` 的接管点
- 给 operator 提供下一步动作

### cleanup_records

职责：

- 记录 worktree、branch、artifact cleanup 状态
- 支持 cleanup 幂等

## Phase 1 口径

`Phase 1` 不要求把新增 4 表全部落地，只要求：

- 默认 layout 迁到 `.ai/state/control-plane.db`
- 现有 5 表继续可用
- `leases` 已具备 acquire / renew / release / reap 最小函数
- `result.json` 与 `evidence_index.json` 可以引用调度状态
- `run_id / attempt / handoff_required / next_action` 的最小契约见 `docs/specs/run-state-and-handoff.md`

## Phase 5 口径

只有在以下条件满足后，才进入正式 multi-repo/multi-worker 控制面扩展：

- canonical schema 已稳定
- 真实 SDK 垂直切片已通过
- planner/review 派生逻辑已固化
- worktree manager、cleanup manager 已存在

## 后置扩展（待 Phase E 验证）

以下扩展当前仍是设计提议，不是已实现 truth：

### resource_leases

职责：

- 承接 container / ssh host / vm 这类资源索引态
- 不替代当前 `leases` 表在 `host_local` 上的最小 claim 语义

### worker_sessions

职责：

- 记录长寿命 worker 或 container session 的索引态
- 与 task-level `.ai/runs/<run_id>/<task_id>/` evidence 面保持分层，不承载 task-level evidence 正文
