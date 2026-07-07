# 2026-07-07 Cleanup Manager Minimal Slice

## Slice

- 这次把 `P3-T04` 从“isolated worktree 只会留下 `deferred`，完全靠人工决定后续 cleanup”推进成 repo-side 已验证的最小 cleanup manager
- 当前 `host_local` 在 declared isolated worktree 场景下会：
  - 对 runtime 自己 create/reuse 管理、且 clean 的 linked worktree 自动执行 `git worktree remove`
  - 对 review-pending、failed、dirty、或外部直接启动的 isolated worktree 显式保留，并写出 `worktree_cleanup` 事件
  - 在 `result.json.cleanup_status` 中写出 `cleaned / deferred / cleanup_failed`
- 当前 branch deletion 仍不自动化；`dispatch_state` 仍未 runtime 化

## Files

- `runtime/host-orchestrator/src/host_orchestrator/worktree_manager.py`
- `runtime/host-orchestrator/src/host_orchestrator/host_local.py`
- `runtime/host-orchestrator/src/host_orchestrator/canonical_result.py`
- `runtime/host-orchestrator/tests/test_path_guard.py`
- `docs/architecture/planning-status.json`
- `docs/architecture/orchestrator-target-architecture.md`
- `docs/specs/task-contract.md`
- `docs/specs/result-contract.md`
- `docs/specs/run-state-and-handoff.md`
- `docs/roadmap/orchestrator-roadmap.md`
- `docs/plans/orchestrator-implementation-plan.md`
- `docs/backlog/orchestrator-task-list.md`
- `docs/README.md`
- `docs/change-evidence/README.md`

## Boundary

- 当前只完成 repo-side **minimal** cleanup manager
- 当前不会自动 delete branch，也不会替代人工 review / closeout / merge 决策
- `deferred` 当前仍是正式 truth：表示 worktree 被显式保留给 review、调试、或人工 cleanup
- `cleanup_failed` 当前只表示 runtime 已尝试 remove clean managed worktree，但 git remove 本身失败
- 因此这次 closeout 只意味着 `P3-T04 repo-side done`，不等于 `dispatch_state` 已 runtime 化，也不等于 platform/live accepted

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_path_guard.py`：pass（7 passed）
- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_wave1_execution.py .\runtime\host-orchestrator\tests\test_planner_adapter.py .\runtime\host-orchestrator\tests\test_agent_work_assets.py`：pass（24 passed）
