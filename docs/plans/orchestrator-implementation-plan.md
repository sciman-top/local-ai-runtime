# Orchestrator Implementation Plan

## Goal

把当前仓库从 Hermes-oriented 文档维护仓，收敛成一个可直接编码的通用本地 AI Dev Orchestrator 主仓，同时保留 Hermes/AgentBridge 兼容线。

## Working Rules

- 代码一律在 `runtime/host-orchestrator` 上就地演进
- 文档主线以 `planning-status.json` + authoritative docs 为准
- `Phase 1` 采用双写过渡方案 A
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
- Verification:
  - `pwsh .\scripts\refresh-reference-repos.ps1 -FetchOnly -SkipDirtyRepos -RepoNames governed-ai-coding-runtime`

### GOV-T02 split selector from verifier

- Status: completed
- Verification:
  - `python .\scripts\verify-planning-status.py`
  - `python .\scripts\select-next-work.py`

### GOV-T03 add repo-level change-evidence index

- Status: completed
- Verification:
  - `docs/change-evidence/README.md` references dated evidence notes

### GOV-T04 add release-style preflight entrypoint

- Status: completed
- Verification:
  - `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`

### GOV-T05 wire docs, AGENTS, and proof routing

- Status: completed
- Verification:
  - `python .\scripts\verify-planning-status.py`

## Ordered Changes Status

### Step 1. P1-T01 默认 layout 迁到 `.ai/state` 与 `.ai/runs`

- Status: completed
- Files:
  - `runtime/host-orchestrator/src/host_orchestrator/paths.py`
  - `runtime/host-orchestrator/tests/test_scaffold.py`
  - `docs/change-evidence/20260706-layout-defaults-to-ai-state.md`
- Verification:
  - `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_scaffold.py -q`

### Step 2. P1-T02 / P1-T03 canonical intake + canonical result writer

- Status: completed (repo-side)
- Files:
  - `runtime/host-orchestrator/src/host_orchestrator/host_local.py`
  - `runtime/host-orchestrator/src/host_orchestrator/agentbridge.py`
  - `runtime/host-orchestrator/src/host_orchestrator/canonical_task.py`
  - `runtime/host-orchestrator/src/host_orchestrator/canonical_result.py`
  - `runtime/host-orchestrator/src/host_orchestrator/wave1_smoke.py`
  - `runtime/host-orchestrator/tests/test_wave1_execution.py`
- Outputs:
  - canonical `task.json` / `task.yaml` intake
  - `.ai/runs/<run_id>/<task_id>/result.json`
  - `.ai/runs/<run_id>/<task_id>/verification_summary.json`
  - `.ai/runs/<run_id>/<task_id>/cost_summary.json`
  - `.ai/runs/<run_id>/<task_id>/evidence_index.json`
  - compatibility markdown projection
- Verification:
  - `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_wave1_execution.py -q`

### Step 3. P1-3 config / worker-profile contract absorption

- Status: completed (repo-side)
- Files:
  - `docs/specs/config-and-worker-profiles.md`
  - `.ai/config/orchestrator.yaml`
  - `.ai/config/workers.yaml`
  - `.ai/config/policies.yaml`
  - `runtime/host-orchestrator/src/host_orchestrator/config_runtime.py`
- Outputs:
  - repo-owned config truth
  - deterministic contract error on missing/invalid config
  - no silent fallback to hardcoded defaults
- Verification:
  - `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_wave1_execution.py -q`

### Step 4. acceptance-and-gates authoritative spec

- Status: completed (contract layer)
- Files:
  - `docs/specs/acceptance-and-gates.md`
  - `docs/product/orchestrator-prd.md`
  - `scripts/governance/preflight.ps1`
- Outputs:
  - PRD 四档 acceptance tiers 显式映射
  - `mock green` / `live probe ready` 不再与 PRD 四档打架

### Step 5. run-state / handoff contract foundation

- Status: completed (contract layer)
- Files:
  - `docs/specs/run-state-and-handoff.md`
  - `docs/specs/state-and-db.md`
- Outputs:
  - `run_id / attempt / resume_point / retry_rewind / handoff_required / next_action` 最小契约

### Step 6. selector policy verifier coverage

- Status: completed
- Files:
  - `docs/architecture/planning-status.json`
  - `docs/architecture/next-work-selection-policy.json`
  - `scripts/verify-planning-status.py`
  - `scripts/select-next-work.py`

### Step 7. impl_pack stale / legacy demotion

- Status: completed
- Files:
  - `ai_dev_orchestrator_impl_pack/00_README_FIRST.md`
  - `ai_dev_orchestrator_impl_pack/03_IMPLEMENTATION_ROADMAP.md`
  - `ai_dev_orchestrator_impl_pack/05_TASK_CONTRACT_SCHEMA.json`
  - `ai_dev_orchestrator_impl_pack/05_SAMPLE_TASKS.json`
  - `ai_dev_orchestrator_impl_pack/06_STATE_MACHINE.md`
  - `ai_dev_orchestrator_impl_pack/07_AGENT_ROLE_MATRIX.md`
  - `ai_dev_orchestrator_impl_pack/08_AGENTS.md`
  - `ai_dev_orchestrator_impl_pack/09_CODEX_MASTER_PROMPT.md`
  - `ai_dev_orchestrator_impl_pack/10_GLM_REVIEW_PROMPT.md`
  - `ai_dev_orchestrator_impl_pack/14_HANDOFF_MESSAGE_TO_CODEX.md`
  - `scripts/verify-planning-status.py`

## Remaining Phase 1 Work

### P1-T04 真实 SDK 切片

- Status: pending
- Preconditions:
  - GPT-5.4 gateway 可用：已满足
  - `codex exec` 最小命令可用：已满足
  - 当前范围限制：`network_proxy` 仍为 `platform_na`，先按纯本地任务推进

### P1-T05 `evidence_index.json` sha256 可重算

- Status: pending
- Gap:
  - 仍缺独立 index 校验脚本

## Phase 2 And Beyond

### P2-T01 schema / contract hardening

- Status:
  - config / acceptance / run-state foundation docs 已落盘
  - formal schema validation tests 仍待实现

### P2-T02 AgentBridge round-trip

- Status: pending

### P3-T01 verification runner

- Status: pending

### P3-T02 worktree manager / cleanup manager

- Status: pending

### P4-T01 planner adapter

- Status: pending

### P4-T02 review adapter

- Status: pending
