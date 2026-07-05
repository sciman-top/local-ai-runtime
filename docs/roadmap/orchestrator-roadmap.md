# Orchestrator 路线图

## 当前主线

当前主产品线是 **通用本地 AI Dev Orchestrator**。

当前下一执行队列是 `Phase 1 垂直切片`，前置是 `Phase 0' 真源收敛` 已落盘并通过 verifier。

## 阶段总表

### Phase 0'

- 目标：真源收敛、主入口改写、Hermes 文档降级、`planning-status.json` + verifier 上线
- 出口门禁：authoritative docs 零冲突、impl_pack 不再是 greenfield 叙事
- 回滚：整体 revert 文档与 verifier 变更

### Phase 1 垂直切片

- 目标：canonical task -> 真实 SDK -> `result.json` -> markdown projection
- 入口条件：
  - GPT-5.4 网关或等效凭据可用
  - `codex exec` 最小命令可跑
- 出口门禁：
  - `repo-side green`
  - `evidence_index.json` sha256 可重算
  - 双写过渡方案 A 断言通过
- 回滚：恢复旧 layout、关闭双写主线

### Phase 2 契约与兼容面

- 目标：task/result/review/run-index schema + AgentBridge round-trip
- 出口门禁：schema tests + projection parity 全绿
- 回滚：保留 JSON 主协议，回退兼容 adapter 演进

### Phase 3 执行与验证

- 目标：verification runner、path guard、worktree manager、cleanup manager
- 出口门禁：`build -> [lint -> typecheck] -> test -> contract -> hotspot` 统一跑通
- 回滚：退回 Phase 2 单切片模式

### Phase 4 Planner / Review

- 目标：`Direct GPT-5.4 API` planner + `Claude Code + GLM-5.2` review adapter
- 出口门禁：planner/review 谓词正反分支全绿
- 回滚：降级为人工触发 planner/review

### Phase 5 多仓多 worker

- 目标：leases/heartbeat/retry/route/quota + 新增 4 表
- 出口门禁：`multi-worker simulation green`
- 回滚：恢复单 writer 主线

### Phase 6 Hermes 兼容收口

- 目标：Hermes/AgentBridge 兼容线三绿
- 出口门禁：
  - parity green
  - historical snapshot mapping green
  - markdown projection green
- 回滚：继续保留 Hermes 顶层旧入口

## Promotion Rule

只有当当前 phase 的出口门禁为绿时，才允许推进 `planning-status.json` 的 `current_active_queue`。
