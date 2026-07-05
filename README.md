# hermes-agent

本仓当前主产品线已经切换为 **通用本地 AI Dev Orchestrator** 的文档与实现种子仓。

## 当前主真源

- 机器可读规划真源：[docs/architecture/planning-status.json](D:/CODE/hermes-agent/docs/architecture/planning-status.json)
- 文档入口：[docs/README.md](D:/CODE/hermes-agent/docs/README.md)

当前主线明确采用以下口径：

- 在现有 `runtime/host-orchestrator` 骨架上就地演进
- `.ai/state/control-plane.db` 是调度真源
- `.ai/runs/<run_id>/<task_id>/` 是正式 evidence 面
- `Hermes/AgentBridge` 只保留为兼容线与历史基线

## 阅读顺序

1. [docs/README.md](D:/CODE/hermes-agent/docs/README.md)
2. [docs/architecture/planning-status.json](D:/CODE/hermes-agent/docs/architecture/planning-status.json)
3. [docs/product/orchestrator-prd.md](D:/CODE/hermes-agent/docs/product/orchestrator-prd.md)
4. [docs/architecture/orchestrator-target-architecture.md](D:/CODE/hermes-agent/docs/architecture/orchestrator-target-architecture.md)
5. [docs/roadmap/orchestrator-roadmap.md](D:/CODE/hermes-agent/docs/roadmap/orchestrator-roadmap.md)
6. [docs/plans/orchestrator-implementation-plan.md](D:/CODE/hermes-agent/docs/plans/orchestrator-implementation-plan.md)
7. [docs/backlog/orchestrator-task-list.md](D:/CODE/hermes-agent/docs/backlog/orchestrator-task-list.md)

## 兼容线

Hermes/AgentBridge 历史基线与兼容资料入口：

- [docs/platforms/hermes/README.md](D:/CODE/hermes-agent/docs/platforms/hermes/README.md)
- [docs/migrations/hermes-compatibility-demotion.md](D:/CODE/hermes-agent/docs/migrations/hermes-compatibility-demotion.md)

原 `docs/实施计划.md`、`docs/任务清单.md`、`docs/当前交接摘要.md` 等旧入口仍保留原路径，但现在只作为降级指针页，避免后续 AI 再把旧 Hermes 主线误判为当前 authoritative truth。

## 当前实现种子

后续编码默认从以下现有目录开始，而不是新建平行顶层包：

- [runtime/host-orchestrator](D:/CODE/hermes-agent/runtime/host-orchestrator/README.md)
- [ai_dev_orchestrator_impl_pack](D:/CODE/hermes-agent/ai_dev_orchestrator_impl_pack/00_README_FIRST.md)
