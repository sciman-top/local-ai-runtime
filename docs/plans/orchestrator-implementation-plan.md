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

- Status: pending
- Goal:
  - Hermes parity
  - container lifecycle
  - historical baseline mapping
  - 后置控制面扩展
- Boundary:
  - 只有在 parity 绿后才评估 `compatibility_projection_ref` 与 `lane` 的 schema rename

### Phase F — Topology Expansion

- Status: pending
- Goal:
  - `remote_non_gui` 次级推进
  - `vm_gui` 条件晋升

## Current Repo-Side Foundations

### Phase 1 closeout already landed repo-side

- `P1-T01` 默认 layout 已迁到 `.ai/state` 与 `.ai/runs`
- `P1-T02` canonical task intake 已落地
- `P1-T03` 正式 `result.json` + compatibility markdown projection 已落地
- `P1-T03A` repo-owned config / worker-profile contract 已吸收
- `P1-T04` 一次非 mock 的 `Codex SDK` real vertical slice 已完成
- `P1-T05` `evidence_index.json` sha256 可重算入口已落地

### Phase 2 contract foundations already landed repo-side

- `P2-T01` acceptance / gates foundation：completed
- `P2-T02` run-state / handoff foundation：completed
- `P2-T03` AgentBridge round-trip parity：completed（repo-side）

## Next Bounded Execution Queue

- `P4-T01` planner adapter：completed（repo-side minimal handoff）
- `P4-T02` review adapter：completed（repo-side graded autonomy `needs_review` gate；低风险任务默认自动推进）
- `P4-T03` 正反触发谓词测试：completed（repo-side positive/negative predicate coverage + force-on overrides）
- `P3-T02` path guard：completed（repo-side fail-closed guard for repo-escape path claims、declared isolated worktree root/branch drift、以及 git-backed write-boundary enforcement）
- `P3-T03` worktree manager：completed（repo-side minimal create/reuse manager for declared linked worktrees plus `cleanup_status` baseline semantics）
- `P3-T04` cleanup manager：completed（runtime-managed clean linked worktrees now auto-remove; review-pending, failed, dirty, or externally launched isolated worktrees remain deferred with `worktree_cleanup` evidence）
- `P3-T05` graded autonomy runtime ledger：completed（runtime-backed `dispatch_state.json` + `result.json` metadata + `runtime_tasks` index alignment）
- next: lifecycle ops (`stale / cancelled / resumed / retry`) + structured review/closeout receipts（branch deletion 仍不自动化；live review sidecar 仍未接线）

其中 `planner/review` 继续保留在 repo `Phase 4`，不并回容器或资源 phase。
