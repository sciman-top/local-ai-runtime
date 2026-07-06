# Local AI Runtime 文档索引

- 中文名：**本地 AI 运行时**
- 当前主产品线：`Hermes -> AgentBridge -> Codex`
- 历史仓库 slug 与当前本地工作目录仍为 `local-ai-dev-orchestrator`；本文档索引只统一展示名，不宣称目录已迁移。

当前主产品线回调为 **Hermes -> AgentBridge -> Codex** 三层闭环。当前 authoritative truth 同时保留三条 repo-side 事实：

- canonical `JSON/YAML` intake / canonical JSON/YAML task contract 仍是当前内部归一化真源；`host_local` 主路径现已可直接接收合规 AgentBridge markdown task
- `.ai/runs/<run_id>/<task_id>/result.json` 仍是正式 task-level evidence 主体
- `AgentBridge results/*.md` 当前仍是 compatibility projection；repo-side parity 已验证，但它们仍不取代 `result.json`

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

## 当前主线口径

- 三层主线是：`Hermes -> AgentBridge -> Codex`
- 当前代码仍在 `runtime/host-orchestrator` 上演进，不新建平行顶层包
- `runtime/host-orchestrator` 是 `host_local` 可信运行时内核
- `.ai/state/control-plane.db` 是调度真源
- `.ai/runs/<run_id>/<task_id>/` 是正式 evidence 面
- `.ai/config/*.yaml` 是 repo-owned 运行时配置真源
- `host_local > remote_non_gui > vm_gui` 是终态能力范围与分级晋升顺序
- `AgentBridge-first intake` 已以安全边界接入 `host_local`；markdown task 先归一化到 repo-owned canonical 默认值，并对 execution-critical override fail closed
- `P2-T03` 的 repo-side AgentBridge round-trip parity 已落地，但尚未自动升级为 `platform compatibility green`
- `P4-T01` 的 repo-side planner handoff 已落地；当前只把 planner-gated task 停在 `waiting_handoff`，尚未宣称 live `Direct GPT-5.4 API` planner 已接线
- `P4-T02` 的 repo-side review gate 已落地；当前会把 review-gated task 在 worker / verification 之后停在 `needs_review`，但尚未宣称 live heterogeneous review adapter 已接线
- `P4-T03` 的 repo-side 谓词正反覆盖已落地；`user_forced_planner / user_forced_review` 现在是 contract 承认的 force-on override，而不是文档漂浮字段
- 基于 2026-07-07 的官方与社区研究，下一最值钱的 repo-side 执行切片转向 `P3-T02` path guard，因为 worktree 只是 Git 级隔离，不是完整状态隔离
- `compatibility_projection_ref` 与 `lane` 字段名当前不改；是否迁移留到 Phase E parity 后再决定
- 当前 active queue 仍是 `PHASE-1-VERTICAL-SLICE`；repo-side exit gates 已闭环，但 live posture 仍停在 `live probe ready`

## Governance Overlay

治理增强层是当前主线的 cross-cutting overlay，不替代 `Phase 1 -> Phase 6` 产品路线图。

- `selector + change-evidence + preflight + reference governance` 是当前 repo-side 治理增强面

## Operator Assets

以下文件是 repo-owned 的操作资产，不属于 authoritative runtime truth，但可直接复用：

- 协作模式说明：[docs/主控-子代理-worktree-协作模式.md](D:/CODE/local-ai-dev-orchestrator/docs/主控-子代理-worktree-协作模式.md)
- prompt 资产入口：[prompts/subagent-worktree/README.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/README.md)
- manifest 模板：[templates/agent-work-manifest.example.yaml](D:/CODE/local-ai-dev-orchestrator/templates/agent-work-manifest.example.yaml)
- dispatch state 模板：[templates/dispatch-state.example.json](D:/CODE/local-ai-dev-orchestrator/templates/dispatch-state.example.json)
- review 结果模板：[templates/review-result.example.json](D:/CODE/local-ai-dev-orchestrator/templates/review-result.example.json)
- closeout bundle 模板：[templates/closeout-bundle.example.json](D:/CODE/local-ai-dev-orchestrator/templates/closeout-bundle.example.json)
- closeout 清单：[templates/closeout-checklist.md](D:/CODE/local-ai-dev-orchestrator/templates/closeout-checklist.md)
- 当前 selector 预期结果仍是 `promote_phase1_execution`
- GPT-5.4 gateway 与 `codex exec` prerequisite probes 已 ready，但 `network_proxy` 仍是 `platform_na`，所以 live execution 仍先限纯本地任务
- `governed-ai-coding-runtime` 已被纳入正式 `governance-sidecar` companion，但它只提供治理机制参考，不定义当前主线实现真相

当前治理入口：

- [next-work-selection-policy.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/next-work-selection-policy.json)
- [change-evidence/README.md](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/README.md)
- [change-evidence/20260706-strategic-regression.md](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-strategic-regression.md)
- [references/README.md](D:/CODE/local-ai-dev-orchestrator/references/README.md)

## Rule Coordination

- [AGENTS.md](D:/CODE/local-ai-dev-orchestrator/AGENTS.md) 是本仓共同项目规则主体。
- [CLAUDE.md](D:/CODE/local-ai-dev-orchestrator/CLAUDE.md) 是 Claude thin wrapper；首个非空行是独立 `@AGENTS.md`。
- `D:\CODE\governed-ai-coding-runtime` 是全局规则控制仓，只负责 `Codex + Claude` global-only rule sync 与 target-project audit；本仓不负责全局规则分发。
- 本仓项目规则差异必须通过 `audit + integration + verification` 闭环解决，不允许 blind overwrite。

## 兼容与历史

Hermes/AgentBridge 历史基线与兼容资料入口：

- [docs/platforms/hermes/README.md](D:/CODE/local-ai-dev-orchestrator/docs/platforms/hermes/README.md)
- [docs/migrations/hermes-compatibility-demotion.md](D:/CODE/local-ai-dev-orchestrator/docs/migrations/hermes-compatibility-demotion.md)

参考源码策略仍保留：

- [参考项目清单.md](D:/CODE/local-ai-dev-orchestrator/docs/参考项目清单.md)
- [社区参考源码策略.md](D:/CODE/local-ai-dev-orchestrator/docs/社区参考源码策略.md)
