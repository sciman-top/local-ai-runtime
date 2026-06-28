# Hermes v2 接口规格

## 1. AgentBridge task metadata

| 字段 | 类型 | 必填 | 默认值 | 写入者 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `task_class` | string | 是 | `B` | orchestrator / human | `A/B/C` 风险类别 |
| `execution_lane` | string | 是 | `host_local` | orchestrator | `host_local/remote_non_gui/vm_gui` |
| `worker_profile` | string | 是 | `local_maint` | orchestrator | worker profile |
| `network_profile` | string | 是 | `off` | orchestrator | `off/allowlist` |
| `approval_boundary` | string | 是 | `handoff_on_risk` | orchestrator | 风险触发边界 |
| `requires_gui` | bool | 是 | `false` | orchestrator / human | 是否需要 GUI |
| `requires_network` | bool | 是 | `false` | orchestrator / human | 是否需要联网 |
| `chain_id` | string | 否 |  | orchestrator | 同链任务标识 |
| `parent_task_id` | string | 否 |  | orchestrator | 父任务 |

## 2. AgentBridge result metadata

| 字段 | 类型 | 必填 | 默认值 | 写入者 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `worker_id` | string | 是 |  | runner | 执行 worker |
| `session_id` | string | 否 |  | runner | Codex session |
| `lane` | string | 是 |  | runner | 实际执行 lane |
| `sandbox_mode` | string | 是 |  | runner | read-only/workspace-write/... |
| `network_mode` | string | 是 |  | runner | off/allowlist |
| `quality_stop` | string | 否 |  | runner | 质量停点原因 |
| `handoff_required` | bool | 是 | `false` | runner | 是否需接管 |
| `evidence_paths` | string[] | 否 | `[]` | runner | 相关证据路径 |

## 3. SQLite 表

### runtime_tasks

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `task_id` | text | 是 | 主键 |
| `state` | text | 是 | 当前状态 |
| `execution_lane` | text | 是 | 当前 lane |
| `worker_profile` | text | 是 | 当前 profile |
| `created_at` | text | 是 | ISO8601 |
| `updated_at` | text | 是 | ISO8601 |
| `result_path` | text | 否 | 最终 result 路径 |

### leases

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `task_id` | text | 是 | 关联任务 |
| `worker_id` | text | 是 | 持有者 |
| `lease_token` | text | 是 | 唯一租约 |
| `acquired_at` | text | 是 | ISO8601 |
| `expires_at` | text | 是 | ISO8601 |

### workers

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `worker_id` | text | 是 | 主键 |
| `lane` | text | 是 | host_local/remote_non_gui/vm_gui |
| `status` | text | 是 | idle/busy/offline |
| `heartbeat_at` | text | 否 | ISO8601 |

### route_decisions

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `task_id` | text | 是 | 任务 |
| `selected_lane` | text | 是 | 选中的 lane |
| `reason` | text | 是 | 路由原因 |
| `created_at` | text | 是 | ISO8601 |

### events

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `event_id` | text | 是 | 主键 |
| `task_id` | text | 否 | 任务 |
| `event_type` | text | 是 | 事件类型 |
| `payload_json` | text | 是 | JSON |
| `created_at` | text | 是 | ISO8601 |

## 4. 状态机

- `queued -> claimed`
  - 条件：原子认领成功
- `claimed -> running`
  - 条件：worker 启动成功
- `running -> completed`
  - 条件：result 成功写回
- `running -> waiting_handoff`
  - 条件：命中中风险接管点
- `running -> needs_review`
  - 条件：结果存在但不能自动流入下游
- `running -> blocked`
  - 条件：缺前提 / 缺权限 / 缺资源
- `running -> failed`
  - 条件：执行失败

## 5. 硬规则

- 运行态只进 SQLite，不进 `AgentBridge`
- 一个 task 只有一个正式 result
- 失败重跑必须新建 task
