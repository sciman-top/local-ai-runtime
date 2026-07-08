# 20260708 Runtime V2 K2-T05 Regression Fixture State Coverage

## Goal

把 `runtime_v2` 的 attempt-level `regression_fixture.json` 从 seed 扩展到当前核心状态路径，为后续 eval summary / regression runner 提供稳定、可机器比较的状态与 artifact refs 摘要。

## Repo-Side Done

- dependency-blocked attempt 会写出 `regression_fixture.json`，并记录 `regression_fixture_ref`
- admission-paused attempt 会写出 `regression_fixture.json`，并记录 `regression_fixture_ref`
- worker-failure retryable / failed attempt 会写出 `regression_fixture.json`，并记录 `regression_fixture_ref`
- retry queued attempt 会写出 `regression_fixture.json`，并记录 `source_attempt_id` 与 `retry_rewind`
- retry queued attempt 不伪造 `result.json`；fixture 的 `artifact_refs.result = null`
- 上述 fixture 均记录到 v2 `artifacts` 表的 `kind = regression_fixture`

## Still Open

- 后续 `20260708-runtime-v2-k2-t05-regression-eval-summary.md` 已补最小 `--eval-regression-fixtures-v2` summary
- `runtime_v2` 仍是 experimental dual-track，默认入口仍未从 v1 切换
- `planning-status.current_active_queue` 仍保持 `PHASE-1-VERTICAL-SLICE`
- 本次没有推进 `remote_non_gui` / `vm_gui` runner wiring，也不声明 `live accepted`

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_runtime_v2.py -k "dependency_block_writes_regression_fixture or admission_pause_writes_regression_fixture or worker_failure_writes_regression_fixture or retry_attempt_writes_queued_regression_fixture" -q`
- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_runtime_v2.py -q`
- `uv run --project .\runtime\host-orchestrator python -m pytest`
- `python .\scripts\verify-planning-status.py`
- `python .\scripts\select-next-work.py`
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`
- `git diff --check`

## Rollback

用 git 回滚本切片涉及的同批 diff：

- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/runner.py`
- `runtime/host-orchestrator/tests/test_runtime_v2.py`
- `docs/specs/runtime-v2-kernel.md`
- `docs/roadmap/orchestrator-roadmap.md`
- `docs/plans/orchestrator-implementation-plan.md`
- `docs/backlog/orchestrator-task-list.md`
- `docs/change-evidence/README.md`
- `docs/change-evidence/20260708-runtime-v2-k2-t05-regression-fixture-state-coverage.md`
