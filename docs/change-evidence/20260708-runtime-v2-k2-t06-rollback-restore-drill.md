# 20260708 Runtime V2 K2-T06 Rollback Restore Drill

## Goal

在真实默认入口仍保持 `v1` 的前提下，为 `runtime_v2` cutover 前的恢复路径补一个可重跑、非破坏的 rollback restore drill，确认人工确认前至少具备机器化恢复路径证据。

## Repo-Side Done

- 新增 `run_cutover_rollback_drill`
- 新增 CLI `--cutover-rollback-drill-v2`
- rollback drill 会先 materialize cutover review summary，然后检查：
  - review summary 仍处于 `manual_approval_required`
  - rollback plan 指向 `.ai/config/orchestrator.yaml` 并要求恢复 `runtime.active_version = v1`
  - archive root 可创建 / 可用
  - 当前默认入口仍为 `runtime.active_version = v1`
- rollback drill 写出 `.ai/runs-v2/_cutover/cutover-rollback-drill-summary.json`
- rollback drill 不执行 restore，不执行 confirmed cutover，不修改默认入口

## Still Open

- `K2-T06` 仍未整体完成；真实默认入口仍未从 v1 切到 v2
- 真实仓没有执行 `--confirm-cutover-v2`
- 仍需 confirmed cutover 前的 operator review 证据与更严格的 archive restore acceptance 条件
- 本次没有推进 `remote_non_gui` / `vm_gui` runner wiring，也不声明 `live accepted`

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_runtime_v2.py -k rollback_drill -q`
- `uv run --project .\runtime\host-orchestrator python -m host_orchestrator --cutover-rollback-drill-v2`：expected ready exit `0`; wrote `.ai/runs-v2/_cutover/cutover-rollback-drill-summary.json`; left `runtime.active_version = v1`
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
- `docs/change-evidence/20260708-runtime-v2-k2-t06-rollback-restore-drill.md`
