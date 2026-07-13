# AGENTS.md - Local AI Runtime
**项目契约**: 2.0
**全局规则复核**: 9.55
**仓库目录**: local-ai-dev-orchestrator
**最后更新**: 2026-07-14

## 1. 当前落点与目标归宿
- 当前落点：`runtime/host-orchestrator`、`.ai/state/control-plane.db` 与既有 evidence 仍是唯一现行运行事实；`local-ai-runtime-0.2-v3.23` 只是 `baseline_candidate`，尚未批准、Truth Reset 或实现。
- 目标归宿：Baseline Approval 后按 v3.23 在 `runtime/local-ai-runtime` 实现面向 Windows 本机、单操作者信任域的通用受控 AI 开发执行平台；产品目标是低人工、可预测、可恢复的开发吞吐。Epoch 1/v0.2 为 Unified Native + 全局 capacity=1 的 deterministic commit-only Batch，Native 快路径追求低交互延迟，Batch 不承诺高速并发；legacy Hermes/AgentBridge/host-orchestrator 最终只读兼容。
- 下一最小里程碑：队列 `LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE` 的 `close_baseline_normative_package_first / LAR-P0A-004`。`LAR-P0A-003` 已闭合 `CanonicalizationPolicy.v1`；规范包 `3/15 present, 12 missing`，最终 manifest 仍不存在。
- `LAR-P0A-EVAL-002` Native thin-path / capability comparative evaluation 已记录非规范 `preserve_v3_23_semantics` 决定。18 个 core trial 因外部 host 漂移跨 3 个分别 Q0-admitted generation，合并指标不得用作 profile promotion；CLI execution interface 仅对当前最终 generation 通过 capability/Q0 证据。App Server、SDK、managed Worktree 仍 inconclusive，Automations 对本 corpus not_applicable。任何后续语义变更仍必须冻结 v3.23 并创建后继 candidate，不能原地改写。
- 本次规则更新只是预批准 planning control-plane 对齐，不是 v3.23 的 P0B Truth Reset；不得据此创建 approval、新 runtime、Batch claim 或 live evidence。

## A. 仓库事实与模块边界
- `runtime/host-orchestrator` 是当前 `host_local` 可信内核；active Baseline Approval、Truth Reset 和 Legacy Ownership Guard 之前，禁止创建 `runtime/local-ai-runtime` 或其他平行执行包。
- `.ai/state/control-plane.db` 是调度真源；`.ai/config/*.yaml` 是 repo-owned runtime contract。
- `.ai/runs/<run_id>/<task_id>/` 是 task-level 正式证据；`docs/change-evidence/README.md` 是 repo-level 治理证据索引，二者不得混用。
- v3.23 候选正文、normative package inventory、v3 机器 work items 与 planning status 只定义目标和阶段门；v3.22 及其 planning artifacts 是 frozen superseded inputs。它们不得覆盖当前 runtime 数据契约或伪造实现证据。
- AgentBridge、adaptive overlay 和 experimental `runtime_v2` 继续按现有实现工作，但只作为 legacy/迁移输入，不驱动 v3.23 下一任务或证明新 baseline 已实现。
- `private-local/` 存本机 secret/探针且不提交；snapshot/Hermes 目录是历史兼容证据，不反转当前主线。

## B. 执行与风险边界
- P0A 默认落点仅限 `docs/specs/local-ai-runtime-0.2*`、`docs/plans/`、planning docs、verifier/tests 和 repo-level evidence；不得修改 `.ai/config`、live state 或 legacy runtime 行为。
- 每个原子 closeout 只执行 `docs/plans/local-ai-runtime-0.2-work-items.json` 中 selector 指向的唯一 selectable 任务；该项验收、验证、evidence、状态同步、本地提交和 clean-worktree 均闭合后，同一 session 才可重新运行 selector 并顺序继续。`planning_optimization_policy` 默认每次 bounded run 最多闭合 3 项或运行 180 分钟，任一失败、预算耗尽、阶段/批准边界、v3.23 successor、live/auth/provider/remote/破坏性边界立即停止。
- BaselineApprovalRecord、ImplementationAcceptanceRecord 和 FullQ0Record 只能在对应工作项、全部前置证据与明确授权下创建；AI 不得自签或用 fixture/simulation 代替。
- live probe、auth/provider、本机凭据和历史兼容运行态属于中高风险；先 dry-run、说明影响与回滚。
- README/docs/PRD/roadmap/plan/backlog 与 planning status 不一致时先阻断并收口事实。
- 不把本仓改造成治理中枢，不盲吸收外部控制面机制；高漂移机制先做 companion/reference 比对。

## C. 门禁、证据与回滚
- fixed order：`build -> test -> contract/invariant -> hotspot`。
- agent-rule contract CI：`.github/workflows/agent-rule-contract.yml` 只验证规则契约，不替代本仓产品门禁。
- build：`gate_na`，`reason=当前切片是 candidate planning 且新包尚不存在`、`alternative_verification=uv run --project ./runtime/host-orchestrator python -m pytest`、`evidence_link=docs/specs/acceptance-and-gates.md`、`expires_at=LAR-P0D-001`。
- test：`uv run --project ./runtime/host-orchestrator python -m pytest`
- contract/invariant：`python scripts/verify-planning-status.py`
- hotspot：`gate_na`，`reason=当前切片不改 runtime hot path`、`alternative_verification=planning tests + verifier + selector + git diff --check`、`evidence_link=docs/specs/acceptance-and-gates.md`、`expires_at=first executable slice after LAR-P0D-001`。
- quick：`python scripts/select-next-work.py`；release-style：`pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit`。
- 触及 `snapshots/agentbridge-20260628/` 或 Hermes 兼容面时，补跑该目录的 contract/bringup/known-good/boundary 脚本。
- 证据：repo-level 写 `docs/change-evidence/`，task-level 写 `.ai/runs/<run_id>/<task_id>/`；记录命令、exit code、关键输出、兼容、N/A 和回滚。
- 回滚只撤销本任务项目规则/代码/证据 diff；控制仓或用户级副本不因本仓回滚而自动恢复。

## D. Global Rule -> Repo Action
- `R1-R5`：先由 planning status/selector 确认唯一 selectable task；批准前不新增 runtime，后续只按 machine work item 的范围和回滚切片执行。
- `R6`：C 章顺序不变，build/hotspot 缺口按完整 N/A 留痕。
- `R7`：保护已验证的 v3.17、两份 v3.18、v3.19、v3.20、v3.21、v3.22 archive bytes/hash、冻结 v3.23 candidate bytes/hash、artifact/approval/plan generations、task/result/review、AgentBridge、`.ai` 真源与历史 snapshot 边界。
- `R8`：严格区分 repo-level 与 task-level evidence，并写明回滚。
- `E4`：planning status/selector/preflight 承接健康但不替代三层批准门；`E5`：高漂移依赖先做 reference 比对；`E6`：contract/schema/runtime 变化同步 migration、compat、rollback 和新 generation。
