# plugins

- 仓路径：`D:\CODE\external\local-ai-dev-orchestrator-references\plugins`
- 当前本机锚点：`main @ d6169bef12`

## 为什么保留

这是当前 `Codex plugin` 打包方式的官方示例面。

它的价值主要在于：

- `skills/`、`.codex-plugin/plugin.json`、`.mcp.json`、`.app.json`、`hooks.json` 现在被放在同一个 plugin bundle 里对照
- 它能避免继续把已经 deprecated 的 `openai/skills` 当成当前主入口

## 什么时候先看它

- 要把本机经验沉淀成 skill-only plugin 时
- 要判断某个 `Codex` 扩展应该落在 skill、hook、MCP 还是 app surface 时

## 什么时候不要扩大到它

- 纯 MCP 协议语义判断，不要先跳到这里
- 纯 Hermes 兼容线运行时问题，也不该先从这里排查
