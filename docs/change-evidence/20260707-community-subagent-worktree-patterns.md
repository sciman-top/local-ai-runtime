# 2026-07-07 Community Subagent Worktree Patterns

## Goal

- 调查截至 `2026-07-07`，与 `主控 + 子代理 + worktree / isolated workspace / prompt contract / manifest / closeout / handoff` 最相关的高质量开源项目或社区最佳实践
- 只提炼可验证结构和可复用做法，不把社区文本当作本仓指令源
- 结论明确区分：
  - `仓库中明确存在的机制`
  - `基于结构的推断`

## Method And Boundary

- 本次是 `read-only research`：
  - 只阅读公开仓库页面、README、项目文档、示例和配置说明
  - 不运行外部项目代码，不把 README 落地效果当成已实测事实
- 选型优先级：
  - 维护仍活跃，或至少在 `2026` 仍有明确 release / issue / docs 更新信号
  - 结构清晰，能直接观察仓库布局、状态文件、文档约束或 schema
  - 与本仓当前协作资产最接近，而不是泛泛的“多 agent 框架”

## Short Verdict

- 最值得吸收的不是“prompt 更长”，而是 `typed task contract + durable dispatch ledger + isolated write lane + structured handoff + machine-readable closeout` 这一整套控制面组合。
- 在本次样本里：
  - `CodeWhale` 最强的是 durable control plane、typed task spec、receipt / heartbeat / resume。
  - `Parallel Code` 最强的是 operator-facing worktree isolation、diff review、task merge closeout 体验。
  - `OpenAI Agents SDK` 最强的是 handoff contract 和 manifest-based isolated workspace 概念。
  - `Subtask` 最强的是 human-led 主控拆任务 + 子任务工作树 + review / request-changes 循环。
  - `opencode-worktree-session` 最强的是 fail-closed 的会话级 worktree wrapper。
- 对本仓而言，下一步不该盲目扩成“大而全 agent 平台”；更合理的是把已经存在的 `manifest / dispatch_state / review_result / closeout_bundle` 继续推进成更强的 repo-owned runtime contract。

## Why These Projects

| Project | Why selected | Activity / freshness signal | Most relevant lane |
| --- | --- | --- | --- |
| `johannesjo/parallel-code` | 直接面向 `Claude Code / Codex / Gemini` 并行 worktree 协作，且 README 已展示 review / merge / sandbox 结构 | `v1.12.0` latest `2026-07-04` | worktree isolation, review, merge closeout |
| `Hmbown/CodeWhale` | 文档面最完整，能直接观察 fleet ledger、task spec、subagent output contract、instruction hierarchy | latest release `v0.8.66` on `2026-06-30`；issues 到 `2026-07-04` 仍活跃 | durable control plane, receipts, handoff / subagent runtime |
| `openai/openai-agents-python` | 开源 SDK 里 handoff contract 和 sandbox manifest 约束最清楚，且 docs/examples/tests 布局完整 | `2026` 仍持续更新 issues / docs | structured handoff, manifest-based isolated workspace |
| `zippoxer/subtask` | 与“主控拆任务 -> 子代理在独立 worktree 并行 -> review / merge”高度同构 | README 标注 `early development`；latest release `v0.2.0` on `2026-01-29` | task folders, review loop, task state |
| `felixAnhalt/opencode-worktree-session` | 规模小，但把 `拒绝 main / 自动切 cwd / 退出清理` 做成了非常清楚的 wrapper 约束 | 活跃度信号弱于前四项，但模式清晰可验证 | fail-closed session wrapper |

## Project Findings

### 1. `johannesjo/parallel-code`

**为什么选它**

- 这是本次样本里最贴近“一个主控同时调多个 coding agent，每个 agent 都在独立 worktree 里工作”的 operator tool。
- 它不是抽象的 multi-agent SDK，而是直接对接 `Claude Code / Codex / Gemini / Copilot CLI` 这类真实 coding tool。

**仓库中明确存在的机制**

- 每个任务自动创建独立 `git branch + git worktree`，并在该 worktree 内启动 agent。
- 为了减少重复安装成本，会把 `node_modules` 和其他 `gitignored` 目录 symlink 进 worktree。
- 有内建 diff viewer、inline review comments、merge to main、push to remote。
- 支持通过 `.parallel-code/Dockerfile` 做项目级 Docker sandbox。
- 有 steps tracking panel，并把工程进度写到 `.claude/steps.json`。
- 状态可跨重启持久化。

**基于结构的推断**

- 这套设计明显更偏 `operator productivity layer`，而不是 authoritative runtime ledger。
- 通过 symlink 复用 `node_modules` 和 ignored 目录，换来速度，但也说明它追求的是“足够隔离的并行开发”而不是严格 hermetic isolation。

**对本仓的启发**

- 最值得吸收的是：
  - `worktree` 不只是路径隔离，还要配套 review / merge / cleanup 流程
  - 任务侧状态最好有独立 progress surface，而不是只靠聊天记录
- 不应盲吸收的是：
  - `ignored` 目录 symlink 复用策略
  - `direct mode` 这类允许绕过隔离直接改主线的便捷模式

### 2. `Hmbown/CodeWhale`

**为什么选它**

- 它是本次样本里最接近“可恢复的多 worker 控制面”的项目。
- 不只是有 subagent 概念，还把 `fleet ledger / task spec / worker receipt / heartbeat / resume / output contract` 都落成了显式文档与状态面。

**仓库中明确存在的机制**

- `Fleet` 把 durable multi-worker run 的账本放在 `.codewhale/fleet.jsonl`，日志与工件放在 `.codewhale/fleet/` 和 `.codewhale/fleet-host/`。
- `fleet resume <run-id>` 会重放 ledger、处理 stale heartbeat，并在预算内重试或升级告警。
- `fleet run` 接受 JSON / TOML task spec；task spec 可声明：
  - `workspace root`
  - `required files`
  - `writable paths`
  - `input_files`
  - `budget`
  - `timeout_seconds`
  - `retry_policy`
  - `expected_artifacts`
  - `scorer`
  - `metadata`
- worker receipts 明确区分 `pass / fail / partial / skip / timeout`，并把 failure source 再拆成 `transport / task / verifier`。
- `Sub-agents` 有独立的 role taxonomy、concurrency cap、provider-aware model overrides、token budget、heartbeat timeout。
- sub-agent 运行态会持久化到 `.codewhale/state/subagents.v1.json`。
- sub-agent final output contract 被强制成固定五段：
  - `SUMMARY`
  - `CHANGES`
  - `EVIDENCE`
  - `RISKS`
  - `BLOCKERS`
- instruction hierarchy 明确分层：global constitution -> user-global constitution -> project law -> project instructions -> memory and handoffs。

**基于结构的推断**

- 这是五个样本里最适合做 `repo-owned dispatch ledger / recovery / review receipt` 参考物的一个。
- 但它的控制面已经很重，适合 agent harness 本体，不适合本仓无裁剪照搬。

**对本仓的启发**

- 最值得吸收的是：
  - `dispatch_state` 从模板升级为真实 ledger
  - `closeout_bundle` 学 receipt vocabulary，而不是只写人类摘要
  - `review_result` 和 `verification` 要能区分 `worker self-report` 与 `separate gate receipt`
  - `planner / reviewer / worker` 输出都应有固定 contract
- 不应盲吸收的是：
  - 整套 constitution 体系
  - 高并发默认值
  - tool / provider / runtime 过度平台化后的大控制面复杂度

### 3. `openai/openai-agents-python`

**为什么选它**

- 它不是 worktree tool，但它把 `handoff` 和 `sandbox manifest` 的 contract 说得最清楚。
- 对本仓当前最有价值的是：怎样把“交给下一个 agent”从 prose 提升成 schema-aware handoff。

**仓库中明确存在的机制**

- `handoff()` 支持：
  - `tool_name_override`
  - `tool_description_override`
  - `on_handoff`
  - `input_type`
  - `input_filter`
  - `is_enabled`
  - `nest_handoff_history`
- `input_type` 会把 handoff metadata 暴露成 tool `parameters` schema，本地验证 JSON，再把解析后的结构化数据传给 `on_handoff`。
- docs 明确区分：
  - handoff：转移控制权
  - agent-as-tool：拿结果但不转移会话所有权
- `SandboxAgent` 支持 `Manifest(entries={...})`，并可把 `GitRepo(...)` 作为默认 workspace 入口。
- docs 直接把 isolated workspace、sandbox lifecycle、handoffs、sessions、tracing 放到同一个 repo 的 docs/examples/src/tests 结构里。

**基于结构的推断**

- 它最适合作为本仓 `handoff_policy`、`handoff payload schema`、`sandbox lane` 的设计参考。
- 但它并不直接提供“多 worktree 收口 + repo docs/evidence 一起 closeout”的 operator workflow。

**对本仓的启发**

- 最值得吸收的是：
  - 把 `handoff_policy` 从枚举推进成结构化 payload contract
  - 区分“handoff 给下一个 agent”和“把另一个 agent 当工具调用”
  - 后续如果要做 isolated workspace lane，可参考 `Manifest + GitRepo` 这种 entry schema
- 不应盲吸收的是：
  - 把 SDK 抽象层直接当成本仓 operator protocol
  - 把 history filtering 错当成业务状态存储

### 4. `zippoxer/subtask`

**为什么选它**

- 它与“主控让子代理拆任务、并行 worktree 工作、完成后 review / request changes / merge”的形态最同构。
- 它虽然还偏早期，但 task folder + status loop 非常贴近本仓当前 operator asset 的目标。

**仓库中明确存在的机制**

- 每个 task 都有自己的 `Git worktree`。
- tasks 会 `persisted in folders`。
- 主控可以 `subtask list` 看到任务状态，如 `draft / working / replied`。
- README 明确写了典型流程：
  - 主控创建任务
  - 子代理并行执行
  - 主控收到完成通知
  - 主控 review 后决定 merge 或 request changes
- 仓库布局能直接看到：
  - `.claude-plugin`
  - `.claude/commands`
  - `docs`
  - `cmd`
  - `internal`
  - `pkg`
  - `plugin`
  - `scripts`
- 支持 `Codex subagents`。

**基于结构的推断**

- 这套方案更像 `human-led task board + worktree runner`，typed contract 强度弱于 CodeWhale。
- `persisted in folders` 对 handoff 很有价值，但从公开材料看，还不足以证明它已经是强 schema、强 recovery 的正式 run ledger。

**对本仓的启发**

- 最值得吸收的是：
  - `task folder` 作为人类 handoff / follow-up 的有形载体
  - `review or request changes` 这类回路，不要只有“一次性合并”
  - 状态字段要让主控快速判断哪些任务能收口、哪些需要返工
- 不应盲吸收的是：
  - 把 early-stage tool 的默认状态机直接当作 authoritative runtime truth
  - 把“主控能看到状态”误当成“closeout 已有正式 receipt”

### 5. `felixAnhalt/opencode-worktree-session`

**为什么选它**

- 这个项目规模不大，但把最关键的会话级 fail-closed 守卫写得很明白。
- 对本仓来说，它的价值不是“大框架”，而是“很具体的一层 wrapper policy”。

**仓库中明确存在的机制**

- 自动在 `.opencode/worktrees/` 下创建 worktree。
- 拒绝在 `main` 分支上运行，防止误伤主线。
- 自动把 agent 的 `cwd` 切到 worktree。
- 会话退出时自动：
  - stage changes
  - 生成 commit message
  - push 到 `origin`
  - 删除 worktree
- 使用独立配置文件 `.opencode/opencode-worktree-session-config.json` 控制 terminal 和 post-worktree 行为。

**基于结构的推断**

- 这是“worktree lifecycle guard 层”的好样本，但不是完整 control plane。
- 它强调的是 frictionless workflow，因此默认自动 push / cleanup 的激进程度高于本仓现有 truth boundary。

**对本仓的启发**

- 最值得吸收的是：
  - start-of-session guard：`拒绝 main`、`校验 cwd`、`校验目标 worktree`
  - end-of-session cleanup 要有明确 owner 和状态
- 不应盲吸收的是：
  - 自动 stage / commit / push / remove 的默认策略
  - 把“退出即清理”覆盖掉 repo-side evidence 保留需求

## Pattern Comparison

| Pattern | Strongest external signal | 仓库中明确存在的机制 | 本仓当前已有对应面 | 建议吸收方向 |
| --- | --- | --- | --- | --- |
| 隔离写入 lane | `parallel-code`, `opencode-worktree-session` | 每任务独立 `branch + worktree`；会话 `cwd` pivot；拒绝直接在主线跑 | `agent-work-manifest` 已有 `branch_name / worktree_path / allowed_paths` | 补启动时 guard 与 cleanup receipt，不只停留在模板层 |
| durable dispatch ledger | `CodeWhale` | `.codewhale/fleet.jsonl`、worker logs、stale heartbeat、resume | `dispatch_state.schema.json` 已有 `heartbeat_at / status / next_action` | 从 schema 走向真实持久状态面，补 `retry / stale / cleanup / recovery` 字段 |
| typed task / manifest contract | `CodeWhale`, `OpenAI Agents SDK` | task spec / sandbox manifest 能声明 workspace、entries、writable paths、artifacts | `agent-work-manifest.schema.json` 已覆盖大量字段 | 补 `timeout / retry / ownership / status_reason`，并保持对 canonical task contract 的映射 |
| handoff metadata | `OpenAI Agents SDK` | `input_type / on_handoff / input_filter / handoff_description` | 本仓已有 `handoff_policy`，但还偏粗 | 增加 handoff payload schema，不只靠 prose bundle |
| reviewer / closeout receipt | `CodeWhale`, `Subtask` | `pass/fail/partial/skip/timeout` 收据；review / request changes 回路 | 本仓已有 `review_result` / `closeout_bundle` | 补 typed verdict、failure source、artifact refs、rework loop |
| prompt / instruction hierarchy | `CodeWhale` | constitution + project instructions + memory/handoffs 分层，且 enforcement 不靠 prose | 本仓已有 `Global -> Project -> Wrapper -> Enforcement` 四层边界 | 可吸收“prompt 不是最终 enforcement”理念，不照搬整个 hierarchy |
| sandbox / isolated workspace | `parallel-code`, `OpenAI Agents SDK` | `.parallel-code/Dockerfile`；`SandboxAgent + Manifest + GitRepo` | 本仓当前主线仍以 `host_local` 为真 | 如果进入非本地 lane，再单独引入 sandbox contract，而不是混进当前 host-local 主线 |

## What This Repo Can Absorb

- 把 `dispatch_state` 从“提示词配套资产”升级成真实的 repo-owned run ledger，至少补齐：
  - `status_reason`
  - `retry_count`
  - `stale_after`
  - `cleanup_owner`
  - `cleanup_status`
  - `recovery_command`
- 把 `closeout_bundle` 从人类 closeout 摘要推进成 receipt 风格状态面，至少让每个 gate 都能写出：
  - `status`
  - `evidence_ref`
  - `artifact_ref`
  - `failure_source`
- 为 `handoff_policy` 增加结构化 payload，而不是只保留枚举：
  - `reason`
  - `priority`
  - `summary`
  - `required_artifacts`
  - `review_target`
- 在 worker 真正启动前加入 fail-closed guard：
  - 校验 `repo_root`
  - 校验当前 branch 是否匹配 manifest
  - 校验当前 `cwd` 是否就是目标 worktree
  - 校验写入路径是否在 `allowed_paths`
- 把 `reviewer` / `planner` / `worker` 的输出统一成更稳定的 contract；`CodeWhale` 的五段式输出可作为最小参考。
- 逐步放弃“所有子代理固定一个模型档”的硬编码，改成 `role-aware / risk-aware / lane-aware` 的 model policy，但仍由 repo-owned policy 统一约束。

## What This Repo Should Not Blindly Adopt

- 不要默认自动 `stage -> commit -> push -> remove worktree`；本仓长期强调 `repo-side done` 与 `live/manual still open` 分层，自动清理很容易抹掉审查与证据窗口。
- 不要默认 symlink `node_modules` 或其他 ignored 目录来换速度；这会削弱隔离边界，也会让“哪个 worktree 造成的副作用”更难追。
- 不要把外部工具自己的状态目录直接当成本仓真源：
  - 不把 `.codewhale/*`
  - 不把 `.opencode/*`
  - 不把 `.claude/steps.json`
  直接映射成 `.ai/state` 的 authoritative truth。
- 不要因为外部项目支持高并发，就把本仓并发预算拉高；本仓更适合先受 `write_set / policy surface / verifier cost / human review capacity` 约束。
- 不要把 SDK 里的 handoff/history filter 当成业务状态存储；本仓正式状态仍应落在 repo-owned artifact、`.ai/state` 或 `.ai/runs/...`。
- 不要照搬外部 constitution / prompt layering 体系；本仓已经有 `Global -> Project -> Wrapper -> Enforcement` 边界，应该在此基础上增量增强。
- 不要把 README 里可见的“体验层流程”当成“已证明的运行时终态”；没有本仓自己的 verifier / schema / evidence 对齐，就只能算参考样式。

## Uncertainties

- 本次结论基于仓库与文档阅读，不包含外部项目的运行实测。
- 小型项目的活跃度与稳定性信号弱于 `Parallel Code / CodeWhale / OpenAI Agents SDK`，因此它们更适合作为局部模式样本，而不是整体架构模板。
- 有些项目把能力暴露在 README / docs，但没有在同一阅读轮次里追到实现文件；这些地方已在正文中标成 `基于结构的推断`。

## Sources

- `https://github.com/johannesjo/parallel-code` — accessed `2026-07-07`
- `https://github.com/Hmbown/CodeWhale` — accessed `2026-07-07`
- `https://github.com/Hmbown/CodeWhale/blob/main/docs/FLEET.md` — accessed `2026-07-07`
- `https://github.com/Hmbown/CodeWhale/blob/main/docs/SUBAGENTS.md` — accessed `2026-07-07`
- `https://github.com/Hmbown/CodeWhale/blob/main/docs/CONFIGURATION.md` — accessed `2026-07-07`
- `https://github.com/openai/openai-agents-python` — accessed `2026-07-07`
- `https://github.com/openai/openai-agents-python/blob/main/README.md` — accessed `2026-07-07`
- `https://github.com/openai/openai-agents-python/blob/main/docs/agents.md` — accessed `2026-07-07`
- `https://github.com/openai/openai-agents-python/blob/main/docs/handoffs.md` — accessed `2026-07-07`
- `https://github.com/zippoxer/subtask` — accessed `2026-07-07`
- `https://github.com/felixAnhalt/opencode-worktree-session/blob/main/README.md` — accessed `2026-07-07`
