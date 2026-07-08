# 20260708 Runtime V2 K2-T06 Operator Runbook

## Goal

在 cutover drill、rollback drill、archive restore acceptance 与 operator approval gate 都已有代码面支撑后，补上真实人工审批 / cutover / restore 操作 runbook，避免后续 operator 把 repo-side ready 误读成已执行或已验收。

## Repo-Side Done

- 新增 `docs/runbooks/runtime-v2-cutover-operator-runbook.md`
- runbook 明确：
  - 当前默认入口仍是 v1
  - `experimental_v2_enabled=true` 不等于 default cutover
  - dry-run 顺序与预期状态
  - approval JSON 人工填写要求
  - confirmed cutover 的唯一命令形态
  - restore 仍是人工高风险操作，当前没有自动 restore 命令
  - `.ai/runs-v2/`、`.ai/archive/`、approval JSON、approval audit JSON 默认不提交
  - 最终汇报必须区分 `repo-side done / confirmed cutover executed / rollback restored / live accepted / still open`
- docs index、runtime v2 spec、plan、backlog、roadmap、planning-status 与 change-evidence index 已引用该 runbook

## Still Open

- `K2-T06` 仍未整体完成；真实默认入口仍未从 v1 切到 v2
- 真实仓仍没有人工签署的 approval JSON，也没有执行 confirmed cutover
- 自动 restore 命令仍未实现；restore 仍是人工高风险操作
- 本次没有推进 `remote_non_gui` / `vm_gui` runner wiring，也不声明 `live accepted`

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest`：`113 passed`
- `python .\scripts\verify-planning-status.py`：`status=pass`; `authoritative_doc_count=19`; `proof_ref=docs/change-evidence/20260708-runtime-v2-k2-t06-operator-runbook.md`
- `python .\scripts\select-next-work.py`：`status=pass`; `next_action=promote_phase1_execution`
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`：pass; build/hotspot remain project-defined `gate_na`
- `git diff --check`：pass

## Rollback

用 git 回滚本切片涉及的同批 diff：

- `docs/runbooks/runtime-v2-cutover-operator-runbook.md`
- `docs/README.md`
- `docs/specs/runtime-v2-kernel.md`
- `docs/roadmap/orchestrator-roadmap.md`
- `docs/plans/orchestrator-implementation-plan.md`
- `docs/backlog/orchestrator-task-list.md`
- `docs/architecture/planning-status.json`
- `docs/change-evidence/README.md`
- `docs/change-evidence/20260708-runtime-v2-k2-t06-operator-runbook.md`
