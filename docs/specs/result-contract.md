# Canonical Result Contract

## 目的

定义正式 `result.json` 以及相关必备运行工件。

## 当前事实边界

- `.ai/runs/<run_id>/<task_id>/result.json` 是当前正式 result 主体
- `.ai/runs/<run_id>/<task_id>/dispatch_state.json` 是当前 runtime ledger companion
- `AgentBridge results/*.md` 当前仍是 compatibility projection
- repo-side 当前已验证 `AgentBridge/tasks/*.md -> host_local -> result.json -> AgentBridge/results/*.md` 的 projection parity 闭环
- repo-side 当前已允许 planner handoff 任务在未接 live planner 时写出 `waiting_handoff` 正式结果
- repo-side 当前已允许 review-gated 任务在 worker / verification 完成后写出 `needs_review` 正式结果
- repo-side 当前已让 `cleanup_status` 反映最小 cleanup truth：repo-root inline task 为 `inline_only`；runtime-managed clean isolated worktree 为 `cleaned`；需要人工保留的 isolated worktree 继续保持 `deferred`；`git worktree remove` 失败时写 `cleanup_failed`
- 低风险写任务当前可在无额外阻断 review 的情况下直接完成；medium/high/critical 风险、policy surface、或 force-on review 仍会停在 `needs_review`
- 当前代码层字段名仍是 `lane`
- 当前字段名仍是 `compatibility_projection_ref`

## 必填字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `task_id` | string | 对应任务 ID |
| `run_id` | string | 本次运行 ID |
| `attempt` | integer | 第几次尝试 |
| `worker_kind` | enum | 走哪条 adapter 路径 |
| `worker_profile` | string | `.ai/config/workers.yaml` 中的具名配置档 |
| `lane` | enum | 实际执行 lane |
| `sandbox_profile` | string | 实际沙箱档 |
| `network_profile` | string | 实际网络档 |
| `status` | enum | `succeeded / failed / blocked / waiting_handoff / needs_review` |
| `started_at` | string | ISO8601 |
| `finished_at` | string | ISO8601 |
| `stdout_log` | string | `stdout.log` 相对路径 |
| `stderr_log` | string | `stderr.log` 相对路径 |
| `verification_summary_ref` | string | `verification_summary.json` 相对路径 |
| `cost_summary` | string | `cost_summary.json` 相对路径 |
| `termination_reason` | string | 退出原因 |
| `cleanup_status` | enum | `deferred / inline_only / cleaned / cleanup_failed` |
| `cleanup_owner` | string | 由谁负责 cleanup |
| `status_reason` | string | 结构化状态原因文本 |
| `dispatch_state_ref` | string | `dispatch_state.json` 相对路径 |
| `artifacts` | string[] | 工件相对路径 |
| `compatibility_projection_ref` | string \| null | markdown projection 相对路径 |
| `handoff_required` | boolean | 是否需要人工接管 |
| `next_action` | string | 下一步动作 |

## 目标态与迁移窗口

目标态：

- AgentBridge result / review 可以与 canonical result surface 做更完整的稳定 round-trip
- verification 输出由真实 gate executor 驱动
- 若 parity 足够稳定，再评估 schema rename

迁移窗口：

- 在 Phase E parity 绿之前，`compatibility_projection_ref` 不改名
- 在同一时间窗之前，`lane` 不提前改成 `execution_lane`
- truth reset 只允许补充说明，不允许把这些改名写成当前事实

## Dispatch State Ledger

`dispatch_state.json` 当前记录比 `result.json` 更细的运行时状态：

- `queued`
- `running`
- `input_required`
- `waiting_handoff`
- `needs_review`
- `completed`
- `failed`
- `cancelled`
- `stale`
- `resumed`

当前 repo-side runtime 已稳定写出的主路径是：

- `running`
- `waiting_handoff`
- `needs_review`
- `completed`
- `failed`

`queued / input_required / cancelled / stale / resumed` 当前先保留为 schema 与 future lifecycle ops 预留状态；不能把它们写成“已经 live 证明”。

## Cleanup Truth

- `cleanup_status` 只反映 cleanup 结果，不代表 branch 已被删除
- `cleanup_owner` 当前会在 `result.json` 与 `dispatch_state.json` 双写；更细的 cleanup 经过仍保留在 `worktree_cleanup` 事件
- `deferred` 当前表示 worktree 被显式保留给后续 review / 调试 / 人工 cleanup；具体原因落在 `worktree_cleanup` 事件
- `cleanup_failed` 当前只用于 cleanup manager 已尝试 remove 但 git remove 命令本身失败的路径

## worker_kind

固定枚举：

- `codex_sdk`
- `codex_exec`
- `scripted`
- `gpt54_direct`
- `claude_glm`

语义：

- `worker_kind` 只描述 adapter 路径
- `worker_profile` 只描述具名配置档
- 两者不可混用
- `scripted` 仅允许作为 repo-side mock / smoke worker_kind；不能支撑 `live accepted`

## verification_summary.json

从 `Phase 1` 起必存在。

当前最小真实 runner 已落地：

- 固定 gate 顺序仍是 `build -> [lint -> typecheck] -> test -> contract -> hotspot`
- 当前只真实执行 `test` 与 `contract`
- `build / lint / typecheck / hotspot` 继续按 `gate_na` 留痕

如果任务当前没有配置 `test` 与 `contract` 真实命令，则仍写出最小文件：

```json
{
  "status": "no_commands_configured",
  "commands_run": []
}
```

如果 `test` 或 `contract` 已配置，则 `verification_summary.json` 必须反映真实执行结果，而不是硬编码默认成功路径。

## cost_summary.json

`Phase 1` 固定采用 token-only 口径：

```json
{
  "mode": "token_only",
  "source": "worker_usage",
  "currency": null,
  "estimated_cost": null
}
```

不在 `Phase 1` 写美元估算，避免第三方网关价格漂移污染事实。

## 双写过渡方案 A

`Phase 1` 期间正式结果以 `result.json` 为主，同时允许写一份兼容 `AgentBridge results/*.md` 投影。

这份 markdown 投影只用于保持现有回归与兼容线不断绿，不改变 `result.json` 的主协议地位。

## Repo-level governance evidence

- `docs/change-evidence/README.md` 只负责 repo-level governance evidence index。
- 它不替代 `.ai/runs/<run_id>/<task_id>/evidence_index.json` 这一类 task-level 正式 evidence。
