# hermes-agent

这个仓是 `Windows 主力机 AI Agent 分层架构 v1.6` 的长期维护仓。

它保存三类内容：

1. 方案定稿：`Codex = 主力执行层`、`Hermes = 隔离学习层`、`PAD = 固定 GUI 补件`、`OpenClaw = 暂缓`
2. 实施与运维：实施计划、任务清单、社区参考源码策略、密钥录入样例
3. 本机验收快照：把 `C:\Users\sciman\Documents\AgentBridge` 当前已验收的安全文件树复制到仓内，便于长期追溯

## 当前真值

- 主链定位：`Codex` 仍是唯一允许直接碰 Windows 主桌面的 agent
- `Hermes` 只做隔离学习层，通过 `AgentBridge` 文件桥生成任务、吸收结果、产出技能草稿和记忆提升
- `Hermes` 当前运行方式：`Docker Desktop + WSL2 backend + 按需 CLI 容器`
- v1 目标固定为：人工触发的批量学习闭环，而不是实时自进化、常驻学习或桌面控制
- 当前 live 运行面仍在：`C:\Users\sciman\Documents\AgentBridge`
- 当前维护仓在：`D:\CODE\hermes-agent`

## 仓内结构

- [docs/Windows主力机-AI-Agent-分层架构-v1.6.md](D:/CODE/hermes-agent/docs/Windows主力机-AI-Agent-分层架构-v1.6.md)：方案定稿
- [docs/实施计划.md](D:/CODE/hermes-agent/docs/实施计划.md)：分阶段实施与当前状态
- [docs/任务清单.md](D:/CODE/hermes-agent/docs/任务清单.md)：后续维护任务与升级门禁
- [docs/社区参考源码策略.md](D:/CODE/hermes-agent/docs/社区参考源码策略.md)：社区参考仓应否拉取、放哪里、如何更新
- [docs/参考项目清单.md](D:/CODE/hermes-agent/docs/参考项目清单.md)：当前已拉取的上游参考源码清单
- [docs/当前交接摘要.md](D:/CODE/hermes-agent/docs/当前交接摘要.md)：当前维护状态的一页交接摘要
- [docs/接手检查单.md](D:/CODE/hermes-agent/docs/接手检查单.md)：下一位接手时的最小检查路径
- [docs/工作交接提示词.md](D:/CODE/hermes-agent/docs/工作交接提示词.md)：可直接复制给下一位 agent 的提示词
- [docs/交接摘要模板.md](D:/CODE/hermes-agent/docs/交接摘要模板.md)：后续交接时可复用模板
- [references/README.md](D:/CODE/hermes-agent/references/README.md)：参考源码目录策略入口
- [snapshots/agentbridge-20260628/README.md](D:/CODE/hermes-agent/snapshots/agentbridge-20260628/README.md)：已验收 `AgentBridge` 快照说明
- `snapshots/agentbridge-20260628/`：当前可公开提交的 `AgentBridge` 配置、脚本、文档、样例任务/结果、日志与快照元数据
- `private-local/`：只在本机保存、不进入 git 的私有运行数据

## 密钥与私有数据边界

以下内容允许保存在本机，但不进入 git：

- 根目录真实 `.env`
- `Hermes` volume 备份
- 任何可能包含运行态认证信息、会话状态或供应商密钥的数据

当前仓通过以下方式避免误提交：

- `.env` 被 `.gitignore` 排除
- `private-local/` 默认整体排除
- 仅提交 `.env.example` 作为格式样例

## 社区参考源码放置结论

应该拉，但不应混在本仓。

推荐放在 `D:\CODE\external\hermes-agent-references`，而不是 `D:\CODE\hermes-agent` 内部。原因很简单：

- 维护仓要保持“决策、计划、快照、脚本索引”的干净边界
- 上游参考仓会频繁更新，混入本仓后会迅速把维护历史污染成 vendor 历史
- 后续拉官方更新、做 diff、切换 tag、保留上游 git history，都更适合在 `external` 区完成

当前已落地的具体清单见 [docs/参考项目清单.md](D:/CODE/hermes-agent/docs/参考项目清单.md)，目录现场索引见 [D:\CODE\external\hermes-agent-references\README.md](D:/CODE/external/hermes-agent-references/README.md)。

## 日常维护入口

如果以后要继续推进这条线，建议先读：

1. [docs/Windows主力机-AI-Agent-分层架构-v1.6.md](D:/CODE/hermes-agent/docs/Windows主力机-AI-Agent-分层架构-v1.6.md)
2. [docs/实施计划.md](D:/CODE/hermes-agent/docs/实施计划.md)
3. [docs/当前交接摘要.md](D:/CODE/hermes-agent/docs/当前交接摘要.md)
4. [docs/接手检查单.md](D:/CODE/hermes-agent/docs/接手检查单.md)
5. [snapshots/agentbridge-20260628/docs/implementation-status.md](D:/CODE/hermes-agent/snapshots/agentbridge-20260628/docs/implementation-status.md)
6. [snapshots/agentbridge-20260628/docs/中文操作说明.md](D:/CODE/hermes-agent/snapshots/agentbridge-20260628/docs/中文操作说明.md)
