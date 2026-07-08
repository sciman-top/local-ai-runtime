# Local AI Runtime 目标架构

## 总原则

- 项目展示名：`Local AI Runtime`
- 中文名：`本地 AI 运行时`
- 当前主产品线：`Hermes -> AgentBridge -> Codex`
- 历史仓库 slug / 当前本地目录仍为 `local-ai-dev-orchestrator`

- 产品主线回调为 `Hermes -> AgentBridge -> Codex`
- 执行 hot path 当前收敛为 `Codex-first`
- `runtime/host-orchestrator` 是 `host_local` 可信运行时内核
- 不新建平行顶层 `orchestrator/` 包
- `.ai/state/control-plane.db` 是调度真源
- `.ai/runs/<run_id>/<task_id>/` 是正式 evidence 面
- `private-local/` 只保留密钥、探针、非正式 smoke

## 当前 repo truth 与迁移窗口

当前仓还没有完成协议反转；以下事实必须显式保留：

- 当前 intake 主路径支持 canonical `task.json` / `task.yaml`，并在 `host_local` 边界接收合规 AgentBridge markdown task
- markdown intake 已接线，但只把受支持字段归一化到 repo-owned canonical 默认值；execution-critical override 与 gate 命令输入保持 fail-closed
- repo-owned `host_local` task entrypoint 现已通过 `host-orchestrator --run-task` 与 `runtime/host-orchestrator/scripts/run-host-task.ps1` 落地，并通过 worker factory 支持 `codex_sdk / codex_exec`
- `.ai/runs/<run_id>/<task_id>/result.json` 仍是正式结果主面
- `AgentBridge results/*.md` 当前仍是 compatibility projection
- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/` 已作为同仓新内核落地；当前只服务 dual-track migration，不切默认入口，也不要求改仓库/目录名
- `remote_non_gui` 当前已具备 repo-owned probe profile、promotion evidence、runner wiring readiness contract 与 acceptance schema guard，但 committed `remote_non_gui_probe` 仍保持 `runner_wired=false`，尚未完成真实 remote host runner acceptance；`vm_gui` 当前只有 conditional promotion / handoff proof，尚未完成真实 vm runner 或 GUI-only workload acceptance
- `compatibility_projection_ref` 与 `lane` 字段名当前仍保持代码层 truth；当前已明确决定不在 repo-side parity / topology closeout 中改名，待真实 remote/vm runner acceptance 与后续 review 稳定性都真实落地后再复评

## Kernel V2 Dual-Track

当前吸收的终态重构方式固定为：

- 不新建新 repo
- 不新建平行顶层 `orchestrator/` 包
- v2 新代码统一落在 `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/`
- 双轨期状态与工件固定分面：`.ai/state/control-plane-v2.db` + `.ai/runs-v2/<run_id>/<task_id>/<attempt_id>/`
- cutover 之前，`--run-task` 的默认入口保持 v1；只有 `runtime.active_version = v2` 后才把默认入口切到 v2

## 三层职责

### 1. Hermes

职责：

- 风险编排 / runtime ledger / 跨执行器适配 / 历史安全边界
- 为三层主线提供隔离与历史 baseline
- 在 parity 阶段承接 container lifecycle 与历史映射验证
- 当前 repo-owned `runtime/host-orchestrator/scripts/run-hermes-parity.ps1` 已把 certified baseline doc、current known-good / boundary anchor、snapshot contract、known-good validator、以及 env-sensitive bring-up drift 收进同一 summary
- 当前 repo-owned `runtime/host-orchestrator/scripts/run-vm-gui-promotion.ps1` 已把 default GUI-only handoff 与 explicit `vm_gui_probe` fail-closed handoff 收进同一 summary

边界：

- 当前 repo truth 不把 Hermes 写成“只剩兼容残留”
- 也不把 Hermes 当前就写成已接管 host runtime 的日常双核心执行入口
- 不重复接管 Codex 已有的 native thread / worktree / review / approval 能力

### 2. AgentBridge

职责：

- AgentBridge 是跨层主契约
- Hermes 与 Codex 之间的唯一文件交换面
- 终态承接 markdown task / result / review round-trip
- 未来若要对齐 MCP Tasks / app-server structured surface，也通过 AgentBridge 与 canonical contract 对齐

边界：

- 当前 task intake 仍不是 markdown-first
- 当前 result markdown 仍是 compatibility projection

### 3. Codex

职责：

- 当前执行层主入口与 hot path
- 通过 `runtime/host-orchestrator` 消费 canonical task
- 产出 `result.json`、`dispatch_state.json`、`verification_summary.json`、`cost_summary.json` 与 `evidence_index.json`
- 低风险路径默认自动推进；medium/high/critical 风险、policy surface、force-on review、或能力不匹配路径再转入 review/handoff

边界：

- 当前只落地 `host_local`
- `remote_non_gui` 次级推进
- `vm_gui` 仅条件晋升
- `worktree` 只提供写入隔离，不等于 memory/provider/session 隔离

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
| `model_policy` | role-aware / risk-aware / lane-aware 调度建议 | 由 runtime 写入 `dispatch_state.json` |

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
- 当前 repo-side 已把 canonical task 的 explicit/default `worker_profile` 选择接到真正的 route 决策，并把 `route_reason` materialize 到 `result.json`、`dispatch_state.json`、以及 `route_decisions`
- 当前 repo-side 已把 `planner_required` 的 risk/dependency/force-on 触发接到 live planner sidecar receipt 边界：planner-gated task 会先写 `planner_result.json`，然后继续停在 `waiting_handoff`；worker-profile 不满足 `execution_lane / requires_network / requires_gui`、selected lane 当前没有 wired runner、或超出 `max_active_leases` 的任务仍会在 worker 前 fail closed 到 handoff
- 当前 repo-side 已把 review gate 收敛为 graded autonomy：低风险任务默认自动推进；medium/high/critical 风险、policy surface、以及 force-on review 接到 `needs_review` handoff 路径；`write_access=true` 当前只作为附加 reason，而不是单独触发 review 的充分条件
- 当前 repo-side path guard、worktree manager、cleanup manager、以及 runtime dispatch ledger 已落地：repo-escape path claim、declared worktree root drift、declared branch drift、以及 worker 结束后落在 `allowed_paths` 外或 `forbidden_paths` 内的新改动都会 fail closed；declared isolated worktree 任务在 repo-root 启动时也可由 runtime create/reuse linked worktree；runtime-managed clean linked worktree 会在成功且无需 handoff 的路径上自动 remove，其他路径则保留 worktree 并写出 `worktree_cleanup` 事件；`dispatch_state.json` 与 `runtime_tasks` 会同步 `attempt / status / status_reason / next_action / cleanup_*`
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
- `model_policy` 由 runtime 根据风险、policy surface、lane 与任务角色写入，不再把所有子代理固定到同一模型与同一 reasoning 档
- 当前 repo-owned live task execution 会直接消费 `local_maint` 的 `codex_sdk` 路径；built-in `codex_exec` profiles 仍保持 non-host-local handoff 边界；`scripted / gpt54_direct / claude_glm` 继续 fail-closed，直到对应 live lane 真正接线

### Verification Runner

职责：

- 按固定顺序执行 `build -> [lint -> typecheck] -> test -> contract -> hotspot`
- 产出 `verification_summary.json`
- 当前真实 gate 仍待后续 Phase C 接线

### Evidence Writer

职责：

- 落盘 `result.json`
- 落盘 `dispatch_state.json`
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
- 当前 `runtime_tasks` 已索引 `run_id / attempt / state_reason / next_action / cleanup_status / cleanup_owner / dispatch_state_path`

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

当前 repo-owned `run-hermes-parity.ps1` 只证明这些历史面与当前 truth boundary 保持一致，而 `run-vm-gui-promotion.ps1` 只证明 GUI-only 条件晋升 / fail-closed handoff；它们都不自动升级为 remote/vm runner、`platform compatibility green`、或 `live accepted`。
