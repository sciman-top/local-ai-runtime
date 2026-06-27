# hermes-agent

- 仓路径：`D:\CODE\external\hermes-agent-references\hermes-agent`
- 当前本机锚点：`main @ f53b184c48`

## 为什么保留

这是当前 `Hermes` 运行时、Docker 发布、配置迁移、s6/bootstrap 行为的第一真值。

当前主链里所有这些判断都要优先回到这里核对：

- 官方 release tag / digest 是否真的存在
- 镜像入口、`main-wrapper.sh`、`stage2-hook.sh` 的真实行为
- `HERMES_UID` / `HERMES_GID` remap 是否还是上游支持路径
- `hermes` CLI 的真实子命令、配置结构、日志行为是否变化

## 什么时候先看它

- `start-hermes.ps1`、`verify-hermes-boundary.ps1`、`run-hermes-wrapper.sh` 的行为需要和上游对齐时
- 需要判断某个本机 boundary 是上游事实、还是本地脚本误判时
- 准备升级 Hermes release / digest 时

## 什么时候不要扩大到它

- 纯 `Codex` 侧规则、skills 组织方式、MCP 协议问题，不要先跳到这里
- 当前 `AgentBridge` 文档索引错漏，也不该先把问题归到上游 Hermes
