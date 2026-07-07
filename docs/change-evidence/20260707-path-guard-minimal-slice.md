# 2026-07-07 Path Guard Minimal Slice

## Slice

- 这次把 `P3-T02` 从 prompt 约定推进成 repo-side 已验证的最小 runtime guard
- canonical task 现在会在进入 worker 前先做两层 fail-closed 校验：
  - `worktree_path / allowed_paths / forbidden_paths / artifacts_out` 必须保持 repo-relative，不能使用绝对路径或 `..` 逃逸
  - 当任务显式声明独立 worktree 时，`workspace_root`、Git root、当前 branch 必须与 `worktree_path / branch_name` 匹配
- guard 通过后，worker 与 verification 都在声明的 worktree `cwd` 中执行；guard 失败则任务进入 `failed` 并留下 `task_failed` 事件

## Files

- `runtime/host-orchestrator/src/host_orchestrator/path_guard.py`
- `runtime/host-orchestrator/src/host_orchestrator/host_local.py`
- `runtime/host-orchestrator/tests/test_path_guard.py`
- `docs/architecture/planning-status.json`
- `docs/architecture/orchestrator-target-architecture.md`
- `docs/specs/task-contract.md`
- `docs/roadmap/orchestrator-roadmap.md`
- `docs/plans/orchestrator-implementation-plan.md`
- `docs/backlog/orchestrator-task-list.md`
- `docs/README.md`
- `docs/change-evidence/README.md`

## Boundary

- 当前只完成 repo-side **minimal** path guard
- 当前还没有把 `allowed_paths` 升级成真实写入拦截器；这轮只校验 path claim 不能越界
- 当前还没有实现 `P3-T03` worktree manager、`P3-T04` cleanup manager，worktree 生命周期仍未自动化
- 当前也没有把 `dispatch_state` / `closeout_bundle` 升级成 runtime 强制状态机
- 因此这次 closeout 只意味着 `P3-T02` 的 repo-side 最小 guard 已落地，不等于多 worker orchestration、live accepted、或 platform compatibility green

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_path_guard.py`：pass（4 passed）
- `uv run --project .\runtime\host-orchestrator python -m pytest`：pass（46 passed）
- `python .\scripts\verify-planning-status.py`：pass
- `python .\scripts\select-next-work.py`：pass（`next_action = promote_phase1_execution`）
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit -Json`：pass
- `git diff --check`：pass
