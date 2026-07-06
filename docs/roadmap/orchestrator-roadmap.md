# Orchestrator 路线图

## 当前主线

当前主产品线是 **通用本地 AI Dev Orchestrator**。

当前 active queue 仍是 `PHASE-1-VERTICAL-SLICE`，但 `Phase 1` 的 repo-side 出口门禁已经补齐：

- `P1-T01` 默认 layout 已迁到 `.ai/state` 与 `.ai/runs`
- `P1-T02` canonical task intake 已落地
- `P1-T03` 正式 `result.json` + compatibility markdown projection 已落地
- `P1-T05` `evidence_index.json` sha256 独立重算入口已落地
- repo-owned `config / worker_profile / policies` 契约已吸收
- selector policy 已进入 verifier 视野，impl_pack stale/legacy demotion 也已机器可检

当前 selector 预期结果已提升到 `promote_phase1_execution`。

## Governance Overlay

这层横切 `Phase 1` 推进前和推进过程中，但不替代既有产品 phase。

- 目标：把 `planning truth / selector split / repo-level change-evidence / release-style preflight / formal reference governance companion` 落成统一治理增强面
- 当前 companion：`governed-ai-coding-runtime`，定位为 `governance-sidecar`
- 当前规则：Governance Overlay 为绿之后，才允许把真实 Phase 1 prerequisite probes 推进到 ready

治理任务包状态：

- `GOV-T01` formalize governed reference companion：已完成
- `GOV-T02` split selector from verifier：已完成
- `GOV-T03` add repo-level change-evidence index：已完成
- `GOV-T04` add release-style preflight entrypoint：已完成
- `GOV-T05` wire docs, AGENTS, and proof routing：已完成

## 阶段总表

### Phase 0'

- 目标：真源收敛、主入口改写、Hermes 文档降级、`planning-status.json` + verifier 上线
- 当前状态：已完成
- 出口门禁：authoritative docs 零冲突、impl_pack 不再是 greenfield 叙事

### Phase 1 垂直切片

- 目标：canonical task -> 真实 SDK -> `result.json` -> markdown projection
- 当前状态：
  - repo-side canonical runtime 与 evidence integrity 已闭环
  - prerequisite probes 已 ready
  - `network_proxy` 仍为 `platform_na`
  - `live accepted` 仍未达成
- 已完成：
  - 默认 layout 迁移
  - canonical task intake
  - canonical result writer
  - compatibility projection
  - repo-owned config / worker-profile contract
  - GPT-5.4 gateway probe
  - `codex exec` minimum probe
  - 一次非 mock 的 `Codex SDK` real vertical slice
  - `evidence_index.json` sha256 独立校验脚本
- 入口条件：
  - Governance Overlay 已落盘并可通过 repo-side gate
  - GPT-5.4 网关或等效凭据可用
  - `codex exec` 最小命令可跑
- 出口门禁：
  - `repo-side green`
  - `evidence_index.json` sha256 可重算
  - 双写过渡方案 A 断言通过

### Phase 2 契约与兼容面

- 目标：task/result/review/run-state/acceptance contract 固化 + AgentBridge round-trip
- 当前状态：
  - config / acceptance / run-state foundation docs 已落盘
  - 下一最小切片是 `P2-T03 AgentBridge round-trip parity`
- 出口门禁：schema tests + projection parity 全绿

### Phase 3 执行与验证

- 目标：verification runner、path guard、worktree manager、cleanup manager
- 出口门禁：`build -> [lint -> typecheck] -> test -> contract -> hotspot` 统一跑通

### Phase 4 Planner / Review

- 目标：`Direct GPT-5.4 API` planner + `Claude Code + GLM-5.2` review adapter
- 出口门禁：planner/review 谓词正反分支全绿

### Phase 5 多仓多 worker

- 目标：leases/heartbeat/retry/route/quota + 新增 4 表
- 出口门禁：`multi-worker simulation green`

### Phase 6 Hermes 兼容收口

- 目标：Hermes/AgentBridge 兼容线三绿
- 出口门禁：
  - parity green
  - historical snapshot mapping green
  - markdown projection green

## Promotion Rule

只有当 Governance Overlay 与当前 phase 的出口门禁都为绿时，才允许推进 `planning-status.json` 的 `current_active_queue`。
