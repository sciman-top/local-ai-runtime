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
- 当前状态：
  - `P3-T01` verification runner fixed gate order 已完成；当前真实执行仍只覆盖 `test / contract`，其余 gate 继续按 `gate_na / not_configured` 留痕
  - `P3-T02` path guard 已升级到 git-backed fail-closed write-boundary enforcement
  - `P3-T03` worktree manager 与 `P3-T04` cleanup manager 已完成
  - `P3-T05` graded-autonomy runtime ledger 已完成：`dispatch_state.json`、`result.json`、以及 `runtime_tasks` 已共享 `attempt / next_action / cleanup_* / status_reason / dispatch_state_ref`
  - `P3-T06` lifecycle ops 已完成：repo-side 现在可显式 materialize `stale / cancelled / resumed`，`retry` 通过 `attempt + retry_rewind` 收口
  - `P5-T01` 的 repo-side `leases / route / quota` 收口已完成：explicit/default `worker_profile` 现在会 materialize `route_reason`，worker-profile `max_active_leases` 超额时会在 worker 前 handoff
  - `P5-T02` 的 deterministic multi-worker simulation 已完成：当前可复放 `retry / route / quota / review-handoff` summary，并输出 JSON evidence
  - `P5-T03` 的 `remote_non_gui` promotion evidence 已完成：当前可复放 baseline remote-lane handoff 与 explicit remote-profile fail-closed handoff summary，并输出 JSON evidence
  - next repo-side gap 转到 `Hermes parity / historical snapshot mapping`
- 出口门禁：`build -> [lint -> typecheck] -> test -> contract -> hotspot` 统一跑通

### Phase 4 Planner / Review

- 目标：`Direct GPT-5.4 API` planner + `Claude Code + GLM-5.2` review adapter
- 当前状态：
  - `P4-T01` 的 repo-side planner handoff 已落地
  - `P4-T02` 的 repo-side review gate 已落地；低风险任务默认自动推进，medium/high/critical 风险、policy surface、以及 force-on review 命中时当前会在 worker / verification 之后停在 `needs_review`
  - `P4-T03` 的 repo-side 正反谓词测试已落地；`user_forced_planner / user_forced_review` 现已作为 force-on override 被 contract 与测试承接
  - `P4-T04` 的 repo-side structured receipts 已落地；review-gated 路径现在会写 `review_result.json`，当前 planner/review/completed outcome 都会写 `closeout_bundle.json`
  - 尚未宣称 live `Direct GPT-5.4 API` planner 或 live `Claude Code + GLM-5.2` review adapter 已接线
- 出口门禁：planner/review 谓词正反分支全绿

### Phase 5 多仓多 worker

- 目标：`remote_non_gui` 推进前的控制面整固
- 出口门禁：`multi-worker simulation green`

### Phase 6 Hermes parity / topology closeout

- 目标：Hermes parity、container lifecycle、historical snapshot mapping，以及远端拓扑 closeout
- 出口门禁：
  - parity green
  - historical snapshot mapping green
  - lane promotion evidence green

## Promotion Rule

只有当 Governance Overlay 与当前 phase 的出口门禁都为绿时，才允许推进 `planning-status.json` 的 `current_active_queue`。
