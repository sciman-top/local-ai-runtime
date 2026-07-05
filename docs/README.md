# 文档索引

当前仓库的唯一主线是 **通用本地 AI Dev Orchestrator**。

## Authoritative Truth

以下文件构成当前 authoritative docs，后续 AI 编码应先读这些文件，再动 `runtime/host-orchestrator`：

1. [planning-status.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/planning-status.json)
2. [orchestrator-prd.md](D:/CODE/local-ai-dev-orchestrator/docs/product/orchestrator-prd.md)
3. [orchestrator-target-architecture.md](D:/CODE/local-ai-dev-orchestrator/docs/architecture/orchestrator-target-architecture.md)
4. [task-contract.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/task-contract.md)
5. [result-contract.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/result-contract.md)
6. [review-contract.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/review-contract.md)
7. [state-and-db.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/state-and-db.md)
8. [orchestrator-roadmap.md](D:/CODE/local-ai-dev-orchestrator/docs/roadmap/orchestrator-roadmap.md)
9. [orchestrator-implementation-plan.md](D:/CODE/local-ai-dev-orchestrator/docs/plans/orchestrator-implementation-plan.md)
10. [orchestrator-task-list.md](D:/CODE/local-ai-dev-orchestrator/docs/backlog/orchestrator-task-list.md)
11. [hermes-compatibility-demotion.md](D:/CODE/local-ai-dev-orchestrator/docs/migrations/hermes-compatibility-demotion.md)

## 主线口径

- 当前主线在现有 `runtime/host-orchestrator` 上演进，不新建平行顶层包。
- `.ai/state/control-plane.db` 是调度真源。
- `.ai/runs/<run_id>/<task_id>/` 是正式 evidence 面。
- `Hermes/AgentBridge 兼容线` 不再承载当前主线 authoritative truth。
- 当前下一编码队列是 `Phase 1 垂直切片`，重点是 canonical task、真实 SDK 执行、双写过渡方案 A。

## 兼容与历史

Hermes/AgentBridge 历史基线与兼容资料入口：

- [docs/platforms/hermes/README.md](D:/CODE/local-ai-dev-orchestrator/docs/platforms/hermes/README.md)

参考源码策略仍保留：

- [参考项目清单.md](D:/CODE/local-ai-dev-orchestrator/docs/参考项目清单.md)
- [社区参考源码策略.md](D:/CODE/local-ai-dev-orchestrator/docs/社区参考源码策略.md)
