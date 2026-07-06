# Local AI Runtime

- 中文名：**本地 AI 运行时**
- 当前主产品线：`Hermes -> AgentBridge -> Codex`
- 历史仓库 slug 与当前本地工作目录仍为 `local-ai-dev-orchestrator`（`D:\CODE\local-ai-dev-orchestrator`）；本次只统一项目展示名，不执行目录迁移。

Local AI Runtime is a Windows-first local orchestration runtime for audited AI coding work. The current mainline keeps a strict three-layer product narrative, retains canonical normalization plus `result.json` as formal evidence, and treats AgentBridge markdown output as the current compatibility projection while allowing compliant AgentBridge markdown tasks to enter `host_local` through a fail-closed intake adapter.

如果你是第一次进入这个仓库，先看这三处：

1. [docs/README.md](D:/CODE/local-ai-dev-orchestrator/docs/README.md)
2. [docs/architecture/planning-status.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/planning-status.json)
3. [runtime/host-orchestrator](D:/CODE/local-ai-dev-orchestrator/runtime/host-orchestrator/README.md)

本仓当前主产品线回调为 **Hermes -> AgentBridge -> Codex** 三层闭环。当前 repo truth 仍明确保留三条边界：

- canonical `JSON/YAML` task contract 仍是当前内部归一化真源；`host_local` 主路径现已可直接接收合规 AgentBridge markdown task
- `.ai/runs/<run_id>/<task_id>/result.json` 仍是正式 task-level evidence 主体
- `AgentBridge results/*.md` 当前仍是 compatibility projection，而不是已完成的主协议反转

## 当前主真源

- 机器可读规划真源：[docs/architecture/planning-status.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/planning-status.json)
- 文档入口：[docs/README.md](D:/CODE/local-ai-dev-orchestrator/docs/README.md)

当前主线采用以下 repo truth：

- `runtime/host-orchestrator` 是 `host_local` 可信运行时内核，不新建平行顶层包
- `.ai/config/*.yaml` 是 repo-owned runtime contract；正式定义见 [docs/specs/config-and-worker-profiles.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/config-and-worker-profiles.md)
- `.ai/state/control-plane.db` 是调度真源
- `.ai/runs/<run_id>/<task_id>/` 是正式 evidence 面
- `host_local > remote_non_gui > vm_gui` 是终态能力范围与分级晋升顺序，不是同等级当前交付义务
- `AgentBridge-first intake` 已以安全边界接入 `host_local`；execution-critical override 与 markdown 侧 gate 命令仍按 fail-closed 处理

## Governance Overlay

当前主线继续叠加 **Governance Overlay**，但它是 cross-cutting 治理增强面，不替代产品 phase。

- `selector + change-evidence + preflight + reference governance` 是当前 repo-side 治理入口
- 当前预期 next action 仍是 `promote_phase1_execution`
- 当前 active queue 仍是 `PHASE-1-VERTICAL-SLICE`
- repo-side gate 已闭环，但 live posture 仍停在 `live probe ready`
- `governed-ai-coding-runtime` 仍只作为 `governance-sidecar` reference companion，不替代本仓 runtime truth

当前治理入口：

- [docs/change-evidence/README.md](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/README.md)
- [docs/architecture/next-work-selection-policy.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/next-work-selection-policy.json)
- `python .\scripts\select-next-work.py`
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`
- [references/README.md](D:/CODE/local-ai-dev-orchestrator/references/README.md)

## 规则协同

- [AGENTS.md](D:/CODE/local-ai-dev-orchestrator/AGENTS.md) 是本仓共同项目规则真源，负责 repo truth、真实 gate、证据与回滚。
- [CLAUDE.md](D:/CODE/local-ai-dev-orchestrator/CLAUDE.md) 是 Claude thin wrapper；它通过 `@AGENTS.md` 承接共同正文，不复制共同项目事实。
- `D:\CODE\governed-ai-coding-runtime` 是全局规则控制仓；本仓只吸收其 `Codex + Claude` global rule source 与 target-project audit 机制，不接受 blind distribution。

## 阅读顺序

1. [docs/README.md](D:/CODE/local-ai-dev-orchestrator/docs/README.md)
2. [docs/architecture/planning-status.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/planning-status.json)
3. [docs/product/orchestrator-prd.md](D:/CODE/local-ai-dev-orchestrator/docs/product/orchestrator-prd.md)
4. [docs/architecture/orchestrator-target-architecture.md](D:/CODE/local-ai-dev-orchestrator/docs/architecture/orchestrator-target-architecture.md)
5. [docs/roadmap/orchestrator-roadmap.md](D:/CODE/local-ai-dev-orchestrator/docs/roadmap/orchestrator-roadmap.md)
6. [docs/plans/orchestrator-implementation-plan.md](D:/CODE/local-ai-dev-orchestrator/docs/plans/orchestrator-implementation-plan.md)
7. [docs/backlog/orchestrator-task-list.md](D:/CODE/local-ai-dev-orchestrator/docs/backlog/orchestrator-task-list.md)
8. [docs/specs/task-contract.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/task-contract.md)
9. [docs/specs/result-contract.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/result-contract.md)
10. [docs/specs/config-and-worker-profiles.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/config-and-worker-profiles.md)
11. [docs/specs/acceptance-and-gates.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/acceptance-and-gates.md)
12. [docs/specs/run-state-and-handoff.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/run-state-and-handoff.md)
13. [docs/change-evidence/20260706-strategic-regression.md](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-strategic-regression.md)

## 历史与兼容

Hermes/AgentBridge 历史基线与兼容资料入口：

- [docs/platforms/hermes/README.md](D:/CODE/local-ai-dev-orchestrator/docs/platforms/hermes/README.md)
- [docs/migrations/hermes-compatibility-demotion.md](D:/CODE/local-ai-dev-orchestrator/docs/migrations/hermes-compatibility-demotion.md)

这些资料仍是 `certified_baseline` 与边界证据，但不反转当前 canonical intake / `result.json` / compatibility projection 的 repo truth。

## 当前实现内核

后续编码默认从以下现有目录开始，而不是新建平行顶层包：

- [runtime/host-orchestrator](D:/CODE/local-ai-dev-orchestrator/runtime/host-orchestrator/README.md)
- [ai_dev_orchestrator_impl_pack](D:/CODE/local-ai-dev-orchestrator/ai_dev_orchestrator_impl_pack/00_README_FIRST.md)
