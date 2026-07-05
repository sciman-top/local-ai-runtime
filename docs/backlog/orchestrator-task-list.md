# Orchestrator Task List

## Phase 0'

- [ ] `P0'-T01` 落主真源与 verifier
  - Done when:
    - `docs/architecture/planning-status.json` 存在
    - `python scripts/verify-planning-status.py` 通过
- [ ] `P0'-T02` 改写 impl_pack 四入口
  - Done when:
    - 不再出现 greenfield 口径
- [ ] `P0'-T03` 下沉 Hermes 主线文档
  - Done when:
    - 顶层旧入口全部变成明确指针页或降级页

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
