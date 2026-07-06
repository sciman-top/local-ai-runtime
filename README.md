# local-ai-dev-orchestrator

本仓当前主产品线已经切换为 **通用本地 AI Dev Orchestrator** 的文档与实现种子仓。

## 当前主真源

- 机器可读规划真源：[docs/architecture/planning-status.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/planning-status.json)
- 文档入口：[docs/README.md](D:/CODE/local-ai-dev-orchestrator/docs/README.md)

当前主线明确采用以下口径：

- 在现有 `runtime/host-orchestrator` 骨架上就地演进
- `.ai/config/*.yaml` 是 repo-owned runtime contract
- `.ai/state/control-plane.db` 是调度真源
- `.ai/runs/<run_id>/<task_id>/` 是正式 evidence 面
- `Hermes/AgentBridge` 只保留为兼容线与历史基线

## Governance Overlay

当前主线额外叠加一层 **Governance Overlay**，但它不是新的产品 phase，也不把本仓改写成 `governed-ai-coding-runtime` 的翻版。

- `selector + change-evidence + preflight + reference governance` 是 Phase 1 推进前和推进过程中的 cross-cutting 治理增强面
- 当前预期 next action 是 `promote_phase1_execution`；repo-side Phase 1 exit gates 已补齐，但 live posture 仍停在 `live probe ready`
- `governed-ai-coding-runtime` 现在是正式的 `governance-sidecar` reference companion，用来借鉴 gate / evidence / selector 治理机制，而不是当前主线实现真源

当前治理入口：

- [docs/change-evidence/README.md](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/README.md)
- [docs/architecture/next-work-selection-policy.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/next-work-selection-policy.json)
- `python .\scripts\select-next-work.py`
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`
- [references/README.md](D:/CODE/local-ai-dev-orchestrator/references/README.md)

## 阅读顺序

1. [docs/README.md](D:/CODE/local-ai-dev-orchestrator/docs/README.md)
2. [docs/architecture/planning-status.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/planning-status.json)
3. [docs/product/orchestrator-prd.md](D:/CODE/local-ai-dev-orchestrator/docs/product/orchestrator-prd.md)
4. [docs/architecture/orchestrator-target-architecture.md](D:/CODE/local-ai-dev-orchestrator/docs/architecture/orchestrator-target-architecture.md)
5. [docs/roadmap/orchestrator-roadmap.md](D:/CODE/local-ai-dev-orchestrator/docs/roadmap/orchestrator-roadmap.md)
6. [docs/plans/orchestrator-implementation-plan.md](D:/CODE/local-ai-dev-orchestrator/docs/plans/orchestrator-implementation-plan.md)
7. [docs/backlog/orchestrator-task-list.md](D:/CODE/local-ai-dev-orchestrator/docs/backlog/orchestrator-task-list.md)
8. [docs/specs/config-and-worker-profiles.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/config-and-worker-profiles.md)
9. [docs/specs/acceptance-and-gates.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/acceptance-and-gates.md)
10. [docs/specs/run-state-and-handoff.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/run-state-and-handoff.md)
11. [docs/change-evidence/README.md](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/README.md)

## 兼容线

Hermes/AgentBridge 历史基线与兼容资料入口：

- [docs/platforms/hermes/README.md](D:/CODE/local-ai-dev-orchestrator/docs/platforms/hermes/README.md)
- [docs/migrations/hermes-compatibility-demotion.md](D:/CODE/local-ai-dev-orchestrator/docs/migrations/hermes-compatibility-demotion.md)

原 `docs/实施计划.md`、`docs/任务清单.md`、`docs/当前交接摘要.md` 等旧入口仍保留原路径，但现在只作为降级指针页，避免后续 AI 再把旧 Hermes 主线误判为当前 authoritative truth。

## 当前实现种子

后续编码默认从以下现有目录开始，而不是新建平行顶层包：

- [runtime/host-orchestrator](D:/CODE/local-ai-dev-orchestrator/runtime/host-orchestrator/README.md)
- [ai_dev_orchestrator_impl_pack](D:/CODE/local-ai-dev-orchestrator/ai_dev_orchestrator_impl_pack/00_README_FIRST.md)
