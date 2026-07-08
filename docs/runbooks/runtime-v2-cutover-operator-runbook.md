# Runtime V2 Cutover Operator Runbook

更新时间：`2026-07-08`

## 1. Scope And Truth Boundary

这份 runbook 只定义 `runtime_v2` 默认入口切换前后的人工操作流程。它不代表当前真实仓已经完成 cutover。

当前 repo truth：

- 默认入口仍是 `.ai/config/orchestrator.yaml` 中的 `runtime.active_version: v1`
- `runtime.experimental_v2_enabled: true` 只表示 v2 dual-track 可用，不表示默认入口已切换
- `--cutover-v2` 默认只写 review summary 并返回 `manual_approval_required`
- `--confirm-cutover-v2` 仍必须绑定通过校验的 `--cutover-approval-ref`
- `--cutover-rollback-drill-v2` 只做非破坏恢复验收，不执行 restore
- `archive-restore-acceptance.json` 是恢复验收摘要，不是恢复已执行证明

明确禁止：

- 不要在未通过本 runbook 前把 `runtime.active_version` 手动改成 `v2`
- 不要把 `.ai/runs-v2/`、`.ai/archive/`、operator approval JSON 或真实运行态备份提交进 git
- 不要把 repo-side drill ready 说成 `live accepted`
- 不要在有未审查工作树改动时执行 confirmed cutover

## 2. Operator Preconditions

执行 confirmed cutover 前必须同时满足：

- `git status --short --branch` 只显示预期状态，且没有未解释的用户改动
- `.ai/config/orchestrator.yaml` 仍是 `active_version: v1` 且 `experimental_v2_enabled: true`
- `.ai/state/control-plane.db` 存在
- `.ai/runs/` 存在
- `--eval-regression-fixtures-v2` 返回 `ok=true`
- `--cutover-drill-v2` 返回 `ready=true / cutover_performed=false`
- `--cutover-v2` 未带 confirmation 时返回 `manual_approval_required / cutover_performed=false`
- `--cutover-rollback-drill-v2` 返回 `rollback_ready=true / restore_performed=false`，且 `archive_restore_acceptance_path` 指向 `archive-restore-acceptance.json`
- operator approval JSON 已由人工填写 `approved=true / approved_by / approved_at`，其中 `approved_at` 必须是 UTC ISO-8601 且以 `Z` 结尾
- approval JSON 引用的是当前 review summary、当前 rollback drill summary 与当前 archive restore acceptance summary
- full gate 已按项目顺序通过：pytest、planning-status verifier、next-work selector、governance preflight、diff hygiene

## 3. Dry-Run Sequence

在 repo root 执行：

```powershell
uv run --project .\runtime\host-orchestrator python -m pytest
python .\scripts\verify-planning-status.py
python .\scripts\select-next-work.py
pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit
git diff --check
```

然后执行 v2 cutover dry-run 面：

```powershell
uv run --project .\runtime\host-orchestrator python -m host_orchestrator --eval-regression-fixtures-v2
uv run --project .\runtime\host-orchestrator python -m host_orchestrator --cutover-drill-v2
uv run --project .\runtime\host-orchestrator python -m host_orchestrator --cutover-v2
uv run --project .\runtime\host-orchestrator python -m host_orchestrator --cutover-rollback-drill-v2
```

验收要点：

- `--cutover-v2` 未带 confirmation 时必须失败关闭，状态为 `manual_approval_required`
- rollback drill 必须写出 `cutover-rollback-drill-summary.json`
- restore acceptance 必须写出 `archive-restore-acceptance.json`
- 上述命令都不得把默认入口切成 v2

## 4. Approval File

生成默认未批准模板：

```powershell
uv run --project .\runtime\host-orchestrator python -m host_orchestrator --cutover-approval-template-v2
```

人工审批者必须检查模板中的：

- `review_summary_path`
- `rollback_drill_summary_path`
- `archive_restore_acceptance_path`
- `acknowledged_risks`
- `operator_instructions`

只有人工确认接受默认入口切换风险和恢复责任后，才允许把 approval JSON 改为：

```json
{
  "schema_version": "runtime_v2_cutover_operator_approval.v1",
  "approved": true,
  "approved_by": "<operator-id>",
  "approved_at": "<UTC timestamp ending in Z>",
  "review_summary_path": "<current cutover-review-summary.json>",
  "rollback_drill_summary_path": "<current cutover-rollback-drill-summary.json>",
  "archive_restore_acceptance_path": "<current archive-restore-acceptance.json>",
  "acknowledged_risks": [
    "default_entrypoint_switch",
    "rollback_restore_required"
  ]
}
```

approval JSON 是运行态人工证据，不是 repo-level 文档证据；默认不要提交。

## 5. Confirmed Cutover

在重新确认 full gate 仍为 green 后，才允许执行：

```powershell
uv run --project .\runtime\host-orchestrator python -m host_orchestrator --cutover-v2 --confirm-cutover-v2 --cutover-approval-ref <approval.json>
```

成功输出必须包含：

- `active_version = v2`
- `archived_db`
- `archived_runs`
- `cutover_drill_summary_path`
- `cutover_review_summary_path`
- `cutover_rollback_drill_summary_path`
- `cutover_archive_restore_acceptance_path`
- `cutover_operator_approval_summary_path`

执行后立即复核：

```powershell
Get-Content .\.ai\config\orchestrator.yaml
uv run --project .\runtime\host-orchestrator python -m pytest
python .\scripts\verify-planning-status.py
pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit
git diff --check
```

只有 post-cutover gate 也通过，才能把该次切换描述为 repo-side cutover complete。是否 `live accepted` 仍需要按当次人工验收范围单独声明。

## 6. Restore Procedure

当前仓还没有自动 restore 命令。restore 是人工高风险操作，只有在 cutover 后 post-check 失败、且 operator 明确决定回退时才执行。

恢复前先保留失败现场：

- 记录当前 `git status --short --branch`
- 记录 cutover 输出中的 `archived_db` 与 `archived_runs`
- 保留当前失败输出、approval summary、rollback drill summary 和 archive restore acceptance summary

恢复动作必须把默认入口回到 v1：

```powershell
git restore .\.ai\config\orchestrator.yaml
```

如果 `.ai/config/orchestrator.yaml` 的 git 版本不是预期 v1，则人工编辑该文件，使 `runtime.active_version` 回到 `v1`，然后重新验证。

恢复 v1 数据源时，按 cutover 输出中的 archive 路径把：

- archived control-plane DB 恢复到 `.ai/state/control-plane.db`
- archived runs root 恢复到 `.ai/runs`

恢复后必须执行：

```powershell
uv run --project .\runtime\host-orchestrator python -m pytest
python .\scripts\verify-planning-status.py
python .\scripts\select-next-work.py
pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit
git diff --check
```

恢复通过后，只能声明 rollback repo-side verified；不要把它说成 v2 cutover accepted。

## 7. Evidence And Closeout

可提交到 git 的 repo-level evidence：

- docs / specs / plan / backlog / roadmap 的状态更新
- `docs/change-evidence/*.md`
- 代码与测试变更

默认不提交：

- `.ai/runs-v2/`
- `.ai/archive/`
- operator approval JSON
- approval audit JSON
- cutover / rollback summary JSON

最终汇报必须区分：

- `repo-side done`
- `confirmed cutover executed`
- `rollback restored`
- `live accepted`
- `still open`

## 8. Stop Conditions

遇到以下任一情况必须停止 confirmed cutover：

- full gate 失败
- `--cutover-drill-v2` 不是 ready
- `--cutover-v2` 未带 confirmation 时没有返回 `manual_approval_required`
- `--cutover-rollback-drill-v2` 不是 ready
- `archive-restore-acceptance.json` status 不是 `accepted`
- approval JSON 未通过 validation，`approved_at` 不是 UTC `Z` 时间戳，或未引用当前 `archive_restore_acceptance_path`
- worktree 有未解释改动
- operator 无法接受 rollback_restore_required 风险
