# AGENTS.md - Local AI Runtime
**项目契约**: 2.0
**全局规则复核**: 9.55
**仓库目录**: local-ai-dev-orchestrator
**最后更新**: 2026-07-10

## 1. 当前落点与目标归宿
- 当前落点：产品主线是 Hermes -> AgentBridge -> Codex；canonical JSON/YAML intake、`result.json` 与 compatibility projection 仍是当前运行事实。
- 目标归宿：在 `runtime/host-orchestrator` 形成可审计本地运行时，按 Phase 1 -> Phase 6 推进；Governance Overlay 只作横切治理，不替代产品路线图。
- 下一最小里程碑：执行 `docs/architecture/planning-status.json` 的 `PHASE-1-VERTICAL-SLICE` active queue，不把未接线目标态写成已完成。

## A. 仓库事实与模块边界
- `runtime/host-orchestrator` 是 `host_local` 可信内核；禁止新建平行顶层 orchestrator 包。
- `.ai/state/control-plane.db` 是调度真源；`.ai/config/*.yaml` 是 repo-owned runtime contract。
- `.ai/runs/<run_id>/<task_id>/` 是 task-level 正式证据；`docs/change-evidence/README.md` 是 repo-level 治理证据索引，二者不得混用。
- AgentBridge 是跨层唯一文件契约；AgentBridge-first intake 尚未全部接线，不得把 compatibility projection 写成 canonical truth。
- adaptive overlay 默认 `observe_default`；guarded 只经显式 experimental `runtime_v2` 入口，不改变默认 v1/active queue/live accepted。
- `private-local/` 存本机 secret/探针且不提交；snapshot/Hermes 目录是历史兼容证据，不反转当前主线。

## B. 执行与风险边界
- 默认落点仅限当前 slice 需要的 `runtime/host-orchestrator`、`docs/`、`.ai/config/`、`scripts/` 或明确历史兼容面。
- live probe、auth/provider、本机凭据和历史兼容运行态属于中高风险；先 dry-run、说明影响与回滚。
- README/docs/PRD/roadmap/plan/backlog 与 planning status 不一致时先阻断并收口事实。
- 不把本仓改造成治理中枢，不盲吸收外部控制面机制；高漂移机制先做 companion/reference 比对。

## C. 门禁、证据与回滚
- fixed order：`build -> test -> contract/invariant -> hotspot`。
- agent-rule contract CI：`.github/workflows/agent-rule-contract.yml` 只验证规则契约，不替代本仓产品门禁。
- build：`gate_na`，`reason=当前主线无独立 build gate`、`alternative_verification=uv run --project ./runtime/host-orchestrator python -m pytest`、`evidence_link=docs/specs/acceptance-and-gates.md`、`expires_at=next_executable_change`。
- test：`uv run --project ./runtime/host-orchestrator python -m pytest`
- contract/invariant：`python scripts/verify-planning-status.py`
- hotspot：`gate_na`，`reason=当前主线无独立 hotspot gate`、`alternative_verification=verifier + pytest + git diff --check`、`evidence_link=docs/specs/acceptance-and-gates.md`、`expires_at=next_executable_change`。
- quick：`python scripts/select-next-work.py`；release-style：`pwsh scripts/governance/preflight.ps1 -DisableAutoCommit`。
- 触及 `snapshots/agentbridge-20260628/` 或 Hermes 兼容面时，补跑该目录的 contract/bringup/known-good/boundary 脚本。
- 证据：repo-level 写 `docs/change-evidence/`，task-level 写 `.ai/runs/<run_id>/<task_id>/`；记录命令、exit code、关键输出、兼容、N/A 和回滚。
- 回滚只撤销本任务项目规则/代码/证据 diff；控制仓或用户级副本不因本仓回滚而自动恢复。

## D. Global Rule -> Repo Action
- `R1-R5`：先定当前主线落点/目标/slice；历史止血写回收点，不新增平行 runtime 或治理 hub。
- `R6`：C 章顺序不变，build/hotspot 缺口按完整 N/A 留痕。
- `R7`：保护 task/result/review、AgentBridge、`.ai` 真源与历史 snapshot 边界。
- `R8`：严格区分 repo-level 与 task-level evidence，并写明回滚。
- `E4`：planning status/selector/preflight 承接健康；`E5`：高漂移依赖先做 reference 比对；`E6`：contract/schema/runtime 变化同步代码、文档、迁移和回滚。
