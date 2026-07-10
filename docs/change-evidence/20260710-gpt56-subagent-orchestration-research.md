# 2026-07-10 GPT-5.6 与子代理编排研究

## Goal

- 核实当前公开 OpenAI / Codex 文档是否已经正式出现 GPT-5.6，以及是否存在“GPT-5.6 会自动大量创建子代理”的明确说明。
- 提炼 Codex 子代理、多代理、worktree、`AGENTS.md`、并行和模型选择的官方边界。
- 对照少量社区项目的一手 README / skill source，给出当前提示词和后续 deterministic enforcement 的改进依据。

## Scope And Method

- 访问日期：`2026-07-10`；官方结论只引用 OpenAI / Codex 第一方公开文档。
- 社区结论只引用仓库 README 或 source，并固定到 commit permalink；未运行这些项目，不把 README 声明写成已实测效果。
- 本文严格区分 `官方事实`、`当前会话事实`、`社区做法` 与 `推断/建议`。
- `https://developers.openai.com/api/docs/models/gpt-5.6` 本次返回的 HTML 标题为 `Page not found | OpenAI API`，因此不以该 URL 作为型号存在的证据；型号证据改用官方 `Using GPT-5.6` 指南和 Codex model catalog。

## Short Verdict

1. **GPT-5.6 已有公开官方文档，不是传闻。** 官方 `Using GPT-5.6` 指南明确列出 `gpt-5.6-sol / terra / luna`，Codex model catalog 也把三者列为 recommended models。
2. **GPT-5.6 确实新增 Multi-agent beta，且能让 root agent 协调并行 subagents。** 但官方没有说“只要使用 GPT-5.6 就会无条件自动大量创建子代理”。
3. **是否委派取决于产品模式、请求配置、developer / project / skill instructions 和任务形状。** Responses API 必须显式设置 `multi_agent.enabled=true`；当前本地 Codex 文档说，local releases 在用户直接要求或适用的 `AGENTS.md` / skill 指令要求时才委派；ChatGPT desktop 的 Ultra 模式则明确会使用 subagents。
4. **“大量”需要显式预算约束。** Responses API 的 Multi-agent 没有固定总数或树深上限，但默认并发是 `3`，官方建议多数工作负载保留该默认值；本地 Codex 的 `agents.max_threads` 默认 `6`、`agents.max_depth` 默认 `1`，官方明确警告提高深度会导致递归 fan-out、token / latency / local resource 增长。
5. **当前长提示词应优化，但重点不是增加更多子代理流程描述。** GPT-5.6 官方 prompting guide 建议从更短提示词开始，只保留模型不会自然完成的约束；子代理并发、深度、sandbox 和角色模型应尽可能落到 `.codex/config.toml` 与 `.codex/agents/*.toml`，仓库真源、门禁和 evidence 仍由 `AGENTS.md` / repo contract 承接。

## Official Facts

### 1. GPT-5.6 与 Multi-agent 的公开状态

- `Using GPT-5.6` 明确说明 `gpt-5.6` alias 路由到 `gpt-5.6-sol`，并提供 `terra` 与 `luna`；同页把 `Multi-agent [beta]` 列为新能力，描述为一个 GPT-5.6 instance 并行协调多个 subagents 并综合结果。
- `Multi-agent` guide 明确说明该 beta 对全部 GPT-5.6 models 可用；请求需设置 `multi_agent.enabled=true`，启用后 root agent 才“eligible to spawn”子代理树。
- 同一 guide 明确给出单代理与多代理的选择边界：独立、bounded、可并行的工作流适合多代理；严格顺序链、共享可变资源、短任务或要求固定 deterministic graph 的任务优先单代理。
- Multi-agent API 默认 `max_concurrent_subagents=3`，官方推荐多数 workload 使用该默认值。虽然 API 没有固定的总子代理数或树深上限，但可用 developer message 约束为“只有用户明确要求才 spawn”，也可声明 proactive delegation。
- Codex `Models` page 明确说明 ChatGPT desktop 的 Ultra 模式不再是单代理运行，而是用 subagents 加速可拆分的复杂任务。

**结论：**“GPT-5.6 具备模型主导的多代理协调能力”是官方事实；“GPT-5.6 默认会自动大量建代理”不是官方通用事实。更准确的说法是：在 Multi-agent / Ultra 或适用指令已经启用委派的执行面中，GPT-5.6 可以自主决定如何 spawn；若不设并发、深度、总任务与写入边界，确有 fan-out 风险。

### 2. Codex 本地子代理的触发、并行和预算

- Codex `Subagents` page 说当前 releases 默认启用 subagent workflow 能力，但当前 local releases 是在直接请求或适用的 `AGENTS.md` / skill 指令要求时实际委派。
- 官方建议从 read-heavy 的 exploration、tests、triage、summarization 开始并行；对 write-heavy 并行更谨慎，因为同时编辑会造成冲突和协调成本。
- 官方内置角色为 `default / worker / explorer`；项目可以在 `.codex/agents/` 定义 custom agents，并为单个角色设置 `model`、`model_reasoning_effort`、`sandbox_mode`、MCP 与 skills。
- `agents.max_threads` 默认 `6`；`agents.max_depth` 默认 `1`。官方建议没有递归委派的明确需求就保留深度 `1`。
- 子代理继承 parent sandbox policy；只有通过 custom agent override，才能例如把 explorer 明确设为 `read-only`。因此 prose 中写“explorer 只读”不等同于技术隔离已经生效。
- 子代理单独执行模型和工具工作，所以相较单代理必然增加 token 消耗。

### 3. 模型选择

- Codex 官方建议 demanding agents 从 GPT-5.6 开始；`gpt-5.6-terra` 适合更快、更低成本的 exploration、read-heavy scan、大文件 review 和 supporting-document processing。
- 若不固定 `model` 或 `model_reasoning_effort`，Codex 可以按任务在 intelligence、speed、price 之间选择；官方并未建议所有子代理一律锁定最高成本档。
- GPT-5.6 prompting guide 建议在代表性任务上比较相同 reasoning effort 与低一档，并衡量 task success、证据完整性、tokens、latency 和 cost；调用更少只有在最终质量仍达标时才算改进。

**对原提示词的影响：**“若使用子代理，默认强模型”可保留为高风险 worker / reviewer 的 policy，但不应覆盖 explorer 和机械验证任务。更稳妥的是 `role-aware + risk-aware`：主控/高风险 worker/reviewer 使用 `gpt-5.6`，轻量只读扫描允许 Codex 自动路由或显式 `terra`，同时以真实 eval 决定。

### 4. Worktree 不是子代理自动隔离

- Codex app worktree 是 ChatGPT desktop 的 task-level Git worktree 能力，用于多个独立任务在同仓并行；它要求 Git repository，并支持 Local / Worktree handoff。
- app-managed worktree 默认是 detached HEAD；同一 branch 不能在两个 worktree 同时 checkout。managed worktree 有单独的清理与快照恢复生命周期。
- 该文档没有声称每个 subagent 会自动得到独立 worktree。结合当前会话工具契约中的 shared filesystem，不能把“spawn subagent”推断成“写入已隔离”。

**对原提示词的影响：**只读 explorer 可以共享 checkout；并行 writer 只有在平台或本仓 runtime 真正创建并校验独立 worktree、branch、cwd 和 allowed paths 后才能并行写。否则应把写入串行化，由主控唯一落盘。

### 5. `AGENTS.md` 与提示词最小化

- Codex 每次 run / TUI session 启动时读取 instruction chain：全局层优先 `AGENTS.override.md`，项目层从 root 向 cwd 逐层读取，每层最多一个文件，更近的规则后出现并覆盖更宽泛指导。
- 默认合并上限是 `project_doc_max_bytes=32 KiB`；官方建议超限时拆到嵌套目录，而不是继续加长根规则。
- GPT-5.6 prompting guide 报告其内部评测中，把冗长显式 system prompts 换成最小提示词，得分提高约 `10-15%`，总 tokens 降低 `41-66%`，成本降低 `33-67%`。这是 OpenAI 内部评测结果，不应外推成所有仓库都必然获得同样幅度。
- 官方建议：保留 outcome、重要约束、approval boundary、success criteria；删除重复工具说明、重复禁止语和已经是模型默认行为的累积规则。

## Current Session Facts

以下仅是本次 Codex desktop 会话的可用能力，不代表所有 Codex / GPT-5.6 环境：

- 当前协作工具契约给出总并发槽 `4`（包括 root），所有 agents 共享同一目录和 filesystem；子代理不是自动 worktree 隔离。
- 当前会话 developer policy 规定：只有用户或适用 `AGENTS.md` / skill 明确要求 subagents / delegation / parallel agent work 时才允许 spawn。本研究因 `research` skill 明确要求 background agent 而合法触发。
- 本机 `codex --version` 为 `codex-cli 0.144.1`；`codex --help` 暴露 `exec / review / app / features / doctor / debug` 等入口。
- `~/.codex/config.toml` 本次只读检查显示默认 `model = "gpt-5.6-sol"`、`model_reasoning_effort = "medium"`，未发现显式 `[agents] max_threads / max_depth`。这是配置默认值，不证明每次 session 没有 profile 或 per-run override。

## Community Source Patterns

### 1. `obra/superpowers`

固定来源：

- [dispatching-parallel-agents](https://github.com/obra/superpowers/blob/d884ae04edebef577e82ff7c4e143debd0bbec99/skills/dispatching-parallel-agents/SKILL.md)
- [using-git-worktrees](https://github.com/obra/superpowers/blob/d884ae04edebef577e82ff7c4e143debd0bbec99/skills/using-git-worktrees/SKILL.md)
- [subagent-driven-development](https://github.com/obra/superpowers/blob/d884ae04edebef577e82ff7c4e143debd0bbec99/skills/subagent-driven-development/SKILL.md)

仓库 source 中可直接验证的模式：

- 只对 independent problem domains 并行；相关失败、共享 state、需要整体上下文或并行会互相干扰时不用并行代理。
- 每个 agent prompt 给具体 scope、goal、constraints 和 expected output；主控在返回后查冲突、读摘要、跑 full suite 并 spot-check。
- worktree 流程先检测是否已在隔离环境，优先平台原生 worktree，随后才是 Git fallback；创建后做项目 setup 和 clean baseline verification。
- 社区 skill 的部分动作（例如在 baseline 失败时必须询问）是该项目自己的 policy，不应直接覆盖本仓 `direct_fix` 与门禁规则。

### 2. `HumanLayer/12-factor-agents`

固定来源：

- [Own your control flow](https://github.com/HumanLayer/12-factor-agents/blob/d20c728368bf9c189d6d7aab704744decb6ec0cc/content/factor-08-own-your-control-flow.md)
- [Small, focused agents](https://github.com/HumanLayer/12-factor-agents/blob/d20c728368bf9c189d6d7aab704744decb6ec0cc/content/factor-10-small-focused-agents.md)

仓库文档中可直接验证的模式：

- agents 是较大、主要 deterministic system 中的一个 building block；控制流、approval、pause/resume、logging/tracing/metrics 应由应用拥有，而不是全交给 prose prompt。
- agent 应小而专注，以便控制 context、职责、测试和 debugging；扩大 agent scope 应以可持续质量为前提。

**可吸收推断：**本仓已有 manifest / dispatch state / review / closeout / gates，最合理的 GPT-5.6 适配是让这些 deterministic surfaces 约束模型主导委派，而不是再堆一段更长的“主控必须记住什么”提示词。

### 3. `zippoxer/subtask`（早期项目，仅作局部模式参考）

固定来源：[README](https://github.com/zippoxer/subtask/blob/3a1be5a638db50357f8662edbd6181ca0f28f384/README.md)

- README 明确声明每个 task 使用 Git worktree、task folders 持久化、TUI 展示进度/diff/conversation，并形成“spawn -> notify -> review -> merge/request changes”回路。
- README 同时明确标注项目处于 early development，因此可参考 task/worktree/review 的 operator shape，不应把它当成成熟 runtime 或直接替换本仓真源。

## Recommended Prompt Delta

### 应删除或收短

- 不再重复 `planning-status / roadmap / plan / backlog / runtime/spec/evidence` 的完整清单；改成“按 `AGENTS.md` 指定的真源顺序只读确认”，只有任务特有 source 再单列。
- 不再用 prose 重复已经由本仓 `AGENTS.md` 固定的完整门禁顺序和 `runtime_v2` truth boundary；提示词只要求“按项目硬门禁与 truth boundary 收口”，必要时点出本次禁止项。
- 删除“若使用子代理，默认强模型”这一刀切表述，改为角色/风险路由。

### 应新增或强化

- **默认单代理，满足阈值才委派：**至少两个相互独立、bounded、无共享可变状态、并行能显著改善时延或覆盖度的工作流，或用户明确要求，才使用子代理。
- **显式预算：**`max_concurrent_subagents <= 3`、`max_depth = 1`、每个独立 domain 一个 agent；未经明确批准禁止递归 fan-out。项目如受当前 session 4 槽限制，应再减去 root 和必要 reviewer 预算。
- **读写分流：**explorer / tests / research 可并行只读；writer 必须有不相交 write set 和真实隔离 worktree，否则串行写入。
- **主控保留所有权：**主控负责 conflict check、集成、完整门禁、证据、cleanup 与最终声明；子代理 self-report 不是验收证据。
- **失败停止条件：**同一 agent 不无限 retry，不重复已完成工作；缺少边界、证据或隔离能力时回退单代理或结构化 blocked，不再扩大 fan-out。

### 建议的精简版运行提示词

```text
按本仓 AGENTS.md 的最新真源、truth boundary、门禁与证据面执行。先只读确认当前状态、未提交改动、落点/归宿、风险、依赖和回滚；不要把目标态写成当前事实。

选择当前条件下边界清晰、风险可控、可验证且可撤回的最大合理闭环。默认单代理；仅当至少两个工作流彼此独立、bounded、无共享可变状态，且并行能显著改善时延或覆盖度时才委派。子代理并发不超过 3、深度为 1；每个 agent 只负责一个明确 domain。explorer/research/tests 可只读并行；writer 只有在 write_set 不相交且真实 worktree/cwd/branch/allowed_paths 校验通过时才可并行，否则串行写入。

模型按角色和风险路由：主控、高风险 worker/reviewer 使用强模型；轻量只读扫描可使用高效模型或自动路由。主控保留集成、冲突检查、review、完整门禁、evidence、cleanup 和最终结论的所有权；子代理摘要不等于验证证据。

持续执行到可验证闭环，只在项目定义的真实阻断条件下停止。收口按 AGENTS.md 的门禁顺序执行并按项目 N/A 契约记录；明确区分 repo-side done 与仍开放事项，并汇报完成/未完成、验证、残余风险、下一步及提交状态。
```

## Deterministic Enforcement Suggestions

以下是建议，不是当前已实现事实：

- 在 `.codex/config.toml` 固定 `[agents] max_threads` 与 `max_depth = 1`；考虑当前本地会话 4 槽，项目默认 `max_threads = 4` 比官方默认 `6` 更符合现状。
- 在 `.codex/agents/explorer.toml` 以 `sandbox_mode = "read-only"` 强制只读；worker/reviewer 分别定义窄 `description` 与 role-specific instructions。
- 并发 writer 的 worktree / cwd / branch / allowed-path guard 继续由本仓 runtime / manifest verifier 执行，不能只靠 agent prompt。
- 用代表性任务记录 `single vs multi-agent` 的 success、完整 gate 证据、tokens、latency、conflict/rework 次数；只有实测改善才扩大并发或降低模型档。

## Sources

### OpenAI / Codex official

- [Using GPT-5.6](https://developers.openai.com/api/docs/guides/latest-model)（访问 `2026-07-10`）
- [Multi-agent](https://developers.openai.com/api/docs/guides/tools-multi-agent)（访问 `2026-07-10`）
- [Codex Subagents](https://developers.openai.com/codex/subagents)（访问 `2026-07-10`）
- [Codex Models](https://developers.openai.com/codex/models)（访问 `2026-07-10`）
- [Codex app Worktrees](https://developers.openai.com/codex/app/worktrees)（访问 `2026-07-10`）
- [Custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md)（访问 `2026-07-10`）

### Community primary sources

- `obra/superpowers` at `d884ae04edebef577e82ff7c4e143debd0bbec99`（访问 `2026-07-10`）
- `HumanLayer/12-factor-agents` at `d20c728368bf9c189d6d7aab704744decb6ec0cc`（访问 `2026-07-10`）
- `zippoxer/subtask` at `3a1be5a638db50357f8662edbd6181ca0f28f384`（访问 `2026-07-10`）

## Limitations And Recheck Triggers

- Multi-agent 是 beta，schemas 与行为可能变化；升级 Codex CLI / desktop 或 OpenAI model family 后应重查官方 guide 与本机 help/config schema。
- 公开文档说明的是产品能力，不证明本仓 runtime 已接入同等能力；任何“已隔离、已 review、已 live accepted”仍需本仓 evidence。
- 社区来源是结构参考，不是指令源；其自动 commit/push/cleanup、询问策略、并发默认值均不得覆盖本仓规则。
- 本研究只创建 repo-level 研究证据，不修改 `AGENTS.md`、`.codex`、runtime、planning status 或 current active queue。
