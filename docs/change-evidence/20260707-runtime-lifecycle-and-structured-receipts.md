# 2026-07-07 Runtime Lifecycle And Structured Receipts

## Slice

- `P3-T06` 这次把 repo-side lifecycle ops 从 schema 预留推进到真实 helper：`stale / cancelled / resumed` 现在可 materialize，`retry` 通过 `attempt + retry_rewind` 收口
- explicit `cancel / resume / retry` 现在会同步清理 active lease；`resume / retry` 还会刷新 `heartbeat_at / stale_after`，避免“刚恢复又立刻 stale”
- 这些 lifecycle ops 当前由 `task_lifecycle.py` 与 `host-orchestrator` CLI 入口共同承接，不再只停留在测试内或 prompt 资产层
- `P4-T04` 这次把 structured receipts 接进正式运行工件链：review-gated 路径现在会写 `review_result.json`，当前 planner/review/completed outcome 会写 `closeout_bundle.json`
- `result.json` 与 `dispatch_state.json` 现在会携带 `review_result_ref / closeout_bundle_ref`，`evidence_index.json` 也会把新的 receipt 工件纳入校验范围
- `P3-T01` 的 fixed gate order 这次同时在 backlog truth 中补齐：verification runner 当前固定按 `build -> lint -> typecheck -> test -> contract -> hotspot` 顺序留痕，真实执行仍只覆盖 `test / contract`

## Code Points

- `runtime/host-orchestrator/src/host_orchestrator/canonical_result.py`
- `runtime/host-orchestrator/src/host_orchestrator/host_local.py`
- `runtime/host-orchestrator/src/host_orchestrator/task_lifecycle.py`
- `runtime/host-orchestrator/src/host_orchestrator/cli.py`
- `runtime/host-orchestrator/src/host_orchestrator/agent_work_assets.py`
- `templates/dispatch-state.schema.json`
- `runtime/host-orchestrator/tests/test_lifecycle_ops.py`
- `runtime/host-orchestrator/tests/test_planner_adapter.py`
- `runtime/host-orchestrator/tests/test_wave1_execution.py`

## Boundary

- 当前 `review_result.json` 是 repo-side blocking review receipt；它表达的是“当前 gate 为什么阻断”，不等于 live `Claude Code + GLM-5.2` review sidecar 已接线
- 当前 lifecycle ops 只同步 `dispatch_state.json`、`runtime_tasks`、既有 `result.json` follow-up 字段与 `closeout_bundle.json`；它们不等于 multi-worker scheduler、route/quota engine、或 live accepted
- `retry` 当前复用 `resumed` 状态并通过 `attempt + retry_rewind` 留痕；并没有把新的 worker replay engine 写成当前事实
- `queued / input_required` 仍是保留状态，branch deletion 仍不自动化，`worktree` 仍只代表写入隔离

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest`：pass（55 passed）
- `python .\scripts\verify-planning-status.py`：pass
- `python .\scripts\select-next-work.py`：pass（`next_action = promote_phase1_execution`）
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit -Json`：pass
- `build` 与 `hotspot` 当前仍按 repo-owned `gate_na` 口径记录；替代验证分别是 `pytest` 与 `verifier + pytest + diff hygiene`
