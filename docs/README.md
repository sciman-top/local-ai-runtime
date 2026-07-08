# Local AI Runtime 文档索引

- 中文名：**本地 AI 运行时**
- 当前主产品线：`Hermes -> AgentBridge -> Codex`
- 历史仓库 slug 与当前本地工作目录仍为 `local-ai-dev-orchestrator`；本文档索引只统一展示名，不宣称目录已迁移。

当前主产品线回调为 **Hermes -> AgentBridge -> Codex** 三层闭环。当前 authoritative truth 同时保留三条 repo-side 事实：

- canonical `JSON/YAML` intake / canonical JSON/YAML task contract 仍是当前内部归一化真源；`host_local` 主路径现已可直接接收合规 AgentBridge markdown task
- `.ai/runs/<run_id>/<task_id>/result.json` 仍是正式 task-level evidence 主体
- `.ai/runs/<run_id>/<task_id>/dispatch_state.json` 现已成为 runtime ledger companion；`AgentBridge results/*.md` 当前仍是 compatibility projection，它们都不取代 `result.json`

## Authoritative Truth

以下文件构成当前 authoritative docs，后续 AI 编码应先读这些文件，再动 `runtime/host-orchestrator`：

1. [planning-status.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/planning-status.json)
2. [orchestrator-prd.md](D:/CODE/local-ai-dev-orchestrator/docs/product/orchestrator-prd.md)
3. [orchestrator-target-architecture.md](D:/CODE/local-ai-dev-orchestrator/docs/architecture/orchestrator-target-architecture.md)
4. [next-work-selection-policy.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/next-work-selection-policy.json)
5. [task-contract.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/task-contract.md)
6. [result-contract.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/result-contract.md)
7. [review-contract.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/review-contract.md)
8. [state-and-db.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/state-and-db.md)
9. [runtime-v2-kernel.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/runtime-v2-kernel.md)
10. [config-and-worker-profiles.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/config-and-worker-profiles.md)
11. [acceptance-and-gates.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/acceptance-and-gates.md)
12. [run-state-and-handoff.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/run-state-and-handoff.md)
13. [orchestrator-roadmap.md](D:/CODE/local-ai-dev-orchestrator/docs/roadmap/orchestrator-roadmap.md)
14. [orchestrator-implementation-plan.md](D:/CODE/local-ai-dev-orchestrator/docs/plans/orchestrator-implementation-plan.md)
15. [orchestrator-task-list.md](D:/CODE/local-ai-dev-orchestrator/docs/backlog/orchestrator-task-list.md)
16. [hermes-compatibility-demotion.md](D:/CODE/local-ai-dev-orchestrator/docs/migrations/hermes-compatibility-demotion.md)
17. [runtime-v2-cutover-operator-runbook.md](D:/CODE/local-ai-dev-orchestrator/docs/runbooks/runtime-v2-cutover-operator-runbook.md)

## 当前主线口径

- 三层主线是：`Hermes -> AgentBridge -> Codex`
- 当前执行 hot path 收敛为 `Codex-first`；Hermes 保留风险编排、runtime ledger、跨执行器适配与历史基线职责，Claude 仍是可插拔 review sidecar
- 当前代码仍在 `runtime/host-orchestrator` 上演进，不新建平行顶层包
- `runtime/host-orchestrator` 是 `host_local` 可信运行时内核
- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/` 已作为同仓新内核吸收进 authoritative docs；它当前是 experimental dual-track，不是默认入口，也不要求改 repo slug / 本地目录名
- `docs/runbooks/runtime-v2-cutover-operator-runbook.md` 是 runtime_v2 默认入口切换的人工操作 runbook；它定义 cutover / approval / restore 边界，但不表示真实仓已执行 confirmed cutover
- `.ai/state/control-plane.db` 是调度真源
- `.ai/state/control-plane-v2.db` 是 v2 双轨控制面；`.ai/runs-v2/<run_id>/<task_id>/<attempt_id>/` 是 v2 尝试级工件面
- `.ai/runs/<run_id>/<task_id>/` 是正式 evidence 面
- `.ai/config/*.yaml` 是 repo-owned 运行时配置真源
- repo-owned `host_local` task entrypoint 现已落地：`host-orchestrator --run-task` 与 `runtime/host-orchestrator/scripts/run-host-task.ps1` 当前会通过 worker factory 支持 `codex_sdk / codex_exec`；在现有 built-in profile 中，`local_maint` 直接走 `codex_sdk`，而 committed `remote_non_gui_probe / vm_gui_probe` 仍因 `runner_wired=false` 在 worker 前 handoff
- `host_local > remote_non_gui > vm_gui` 是终态能力范围与分级晋升顺序
- `AgentBridge-first intake` 已以安全边界接入 `host_local`；markdown task 先归一化到 repo-owned canonical 默认值，并对 execution-critical override fail closed
- `P2-T03` 的 repo-side AgentBridge round-trip parity 已落地，但尚未自动升级为 `platform compatibility green`
- `P4-T01` 的 live planner sidecar receipt 已落地；当前 planner-gated task 会先运行 codex-backed planner sidecar、写出 `planner_result.json`，然后仍停在 `waiting_handoff`，尚未宣称 live `Direct GPT-5.4 API` planner 已接线
- `P4-T02` 的 repo-side review gate 已落地；低风险任务默认自动推进，medium/high/critical 风险、policy surface、以及 force-on review 会在 worker / verification 之后停在 `needs_review`；配置 `review_worker_profile = claude_glm_review` 的 host_local review path 当前可 materialize bounded live heterogeneous review receipt，但这仍不等于 live `claude_glm` primary task execution
- `P4-T03` 的 repo-side 谓词正反覆盖已落地；`user_forced_planner / user_forced_review` 现在是 contract 承认的 force-on override，而不是文档漂浮字段
- `P3-T02` 的 repo-side path guard 已落地；repo-escape path claim、declared worktree root drift、declared branch drift、以及 worker 结束后落在 `allowed_paths` 外或 `forbidden_paths` 内的新改动都会 fail closed；当前 git-backed 变更审计要求 workspace 具备 `.git` admin path
- `P3-T03` 的 repo-side 最小 worktree manager 已落地；declared isolated worktree 任务现在可从 repo root 自动 create/reuse linked worktree，并在其中执行 worker 与 verification
- `P3-T04` 的 repo-side 最小 cleanup manager 已落地；runtime 现在只会自动 remove 自己管理、且 clean 的 linked worktree，review-pending、failed、dirty、或外部直接启动的 isolated worktree 会保留并写出 `worktree_cleanup` 事件
- `P3-T05` 的 graded-autonomy runtime ledger 已落地；`dispatch_state.json`、`result.json`、以及 `runtime_tasks` 现在共享 `attempt / next_action / cleanup_owner / cleanup_status / status_reason / dispatch_state_ref` 一组收口字段
- `P3-T06` 的 repo-side lifecycle ops 已落地；`task_lifecycle.py` 与 CLI 现在可显式 materialize `stale / cancelled / resumed`，`retry` 通过 `attempt + retry_rewind` 收口
- `P4-T04` 的 repo-side structured receipts 已落地；live planner-sidecar 路径现在会写 `planner_result.json`，review-gated 路径会写 `review_result.json`，当前 runtime outcome 会写 `closeout_bundle.json`，并通过 `result.json / dispatch_state.json / evidence_index.json` 串起引用；当前 live review receipt 仅基于 bounded runtime summary materialize
- `P5-T01` 的 repo-side `leases / route / quota` 收口已落地；explicit/default `worker_profile` 现在会 materialize `route_reason`，selected profile 的 `max_active_leases` 超额时会在 worker 前 handoff
- `P5-T02` 的 deterministic multi-worker simulation 已落地；当前可复放 `retry / route / quota / review-handoff` summary，但这仍不等于 live 多 worker scheduler
- `P5-T03` 的 `remote_non_gui` promotion evidence 已落地；repo-owned `remote_non_gui_probe` 现在可被显式选中，但 `host_local` 只会 fail closed 到 handoff，并额外留下机器可读 `handoff_receipt.json` / `handoff_receipt_ref`，不会伪装成 remote runner 已执行
- `P5-T04` 的 `remote_non_gui` runner wiring readiness 已落地；临时测试配置可证明 `runner_wired=true` 会调用注入 runner，runner 失败保持 failed dispatch 且不写成功 `result.json`，但 committed profile 仍未接真实 remote runner
- `P6-T01` / `P6-T02` 的 repo-side Hermes parity / historical snapshot mapping verifier 已落地；`run-hermes-parity.ps1` 现在会把 certified baseline doc、current known-good / boundary anchors、snapshot contract、known-good validator、以及 env-sensitive bring-up drift 收进同一 summary，但这仍不等于 `platform compatibility green`
- `P6-T03` 的 repo-side `vm_gui` conditional promotion evidence 已落地；默认 GUI-only 请求现在会在 `host_local` 上因 `execution_lane=vm_gui; requires_gui=true` handoff，显式 `vm_gui_probe` 也只会 fail closed 到 `runner_not_wired`
- `worktree` 当前只代表写入隔离，不代表 memory/provider/session 隔离
- branch deletion 仍不自动化；当前 repo-side topology promotion proof 与 runner wiring readiness 已收口，next open set 收窄到真实 remote host runner acceptance 与后续 review hardening
- 当前 `host_local` task entrypoint 虽已接线真实 worker factory，且 live planner sidecar receipt 与 bounded live heterogeneous review sidecar receipt 已能在 configured host_local path 上 materialize，但这仍不等于 live `claude_glm` primary task execution、真实 remote/vm runner、`platform compatibility green`、或 `live accepted`
- `compatibility_projection_ref` 与 `lane` 字段名当前明确继续保留；待真实 remote/vm runner acceptance 与后续 review 稳定性都真实落地后再复评是否迁移
- 当前 active queue 仍是 `PHASE-1-VERTICAL-SLICE`；repo-side exit gates 已闭环，但 live posture 仍停在 `live probe ready`

## Governance Overlay

治理增强层是当前主线的 cross-cutting overlay，不替代 `Phase 1 -> Phase 6` 产品路线图。

- `selector + change-evidence + preflight + reference governance` 是当前 repo-side 治理增强面

## Operator Assets

以下文件是 repo-owned 的操作资产，不属于 authoritative runtime truth，但可直接复用：

- 协作模式说明：[docs/主控-子代理-worktree-协作模式.md](D:/CODE/local-ai-dev-orchestrator/docs/主控-子代理-worktree-协作模式.md)
- prompt 资产入口：[prompts/subagent-worktree/README.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/README.md)
- manifest 模板：[templates/agent-work-manifest.example.yaml](D:/CODE/local-ai-dev-orchestrator/templates/agent-work-manifest.example.yaml)
- dispatch state 模板：[templates/dispatch-state.example.json](D:/CODE/local-ai-dev-orchestrator/templates/dispatch-state.example.json)
- review 结果模板：[templates/review-result.example.json](D:/CODE/local-ai-dev-orchestrator/templates/review-result.example.json)
- closeout bundle 模板：[templates/closeout-bundle.example.json](D:/CODE/local-ai-dev-orchestrator/templates/closeout-bundle.example.json)
- closeout 清单：[templates/closeout-checklist.md](D:/CODE/local-ai-dev-orchestrator/templates/closeout-checklist.md)
- 子代理模型策略默认按 role-aware / risk-aware / lane-aware 选择，不再固定 `gpt-5.4 + xhigh`
- 当前 selector 预期结果仍是 `promote_phase1_execution`
- GPT-5.4 gateway 与 `codex exec` prerequisite probes 已 ready，但 `network_proxy` 仍是 `platform_na`，所以 live execution 仍先限纯本地任务
- `governed-ai-coding-runtime` 已被纳入正式 `governance-sidecar` companion，但它只提供治理机制参考，不定义当前主线实现真相

当前治理入口：

- [next-work-selection-policy.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/next-work-selection-policy.json)
- [change-evidence/README.md](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/README.md)
- [change-evidence/20260706-strategic-regression.md](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-strategic-regression.md)
- [references/README.md](D:/CODE/local-ai-dev-orchestrator/references/README.md)

## Rule Coordination

- [AGENTS.md](D:/CODE/local-ai-dev-orchestrator/AGENTS.md) 是本仓共同项目规则主体。
- [CLAUDE.md](D:/CODE/local-ai-dev-orchestrator/CLAUDE.md) 是 Claude thin wrapper；首个非空行是独立 `@AGENTS.md`。
- `D:\CODE\governed-ai-coding-runtime` 是全局规则控制仓，只负责 `Codex + Claude` global-only rule sync 与 target-project audit；本仓不负责全局规则分发。
- 本仓项目规则差异必须通过 `audit + integration + verification` 闭环解决，不允许 blind overwrite。

## 兼容与历史

Hermes/AgentBridge 历史基线与兼容资料入口：

- [docs/platforms/hermes/README.md](D:/CODE/local-ai-dev-orchestrator/docs/platforms/hermes/README.md)
- [docs/migrations/hermes-compatibility-demotion.md](D:/CODE/local-ai-dev-orchestrator/docs/migrations/hermes-compatibility-demotion.md)

参考源码策略仍保留：

- [参考项目清单.md](D:/CODE/local-ai-dev-orchestrator/docs/参考项目清单.md)
- [社区参考源码策略.md](D:/CODE/local-ai-dev-orchestrator/docs/社区参考源码策略.md)
