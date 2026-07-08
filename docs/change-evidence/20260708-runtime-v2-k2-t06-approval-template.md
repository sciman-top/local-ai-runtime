# 20260708 Runtime V2 K2-T06 Approval Template

## Goal

在 operator approval evidence gate 之后，补上可重复生成的 approval JSON 模板，避免真实 cutover 前依赖手写字段，同时保持默认入口不切换。

## Repo-Side Done

- 新增 `write_cutover_operator_approval_template`
- 新增 CLI `--cutover-approval-template-v2`
- 新增可选输出参数 `--cutover-approval-template-output`
- 模板生成会先刷新：
  - cutover drill summary
  - cutover review summary
  - rollback restore drill summary
- 模板默认写入 `approved=false`、空 `approved_by`、空 `approved_at`
- 模板包含当前 review / rollback drill summary 引用与 `default_entrypoint_switch / rollback_restore_required` 风险项
- 模板生成和模板 validation 都不会调用 `perform_cutover`

## Still Open

- `K2-T06` 仍未整体完成；真实默认入口仍未从 v1 切到 v2
- 真实仓仍没有人工签署的 approval JSON，也没有执行 confirmed cutover
- 仍需审批留痕流程，或更严格的 archive restore acceptance 条件
- 本次没有推进 `remote_non_gui` / `vm_gui` runner wiring，也不声明 `live accepted`

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_runtime_v2.py -k "cutover_approval_template or operator_approval or confirmation_and_operator" -q`
- `uv run --project .\runtime\host-orchestrator python -m host_orchestrator --cutover-approval-template-v2`：`template_written=true / cutover_performed=false`; left `runtime.active_version = v1`
- `uv run --project .\runtime\host-orchestrator python -m pytest`：`112 passed`
- `python .\scripts\verify-planning-status.py`：`status=pass`; `proof_ref=docs/change-evidence/20260708-runtime-v2-k2-t06-approval-template.md`
- `python .\scripts\select-next-work.py`：`status=pass`; `next_action=promote_phase1_execution`
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`：pass; build/hotspot remain project-defined `gate_na`
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
- `docs/change-evidence/20260708-runtime-v2-k2-t06-approval-template.md`
