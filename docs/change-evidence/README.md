# Change Evidence Index

这个目录只存 **repo-level governance evidence**，不存 task-level `.ai/runs/<run_id>/<task_id>/` 正式工件。

边界：

- 这里记录 selector、preflight、reference governance、docs routing 这类仓级治理证据
- task-level `result.json`、`verification_summary.json`、`cost_summary.json`、`evidence_index.json` 仍属于 `.ai/runs/<run_id>/<task_id>/`
- 这里的索引只回答“当前仓的治理增强面何时、为何、如何被刷新”

当前入口：

- [20260706 Verification Runner Minimal Gates](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-verification-runner-minimal-gates.md)
- [20260706 Host Local Robustness And Lease Helpers](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-host-local-robustness-and-lease-helpers.md)
- [20260706 Strategic Regression](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-strategic-regression.md)
- [20260706 Layout Defaults To AI State](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-layout-defaults-to-ai-state.md)
- [20260706 Canonical Runtime Cuts Over From AgentBridge](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-canonical-runtime-cuts-over-from-agentbridge.md)
- [20260706 Config And Worker Profile Contract](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-config-and-worker-profile-contract.md)
- [20260706 Acceptance And Gates Contract](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-acceptance-and-gates-contract.md)
- [20260706 Run State And Handoff Foundation](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-run-state-and-handoff-foundation.md)
- [20260706 Selector Policy Promoted To Verifier Scope](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-selector-policy-promoted-to-verifier-scope.md)
- [20260706 Phase1 Prereq Probes Ready](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-phase1-prereq-probes-ready.md)
- [20260706 Phase1 Real SDK Vertical Slice](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-phase1-real-sdk-vertical-slice.md)
- [20260706 Phase1 Evidence Index Revalidation](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-phase1-evidence-index-revalidation.md)
- [20260706 impl_pack Stale Demotion And Verifier Coverage](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-impl-pack-stale-demotion-and-verifier-coverage.md)
- [20260706 Governed Governance Absorption](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-governed-governance-absorption.md)
- [20260706 Preflight Line-Ending Hygiene Closeout](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-preflight-line-ending-hygiene-closeout.md)
- [20260706 Rule Governance Pilot Coordination](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-rule-governance-pilot-coordination.md)

当前最新结论：

- authoritative docs 已回调为 `Hermes -> AgentBridge -> Codex` 三层主线
- 当前 repo truth 仍保持 canonical intake、`result.json` 正式 evidence、以及 compatibility projection
- `host_local` 失败收口、最小 lease lifecycle helpers、以及 exec fallback 进程守卫已落 repo-side
- 最小 verification runner 已落 repo-side，`verification_summary.json` 在配置 `test / contract` 时会反映真实 gate 结果
- Governance Overlay 已作为当前主线的 cross-cutting layer 落盘
- `P1-T01 / P1-T02 / P1-T03` 的 repo-side code slice 已闭环到 canonical runtime + compatibility projection
- repo-owned config / worker-profile contract 已落盘，host runtime 不再依赖散落硬编码默认值
- selector policy、acceptance tiers、run-state/handoff foundation 与 impl_pack stale demotion 已进入 authoritative/verifier 同步面
- GPT-5.4 gateway probe 与 `codex exec` minimum probe 已 ready，当前 selector 预期结果已提升到 `promote_phase1_execution`
- 一次非 mock 的 `Codex SDK` canonical runtime vertical slice 已成功写出正式 `.ai/runs/...` 工件
- `P1-T05` 的 `evidence_index.json` sha256 / byte_count 独立重算入口已落盘，并能回放 real SDK 产物
- `network_proxy` 仍是 `platform_na`，所以当前 `Phase 1` 真实执行应先限纯本地任务
- Python repo-level line-ending policy 已显式覆盖 `*.py -> LF`
- 本仓已接入 `AGENTS.md` 共同项目规则主体 + `CLAUDE.md` thin wrapper 试点；全局规则真源仍在 `D:\CODE\governed-ai-coding-runtime`
- 当前 active queue 仍是 `PHASE-1-VERTICAL-SLICE`
- 当前预期 next action 仍是粗粒度的 `promote_phase1_execution`；其内部下一最小实现切片是 `P2-T03 AgentBridge round-trip parity`
