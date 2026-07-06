# Hermes Compatibility Demotion

> Status: superseded by `docs/change-evidence/20260706-strategic-regression.md`

## 目的

本文件保留为历史迁移记录，但不再代表当前 authoritative truth。

旧 demotion 叙事的有效部分仍然存在：

- Hermes/AgentBridge 仍是 `certified_baseline`
- 旧 Hermes 主线文档仍保留历史入口与兼容资料

被本次 strategic return supersede 的部分是：

- “当前主线只能写成 generic orchestrator”
- “Hermes 只剩 compatibility lane 的当前主叙事”
- “AgentBridge 不再作为跨层主契约的目标态”

## 当前 authoritative 口径

当前 authoritative truth 以以下文件为准：

1. `docs/architecture/planning-status.json`
2. `docs/product/orchestrator-prd.md`
3. `docs/architecture/orchestrator-target-architecture.md`
4. `docs/plans/orchestrator-implementation-plan.md`
5. `docs/backlog/orchestrator-task-list.md`
6. `docs/change-evidence/20260706-strategic-regression.md`

## 仍然保留的边界

- `docs/platforms/hermes/` 与 `snapshots/agentbridge-20260628/` 继续作为历史基线与边界证据
- 当前 canonical intake / `result.json` / compatibility projection 的 repo truth 不因 strategic return 被反转
- 后续 AI 仍应从当前 authoritative docs 读取主线，而不是从本文件倒推出当前实现真相
