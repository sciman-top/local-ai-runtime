# 20260708 Runtime V2 K2-T05 Regression Eval Summary

## Goal

为 `runtime_v2` 增加最小 repo-side regression fixture evaluator，使已记录的 `regression_fixture.json` 能被统一扫描、校验并汇总。

## Repo-Side Done

- 新增 `runtime_v2.evaluation.evaluate_regression_fixtures`
- 新增 CLI `--eval-regression-fixtures-v2`
- evaluator 从 v2 `artifacts` 表读取 `kind = regression_fixture`
- evaluator 校验 fixture schema、required fields、missing fixture files，并汇总 status / next_action counts
- evaluator 写出 `.ai/runs-v2/_eval/regression-fixture-summary.json`
- CLI 返回 evaluator JSON；当无 fixture、缺文件或 schema/字段校验失败时 `ok = false`

## Still Open

- `runtime_v2` 仍是 experimental dual-track，默认入口仍未从 v1 切换
- `planning-status.current_active_queue` 仍保持 `PHASE-1-VERTICAL-SLICE`
- 本次没有推进 `remote_non_gui` / `vm_gui` runner wiring，也不声明 `live accepted`
- 更完整的历史 corpus / cross-version benchmark 可作为后续 hardening，但不阻塞当前 scoped K2-T05 repo-side closeout

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_runtime_v2.py -k regression_fixture_eval_summary_and_cli -q`
- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_runtime_v2.py -q`
- `uv run --project .\runtime\host-orchestrator python -m pytest`
- `python .\scripts\verify-planning-status.py`
- `python .\scripts\select-next-work.py`
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`
- `git diff --check`

## Rollback

用 git 回滚本切片涉及的同批 diff：

- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/evaluation.py`
- `runtime/host-orchestrator/src/host_orchestrator/cli.py`
- `runtime/host-orchestrator/tests/test_runtime_v2.py`
- `docs/specs/runtime-v2-kernel.md`
- `docs/roadmap/orchestrator-roadmap.md`
- `docs/plans/orchestrator-implementation-plan.md`
- `docs/backlog/orchestrator-task-list.md`
- `docs/change-evidence/README.md`
- `docs/change-evidence/20260708-runtime-v2-k2-t05-regression-eval-summary.md`
