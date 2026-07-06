# 2026-07-07 Official Research: Subagents, Worktrees, Structured Contracts, Review Gates, and Closeout

## Goal

- 只基于第一方 / 官方文档，调查截至 `2026-07-07` 与 `主控 + 子代理 + worktree / isolated workspace / handoff / review gate / structured outputs / closeout` 最相关的资料
- 优先覆盖 `OpenAI Codex / OpenAI docs`、`Anthropic Claude Code docs`、`Git 官方文档`
- 明确区分：
  - `文档明确支持`
  - `根据文档推断`
- 给出与本仓当前 `repo-owned 主控 + 子代理 + worktree + handoff/review/closeout` 模式的对照建议

## Scope And Method

- 来源范围只限官方 / 第一方文档
- 访问日期统一为 `2026-07-07`
- 本文只回答“官方文档是否明确支持、支持到什么边界、哪些仍需 repo 自定义协议”
- 本文不把“未在本次查到”直接等同于“官方绝对不支持”；这类结论一律标成 `根据文档推断`

## Sources

### OpenAI / Codex

- `https://developers.openai.com/codex/subagents` (accessed `2026-07-07`)
- `https://developers.openai.com/codex/concepts/subagents` (accessed `2026-07-07`)
- `https://developers.openai.com/codex/app/worktrees` (accessed `2026-07-07`)
- `https://developers.openai.com/codex/agent-approvals-security` (accessed `2026-07-07`)
- `https://developers.openai.com/codex/concepts/sandboxing/auto-review` (accessed `2026-07-07`)
- `https://developers.openai.com/codex/noninteractive` (accessed `2026-07-07`)
- `https://developers.openai.com/codex/app-server` (accessed `2026-07-07`)
- `https://developers.openai.com/codex/cli/slash-commands` (accessed `2026-07-07`)
- `https://developers.openai.com/codex/app/review` (accessed `2026-07-07`)
- `https://developers.openai.com/codex/use-cases/verified-operations-workflows` (accessed `2026-07-07`)
- `https://developers.openai.com/codex/github-action` (accessed `2026-07-07`)
- `https://developers.openai.com/codex/glossary` (accessed `2026-07-07`)

### Anthropic / Claude Code

- `https://docs.anthropic.com/en/docs/claude-code/sub-agents` (accessed `2026-07-07`)
- `https://docs.anthropic.com/en/docs/claude-code/common-workflows` (accessed `2026-07-07`)
- `https://docs.anthropic.com/en/docs/claude-code/memory` (accessed `2026-07-07`)
- `https://docs.anthropic.com/en/docs/claude-code/hooks` (accessed `2026-07-07`)
- `https://docs.anthropic.com/en/docs/claude-code/output-styles` (accessed `2026-07-07`)
- `https://docs.anthropic.com/en/docs/claude-code/cli-reference` (accessed `2026-07-07`)
- `https://docs.anthropic.com/en/docs/claude-code/security` (accessed `2026-07-07`)
- `https://docs.anthropic.com/en/docs/claude-code/routines` (accessed `2026-07-07`)
- `https://docs.anthropic.com/en/docs/claude-code/ide-integrations` (accessed `2026-07-07`)

### Git

- `https://git-scm.com/docs/git-worktree` (accessed `2026-07-07`)
- `https://git-scm.com/docs/gitrepository-layout` (accessed `2026-07-07`)
- `https://git-scm.com/docs/gitglossary` (accessed `2026-07-07`)

## Key Findings

## 1. 主控 + 子代理

### 文档明确支持

- OpenAI Codex 明确支持 `subagent workflows`：Codex 可以在你明确要求时生成 specialized agents，并在并行执行后汇总结果；官方同时强调 subagent 适合 `bounded job` 且要有 `clear return format`。来源：`OpenAI Codex / Subagents`、`Subagent concepts`
- OpenAI Codex 明确把 subagent 定义成可带有不同模型配置和不同 instructions 的专门代理；官方示例把 `name / description / model / tools` 作为 agent 定义的重要字段。来源：`OpenAI Codex / Subagents`
- Anthropic Claude Code 明确支持 custom subagents；每个 subagent 都有自己的 `context window`、自己的 `tools`、自己的 `custom system prompt`，也可以选不同模型。来源：`Claude Code / Create custom subagents`
- Anthropic 官方明确把 subagent 文件落在 `.claude/agents/` 或 `~/.claude/agents/`，并使用 Markdown + YAML frontmatter 配置。来源：`Claude Code / Create custom subagents`
- Anthropic 官方明确说明 Claude 会根据 subagent 的 `description` 和 `tool access` 自主判断是否调用它。来源：`Claude Code / Create custom subagents`

### 根据文档推断

- 两家官方文档都已经把“主控调度多个专用子代理”视为一等工作模式，但都没有把“跨仓统一的 canonical handoff/result schema”作为内建标准给出来；真正可跨实现复用的 task contract 仍需要 repo 自己定义
- OpenAI 更接近“显式请求后并行生成 subagents，再由主控汇总”；Anthropic 更接近“通过 subagent 定义、工具权限和 prompt shape 让主会话自己决定何时调用”。因此两者都支持“主控 + 子代理”，但路由重心不完全相同

## 2. Worktree / Isolated Workspace / Handoff

### 文档明确支持

- Git 官方明确支持一个仓库挂多个 `working trees`，允许 `more than one branch at a time`；linked worktree 有自己的 working tree 和 index，但共享仓库的大部分公共元数据。来源：`git-worktree`、`gitrepository-layout`
- Git 官方明确要求 linked worktree 用完后应执行 `git worktree remove`；也提供 `lock / unlock / prune / repair / list` 等生命周期命令。来源：`git-worktree`
- OpenAI Codex app 官方明确支持 worktrees：worktree 用于让多个独立任务在同一项目内并行而互不干扰；Git 仓库里的 automations 也可以运行在 dedicated background worktree。来源：`Codex app / Worktrees`、`Codex app / Automations`
- OpenAI Codex 官方明确支持 `Handoff` 在 `Local` 和 `Worktree` 之间移动 thread，并说明 Codex 会处理相关 Git 操作；每个 task branch 也维护自己的 handoff history 以便恢复上下文。来源：`Codex app / Worktrees`、`Codex glossary`
- OpenAI Codex 官方明确把 worktree 背后的 Git 约束说出来：同一 branch 不能同时在多个地方 checkout，因此并行任务要靠 worktree + branch 分离。来源：`Codex app / Worktrees`
- Anthropic 官方在 `Common workflows` 中明确推荐：需要多个 Claude Code session 并行时，使用 Git worktrees。来源：`Claude Code / Common workflows`
- Anthropic 官方在 `Security` 中明确说明 cloud execution 使用 `isolated virtual machines`，默认有限制的 network access，并且 `git push` 只允许当前工作分支。来源：`Claude Code / Security`
- Anthropic 官方在 `Memory` 中明确说明：同一个 Git 仓库下的所有 worktrees 和子目录共享一个 auto memory 目录。来源：`Claude Code / Memory`

### 根据文档推断

- `worktree` 是 Git 级别 checkout / index 隔离，不等于完整的“所有运行时状态都天然隔离”；尤其 Anthropic 官方已明确 auto memory 在同仓 worktrees 之间共享，所以“多 worktree = 多上下文完全隔离”这个说法不成立
- OpenAI Codex app 的 `Handoff` 是强一等特性；Git 官方只提供底层 checkout 生命周期，不提供 AI 级 handoff 语义；Anthropic 在本次查到的官方页里也没有给出与 Codex app 等价的 Local/Worktree handoff 原语。因此跨平台 handoff contract 仍应保持 repo-owned
- 如果本仓未来把 `isolated workspace` 扩大到 cloud / remote lane，Anthropic 官方材料更像“VM 级隔离 + 受控网络 + 分支限制”，OpenAI Codex app 文档更像“worktree lane + thread handoff + app-managed Git operations”；两者不应被混写成同一种 isolation

## 3. Prompt / Manifest / Structured Contract

### 文档明确支持

- OpenAI Codex 官方明确支持 machine-readable 输出通道：`codex exec --json` 会输出 machine-readable events，适合 bot orchestration、CI 和非交互场景。来源：`OpenAI Codex / Non-interactive Mode`
- OpenAI Codex 官方明确支持 version-specific schema generation：`codex app-server generate-ts` 与 `generate-json-schema` 可以从 CLI 生成 TypeScript schema 或 JSON Schema bundle，而且输出与执行该命令的 Codex 版本严格对应。来源：`OpenAI Codex / App Server`
- OpenAI Codex 官方明确支持 project-shared prompt contract：custom slash commands 可以放在项目目录并带 YAML frontmatter，例如 `description`、`argument-hint`、`model`、`requires-approval`。来源：`OpenAI Codex / Slash Commands`
- OpenAI Codex 官方明确支持 plugin manifest：`.codex-plugin/plugin.json` 是 required manifest，还可附加 `skills/`、`hooks/`、`.app.json`、`.mcp.json`。来源：`OpenAI Codex / Build plugins`
- OpenAI Codex 官方明确建议 verified operations 使用 `structured inputs`、`explicit approval`、`verification artifact`，并对成功、失败、重试与证据进行可审计汇报。来源：`OpenAI Codex / Run verified operations`
- Anthropic 官方明确支持几个不同层次的 prompt / contract surface：
  - `CLAUDE.md` 用于项目约定。来源：`Claude Code / CLI reference`
  - `Output styles` 改系统提示中的 role、tone 和 output format。来源：`Claude Code / Output styles`
  - `Subagents` 用 Markdown + YAML frontmatter 定义。来源：`Claude Code / Create custom subagents`
  - `Hooks` 使用 JSON 输入 / 输出格式，可自动执行 shell command、HTTP endpoint 或 LLM prompt。来源：`Claude Code / Hooks`
  - `Routines` 把 prompt、repositories、connectors 打包成一个可自动执行的 saved configuration。来源：`Claude Code / Routines`

### 根据文档推断

- OpenAI 在“结构化 contract 可机器消费”这件事上，官方面最完整：`--json` 事件流、`App Server` schema 生成、plugin manifest、slash command frontmatter、verified-operations prompt shape 可以拼成一套比较完整的 control-plane surface
- Anthropic 官方也有多种结构化 surface，但它们更分散在 `CLAUDE.md / output style / subagent frontmatter / hooks JSON / routine config`；在本次查到的官方页里，没有看到与 OpenAI App Server 同级、专门面向 agent closeout/result contract 的 versioned JSON Schema 面
- 因此如果本仓想要一个跨 OpenAI / Anthropic 的稳定 dispatch/result contract，不应指望直接照搬某一家官方格式；更合理的是 repo 自己保留 canonical schema，再为各家适配

## 4. Human Review / Approval

### 文档明确支持

- OpenAI Codex 官方明确把安全控制拆成两层：`sandbox mode` 决定技术边界，`approval policy` 决定什么时候必须停下来请求批准。来源：`OpenAI Codex / Agent approvals & security`、`Sandbox`
- OpenAI Codex 官方明确说明本地默认网络关闭，并在超出沙箱或受信动作集时走 approval flow。来源：`OpenAI Codex / Agent approvals & security`
- OpenAI Codex 官方明确支持 `Auto-review`：把沙箱边界上的人工批准替换成单独 reviewer agent，但主 agent 仍运行在同一沙箱和同一审批策略下。来源：`OpenAI Codex / Auto-review`
- OpenAI Codex app 官方明确提供 `Review` surface，在变更落地前标出 issues。来源：`OpenAI Codex app / Review`
- OpenAI Codex GitHub Action 官方明确支持把 Codex 质量检查接入 CI workflow，用于 gate changes 或自动 post review。来源：`OpenAI Codex / GitHub Action`
- Anthropic 官方明确支持权限与策略控制面：`Hooks` 可以在 Claude Code 生命周期特定节点自动运行，并使用结构化输入 / 输出阻断或放行动作。来源：`Claude Code / Hooks`
- Anthropic 官方明确说明 cloud execution 有额外安全控制，如 isolated VM、network access control、credential proxy 和 branch restrictions。来源：`Claude Code / Security`

### 根据文档推断

- OpenAI 的官方材料已经把“reviewer agent / review pane / approval policy / CI gate”连成较完整闭环；如果本仓主执行面偏 OpenAI/Codex，这些机制更适合直接映射到 repo 的 review gate 与 approval boundary
- Anthropic 官方材料明确支持权限、hooks 和受控云执行，但在本次查到的页里，没有看到与 OpenAI `Auto-review` 等价的“内建 reviewer agent 替代人工审批”页面；因此若走 Claude Code lane，review gate 更像是 `permissions + hooks + human process` 的组合，而不是现成同构能力

## 5. Verification / Closeout

### 文档明确支持

- OpenAI Codex 官方明确要求 verified operations 在回报前进行验证：从 log、artifact、dashboard、screenshot 或其他 proof 验证结果，再报告哪些成功、失败、重试或需要人工决策。来源：`OpenAI Codex / Run verified operations`
- OpenAI Codex 官方明确支持 non-interactive / CI 驱动 closeout：`codex exec --json` 适合自动化环境，`GitHub Action` 适合在 workflow 中执行质量检查、补丁或 review。来源：`OpenAI Codex / Non-interactive Mode`、`GitHub Action`
- Git 官方明确给出 worktree closeout 的底层生命周期：完成后 `git worktree remove`，离线场景可 `lock`，过期 admin state 可 `prune` 或 `repair`。来源：`git-worktree`
- Anthropic 官方明确支持 `Hooks` 的结构化事件与可编排动作，这为“closeout 前自动做验证 / 阻断 / 告警”提供了第一方扩展点。来源：`Claude Code / Hooks`
- Anthropic 官方明确支持 `Routines` 在 Anthropic-managed cloud 上持续运行，可附加 triggers。来源：`Claude Code / Routines`

### 根据文档推断

- Git 只定义 worktree 生命周期，不定义 AI 任务 closeout bundle；因此 `verification summary / review result / closeout bundle / handoff summary` 这类资产仍应由 repo 自己保持 authoritative schema
- OpenAI 的官方资料已经能支撑“结构化输入 -> 审批 -> 运行 -> 验证 -> 机器可读 closeout”这条链路；Anthropic 官方资料更适合支撑“策略钩子 + 自动例行任务 + 并行会话”，但 closeout schema 仍需 repo-owned

## Cross-Repo Comparison For This Repository

## 建议 1：保留 `repo-owned canonical contract`，不要把任何单家官方格式直接当全仓真源

- 原因：OpenAI 和 Anthropic 都有官方结构化 surface，但字段分布和能力边界不同
- 建议：继续让本仓自己的 `manifest / dispatch_state / review_result / closeout bundle` 做 canonical truth，再分别适配到：
  - OpenAI 的 `subagent definitions / slash command frontmatter / --json / App Server schema`
  - Anthropic 的 `subagent frontmatter / CLAUDE.md / output styles / hooks JSON / routines`

## 建议 2：把 `worktree` 明确定义为执行隔离，不要误写成完整状态隔离

- 原因：Git 官方只保证 checkout / index / per-worktree admin state；Anthropic 官方还明确指出同仓 worktrees 共享 auto memory
- 建议：本仓应继续把 `worktree` 视作文件写入和 branch 并行隔离，而不是把 memory、policy cache、provider state、secrets 访问都默认视作已隔离

## 建议 3：把 `handoff` 继续保持 repo-owned，而不是依赖 Git 原语

- 原因：Git 官方没有 handoff 概念；OpenAI Codex app 有 handoff，但它是 Codex app 特性，不是 Git 通用契约；Anthropic 本次查到的官方页里也没有等价内建 handoff contract
- 建议：本仓现有 `handoff / planner / review / closeout` 资产仍应保留，并继续要求 machine-readable summary 与 artifact refs

## 建议 4：若主执行面偏 OpenAI/Codex，可优先对齐 `approval + auto-review + verified operations`

- 原因：OpenAI 官方已经把 `sandbox`、`approval policy`、`auto-review`、`review surface`、`verified operations` 串成比较完整的一组
- 建议：本仓的 `review_required`、`verification_summary`、`closeout bundle`、`auditable result` 可优先映射到这组官方能力，而不是只做 prose checklist

## 建议 5：若接入 Claude Code lane，应把重点放在 `hooks + permission boundary + memory policy`

- 原因：Anthropic 官方明确给了 hooks JSON、受控云执行、安全边界和 shared memory 事实
- 建议：本仓若允许 Claude 并行 worker 进入同仓 worktrees，应补充：
  - memory sharing guard
  - hook-based verification / block
  - branch / workspace / allowed path validation

## 建议 6：`closeout` 必须同时覆盖任务结果和 worktree 生命周期

- 原因：官方材料把这两层拆开了：
  - OpenAI / Anthropic：更关注 agent 运行、审批、验证、自动化
  - Git：更关注 linked worktree 的底层生命周期
- 建议：本仓 closeout 不应只写“任务完成”，还应显式记录：
  - verification artifact refs
  - review / approval outcome
  - branch / worktree cleanup status
  - residual risk
  - next action

## Bottom Line

- 官方文档已经明确支持 `主控 + 子代理 + worktree / isolated execution / structured prompt surfaces / approval boundary / verification-oriented closeout` 这个大方向
- 但它们支持的是“各平台自己的能力面”，不是一个可直接跨平台复用的统一 control-plane contract
- 对本仓最稳妥的方向不是删掉 repo-owned 协议层，而是：
  - 保留 repo 自己的 canonical schema
  - 把 OpenAI / Anthropic / Git 官方能力接成 adapter layer
  - 把 `worktree lifecycle`、`handoff summary`、`review gate`、`verification artifact`、`closeout bundle` 一起当正式产物

## Uncertainties And Open Questions

- 本次查到的 Anthropic 官方页面里，没有看到与 OpenAI `Auto-review` 对位的“内建 reviewer agent”页面；这应理解为“本次研究未见明确文档”，不应过度外推成“Anthropic 绝对没有”
- OpenAI 的 `Handoff` 明确出现在 Codex app / glossary / worktree 语境中；是否所有执行面都具有完全等价的 handoff UX，本次不作扩展结论
- Git 官方文档提供的是 worktree 机制与生命周期，不提供 AI-level manifest、review gate 或 handoff contract；这些上层协议仍需本仓保持 authoritative 定义
