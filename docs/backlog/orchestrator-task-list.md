# Orchestrator Task List

## Phase 0'

- [x] `P0'-T01` 落主真源与 verifier
  - Done when:
    - `docs/architecture/planning-status.json` 存在
    - `python scripts/verify-planning-status.py` 通过
  - Status note:
    - 2026-07-06 已落盘并可通过 verifier
- [x] `P0'-T02` 改写 impl_pack 四入口
  - Done when:
    - 不再出现 greenfield 口径
  - Status note:
    - 2026-07-06 已统一为基于 `runtime/host-orchestrator` 的落点说明
- [x] `P0'-T03` 下沉 Hermes 主线文档
  - Done when:
    - 顶层旧入口全部变成明确指针页或降级页
  - Status note:
    - 2026-07-06 顶层旧 Hermes 入口已降级为指针页，兼容正文下沉到 `docs/platforms/hermes/`

## Governance Overlay

- [x] `GOV-T01` formalize governed reference companion
  - Done when:
    - `governed-ai-coding-runtime` 以 `governance-sidecar` 进入 manifest / references / observation surfaces
  - Status note:
    - 2026-07-06 已正式纳入 companion 参考面，不进入 `default_refresh_set`
- [x] `GOV-T02` split selector from verifier
  - Done when:
    - `scripts/select-next-work.py` 独立返回下一步动作
    - `scripts/verify-planning-status.py` 只做一致性校验
  - Status note:
    - 2026-07-06 prerequisite probes ready 后，当前 selector 预期结果已提升为 `promote_phase1_execution`
- [x] `GOV-T03` add repo-level change-evidence index
  - Done when:
    - `docs/change-evidence/README.md` 与 dated evidence note 已落盘
  - Status note:
    - 2026-07-06 已补齐 repo-level change evidence index
- [x] `GOV-T04` add release-style preflight entrypoint
  - Done when:
    - `scripts/governance/preflight.ps1` 可执行
    - build / hotspot 缺口用 `gate_na` 明示
  - Status note:
    - 2026-07-06 已固化 repo-owned release-style preflight
- [x] `GOV-T05` wire docs, AGENTS, and proof routing
  - Done when:
    - README / docs / AGENTS 对 Governance Overlay 口径一致
  - Status note:
    - 2026-07-06 已完成 proof routing 与入口同步
- [x] `GOV-T06` selector policy verifier coverage
  - Done when:
    - `next-work-selection-policy.json` 进入 authoritative/verifier 视野
    - `review_expires_at` 只做存在性与 ISO 形状校验
  - Status note:
    - 2026-07-06 verifier 与 selector 的 policy 边界已分离
- [x] `GOV-T07` impl_pack stale demotion and machine checks
  - Done when:
    - stale/legacy marker 可被 verifier 机器检查
    - `00_README_FIRST.md` 不再把 stale `05` 当主读入口
  - Status note:
    - 2026-07-06 impl_pack stale/legacy 标识与 verifier 覆盖已同步

治理任务完成后：

- 当前产品 active queue 仍然是 `PHASE-1-VERTICAL-SLICE`
- 当前预期 next action 已是 `promote_phase1_execution`

## Phase 1

- [x] `P1-T01` 默认 layout 迁到 `.ai/state` 与 `.ai/runs`
  - Done when:
    - `test_scaffold.py` 新断言为绿
  - Status note:
    - 2026-07-06 `RuntimeLayout` 默认路径已切到 `.ai/state/control-plane.db` 与 `.ai/runs`
- [x] `P1-T02` canonical task intake 落地
  - Done when:
    - task loader 拒绝作者手写 `planner_required / review_required`
  - Status note:
    - 2026-07-06 canonical task loader 与 authored-derived-field 拒绝测试已落盘
- [x] `P1-T03` 正式 `result.json` + markdown projection 双写
  - Done when:
    - `result.json` 存在
    - markdown projection 仍存在
  - Status note:
    - 2026-07-06 host-local runtime 已写出 canonical run artifacts 与 compatibility projection
- [x] `P1-T03A` repo-owned config / worker-profile contract
  - Done when:
    - `.ai/config/*.yaml` 成为运行时真源
    - 缺失配置返回 deterministic contract error
  - Status note:
    - 2026-07-06 已移除运行时代码中的静默默认值回退
- [x] `P1-T04` 一次真实 SDK 垂直切片
  - Done when:
    - 真实 task run 成功
    - mock 未被记为 live green
  - Status note:
    - 2026-07-06 已用 `Codex SDK` 在隔离工作区中完成一次非 mock canonical runtime vertical slice
- [ ] `P1-T05` `evidence_index.json` sha256 可重算
  - Done when:
    - index 校验脚本通过

## Phase 2

- [x] `P2-T01` acceptance-and-gates authoritative spec
  - Done when:
    - PRD 四档 acceptance tiers 与 `mock green` / `live probe ready` 映射固定
  - Status note:
    - 2026-07-06 新 spec 已落盘，未新增冲突 tier
- [x] `P2-T02` run-state-and-handoff foundation
  - Done when:
    - `run_id / attempt / handoff_required / next_action` 契约已落盘
  - Status note:
    - 2026-07-06 已明确 Phase 1-4 foundation 边界
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

- [ ] `P5-T01` 控制面新增 4 表
- [ ] `P5-T02` repo/branch/worker quota
- [ ] `P5-T03` multi-worker simulation

## Phase 6

- [ ] `P6-T01` Hermes parity closeout
- [ ] `P6-T02` historical snapshot mapping
- [ ] `P6-T03` markdown projection compatibility
