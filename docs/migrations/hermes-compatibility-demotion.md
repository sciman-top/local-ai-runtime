# Hermes Compatibility Demotion

## 目的

把 Hermes/AgentBridge 从“当前主线真源”降级为“历史基线 + 兼容产品线”。

## 现在的结构

### 当前主线

- `README.md`
- `docs/README.md`
- `docs/architecture/planning-status.json`
- `docs/product/*`
- `docs/architecture/*`
- `docs/specs/*`
- `docs/roadmap/*`
- `docs/plans/*`
- `docs/backlog/*`

### Hermes 兼容线

- `docs/platforms/hermes/`
- `snapshots/agentbridge-20260628/`

## 下沉规则

- 旧 Hermes 主线文档不删除
- 顶层旧入口改成降级说明或指针页
- Hermes 历史内容迁到 `docs/platforms/hermes/`
- `planning-status.json.certified_baseline` 指向 Hermes compatibility baseline

## Claim Boundary

- 可以宣称：
  - Hermes/AgentBridge 是已验收历史基线
  - Hermes/AgentBridge 仍是兼容线
- 不可以宣称：
  - Hermes/AgentBridge 仍定义当前 generic orchestrator 主线
  - 旧 `实施计划 / 任务清单 / 当前交接摘要` 仍是当前 authoritative truth

## 后续 AI 执行入口

后续 AI 编码应先读：

1. `docs/architecture/planning-status.json`
2. `docs/plans/orchestrator-implementation-plan.md`
3. `docs/backlog/orchestrator-task-list.md`

而不是再从 Hermes 历史文档回溯当前主线意图。
