# Local AI Runtime 目标架构

## 总原则

- 项目展示名：`Local AI Runtime`
- 中文名：`本地 AI 运行时`
- 当前主产品线：`Hermes -> AgentBridge -> Codex`
- 历史仓库 slug / 当前本地目录仍为 `local-ai-dev-orchestrator`

- 产品主线回调为 `Hermes -> AgentBridge -> Codex`
- `runtime/host-orchestrator` 是 `host_local` 可信运行时内核
- 不新建平行顶层 `orchestrator/` 包
- `.ai/state/control-plane.db` 是调度真源
- `.ai/runs/<run_id>/<task_id>/` 是正式 evidence 面
- `private-local/` 只保留密钥、探针、非正式 smoke

## 当前 repo truth 与迁移窗口

当前仓还没有完成协议反转；以下事实必须显式保留：

- 当前 intake 主路径支持 canonical `task.json` / `task.yaml`，并在 `host_local` 边界接收合规 AgentBridge markdown task
- markdown intake 已接线，但只把受支持字段归一化到 repo-owned canonical 默认值；execution-critical override 与 gate 命令输入保持 fail-closed
- `.ai/runs/<run_id>/<task_id>/result.json` 仍是正式结果主面
- `AgentBridge results/*.md` 当前仍是 compatibility projection
- `remote_non_gui` / `vm_gui` 目前只有 contract 枚举，没有 runner 实现
- `compatibility_projection_ref` 与 `lane` 字段名当前仍保持代码层 truth；迁移是否发生留到 Phase E parity 后决定

## 三层职责

### 1. Hermes

职责：

- 编排 / 学习 / 历史安全边界
- 为三层主线提供隔离与历史 baseline
- 在 parity 阶段承接 container lifecycle 与历史映射验证

边界：

- 当前 repo truth 不把 Hermes 写成“只剩兼容残留”
- 也不把 Hermes 当前就写成已接管 host runtime 的执行入口

### 2. AgentBridge

职责：

- AgentBridge 是跨层主契约
- Hermes 与 Codex 之间的唯一文件交换面
- 终态承接 markdown task / result / review round-trip

边界：

- 当前 task intake 仍不是 markdown-first
- 当前 result markdown 仍是 compatibility projection

### 3. Codex

职责：

- 当前执行层主入口
- 通过 `runtime/host-orchestrator` 消费 canonical task
- 产出 `result.json`、`verification_summary.json`、`cost_summary.json` 与 `evidence_index.json`

边界：

- 当前只落地 `host_local`
- `remote_non_gui` 次级推进
- `vm_gui` 仅条件晋升

## Governance Overlay

这层是当前主线的 cross-cutting overlay，不是新的产品 phase：

- `docs/architecture/planning-status.json`：唯一状态真源
- `docs/architecture/next-work-selection-policy.json`：selector policy 真源
- `scripts/select-next-work.py`：下一步动作选择入口
- `scripts/governance/preflight.ps1`：release-style closeout 入口
- `docs/change-evidence/README.md`：repo-level governance evidence index
- `references/README.md`：formal reference governance companion 入口

边界：

- repo-level governance evidence 只落在 `docs/change-evidence/`
- 它不替代 `.ai/runs/<run_id>/<task_id>/evidence_index.json`
- `governed-ai-coding-runtime` 只作为 `governance-sidecar` companion 参与治理借鉴，不定义当前主线运行时协议

## 规则协同边界

- global rules：`D:\CODE\governed-ai-coding-runtime` 中的 `Codex + Claude` 全局规则源。
- project rules：本仓根 `AGENTS.md`，负责 repo truth、gate、evidence、rollback。
- wrappers：本仓根 `CLAUDE.md`，只写 Claude 差异，不复制共同项目正文。
- enforcement：`.codex`、`.claude/settings.json`、`.claude/rules/`、hooks、CI；它们是确定性限制面，不由 prose 规则副本代替。
- 目标仓与控制仓之间只允许 `audit + integration + verification` 协同；不恢复 blind target-repo rule distribution。

## 正交维度

| 维度 | 当前含义 | 当前口径 |
| --- | --- | --- |
| `execution_lane` | topology | contract 层定义 `host_local / remote_non_gui / vm_gui` |
| `worker_kind` | executor adapter | `codex_sdk / codex_exec / scripted / gpt54_direct / claude_glm` |
| `worker_profile` | repo-owned 具名配置档 | `.ai/config/workers.yaml` |

补充说明：

- 当前 result surface 中代码字段名仍是 `lane`
- 这不否认 contract 层的 `execution_lane` 定义
- 命名统一是后置迁移决策，不在本轮 truth reset 中提前执行

## 组件边界

### Intake / Normalization

职责：

- 当前读取 canonical `task.json` / `task.yaml`，并在 `host_local` 主路径接受合规 AgentBridge markdown task 后归一化到 canonical payload
- 校验 schema
- 校验 markdown front matter contract，并拒绝 execution-critical override / gate command injection
- repo-side parity 当前已验证到 `result.json`、`evidence_index.json`、以及 `AgentBridge/results/*.md` projection 闭环
- 派生 `planner_required` / `review_required` / `touches_policy_surface`
- 当前 repo-side 已把 `planner_required` 的 risk/dependency/force-on 触发接到 `waiting_handoff` handoff 路径，并把 `review_required` 的 risk/write/policy/force-on 触发接到 `needs_review` handoff 路径；当前仍不是 live heterogeneous review adapter
- 当前下一块执行面缺口仍是 path guard；外部研究已确认 worktree 只是 Git 级隔离，不等于完整状态隔离
- 盖章运行时字段

依赖契约：

- `docs/specs/task-contract.md`
- `docs/specs/config-and-worker-profiles.md`

### Config Resolution

职责：

- 读取 `.ai/config/orchestrator.yaml`
- 读取 `.ai/config/workers.yaml`
- 读取 `.ai/config/policies.yaml`
- 把 repo-owned abstraction 映射到实际执行参数
- 对缺失/错误配置给出 deterministic contract error

### Worker Adapters

职责：

- `codex_sdk`
- `codex_exec`
- `gpt54_direct`
- `claude_glm`

约束：

- `worker_kind` 描述 adapter 路径
- `worker_profile` 描述 `.ai/config/workers.yaml` 中的具名配置档

### Verification Runner

职责：

- 按固定顺序执行 `build -> [lint -> typecheck] -> test -> contract -> hotspot`
- 产出 `verification_summary.json`
- 当前真实 gate 仍待后续 Phase C 接线

### Evidence Writer

职责：

- 落盘 `result.json`
- 落盘 `stdout.log` / `stderr.log`
- 落盘 `verification_summary.json`
- 落盘 `cost_summary.json`
- 落盘 `evidence_index.json`
- 落盘 `compatibility_projection_ref`

依赖契约：

- `docs/specs/result-contract.md`
- `docs/specs/run-state-and-handoff.md`

## 存储拆分

### AgentBridge 文件面

- 跨层契约正文
- 终态由 Hermes 与 Codex 共享
- 当前 task intake 尚未切到此主路径

### 调度真源

- `.ai/state/control-plane.db`
- 保存 runtime task state、leases、workers、route decisions、events

### 正式 evidence

- `.ai/runs/<run_id>/<task_id>/`
- 保存每任务正式工件与索引

### repo-level governance evidence

- `docs/change-evidence/README.md`
- 保存 selector / preflight / reference governance 这类 repo-side 治理证据
- 不替代 task-level `evidence_index.json`

## 当前代码落点

后续实现一律从以下现有路径开始，而不是新建 parallel package：

- `runtime/host-orchestrator/src/host_orchestrator/cli.py`
- `runtime/host-orchestrator/src/host_orchestrator/paths.py`
- `runtime/host-orchestrator/src/host_orchestrator/config_runtime.py`
- `runtime/host-orchestrator/src/host_orchestrator/canonical_task.py`
- `runtime/host-orchestrator/src/host_orchestrator/canonical_result.py`
- `runtime/host-orchestrator/src/host_orchestrator/host_local.py`
- `runtime/host-orchestrator/src/host_orchestrator/agentbridge.py`
- `runtime/host-orchestrator/src/host_orchestrator/db.py`
- `runtime/host-orchestrator/src/host_orchestrator/worker.py`
- `runtime/host-orchestrator/src/host_orchestrator/exec_fallback.py`

## 历史基线位置

Hermes/AgentBridge 历史与兼容资料位于：

- `docs/platforms/hermes/`
- `snapshots/agentbridge-20260628/`

当前主线只引用它们作为 `certified_baseline` 与边界证据，不再把它们当作当前 active queue 的直接运行时 truth。
