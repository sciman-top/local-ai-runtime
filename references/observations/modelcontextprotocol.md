# modelcontextprotocol

- 仓路径：`D:\CODE\external\local-ai-dev-orchestrator-references\modelcontextprotocol`
- 当前本机锚点：`main @ 60dc69e9a9`

## 为什么保留

这是 MCP 协议层本体真值。当前主链虽然没有把它作为首要实施面，但后续只要涉及 tool / server / connector 约束，就需要它来划清协议边界。

## 什么时候先看它

- 需要确认某个 MCP capability、message shape、协议约束时
- 需要区分“工具实现问题”与“协议本身不支持”时

## 什么时候不要扩大到它

- 纯 Hermes 容器 bring-up、provider、boundary 问题，不该先看这里
