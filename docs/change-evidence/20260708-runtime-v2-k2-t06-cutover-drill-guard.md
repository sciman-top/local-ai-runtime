# 20260708 Runtime V2 K2-T06 Cutover Drill Guard

## Goal

为 `runtime_v2` 增加第一批 cutover drill 与 fail-closed cutover guard，确保默认入口切换前的条件被机器化记录，而不是直接把目标态写成当前事实。

## Repo-Side Done

- 新增 `run_cutover_drill`
- 新增 CLI `--cutover-drill-v2`
- cutover drill 写出 `.ai/runs-v2/_cutover/cutover-drill-summary.json`
- `.gitignore` 现在忽略 `.ai/runs-v2/`，避免 repo-local drill / eval runtime artifacts 污染提交面
- cutover drill 检查：
  - `runtime.experimental_v2_enabled = true`
  - `runtime.active_version` 仍为 `v1`
  - 至少存在一条 completed v2 attempt
  - `--eval-regression-fixtures-v2` summary 为 ok
- `--cutover-v2` 现在先跑 cutover drill；drill 未 ready 时返回 blocked summary，且不修改 `runtime.active_version`

## Still Open

- `K2-T06` 仍未整体完成；默认入口仍未从 v1 切到 v2
- 仍需真实本地编码任务 v2 自动闭环证据、门禁与人工边界满足后，才允许实际 cutover
- 本次没有推进 `remote_non_gui` / `vm_gui` runner wiring，也不声明 `live accepted`

## Verification

- `python -m json.tool .\docs\architecture\planning-status.json`
- `uv run --project .\runtime\host-orchestrator python -m host_orchestrator --cutover-drill-v2`：expected blocked exit `1`; wrote `.ai/runs-v2/_cutover/cutover-drill-summary.json`; current blockers are `runtime_v2_enabled`, `completed_v2_attempt`, and `regression_fixture_eval`
- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_runtime_v2.py -k "cutover_drill or cutover_fails_closed" -q`
- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_runtime_v2.py -q`
- `uv run --project .\runtime\host-orchestrator python -m pytest`
- `python .\scripts\verify-planning-status.py`
- `python .\scripts\select-next-work.py`
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`
- `git diff --check`

## Rollback

用 git 回滚本切片涉及的同批 diff：

- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/migration.py`
- `runtime/host-orchestrator/src/host_orchestrator/cli.py`
- `runtime/host-orchestrator/tests/test_runtime_v2.py`
- `.gitignore`
- `docs/specs/runtime-v2-kernel.md`
- `docs/roadmap/orchestrator-roadmap.md`
- `docs/plans/orchestrator-implementation-plan.md`
- `docs/backlog/orchestrator-task-list.md`
- `docs/change-evidence/README.md`
- `docs/change-evidence/20260708-runtime-v2-k2-t06-cutover-drill-guard.md`
