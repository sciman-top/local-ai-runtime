# codex

- 仓路径：`D:\CODE\external\hermes-agent-references\codex`
- 当前本机锚点：`main @ 328e95110c`

## 为什么保留

这是 `Codex = 主力执行层` 这条主链的行为真值参考。

保留它的价值在于：

- 以后如果 `Codex` 的配置、规则加载、执行边界、工具行为需要对照上游实现，这里是第一源码入口
- 它帮助防止把 Hermes 侧问题误判成 Codex 平台问题，反之亦然

## 什么时候先看它

- 要核对 `Codex` CLI / App / rules / AGENTS 相关行为时
- 要判断“是否应该由 Codex 执行，还是只能留在 Hermes 隔离层”时

## 什么时候不要扩大到它

- 当前 Hermes 镜像、s6、provider session、volume init 等容器问题，不要先看这里
