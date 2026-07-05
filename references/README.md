# references

这个目录只存“参考策略、观察记录、刷新索引和 machine-readable shelf manifest”，不存上游源码本体。

大多数上游参考源码当前统一放在：

- `D:\CODE\external\local-ai-dev-orchestrator-references`

治理 companion 单独保留在：

- `D:\CODE\governed-ai-coding-runtime`

当前分层口径：

- `core-mainline`：`codex`、`plugins`、`modelcontextprotocol`、`servers`
- `secondary-mainline`：`openai-agents-python`
- `governance-sidecar`：`governed-ai-coding-runtime`
- `compatibility`：`hermes-agent`
- `archive-on-demand`：`skills`、`hermes-agent-self-evolution`、`openclaw`
- `conditional-not-cloned`：`claude-code`

QQ / OneBot / IM 渠道层项目如 `AstrBot`、`NapCat-Docker`、`NapCatQQ`、`aiocqhttp` 不应并入这里，继续复用它们自己的外部参考架。

本目录内的当前入口：

- [reference-shelf.manifest.json](D:/CODE/local-ai-dev-orchestrator/references/reference-shelf.manifest.json)：参考架根路径、默认刷新集合和分层真源
- [observations/README.md](D:/CODE/local-ai-dev-orchestrator/references/observations/README.md)：每个参考仓“为什么本机仍要保留它”的短观察记录
- [updates/README.md](D:/CODE/local-ai-dev-orchestrator/references/updates/README.md)：批量刷新参考仓后的历史摘要与稳定入口
- [observations/governed-ai-coding-runtime.md](D:/CODE/local-ai-dev-orchestrator/references/observations/governed-ai-coding-runtime.md)：治理 sidecar companion 的使用边界
- [docs/社区参考源码策略.md](D:/CODE/local-ai-dev-orchestrator/docs/社区参考源码策略.md)
- [docs/参考项目清单.md](D:/CODE/local-ai-dev-orchestrator/docs/参考项目清单.md)
