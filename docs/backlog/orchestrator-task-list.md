# Local AI Runtime 任务清单

项目展示名是 `Local AI Runtime`，中文名是 `本地 AI 运行时`。当前主产品线是 `Hermes -> AgentBridge -> Codex`；历史仓库 slug / 当前本地目录仍为 `local-ai-dev-orchestrator`。

当前 active queue 仍然是 `PHASE-1-VERTICAL-SLICE`，当前预期 next action 仍是 `promote_phase1_execution`。

## Strategic Return Overlay

- [x] `A-T01` authoritative docs / planning-status / policy / verifier / change-evidence truth reset
  - Done when:
    - `Hermes -> AgentBridge -> Codex` 成为 authoritative docs 的主叙事
    - canonical intake / `result.json` / compatibility projection 当前事实仍被显式保留
    - `python .\scripts\verify-planning-status.py` 通过
  - Status note:
    - 2026-07-06 已完成 repo-side 落盘
- [x] `B-T01` host_local crash recovery and lease helpers
  - Done when:
    - worker crash 后 `task failed + worker idle`
    - 当前 `leases` 表具备 acquire / renew / release / reap 最小函数
  - Status note:
    - 2026-07-06 已落 `host_local` 失败收口、lease helpers、以及 exec fallback 进程守卫
- [x] `C-T01` verification runner
  - Done when:
    - `verification_summary.json` 不再默认 `no_commands_configured`
    - 最小 `test + contract` gate 真实执行
  - Status note:
    - 2026-07-06 已落最小真实 gate executor；`build / lint / typecheck / hotspot` 继续按 `gate_na` 或 `not_configured` 留痕
- [ ] `D-T01` AgentBridge-first intake upgrade
  - Done when:
    - markdown task 能无损映射 canonical 18 字段
    - `host_local` 主路径能接收 canonical JSON/YAML 与 AgentBridge markdown
- [ ] `E-T01` Hermes parity and container lifecycle
  - Done when:
    - parity / historical mapping / container lifecycle 进入同一闭环
    - 是否做 `compatibility_projection_ref` 与 `lane` rename 有明确决策
- [ ] `F-T01` topology expansion
  - Done when:
    - `remote_non_gui` 进入 simulation
    - `vm_gui` 只有在真实 GUI-only workload 证据下才升级

能力范围与晋升顺序固定为：`host_local > remote_non_gui > vm_gui`。

## Governance Overlay

- [x] `GOV-T01` formalize governed reference companion
- [x] `GOV-T02` split selector from verifier
- [x] `GOV-T03` add repo-level change-evidence index
- [x] `GOV-T04` add release-style preflight entrypoint
- [x] `GOV-T05` wire docs, AGENTS, and proof routing
- [x] `GOV-T06` selector policy verifier coverage
- [x] `GOV-T07` impl_pack stale demotion and machine checks
- [x] `GOV-T08` absorb control-repo global-only rule governance
- [x] `GOV-T09` add target-project `AGENTS.md + CLAUDE.md` coordination pilot
- [x] `GOV-T10` align docs, wrapper boundary, and repo-level evidence for the pilot

## Phase 1

- [x] `P1-T01` 默认 layout 迁到 `.ai/state` 与 `.ai/runs`
- [x] `P1-T02` canonical task intake 落地
- [x] `P1-T03` 正式 `result.json` + markdown projection 双写
- [x] `P1-T03A` repo-owned config / worker-profile contract
- [x] `P1-T04` 一次真实 SDK 垂直切片
- [x] `P1-T05` `evidence_index.json` sha256 可重算

## Phase 2

- [x] `P2-T01` acceptance-and-gates authoritative spec
- [x] `P2-T02` run-state-and-handoff foundation
- [ ] `P2-T03` AgentBridge round-trip parity

## Phase 3

- [ ] `P3-T01` verification runner 固定 gate 顺序
- [ ] `P3-T02` path guard
- [ ] `P3-T03` worktree manager
- [ ] `P3-T04` cleanup manager

## Phase 4

- [ ] `P4-T01` planner adapter
- [ ] `P4-T02` review adapter
- [ ] `P4-T03` 正反触发谓词测试

## Phase 5

- [ ] `P5-T01` leases / retry / route / quota 收口
- [ ] `P5-T02` multi-worker simulation
- [ ] `P5-T03` remote_non_gui promotion evidence

## Phase 6

- [ ] `P6-T01` Hermes parity closeout
- [ ] `P6-T02` historical snapshot mapping
- [ ] `P6-T03` vm_gui conditional promotion evidence
