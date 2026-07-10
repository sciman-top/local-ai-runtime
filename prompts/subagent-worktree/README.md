> Status: non-authoritative operational prompt asset. Use with the current repo truth and a task manifest; do not treat this directory as runtime truth.

# Prompt Pack

这个目录提供一套可复用的 `主控 + 子代理 + worktree` prompt 资产。

使用顺序：

1. 主控先只读确认约束与候选工作流
   - 只声明 `orchestration_constraints`；实际单/多代理模式由 repo-owned decision engine 派生
   - 默认单代理；只有至少两个独立、有界工作流且并行或上下文隔离有实质收益时才允许多代理
2. 再准备 manifest
   - [templates/agent-work-manifest.example.yaml](D:/CODE/local-ai-dev-orchestrator/templates/agent-work-manifest.example.yaml)
   - `manifest` 里的 `allowed_paths / forbidden_paths / verification_commands / handoff_policy` 视为正式 dispatch contract
   - `user_forced_planner / user_forced_review` 只允许 force on；如无明确需要，留空而不是写 `false`
3. 多代理时准备 dispatch state
   - [templates/dispatch-state.example.json](D:/CODE/local-ai-dev-orchestrator/templates/dispatch-state.example.json)
   - 每次派发 explorer / worker / reviewer 都应更新对应 `dispatch_state`
4. 主控开场
   - [master.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/master.prompt.md)
5. 按需只读探索
   - [explorer.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/explorer.prompt.md)
6. 独立实现
   - [worker.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/worker.prompt.md)
7. 规格复核
   - [spec-reviewer.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/spec-reviewer.prompt.md)
8. 质量复核
   - [quality-reviewer.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/quality-reviewer.prompt.md)
   - review 结果可对齐 [templates/review-result.example.json](D:/CODE/local-ai-dev-orchestrator/templates/review-result.example.json)
9. 收口 bundle
   - [templates/closeout-bundle.example.json](D:/CODE/local-ai-dev-orchestrator/templates/closeout-bundle.example.json)
   - [templates/closeout-checklist.md](D:/CODE/local-ai-dev-orchestrator/templates/closeout-checklist.md)

固定要求：

- 子代理模型策略默认按 role-aware / risk-aware / lane-aware 选择，不再统一锁死 `gpt-5.4 + xhigh`
- 多代理默认预算为并发 3、总数 6、树深 1；输入上限写入 `manifest.orchestration_constraints`，实际模式、波次与路由写入 `orchestration_decision.v1`
- 不因模型支持 Multi-agent 就自动派发；没有独立有界工作流或实质收益时保持单代理
- 实际模型与 reasoning effort 由 decision 派生，并在 `dispatch_state.json.model_policy` 与 attempt evidence 中留痕
- prompt 资产只提供操作骨架，不替代当前仓库的 authoritative truth
- `planner_required / review_required` 只能由风险、依赖、policy surface、能力边界和 force-on overrides 派生，不能手写回 canonical task
- 可先运行 `uv run --project .\runtime\host-orchestrator python .\scripts\validate-agent-work-assets.py` 检查模板资产没有漂移

项目级 Codex enforcement：

- [.codex/config.toml](D:/CODE/local-ai-dev-orchestrator/.codex/config.toml) 固定 `max_threads = 4 / max_depth = 1`
- [.codex/agents/explorer.toml](D:/CODE/local-ai-dev-orchestrator/.codex/agents/explorer.toml) 固定为 `gpt-5.6-terra + medium + read-only`
- [.codex/agents/spec_reviewer.toml](D:/CODE/local-ai-dev-orchestrator/.codex/agents/spec_reviewer.toml) 与 [.codex/agents/quality_reviewer.toml](D:/CODE/local-ai-dev-orchestrator/.codex/agents/quality_reviewer.toml) 固定为 `gpt-5.6-sol + high + read-only`
- 当前不覆盖 built-in worker；在 agent session 能被 runtime worktree guard 真实绑定前，不用配置文件假装写入已隔离
