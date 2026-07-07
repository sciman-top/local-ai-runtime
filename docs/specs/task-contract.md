# Canonical Task Contract

## 目的

定义当前 repo 内部 normalized task 协议。

当前主协议是 `JSON/YAML`；当前内部归一化主协议仍是 canonical task contract，当前直接 intake 允许 `task.json` / `task.yaml` 与受限 AgentBridge markdown task。

`worker_profile`、policy surface 派生、以及 repo-owned 执行抽象的正式定义，见：

- `docs/specs/config-and-worker-profiles.md`

## 当前事实边界

- 当前 `host_local` 主路径可直接读取 canonical `task.json` / `task.yaml`，也可接收合规 AgentBridge markdown task
- markdown intake 会先归一化为 repo-owned canonical 默认值，并对 execution-critical override / gate command injection fail closed
- `execution_lane` 是 contract 层 topology 字段
- 当前代码层 result surface 仍保留 `lane` 字段名；命名统一不是本轮 truth reset 的目标
- `worktree_path` 当前只定义写入隔离边界，不代表 memory/provider/session 隔离

## 目标态与迁移窗口

目标态：

- Hermes 侧产出的 AgentBridge markdown task 能进入 `runtime/host-orchestrator`
- front matter 被无损映射到 canonical 18 字段
- worker 执行前仍以 canonical payload 为内部真源

迁移窗口：

- 当前已完成 Phase D 的安全 intake 接线；canonical `JSON/YAML` 不再是唯一直接输入形态，但仍是当前内部主协议
- 作者仍不得手写派生字段
- 即使未来引入 markdown-first intake，也不改变 canonical schema 的内部归一化地位

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

## Path Guard

当前 repo-side 已 materialize 的 path guard：

- `worktree_path` 必须保持 repo-relative，并且解析后仍位于 repo root 之下
- `allowed_paths`、`forbidden_paths`、`artifacts_out` 必须保持 repo-relative；不允许绝对路径，也不允许通过 `..` 逃逸
- 当 `worktree_path != "."` 时，`host_local` 在进入 worker 前还会校验：
  - 当前 `workspace_root` 是否等于声明的 worktree 路径
  - 当前 Git root 是否等于该 worktree root
  - 当前 branch 是否等于 `branch_name`
- worker 结束后，runtime 会对新的 Git 变更集做 fail-closed 审计：
  - `write_access = false` 时，不允许出现新的写入
  - 新改动不得落在 `allowed_paths` 之外
  - 新改动不得命中 `forbidden_paths`

当前边界：

- 当前 git-backed 变更审计要求 workspace 具备 `.git` admin path；对非 Git 轻量夹具只保留声明校验，不伪装成已完成的写入审计

## Worktree Manager

当前 repo-side 已 materialize 的 worktree manager：

- 当 `worktree_path != "."` 且 `host_local` 入口仍从 repo root 启动时，runtime 会按 `branch_name` 与 `base_branch` create 或 reuse declared linked worktree
- create/reuse 成功后，worker 与 verification 会改在该 worktree `cwd` 中执行
- 若 declared worktree 已存在但 branch 不符、Git root 不符、或目标路径不是有效 linked worktree，则继续 fail closed

当前边界：

- runtime 当前会把 clean、无 handoff 的 runtime-managed linked worktree 交给 cleanup manager 自动 remove；branch deletion 仍不自动化
- `worktree` 当前只代表写入隔离，不代表 memory/provider/session 隔离

## Cleanup Manager

当前 repo-side 已 materialize 的 cleanup manager：

- 只有 declared isolated worktree 且被 runtime create/reuse 管理的路径才会进入自动 cleanup 尝试
- 当 run `status = succeeded`、`handoff_required = false`、且 linked worktree 保持 clean 时，runtime 会自动 remove 该 worktree，并把 `cleanup_status` 写成 `cleaned`
- 当 review/handoff 仍待处理、run 失败、worktree 仍 dirty、或 isolated worktree 不是由 repo-root runtime 这次 create/reuse 管理时，runtime 会保留 worktree 并写出 `worktree_cleanup` 事件说明原因
- 当 `git worktree remove` 本身失败时，runtime 会把 `cleanup_status` 写成 `cleanup_failed`

当前边界：

- cleanup manager 不会自动删除 branch
- cleanup manager 会让 `result.json`、`dispatch_state.json`、以及 `worktree_cleanup` 事件在 `cleanup_status / cleanup_owner` 上保持一致；branch deletion 仍不自动化

## 派生字段

以下字段由 orchestrator 在 intake 时派生并盖章，任务作者不能手写：

- `planner_required`
- `review_required`
- `touches_policy_surface`

### planner_required

当前 canonical base signal 已 materialize 的触发条件：

- `depends_on` 非空
- `risk_level in {high, critical}`
- `user_forced_planner = true`

当前 `host_local` runtime 还会在以下能力不匹配路径直接 handoff，即使任务作者没有显式写出 planner 相关字段：

- `execution_lane != worker_profile.lane`
- `requires_network = true` 且所选 `worker_profile.network_profile = off`
- `requires_gui = true`
- 所选 `worker_profile` 的 active lease 数超过 `max_active_leases`

保留为 future planner routing 的候选条件，但当前代码尚未 materialize：

- `task_count > 1`
- `target_repo_count > 1`

### review_required

当前 canonical base signal 已 materialize 的触发条件：

- `risk_level in {medium, high, critical}`
- `user_forced_review = true`

当前 `host_local` runtime 还会追加以下 review gate 语义：

- `touches_policy_surface = true` 时，最终运行会停在 `needs_review`
- 当风险或 policy surface 已经要求 review 时，`write_access = true` 会被记入 `status_reason`，但它当前不是单独触发 review 的充分条件

保留为 future review routing 的候选条件，但当前代码尚未 materialize：

- `target_repo_count > 1`

### touches_policy_surface

不是作者输入字段；派生规则为：

- `allowed_paths` 与 `.ai/config/policies.yaml` 中的 `policy_surface_globs` 命中即为 true

## worker_profile 选择

- `worker_profile` 是 repo-owned abstraction，不允许继续作为 ad hoc string 漂浮在 task 外层
- canonical task 当前可以省略 `worker_profile`，由 orchestrator 使用 `.ai/config/orchestrator.yaml` 的默认档补齐
- 若显式指定，必须命中 `.ai/config/workers.yaml`
- 显式/默认 `worker_profile` 的最终选择当前已 materialize 到 `result.json`、`dispatch_state.json`、以及 `route_decisions` 中的 `route_reason`

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
