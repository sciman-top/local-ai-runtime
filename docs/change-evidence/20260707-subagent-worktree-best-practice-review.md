# 2026-07-07 Subagent Worktree Best-Practice Review

## Goal

- 审查当前 repo-owned 的 `主控 + 子代理 + worktree` 协作资产，判断它是否已经接近最佳实践
- 对照官方文档与社区优秀项目，识别可泛化、可自动化、可高并发演进的缺口

## Verdict

- 当前这套模式 **方向正确，但还不是“最佳”或“高度自动化终态”**
- 作为 **人工主控、半自动、多切片单仓协作包**，它已经明显优于纯聊天式即兴操作
- 作为 **高并发、强约束、可恢复、可观测、可泛化的 control plane**，它还缺少关键的 machine-readable contract、dispatch guard、status ledger 和 closeout bundle

## What Is Already Good

- 明确把 `prompt` 资产定义为 `non-authoritative operational asset`，没有把目标态误写成 runtime truth
- 明确主控、explorer、worker、reviewer 分工，且保留 `repo-side done != platform/live accepted` 边界
- 明确 `worktree` 主要用于写入隔离，而不是为了“多开模型”本身
- 明确要求 README / planning / backlog / evidence 一起 closeout，而不是只收代码

## Main Gaps

### 1. Manifest 还不是 canonical task contract 的子集

- 当前模板只覆盖 `objective / truth_sources / tasks / read_set / write_set / done_when / tests / risk_level / blocked_by / worktree_name / branch_name`
- 它没有承接 repo 里已经正式定义的 `target_repo / base_branch / allowed_paths / forbidden_paths / write_access / merge_policy / execution_lane / requires_network / requires_gui / artifacts_out / handoff_policy / verification_commands`
- 这意味着当前 manifest 更像“人读得懂的 dispatch 草图”，还不是能被 runtime、review gate、cleanup manager 直接消费的统一协议

### 2. 并发判定只看 `write_set`，还不够

- 当前文档把 `write_set` 作为主要并发判据，这是一个好起点
- 但 repo truth 已经把 `planner_required / review_required / touches_policy_surface` 定义为机器派生字段，且 `planner_required` 不只受 `write_set` 影响，还受任务数量、跨仓、依赖、风险等级影响
- 当前 prompt pack 里没有 `lease`、没有 `worktree` 心跳、没有 fail-fast、没有并发预算、没有 stale worker 回收

### 3. Prompt 输出还不够结构化，不利于自动编排

- `worker.prompt.md`、`spec-reviewer.prompt.md`、`quality-reviewer.prompt.md` 主要还是 prose 输出
- 它们没有直接对齐 repo 已存在的 `review-contract` 与 `run-state-and-handoff` contract
- 缺少 `reviewer_kind / review_mode / blocking_reasons / source_evidence_refs / cleanup_owner / cleanup_status / next_action` 这类字段，导致结果难以被下一步流程稳定消费

### 4. Closeout 还是 checklist，不是正式 result bundle

- 当前 `templates/closeout-checklist.md` 适合人工核对
- 但它没有提供 machine-readable 的 merge 结果、branch/worktree 实际清理状态、evidence refs、gate 输出、残留风险、下一动作
- 这不利于恢复、重试、handoff、批量并发收口，也不利于后续健康面板或状态面板

### 5. 模型策略过于硬编码，不利于效率和成本优化

- 当前把所有子代理默认锁在 `gpt-5.4 + xhigh`
- 这与当前用户偏好并不冲突，短期内继续作为默认强模型策略是合理的
- 但从可泛化治理角度看，长期仍更适合演进到“默认强模型 + repo-owned 的 role-aware / risk-aware override 能力”，而不是永远把所有角色写死成同一档

### 6. 缺少防止 worktree/cwd 漂移的 runtime guard

- prompt 里要求 worker 在独立 worktree 工作，但没有正式 guard 来验证当前 `cwd`、当前分支、当前 Git root、目标 worktree 是否匹配
- 这类问题在社区实践中是高频真实故障，不是理论问题

## External Signals

### Official docs

- Git 官方文档确认 `git worktree` 适合一个仓库同时挂多个工作树；linked worktree 与主仓共享对象库，但 `HEAD`、`index` 等是 per-worktree 状态，且完成后应通过 `git worktree remove` 清理；对暂时离线的工作树可加锁防止被 prune
- OpenAI 官方 orchestration 文档强调：先决定是“handoff 交接所有权”还是“manager 调 specialist as tool”；并明确建议“能单 agent 先单 agent”，只有当 contract、policy、能力隔离真的改善时才拆分
- OpenAI Agents SDK 文档提供 `input_type / on_handoff / input_filter / recommended handoff prompt prefix`，说明 handoff 最佳实践不是只写 prompt，还要传结构化元数据并控制历史裁剪
- Anthropic 官方 subagents 文档强调：子代理要有独立上下文、独立工具权限、可按角色选模型；适合隔离大输出与并行研究，但在延迟敏感、强共享上下文的任务上不应滥用

### Community projects

- `subtask` 把每个任务放进独立 Git worktree，并持久化 task folder、状态、diff 与会话，这比纯 prompt 更接近可恢复的任务系统
- `parallel-cc` 把并行执行做成 coordinator + per-task isolation + result aggregation + configurable concurrency + fail-fast
- `CodeWhale` 的做法更接近你当前方向：子会话可 fresh/fork、parallel edit lane 自动建 worktree，brief 用紧凑字段而不是长 prose，并且有 heartbeat timeout 来回收卡死 worker
- `opencode-worktree-session` 直接把“拒绝在 main 上跑、自动切到 worktree、退出后自动提交/推送/清理”做成工具层行为，这比靠 prompt 记忆更稳

## Recommended Next Shape

### 1. 把 manifest 升级为正式 dispatch contract

- 目标不是另起一套 schema，而是让 `templates/agent-work-manifest.*` 成为 `docs/specs/task-contract.md` 的可执行子集或投影
- 至少补齐：
  - `target_repo`
  - `base_branch`
  - `allowed_paths`
  - `forbidden_paths`
  - `write_access`
  - `merge_policy`
  - `execution_lane`
  - `requires_network`
  - `requires_gui`
  - `artifacts_out`
  - `handoff_policy`
  - `verification_commands`
  - `user_forced_planner`
  - `user_forced_review`

### 2. 单独拆出 dispatch / lease / closeout 三类工件

- `task_manifest.yaml`
  - 描述任务意图、边界、依赖、allowed paths、gate 命令
- `dispatch_state.json`
  - 描述 agent id、role、model、worktree path、branch、lease owner、heartbeat、started_at、status
- `closeout_bundle.json`
  - 描述 merge result、verification refs、evidence refs、cleanup status、residual risk、next action

### 3. 让 review 输出直接对齐 repo review contract

- `spec-reviewer` 与 `quality-reviewer` 不再只输出 prose
- 直接输出能映射到 `docs/specs/review-contract.md` 的结构化字段
- `Ready to merge` 只是一个展示字段，不应是唯一正式结论

### 4. 把 worktree guard 从 prompt 变成工具/脚本

- 在 worker 开始前强制记录并校验：
  - `cwd`
  - `git rev-parse --show-toplevel`
  - 当前分支
  - 目标 branch / worktree / allowed_paths
- 若不匹配，直接 fail closed

### 5. 让并发策略变成“风险 + 依赖 + 写集 + policy surface”四维判定

- 当前只按 `write_set` 判定并发，适合 v0
- 下一步应至少把：
  - `blocked_by`
  - `risk_level`
  - `touches_policy_surface`
  - `target_repo`
  - `shared fixture/schema/doc truth surface`
  一起纳入并发决策

### 6. 模型路由改为 role-aware，而不是全部 `gpt-5.4 + xhigh`

- 默认仍可保留 `gpt-5.4 + xhigh`
- `explorer`：如未来用户允许再降成本，可优先低成本、快速、只读
- `worker`：中高能力，按风险升档
- `reviewer`：按风险选择更强模型或异构模型
- `planner`：仅在 `planner_required` 命中时启用更高代价路径

## Practical Conclusion

- **是否最佳**：不是
- **是否值得保留并继续演进**：是
- **当前最适合的定位**：repo-owned 操作协议包 / 人工主控协作骨架
- **距离高效、高速、高并发、自动化、智能化的主要差距**：不是 prompt 还不够长，而是 contract、guard、lease、state、closeout 还没 fully executable

## Source Links

- [Git worktree documentation](https://git-scm.com/docs/git-worktree)
- [OpenAI API: Orchestration and handoffs](https://developers.openai.com/api/docs/guides/agents/orchestration)
- [OpenAI Agents SDK: Handoffs](https://openai.github.io/openai-agents-python/handoffs/)
- [Anthropic Claude Code: Create custom subagents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)
- [zippoxer/subtask](https://github.com/zippoxer/subtask)
- [frankbria/parallel-cc](https://github.com/frankbria/parallel-cc)
- [Hmbown/CodeWhale docs/SUBAGENTS.md](https://github.com/Hmbown/CodeWhale/blob/main/docs/SUBAGENTS.md)
- [felixAnhalt/opencode-worktree-session](https://github.com/felixAnhalt/opencode-worktree-session)
- [obra/superpowers issue: Git worktree confusion](https://github.com/obra/superpowers/issues/5)
