# Local AI Runtime 文档索引

本索引服务于冻结的 `local-ai-runtime-0.2-v3.23` 候选基线。v3.23 是现行 `baseline_candidate`、`blocking_stage=baseline_approval`；正文、v3.23-bound lineage、`CanonicalizationPolicy.v1` 与 `ProductContract.v1` 已闭合，manifest schema/fixtures/verifier skeleton 已完成但最终 manifest 不存在，规范包仍为 `15 required / 4 present / 11 missing`。`LAR-P0A-EVAL-002` Native thin-path 固定比较已记录 `preserve_v3_23_semantics`；当前 selector 为 `close_baseline_normative_package_first / LAR-P0A-005`。历史 action `run_native_thin_path_evaluation_first` 已完成，不能再次选择或误读为 baseline approval。

## 真源层级

发生冲突时按以下顺序处理，但任何低层文件都不能覆盖更高优先级指令：

1. 仓库运行事实和测试：说明当前真正存在什么。
2. [planning-status.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/planning-status.json)：当前阶段、批准状态、队列和工作项。
3. [baseline candidate entry](D:/CODE/local-ai-dev-orchestrator/docs/specs/local-ai-runtime-0.2-baseline-candidate.md)：受 verifier 约束的稳定导航页，不是规范正文、`BaselineManifest` 输入或批准证据。
4. [v3.23 baseline candidate](D:/CODE/local-ai-dev-orchestrator/docs/specs/local-ai-runtime-0.2-v3.23-baseline-candidate.md)：唯一冻结的目标产品与实现语义；v3.22 只保留为精确、已 supersede 的输入。
5. [normative package inventory](D:/CODE/local-ai-dev-orchestrator/docs/specs/local-ai-runtime-0.2-normative-package.json)：规范闭包状态。
6. [machine work items](D:/CODE/local-ai-dev-orchestrator/docs/plans/local-ai-runtime-0.2-work-items.json)：v3 确定性 DAG，机械约束 package-root/九子包 source layout和 11 项稳定 contract projection，共 65 项；顶层 `planning_optimization_policy` 保持每个原子 closeout 只领取 selector 返回的一项，闭合后同一 run 可重新 selector，默认最多 3 个 work item 或运行 180 分钟。
7. PRD、architecture、roadmap、plan、backlog 和 acceptance：面向不同职责的投影。

当前 `complexity_health=warning_all_dimensions`：数量面已到硬上限，AGENTS/machine plan/verifier/tests 已超过 80% warning 线。该状态要求后续增长先做同切片等量减重，不能被解读为控制面重量问题已经消失。

v3.23 正文是自包含候选，不依赖 v3.14-v3.22 补语义。旧版本只进入版本谱系和评审证据，不能成为实现时的隐式要求；冻结 v3.17-v3.22 文件保留为精确 archives。本文已声明但尚未物化的规范 artifact 各自拥有独立 ID/version；首次落盘关闭 inventory 缺口，不允许原地改写正文或已 present artifact。若比较评测改变 Batch 禁止面、adapter、authority、并发、Q0 trigger、质量晋升或事实来源，必须冻结 v3.23 并建立 v3.24 successor，不能以文档投影原地改写候选语义。

无版本 [baseline candidate entry](D:/CODE/local-ai-dev-orchestrator/docs/specs/local-ai-runtime-0.2-baseline-candidate.md) 只提供稳定发现路径。它由 `planning-status.json` 的 `baseline_entry` 绑定到 v3.23 的 ID、路径、精确字节和 SHA-256，且 `approval_input=false`；它不能复制、替代或修订冻结正文。

## 当前权威文档

| 文档 | 职责 | 不承担 |
|---|---|---|
| [PRD](D:/CODE/local-ai-dev-orchestrator/docs/product/orchestrator-prd.md) | 用户、产品面、工作流、目标、非目标、成功口径 | 逐字段协议 |
| [目标架构](D:/CODE/local-ai-dev-orchestrator/docs/architecture/orchestrator-target-architecture.md) | 组件、信任边界、数据流、状态和迁移架构 | 当前实现完成声明 |
| [路线图](D:/CODE/local-ai-dev-orchestrator/docs/roadmap/orchestrator-roadmap.md) | P0A-P5 阶段、入口和出口 | 单任务修改步骤 |
| [实施计划](D:/CODE/local-ai-dev-orchestrator/docs/plans/orchestrator-implementation-plan.md) | AI 执行协议、阶段顺序、切片策略 | 规范正文替代品 |
| [任务清单](D:/CODE/local-ai-dev-orchestrator/docs/backlog/orchestrator-task-list.md) | 人类可读 backlog 和状态 | 机器依赖真源 |
| [machine work items](D:/CODE/local-ai-dev-orchestrator/docs/plans/local-ai-runtime-0.2-work-items.json) | 稳定 ID、依赖、范围、验收、命令、证据、回滚、停止条件 | Baseline Approval |
| [验收与门禁](D:/CODE/local-ai-dev-orchestrator/docs/specs/acceptance-and-gates.md) | 三层门、开发门、Q0、cohort、硬门 | 运行证据本身 |
| [selector policy](D:/CODE/local-ai-dev-orchestrator/docs/architecture/next-work-selection-policy.json) | 阶段选择优先级 | 状态变更 |

## 当前运行事实

- `runtime/host-orchestrator` 仍是唯一现行可信内核。
- `.ai/state/control-plane.db` 和 `.ai/runs/<run_id>/<task_id>/` 继续按 legacy 合同工作。
- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/` 是既有 experimental 迁移输入，不是 v3.23 目标包，也不自动晋升。
- `runtime/local-ai-runtime` 尚不存在。
- `.ai/config`、provider/auth、scheduled task、live probe、repo ownership 和默认入口均未因本次文档更新改变。
- Native thin-path / capability comparative evaluation 已完成并记录 `preserve_v3_23_semantics`。结果不 promotion 当前 high-effort profile，也不删除独立 gates/evidence/recovery；当前回到 P0A 规范闭包。P0B Truth Reset 及之后任务全部被 active Baseline Approval 阻断。

## AI 执行协议

每个编码任务按以下固定顺序执行：

1. 运行 `python scripts/select-next-work.py`，只接受返回的 action 和 `current_work_item.task_id`。
2. 从 machine work items 读取该任务的 dependencies、preconditions、scope、acceptance、verification、rollback、stop_conditions 和 prohibited_actions。
3. 证明依赖已完成且当前门有效；不能证明时停止，不猜测完成状态。
4. 只修改 `scope.primary_files` 及为测试/证据必要的邻近文件；范围扩大必须回写任务定义或创建后继任务。
5. 先写失败测试或 verifier fixture，再做最小实现。
6. 按任务列出的命令验证，并补跑项目固定顺序 `build -> test -> contract/invariant -> hotspot`。
7. 在 `docs/change-evidence/` 写命令、退出码、关键结果、N/A、风险和只回滚本切片的方法。
8. 只有所有 acceptance 逐项有证据时，才把任务状态改为 `completed`，并激活唯一后继任务。

完成第 8 步后才允许同一 run 重新从第 1 步开始。bounded continuation 不跨阶段/批准边界，不跨 v3.23 successor，不触及 live/auth/provider/remote/破坏性动作；失败或预算耗尽即停止。work item 是原子闭环，不再等同于一个 AI 会话。

不得由 AI 自行创建 `BaselineApprovalRecord`、`ImplementationAcceptanceRecord` 或 `FullQ0Record`，除非任务明确具有相应授权和全部前置证据。

## 历史与兼容资料

以下文件属于 legacy、experimental 或 non-authoritative 资料，只可用于理解既有行为，不是 v3.23 新实现的规范语义源：

- `docs/specs/task-contract.md`
- `docs/specs/result-contract.md`
- `docs/specs/state-and-db.md`
- `docs/specs/runtime-v2-kernel.md`
- `docs/specs/config-and-worker-profiles.md`
- `docs/specs/run-state-and-handoff.md`
- `docs/specs/adaptive-orchestration.md`
- `docs/runbooks/runtime-v2-cutover-operator-runbook.md`
- `docs/platforms/hermes/`
- `ai_dev_orchestrator_impl_pack/`

这些资料只能用于 P0C legacy inventory、compat 和迁移取证。若与 v3.23 目标语义冲突，必须保持 legacy 行为隔离，并由 approved contract generation 解决，不能在实现中私自折中。特别是 `adaptive-orchestration.md` 记录的是历史 experimental overlay；当前队列和下一项只能从 `planning-status.json`、v3.23 candidate、machine work items 与 selector 获取。

## 验证入口

```powershell
python scripts/verify-planning-status.py
python scripts/select-next-work.py
uv run --project ./runtime/host-orchestrator python -m pytest
pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit
git diff --check
```

planning verifier 只证明规划陈述与文件事实一致。Baseline Approval、Implementation Acceptance、Full Q0 / P2 Admission 是三个独立的、不可相互替代的门。
