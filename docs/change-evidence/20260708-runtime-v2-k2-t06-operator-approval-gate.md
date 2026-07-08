# 20260708 Runtime V2 K2-T06 Operator Approval Gate

## Goal

在 `--confirm-cutover-v2` 已存在的基础上，补上可验证的 operator approval evidence gate，避免单个确认参数绕过人工审批留痕后直接切换默认入口。

## Repo-Side Done

- 新增 `validate_cutover_operator_approval`
- 新增 CLI `--cutover-approval-ref`
- `--cutover-v2 --confirm-cutover-v2` 现在会在 `perform_cutover` 前执行：
  - cutover drill
  - cutover review summary
  - rollback restore drill
  - operator approval JSON validation
- approval JSON 必须满足：
  - `schema_version = runtime_v2_cutover_operator_approval.v1`
  - `approved = true`
  - `approved_by` 与 `approved_at` 非空
  - `review_summary_path` 指向当前 `.ai/runs-v2/_cutover/cutover-review-summary.json`
  - `rollback_drill_summary_path` 指向当前 `.ai/runs-v2/_cutover/cutover-rollback-drill-summary.json`
  - `acknowledged_risks` 包含 `default_entrypoint_switch` 与 `rollback_restore_required`
- approval 缺失或不匹配时写出 `.ai/runs-v2/_cutover/cutover-operator-approval-summary.json`，返回 `approval_required / cutover_performed=false`，且不修改 `runtime.active_version`

## Still Open

- `K2-T06` 仍未整体完成；真实默认入口仍未从 v1 切到 v2
- 真实仓没有提供 approval JSON，也没有执行 `--confirm-cutover-v2`
- 仍需真实 operator approval 文件模板、审批留痕流程，或更严格的 archive restore acceptance 条件
- 本次没有推进 `remote_non_gui` / `vm_gui` runner wiring，也不声明 `live accepted`

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_runtime_v2.py -k "operator_approval or confirmation_and_operator" -q`
- `uv run --project .\runtime\host-orchestrator python -m host_orchestrator --cutover-v2 --confirm-cutover-v2`：expected approval-required exit `1`; wrote `.ai/runs-v2/_cutover/cutover-operator-approval-summary.json`; left `runtime.active_version = v1`
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
- `docs/change-evidence/20260708-runtime-v2-k2-t06-operator-approval-gate.md`
