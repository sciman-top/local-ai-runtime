# Config And Worker Profiles Contract

## 目的

定义 repo-owned 的运行时配置真源，以及 `worker_profile` 如何映射到实际执行配置。

当前 authoritative config 面固定为：

- `.ai/config/orchestrator.yaml`
- `.ai/config/workers.yaml`
- `.ai/config/policies.yaml`

这三份文件缺失、语法错误、字段类型错误、或 profile 引用不存在时，host runtime 必须返回 deterministic contract error；不允许静默回退到代码硬编码默认值。

## Ownership Boundary

### Repo-owned contract

以下值属于当前仓的正式契约：

- `default_worker_profile`
- `review_worker_profile`
- `run_id_prefix`
- `projection_required`
- `runtime.active_version`
- `runtime.experimental_v2_enabled`
- `runtime.control_plane_db_v2`
- `runtime.artifact_root_v2`
- `worker_profile` 名称
- `worker_kind`
- `lane`
- `model`
- `provider`
- `sandbox_profile`
- `approval_policy`
- `network_profile`
- `projection_mode`
- `max_active_leases`
- `policy_surface_globs`
- `sensitive_paths`

### User-side Codex config

以下值仍属于用户侧环境与执行器配置，不由仓库直接写死：

- 实际登录态
- 用户侧 provider credential
- 本机 permission profile / sandbox 实际允许边界
- CLI/App 的默认 model availability
- 是否允许联网的最终宿主策略

仓库只能声明抽象层，不能假定用户侧 Codex config 一定与 repo contract 完全一致。

## orchestrator.yaml

当前最小字段：

```yaml
run:
  default_worker_profile: local_maint
  review_worker_profile: claude_glm_review
  run_id_prefix: host-local

runtime:
  active_version: v1
  experimental_v2_enabled: true
  control_plane_db_v2: .ai/state/control-plane-v2.db
  artifact_root_v2: .ai/runs-v2

acceptance:
  projection_required: true
```

语义：

- `default_worker_profile`：当 canonical task 未显式指定具名 profile 时使用
- `review_worker_profile`：当 review-gated host_local 路径需要 live heterogeneous receipt 时使用；当前只消费 bounded runtime summary，不代表 primary task execution
- `run_id_prefix`：默认 `run_id` 前缀
- `projection_required`：是否要求写出 compatibility markdown projection
- `runtime.active_version`：`--run-task` 当前应绑定的默认运行时版本；cutover 前保持 `v1`
- `runtime.experimental_v2_enabled`：是否允许使用 `--run-task-v2` 等实验入口
- `runtime.control_plane_db_v2` / `runtime.artifact_root_v2`：v2 双轨期独立状态与工件根路径

## workers.yaml

每个 `worker_profile` 必须至少定义：

| 字段 | 说明 |
| --- | --- |
| `worker_kind` | adapter 路径，如 `codex_sdk`、`codex_exec`、`scripted` |
| `lane` | `host_local / remote_non_gui / vm_gui` |
| `model` | repo 期望的模型标识 |
| `provider` | repo 观察到的 provider 名称 |
| `sandbox_profile` | `workspace_write / read_only / danger_full_access` |
| `approval_policy` | `never / on_request` |
| `network_profile` | `off / restricted / on` |
| `projection_mode` | `compatibility_dual_write / canonical_only` |
| `max_active_leases` | 该 profile 允许同时持有的 active lease 上限；超额时在 worker 前 handoff |

### 当前已定义 profile

| profile | 用途 | 边界 |
| --- | --- | --- |
| `local_maint` | 当前 Phase 1 host-local 默认 profile | repo-side 与 live SDK 共用入口 |
| `claude_glm_review` | 当前 bounded live heterogeneous review receipt profile | 只 materialize host_local review receipt，不得伪装成 live task execution 或 non-host_local runner |
| `wave1_smoke` | Wave 1 deterministic smoke profile | 只允许 repo-side mock，不得宣称 live accepted |
| `remote_non_gui_probe` | repo-side `remote_non_gui` promotion evidence profile | 只证明 lane promotion / fail-closed handoff，不得宣称 remote runner 已执行 |
| `vm_gui_probe` | repo-side `vm_gui` conditional promotion evidence profile | 只证明 GUI-only 条件晋升 / fail-closed handoff，不得宣称 vm runner 已执行 |

## policies.yaml

当前最小字段：

- `policy_surface_globs`
- `sensitive_paths`
- `verification_profiles`
- `continuation_policies`
- `retry_policies`

语义：

- `policy_surface_globs` 用于派生 `touches_policy_surface`
- `sensitive_paths` 用于 compatibility import 与未来 path guard 的最低保护边界
- `verification_profiles` 固定承接 `build -> lint -> typecheck -> test -> contract -> hotspot` 的 v2 gate 配置
- `continuation_policies` 固定承接 `auto / guarded` 这类自动继续与 review/pause 语义
- `retry_policies` 固定承接 gate failure / worker failure 的 recoverable 语义
- `workers.yaml` 的 `model` 是 profile 默认值；单次运行仍可在 `dispatch_state.json.model_policy` 中按角色、风险和 lane 上调或下调 reasoning 档

## Selection Rules

`worker_profile` 是 repo-owned abstraction，不再允许继续是 ad hoc string。

当前选择规则：

1. canonical task 若显式指定 `worker_profile`，必须命中 `workers.yaml`
2. 未显式指定时，使用 `orchestrator.yaml:run.default_worker_profile`
3. `orchestrator.yaml:run.review_worker_profile` 若存在，必须命中 `workers.yaml`，且当前只在 review-gated `host_local` 路径上消费
4. `requires_gui = true` 时，只能选择 `lane = vm_gui` 的 profile
5. `requires_network = true` 时，只能选择 `network_profile != off` 的 profile
6. `risk_level in {high, critical}` 且 `write_access = true` 时，不允许隐式提升权限；必须通过 repo-owned profile 明确声明
7. selected `worker_profile` 的 active lease 数超过 `max_active_leases` 时，runtime 必须在 worker 前 fail closed 到 handoff，而不是伪装成多 worker 已调度
8. `wave1_smoke` 这类 mock profile 只能证明 `mock green`，不能满足 `live probe ready` 或 `live accepted`
9. 默认模型策略应当是 role-aware / risk-aware / lane-aware，而不是把所有子代理固定为同一模型与同一 reasoning effort
10. 当 `HostLocalRunner` 选中的 profile `lane != host_local` 时，当前必须 fail closed 到 handoff，并把 non-host-local promotion 只写成 repo-side evidence，不得伪装成 remote/vm runner 已执行

## Mapping To Codex Runtime

repo contract 到当前执行实现的映射：

- `sandbox_profile` -> `openai_codex.Sandbox` / `codex exec -s`
- `approval_policy` -> `openai_codex.ApprovalMode` / `approval_policy`
- `model` -> SDK thread/run model 或 `codex exec -m`
- `network_profile` -> 运行时记录与 gate 判断口径；最终宿主是否真正放行网络仍由用户侧环境决定

结论：

- `approval` / `sandbox` / `network` 必须先经过 repo-owned abstraction
- host runtime 只消费 abstraction，不直接在代码里散落硬编码默认值
- 当前 repo-owned live task entrypoint 会通过 worker factory 物化 `worker_kind`：
  - `codex_sdk` -> `CodexSdkWorker`
  - `codex_exec` -> `CodexExecFallbackWorker`
  - `claude_glm` -> `ClaudeCodeStructuredWorker`（当前只用于 bounded live heterogeneous review receipt）
  - `scripted / gpt54_direct` 当前仍对 live task execution fail closed，不得伪装成已接线
  - `claude_glm` 当前仍对 primary live task execution fail closed，不得把 review receipt path 写成 worker execution 已接线

## impl_pack Absorption

`ai_dev_orchestrator_impl_pack/07_AGENT_ROLE_MATRIX.md` 的角色分层现在只保留为历史说明。

当前 authoritative truth 已迁到本文件；`07` 应标记为 `role-superseded`。
