# 20260708 Runtime V2 K2-T06 Archive Restore Acceptance

## Goal

在 rollback drill 已存在的基础上，补上 archive restore acceptance 摘要，避免只验证 archive 目录可用就把 confirmed cutover 视为可恢复。

## Repo-Side Done

- `--cutover-rollback-drill-v2` 现在会同步写出 `.ai/runs-v2/_cutover/archive-restore-acceptance.json`
- restore acceptance 检查：
  - archive root 可用
  - v1 control-plane DB 源存在
  - v1 runs 源目录存在
  - rollback plan 仍指向 `.ai/config/orchestrator.yaml` 并恢复 `runtime.active_version = v1`
- 缺少 v1 DB 或 v1 runs 源时，rollback drill 返回 `blocked / rollback_ready=false / restore_performed=false`
- ready path 仍不执行 restore、不切换默认入口；confirmed cutover 仍必须通过 operator approval gate

## Still Open

- `K2-T06` 仍未整体完成；真实默认入口仍未从 v1 切到 v2
- 真实仓仍没有人工签署的 approval JSON，也没有执行 confirmed cutover
- 真实人工审批 / cutover / restore 操作 runbook 仍待补充
- 本次没有推进 `remote_non_gui` / `vm_gui` runner wiring，也不声明 `live accepted`

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_runtime_v2.py -k restore_sources_are_missing -q`：red first 后 green，最终 `1 passed, 33 deselected`
- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_runtime_v2.py -k "rollback_drill or approval_template or confirmation_and_operator" -q`：`4 passed, 30 deselected`
- `uv run --project .\runtime\host-orchestrator python -m host_orchestrator --cutover-rollback-drill-v2`：真实仓 safe probe 返回 `status=ready / rollback_ready=true / restore_performed=false / active_version=v1`，并写出 `archive_restore_acceptance_path`
- `uv run --project .\runtime\host-orchestrator python -m pytest`：`113 passed`
- `python .\scripts\verify-planning-status.py`：`status=pass`; `proof_ref=docs/change-evidence/20260708-runtime-v2-k2-t06-archive-restore-acceptance.md`
- `python .\scripts\select-next-work.py`：`status=pass`; `next_action=promote_phase1_execution`
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`：pass; build/hotspot remain project-defined `gate_na`
- `git diff --check`：pass
- `git ls-files .ai\runs-v2 .ai\archive`：no tracked runtime archive/artifact files

## Rollback

用 git 回滚本切片涉及的同批 diff：

- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/migration.py`
- `runtime/host-orchestrator/tests/test_runtime_v2.py`
- `docs/specs/runtime-v2-kernel.md`
- `docs/roadmap/orchestrator-roadmap.md`
- `docs/plans/orchestrator-implementation-plan.md`
- `docs/backlog/orchestrator-task-list.md`
- `docs/architecture/planning-status.json`
- `docs/change-evidence/README.md`
- `docs/change-evidence/20260708-runtime-v2-k2-t06-archive-restore-acceptance.md`
