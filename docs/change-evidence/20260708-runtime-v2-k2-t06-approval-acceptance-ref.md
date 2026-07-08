# 20260708 Runtime V2 K2-T06 Approval Acceptance Ref

## Goal

在 archive restore acceptance 与 operator approval gate 都已存在后，收紧 confirmed cutover 前的人工审批证据：approval JSON 必须显式引用当前 `archive-restore-acceptance.json`，避免人工只看 review / rollback drill summary 就批准默认入口切换。

## Repo-Side Done

- `validate_cutover_operator_approval(...)` 新增 `archive_restore_acceptance_ref` 检查
- 缺少当前 `archive_restore_acceptance_path` 引用的 approval JSON 返回 `approval_required / cutover_performed=false`
- `--cutover-approval-template-v2` 生成的默认未批准模板现在包含 `archive_restore_acceptance_path`
- sanitized `operator-approval-audit.json` 现在记录 approval JSON 中的 `archive_restore_acceptance_path`
- confirmed cutover 成功输出现在包含 `cutover_archive_restore_acceptance_path`
- runtime v2 spec、operator runbook、plan、backlog、roadmap、planning-status 与 change-evidence index 已同步该边界

## Still Open

- `K2-T06` 仍未整体完成；真实默认入口仍未从 v1 切到 v2
- 真实仓仍没有人工签署的 approval JSON，也没有执行 confirmed cutover
- 本次没有新增自动 restore 命令；restore 仍是人工高风险操作
- 本次没有推进 `remote_non_gui` / `vm_gui` runner wiring，也不声明 `live accepted`

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_runtime_v2.py::test_runtime_v2_cutover_approval_requires_archive_restore_acceptance_ref`：red first，缺少 acceptance ref 时旧实现错误返回 `approved`
- `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_runtime_v2.py::test_runtime_v2_cutover_approval_requires_archive_restore_acceptance_ref runtime\host-orchestrator\tests\test_runtime_v2.py::test_runtime_v2_cutover_approval_template_is_non_destructive_and_editable runtime\host-orchestrator\tests\test_runtime_v2.py::test_runtime_v2_cli_cutover_requires_confirmation_and_operator_approval`：`3 passed`
- `uv run --project .\runtime\host-orchestrator python -m pytest`：`114 passed`
- `python .\scripts\verify-planning-status.py`：`status=pass`; `authoritative_doc_count=19`; `proof_ref=docs/change-evidence/20260708-runtime-v2-k2-t06-approval-acceptance-ref.md`
- `python .\scripts\select-next-work.py`：`status=pass`; `next_action=promote_phase1_execution`
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`：pass; build/hotspot remain project-defined `gate_na`
- `git diff --check`：pass
- `git ls-files .ai\runs-v2 .ai\archive`：no tracked runtime archive/artifact files

## Rollback

用 git 回滚本切片涉及的同批 diff：

- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/migration.py`
- `runtime/host-orchestrator/src/host_orchestrator/cli.py`
- `runtime/host-orchestrator/tests/test_runtime_v2.py`
- `docs/specs/runtime-v2-kernel.md`
- `docs/runbooks/runtime-v2-cutover-operator-runbook.md`
- `docs/roadmap/orchestrator-roadmap.md`
- `docs/plans/orchestrator-implementation-plan.md`
- `docs/backlog/orchestrator-task-list.md`
- `docs/architecture/planning-status.json`
- `docs/change-evidence/README.md`
- `docs/change-evidence/20260708-runtime-v2-k2-t06-approval-acceptance-ref.md`
