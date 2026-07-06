# 通用本地 AI Dev Orchestrator 目标架构

## 总原则

- 就地演进 `runtime/host-orchestrator`
- 不新建平行顶层 `orchestrator/` 包
- `.ai/state/control-plane.db` 是调度真源
- `.ai/runs/<run_id>/<task_id>/` 是正式 evidence 面
- `private-local/` 只保留密钥、探针、非正式 smoke
- `Hermes/AgentBridge 兼容线` 是 adapter，不是主协议

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

## 组件边界

### 1. Intake / Normalization

职责：

- 读取 canonical `task.json` / `task.yaml`
- 校验 schema
- 派生 `planner_required` / `review_required` / `touches_policy_surface`
- 盖章运行时字段

依赖契约：

- `docs/specs/task-contract.md`
- `docs/specs/config-and-worker-profiles.md`

### 1A. Config Resolution

职责：

- 读取 `.ai/config/orchestrator.yaml`
- 读取 `.ai/config/workers.yaml`
- 读取 `.ai/config/policies.yaml`
- 把 repo-owned abstraction 映射到实际执行参数
- 对缺失/错误配置给出 deterministic contract error

落点：

- `runtime/host-orchestrator/src/host_orchestrator/`

### 2. Worker Adapters

职责：

- `codex_sdk`
- `codex_exec`
- `gpt54_direct`
- `claude_glm`

约束：

- `worker_kind` 描述 adapter 路径
- `worker_profile` 描述 `.ai/config/workers.yaml` 中的具名配置档

### 3. Verification Runner

职责：

- 按固定顺序执行 `build -> [lint -> typecheck] -> test -> contract -> hotspot`
- 产出 `verification_summary.json`

### 4. Evidence Writer

职责：

- 落盘 `result.json`
- 落盘 `stdout.log` / `stderr.log`
- 落盘 `verification_summary.json`
- 落盘 `cost_summary.json`
- 落盘 `evidence_index.json`
- 落盘 `compatibility_projection_ref`（如启用 dual-write）

依赖契约：

- `docs/specs/result-contract.md`
- `docs/specs/run-state-and-handoff.md`

### 5. Compatibility Adapter

职责：

- `AgentBridge markdown -> canonical task`
- `canonical result / review -> markdown projection`

边界：

- 只服务 Hermes/AgentBridge 兼容线
- 不再承载当前主线 authoritative truth

## 存储拆分

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

### 非正式隔离态

- `private-local/wave-smokes/`
- `private-local/` 下的密钥、本机探针、非正式回放态

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

## 兼容线位置

Hermes/AgentBridge 历史与兼容资料位于：

- `docs/platforms/hermes/`
- `snapshots/agentbridge-20260628/`

当前主线只引用它们作为 `certified_baseline`，不再以它们定义当前 active queue。
