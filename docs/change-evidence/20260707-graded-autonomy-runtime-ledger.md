# 2026-07-07 Graded Autonomy Runtime Ledger

## Slice

- `dispatch_state.json` 已从 operator asset 升级为 runtime-backed ledger，固定落在 `.ai/runs/<run_id>/<task_id>/dispatch_state.json`
- `result.json` 现在会盖章 `cleanup_owner`、`status_reason`、`dispatch_state_ref`
- `runtime_tasks` 现在索引 `run_id / attempt / state_reason / next_action / cleanup_status / cleanup_owner / dispatch_state_path`
- `allowed_paths / forbidden_paths / worktree_path / branch_name` 不再只做声明校验；当前在具备 `.git` admin path 的 workspace 中，worker 结束后会对新的变更集做 fail-closed 审计
- graded autonomy 当前收口为：
  - 低风险任务默认自动推进
  - medium/high/critical 风险、policy surface、以及 force-on review 停在 `needs_review`
  - 高风险、依赖、lane/network/gui 能力不匹配停在 `waiting_handoff`
- prompt 资产与 closeout 示例已改成 role-aware / risk-aware / lane-aware model policy，不再把所有子代理写死为 `gpt-5.4 + xhigh`

## Code Points

- `runtime/host-orchestrator/src/host_orchestrator/dispatch_state.py`
- `runtime/host-orchestrator/src/host_orchestrator/path_guard.py`
- `runtime/host-orchestrator/src/host_orchestrator/canonical_result.py`
- `runtime/host-orchestrator/src/host_orchestrator/db.py`
- `runtime/host-orchestrator/src/host_orchestrator/host_local.py`
- `runtime/host-orchestrator/tests/test_agent_work_assets.py`
- `runtime/host-orchestrator/tests/test_path_guard.py`
- `runtime/host-orchestrator/tests/test_planner_adapter.py`
- `runtime/host-orchestrator/tests/test_wave1_execution.py`

## Boundary

- 当前 runtime 已稳定写出 `running / waiting_handoff / needs_review / completed / failed` 主路径
- `queued / input_required / cancelled / stale / resumed` 当前先保留为 schema 与 future lifecycle ops 预留状态；不能写成“已 live 演练”
- `worktree` 当前只代表写入隔离，不代表 memory/provider/session 隔离
- branch deletion 仍不自动化
- 当前仍没有 live `Direct GPT-5.4 API` planner、live `Claude Code + GLM-5.2` review sidecar、或 `platform compatibility green`
- 这次 closeout 只意味着 repo-side graded-autonomy + runtime-ledger 切片完成，不等于 `live accepted`

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest`：pass（52 passed）
- `python .\scripts\verify-planning-status.py`：pass
- `python .\scripts\select-next-work.py`：pass（`next_action = promote_phase1_execution`）
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit -Json`：pass
- `build` 与 `hotspot` 当前仍按 repo-owned `gate_na` 口径记录；替代验证分别是 `pytest` 与 `verifier + pytest + diff hygiene`
