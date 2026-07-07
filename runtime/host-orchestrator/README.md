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
  - 读取 canonical `task.json` / `task.yaml`
  - 写入 `.ai/runs/<run_id>/<task_id>/result.json`
  - 双写 compatibility markdown projection
  - 生成 canonical artifact 与 projection artifact
  - 写入基础运行态表与事件
- `W1-T06` 所需的三类 Wave 1 smoke 样本任务集：
  - `code_refactor`
  - `docs_sync`
  - `script_contract`
- `W1-T07` 所需的一键 repo-side 验收脚本：
  - `scripts/run-wave1-smokes.ps1`
  - `scripts/test-wave1-acceptance.ps1`
- `P5-T02` 所需的 deterministic multi-worker simulation suite：
  - `src/host_orchestrator/multi_worker_simulation.py`
  - `scripts/run-multi-worker-simulation.ps1`
- `P5-T03` 所需的 remote_non_gui promotion evidence suite：
  - `src/host_orchestrator/remote_non_gui_promotion.py`
  - `scripts/run-remote-non-gui-promotion.ps1`
- `P6-T03` 所需的 vm_gui conditional promotion evidence suite：
  - `src/host_orchestrator/vm_gui_promotion.py`
  - `scripts/run-vm-gui-promotion.ps1`

当前明确不做：

- live `Codex SDK` 真机执行验收
- watcher / lease 抢占
- 自动重试 / auto_continue
- live 多 worker scheduler / 多 repo executor
- live `AgentBridge` 自动接线

当前验证口径：

- `uv run pytest` 已覆盖 `W1-T01 ~ W1-T07` 的 repo-side 回归
- `P1-1` 的第一步已落地到 repo-side：优先采集 SDK 结构化 `usage`，并把 token 使用量写入运行态事件与结果观察；文本 probe 仍只保留为后续保底方案
- `runtime/host-orchestrator/scripts/test-wave1-acceptance.ps1` 会串起：
  - `uv run pytest`
  - `snapshots/agentbridge-20260628/scripts/test-agentbridge-contract.ps1`
  - `private-local/wave-smokes/` 下的 deterministic smoke suite
- `runtime/host-orchestrator/scripts/run-multi-worker-simulation.ps1` 会生成 deterministic `route / quota / retry / review-handoff` simulation summary
- `runtime/host-orchestrator/scripts/run-remote-non-gui-promotion.ps1` 会生成 deterministic baseline remote-lane handoff 与 explicit remote-profile fail-closed handoff summary
- `runtime/host-orchestrator/scripts/run-vm-gui-promotion.ps1` 会生成 deterministic baseline GUI-only handoff 与 explicit `vm_gui` profile fail-closed handoff summary
- 以上只证明 repo-side 结构、契约、样本任务与 fake-first 验收资产成立
- deterministic multi-worker simulation 只证明 repo-side orchestration behavior，不等于 live 多 worker scheduler 已验收
- remote_non_gui promotion evidence 只证明 lane promotion / fail-closed handoff，不等于 remote runner 已验收
- vm_gui conditional promotion evidence 只证明 GUI-only 条件晋升 / fail-closed handoff，不等于 vm runner 已验收
- `AgentBridge` 当前只保留为 compatibility adapter，不再作为主协议输入
- 还不等于 `Phase 1 accepted`

后续原子任务会在这个骨架上继续叠加。
