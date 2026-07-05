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
- 所有状态演进都通过 canonical contract 与 verifier 驱动

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
- `result.json` 与 `evidence_index.json` 可以引用调度状态

## Phase 5 口径

只有在以下条件满足后，才进入正式 multi-repo/multi-worker 控制面扩展：

- canonical schema 已稳定
- 真实 SDK 垂直切片已通过
- planner/review 派生逻辑已固化
- worktree manager、cleanup manager 已存在
