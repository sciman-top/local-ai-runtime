# 2026-07-10 GPT-5.6 Bounded Subagent Orchestration

> Status: superseded as an authorable decision contract by `Adaptive Orchestration Overlay`. 本文件保留首次 bounded prompt/config 试验的历史证据；当前 manifest 只写 `orchestration_constraints`，实际模式由 `orchestration_decision.v1` 派生。

## Goal

- 让 repo-owned 子代理提示词适配 GPT-5.6 Multi-agent，而不把模型能力误写成默认无限委派。
- 把单/多代理选择、并发预算、总数、树深、写冲突与停止策略从 prose 下沉到可校验 manifest contract。
- 保持 `runtime_v2`、`current_active_queue`、live acceptance 与现有 runtime worker profiles 不变。

## Basis

- 官方与社区研究：[20260710-gpt56-subagent-orchestration-research.md](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260710-gpt56-subagent-orchestration-research.md)
- 官方事实：GPT-5.6 Multi-agent 是显式启用的 beta；独立 bounded workstreams 适合多代理，顺序链、共享可变状态和小任务优先单代理；多数 workload 推荐并发上限 `3`。
- 本仓事实：子代理共享 filesystem，worktree 只提供写入隔离；主控仍负责冲突、集成、门禁、evidence 与 cleanup。

## Changes

- `master.prompt.md` 改为默认单代理、阈值式委派，不再固定“先 explorer、再 worker”。
- `explorer.prompt.md` 采用“最大合理切片”；`worker.prompt.md` 要求最小但完整修改，且只在 manifest / merge policy 或用户明确要求时 commit。
- manifest 新增必填 `orchestration_policy`：
  - `selected_mode / decision_reason`
  - `max_concurrent_subagents / max_total_subagents / max_tree_depth`
  - `nested_subagents_allowed / write_conflict_policy / stop_policy`
- validator fail closed：
  - `single_agent` 必须使用零子代理预算并禁用嵌套。
  - `multi_agent` 并发为 `1..3`、总数为 `1..6`、树深固定为 `1`，并发不得大于总数。
  - `nested_subagents_allowed` 固定为 `false`。
- JSON Schema 通过 `if/then` 同步约束 single-agent 零预算与 multi-agent 非零预算；`max_concurrent_subagents <= max_total_subagents` 的跨字段比较继续由 Python validator 负责。
- 模板默认模型更新为 `gpt-5.6-sol + high`，reasoning effort 增加 GPT-5.6 支持的 `max`，但不自动选择最高档。
- 保留原有 `.codex/config.toml` 的 `sandbox_workspace_write.network_access = true`，新增 `agents.max_threads = 4 / max_depth = 1`。
- 新增 project-scoped `explorer / spec_reviewer / quality_reviewer`，全部强制 `read-only`；explorer 使用 `gpt-5.6-terra + medium`，reviewers 使用 `gpt-5.6-sol + high`。
- 当前不覆盖 built-in worker：custom agent config 无法证明独立 worktree 已建立，写入隔离仍由 runtime worktree guard 负责。

## Verification

- TDD RED：`test_agent_work_assets.py` 首次运行出现 `2 failed, 7 passed`，原因分别为 schema 和示例缺少 `orchestration_policy`。
- Target GREEN：同文件复测 `9 passed`。
- Asset validation：`validate-agent-work-assets.py` 返回 `status=pass`，五类模板全部通过。
- Focused regression：`test_agent_work_assets.py + test_lifecycle_ops.py` 返回 `15 passed`。
- JSON syntax：两个修改后的 schema 均通过 `python -m json.tool`。
- Full pytest：最终复跑 `135 passed in 36.95s`；preflight 复跑为 `135 passed in 35.79s`。
- Planning verifier：`status=pass`，authoritative docs `19`。
- Next-work selector：`status=pass / next_action=promote_phase1_execution`，active queue 未变。
- Governance preflight：exit `0`；test、contract/invariant、Docs、Scripts、`git diff --check` 全部 pass。
- Project Codex config TDD RED：缺少 `[agents]`，定向测试 `1 failed`；补齐配置与角色后 `1 passed`。
- Schema conditional TDD RED：缺少 `orchestration_policy.allOf`，定向测试 `1 failed`；补齐 `if/then` 后 `1 passed`。
- `codex debug prompt-input`：exit `0`，新进程成功加载项目规则链。
- 单代理只读 live probe：exit `0`，耗时 `16.55s`，usage 为 `54688 input / 24320 cached / 283 output / 103 reasoning`；返回 `single_agent / PHASE-1-VERTICAL-SLICE / promote_phase1_execution`。

## N/A And Boundaries

- build：`gate_na`；本仓没有独立 build gate，替代验证为完整 pytest，依据 `docs/specs/acceptance-and-gates.md`。恢复条件：仓库新增正式 build script / CI gate。
- hotspot：`gate_na`；本仓没有独立 hotspot gate，替代验证为 verifier、pytest 与 diff hygiene。恢复条件：仓库新增正式 hotspot gate。
- `.codex/config.toml` 原先是用户未跟踪内容；本次在用户明确要求连续执行后做增量整合，保留原有网络设置，不改 provider/auth。
- 没有修改 `planning-status.json`、selector 预期、`runtime.active_version`、worker profile、`current_active_queue` 或 live posture。

## Platform N/A

- `codex doctor --json --summary`
  - reason：当前 CLI 两次超过 `60s` 无输出。
  - alternative_verification：tomllib 配置测试、`codex debug prompt-input`、严格项目配置单代理 probe。
  - evidence_link：本文件 Verification。
  - expires_at：Codex CLI 升级或 doctor/provider 诊断恢复后复测。
- strict global config
  - reason：用户级 `~/.codex/config.toml` 含当前 CLI 不识别的 `disable_response_storage`；删除它可能改变数据保留语义，本次不擅自修改。
  - alternative_verification：`--ignore-user-config --strict-config` 成功验证项目配置，认证仍由现有 Codex 登录提供。
  - evidence_link：本文件 Verification。
  - expires_at：用户级配置完成官方迁移后恢复全链 strict probe。
- multi-agent live probe
  - reason：隔离用户配置的尝试出现 `collab spawn failed: no thread with id` 与 read-only policy rejection；保留用户配置的尝试因 API-key/ChatGPT provider mismatch 在模型调用前退出。子代理自报不能作为成功证据。
  - alternative_verification：项目 agent TOML 解析测试、并发/深度 manifest validator、prompt-input、新进程单代理 probe。
  - evidence_link：本文件 Verification 与 `20260710-gpt56-subagent-orchestration-research.md`。
  - expires_at：CLI collaboration thread 与本机 provider/auth 路径对齐后复测。

## Rollback

- 以同一变更集回滚 prompt pack、操作说明、manifest / dispatch schemas、validator、测试和本证据索引。
- 回滚不会触及用户未跟踪的 `.codex/`，也不会改变 runtime v1 / v2 数据或 task-level `.ai/runs/` 工件。
