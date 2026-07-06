# 通用本地 AI Dev Orchestrator PRD

## 产品身份

本仓当前主产品线是 **通用本地 AI Dev Orchestrator**，不是 Hermes maintenance repo 的继续扩写。

它的目标是把本地 AI 编码流程收敛为一套可审计、可恢复、可并发、可条件升级的控制面，直接复用现有 `runtime/host-orchestrator` 骨架，而不是重写一个平行系统。

## 目标用户

- Windows-first 的高频 AI coding operator
- 同时使用 Codex、Direct GPT-5.4 API、Claude Code + GLM-5.2 的单人操作者
- 需要 `multi-repo / multi-worker / strong evidence / rollback discipline` 的本地工程流用户

## 必须能力

### 控制面

- Python 确定性 orchestrator
- canonical `JSON/YAML` task contract
- repo-owned `config / worker_profile / policies` contract
- `.ai/state/control-plane.db` 调度真源
- `.ai/runs/<run_id>/<task_id>/` 正式 evidence 面
- Governance Overlay：`planning truth / selector split / repo-level change-evidence / release-style preflight / formal reference governance companion`
- `runtime/host-orchestrator` 就地演进

### 执行面

- `Codex SDK` 主 worker
- `codex exec` fail-closed fallback
- worktree-per-write-task
- single-writer discipline

### 智能层

- `Direct GPT-5.4 API` 条件必经 planner
- `Claude Code + GLM-5.2` 条件必经 heterogeneous review
- `subagents` 读多写少，写任务需独立 worktree + lease + allowlist

### 并发层

- 多仓
- 多 worker
- lease / renew / expire / route / retry
- repo quota / branch quota / worker concurrency limit

## 非目标

- 不做无闸门 auto-merge
- 不做多租户 SaaS
- 不做云端共享控制面
- 不把当前仓重塑成通用 governance hub
- 不把 Hermes/AgentBridge 继续当当前主线协议
- 不在 Phase 1 就宣称 live multi-worker accepted

## 成功标准

### 近期

- Phase 1 垂直切片跑通：canonical task -> 真实 SDK -> result.json -> markdown projection
- 双写过渡方案 A 保持 `repo-side green`
- `planning-status.json` + verifier + selector + preflight 成为默认治理 gate
- `selector + change-evidence + preflight + reference governance` 成为 Phase 1 前置的 Governance Overlay

### 中期

- planner/review 触发条件全是机器可判定字段
- 多仓/多 worker simulation green
- Hermes/AgentBridge compatibility line 能 round-trip

### 长期

- 形成可持续的本地 AI 编排主仓
- 旧 Hermes 文档退为历史/兼容基线，不再与主真源冲突

## 性能与并发目标

- 单人主机优先，不做多租户假设
- 初期目标：1 个真实 writer 跑通主线
- 中期目标：单仓 1-2 writers，read-heavy workers 4+
- 后续目标：多仓并行、route-based worker orchestration

## Acceptance Mapping

当前 acceptance tiers 的 authoritative mapping 固定为：

| tier | 细分状态 |
| --- | --- |
| `repo-side green` | 可包含 `mock green` |
| `multi-worker simulation green` | 无额外子状态要求 |
| `platform compatibility green` | 无额外子状态要求 |
| `live accepted` | 进入前必须先满足 `live probe ready` |

## 风险边界

- 所有 live claim 必须服从四档验收：`repo-side green`、`multi-worker simulation green`、`platform compatibility green`、`live accepted`
- `mock green` 只是 `repo-side green` 的子状态，不是新的 acceptance tier
- `live probe ready` 只是进入 `live accepted` 前的 readiness gate，不是新的 acceptance tier
- planner/review 失败、缺 gateway、缺 credentials 只能降级，不能伪装成 live success
- `Hermes/AgentBridge 兼容线` 只保留兼容与历史承载，不恢复为当前主线 authoritative truth
- `governed-ai-coding-runtime` 只作为 `governance-sidecar` companion 提供 gate / evidence / selector 机制参考，不替代当前主线实现真源
