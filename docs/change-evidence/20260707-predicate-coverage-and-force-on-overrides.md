# 2026-07-07 Predicate Coverage And Force-On Overrides

## Slice

- 这次把 `P4-T03` 从“计划中的正反触发谓词测试”推进成 repo-side 已验证切片
- `planner_required` 与 `review_required` 现在不仅有正反测试覆盖，也正式承接了 `user_forced_planner / user_forced_review`
- 这两个 override 当前只允许 `true`；`false` 会被 canonical task 与 manifest contract 一起拒绝，避免伪造“强制关闭 gate”
- 配套 prompt / operator guide / task contract 也同步收口，避免 runtime truth 与操作资产再次漂移

## Files

- `runtime/host-orchestrator/src/host_orchestrator/canonical_task.py`
- `runtime/host-orchestrator/src/host_orchestrator/agent_work_assets.py`
- `runtime/host-orchestrator/tests/test_planner_adapter.py`
- `runtime/host-orchestrator/tests/test_agent_work_assets.py`
- `templates/agent-work-manifest.example.yaml`
- `templates/agent-work-manifest.schema.json`
- `prompts/subagent-worktree/README.md`
- `prompts/subagent-worktree/master.prompt.md`
- `docs/主控-子代理-worktree-协作模式.md`
- `docs/specs/task-contract.md`
- `docs/README.md`
- `docs/architecture/orchestrator-target-architecture.md`
- `docs/product/orchestrator-prd.md`
- `docs/roadmap/orchestrator-roadmap.md`
- `docs/plans/orchestrator-implementation-plan.md`
- `docs/backlog/orchestrator-task-list.md`

## Boundary

- 当前只完成 repo-side predicate coverage 与 force-on override contract
- 当前仍没有接入 live `Direct GPT-5.4 API` planner
- 当前仍没有接入 live `Claude Code + GLM-5.2` reviewer
- 当前仍没有把 `dispatch_state` / `closeout_bundle` 升级成 runtime 强制状态机
- 当前仍没有实现 `P3-T02` path guard；官方与社区研究都表明 worktree 不是完整状态隔离，因此这仍是当前最值钱的下一刀

## Research Alignment

- 官方研究确认：OpenAI Codex、Anthropic Claude Code、Git 官方文档都支持 `主控 + 子代理 + worktree / structured contract / approval or review boundary / verification-oriented closeout` 这个大方向
- 官方研究同时确认：`worktree` 只是 Git 级隔离，不等于完整状态隔离；handoff、review gate、closeout bundle 仍应保持 repo-owned contract
- 社区研究确认：高质量样本真正可泛化的价值不在于 prompt 更长，而在于 `manifest -> dispatch ledger -> handoff payload -> review/closeout receipt -> cleanup guard` 的 machine-readable 控制面

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_planner_adapter.py runtime\host-orchestrator\tests\test_agent_work_assets.py`：pass（13 passed）
- `uv run --project .\runtime\host-orchestrator python -m pytest`：pass（42 passed）
- `uv run --project .\runtime\host-orchestrator python .\scripts\validate-agent-work-assets.py`：pass
- `python .\scripts\verify-planning-status.py`：pass
- `python .\scripts\select-next-work.py`：pass（`next_action = promote_phase1_execution`）
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit -Json`：pass
- `git diff --check`：pass
