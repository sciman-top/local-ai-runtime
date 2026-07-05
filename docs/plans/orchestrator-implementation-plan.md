# Orchestrator Implementation Plan

## Goal

把当前仓库从 Hermes-oriented 文档维护仓，收敛成一个可直接编码的通用本地 AI Dev Orchestrator 主仓，同时保留 Hermes/AgentBridge 兼容线。

## Working Rules

- 代码一律在 `runtime/host-orchestrator` 上就地演进
- 文档主线以 `planning-status.json` + authoritative docs 为准
- `Phase 1` 采用双写过渡方案 A
- `Wave 1 smoke` 继续隔离在 `private-local/wave-smokes/`
- gate 顺序固定为 `build -> [lint -> typecheck] -> test -> contract -> hotspot`

## Phase 0' 真源收敛

### P0'-T01 主真源落盘

- Files:
  - `README.md`
  - `docs/README.md`
  - `docs/architecture/planning-status.json`
  - `scripts/verify-planning-status.py`
- Inputs:
  - 当前仓顶层入口
  - 新主线口径
- Outputs:
  - 唯一主入口
  - 机器可读规划真源
  - verifier
- Verification:
  - `python scripts/verify-planning-status.py`
- Rollback:
  - revert 文档与 verifier bundle

### P0'-T02 impl_pack 入口改写

- Files:
  - `ai_dev_orchestrator_impl_pack/00_README_FIRST.md`
  - `ai_dev_orchestrator_impl_pack/04_REPOSITORY_LAYOUT.md`
  - `ai_dev_orchestrator_impl_pack/13_BOOTSTRAP_CHECKLIST.md`
  - `ai_dev_orchestrator_impl_pack/14_HANDOFF_MESSAGE_TO_CODEX.md`
- Inputs:
  - 现有 `runtime/host-orchestrator`
- Outputs:
  - 消除 greenfield 叙事
- Verification:
  - 搜索不得再出现“创建项目目录骨架”“生成最小可运行的 Python Orchestrator”
- Rollback:
  - revert impl_pack 四文件

### P0'-T03 Hermes 文档下沉

- Files:
  - `docs/platforms/hermes/`
  - 原 Hermes 主线入口文件
- Outputs:
  - 兼容/历史目录
  - 顶层指针页
- Verification:
  - 顶层旧入口都有降级说明
- Rollback:
  - 恢复顶层旧文件正文

## Phase 1 垂直切片

### P1-T01 默认 layout 迁移

- Files:
  - `runtime/host-orchestrator/src/host_orchestrator/paths.py`
  - `runtime/host-orchestrator/tests/test_scaffold.py`
- Inputs:
  - 现有 `private-local/control-plane`
- Outputs:
  - `.ai/state/control-plane.db`
  - `.ai/runs`
- Verification:
  - `uv run pytest runtime/host-orchestrator/tests/test_scaffold.py -q`
- Rollback:
  - revert layout paths

### P1-T02 canonical task intake

- Files:
  - `runtime/host-orchestrator/src/host_orchestrator/`
  - `docs/specs/task-contract.md`
- Outputs:
  - task loader
  - 派生字段盖章逻辑
- Verification:
  - contract unit tests
- Rollback:
  - revert intake module

### P1-T03 result.json 与双写过渡

- Files:
  - `runtime/host-orchestrator/src/host_orchestrator/host_local.py`
  - `runtime/host-orchestrator/src/host_orchestrator/agentbridge.py`
  - `runtime/host-orchestrator/tests/test_wave1_execution.py`
- Outputs:
  - 正式 `result.json`
  - markdown projection
  - `verification_summary.json`
  - `cost_summary.json`
  - `evidence_index.json`
- Verification:
  - `uv run pytest runtime/host-orchestrator/tests/test_wave1_execution.py -q`
- Rollback:
  - revert dual-write path

### P1-T04 真实 SDK 切片

- Files:
  - `runtime/host-orchestrator/src/host_orchestrator/worker.py`
  - `runtime/host-orchestrator/src/host_orchestrator/exec_fallback.py`
  - `runtime/host-orchestrator/scripts/`
- Preconditions:
  - GPT-5.4 gateway 可用
  - `codex exec` 最小命令可用
- Outputs:
  - 一次真实 SDK run
- Verification:
  - 真实 task run 成功
  - mock 不得记为 live green
- Rollback:
  - 降回 repo-side only，不宣称 live green

## Phase 2 契约与兼容面

### P2-T01 schema 固化

- Files:
  - `docs/specs/*.md`
  - 未来 schema 文件
- Outputs:
  - task/result/review/run-index schema
- Verification:
  - schema validation tests

### P2-T02 AgentBridge round-trip

- Files:
  - `runtime/host-orchestrator/src/host_orchestrator/agentbridge.py`
  - adapter tests
- Outputs:
  - import/export parity
- Verification:
  - round-trip tests 全绿

## Phase 3 执行与验证

### P3-T01 verification runner

- Files:
  - 新增 runner 模块
  - `runtime/host-orchestrator/scripts/`
- Outputs:
  - 固定 gate 顺序执行器
- Verification:
  - `build -> [lint -> typecheck] -> test -> contract -> hotspot`

### P3-T02 worktree manager

- Files:
  - 新增 worktree 模块
- Outputs:
  - quota
  - lifecycle
  - single writer 强制
  - cleanup 幂等

## Phase 4 Planner / Review

### P4-T01 planner adapter

- Outputs:
  - `gpt54_direct` planner adapter
  - machine-checkable `planner_required`

### P4-T02 review adapter

- Outputs:
  - `claude_glm` review adapter
  - machine-checkable `review_required`

## Phase 5 多仓多 worker

### P5-T01 控制面扩展

- Outputs:
  - `task_attempts`
  - `review_outcomes`
  - `handoff_records`
  - `cleanup_records`

### P5-T02 并发治理

- Outputs:
  - heartbeat
  - route
  - retry
  - quota

## Phase 6 Hermes 兼容收口

### P6-T01 parity closeout

- Outputs:
  - canonical ↔ AgentBridge parity green
  - historical snapshot mapping green
  - markdown projection green

## Phase Discipline

每个 phase 的：

- 第一个动作：更新 `planning-status.json`
- 最后一个动作：重跑 `python scripts/verify-planning-status.py`
