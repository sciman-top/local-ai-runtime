# Adaptive Orchestration Overlay Spec

## Status And Boundary

`Adaptive Orchestration Overlay` 是 `Local AI Runtime` 的 cross-cutting 产品能力，不替代 `Phase 1 -> Phase 6` 路线图，也不改变 `Hermes -> AgentBridge -> Codex` 主线。

当前状态：

- `observe` 已作为 repo-side 正式能力落地
- `guarded` 已作为显式 `runtime_v2` 实验入口落地
- `.ai/config/policies.yaml` 的 active profile 仍是 `observe_default`
- `runtime.active_version` 仍是 `v1`
- `current_active_queue` 仍是 `PHASE-1-VERTICAL-SLICE`
- 当前不声明 `live accepted`

本能力不依赖 Trellis、Grill 或 Superpowers。外部 skill 只能作为可替换 adapter；核心控制流、预算、冲突、证据和晋升判断由本仓拥有。

## Truth Model

- canonical v1/v2 task 继续是执行真源
- `agent-work-manifest` 是 versioned batch dispatch envelope，不是平行 task truth
- 缺少 `schema_version / orchestration_constraints` 的旧 v1 manifest 会归一化为 `agent_work_manifest.v1 + observe_default + single_agent + zero delegation budget`，不会被静默升级为 guarded execution
- manifest 在 guarded 路径进入 worker 前必须归一化为 canonical runtime_v2 tasks
- `orchestration-decision.json` 是 run-level 决策证据，不替代 task/attempt evidence
- `orchestration-execution.json` 是 guarded batch execution summary，不替代各 task 的 `result.json`

## Input Contract

manifest schema version 固定为 `agent_work_manifest.v1`。

作者可输入 `orchestration_constraints`：

| 字段 | 语义 |
| --- | --- |
| `profile` | 引用 `.ai/config/policies.yaml` 中的版本化 profile |
| `mode_preference` | `auto / single_agent / multi_agent`；multi 只是偏好 |
| `max_concurrent_subagents` | manifest 向下收紧的并发上限，最大 3 |
| `max_total_subagents` | manifest 向下收紧的总预算，最大 6 |
| `max_tree_depth` | 只能是 0 或 1 |
| `write_conflict_policy` | `serialize / reject` |
| `stop_policy` | 冲突后停止全部或完成独立工作流 |

作者不得输入：

- `selected_mode`
- `decision_reason`
- 执行波次
- 最终角色、模型或能力分配

这些字段只能由 decision engine 派生。

派生输出 schema 固定为 `orchestration_decision.v1`。

task 可选 `intent`：

`general / bugfix / feature / refactor / research / docs / review / migration / operations`

缺省值为 `general`，因此旧任务可以兼容归一化。

可选 `evaluation_context` 用于受控 A/B：

- `experiment_id`
- `variant = baseline / candidate`
- `repeat_index >= 1`
- candidate 必须提供 `baseline_run_id`

## Deterministic Decision

decision engine 固定执行：

1. 校验 manifest 与 repo-owned config。
2. 构建 dependency DAG；unknown dependency 或 cycle fail closed。
3. 构建读写冲突图。
4. 校验 worker profile、lane、network、GUI、runner wiring 与 lease capacity。
5. writer 校验 worktree root、branch、cwd 与隔离状态。
6. 根据 intent、role、risk 和 policy surface 派生能力与模型路由。
7. 在 profile 与 manifest 双重上限内形成执行波次。

guarded 入口把每个 canonical task 视为一次 planned worker launch；`planned_worker_count` 超过 `max_total_subagents` 时整批在 worker 前阻断，不允许把超额任务改成无界串行 worker 来绕过总预算。lease 数据库存在但不可读时返回 `lease_state_unavailable`，不得按零占用继续决策。

以下情况不得并行：

- write/write 重叠
- write/read 重叠
- unbounded write set
- 共享 worktree
- policy surface competition
- authoritative truth competition
- writer isolation 未验证
- worker/profile/lease 能力不足
- 小于两个独立 ready workstreams

`mode_preference=multi_agent` 不得绕过上述条件；不满足时必须降级为 `single_agent` 并记录稳定 reason code。

## Profiles

当前 repo-owned profiles：

- `observe_default`：只计算和记录，不运行 worker
- `guarded_read_only`：显式 v2 入口可并行只读任务；writer 仍须是真实 linked worktree，并保持串行
- `guarded_isolated_writers`：只有 disjoint write set、真实隔离 worktree 和可用 lease 同时成立时才允许 writer 并行

active profile 保持 `observe_default`。选择 guarded profile 本身不会改变默认入口；只有显式调用 guarded CLI 才会执行。

## Capability And Model Routing

通用能力 ID 固定为：

- `clarification`
- `systematic_debugging`
- `test_first`
- `exploration`
- `spec_review`
- `quality_review`
- `worktree_isolation`

能力不可用时记录 `capability_unavailable` 并按 stop policy fail closed；runtime 不自动安装外部 skill。

模型路由按 role、intent、risk 匹配 `.ai/config/policies.yaml`，实际 model 与 reasoning effort 同时传入 worker request，并写入 decision 和 attempt evidence。只读 explorer 使用 `adaptive_read`；只读 reviewer 使用 `adaptive_review`；writer 使用 `adaptive_write` 或满足写权限边界的显式 worker profile。只读 task 不得绑定 write sandbox，writer 不得绑定 read-only sandbox。默认 `local_maint` 不因本功能被改成多并发。

## Evidence Contracts

决策工件：

`.ai/runs-v2/<run_id>/_orchestration/<decision_id>/orchestration-decision.json`

guarded summary：

`.ai/runs-v2/<run_id>/_orchestration/<decision_id>/orchestration-execution.json`

归一化任务副本：

`.ai/runs-v2/<run_id>/_orchestration/<decision_id>/tasks/<task_id>.yaml`

guarded attempt 的 `attempt.json / result.json / trace_manifest.json / closeout_bundle.json / regression_fixture.json` 必须携带：

- `orchestration_decision_ref`
- `decision_id`
- `policy_version`

每个 guarded attempt 还写 `evidence_index.json`，以 sha256 与 byte count 枚举 decision 和现有 attempt artifacts。`regression_fixture.json` 记录 model policy、evaluation context 与 orchestration metrics。v2 artifacts 表以 `kind=orchestration_decision / evidence_index` 建立 task attempt 到 run-level decision 和 task evidence index 的引用。

## CLI

只读决策入口：

```powershell
host-orchestrator --evaluate-orchestration-manifest <manifest.yaml>
```

固定输出 `worker_execution_attempted=false`；允许写 decision evidence，但不得创建或改变 control-plane task state。

显式 guarded 入口：

```powershell
host-orchestrator --run-orchestration-manifest-v2 <manifest.yaml>
```

仅接受 `effect=guarded` 且 `decision_status=guarded_ready` 的决策。observe profile、依赖/契约错误、能力缺失或 stop-policy blocker 必须在 worker 前返回 blocked。

## Evaluation And Promotion

`--eval-regression-fixtures-v2` 继续是统一 eval 入口，并额外汇总：

- task success
- gate pass
- evidence completeness
- total tokens
- task 与 batch wall time
- human handoff
- subagent count
- conflict、retry、rework

baseline/candidate 比较必须满足：

- task IDs、verification profiles、model 与 reasoning effort 一致
- baseline 和 candidate 各至少 3 个 repeat indexes
- success、gate、evidence 三项无回归
- token、batch latency、handoff、retry、rework 中至少一项严格改善，且其他可比较项不变差

满足后只返回 `eligible_for_manual_review`；`automatic_promotion_performed` 永远为 false。证据不足返回 `insufficient_evidence`。

## Rollback

- 默认回退：保持或恢复 `active_profile=observe_default`
- 停止 guarded：不再调用显式 guarded CLI
- runtime 回退：继续使用现有 v1 或独立 `--run-task-v2`
- 新增 decision/execution 工件与引用字段均为 additive；旧 consumer 可忽略
- 不自动删除 branch，不自动执行 v2 cutover，不改 `current_active_queue`
