# 20260708 Runtime V2 K2-T06 Cutover Review Rollback Drill

## Goal

在 `--cutover-drill-v2` 已 ready 的前提下，为 `runtime_v2` 默认入口切换补上人工确认边界、review summary 与 rollback plan，避免 `--cutover-v2` 在无人确认时直接把 `runtime.active_version` 从 `v1` 切到 `v2`。

## Repo-Side Done

- 新增 `run_cutover_review`
- 新增 CLI `--confirm-cutover-v2`
- `--cutover-v2` 保留原有 fail-closed drill 行为：drill 未 ready 时仍返回 drill blocked summary，且不修改 `runtime.active_version`
- drill ready 后，默认 `--cutover-v2` 写出 `.ai/runs-v2/_cutover/cutover-review-summary.json`，返回 `manual_approval_required / cutover_performed=false`，且不修改 `runtime.active_version`
- 只有显式传入 `--cutover-v2 --confirm-cutover-v2` 时，CLI 才进入已有 `perform_cutover` 路径
- review summary 记录 prospective changes 与 rollback plan，包括恢复 `.ai/config/orchestrator.yaml` 的 `runtime.active_version = v1`、恢复 legacy db/runs archive、以及 git 恢复入口

## Still Open

- `K2-T06` 仍未整体完成；真实默认入口仍未从 v1 切到 v2
- 真实仓没有执行 `--confirm-cutover-v2`
- 仍需 confirmed cutover 前的 operator review 证据、archive 恢复演练或更完整的 rollback restore check
- 本次没有推进 `remote_non_gui` / `vm_gui` runner wiring，也不声明 `live accepted`

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_runtime_v2.py -k "cutover_review or explicit_confirmation or cutover_fails_closed" -q`
- `uv run --project .\runtime\host-orchestrator python -m host_orchestrator --cutover-v2`：expected manual-approval exit `1`; wrote `.ai/runs-v2/_cutover/cutover-review-summary.json`; left `runtime.active_version = v1`
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
- `docs/specs/runtime-v2-kernel.md`
- `docs/roadmap/orchestrator-roadmap.md`
- `docs/plans/orchestrator-implementation-plan.md`
- `docs/backlog/orchestrator-task-list.md`
- `docs/architecture/planning-status.json`
- `docs/change-evidence/README.md`
- `docs/change-evidence/20260708-runtime-v2-k2-t06-cutover-review-rollback-drill.md`
