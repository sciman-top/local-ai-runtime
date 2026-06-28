# host-orchestrator

`Wave 1 / Phase 1` 的主机侧调度骨架。

当前已完成的 repo-side 薄切片：

- Python 3.11+ 工程骨架
- 统一的本地路径约定
- 最小 CLI 入口
- `W1-T02` 所需的 Python Codex SDK worker 参数映射与最小执行包装
- `W1-T03` 所需的 `codex exec` fallback 参数构造与输出读取包装
- `W1-T04` 所需的 `control-plane.db` 初始化与基础表结构
- `W1-T05` 所需的 fake-first `host_local` 单任务闭环：
  - 读取 `AgentBridge/tasks/*.md`
  - 写入一对一 `results/*.md`
  - 生成 artifact
  - 写入基础运行态表与事件

当前明确不做：

- live `Codex SDK` 真机执行验收
- watcher / lease 抢占
- 自动重试 / auto_continue
- 多 worker / 多 repo
- live `AgentBridge` 自动接线

当前验证口径：

- `uv run pytest` 已覆盖 `W1-T01 ~ W1-T05` 的 fake-first 回归
- `snapshots/agentbridge-20260628/scripts/test-agentbridge-contract.ps1` 仍通过
- 以上只证明 repo-side 结构、契约与 fake-first 闭环成立
- 还不等于 `Phase 1 accepted`

后续原子任务会在这个骨架上继续叠加。
