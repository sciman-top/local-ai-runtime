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
    - 2026-07-06 当前 selector 预期结果为 `phase1_prereq_probe_first`
- [x] `GOV-T03` add repo-level change-evidence index
  - Done when:
    - `docs/change-evidence/README.md` 与 dated evidence note 已落盘
  - Status note:
    - 2026-07-06 已补第一份 governed absorption evidence
- [x] `GOV-T04` add release-style preflight entrypoint
  - Done when:
    - `scripts/governance/preflight.ps1` 可执行
    - build / hotspot 缺口用 `gate_na` 明示
  - Status note:
    - 2026-07-06 已固化 repo-owned release-style preflight
- [x] `GOV-T04A` preflight line-ending hygiene closeout
  - Done when:
    - `.gitattributes` 显式覆盖 `*.py text eol=lf`
    - 当前治理脚本切片的 Python 文件不再触发 CRLF warning
    - `git diff --check` 回到零噪声
  - Status note:
    - 2026-07-06 已按“规则 + 定向修复”收敛 Python 行尾策略与当前 warning
- [x] `GOV-T05` wire docs, AGENTS, and proof routing
  - Done when:
    - README / docs / AGENTS 对 Governance Overlay 口径一致
  - Status note:
    - 2026-07-06 已完成 proof routing 与入口同步

治理任务完成后：

- 当前产品 active queue 仍然是 `PHASE-1-VERTICAL-SLICE`
- 当前预期 next action 仍然是 `phase1_prereq_probe_first`

## Phase 1

- [ ] `P1-T01` 默认 layout 迁到 `.ai/state` 与 `.ai/runs`
  - Done when:
    - `test_scaffold.py` 新断言为绿
- [ ] `P1-T02` canonical task intake 落地
  - Done when:
    - task loader 拒绝作者手写 `planner_required / review_required`
- [ ] `P1-T03` 正式 `result.json` + markdown projection 双写
  - Done when:
    - `result.json` 存在
    - markdown projection 仍存在
- [ ] `P1-T04` 一次真实 SDK 垂直切片
  - Done when:
    - 真实 task run 成功
    - mock 未被记为 live green
- [ ] `P1-T05` `evidence_index.json` sha256 可重算
  - Done when:
    - index 校验脚本通过

## Phase 2

- [ ] `P2-T01` 固化 task/result/review/run-index schema
- [ ] `P2-T02` AgentBridge round-trip parity

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
