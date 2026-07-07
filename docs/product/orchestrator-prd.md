# Local AI Runtime（本地 AI 运行时）PRD

## 产品身份

项目展示名是 `Local AI Runtime`，中文名是 `本地 AI 运行时`。当前本地工作目录与历史仓库 slug 仍为 `local-ai-dev-orchestrator`；本次命名统一不等于目录迁移。

本仓当前主产品线回调为 **Hermes -> AgentBridge -> Codex** 三层闭环，而不是继续沿用“generic orchestrator 主线 + Hermes compatibility lane”的叙事。执行 hot path 当前收敛为 **Codex-first**；Hermes 保留风险编排、runtime ledger、跨执行器适配与历史基线职责，Claude 只作为可插拔 review sidecar。

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

- 风险编排 / runtime ledger / 跨执行器适配 / 历史安全边界
- 承载隔离工作流与历史 baseline
- 不在当前 repo truth 中被误写成“只剩兼容残留”
- 不重复接管 Codex 已有的 native thread / worktree / review / approval 能力

### AgentBridge

- 唯一跨层文件契约
- 终态承接 Hermes 任务正文与结果投影
- 当前 repo truth 下，markdown task intake 已在 `host_local` 主路径接线，但只按 repo-owned canonical 默认值安全归一化；markdown result 仍是 compatibility projection，且 repo-side projection parity 已验证
- 后续若要对齐 MCP Tasks / app-server structured surface，也仍通过 AgentBridge 与 canonical contract 对齐，不反转当前 repo truth

### Codex

- 当前执行层主入口与 hot path
- `runtime/host-orchestrator` 是 `host_local` 可信运行时内核
- 当前主 worker 仍围绕 `Codex SDK` / `codex exec` / repo-owned worker profiles
- 低风险路径默认由 Codex 自动推进；中风险路径允许先执行再阻断式 review；高风险/跨 lane/network/GUI 路径先 handoff

## 必须能力

### 控制面

- canonical `JSON/YAML` task contract
- repo-owned `config / worker_profile / policies` contract
- `.ai/state/control-plane.db` 调度真源
- `.ai/runs/<run_id>/<task_id>/` 正式 evidence 面
- 统一 `task / result / review / dispatch / closeout` 状态枚举与 `next_action / cleanup_owner / cleanup_status / status_reason`
- runtime-backed `dispatch_state.json` ledger，与 `result.json` 和 `runtime_tasks` 同步 `attempt / next_action / cleanup_* / status_reason / dispatch_state_ref`
- Governance Overlay：`selector + change-evidence + preflight + reference governance`
- `AGENTS.md` 共同项目规则主体 + `CLAUDE.md` thin wrapper + 控制仓 global rule source / target-project audit 协同边界
- `runtime/host-orchestrator` 就地演进

### 执行面

- `Codex SDK` 主 worker
- `codex exec` fail-closed fallback
- repo-owned `host_local` task entrypoint：`host-orchestrator --run-task` / `run-host-task.ps1`
- worktree-per-write-task
- single-writer discipline
- `allowed_paths / forbidden_paths / worktree_path / branch_name` 必须成为 runtime enforcement，而不只是静态声明
- 当前 git-backed write-boundary enforcement 会在 worker 后审计新改动；若 workspace 缺少 `.git` admin path，则这一步保持显式边界，不伪装成已验证
- `worktree` 只代表写入隔离，不代表 memory/provider/session 隔离

### 智能层

- `Direct GPT-5.4 API` 仍是高风险 handoff lane，而不是低风险日常默认入口
- `Claude Code + GLM-5.2` 仍是 heterogeneous review lane，而不是所有任务的日常必经路径
- `subagents` 读多写少，写任务需独立 worktree + lease + allowlist
- 当前 planner-gated task 已可先运行 codex-backed live planner sidecar、写出 `planner_result.json`，然后仍停在 `waiting_handoff`；这不是 live `Direct GPT-5.4 API` planner 已执行
- 模型策略改为 role-aware / risk-aware / lane-aware，而不是所有子代理固定 `gpt-5.4 + xhigh`

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
- 当前明确不在 repo-side parity / topology closeout 中做 `compatibility_projection_ref` 或 `lane` 字段改名；待 non-host_local runner wiring 与后续 review 稳定性都真实落地后再复评
- 不在无真实 GUI-only workload 证据时强行把 `vm_gui` 纳入同等级 live closeout

## 成功标准

### 近期

- 当前 `PHASE-1-VERTICAL-SLICE` 继续维持：canonical task -> 真实 SDK -> `result.json` -> markdown projection
- `planning-status.json` + verifier + selector + preflight 继续成为默认治理 gate
- `selector + change-evidence + preflight + reference governance` 继续作为 Governance Overlay 生效
- 当前 truth boundary 在 authoritative docs 中保持一致，不再把目标态写成当前事实
- graded autonomy matrix 当前已明确为：低风险自动推进；medium/high/critical 风险、policy surface、或 force-on review 停在 `needs_review`；高风险/跨 lane/network/GUI 先停在 `waiting_handoff`

### 中期

- `host_local` 正确性、verification runner、安全边界下的 AgentBridge-first intake、repo-side projection parity、live planner sidecar receipt boundary、repo-side review gate、runtime ledger、repo-side lifecycle ops、repo-side structured planner/review/closeout receipts、git-backed write-boundary enforcement、repo-side `leases / route / quota` closeout、deterministic multi-worker simulation suite、`remote_non_gui` promotion evidence、repo-owned Hermes parity / historical snapshot mapping verifier、`vm_gui` conditional promotion evidence、以及 bounded live heterogeneous review receipt 已落地；后续 open set 收窄到 non-host_local runner wiring 与后续 review hardening
- repo-owned `host_local` task entrypoint 与 worker factory 已落地：当前 `host-orchestrator --run-task` / `run-host-task.ps1` 已直接消费 `local_maint` 的 `codex_sdk` 路径，并在结构上支持 `codex_exec`；built-in `codex_exec` profiles 仍保持 non-host-local handoff，而 `scripted / gpt54_direct / claude_glm` 继续 live task execution fail-closed
- 当前字段名决策也已固定：`compatibility_projection_ref` 与 `lane` 继续保持现名，不在当前 repo-side parity / topology closeout 中改名
- planner/review 触发条件全是机器可判定字段，且 `user_forced_planner / user_forced_review` 只允许 force on，不允许伪造 force off
- AgentBridge round-trip 与 Hermes parity 继续在不反转 repo truth 的前提下推进；当前 verifier 只证明 repo-side baseline / snapshot mapping，不自动升级为 `platform compatibility green`

### 长期

- 形成可持续的 `Hermes -> AgentBridge -> Codex` 单机三层闭环
- `remote_non_gui` 与条件晋升后的 `vm_gui` 继续停留在受控拓扑扩展边界；当前只证明 repo-side promotion / fail-closed handoff，不证明 live runner 已执行
- 旧 Hermes 文档退为历史/兼容基线，不再与主真源冲突

## 性能与并发目标

- 单人主机优先，不做多租户假设
- 初期目标：1 个真实 writer 跑通主线
- 中期目标：单仓 1-2 writers，read-heavy workers 4+
- 后续目标：多仓并行、route-based worker orchestration
- 并发判定当前按 `risk + depends_on + policy_surface + write_set + repo truth surface` 共同裁决，不再只看 `write_set`
- 模型成本当前按 `role-aware / risk-aware / lane-aware` 选择，避免把全部任务锁死为同一模型与同一 reasoning 档

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
- repo-owned `host_local` task entrypoint、codex-backed live planner sidecar receipt、以及 bounded live heterogeneous review receipt 只是当前主线 runtime 接线，不等于 live `claude_glm` primary task execution、non-host_local runner、`platform compatibility green`、或 `live accepted`
- 当前 repo truth 仍是 canonical intake + `result.json` + compatibility projection；目标态只能写成迁移窗口，不得写成当前事实
- `governed-ai-coding-runtime` 只作为 `governance-sidecar` companion 提供 gate / evidence / selector 机制参考，不替代当前主线实现真源
- 全局规则真源在控制仓；本仓只维护 repo-specific truth，并通过 audit + integration + verification 吸收规则治理能力
