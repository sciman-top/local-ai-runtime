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
- admission slot 冲突 -> `paused`
- low-risk + `continuation_policy=auto` + gate 通过 -> `completed`
- medium/high risk 或 policy surface 命中 -> `reviewing` / `paused`
- gate failure / worker failure -> `retryable`（按 retry policy）

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
- `sidecars/planner_result.json`
- `sidecars/review_result.json`

## CLI Surface

当前实验入口固定为：

- `--run-task-v2`
- `--resume-task-v2`
- `--retry-task-v2`
- `--migrate-control-plane-v2`
- `--cutover-v2`

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
- 默认入口未切换
- active queue 未改写
- Hermes / AgentBridge 仍保留 compatibility / baseline / adapter 边界
