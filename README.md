# hermes-agent

这个仓是 `Windows 主力机 AI Agent 分层架构 v1.6` 的长期维护仓，也是 `Hermes v2` 高自治终态文档的正式落盘仓。

它保存四类内容：

1. 方案定稿：`Codex = 主力执行层`、`Hermes = 隔离学习层`、`PAD = 固定 GUI 补件`、`OpenClaw = 暂缓`
2. 实施与运维：实施计划、任务清单、社区参考源码策略、密钥录入样例
3. 本机验收快照：把 `C:\Users\sciman\Documents\AgentBridge` 当前已验收的安全文件树复制到仓内，便于长期追溯
4. v2 终态文档：高自治四平面、路线图、实施规格、接口规格、runner 协议、测试规格

## 当前真值

当前采用双层真相：

- `active truth`：当前已验收的 `v1.6` 可审计批处理闭环
- `target truth`：`Hermes v2` 高自治四平面终态
- 当前稳定口径以 [docs/实施计划.md](D:/CODE/hermes-agent/docs/实施计划.md) 和 [docs/当前交接摘要.md](D:/CODE/hermes-agent/docs/当前交接摘要.md) 为准
- 当前短结论：
  - `Phase 0`：已收口到 `P0-2 accepted + P0-1 still blocked + P0-3 platform_na`
  - `Phase 1 / Wave 1`：repo-side 骨架、smoke、structured usage、worktree 收口已完成，但仍未做 live `Codex SDK` 真机执行验收
  - 当前 live 运行面仍在 `C:\Users\sciman\Documents\AgentBridge`
  - 当前 boundary 证据锚点仍是 [verify-hermes-boundary-20260628-225841-414.json](D:/CODE/hermes-agent/snapshots/agentbridge-20260628/docs/verify-hermes-boundary-20260628-225841-414.json)
  - 当前 `Phase 1` 探针报告锚点仍是 [phase1-capability-probe-report-20260628-143744.md](D:/CODE/hermes-agent/docs/phase1-capability-probe-report-20260628-143744.md)

## 仓内结构

- [docs/Windows主力机-AI-Agent-分层架构-v1.6.md](D:/CODE/hermes-agent/docs/Windows主力机-AI-Agent-分层架构-v1.6.md)：方案定稿
- [docs/Hermes-v2-终态收口-20260628.md](D:/CODE/hermes-agent/docs/Hermes-v2-终态收口-20260628.md)：v2 `target truth`
- [docs/Hermes-v2-路线图.md](D:/CODE/hermes-agent/docs/Hermes-v2-路线图.md)：v2 波次与并行关系
- [docs/Hermes-v2-实施规格.md](D:/CODE/hermes-agent/docs/Hermes-v2-实施规格.md)：目录、模块、进程、路径
- [docs/Hermes-v2-接口规格.md](D:/CODE/hermes-agent/docs/Hermes-v2-接口规格.md)：字段、SQLite、状态机
- [docs/Hermes-v2-runner-协议.md](D:/CODE/hermes-agent/docs/Hermes-v2-runner-%E5%8D%8F%E8%AE%AE.md)：三条 lane 的任务包与回写协议
- [docs/Hermes-v2-测试规格.md](D:/CODE/hermes-agent/docs/Hermes-v2-%E6%B5%8B%E8%AF%95%E8%A7%84%E6%A0%BC.md)：Wave 0-5 测试矩阵
- [docs/实施计划.md](D:/CODE/hermes-agent/docs/实施计划.md)：分阶段实施与当前状态
- [docs/任务清单.md](D:/CODE/hermes-agent/docs/任务清单.md)：后续维护任务与升级门禁
- [docs/社区参考源码策略.md](D:/CODE/hermes-agent/docs/社区参考源码策略.md)：社区参考仓应否拉取、放哪里、如何更新
- [docs/参考项目清单.md](D:/CODE/hermes-agent/docs/参考项目清单.md)：当前已拉取的上游参考源码清单
- [docs/当前交接摘要.md](D:/CODE/hermes-agent/docs/当前交接摘要.md)：当前维护状态的一页交接摘要
- [docs/AgentBridge-迁移与复用-runbook.md](D:/CODE/hermes-agent/docs/AgentBridge-%E8%BF%81%E7%A7%BB%E4%B8%8E%E5%A4%8D%E7%94%A8-runbook.md)：以后迁移 live 运行面、跨机复用、交付他人时的正式 runbook
- [docs/接手检查单.md](D:/CODE/hermes-agent/docs/接手检查单.md)：下一位接手时的最小检查路径
- [docs/工作交接提示词.md](D:/CODE/hermes-agent/docs/工作交接提示词.md)：可直接复制给下一位 agent 的提示词
- [docs/交接摘要模板.md](D:/CODE/hermes-agent/docs/交接摘要模板.md)：后续交接时可复用模板
- [references/README.md](D:/CODE/hermes-agent/references/README.md)：参考源码目录策略入口
- [references/observations/README.md](D:/CODE/hermes-agent/references/observations/README.md)：各参考仓保留理由与使用边界
- [references/updates/reference-refresh-latest.md](D:/CODE/hermes-agent/references/updates/reference-refresh-latest.md)：最新一次参考仓刷新与差异摘要
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

当前维护口径已经收紧为三层：

- `core`：`hermes-agent`、`codex`、`modelcontextprotocol`、`servers`
- `secondary`：`skills`、`hermes-agent-self-evolution`
- `conditional`：`openclaw`

默认刷新只覆盖 `core`。`NapCat/AstrBot` 这类 QQ 渠道层项目继续复用它们自己的专属参考架，不并入这里。

## 日常维护入口

如果以后要继续推进这条线，建议先读：

1. [docs/Windows主力机-AI-Agent-分层架构-v1.6.md](D:/CODE/hermes-agent/docs/Windows主力机-AI-Agent-分层架构-v1.6.md)
2. [docs/Hermes-v2-终态收口-20260628.md](D:/CODE/hermes-agent/docs/Hermes-v2-终态收口-20260628.md)
3. [docs/实施计划.md](D:/CODE/hermes-agent/docs/实施计划.md)
4. [docs/当前交接摘要.md](D:/CODE/hermes-agent/docs/当前交接摘要.md)
5. [docs/AgentBridge-迁移与复用-runbook.md](D:/CODE/hermes-agent/docs/AgentBridge-%E8%BF%81%E7%A7%BB%E4%B8%8E%E5%A4%8D%E7%94%A8-runbook.md)
6. [docs/接手检查单.md](D:/CODE/hermes-agent/docs/接手检查单.md)
7. [snapshots/agentbridge-20260628/docs/implementation-status.md](D:/CODE/hermes-agent/snapshots/agentbridge-20260628/docs/implementation-status.md)
8. [snapshots/agentbridge-20260628/docs/中文操作说明.md](D:/CODE/hermes-agent/snapshots/agentbridge-20260628/docs/中文操作说明.md)
9. [references/updates/reference-refresh-latest.md](D:/CODE/hermes-agent/references/updates/reference-refresh-latest.md)
