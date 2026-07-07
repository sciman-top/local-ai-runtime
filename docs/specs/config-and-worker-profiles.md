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
- `run_id_prefix`
- `projection_required`
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
  run_id_prefix: host-local

acceptance:
  projection_required: true
```

语义：

- `default_worker_profile`：当 canonical task 未显式指定具名 profile 时使用
- `run_id_prefix`：默认 `run_id` 前缀
- `projection_required`：是否要求写出 compatibility markdown projection

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
| `wave1_smoke` | Wave 1 deterministic smoke profile | 只允许 repo-side mock，不得宣称 live accepted |
| `remote_non_gui_probe` | repo-side `remote_non_gui` promotion evidence profile | 只证明 lane promotion / fail-closed handoff，不得宣称 remote runner 已执行 |

## policies.yaml

当前最小字段：

- `policy_surface_globs`
- `sensitive_paths`

语义：

- `policy_surface_globs` 用于派生 `touches_policy_surface`
- `sensitive_paths` 用于 compatibility import 与未来 path guard 的最低保护边界
- `workers.yaml` 的 `model` 是 profile 默认值；单次运行仍可在 `dispatch_state.json.model_policy` 中按角色、风险和 lane 上调或下调 reasoning 档

## Selection Rules

`worker_profile` 是 repo-owned abstraction，不再允许继续是 ad hoc string。

当前选择规则：

1. canonical task 若显式指定 `worker_profile`，必须命中 `workers.yaml`
2. 未显式指定时，使用 `orchestrator.yaml:run.default_worker_profile`
3. `requires_gui = true` 时，只能选择 `lane = vm_gui` 的 profile
4. `requires_network = true` 时，只能选择 `network_profile != off` 的 profile
5. `risk_level in {high, critical}` 且 `write_access = true` 时，不允许隐式提升权限；必须通过 repo-owned profile 明确声明
6. selected `worker_profile` 的 active lease 数超过 `max_active_leases` 时，runtime 必须在 worker 前 fail closed 到 handoff，而不是伪装成多 worker 已调度
7. `wave1_smoke` 这类 mock profile 只能证明 `mock green`，不能满足 `live probe ready` 或 `live accepted`
8. 默认模型策略应当是 role-aware / risk-aware / lane-aware，而不是把所有子代理固定为同一模型与同一 reasoning effort
9. 当 `HostLocalRunner` 选中的 profile `lane != host_local` 时，当前必须 fail closed 到 handoff，并把 non-host-local promotion 只写成 repo-side evidence，不得伪装成 remote/vm runner 已执行

## Mapping To Codex Runtime

repo contract 到当前执行实现的映射：

- `sandbox_profile` -> `openai_codex.Sandbox` / `codex exec -s`
- `approval_policy` -> `openai_codex.ApprovalMode` / `approval_policy`
- `model` -> SDK thread/run model 或 `codex exec -m`
- `network_profile` -> 运行时记录与 gate 判断口径；最终宿主是否真正放行网络仍由用户侧环境决定

结论：

- `approval` / `sandbox` / `network` 必须先经过 repo-owned abstraction
- host runtime 只消费 abstraction，不直接在代码里散落硬编码默认值

## impl_pack Absorption

`ai_dev_orchestrator_impl_pack/07_AGENT_ROLE_MATRIX.md` 的角色分层现在只保留为历史说明。

当前 authoritative truth 已迁到本文件；`07` 应标记为 `role-superseded`。
