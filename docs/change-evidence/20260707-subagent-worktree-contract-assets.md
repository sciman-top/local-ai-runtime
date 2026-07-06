# 2026-07-07 Subagent Worktree Contract Assets

## Slice

- 这次在原有 `主控 + 子代理 + worktree` 操作资产基础上，继续把关键协作面推进为更强的 machine-readable contract
- `agent-work-manifest` 现已对齐 canonical task contract 的核心字段，同时保留 `read_set / write_set` 这类 dispatch-only 约束
- 新增 `dispatch_state` 与 `closeout_bundle` 模板 / schema，并补一条 repo-owned 自检入口
- reviewer 侧也补齐了 `review_result` 模板 / schema，避免 prompt 已结构化但 contract 仍缺位

## Files

- `templates/agent-work-manifest.example.yaml`
- `templates/agent-work-manifest.schema.json`
- `templates/dispatch-state.example.json`
- `templates/dispatch-state.schema.json`
- `templates/closeout-bundle.example.json`
- `templates/closeout-bundle.schema.json`
- `templates/review-result.example.json`
- `templates/review-result.schema.json`
- `templates/closeout-checklist.md`
- `scripts/validate-agent-work-assets.py`
- `runtime/host-orchestrator/src/host_orchestrator/agent_work_assets.py`
- `runtime/host-orchestrator/tests/test_agent_work_assets.py`
- `docs/主控-子代理-worktree-协作模式.md`
- `prompts/subagent-worktree/README.md`
- `prompts/subagent-worktree/master.prompt.md`
- `prompts/subagent-worktree/explorer.prompt.md`
- `prompts/subagent-worktree/worker.prompt.md`
- `prompts/subagent-worktree/spec-reviewer.prompt.md`
- `prompts/subagent-worktree/quality-reviewer.prompt.md`
- `docs/README.md`
- `docs/change-evidence/README.md`

## Boundary

- 当前只增强 repo-owned operator assets 与自检能力
- 当前没有修改 `runtime/host-orchestrator` 主执行路径
- 当前没有修改 `planning-status.json`、`.ai/config/*.yaml` 或 current queue
- 当前没有把 `dispatch_state` / `closeout_bundle` 升级成 runtime 强制状态机
- 当前没有把 `review_result` 升级成 runtime blocking gate；当前仍是 operator-first contract
- 当前继续保持子代理默认模型策略为 `gpt-5.4 + xhigh`

## Verification

- `uv run --project .\runtime\host-orchestrator python .\scripts\validate-agent-work-assets.py`：pass
- `uv run --project .\runtime\host-orchestrator python -m pytest`：pass（37 passed）
- `python .\scripts\verify-planning-status.py`：pass
- `python .\scripts\select-next-work.py`：pass（`next_action = promote_phase1_execution`）
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit -Json`：pass
