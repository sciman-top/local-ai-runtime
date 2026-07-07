# 2026-07-07 Worktree Manager Minimal Slice

## Slice

- 这次把 `P3-T03` 从“只靠 prompt/模板约定的 isolated worktree”推进成 repo-side 已验证的最小 runtime manager
- 当前 `host_local` 在任务声明 `worktree_path != "."` 且调用入口仍位于 repo root 时，会：
  - 自动 create 或 reuse 对应的 linked worktree
  - 校验 worktree root 与 `branch_name`
  - 把 worker 与 verification 的 `cwd` 切到该 worktree
- 同一轮里，`result.json.cleanup_status` 现在开始表达最小 truth：
  - repo-root inline 执行任务：`inline_only`
  - declared isolated worktree 任务：`deferred`
- 当前还不会自动删除 worktree 或 branch；cleanup 仍留给下一刀

## Files

- `runtime/host-orchestrator/src/host_orchestrator/worktree_manager.py`
- `runtime/host-orchestrator/src/host_orchestrator/host_local.py`
- `runtime/host-orchestrator/src/host_orchestrator/canonical_result.py`
- `runtime/host-orchestrator/tests/test_path_guard.py`
- `runtime/host-orchestrator/tests/test_wave1_execution.py`
- `docs/architecture/planning-status.json`
- `docs/architecture/orchestrator-target-architecture.md`
- `docs/specs/task-contract.md`
- `docs/specs/result-contract.md`
- `docs/roadmap/orchestrator-roadmap.md`
- `docs/plans/orchestrator-implementation-plan.md`
- `docs/backlog/orchestrator-task-list.md`
- `docs/README.md`
- `docs/change-evidence/README.md`

## Boundary

- 当前只完成 repo-side **minimal** worktree manager
- 当前还没有把 `dispatch_state` 升级成 runtime 强制 ledger
- 当前还没有实现 `P3-T04` cleanup manager；runtime 只负责 create / reuse / record `deferred`，不会自动删除 worktree 或 branch
- 当前也没有接入 merge/commit receipt，所以 cleanup 仍必须保持 fail-safe，不得把未审查改动默默清掉
- 因此这次 closeout 只意味着 `P3-T03 repo-side done`，不等于 Phase 3 整体完成，也不等于 platform/live accepted

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_path_guard.py .\runtime\host-orchestrator\tests\test_wave1_execution.py`：pass（15 passed）
- `uv run --project .\runtime\host-orchestrator python -m pytest`：pass（46 passed）
- `python .\scripts\verify-planning-status.py`：pass
- `python .\scripts\select-next-work.py`：pass（`next_action = promote_phase1_execution`）
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit -Json`：pass
- `git diff --check`：pass
