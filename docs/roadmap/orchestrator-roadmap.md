# Local AI Runtime 路线图

项目展示名是 `Local AI Runtime`，中文名是 `本地 AI 运行时`。当前主产品线是 `Hermes -> AgentBridge -> Codex`；历史仓库 slug / 当前本地目录仍为 `local-ai-dev-orchestrator`。

## 当前主线

当前主产品线回调为 **Hermes -> AgentBridge -> Codex**。

当前 repo truth 同时保留：

- canonical `JSON/YAML` intake 仍是当前主路径
- `.ai/runs/<run_id>/<task_id>/result.json` 仍是正式 evidence 主体
- `AgentBridge results/*.md` 当前仍是 compatibility projection
- 当前 active queue 仍是 `PHASE-1-VERTICAL-SLICE`

当前 selector 预期结果仍是 `promote_phase1_execution`。

## Governance Overlay

这层横切产品推进过程，但不替代既有产品 phase。

- 目标：把 `selector + change-evidence + preflight + reference governance` 落成统一治理增强面
- 当前 companion：`governed-ai-coding-runtime`，定位为 `governance-sidecar`
- 当前规则：Governance Overlay 为绿之后，才允许继续推进当前 active queue

治理任务包状态：

- `GOV-T01` formalize governed reference companion：已完成
- `GOV-T02` split selector from verifier：已完成
- `GOV-T03` add repo-level change-evidence index：已完成
- `GOV-T04` add release-style preflight entrypoint：已完成
- `GOV-T05` wire docs, AGENTS, and proof routing：已完成
- `GOV-T08` absorb control-repo global-only rule governance：已完成
- `GOV-T09` add target-project `AGENTS.md + CLAUDE.md` coordination pilot：已完成
- `GOV-T10` align docs, wrapper boundary, and repo-level evidence for the pilot：已完成

## 战略回调 Overlay（A-F）

这组阶段是对现有产品路线图的重新解释顺序，不替代 `Phase 1 -> Phase 6` 编号。

### Phase A — Truth Reset

- 目标：同步 authoritative docs、planning-status、policy、verifier 与 evidence note
- 当前状态：已落 repo-side
- 边界：保留 canonical internal normalization / `result.json` / compatibility projection 当前事实，不提前宣称 parity、execution-critical override live support、或字段改名已完成

### Phase B — Host_local Robustness

- 目标：`host_local` 正确性修复、异常收口、lease 基础函数
- 当前状态：已完成（repo-side）

### Phase C — Verification Runner

- 目标：最小真实 gate executor 取代硬编码 verification 口径
- 当前状态：已完成（repo-side）

### Phase D — AgentBridge-first Intake Upgrade

- 目标：合规 markdown task 安全接入主路径，并归一化到 repo-owned canonical 默认值
- 当前状态：已完成（repo-side，safe intake boundary）

### Phase E — Hermes Parity + Container Lifecycle

- 目标：Hermes parity、container lifecycle、历史 baseline mapping、后置控制面扩展
- 当前状态：待实现

### Phase F — Topology Expansion

- 目标：`remote_non_gui` 再到条件晋升的 `vm_gui`
- 当前状态：待实现

## 产品阶段总表

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

### Phase 2 契约与 intake parity

- 目标：task/result/review/run-state/acceptance contract 固化，并在安全 intake 接线后推进 AgentBridge round-trip parity
- 当前状态：
  - config / acceptance / run-state foundation docs 已落盘
  - repo-side projection parity 已落地
  - 尚未自动升级为 `platform compatibility green`
- 出口门禁：schema tests + projection parity 全绿

### Phase 3 执行与验证

- 目标：verification runner、path guard、worktree manager、cleanup manager
- 出口门禁：`build -> [lint -> typecheck] -> test -> contract -> hotspot` 统一跑通

### Phase 4 Planner / Review

- 目标：`Direct GPT-5.4 API` planner + `Claude Code + GLM-5.2` review adapter
- 出口门禁：planner/review 谓词正反分支全绿

### Phase 5 多仓多 worker

- 目标：leases/heartbeat/retry/route/quota
- 出口门禁：`multi-worker simulation green`

### Phase 6 Hermes parity / topology closeout

- 目标：Hermes parity、container lifecycle、historical snapshot mapping，以及远端拓扑 closeout
- 出口门禁：
  - parity green
  - historical snapshot mapping green
  - lane promotion evidence green

## Promotion Rule

只有当 Governance Overlay 与当前 phase 的出口门禁都为绿时，才允许推进 `planning-status.json` 的 `current_active_queue`。
