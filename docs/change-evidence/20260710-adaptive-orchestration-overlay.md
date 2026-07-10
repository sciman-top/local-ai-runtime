# 2026-07-10 Adaptive Orchestration Overlay

## Goal

- 将单代理/多代理选择产品化为 repo-owned `Adaptive Orchestration Overlay`，而不是把 Trellis、Grill 或 Superpowers 作为核心依赖。
- 按 `observe -> guarded -> evaluated promotion` 推进，保持 `PHASE-1-VERTICAL-SLICE`、`promote_phase1_execution`、默认 v1 和 `live accepted=false`。
- 把 authorable constraints、derived decision、guarded execution、attempt evidence 与人工晋升评测收成可验证闭环。

## Basis

- 官方/社区研究：[20260710-gpt56-subagent-orchestration-research.md](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260710-gpt56-subagent-orchestration-research.md)
- 工作流比较：[20260710-trellis-grill-vs-superpowers-research.md](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260710-trellis-grill-vs-superpowers-research.md)
- 产品规格：[adaptive-orchestration.md](D:/CODE/local-ai-dev-orchestrator/docs/specs/adaptive-orchestration.md)
- 机器可读状态：[planning-status.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/planning-status.json)

## Changes

- manifest 将 authorable input 收敛为 `orchestration_constraints`；实际模式、原因码、波次、冲突、角色、模型和能力写入派生 `orchestration_decision.v1`。
- 缺少新增顶层字段的旧 v1 manifest 归一化到 `observe_default + single_agent + zero delegation budget`，不会静默进入 guarded。
- `.ai/config/policies.yaml` 增加版本化 observe/guarded profiles、模型路由、能力路由和总代理预算；`.ai/config/workers.yaml` 增加 read/review/write profiles。
- `--evaluate-orchestration-manifest` 只写 decision evidence，不启动 worker、不创建 control-plane task state。
- `--run-orchestration-manifest-v2` 只接受 guarded-ready decision，并先归一化为 canonical v2 tasks。
- 冲突、lane/network/GUI、lease、能力、sandbox、planner、worker 总预算和 writer isolation 路径 fail closed；linked worktree 在 decision 与执行点双重校验。
- model 与 reasoning effort 同时传入真实 worker request；失败 summary 保留 decision/route/model 引用。
- guarded attempt 写入 `orchestration_decision_ref / decision_id / policy_version`，并新增带 sha256/byte count 的 `evidence_index.json`。
- regression evaluator 要求同 task/model/reasoning/gate 的 baseline/candidate 各至少 3 次，且只返回人工晋升资格，永不自动 promotion。
- PRD、架构、路线图、实施计划、backlog、task/result/state/runtime/config/gates/handoff specs、prompt pack、planning status 和 verifier 已进入同一 consistency surface。

## Verification

- Focused implementation tests：`57 passed`（adaptive orchestration、agent-work assets、SDK/exec request mapping、wave1 regression）。
- Evidence precision follow-up：`test_adaptive_orchestration.py` 为 `19 passed`，覆盖 worker-attempt stage、总代理预算、lease read failure、linked worktree、reasoning effort 与 error decision refs。
- Full pytest：`158 passed in 44.89s`。
- Asset validation：7 类 manifest/dispatch/closeout/review/orchestration/runner-acceptance 示例通过 repo-owned validator；全部 JSON template 与 `planning-status.json` 解析通过。
- Planning verifier：`status=pass`，authoritative docs 为 `20`，active profile 为 `observe_default`，adaptive proof ref 存在。
- Next-work selector：首次因 34 秒外层命令超时且无输出；确认它会内嵌完整 preflight 后，以 180 秒上限复跑通过，仍返回 `promote_phase1_execution`。
- Selector-invoked governance preflight：exit `0`；`158 passed in 41.30s`，contract/docs/scripts/diff hygiene 通过，build/hotspot 按既有 `gate_na` 契约留痕。

## N/A And Boundaries

- build：`gate_na`；当前仓没有独立 build gate。替代验证为完整 pytest；恢复条件为仓库新增正式 build script / CI gate。
- hotspot：`gate_na`；当前仓没有独立 hotspot gate。替代验证为 pytest、planning verifier、selector、governance preflight 与 diff hygiene；恢复条件为仓库新增正式 hotspot gate。
- `AO-T06` 仍开放：尚无代表性真实 baseline/candidate corpus，因此 promotion status 固定为 `insufficient_evidence`。
- repo-side guarded 机制不等于默认 v2 cutover、remote/vm runner acceptance 或 live accepted。
- `.codex` 角色配置是本仓开发工具约束，不代表 runtime writer isolation；运行时只承认实际 worktree/branch/common-dir/path 证据。

## Rollback

- 首选把 `.ai/config/policies.yaml` 的 active profile 保持或恢复为 `observe_default`，并停止调用显式 guarded CLI。
- 如需完整回滚，以同一变更集回滚 runtime、config、templates、tests、docs、planning verifier 和本证据索引。
- 回滚不删除 branch/worktree，不切默认入口，不改 active queue，也不把已有 run-level decision 工件解释为 task success。
