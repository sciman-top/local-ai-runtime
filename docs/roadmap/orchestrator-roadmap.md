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

## Kernel V2 双轨迁移

这组工作包已吸收到最新路线图，但当前默认入口未切换，active queue 也不因此改写。

- `WP1` Legacy 冻结与双轨骨架：进行中
  - `runtime_v2/` 包、实验 CLI、`runtime.*` 配置字段已经落盘
- `WP2` V2 契约、状态机与存储真源：进行中
  - v2 canonical task、6 表存储、`.ai/runs-v2/` 工件骨架已落盘
- `WP3` 调度 / admission / 自动继续内核：进行中
  - `dependency_refs`、原子 slot admission、`resume_point / retry_rewind` 的 v2 一等字段已落第一批实现
  - dependency-blocked task 现在会持久化 repo-relative `tasks.task_path`，并可在依赖完成后通过 `--run-ready-blocked-v2` 批量续跑
- `WP4` 执行 / gate / 隔离 / sidecar 收口：进行中
  - review receipt、bounded review sidecar hook、pre-worker policy guard 已落第一批实现；non-host_local / vm_gui primary runner 仍未接线
- `WP5` trace / eval / 证据闭环：进行中
  - completed / reviewing / gate-retryable final-result、dependency-blocked、admission-paused、pre-worker policy-guard blocked、worker-failure retryable / failed、retry queued 路径已写出 attempt-level `regression_fixture.json`
  - 最小 `--eval-regression-fixtures-v2` 已可重跑并写出 repo-side regression fixture summary
- `WP6` cutover / archive / 真相面切换：进行中
  - 第一批 `--cutover-drill-v2`、`--cutover-v2` fail-closed guard、cutover review / manual approval gate、`--cutover-rollback-drill-v2` 非破坏恢复路径检查与 `--confirm-cutover-v2` 人工确认闸门已落地；真实 `local_maint` v2 live coding probe 已 completed，当前 drill ready 但默认 `--cutover-v2` 仍返回 `manual_approval_required / cutover_performed=false`，默认入口仍未切换

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
- 当前状态：
  - repo-side 已完成
  - 当前明确决定继续保留 `compatibility_projection_ref` 与 `lane` 现名，不在当前 repo-side parity / topology closeout 中做字段改名
  - 是否需要 schema rename，待 bounded live heterogeneous review receipt、non-host_local runner wiring、以及后续 review 稳定性都真实落地后再复评

### Phase F — Topology Expansion

- 目标：`remote_non_gui` 再到条件晋升的 `vm_gui`
- 当前状态：待实现

## 产品阶段总表

### Phase 1 垂直切片

- 目标：canonical task -> 真实 SDK -> `result.json` -> markdown projection
- 当前状态：
  - repo-side canonical runtime 与 evidence integrity 已闭环
  - repo-owned `host_local` task entrypoint 与 worker factory 已落地：`host-orchestrator --run-task` / `run-host-task.ps1` 当前已直接消费 `local_maint` 的 `codex_sdk` 路径，并在结构上支持 `codex_exec`
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
  - `P6-T01` / `P6-T02` 的 repo-side Hermes parity / historical snapshot mapping verifier 已完成：当前可复放 baseline doc、current known-good / boundary anchor、snapshot contract、known-good validator、以及 env-sensitive bring-up drift summary
  - `P6-T03` 的 `vm_gui` conditional promotion evidence 已完成：当前可复放 baseline GUI-only handoff 与 explicit `vm_gui_probe` fail-closed handoff summary，并输出 JSON evidence
  - repo-owned `host_local` task entrypoint 与 worker factory 已完成：`host-orchestrator --run-task` / `run-host-task.ps1` 当前已直接消费 `local_maint` 的 `codex_sdk` 路径，并在结构上支持 `codex_exec`；built-in `codex_exec` profiles 仍保持 non-host-local handoff，而 `scripted / gpt54_direct / claude_glm` 继续 live task execution fail-closed
  - next repo-side open set 收窄到 non-host_local runner wiring 与后续 review hardening
- 出口门禁：`build -> [lint -> typecheck] -> test -> contract -> hotspot` 统一跑通

### Phase 4 Planner / Review

- 目标：`Direct GPT-5.4 API` planner + `Claude Code + GLM-5.2` review adapter
- 当前状态：
  - `P4-T01` 的 live planner sidecar receipt 已落地；planner-gated task 当前会先运行 codex-backed planner sidecar、写出 `planner_result.json`，然后仍停在 `waiting_handoff`
  - `P4-T02` 的 repo-side review gate 已落地；低风险任务默认自动推进，medium/high/critical 风险、policy surface、以及 force-on review 命中时当前会在 worker / verification 之后停在 `needs_review`
  - `P4-T03` 的 repo-side 正反谓词测试已落地；`user_forced_planner / user_forced_review` 现已作为 force-on override 被 contract 与测试承接
  - `P4-T04` 的 repo-side structured receipts 已落地；live planner-sidecar 路径现在会写 `planner_result.json`，review-gated 路径会写 `review_result.json`，当前 planner/review/completed outcome 都会写 `closeout_bundle.json`
  - bounded live `Claude Code + GLM-5.2` review receipt path 已接线，但这仍不等于 live `Claude Code + GLM-5.2` primary task execution、non-host_local runner、`platform compatibility green`、或 `live accepted`
- 出口门禁：planner/review 谓词正反分支全绿

### Phase 5 多仓多 worker

- 目标：`remote_non_gui` 推进前的控制面整固
- 出口门禁：`multi-worker simulation green`

### Phase 6 Hermes parity / topology closeout

- 目标：Hermes parity、container lifecycle、historical snapshot mapping，以及远端拓扑 closeout
- 当前状态：
  - `P6-T01` 的 repo-side Hermes parity closeout 已完成：`run-hermes-parity.ps1` 当前会把 certified baseline doc、current known-good / boundary anchors、snapshot contract、known-good validator、以及 historical container lifecycle boundary 收进同一 summary
  - `P6-T02` 的 repo-side historical snapshot mapping 已完成：current anchor 固定到 `known-good-20260628-225738-431.json` 与 `verify-hermes-boundary-20260628-225841-414.json`
  - `P6-T03` 的 repo-side `vm_gui` conditional promotion evidence 已完成：`run-vm-gui-promotion.ps1` 当前会把 default GUI-only handoff 与 explicit `vm_gui_probe` fail-closed handoff 收进同一 summary
  - 当前 shell 中 Hermes bring-up gate 只剩 `independent_key / independent_base_url` 两个 env-sensitive blocker；这仍不自动升级为 `platform compatibility green` 或 `live accepted`
  - next repo-side open set 收窄到 non-host_local runner wiring 与后续 review hardening
- 出口门禁：
  - parity green
  - historical snapshot mapping green
  - lane promotion evidence green

## Promotion Rule

只有当 Governance Overlay 与当前 phase 的出口门禁都为绿时，才允许推进 `planning-status.json` 的 `current_active_queue`。
