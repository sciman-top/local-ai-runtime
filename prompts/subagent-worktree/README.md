> Status: non-authoritative operational prompt asset. Use with the current repo truth and a task manifest; do not treat this directory as runtime truth.

# Prompt Pack

这个目录提供一套可复用的 `主控 + 子代理 + worktree` prompt 资产。

使用顺序：

1. 先准备 manifest
   - [templates/agent-work-manifest.example.yaml](D:/CODE/local-ai-dev-orchestrator/templates/agent-work-manifest.example.yaml)
   - `manifest` 里的 `allowed_paths / forbidden_paths / verification_commands / handoff_policy` 视为正式 dispatch contract
   - `user_forced_planner / user_forced_review` 只允许 force on；如无明确需要，留空而不是写 `false`
2. 先准备 dispatch state
   - [templates/dispatch-state.example.json](D:/CODE/local-ai-dev-orchestrator/templates/dispatch-state.example.json)
   - 每次派发 explorer / worker / reviewer 都应更新对应 `dispatch_state`
3. 主控开场
   - [master.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/master.prompt.md)
4. 只读探索
   - [explorer.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/explorer.prompt.md)
5. 独立实现
   - [worker.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/worker.prompt.md)
6. 规格复核
   - [spec-reviewer.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/spec-reviewer.prompt.md)
7. 质量复核
   - [quality-reviewer.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/quality-reviewer.prompt.md)
   - review 结果可对齐 [templates/review-result.example.json](D:/CODE/local-ai-dev-orchestrator/templates/review-result.example.json)
8. 收口 bundle
   - [templates/closeout-bundle.example.json](D:/CODE/local-ai-dev-orchestrator/templates/closeout-bundle.example.json)
   - [templates/closeout-checklist.md](D:/CODE/local-ai-dev-orchestrator/templates/closeout-checklist.md)

固定要求：

- 子代理模型策略默认按 role-aware / risk-aware / lane-aware 选择，不再统一锁死 `gpt-5.4 + xhigh`
- 实际模型与 reasoning effort 以 `dispatch_state.json.model_policy` 为准
- prompt 资产只提供操作骨架，不替代当前仓库的 authoritative truth
- `planner_required / review_required` 只能由风险、依赖、policy surface、能力边界和 force-on overrides 派生，不能手写回 canonical task
- 可先运行 `uv run --project .\runtime\host-orchestrator python .\scripts\validate-agent-work-assets.py` 检查模板资产没有漂移
