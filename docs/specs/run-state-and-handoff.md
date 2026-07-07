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

## Resume Point

`resume_point` 当前最小枚举：

- `task_intake`
- `worker_execution`
- `verification`
- `handoff`
- `cleanup`

`Phase 1` 可以暂不实现恢复动作，但字段语义必须先固定。

## Retry Rewind

`retry_rewind` 表示下一次 attempt 必须回退到的最小一致性边界。

当前最小规则：

- canonical task intake 失败 -> rewind 到 `task_intake`
- worker 失败但 task contract 仍有效 -> rewind 到 `worker_execution`
- verification 输出失真 -> rewind 到 `verification`

## Handoff

`handoff_required = true` 时，至少要留下：

- `result.json`
- `verification_summary.json`
- `cost_summary.json`
- `evidence_index.json`
- 明确的 `next_action`

如果进入 review / operator handoff，最小工件集合不能低于以上四件。

## Cleanup Ownership

当前约束：

- task-level evidence 默认不内联删除
- `cleanup_status` 必须留在正式 result 中
- isolated worktree 的 `cleanup_owner` 当前落在 `worktree_cleanup` 事件载荷中：自动 remove 成功时归 `runtime`，显式保留或 remove 失败时归 `operator`
- branch deletion 当前仍不属于 runtime 自动 cleanup 范围

## Trajectory And Replay

最低 replay 要求：

- DB 中至少保留 `task_started` / `task_completed` 事件
- `runtime_tasks.result_path` 指向正式 `result.json`
- `evidence_index.json` 可枚举本次运行的重要工件

这保证 Phase 1-4 即便没有完整 replay engine，也能回放最小运行轨迹
