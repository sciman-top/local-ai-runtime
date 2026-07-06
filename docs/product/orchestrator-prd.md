# Local AI Runtime（本地 AI 运行时）PRD

## 产品身份

项目展示名是 `Local AI Runtime`，中文名是 `本地 AI 运行时`。当前本地工作目录与历史仓库 slug 仍为 `local-ai-dev-orchestrator`；本次命名统一不等于目录迁移。

本仓当前主产品线回调为 **Hermes -> AgentBridge -> Codex** 三层闭环，而不是继续沿用“generic orchestrator 主线 + Hermes compatibility lane”的叙事。

其中当前 repo truth 仍保持不变：

- canonical `JSON/YAML` intake 仍是当前运行主路径
- `.ai/runs/<run_id>/<task_id>/result.json` 仍是正式 task-level evidence 主体
- `AgentBridge results/*.md` 当前仍是 compatibility projection
- `runtime/host-orchestrator` 是 `host_local` 可信运行时内核

这意味着产品主线已经回调，但协议反转、字段改名和高阶控制面扩展都仍受迁移窗口约束，不能写成当前事实。

## 目标用户

- Windows-first 的高频 AI coding operator
- 同时使用 Codex、Direct GPT-5.4 API、Claude Code + GLM-5.2 的单人操作者
- 需要 `multi-repo / multi-worker / strong evidence / rollback discipline` 的本地工程流用户

## 三层职责

### Hermes

- 编排 / 学习 / 历史安全边界
- 承载隔离工作流与历史 baseline
- 不在当前 repo truth 中被误写成“只剩兼容残留”

### AgentBridge

- 唯一跨层文件契约
- 终态承接 Hermes 任务正文与结果投影
- 当前 repo truth 下，markdown task intake 已在 `host_local` 主路径接线，但只按 repo-owned canonical 默认值安全归一化；markdown result 仍是 compatibility projection，且 repo-side projection parity 已验证

### Codex

- 当前执行层主入口
- `runtime/host-orchestrator` 是 `host_local` 可信运行时内核
- 当前主 worker 仍围绕 `Codex SDK` / `codex exec` / repo-owned worker profiles

## 必须能力

### 控制面

- canonical `JSON/YAML` task contract
- repo-owned `config / worker_profile / policies` contract
- `.ai/state/control-plane.db` 调度真源
- `.ai/runs/<run_id>/<task_id>/` 正式 evidence 面
- Governance Overlay：`selector + change-evidence + preflight + reference governance`
- `AGENTS.md` 共同项目规则主体 + `CLAUDE.md` thin wrapper + 控制仓 global rule source / target-project audit 协同边界
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

### 能力范围与晋升顺序

- `host_local > remote_non_gui > vm_gui`
- `host_local` 是当前主线能力与近期 closeout 对象
- `remote_non_gui` 是次级拓扑能力
- `vm_gui` 只有在出现持续的 GUI-only workload 证据后才进入同等级 closeout

## 非目标

- 不做无闸门 auto-merge
- 不做多租户 SaaS
- 不做云端共享控制面
- 不把当前仓重塑成通用 governance hub
- 不把 AgentBridge round-trip parity、execution-critical override live support、或字段改名写成已完成
- 不在 Phase E parity 前做 `compatibility_projection_ref` 或 `lane` 字段改名
- 不在无真实 GUI-only workload 证据时强行把 `vm_gui` 纳入同等级 live closeout

## 成功标准

### 近期

- 当前 `PHASE-1-VERTICAL-SLICE` 继续维持：canonical task -> 真实 SDK -> `result.json` -> markdown projection
- `planning-status.json` + verifier + selector + preflight 继续成为默认治理 gate
- `selector + change-evidence + preflight + reference governance` 继续作为 Governance Overlay 生效
- 当前 truth boundary 在 authoritative docs 中保持一致，不再把目标态写成当前事实

### 中期

- `host_local` 正确性、verification runner、安全边界下的 AgentBridge-first intake、以及 repo-side projection parity 已落地；后续才进入更高阶 planner/review 与 Hermes parity
- planner/review 触发条件全是机器可判定字段
- AgentBridge round-trip 与 Hermes parity 能在不反转 repo truth 的前提下推进

### 长期

- 形成可持续的 `Hermes -> AgentBridge -> Codex` 单机三层闭环
- `remote_non_gui` 与条件晋升后的 `vm_gui` 进入受控拓扑扩展
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
- 当前 repo truth 仍是 canonical intake + `result.json` + compatibility projection；目标态只能写成迁移窗口，不得写成当前事实
- `governed-ai-coding-runtime` 只作为 `governance-sidecar` companion 提供 gate / evidence / selector 机制参考，不替代当前主线实现真源
- 全局规则真源在控制仓；本仓只维护 repo-specific truth，并通过 audit + integration + verification 吸收规则治理能力
