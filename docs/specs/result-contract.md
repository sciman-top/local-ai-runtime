# Canonical Result Contract

## 目的

定义正式 `result.json` 以及相关必备运行工件。

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
| `artifacts` | string[] | 工件相对路径 |
| `handoff_required` | boolean | 是否需要人工接管 |
| `next_action` | string | 下一步动作 |

## worker_kind

固定枚举：

- `codex_sdk`
- `codex_exec`
- `gpt54_direct`
- `claude_glm`

语义：

- `worker_kind` 只描述 adapter 路径
- `worker_profile` 只描述具名配置档
- 两者不可混用

## verification_summary.json

从 `Phase 1` 起必存在。

如果当前任务没有配置真实验证命令，也必须写出最小文件：

```json
{
  "status": "no_commands_configured",
  "commands_run": []
}
```

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
