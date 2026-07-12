# Local AI Runtime 文档索引

本索引服务于 `local-ai-runtime-0.2-v3.21` 候选重基线。当前状态固定为 `baseline_candidate`、`blocking_stage=baseline_approval`，下一动作是 `close_baseline_normative_package_first`。

## 真源层级

发生冲突时按以下顺序处理，但任何低层文件都不能覆盖更高优先级指令：

1. 仓库运行事实和测试：说明当前真正存在什么。
2. [planning-status.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/planning-status.json)：当前阶段、批准状态、队列和工作项。
3. [v3.21 baseline candidate](D:/CODE/local-ai-dev-orchestrator/docs/specs/local-ai-runtime-0.2-v3.21-baseline-candidate.md)：目标产品与实现语义。
4. [normative package inventory](D:/CODE/local-ai-dev-orchestrator/docs/specs/local-ai-runtime-0.2-normative-package.json)：规范闭包状态。
5. [machine work items](D:/CODE/local-ai-dev-orchestrator/docs/plans/local-ai-runtime-0.2-work-items.json)：58 项执行分解；P1A-P1F 共 33 个单次 AI 编码切片，每次只领取 selector 返回的一项。
6. PRD、architecture、roadmap、plan、backlog 和 acceptance：面向不同职责的投影。

v3.21 正文是自包含候选，不依赖 v3.14-v3.20 补语义。旧版本只进入版本谱系和评审证据，不能成为实现时的隐式要求；v3.19 和冻结 v3.20 文件保留为精确 superseded archives。本文已声明但尚未物化的规范 artifact 各自拥有独立 ID/version；首次落盘关闭 inventory 缺口，不允许原地改写正文或已 present artifact。

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
- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/` 是既有 experimental 迁移输入，不是 v3.21 目标包，也不自动晋升。
- `runtime/local-ai-runtime` 尚不存在。
- `.ai/config`、provider/auth、scheduled task、live probe、repo ownership 和默认入口均未因本次文档更新改变。
- 当前 candidate 规划允许 P0A 规范闭包；P0B Truth Reset 及之后任务全部被 active Baseline Approval 阻断。

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

不得由 AI 自行创建 `BaselineApprovalRecord`、`ImplementationAcceptanceRecord` 或 `FullQ0Record`，除非任务明确具有相应授权和全部前置证据。

## 历史与兼容资料

以下文件仍可用于理解 legacy 行为，但不是 v3.21 新实现的规范语义源：

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

这些资料只能用于 P0C legacy inventory、compat 和迁移取证。若与 v3.21 目标语义冲突，必须保持 legacy 行为隔离，并由 approved contract generation 解决，不能在实现中私自折中。

## 验证入口

```powershell
python scripts/verify-planning-status.py
python scripts/select-next-work.py
uv run --project ./runtime/host-orchestrator python -m pytest
pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit
git diff --check
```

planning verifier 只证明规划陈述与文件事实一致。Baseline Approval、Implementation Acceptance、Full Q0 / P2 Admission 是三个独立的、不可相互替代的门。
