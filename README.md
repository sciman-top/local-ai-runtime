# Local AI Runtime

Local AI Runtime 是面向 Windows 本机、单操作者信任域的通用受控 AI 开发执行平台。目标产品由 Codex Native Direct/Spec/Program、Python Policy/Evidence Kernel 和全局单 writer 的 deterministic commit-only Batch 组成；legacy Hermes/AgentBridge/host-orchestrator 最终只保留只读兼容面。

## 当前状态

当前规范候选是 `local-ai-runtime-0.2-v3.23`，状态为 `baseline_candidate`，`blocking_stage=baseline_approval`。冻结正文和 v3.23-bound lineage 已落盘，`BaselineManifest.v1` schema/fixtures/verifier skeleton、`CanonicalizationPolicy.v1`、`ProductContract.v1`、`QualificationContractSet.v1` 与 `ExecutionSafetyContractSet.v1` contract bundles 已完成，但最终 manifest 尚未创建且 standalone verifier 尚未冻结；规范包仍如实为 `15 required / 6 present / 9 missing`，因此仍是 **Request changes**，不是已批准实现基线。

稳定发现入口是 [baseline candidate entry](D:/CODE/local-ai-dev-orchestrator/docs/specs/local-ai-runtime-0.2-baseline-candidate.md)。它只导航到冻结 v3.23 正文，不能作为另一份规范正文、`BaselineManifest` 输入或批准证据。

- 当前队列：`LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE`
- 当前动作：`close_baseline_normative_package_first`
- 当前工作项：`LAR-P0A-007`
- 当前可执行内核：`runtime/host-orchestrator`
- 新包 `runtime/local-ai-runtime`：尚不存在，批准前禁止创建
- Truth Reset：未执行
- Implementation Acceptance：未执行
- Full Q0 / P2 Admission：未执行

机器真值在 [planning-status.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/planning-status.json)。`python scripts/verify-planning-status.py` 通过只表示上述陈述内部一致，不表示 baseline 已批准或 runtime 已实现。

AI 实施采用 machine work items 顶层 `planning_optimization_policy`：一个 work item 仍是唯一原子 evidence/commit/rollback 单元，但完整 closeout 后可在同一 run 重新 selector，默认最多 3 个 work item 或运行 180 分钟。失败、预算耗尽、阶段/批准、successor、live/auth/provider/remote/破坏性边界均停止。该策略没有 promotion 新 model/profile，也没有改变 v3.23 的单 writer 或 runtime authority。

当前 planning complexity health 是 `warning_all_dimensions`，不是“已变轻”：14 份权威文档、65 个 work items、11 个 projections 和 15 个 normative artifacts 已在数量硬上限，AGENTS/machine plan/verifier/tests 也都超过 80% warning 线。后续扩展这些面必须在同一切片先合并或删除等量复杂度。

## 阅读顺序

1. [planning-status.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/planning-status.json)：当前阶段、门和唯一工作项。
2. [baseline candidate entry](D:/CODE/local-ai-dev-orchestrator/docs/specs/local-ai-runtime-0.2-baseline-candidate.md)：稳定导航页，受 planning verifier 约束，不复制规范正文。
3. [v3.23 baseline candidate](D:/CODE/local-ai-dev-orchestrator/docs/specs/local-ai-runtime-0.2-v3.23-baseline-candidate.md)：唯一冻结的完整、自包含目标语义；v3.17-v3.22 只作为精确谱系和 superseded inputs 保留。
4. [normative package inventory](D:/CODE/local-ai-dev-orchestrator/docs/specs/local-ai-runtime-0.2-normative-package.json)：批准前必须闭合的 artifact 及真实缺口。
5. [machine work items](D:/CODE/local-ai-dev-orchestrator/docs/plans/local-ai-runtime-0.2-work-items.json)：v3 确定性 DAG，含 Native thin-path 前置评测、关闭的 package-root/九子包 source layout、65 项 AI 可执行任务、11 项稳定 contract projection、依赖、验收、命令、证据、回滚和停止条件；其中 P1A-P1F 是 35 个受全局单 writer 运行边界约束的编码切片。
6. [PRD](D:/CODE/local-ai-dev-orchestrator/docs/product/orchestrator-prd.md) 与 [目标架构](D:/CODE/local-ai-dev-orchestrator/docs/architecture/orchestrator-target-architecture.md)：产品和系统投影。
7. [路线图](D:/CODE/local-ai-dev-orchestrator/docs/roadmap/orchestrator-roadmap.md)、[实施计划](D:/CODE/local-ai-dev-orchestrator/docs/plans/orchestrator-implementation-plan.md)、[任务清单](D:/CODE/local-ai-dev-orchestrator/docs/backlog/orchestrator-task-list.md)：阶段和执行顺序。
8. [验收与门禁](D:/CODE/local-ai-dev-orchestrator/docs/specs/acceptance-and-gates.md)：批准、实现验收、Q0 和 cohort 口径。

## 当前与目标边界

| 面 | 当前事实 | 批准后的目标 |
|---|---|---|
| 执行内核 | `runtime/host-orchestrator`；`.ai/state/control-plane.db` | `runtime/local-ai-runtime` 独立模块化单体 |
| 产品主面 | 既有 Hermes -> AgentBridge -> Codex 兼容运行面 | Unified Native + Batch |
| Batch | 新 Batch 不存在、不可 claim | 已批准模板、qualification、Authorization 下的单 writer commit-only |
| 状态 | legacy DB 与 evidence 保持原样 | 新 runtime 独立 DB、外置 evidence、fenced side effects |
| Git 交付 | legacy 行为不变 | 本地 deterministic commit + task ref；不 merge/push |
| 自治 | 不因本次规划更新扩大 | B0 -> B1 -> B2 -> B3 分级放行 |
| 迁移 | 未 Truth Reset、未 cutover | legacy guard -> isolated implementation -> per-repo CAS cutover |

本轮规划重基线不修改 `.ai/config`、legacy DB、worker profile、默认入口或现有 runtime 行为。根 [AGENTS.md](D:/CODE/local-ai-dev-orchestrator/AGENTS.md) 继续描述现行内核；只有 active Baseline Approval 后的 `LAR-P0B-001` 才能执行 Truth Reset。

## 常用检查

```powershell
uv run --project ./runtime/host-orchestrator python -m pytest
python scripts/verify-planning-status.py
python scripts/select-next-work.py
pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit
git diff --check
```

预期 selector 结果为 `close_baseline_normative_package_first`，并返回 `LAR-P0A-007`。`LAR-P0A-006` 已闭合 `EffectPlan`、stable `writer_effect_id`/attempt-scoped `writer_launch_id`、Writer/StageJob suspended atomic Job join、exact stdio HANDLE_LIST、parent-end close/EOF、execution-commit barrier、Authorization/SafetyOnly authority union、same-name Job fail-closed 与 non-forking adoption；本次未启动 process、打开 Job 或修改 live/runtime authority。`LAR-P0A-EVAL-002` 固定比较已记录 `preserve_v3_23_semantics`：精简 Native 为 `4/9`，Native+agent-side mandatory gate prompt 为 `1/9`，两者都不足以 promotion `gpt-5.6-sol/high` profile；独立 evaluator gates/evidence/recovery 继续保留。18 个 core trial 因外部 host 漂移跨 3 个分别 Q0-admitted CLI generation，合并结果只用于保守决策，不是同 generation profile promotion 证据；CLI execution interface 的资格只绑定当前最终 generation，不能外推到 App Server、SDK、managed Worktree 或 Automations。baseline 仍未批准；任何实现任务若绕过 normative closure、Baseline Approval、Truth Reset 或 Legacy Ownership Guard，均属于非法跳阶段。

## 不可误读的结论

- v3.23 正文完整且谱系 present，不等于规范包完整；正文 ID、各 artifact version 和最终 BaselineManifest 是三个不同的版本层次。
- planning gate 绿色，不等于 Baseline Approval 绿色。
- Baseline Approval 绿色，不等于 Implementation Acceptance 绿色。
- Implementation Acceptance 绿色，不等于 Full Q0 或 P2 Admission 绿色。
- repo-side fixture、simulation、probe 或 legacy evidence 不得替代新 runtime 的真实门禁。
- 用户最终仍负责检查、集成、merge 和 push；Batch 0.2 不执行这些操作。
