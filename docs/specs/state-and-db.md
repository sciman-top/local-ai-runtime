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

## 当前 runtime_tasks 索引面

`runtime_tasks` 当前已索引以下关键字段：

- `task_id`
- `run_id`
- `attempt`
- `state`
- `state_reason`
- `execution_lane`
- `worker_profile`
- `next_action`
- `cleanup_status`
- `cleanup_owner`
- `created_at`
- `updated_at`
- `result_path`
- `dispatch_state_path`

语义：

- `state` 是 DB 级调度视角
- `state_reason` 是当前阶段的结构化说明
- `next_action` 给 operator / downstream adapter 一个明确下一步
- `cleanup_status / cleanup_owner` 让 worktree closeout 不再只停在事件文本
- `dispatch_state_path` 把 DB 与 `.ai/runs/<run_id>/<task_id>/dispatch_state.json` runtime ledger 对齐

## 当前 dispatch_state runtime ledger

repo-side 当前已把 `dispatch_state.json` 升级成 runtime-backed ledger，路径固定为：

- `.ai/runs/<run_id>/<task_id>/dispatch_state.json`

当前 ledger 至少承接：

- `run_id`
- `attempt`
- `task_id`
- `status`
- `status_reason`
- `next_action`
- `cleanup_status`
- `cleanup_owner`
- `heartbeat_at`
- `worker_profile`
- `execution_lane`
- `allowed_paths / forbidden_paths / worktree_path / branch_name`
- `last_result_ref / verification_summary_ref / evidence_index_ref`

当前 repo-side runtime 已稳定写出的主路径状态是：

- `running`
- `waiting_handoff`
- `needs_review`
- `completed`
- `failed`

`queued / input_required / cancelled / stale / resumed` 当前先保留为 schema 与 future lifecycle ops 预留状态，不应写成“已完成 live 行为”。

## 当前 events 责任

`events` 继续承担可回放轨迹：

- `task_started`
- `task_completed`
- `task_failed`
- `worker_started`
- `worker_completed`
- `worker_failed`
- `worktree_prepared`
- `worktree_cleanup`

当前做法是：

- DB 保留调度索引
- `dispatch_state.json` 保留更细的运行时阶段
- `result.json` 继续作为正式 task-level outcome

## Phase 1 口径

`Phase 1` 当前已满足：

- 默认 layout 迁到 `.ai/state/control-plane.db`
- 现有 5 表继续可用
- `leases` 已具备 acquire / renew / release / reap 最小函数
- `result.json` 与 `evidence_index.json` 可以引用调度状态
- `run_id / attempt / handoff_required / next_action / cleanup_owner / cleanup_status / status_reason` 的最小契约已 materialize
- runtime-backed `dispatch_state.json` ledger 已与 `runtime_tasks` 建立索引关系

## Phase 5 口径

只有在以下条件满足后，才进入正式 multi-repo/multi-worker 控制面扩展：

- canonical schema 已稳定
- 真实 SDK 垂直切片已通过
- planner/review 派生逻辑已固化
- worktree manager、cleanup manager、以及 runtime ledger 已存在

## 候选扩展表（尚未落地）

以下扩展当前仍是设计提议，不是已实现 truth：

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
