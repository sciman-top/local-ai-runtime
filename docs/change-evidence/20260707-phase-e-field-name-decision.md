# 2026-07-07 Phase-E Field-Name Decision

## Slice

- 本次切片只收口 `E-T01` 的最后一个决策缺口
- 目标不是改协议字段，而是把当前 repo-side closeout 的字段名边界写成明确决策，并同步回当前机器真源与 contract / README 入口

## Decision

- `compatibility_projection_ref` 继续保持现名
- `lane` 继续保持现名
- 当前不在 repo-side parity / topology closeout 中做字段改名
- 是否需要 schema rename，待 live planner/review sidecar 与 non-host_local runner 真接线后再复评

## Why

- 当前 repo-side runtime、tests、evidence、projection、以及 docs 都已经围绕这两个字段闭环
- 现阶段继续改名不会提高当前 repo-side truth 的证明强度，反而会把一次已经验证通过的 parity / topology closeout 重新扩成协议迁移
- 当前仍没有 live planner/review sidecar 或 non-host_local runner 的真实接线证据，因此不应把字段迁移写成当前必要动作

## Evidence

- `README.md`
- `docs/architecture/planning-status.json`
- `docs/architecture/orchestrator-target-architecture.md`
- `docs/specs/result-contract.md`
- `docs/README.md`
- `docs/plans/orchestrator-implementation-plan.md`
- `docs/backlog/orchestrator-task-list.md`
- `runtime/host-orchestrator/tests/test_agentbridge_intake.py`
- `runtime/host-orchestrator/tests/test_wave1_execution.py`

## Boundary

- 这不是字段迁移已完成
- 这不是 `platform compatibility green`
- 这不是 `live accepted`
- 这只是当前 repo-side closeout 的“保持现名”决策
