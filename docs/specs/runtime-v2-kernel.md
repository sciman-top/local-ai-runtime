# Runtime V2 Kernel Spec

## Status

- 当前状态：`absorbed / experimental / dual-track`
- 默认入口：`未切换`
- 仓库与目录命名：`不修改`

当前终态重构方式固定为：保留本项目作为唯一主仓，在 `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/` 内落新内核；旧 `host_local`、`db.py`、`verification.py` 继续承担 `legacy_v1` 主路径，直到 cutover 条件满足。

## 代码落点

- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/contracts.py`
- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/scheduler.py`
- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/admission.py`
- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/storage.py`
- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/executor.py`
- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/artifacts.py`
- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/tracing.py`
- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/migration.py`
- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/runner.py`

## Config Surface

`runtime_v2` 当前 authoritative config 继续只使用三份 repo-owned config：

- `.ai/config/orchestrator.yaml`
- `.ai/config/workers.yaml`
- `.ai/config/policies.yaml`

新增字段：

- `runtime.active_version`
- `runtime.experimental_v2_enabled`
- `runtime.control_plane_db_v2`
- `runtime.artifact_root_v2`
- `verification_profiles`
- `continuation_policies`
- `retry_policies`

## Canonical Task V2

当前 v2 canonical task 保留以下核心字段：

- `task_id`
- `title`
- `description`
- `target_repo`
- `base_branch`
- `branch_name`
- `worktree_path`
- `allowed_paths`
- `forbidden_paths`
- `write_access`
- `risk_level`
- `merge_policy`
- `requires_network`
- `requires_gui`
- `artifacts_out`
- `worker_profile`

当前 v2 canonical task 新语义固定为：

- `dependency_refs`
- `verification_profile`
- `continuation_policy`

当前 v2 明确拒绝 authored legacy fields：

- `depends_on`
- `verification_commands`
- `handoff_policy`
- `planner_required`
- `review_required`
- `touches_policy_surface`

## State Machine

当前 v2 固定状态集为：

- `queued`
- `blocked`
- `ready`
- `admitted`
- `running`
- `gating`
- `reviewing`
- `paused`
- `retryable`
- `completed`
- `failed`
- `cancelled`

当前已落第一批实现的关键路径：

- `dependency_refs` 未满足 -> `blocked`
- `dependency_refs` 后续满足 -> `--run-ready-blocked-v2` 可批量续跑 dependency-blocked task
- pre-worker policy guard 命中 -> `blocked`
- admission slot 冲突 -> `paused`
- low-risk + `continuation_policy=auto` + gate 通过 -> `completed`
- medium/high risk 或 policy surface 命中 -> `reviewing` / `paused`
- gate failure / worker failure -> `retryable`（按 retry policy）

当前 ready-blocked 自动续跑边界：

- 只扫描 `status = blocked` 且 `status_reason = dependency_refs are not satisfied` 的任务
- 只续跑已持久化 repo-relative `tasks.task_path` 的任务
- 非依赖原因的 `blocked` 不会被批量入口自动运行

当前 pre-worker policy guard 边界：

- `requires_network = true` 但 selected worker profile 的 `network_profile = off` -> `blocked`
- selected worker profile 的 `lane != host_local` -> `blocked`，因为 `runtime_v2` 当前仍未接线 non-host-local primary runner
- `requires_gui = true` -> `blocked`，因为 `runtime_v2` 当前仍未接线 `vm_gui` primary runner
- `write_access = true` 且 `allowed_paths` 与 repo-owned `sensitive_paths` 重叠 -> `blocked`
- guard 命中时不会执行 worker，不会占用 admission slot，`gate_report.json` 会写入 `policy_guard.blocking_reasons`

## Storage

当前双轨期物理落点固定为：

- `.ai/state/control-plane-v2.db`
- `.ai/runs-v2/<run_id>/<task_id>/<attempt_id>/`

当前 v2 存储固定为 6 表：

- `tasks`
- `task_dependencies`
- `task_attempts`
- `leases`
- `artifacts`
- `events`

`tasks` 当前已把以下字段提升为一等字段：

- `task_path`

其中 `task_path` 存 repo-relative task path，用于 `--run-ready-blocked-v2` 在依赖满足后重新加载 canonical task；既有 DB 通过初始化时的向后兼容迁移补列。

`task_attempts` 当前已把以下字段提升为一等字段：

- `attempt_id`
- `resume_point`
- `retry_rewind`

## Artifact Contract

当前 v2 每次尝试固定工件集合：

- `attempt.json`
- `result.json`
- `gate_report.json`
- `trace_manifest.json`
- `closeout_bundle.json`
- `regression_fixture.json`
- `sidecars/planner_result.json`
- `sidecars/review_result.json`

当前 `regression_fixture.json` 的覆盖边界：

- completed / reviewing / gate-retryable final-result attempt
- dependency-blocked attempt
- admission-paused attempt
- pre-worker policy-guard blocked attempt
- worker-failure retryable / failed attempt
- retry queued attempt；该路径不伪造 `result.json`，fixture 的 `artifact_refs.result = null`
- fixture 会复制 attempt 的关键判定面：status、next_action、worker/verification/continuation profile、gate status、gate names、changed_paths、review flag、policy guard reasons、以及核心 artifact refs
- `--eval-regression-fixtures-v2` 会从 v2 `artifacts.kind = regression_fixture` 读取 fixture，写出 `.ai/runs-v2/_eval/regression-fixture-summary.json`
- 当前 eval summary 只校验 repo-side fixture schema / required fields / missing files / status counts，不等于 live cutover 验收

当前 pre-worker policy guard 路径会在 `result.json` 与 `gate_report.json` 中写入：

- `policy_guard_reasons[]`，每项包含 `category` 与 `detail`
- `gate_report.policy_guard.status = blocked`
- `gate_report.policy_guard.blocking_reasons[]`

当前 `sidecars/review_result.json` 在 review-gated 路径上至少包含：

- `reviewer_kind`
- `review_mode`
- `model`
- `state`
- `blocking_reasons[]`，每项包含 `category` 与 `detail`
- `changed_paths`
- `gate_failed`
- `policy_surface_touched`
- `recommended_action`
- `sidecar_status`
- `findings`
- `sidecar_blocking_reasons`
- `missing_tests`

当前已 materialize 的 `blocking_reasons[].category`：

- `risk_level`
- `policy_surface`
- `verification`

当前 v2 bounded review sidecar 边界：

- 显式传入 `review_worker`、显式传入 `worker_factory`、或 runner 使用 live factory 时，review-gated 路径可尝试 materialize sidecar receipt
- sidecar 成功时，`sidecar_status = materialized`，并把由 review worker profile 派生的 reviewer/model、findings、sidecar blocking reasons 写入同一个 `review_result.json`
- sidecar 缺失、无 primary worker summary、或 sidecar 失败时，`sidecar_status` 保持 `not_configured` 或 `fallback`，repo-side blocking receipt 仍 fail-closed 保留
- 这不等于 `runtime_v2` 默认入口切换，也不等于 live accepted

## CLI Surface

当前实验入口固定为：

- `--run-task-v2`
- `--run-ready-blocked-v2`
- `--resume-task-v2`
- `--retry-task-v2`
- `--migrate-control-plane-v2`
- `--eval-regression-fixtures-v2`
- `--cutover-drill-v2`
- `--cutover-rollback-drill-v2`
- `--cutover-v2`
- `--confirm-cutover-v2`
- `--cutover-approval-ref`
- `--cutover-approval-template-v2`
- `--cutover-approval-template-output`

当前默认入口规则：

- `--run-task` 在 `runtime.active_version = v1` 时仍走旧 `host_local`
- `runtime.active_version = v2` 后，`--run-task` 才切到 v2

## Cutover Boundary

cutover 之前必须同时满足：

- v2 unit / integration / e2e 为绿
- verification profiles 可重跑
- 至少一条真实本地编码任务在无人工 relay 下闭环到 `completed`
- selector / preflight / verifier / docs truth 已承认 v2 状态与工件

当前 truth boundary 固定为：

- `runtime_v2` 已吸收进 authoritative docs 与代码
- `--cutover-drill-v2` 会写出 `.ai/runs-v2/_cutover/cutover-drill-summary.json`，只做前置条件检查，不切换默认入口
- `--cutover-v2` 会先跑 cutover drill；drill 未 ready 时 fail-closed，返回 blocked summary 且不修改 `runtime.active_version`
- drill ready 后，`--cutover-v2` 仍会先写出 `.ai/runs-v2/_cutover/cutover-review-summary.json`，返回 `manual_approval_required` 且不修改 `runtime.active_version`
- `--cutover-rollback-drill-v2` 会写出 `.ai/runs-v2/_cutover/cutover-rollback-drill-summary.json`，验证 review summary、恢复目标、archive root 与当前默认入口仍为 v1；它不执行 restore，也不切换默认入口
- `--cutover-approval-template-v2` 会写出 `.ai/runs-v2/_cutover/operator-approval.template.json` 或 `--cutover-approval-template-output` 指定路径；模板默认 `approved=false`，只生成可人工编辑的 approval JSON，不切换默认入口
- 只有同时传入 `--cutover-v2 --confirm-cutover-v2 --cutover-approval-ref <approval.json>`，且 approval JSON 校验通过，才允许执行默认入口切换；该路径必须保留 review summary、rollback drill summary、operator approval summary 与 rollback plan 引用
- approval JSON 必须使用 `runtime_v2_cutover_operator_approval.v1`，包含 `approved=true`、`approved_by`、`approved_at`、当前 review summary path、当前 rollback drill summary path，并确认 `default_entrypoint_switch / rollback_restore_required`
- approval validation 会写出 `approval_sha256`、`approval_byte_count`、`approved_by`、`approved_at` 与 sanitized `operator-approval-audit.json`，用于确认审批文件留痕；该审计摘要不等于执行 cutover
- 当前已有一条真实 `local_maint` v2 live coding probe completed，`--eval-regression-fixtures-v2` 为 `ok=true`，`--cutover-drill-v2` 为 `ready=true / cutover_performed=false`，`--cutover-v2` 默认返回 `manual_approval_required / cutover_performed=false`，`--cutover-rollback-drill-v2` 为 `ready=true / restore_performed=false`，`--cutover-approval-template-v2` 能生成默认未批准模板，`--cutover-v2 --confirm-cutover-v2` 在缺少或未批准 `--cutover-approval-ref` 时返回 `approval_required / cutover_performed=false`
- 默认入口未切换
- active queue 未改写
- Hermes / AgentBridge 仍保留 compatibility / baseline / adapter 边界
