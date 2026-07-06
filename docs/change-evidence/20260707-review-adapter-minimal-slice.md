# 2026-07-07 Review Adapter Minimal Slice

## Slice

- `P4-T02` 这次只把 repo-side 最小 review gate 接到 `host_local`
- 当前命中 `review_required` 时，worker 与 verification 仍会先执行，然后正式结果停在 `needs_review`
- 当前只证明 repo-side `needs_review` / `waiting_handoff` / `completed` 三种终态都能按真实条件写出正式工件

## Code Points

- `runtime/host-orchestrator/src/host_orchestrator/canonical_task.py`
- `runtime/host-orchestrator/src/host_orchestrator/host_local.py`
- `runtime/host-orchestrator/src/host_orchestrator/wave1_smoke.py`
- `runtime/host-orchestrator/tests/test_planner_adapter.py`
- `runtime/host-orchestrator/tests/test_wave1_execution.py`

## Boundary

- 当前只完成 repo-side review gate 与 `needs_review` 状态落点
- 当前 `review_required` 只基于已 materialize 的 `risk_level / write_access / policy_surface` 判定
- 当前没有接入 live `Claude Code + GLM-5.2` reviewer
- 当前没有落盘 review result artifact 到 `.ai/runs/...`
- 当前没有进入 `P4-T03` 正反谓词完整收口
- 当前没有进入 `P5` leases / retry / route / quota 收口

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_planner_adapter.py`：pass（7 passed）
- `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_wave1_execution.py`：pass（11 passed）
- `uv run --project .\runtime\host-orchestrator python -m pytest`：pass（37 passed）
- `python .\scripts\verify-planning-status.py`：pass
- `python .\scripts\select-next-work.py`：pass（`next_action = promote_phase1_execution`）
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit -Json`：pass
