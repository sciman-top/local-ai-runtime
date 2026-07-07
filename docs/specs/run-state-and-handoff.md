# Run State And Handoff Contract

> Phase Boundary: 这是 `Phase 1-4` 需要的 contract foundation，不是 `Phase 5` 的实现预热，也不改变 `state-and-db.md` 现有的 `Phase 5` 进入条件。

## 目的

定义单次运行、重试、接管与 cleanup 的最小正式字段。

## Core Fields

| 字段 | 说明 |
| --- | --- |
| `run_id` | 一次运行的稳定标识 |
| `attempt` | 同一 `task_id` 的第几次尝试 |
| `resume_point` | 若支持恢复，应从哪个阶段继续 |
| `retry_rewind` | 重试时需要回退到哪个工件/状态边界 |
| `handoff_required` | 是否需要人工或异质 review 接管 |
| `next_action` | 当前运行结束后建议的下一步 |
| `cleanup_owner` | 由谁负责 worktree / artifact cleanup |
| `status_reason` | 当前状态的结构化原因 |
| `route_reason` | 当前 route/worker_profile 选择原因 |
| `dispatch_state_ref` | 关联的 `dispatch_state.json` 路径 |

## Resume Point

`resume_point` 当前最小枚举：

- `task_intake`
- `worker_execution`
- `verification`
- `handoff`
- `cleanup`

当前 repo-side 已提供最小 `resume_task` helper 与 CLI 入口：它会同步更新 `dispatch_state.json`、`runtime_tasks`、清理 active lease、刷新 `heartbeat_at / stale_after`、以及既有 closeout follow-up 口径，但仍不会把 live replay engine 写成已完成。

## Retry Rewind

`retry_rewind` 表示下一次 attempt 必须回退到的最小一致性边界。

当前最小规则：

- canonical task intake 失败 -> rewind 到 `task_intake`
- worker 失败但 task contract 仍有效 -> rewind 到 `worker_execution`
- verification 输出失真 -> rewind 到 `verification`

当前 repo-side 已提供最小 `retry_task` helper 与 CLI 入口：它会递增 `attempt`，记录 `retry_rewind`，清理 active lease，并通过刷新 `heartbeat_at / stale_after` 的 `resumed` 路径留痕；这仍不等于 multi-worker retry scheduler 已落地。

## Handoff

`handoff_required = true` 时，至少要留下：

- `result.json`
- `dispatch_state.json`
- `verification_summary.json`
- `cost_summary.json`
- `evidence_index.json`
- 明确的 `next_action`

如果进入 review / operator handoff，最小工件集合不能低于以上五件。

补充说明：

- planner-gated 路径当前在 live planner sidecar 成功 materialize 时，还会额外写出 `planner_result.json`，并继续停在 `waiting_handoff`
- review-gated 路径当前还会额外写出 `review_result.json`
- 当前 planner/review/completed runtime outcome 还会额外写出 `closeout_bundle.json`
- explicit/default `worker_profile` 选择原因当前会落到 `result.json`、`dispatch_state.json`、以及 `route_decisions`
- 若选中 profile 的 active lease 数超过 `max_active_leases`，当前会在 worker 前 handoff，并仍保留同等最小工件集合
- 若选中 profile 的 `lane != host_local` 而当前 runtime 仍是 `host_local`，当前也会在 worker 前 fail closed 到 handoff，并仍保留同等最小工件集合
- 这些 extra receipts 表达的是 repo-side receipt truth；当前只证明 codex-backed host_local planner sidecar receipt 已接线，不等于 live `Direct GPT-5.4 API` planner、live review sidecar、或 non-host_local runner 已接线

## Cleanup Ownership

当前约束：

- task-level evidence 默认不内联删除
- `cleanup_status` 必须留在正式 result 中
- `cleanup_owner` 当前会在 `result.json` 与 `dispatch_state.json` 双写；更细的 cleanup 经过仍记录在 `worktree_cleanup` 事件载荷中
- `closeout_bundle.json` 当前会把 cleanup truth、review receipt truth、以及 repo-side / live boundary 一并收口
- isolated worktree 自动 remove 成功时归 `runtime`，显式保留或 remove 失败时归 `operator`
- branch deletion 当前仍不属于 runtime 自动 cleanup 范围

## Trajectory And Replay

最低 replay 要求：

- DB 中至少保留 `task_started` / `task_completed` 事件
- `runtime_tasks.result_path` 指向正式 `result.json`
- `runtime_tasks.dispatch_state_path` 指向正式 `dispatch_state.json`
- `evidence_index.json` 可枚举本次运行的重要工件

这保证 Phase 1-4 即便没有完整 replay engine，也能回放最小运行轨迹。
