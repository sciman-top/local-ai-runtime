# hermes-agent-self-evolution

- 仓路径：`D:\CODE\external\local-ai-dev-orchestrator-references\hermes-agent-self-evolution`
- 当前本机锚点：`main @ 0a929e3aa2`

## 为什么保留

这是“隔离学习层后续怎么增强”的储备真值，不是当前 v1 bring-up 的直接依赖。

保留它的原因主要是两点：

- 以后如果真要把 `skills-drafts/`、`memory-promotions/` 走向更系统的学习闭环，需要一个上游参考面
- 它能帮助区分“当前 v1 只做人工触发批量学习”与“未来可能的自进化路线”

## 什么时候先看它

- 用户明确要推进学习层、自我改写、技能吸收或记忆提升的下一阶段时
- 需要判断某个新需求是不是已经越过当前 v1 边界时

## 什么时候不要扩大到它

- 当前 `Docker Desktop + WSL2 + AgentBridge` bring-up、boundary、snapshot 问题，不要先跳到这里
- 这不是当前主链运行失败时的第一排查仓
