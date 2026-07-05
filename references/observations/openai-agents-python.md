# openai-agents-python

- 仓路径：`D:\CODE\external\local-ai-dev-orchestrator-references\openai-agents-python`
- 当前本机锚点：`main @ 1643dbe617`

## 为什么保留

这是 `Direct GPT / multi-agent orchestration` 这条主线最接近的官方 Python 参考面之一。

保留它的主要价值：

- `handoffs`、`guardrails`、`sessions`、`human in the loop`、`sandbox agents` 与本仓后续 `planner/review/handoff_records` 设计高度相关
- 它能帮助判断哪些 orchestration 能力应该由 SDK 承担，哪些仍应留在 repo 自己的 control plane

## 什么时候先看它

- 要推进 `gpt54_direct` planner adapter、handoff、session 管理或长任务 sandbox 语义时
- 要评估“直接 Responses API 包装”与“更高层 agent SDK”边界时

## 什么时候不要扩大到它

- 当前 `Codex` CLI / App / AGENTS / hooks 行为判断，不要先跳到这里
- 当前 Hermes 兼容线 bring-up 或 boundary 问题，也不该先从这里排查
