# 2026-07-10 Trellis + Grill vs Superpowers Research

## Question

“Superpowers 太慢且消耗额度，应改用 Trellis + Grill”是否成立？

本文将 Trellis 解释为 [mindfold-ai/Trellis](https://github.com/mindfold-ai/Trellis)。同名项目很多；若建议者指其他实现，结论需要重新核对。

## Verified Facts

### Superpowers

- [Superpowers README](https://github.com/obra/superpowers) 把自己定义为完整开发方法论，而不是单一工具。
- 默认流程包含 brainstorming、worktree、2-5 分钟粒度 implementation plan、subagent-driven development、双阶段 review、严格 TDD、branch closeout。
- 本机 `using-superpowers` 要求只要有 1% 可能适用就加载 skill，并在任何回复或动作前检查。
- 本机安装包含 14 个 Superpowers skill 目录；所有 `SKILL.md` 合计约 108,801 bytes。实际 token 消耗取决于哪些 skill 被加载，不能把文件总量直接等同于每轮 token。

结论：小任务上存在高固定流程成本是事实；“一定浪费额度”仍需真实 usage 数据证明。

### Trellis

- [Trellis README](https://github.com/mindfold-ai/Trellis) 定义四阶段循环：Plan、Implement、Verify、Finish，并明确自动调用 skills 和 sub-agents。
- Trellis 持久化 `.trellis/spec/`、`.trellis/tasks/` 和 `.trellis/workspace/`，自动注入规格、PRD、检查上下文和 journal。
- [Real-World Scenarios](https://docs.trytrellis.app/start/real-world-scenarios) 说明 `trellis init` 会生成约 17 个默认 spec templates 和 bootstrap task。
- [Multi-Platform Configuration](https://docs.trytrellis.app/advanced/multi-platform) 说明 Codex 集成会生成或使用根 `AGENTS.md`、`.codex/skills/`、`.codex/agents/`、prompts 和 hooks。

结论：Trellis 更擅长持久化项目知识和跨平台复用，但并不是轻量执行器；初始化、context injection、PRD、subagents、check 和 journal 同样有成本。

### Grill Me

- [Matt Pocock 的 Grill Me 原文](https://www.aihero.dev/my-grill-me-skill-has-gone-viral) 与本机 skill 都要求逐个问题遍历设计决策，能从代码发现的事实由 agent 自行探索，并为问题提供推荐答案。
- 原文称典型 grilling session 往往持续约 45 分钟。

结论：skill 文件很短，但交互轮数可能很高。它适合高歧义、高代价设计，不适合每个日常修复。

## Missing Evidence

- 未发现可信的 Superpowers vs Trellis + Grill 同任务 A/B benchmark。
- 没有公开证据证明 Trellis + Grill 的 token、延迟或成功率普遍优于 Superpowers。
- README 对自身效果的描述只能证明设计意图，不能替代本机 workload eval。

## Recommendation

- 泛化结论“卸载 Superpowers，Trellis + Grill 更省”不成立。
- 对 greenfield、多成员、多 AI 平台且缺少持久化规范的项目，Trellis 值得 pilot。
- 对需求模糊、架构代价高的任务，按需使用 Grill Me。
- 对小修复、明确功能和已有成熟治理仓，Superpowers 全套流程与 Trellis 全套流程都可能过重。
- 当前仓已具备 `AGENTS.md`、planning status、roadmap/plan/backlog、`.ai` runtime state、manifest、review、gates 和 evidence。直接初始化 Trellis 会形成 `.trellis` 与现有真源的重复治理层，并可能改写或重复 `.codex` 资产。
- 当前仓的推荐方案是：不引入 Trellis；禁用或不采用 `using-superpowers` 的全局强制 bootstrap，只保留按需的 systematic debugging、TDD、verification、worktree/review skills；Grill Me 仅在高歧义设计阶段显式触发。

## Recheck Trigger

- 若要实际替换工作流，应先用同一组代表性任务比较：task success、完整门禁证据、token、延迟、人工轮数、subagent 数、返工和冲突次数。
- 若建议者指的不是 `mindfold-ai/Trellis`，需按具体仓库重新评估。
