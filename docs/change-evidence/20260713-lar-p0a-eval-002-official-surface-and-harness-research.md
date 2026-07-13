# 2026-07-13 LAR-P0A-EVAL-002 Official Surface And Harness Research

## Result

本笔记只提供 `LAR-P0A-EVAL-002` 的一手资料依据。它是
`reference_only / non_normative`，不执行 comparative trial，不资格化任何
Codex capability，不判定 terminal evaluation decision，不创建 Baseline Approval、
Truth Reset、Batch claim 或 live evidence，也不改变冻结的 v3.23 candidate 语义。

截至 2026-07-13，可由一手来源支持的结论是：

1. `gpt-5.6-sol` 是 OpenAI 当前公开的 GPT-5.6 旗舰能力型号；更强模型和更精简的
   prompt/tool inventory 值得优先评测，但官方资料同样要求在代表性 workload 上比较
   质量、token、延迟与成本，不能据此推导 gates、evidence、authority 或 recovery 已
   被模型替代。[O1]
2. Codex CLI、App Server、SDK、ChatGPT desktop app managed Worktree 和
   Scheduled tasks/Automations 是不同的公开产品面。它们的协议、生命周期、sandbox、
   effect 和 recovery 边界不同；v3.23 将其拆成独立 capability generation/Q0，而不是
   一个 `CodexPlatformAdapter` 配置开关，符合官方公开边界。[O2][O3][O4][O5][O6]
3. “Superpowers、Trellis、Hermes 已被高智能模型普遍淘汰”没有一手证据。它们解决的
   分别是方法论纪律、repo 内持久化工程框架、长期/远程/消息/定时 agent runtime，
   不等同于模型推理能力。[S1][T1][H1]
4. `grill-with-docs` 不是已证实“比 `grill-me` 更好”的同功能升级版。两者运行相同的
   逐题访谈；前者额外写 `CONTEXT.md` 和少量 ADR，后者明确不写 workspace。选择取决于
   是否需要持久化术语/决策，而不是通用质量排序。[G1][G2][G3][G4]
5. 对当前 sealed local corpus，完整 Trellis、Hermes、`grill-me` 和
   `grill-with-docs` 均不应进入 core lane；完整 Superpowers 也不满足无额外人工决定、
   无额外 workflow side effect 的 conditional lane 约束。它们的未来价值应按任务族
   条件资格化，不能成为 Native 快路径或 deterministic Batch 的默认控制面。

## Scope And Method

- 研究对象：OpenAI GPT-5.6 与 Codex 五个 surface，以及
  `obra/superpowers`、`mindfold-ai/Trellis`、`NousResearch/hermes-agent`、
  `mattpocock/skills` 中的 `grill-me` / `grill-with-docs`。
- 资料边界：只使用 OpenAI 官方文档/官方仓库和各第三方项目原始仓库、固定 commit
  文档、官方 release/tag 页面。
- 访问日期：来源登记表中的每一项均于 `2026-07-13` 访问。
- 执行边界：未安装或运行第三方工具，未运行 Codex live/effectful probe，未修改
  provider/auth/config、live state 或治理真源。
- OpenAI Codex manual helper 因代理响应缺少 `x-content-sha256` 完整性响应头而未被
  采用；OpenAI 事实改由官方 Docs MCP 获取。该失败只限制来源路径，不构成 capability
  failure 或本机 surface qualification 结果。
- 上游 README 中的质量、效率、自学习等表述只作为“上游声明的产品能力”，不作为
  独立 benchmark 或本仓成功证据。

名称存在以下 bounded uncertainty：

- 本文把 `Trellis` 映射为 `mindfold-ai/Trellis`，因为它与 AI coding engineering
  framework 语境及本仓既有研究一致；同名项目很多，若建议者指其他 URL，结论必须
  重做。
- 本文把 `Hermes` 映射为 `NousResearch/hermes-agent`，因为用户讨论的是 agent、
  gateway、cron、VPS/remote runtime；名称本身并不唯一。
- “harness/herness”被视为通用类别，不映射为另一个未给 URL 的具体产品。

## OpenAI Model Finding

OpenAI 的 `Using GPT-5.6` 页面明确给出：

- `gpt-5.6` alias 路由到 `gpt-5.6-sol`；`sol` 用于 flagship capability，`terra`
  面向较低价格的强性能，`luna` 面向高吞吐效率。[O1]
- GPT-5.6 支持 `none`、`low`、`medium`、`high`、`xhigh`、`max` reasoning effort；
  官方建议保持原 effort 作为基线，再比较更低一级，并按实际 workload 找质量、延迟、
  token 与成本的平衡，而不是默认最高 effort。[O1]
- 官方提示精简重复 instructions、examples 和不相关 tools 可能改善质量与 token
  效率，但明确把其内部样本结果称为 directional，并要求在自己的代表性任务上逐组
  删除、重新评测。[O1]
- 官方仍要求明确 autonomy、approval boundaries、hard constraints 和 success
  criteria；模型更能理解意图，不等于可以删除安全或 effect ownership 边界。[O1]

因此，当前 `gpt-5.6-sol/high` 适合作为 sealed evaluation 的固定实验条件，但不能由
型号说明直接推出：

- `high` 是全局最优 effort；
- Superpowers/Trellis/Hermes 已无价值；
- Native 输出天然满足本仓 gate/evidence/rollback contract；
- Batch 可以从全局 `capacity=1` 无验证地升级为多 writer 高速并发。

当前 contract 的做法更接近官方建议：固定 snapshot、task family、model/effort 和
tool inventory，报告 success、质量、wall time、token/成本与人工，并让质量、安全、
证据 floor 优先于效率收益。

## Codex Surface Boundaries

| Surface | 官方可证实的公开能力 | 对 v3.23 的保守推论 | 当前研究结论 |
| --- | --- | --- | --- |
| CLI / `codex exec` | 面向 pipeline、CI、scheduled jobs 和 shell composition；默认 read-only sandbox，可显式选 workspace-write/full access；提供 JSONL events、JSON Schema final output、session resume 和 Git-repo guard。[O2] | 最薄且最接近当前 core corpus 的 Native execution interface。JSONL/structured output 可作为 adapter input，但不自动等价于本仓不可变 evidence、authority ledger、gate order 或可复算 rollback receipt。 | `applicable_candidate`，仍须按 sealed trial 独立资格化。 |
| App Server | 为富客户端提供 auth、conversation history、approvals 和 streamed agent events；使用双向 JSON-RPC，stdio 为默认 JSONL transport；stable 与 `experimentalApi` 明确分开；thread/turn/review/command/approval 等拥有独立 lifecycle。[O3] | 适合作为深度 UI/client integration adapter，不应被 CLI 成功结果资格化。schema 与 experimental method 会随 Codex version 变化，必须锁定 identity 并做 client lifecycle、sandbox、effect、error/recovery Q0。 | `independent_candidate`，不由 CLI 继承。 |
| Codex SDK | TypeScript SDK 比 non-interactive mode 更灵活，并明确支持 thread start/resume；Python SDK 控制本地 App Server，当前公开为 beta，published build 携带 pinned Codex CLI runtime dependency，公开页证明 `thread_start`、同一 thread 的后续 `run` 与 sandbox presets，但未由 O4 证明跨会话 resume。[O4] | SDK 不是“与当前 CLI 完全相同的薄包装”。package/runtime pinning、请求/响应投影和错误语义必须作为独立 generation；为了复用本机 CLI 而覆写 pinned binary 也需要显式资格化。 | `independent_candidate`，无 package/runtime evidence 时为 inconclusive。 |
| Managed Worktree | ChatGPT desktop app 基于 Git worktree 创建 task-dedicated、通常 disposable 的 managed worktree；起点是所选 branch 的 `HEAD`，可带入未提交变更，默认 detached HEAD；App 管理 cleanup、snapshot 和 restore，最近 worktree 保留数量可配置。[O5] | 这是一套 App-owned isolation/lifecycle，不只是调用 `git worktree add`。创建 identity、dirty-state carry-in、cleanup、snapshot/restore、branch conflict 与 effect boundary 必须单独 Q0，不能由手工 disposable worktree trial 继承。 | `independent_candidate`，未授权创建 App task 时保持 inconclusive。 |
| Scheduled tasks / Automations | 可后台周期执行，使用 project directory 或 isolated worktree；独立 run 可启动新 task，也可回到已有 task 延续 context；本地项目要求机器开机且 App 运行；无人值守使用默认 sandbox，组织允许时使用 `approval_policy="never"`，官方建议最小权限并先手工测试 prompt。[O6] | 它是 scheduler/effect surface，不只是 CLI timer。trigger、unattended sandbox、local-vs-worktree 写入、cancellation、cleanup、external plugin/effect 和 evidence projection 均需独立资格化；未经授权不应为本评测创建 schedule。 | `independent_candidate`，当前只读研究不授予资格。 |

五个 surface 可以共用模型与部分配置，但官方文档没有提供“一个 surface 通过即可证明
其他 surface 行为相同”的保证。相反，公开文档暴露了不同协议、runtime dependency、
lifecycle 和 effect ownership。v3.23 的 `no_cross_surface_inheritance` 与以下 generation
trigger 是必要的，而不是过度治理：

- model 或 reasoning effort 改变；
- tool inventory、sandbox 或 permission 改变；
- SDK package/pinned runtime 或 App Server stable/experimental schema 行为改变；
- managed Worktree carry-in、cleanup、snapshot/restore 行为改变；
- Automation trigger、unattended sandbox、worktree 或 external effect 行为改变。

## Third-Party Harness Findings

### Superpowers (`obra/superpowers`)

上游 README 把 Superpowers 定义为“complete software development methodology”，不是
一个窄执行器。公开流程包括 brainstorming、用户 sign-off、worktree、详细计划、
subagent-driven development、TDD、两阶段 review 和 branch closeout，并明确写着
“Mandatory workflows, not suggestions”。上游也提供 Codex App/CLI plugin 安装路径。
[S1]

这说明它没有被 Codex 原生能力从逻辑上“替代”：它提供的是强制流程策略。然而，完整
套件会加入额外的人机 checkpoint、worktree、subagent 和 review authority。对 sealed
corpus：

- read-only truth audit 不需要 design/implementation/branch workflow；完整方法论没有
  同等对照价值；
- 两个 bounded regression-test family 已固定输入、allowed paths、oracle、gate 和
  rollback；完整流程要求额外 sign-off/plan/worktree，违反 conditional lane 的“无新增
  human decision / non-disposable side effect”边界；
- 单独抽取 verification/debugging/review skill 可在未来作为 task-local aid 评测，但
  不能把“某个 skill 有用”推广为“Superpowers 控制面应成为 adapter”。

保守适用性：`conditional_only`；当前 sealed corpus 的“完整 Superpowers workflow”应
预声明 `not_applicable`。若未来只测一个固定 skill，需固定其 exact identity、invocation
和 workflow trace，且不得改变 selector、authority、gate 或人工定义。

维护事实只用于反驳“项目已消失”：仓库在访问时未归档，最新 release `v6.1.1` 发布于
2026-07-02。[S2] 这不证明本仓净收益。

### Trellis (`mindfold-ai/Trellis`)

上游把 Trellis 定义为 repo 内 AI coding engineering framework：

- `.trellis/spec/` 自动注入规范；
- `.trellis/tasks/` 保存 PRD、implementation/review context 和 task status；
- `.trellis/workspace/` 保存 journal/project memory；
- Plan -> Implement -> Verify -> Finish 使用 auto-invoked skills 与 research/implement/
  check subagents，Finish 会把学习写回 spec。[T1]

其官方 platform map 显示 Codex 集成还会使用 `.codex/`、`.agents/skills/`、
`.codex/agents/` 和 `.codex/hooks*`。[T2] 这些路径与本仓既有 AGENTS、planning status、
machine work items、selector、evidence 和 `.ai` runtime state 形成明显的第二真源/第二
workflow risk。Trellis 代码许可证为 AGPL-3.0；任何复制、派生或嵌入 runtime 的方案还
需要独立 license review。[T3]

保守适用性：当前 core corpus 为 `not_applicable`。允许 Trellis 初始化或写 journal/spec
会违反 sealed allowed paths 与 `second_control_plane_prohibited`；只抽取一个不落状态的
通用检查提示又不足以代表 Trellis 框架。只有未来出现“多个 coding platforms 共用
repo-owned memory/spec”的明确任务族，才值得在隔离仓做单独 pilot。

访问时仓库未归档，存在 `v0.6.6` tag，不能称为已被模型淘汰；活跃度同样不证明质量、
稳定性或本仓收益。[T4]

### Hermes Agent (`NousResearch/hermes-agent`)

上游 README 描述的是独立长期 agent runtime，而不是 coding skill：persistent memory、
self-created/improving skills（上游自述）、CLI/TUI、Telegram/Discord/Slack/WhatsApp/
Signal gateway、cron scheduling、isolated subagents，以及 local/Docker/SSH/Singularity/
Modal/Daytona terminal backends；官方索引还列出 command approval、DM pairing 和
container isolation。[H1]

这类能力不会因为 coding model 更强而自动消失；它们属于长生命周期、remote execution、
credentials、message delivery 和 external effects。当前 EVAL task families 没有 remote、
VPS、cron 或 gateway requirement，contract 也明确规定本地 corpus 记录
`not_applicable`，不能记录“已替代”。

保守适用性：当前为 `not_applicable`，继续作为 legacy/reference input。未来若引入
remote runner、message gateway 或 scheduled delivery，应按新 task family、effect
owner、credential boundary、recovery 和 capability generation 独立资格化，而不是让
Hermes 接管 v3.23 control plane。

访问时仓库未归档，最新 release `v2026.7.7.2` 发布于 2026-07-08。[H2]

### `grill-me` And `grill-with-docs` (`mattpocock/skills`)

固定 skill frontmatter 均声明 `disable-model-invocation: true`；在遵循该字段的 host 中，
它们应由用户显式调用，而不是成为 agent 自动 mandatory step。[G1][G2]

两者的共同点是针对 plan/design 逐题访谈，每次等待用户回答；能从 codebase 发现的事实
应由 agent 自行读取。区别是：

| Skill | 一手来源中的状态行为 | 合适场景 | 不适合场景 |
| --- | --- | --- | --- |
| `grill-me` | stateless，不写 workspace；结果留在 conversation。[G3] | 高歧义且只需澄清，不希望新增 repo artifact。 | sealed input、明确小修、低人工无人值守 Batch。 |
| `grill-with-docs` | stateful；术语写入 `CONTEXT.md`，少量 hard-to-reverse decision 写入 `docs/adr/`。[G4] | 领域语言未收敛，且明确授权持久化 glossary/ADR。 | allowed paths 不含这些文档的 task、已冻结 contract、要求零额外人工的 Batch。 |

因此“`grill-with-docs` 比 `grill-me` 好”只能改写为条件判断：需要 durable glossary/ADR
时前者功能更完整；不需要 repo 写入或希望减少 effect 时后者更薄。两者都不提供 gate、
evidence、rollback、scheduler 或 crash recovery，也不应加入本次 sealed core variants。

访问时上游仓库未归档，最新 release `v1.1.0` 发布于 2026-07-08。[G5]

## Applicability Decision Support

本研究给 `LAR-P0A-EVAL-002` 的 non-terminal support 如下：

| Object | Current sealed corpus | Reason |
| --- | --- | --- |
| `gpt-5.6-sol/high` | fixed experimental condition | 官方支持该 model/effort；不宣称全局最优。 |
| `thin_codex_native` via CLI | core applicable | CLI 是当前最薄的公开 non-interactive execution surface。 |
| `native_plus_key_gates` | core applicable | 官方模型建议保留明确边界与实测；本仓 gates/evidence/recovery 是产品要求。 |
| App Server | separate capability probe | 富客户端 protocol/lifecycle，不由 CLI trial 继承。 |
| SDK | separate capability probe | package/API/pinned runtime 与 error projection 独立。 |
| managed Worktree | separate capability probe | App-owned creation/carry-in/cleanup/restore 独立。 |
| Automations | separate capability probe | unattended schedule/sandbox/effect 独立；本研究不授权创建 schedule。 |
| full Superpowers workflow | conditional; current corpus not applicable | 添加 sign-off、plan、worktree、subagent/review workflow。 |
| Trellis framework | not applicable | 持久状态和第二控制面与 sealed paths/authority 冲突。 |
| Hermes Agent | not applicable | corpus 无 remote/VPS/cron/gateway requirement。 |
| `grill-me` | not applicable to trial | 显式人工访谈会改变 fixed input 与 human-minute profile。 |
| `grill-with-docs` | not applicable to trial | 除人工访谈外还写未授权 `CONTEXT.md`/ADR。 |

这些判断应在观察 core trial 结果前固定，避免按结果选择 comparator。真正的 terminal
decision 仍必须来自 sealed evidence schema 下的完整分母，而不是本文。

## Product And Architecture Implications

### Keep Native First, Not Native Only

GPT-5.6 与 Codex Native 的进步支持默认走更薄的 Native 快路径，减少重复 prompt、重复
context 和无价值的流程 checkpoint；它不支持删除本仓特有的 authority、gate、evidence、
rollback、generation 与 Q0。建议保持 v3.23 的目标架构：

```text
Native Direct / Spec / Program
        |
qualified capability adapter (CLI | App Server | SDK | managed Worktree | Automation)
        |
Python policy + authority + evidence + recovery kernel
        |
deterministic commit-only Batch (Epoch 1 global capacity=1)
        |
legacy Hermes / AgentBridge / host-orchestrator read-only compatibility
```

这里的 adapter 应是 capability family，而不是一个“大而全的 Codex adapter”。profile
只能选择已按 exact generation 资格化的 surface。

### Keep Two Performance Promises Separate

- Native 快路径优化低交互延迟、较少上下文重复和较少人工 checkpoint。
- Batch 优化低人工、可预测、可恢复、可审计的 development throughput。
- Epoch 1 全局单 writer 是可靠性/authority boundary，不应宣传为高速并发。提高速度的
  首要来源是减少等待和返工，不是增加 Batch writer。

### Treat Harnesses As Conditional Policies

- Superpowers：只按需复用已证明有净收益的单一 skill/workflow，不引入 mandatory
  bootstrap 作为产品控制面。
- Trellis：不初始化到当前仓；若未来验证跨平台 memory/spec 价值，在隔离 pilot 中测试，
  并先处理第二真源与 AGPL 边界。
- Hermes：保持 legacy/reference；只在 remote/VPS/cron/gateway task family 出现时重评。
- Grill：只在高不确定性设计阶段显式调用；是否写 glossary/ADR 决定选哪一个，不进入
  默认 Batch。

本次一手资料没有要求改变 v3.23 的 Batch 禁止面、adapter contract、authority、并发、
Q0 trigger 或 quality floor，因此它本身只支持继续执行既有 `LAR-P0A-EVAL-002`，不构成
`preserve_v3_23_semantics` terminal decision。若后续实测要求上述规范语义改变，仍必须
冻结 v3.23 并创建 v3.24 successor。

## Unverified Or Inconclusive

- 没有找到一手、同 snapshot、同 task family、同 model/effort 的
  Superpowers vs Trellis vs Grill vs Codex Native A/B benchmark。
- 没有一手证据证明 `grill-with-docs` 在成功率、人工分钟、token、P50/P95 wall time、
  返工或 downstream acceptance 上普遍优于 `grill-me`。
- 上游仍维护只证明项目未消失，不证明其 workflow 在本仓产生正向净收益。
- 公开文档不能证明本机安装的 CLI/App Server/SDK/App/Automation exact generation 已
  通过本仓 sandbox、tool inventory、effect、rollback 和 evidence Q0。
- 本研究没有建立任何第三方 harness 的 sealed local identity，也没有判定其安装安全、
  供应链完整性或运行兼容性。
- Trellis/Hermes 的名称映射仍受用户未提供 canonical URL 的限制。
- App Server 文档包含 stable 与 experimental API；某一版本生成的 schema 只匹配该
  Codex version。[O3] 未固定 binary/schema identity 前不能推广协议兼容。
- Python Codex SDK 当前公开为 beta 且 published build pin runtime；未核对 exact package
  与目标 CLI generation 前保持 inconclusive。[O4]

## Source Register

所有来源均为一手资料，访问日期均为 `2026-07-13`。

| ID | Source | URL | Accessed |
| --- | --- | --- | --- |
| O1 | OpenAI, Using GPT-5.6 / current model guidance | https://developers.openai.com/api/docs/guides/latest-model | 2026-07-13 |
| O2 | OpenAI, Codex non-interactive mode | https://learn.chatgpt.com/docs/non-interactive-mode | 2026-07-13 |
| O3 | OpenAI, Codex App Server | https://learn.chatgpt.com/docs/app-server | 2026-07-13 |
| O4 | OpenAI, Codex SDK | https://learn.chatgpt.com/docs/codex-sdk | 2026-07-13 |
| O5 | OpenAI, Codex managed Git worktrees | https://learn.chatgpt.com/docs/environments/git-worktrees | 2026-07-13 |
| O6 | OpenAI, Scheduled tasks / Automations | https://learn.chatgpt.com/docs/automations | 2026-07-13 |
| S1 | Superpowers README at fixed commit `d884ae04...` | https://github.com/obra/superpowers/blob/d884ae04edebef577e82ff7c4e143debd0bbec99/README.md | 2026-07-13 |
| S2 | Superpowers official release `v6.1.1` | https://github.com/obra/superpowers/releases/tag/v6.1.1 | 2026-07-13 |
| T1 | Trellis README at fixed commit `b1edc67b...` | https://github.com/mindfold-ai/Trellis/blob/b1edc67b91a46ce63d507868650e248199bd7e50/README.md | 2026-07-13 |
| T2 | Trellis official Codex/platform file map at fixed commit | https://github.com/mindfold-ai/Trellis/blob/b1edc67b91a46ce63d507868650e248199bd7e50/.agents/skills/trellis-meta/references/platform-files/platform-map.md | 2026-07-13 |
| T3 | Trellis license at fixed commit | https://github.com/mindfold-ai/Trellis/blob/b1edc67b91a46ce63d507868650e248199bd7e50/LICENSE | 2026-07-13 |
| T4 | Trellis official repository/tag history | https://github.com/mindfold-ai/Trellis/tags | 2026-07-13 |
| H1 | Hermes Agent README at fixed commit `f813c7dd...` | https://github.com/NousResearch/hermes-agent/blob/f813c7ddad6f7a4973f83737d36d5e11a5cbbe50/README.md | 2026-07-13 |
| H2 | Hermes Agent official release `v2026.7.7.2` | https://github.com/NousResearch/hermes-agent/releases/tag/v2026.7.7.2 | 2026-07-13 |
| G1 | `grill-me` skill at fixed commit `6704a52a...` | https://github.com/mattpocock/skills/blob/6704a52ac4694ddcfc39665931211d6480b4b897/skills/productivity/grill-me/SKILL.md | 2026-07-13 |
| G2 | `grill-with-docs` skill at fixed commit `6704a52a...` | https://github.com/mattpocock/skills/blob/6704a52ac4694ddcfc39665931211d6480b4b897/skills/engineering/grill-with-docs/SKILL.md | 2026-07-13 |
| G3 | `grill-me` official docs at fixed commit | https://github.com/mattpocock/skills/blob/6704a52ac4694ddcfc39665931211d6480b4b897/docs/productivity/grill-me.md | 2026-07-13 |
| G4 | `grill-with-docs` official docs at fixed commit | https://github.com/mattpocock/skills/blob/6704a52ac4694ddcfc39665931211d6480b4b897/docs/engineering/grill-with-docs.md | 2026-07-13 |
| G5 | Matt Pocock skills official release `v1.1.0` | https://github.com/mattpocock/skills/releases/tag/v1.1.0 | 2026-07-13 |

## Rollback

删除本研究笔记即可。不得同时回滚或修改 frozen evaluation contract、planning status、
machine work items、candidate bytes、`.ai/config`、`.ai/state/control-plane.db`、provider/
auth、Codex processes 或任何既有 evidence。
