# 文档索引

当前仓库的唯一主线是 **通用本地 AI Dev Orchestrator**。

## Authoritative Truth

以下文件构成当前 authoritative docs，后续 AI 编码应先读这些文件，再动 `runtime/host-orchestrator`：

1. [planning-status.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/planning-status.json)
2. [orchestrator-prd.md](D:/CODE/local-ai-dev-orchestrator/docs/product/orchestrator-prd.md)
3. [orchestrator-target-architecture.md](D:/CODE/local-ai-dev-orchestrator/docs/architecture/orchestrator-target-architecture.md)
4. [next-work-selection-policy.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/next-work-selection-policy.json)
5. [task-contract.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/task-contract.md)
6. [result-contract.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/result-contract.md)
7. [review-contract.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/review-contract.md)
8. [state-and-db.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/state-and-db.md)
9. [config-and-worker-profiles.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/config-and-worker-profiles.md)
10. [acceptance-and-gates.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/acceptance-and-gates.md)
11. [run-state-and-handoff.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/run-state-and-handoff.md)
12. [orchestrator-roadmap.md](D:/CODE/local-ai-dev-orchestrator/docs/roadmap/orchestrator-roadmap.md)
13. [orchestrator-implementation-plan.md](D:/CODE/local-ai-dev-orchestrator/docs/plans/orchestrator-implementation-plan.md)
14. [orchestrator-task-list.md](D:/CODE/local-ai-dev-orchestrator/docs/backlog/orchestrator-task-list.md)
15. [hermes-compatibility-demotion.md](D:/CODE/local-ai-dev-orchestrator/docs/migrations/hermes-compatibility-demotion.md)

## 主线口径

- 当前主线在现有 `runtime/host-orchestrator` 上演进，不新建平行顶层包。
- `.ai/state/control-plane.db` 是调度真源。
- `.ai/runs/<run_id>/<task_id>/` 是正式 evidence 面。
- `.ai/config/*.yaml` 是 repo-owned 运行时配置真源。
- `Hermes/AgentBridge 兼容线` 不再承载当前主线 authoritative truth。
- 当前 active queue 仍是 `Phase 1 垂直切片`；repo-side exit gates 已闭环，下一 bounded slice 是 `P2-T03 AgentBridge round-trip parity`，但 live posture 仍停在 `live probe ready`。

## Governance Overlay

治理增强层是当前主线的 cross-cutting overlay，不替代 `Phase 1 -> Phase 6` 产品路线图。

- `selector + change-evidence + preflight + reference governance` 是 Phase 1 推进前和推进过程中的治理增强面。
- 当前 selector 预期结果是 `promote_phase1_execution`；GPT-5.4 gateway 与 `codex exec` prerequisite probes 已 ready，`P1-T05` evidence integrity 也已补齐，但 `network_proxy` 仍是 `platform_na`，所以 live execution 仍先限纯本地任务。
- `governed-ai-coding-runtime` 已被纳入正式 `governance-sidecar` companion，但它只提供治理机制参考，不定义当前主线实现真相。

当前治理入口：

- [next-work-selection-policy.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/next-work-selection-policy.json)
- [change-evidence/README.md](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/README.md)
- [references/README.md](D:/CODE/local-ai-dev-orchestrator/references/README.md)

## Rule Coordination

- [AGENTS.md](D:/CODE/local-ai-dev-orchestrator/AGENTS.md) 是本仓共同项目规则主体。
- [CLAUDE.md](D:/CODE/local-ai-dev-orchestrator/CLAUDE.md) 是 Claude thin wrapper；首个非空行是独立 `@AGENTS.md`。
- `D:\CODE\governed-ai-coding-runtime` 是全局规则控制仓，只负责 `Codex + Claude` global-only rule sync 与 target-project audit；本仓不负责全局规则分发。
- 本仓项目规则差异必须通过 `audit + integration + verification` 闭环解决，不允许 blind overwrite。

## 兼容与历史

Hermes/AgentBridge 历史基线与兼容资料入口：

- [docs/platforms/hermes/README.md](D:/CODE/local-ai-dev-orchestrator/docs/platforms/hermes/README.md)

参考源码策略仍保留：

- [参考项目清单.md](D:/CODE/local-ai-dev-orchestrator/docs/参考项目清单.md)
- [社区参考源码策略.md](D:/CODE/local-ai-dev-orchestrator/docs/社区参考源码策略.md)
