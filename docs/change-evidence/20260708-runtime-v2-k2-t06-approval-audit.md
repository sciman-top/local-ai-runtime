# 20260708 Runtime V2 K2-T06 Approval Audit

## Goal

在 approval template 与 approval gate 之后，补上 approval validation 的可追溯审计摘要，确保真实 cutover 前能证明审批文件内容、操作者字段和风险确认来源。

## Repo-Side Done

- approval validation 现在记录：
  - `approval_sha256`
  - `approval_byte_count`
  - `approved_by`
  - `approved_at`
  - `approval_audit_path`
- 新增 sanitized `operator-approval-audit.json`
- audit payload 只记录 approval schema 所需字段与 source hash，不复制 approval JSON 的任意额外字段
- 默认未批准模板进入 validation 时仍返回 `approval_required / cutover_performed=false`
- 人工补齐 `approved=true / approved_by / approved_at` 后，approval validation 可返回 `approved`，但 validation 本身仍不执行 cutover

## Still Open

- `K2-T06` 仍未整体完成；真实默认入口仍未从 v1 切到 v2
- 真实仓仍没有人工签署的 approval JSON，也没有执行 confirmed cutover
- 仍需更严格的 archive restore acceptance 条件，或真实人工审批流程的外部操作 runbook
- 本次没有推进 `remote_non_gui` / `vm_gui` runner wiring，也不声明 `live accepted`

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_runtime_v2.py -k "cutover_approval_template or operator_approval or confirmation_and_operator" -q`
- `uv run --project .\runtime\host-orchestrator python -m host_orchestrator --cutover-v2 --confirm-cutover-v2 --cutover-approval-ref .ai\runs-v2\_cutover\operator-approval.template.json`：expected fail-closed exit `1`; wrote `approval_sha256 / approval_byte_count / operator-approval-audit.json`; left `runtime.active_version = v1`
- `uv run --project .\runtime\host-orchestrator python -m pytest`：`112 passed`
- `python .\scripts\verify-planning-status.py`：`status=pass`; `proof_ref=docs/change-evidence/20260708-runtime-v2-k2-t06-approval-audit.md`
- `python .\scripts\select-next-work.py`：`status=pass`; `next_action=promote_phase1_execution`
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`：pass; build/hotspot remain project-defined `gate_na`
- `git diff --check`

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
- `docs/change-evidence/20260708-runtime-v2-k2-t06-approval-audit.md`
