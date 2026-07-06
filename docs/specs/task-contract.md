# Canonical Task Contract

## 目的

定义通用本地 AI Dev Orchestrator 的正式任务协议。

当前主协议是 `JSON/YAML`，不是 `AgentBridge markdown`。

`worker_profile`、policy surface 派生、以及 repo-owned 执行抽象的正式定义，见：

- `docs/specs/config-and-worker-profiles.md`

## 必填字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `task_id` | string | 全局唯一任务 ID |
| `title` | string | 任务标题 |
| `target_repo` | string | 目标仓 ID 或路径别名 |
| `base_branch` | string | 基线分支 |
| `branch_name` | string | 任务分支名 |
| `worktree_path` | string | 本任务 worktree 路径 |
| `allowed_paths` | string[] | 允许写入路径 |
| `forbidden_paths` | string[] | 禁止访问路径 |
| `write_access` | boolean | 本任务是否允许写 |
| `risk_level` | enum | `low / medium / high / critical` |
| `merge_policy` | enum | `draft_pr_only / manual_merge_only / never_merge` |
| `execution_lane` | enum | `host_local / remote_non_gui / vm_gui` |
| `requires_network` | boolean | 是否需联网 |
| `requires_gui` | boolean | 是否需 GUI |
| `depends_on` | string[] | 依赖的前置任务 |
| `artifacts_out` | string[] | 预期输出工件 |
| `handoff_policy` | enum | `none / handoff_on_risk / handoff_before_merge / handoff_always` |
| `verification_commands` | object | 结构化 gate 命令 |

## verification_commands

固定 6 键：

- `build`
- `test`
- `lint`
- `typecheck`
- `contract`
- `hotspot`

每项允许为 `null`；执行顺序固定为：

`build -> [lint -> typecheck] -> test -> contract -> hotspot`

固定 gate 口径与 acceptance tier 映射，见：

- `docs/specs/acceptance-and-gates.md`

## 派生字段

以下字段由 orchestrator 在 intake 时派生并盖章，任务作者不能手写：

- `planner_required`
- `review_required`
- `touches_policy_surface`

### planner_required

满足任一条件即为 true：

- `task_count > 1`
- `target_repo_count > 1`
- `depends_on` 非空
- `risk_level in {high, critical}`
- `user_forced_planner = true`

### review_required

满足任一条件即为 true：

- `risk_level in {medium, high, critical}`
- `write_access = true`
- `target_repo_count > 1`
- `touches_policy_surface = true`
- `user_forced_review = true`

### touches_policy_surface

不是作者输入字段；派生规则为：

- `allowed_paths` 与 `.ai/config/policies.yaml` 中的 `policy_surface_globs` 命中即为 true

## worker_profile 选择

- `worker_profile` 是 repo-owned abstraction，不允许继续作为 ad hoc string 漂浮在 task 外层
- canonical task 当前可以省略 `worker_profile`，由 orchestrator 使用 `.ai/config/orchestrator.yaml` 的默认档补齐
- 若显式指定，必须命中 `.ai/config/workers.yaml`

## Override 规则

- 只允许 `user_forced_planner = true`
- 只允许 `user_forced_review = true`
- 不允许 force off
- 任务输入中如果直接出现 `planner_required` 或 `review_required`，应视为 contract error

## 示例

```yaml
task_id: TASK-20260706-vertical-slice
title: Real SDK vertical slice on canonical task input
target_repo: hermes-agent
base_branch: main
branch_name: codex/phase1-vertical-slice
worktree_path: .worktrees/phase1-vertical-slice
allowed_paths:
  - runtime/host-orchestrator/**
  - docs/**
forbidden_paths:
  - .env
  - .env.*
  - .git/config
write_access: true
risk_level: medium
merge_policy: draft_pr_only
execution_lane: host_local
requires_network: false
requires_gui: false
depends_on: []
artifacts_out:
  - .ai/runs/<run_id>/<task_id>/result.json
handoff_policy: handoff_on_risk
verification_commands:
  build: null
  lint: null
  typecheck: null
  test: uv run pytest
  contract: pwsh -NoProfile -ExecutionPolicy Bypass -File snapshots/agentbridge-20260628/scripts/test-agentbridge-contract.ps1
  hotspot: null
```
