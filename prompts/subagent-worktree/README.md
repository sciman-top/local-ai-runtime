> Status: non-authoritative operational prompt asset. Use with the current repo truth and a task manifest; do not treat this directory as runtime truth.

# Prompt Pack

这个目录提供一套可复用的 `主控 + 子代理 + worktree` prompt 资产。

使用顺序：

1. 先准备 manifest
   - [templates/agent-work-manifest.example.yaml](D:/CODE/local-ai-dev-orchestrator/templates/agent-work-manifest.example.yaml)
2. 主控开场
   - [master.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/master.prompt.md)
3. 只读探索
   - [explorer.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/explorer.prompt.md)
4. 独立实现
   - [worker.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/worker.prompt.md)
5. 规格复核
   - [spec-reviewer.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/spec-reviewer.prompt.md)
6. 质量复核
   - [quality-reviewer.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/quality-reviewer.prompt.md)

固定要求：

- 所有子代理统一用 `gpt-5.4`
- 所有子代理统一用 `xhigh`
- prompt 资产只提供操作骨架，不替代当前仓库的 authoritative truth
