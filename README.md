# Local AI Runtime

Local AI Runtime 是 Windows-first 的本地 AI 编码运行时。目标产品由 Codex Native Direct/Spec/Program、Python Policy/Evidence Kernel 和全局单 writer 的 deterministic commit-only Batch 组成；legacy Hermes/AgentBridge/host-orchestrator 最终只保留只读兼容面。

## 当前状态

当前规范候选是 `local-ai-runtime-0.2-v3.21`，状态为 `baseline_candidate`，`blocking_stage=baseline_approval`。完整正文已经落盘，但规范 schema、catalog、transition table、example、fixture、migration specification、独立 verifier 和一致性评审尚未闭合，因此现在仍是 **Request changes**，不是已批准实现基线。

- 当前队列：`LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE`
- 当前动作：`close_baseline_normative_package_first`
- 当前工作项：`LAR-P0A-001`
- 当前可执行内核：`runtime/host-orchestrator`
- 新包 `runtime/local-ai-runtime`：尚不存在，批准前禁止创建
- Truth Reset：未执行
- Implementation Acceptance：未执行
- Full Q0 / P2 Admission：未执行

机器真值在 [planning-status.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/planning-status.json)。`python scripts/verify-planning-status.py` 通过只表示上述陈述内部一致，不表示 baseline 已批准或 runtime 已实现。

## 阅读顺序

1. [planning-status.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/planning-status.json)：当前阶段、门和唯一工作项。
2. [v3.21 baseline candidate](D:/CODE/local-ai-dev-orchestrator/docs/specs/local-ai-runtime-0.2-v3.21-baseline-candidate.md)：完整、自包含目标语义；v3.19 与冻结 v3.20 原始字节保留为 superseded candidates。
3. [normative package inventory](D:/CODE/local-ai-dev-orchestrator/docs/specs/local-ai-runtime-0.2-normative-package.json)：批准前必须闭合的 artifact 及真实缺口。
4. [machine work items](D:/CODE/local-ai-dev-orchestrator/docs/plans/local-ai-runtime-0.2-work-items.json)：v2 机器图，含关闭的 package-root/九子包 source layout、58 项 AI 可执行任务、依赖、验收、命令、证据、回滚和停止条件；其中 P1A-P1F 是 33 个严格串行、单次只执行一个的编码切片。
5. [PRD](D:/CODE/local-ai-dev-orchestrator/docs/product/orchestrator-prd.md) 与 [目标架构](D:/CODE/local-ai-dev-orchestrator/docs/architecture/orchestrator-target-architecture.md)：产品和系统投影。
6. [路线图](D:/CODE/local-ai-dev-orchestrator/docs/roadmap/orchestrator-roadmap.md)、[实施计划](D:/CODE/local-ai-dev-orchestrator/docs/plans/orchestrator-implementation-plan.md)、[任务清单](D:/CODE/local-ai-dev-orchestrator/docs/backlog/orchestrator-task-list.md)：阶段和执行顺序。
7. [验收与门禁](D:/CODE/local-ai-dev-orchestrator/docs/specs/acceptance-and-gates.md)：批准、实现验收、Q0 和 cohort 口径。

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

预期 selector 结果为 `close_baseline_normative_package_first`，并返回 `LAR-P0A-001`。任何实现任务若绕过 Baseline Approval、Truth Reset 或 Legacy Ownership Guard，均属于非法跳阶段。

## 不可误读的结论

- v3.21 正文完整，不等于规范包完整；正文 ID、各 artifact version 和最终 BaselineManifest 是三个不同的版本层次。
- planning gate 绿色，不等于 Baseline Approval 绿色。
- Baseline Approval 绿色，不等于 Implementation Acceptance 绿色。
- Implementation Acceptance 绿色，不等于 Full Q0 或 P2 Admission 绿色。
- repo-side fixture、simulation、probe 或 legacy evidence 不得替代新 runtime 的真实门禁。
- 用户最终仍负责检查、集成、merge 和 push；Batch 0.2 不执行这些操作。
