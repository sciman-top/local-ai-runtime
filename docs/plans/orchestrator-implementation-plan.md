# Local AI Runtime 实施计划

项目展示名是 `Local AI Runtime`，中文名是 `本地 AI 运行时`。当前主产品线是 `Hermes -> AgentBridge -> Codex`；历史仓库 slug / 当前本地目录仍为 `local-ai-dev-orchestrator`。

## Goal

把当前仓库回调为 **Hermes -> AgentBridge -> Codex** 三层主线，同时严格保留当前 repo truth：

- canonical `JSON/YAML` intake 仍是当前主路径
- `.ai/runs/<run_id>/<task_id>/result.json` 仍是正式 evidence 主体
- `AgentBridge results/*.md` 当前仍是 compatibility projection
- `runtime/host-orchestrator` 是 `host_local` 可信运行时内核

## Working Rules

- 代码一律在 `runtime/host-orchestrator` 上就地演进
- 文档主线以 `planning-status.json` + authoritative docs 为准
- `Phase 1` 继续采用双写过渡方案 A
- `Wave 1 smoke` 继续隔离在 `private-local/wave-smokes/`
- gate 顺序固定为 `build -> [lint -> typecheck] -> test -> contract -> hotspot`
- 不改仓库名 / 远端 slug / 本地目录名；终态重构通过同仓 `runtime_v2` 新内核完成

## Governance Overlay

这组任务是 cross-cutting overlay，不替代 `Phase 1 -> Phase 6` 产品路线图。

当前 companion：

- `governed-ai-coding-runtime`

当前预期 selector 结果：

- `promote_phase1_execution`

### GOV-T01 formalize governed reference companion

- Status: completed

### GOV-T02 split selector from verifier

- Status: completed

### GOV-T03 add repo-level change-evidence index

- Status: completed

### GOV-T04 add release-style preflight entrypoint

- Status: completed

### GOV-T05 wire docs, AGENTS, and proof routing

- Status: completed

### GOV-T08 absorb control-repo global-only rule governance

- Status: completed

### GOV-T09 add target-project `AGENTS.md + CLAUDE.md` coordination pilot

- Status: completed

### GOV-T10 align docs, wrapper boundary, and repo-level evidence for the pilot

- Status: completed

## Strategic Return Landing Order

### Phase A — Truth Reset

- Status: completed (repo-side)
- Scope:
  - authoritative docs
  - `planning-status.json`
  - selector policy / verifier
  - change-evidence
- Boundary:
  - 不反转当前 canonical intake / `result.json` / compatibility projection 事实
  - 不提前落 `compatibility_projection_ref` 或 `lane` 改名
  - 不把 AgentBridge round-trip parity、execution-critical override live support、或字段改名写成已完成

### Phase B — Host_local Robustness

- Status: completed (repo-side)
- Goal:
  - `host_local` 异常收口
  - 当前 `leases` 表最小函数
  - worker crash 后 `task failed + worker idle`
- Outputs:
  - `acquire_lease / renew_lease / release_lease / reap_stale_leases`
  - `host_local` failure path now records `task_failed`, flips runtime task to `failed`, restores worker to `idle`, and releases the lease
  - `codex exec` fallback now runs behind a process-tree guard

### Phase C — Verification Runner

- Status: completed (repo-side)
- Goal:
  - 最小真实 gate executor
  - 替换 `verification_summary.json` 的硬编码默认成功口径
- Outputs:
  - `verification.py` 最小 gate executor
  - 当前只真实执行 `test + contract`
  - `build / lint / typecheck / hotspot` 继续按 `gate_na` 或 `not_configured` 留痕

### Phase D — AgentBridge-first Intake Upgrade

- Status: completed (repo-side, safe intake boundary)
- Goal:
  - 合规 AgentBridge markdown task 可直接进入 `host_local` 主路径
  - markdown intake 先归一化到 repo-owned canonical 默认值
  - execution-critical override / markdown 侧 gate 命令输入 fail closed

### Phase E — Hermes Parity + Container Lifecycle

- Status: completed (repo-side)
- Goal:
  - Hermes parity
  - container lifecycle
  - historical baseline mapping
  - 后置控制面扩展
- Boundary:
  - 当前已明确决定继续保留 `compatibility_projection_ref` 与 `lane` 现名，不在当前 repo-side parity / topology closeout 中做字段改名
  - 只有当 bounded live heterogeneous review receipt、真实 remote/vm runner acceptance、以及后续 review 稳定性都真实落地后，才重新评估是否需要 schema rename

### Phase F — Topology Expansion

- Status: in_progress
- Goal:
  - `remote_non_gui` 次级推进
  - `vm_gui` 条件晋升
- Current boundary:
  - `remote_non_gui` runner wiring readiness contract、acceptance-ref guard 与最小 schema 已落 repo-side，但 committed `remote_non_gui_probe` 仍保持 `runner_wired=false`
  - 真实 remote host runner acceptance、真实 GUI-only workload acceptance、以及 `live accepted` 仍未开始

## Current Repo-Side Foundations

### Phase 1 closeout already landed repo-side

- `P1-T01` 默认 layout 已迁到 `.ai/state` 与 `.ai/runs`
- `P1-T02` canonical task intake 已落地
- `P1-T03` 正式 `result.json` + compatibility markdown projection 已落地
- `P1-T03A` repo-owned config / worker-profile contract 已吸收
- `P1-T04` 一次非 mock 的 `Codex SDK` real vertical slice 已完成
- `P1-T05` `evidence_index.json` sha256 可重算入口已落地
- repo-owned `host_local` task entrypoint 与 worker factory 已落地：`host-orchestrator --run-task` / `run-host-task.ps1` 当前已直接消费 `local_maint` 的 `codex_sdk` 路径，并在结构上支持 `codex_exec`；built-in `codex_exec` profiles 仍保持 non-host-local handoff，而 `scripted / gpt54_direct / claude_glm` 继续 live task execution fail-closed

### Phase 2 contract foundations already landed repo-side

- `P2-T01` acceptance / gates foundation：completed
- `P2-T02` run-state / handoff foundation：completed
- `P2-T03` AgentBridge round-trip parity：completed（repo-side）

## Next Bounded Execution Queue

- `P3-T01` verification runner fixed gate order：completed（repo-side fixed order with `gate_na / not_configured / pass / fail` preservation）
- `P4-T01` planner adapter：completed（live planner sidecar receipt + worker-boundary stop）
- `P4-T02` review adapter：completed（repo-side graded autonomy `needs_review` gate；低风险任务默认自动推进）
- `P4-T03` 正反触发谓词测试：completed（repo-side positive/negative predicate coverage + force-on overrides）
- `P3-T02` path guard：completed（repo-side fail-closed guard for repo-escape path claims、declared isolated worktree root/branch drift、以及 git-backed write-boundary enforcement）
- `P3-T03` worktree manager：completed（repo-side minimal create/reuse manager for declared linked worktrees plus `cleanup_status` baseline semantics）
- `P3-T04` cleanup manager：completed（runtime-managed clean linked worktrees now auto-remove; review-pending, failed, dirty, or externally launched isolated worktrees remain deferred with `worktree_cleanup` evidence）
- `P3-T05` graded autonomy runtime ledger：completed（runtime-backed `dispatch_state.json` + `result.json` metadata + `runtime_tasks` index alignment）
- `P3-T06` lifecycle ops：completed（repo-side stale/cancel/resume/retry helpers + CLI entrypoints + tests）
- `P4-T04` structured review/closeout receipts：completed（`review_result.json` + `closeout_bundle.json` + result/dispatch/evidence refs）
- `P6-T01` Hermes parity closeout：completed（repo-owned verifier 现已把 certified baseline doc、current known-good / boundary anchors、snapshot contract、known-good validator、以及 historical container lifecycle boundary 收进同一 summary）
- `P6-T02` historical snapshot mapping：completed（current known-good / boundary anchor 已在 implementation-status、handoff summary、以及 checklist 三面一致）
- `P6-T03` vm_gui conditional promotion evidence：completed（repo-owned `vm_gui_probe` profile、GUI-only handoff、以及显式 vm lane fail-closed summary 已收口）
- `P5-T03` follow-on handoff receipt hardening：completed（pre-worker handoff 现在写 `handoff_receipt.json`，remote_non_gui promotion summary 会读取 `handoff_reason_codes / worker_execution_attempted`）
- `P5-T04` remote_non_gui runner wiring readiness：completed（`runner_wired=false` 继续 pre-worker handoff；临时 `runner_wired=true` 测试配置必须绑定 repo-relative、schema-valid 的 `runner_acceptance_ref` 后才可调用注入 runner；runner 失败保持 failed dispatch 且不写成功 result）
- next: `真实 remote host runner acceptance + follow-on review hardening`（bounded live heterogeneous review receipt 已落地；branch deletion 仍不自动化；真实 GUI-only workload acceptance 仍未开始）

其中 `planner/review` 继续保留在 repo `Phase 4`，不并回容器或资源 phase。

## Kernel V2 Dual-Track Migration

当前已接受并落地的实施方式固定为：保留本项目作为唯一主仓，在 `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/` 内实现新内核；旧 `host_local` 保持 `legacy_v1` 默认入口，直到 cutover 条件满足。

### 当前已落地切片

- `WP1`：双轨骨架 + experimental CLI 已落地
  - 当前入口包括 `--run-task-v2`、`--run-ready-blocked-v2`、`--resume-task-v2`、`--retry-task-v2`、`--migrate-control-plane-v2`、`--eval-regression-fixtures-v2`、`--cutover-drill-v2`、`--cutover-rollback-drill-v2`、`--cutover-v2`、`--confirm-cutover-v2`、`--cutover-approval-ref`、`--cutover-approval-template-v2`
- `WP2`：v2 canonical task、6 表存储、attempt-level 工件面已落地
- `WP3`：dependency block、ready dependency-blocked auto-continue、atomic admission、attempt-centric resume/retry 已落第一批实现
- `WP4`：review receipt / bounded sidecar hook / pre-worker policy guard 已落第一批实现
- `WP5`：attempt-level `regression_fixture.json` 已扩展到 completed / reviewing / gate-retryable final-result、dependency-blocked、admission-paused、pre-worker policy-guard blocked、worker-failure retryable / failed、retry queued 核心状态路径；最小 `--eval-regression-fixtures-v2` 已写出 repo-side summary
- `WP6`：第一批 cutover drill / fail-closed guard、cutover review / manual approval gate、非破坏 rollback restore drill、archive restore acceptance、operator approval evidence gate、默认未批准的 operator approval template 生成入口、approval hash / sanitized audit 留痕、approval 对 `archive_restore_acceptance_path` 的强引用校验、以及 `approved_at` UTC `Z` 时间戳校验已落地；`--cutover-v2` 在 drill 未 ready 时不修改 `runtime.active_version`，drill ready 后仍默认返回 `manual_approval_required`；`--cutover-rollback-drill-v2` 会验证 v1 DB / v1 runs 源并写出 `archive-restore-acceptance.json`，但不执行 restore；`--confirm-cutover-v2` 还必须绑定通过校验、引用当前 archive restore acceptance 且带 UTC approval timestamp 的 `--cutover-approval-ref` 才进入默认入口切换路径；当前已有一条真实 `local_maint` v2 live coding probe completed，eval summary `ok=true`，cutover drill `ready=true / cutover_performed=false`
- 文档/spec/verifier 已开始同步吸收 `Kernel V2`，但 `planning-status.current_active_queue` 仍保持 `PHASE-1-VERTICAL-SLICE`

### 下一步

- 下一步应在不改默认入口的前提下继续收紧 confirmed cutover 前的人工验收证据；真实人工审批 / cutover / restore 操作 runbook 已落在 `docs/runbooks/runtime-v2-cutover-operator-runbook.md`
- `WP6` 仍必须保持 default v1，直到 cutover 条件、门禁、人工边界与恢复路径真实满足
