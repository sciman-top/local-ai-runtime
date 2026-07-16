# AGENTS.md - Local AI Runtime
**项目契约**: 2.0
**全局规则复核**: 9.57
**仓库目录**: local-ai-dev-orchestrator
**最后更新**: 2026-07-16

## 1. 当前落点与目标归宿
- 当前落点：`runtime/host-orchestrator`、`.ai/state/control-plane.db` 与既有 evidence 仍是唯一现行运行事实；`local-ai-runtime-0.2-v3.24` 只是 `baseline_candidate`，尚未批准、Truth Reset 或实现。
- 目标归宿：Baseline Approval 后按 v3.24 在 `runtime/local-ai-runtime` 实现 Windows-local、single-operator、Python 3.11.x modular monolith。产品面为 Unified Native Direct/Spec/Program + 全局 `capacity=1` 的 deterministic commit-only Batch；Native 负责低延迟意图形成，Batch 只消费已资格化的封闭模板并产出本地 commit/task ref，不 merge/push。
- 首发体验：预资格化主机上，操作者经 `doctor -> repo qualify -> template list/show -> batch dry-run -> batch submit -> status/action -> evidence show` 完成第一次安全提交；首发只提供 `docs_contract_sync_v1`、`bounded_lint_type_repair_v1`、`focused_test_repair_v1`、`mechanical_repo_maintenance_v1` 四个 launch templates。
- 下一最小里程碑：队列 `LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE` 的 `close_baseline_normative_package_first / LAR-P0A-004`，创建 v3.24-bound `ProductContract.v2`、first-run journey、launch template 与 operator presentation contracts。规范包为 `6/15 present, 9 non-present`；最终 manifest 仍不存在。
- v3.24 因 v3.23 无法证明 exact uv environment、manifest-selected Python、hash-pinned build backend，且 launch product experience 不完整而成为 successor。v3.23 candidate/package/plan 是精确 superseded inputs；Native comparative evaluation 仅作为非规范 predecessor evidence，不 promotion profile。
- 本次只是预批准 planning control-plane 重基线，不是 P0B Truth Reset；不得据此创建 approval、新 runtime、Batch claim 或 live evidence。任何 v3.24 冻结语义变更都必须创建 v3.25 successor。

## A. 仓库事实与模块边界
- `runtime/host-orchestrator` 是当前 `host_local` 可信内核；active Baseline Approval、Truth Reset 和 Legacy Ownership Guard 之前，禁止创建或激活 `runtime/local-ai-runtime`。
- `.ai/state/control-plane.db` 是现行 legacy 调度真源；`.ai/config/*.yaml` 是 repo-owned runtime contract。v3.24 target 的 SQLite/journal 规则尚未实现：SQLite 将是唯一 policy/transition authority，journal 只作 observation/recovery input。
- `.ai/runs/<run_id>/<task_id>/` 是 task-level 正式证据；`docs/change-evidence/` 是 repo-level 治理证据，二者不得混用。
- v3.24 candidate、normative inventory、v4 machine work items、planning status 与 selector 只定义目标和阶段门；它们不得覆盖当前 runtime 数据契约或伪造实现证据。
- carried-forward present artifacts 只有 `CanonicalizationPolicy.v1`、`ExecutionSafetyContractSet.v1`、`EvidenceContractSet.v1`、`DeterministicGitContractSet.v1` 四项；`ProductContract.v1` 与 `QualificationContractSet.v1` 不适用于 v3.24。
- 目标源码布局固定为 package root `__init__.py`/`__main__.py` 加 `contracts/kernel/qualification/storage/execution/recovery/git_local/operations/compat` 九个子包；`required_source_owners` 必须一对一，禁止新增隐式顶层模块。
- AgentBridge、adaptive overlay、experimental `runtime_v2`、Hermes/snapshot 只作 legacy/迁移输入；B3 portfolio scheduling、multi-writer、remote/distributed runtime、SDK/App Server/managed Worktree/Automations 均不属于 0.2 首发。

## B. 执行与风险边界
- P0A 落点仅限 `docs/specs/local-ai-runtime-0.2*`、planning docs、verifier/tests 与 repo-level evidence；不得修改 `.ai/config`、live state 或 legacy runtime 行为。
- 只执行 selector 指向的唯一 machine work item。acceptance、declared verification、evidence、status、一个可回滚 local commit 和 clean worktree 全闭合后，同一 session 才可重新 selector。`planning_optimization_policy` 默认最多 3 项或 180 分钟；失败、预算、阶段/批准、successor、live/auth/provider/remote/破坏性边界立即停止。
- BaselineApprovalRecord、ImplementationAcceptanceRecord、FullQ0Record 只能在对应工作项、全部前置证据和明确授权下创建；AI 不得自签或用 fixture/simulation 代替。
- P0B Truth Reset 后，P0C legacy guard 与无副作用 P0D package scaffold 可准备并行；P1 必须等待 P0C/P0D 两者闭合。无批准不得提前利用该并行结构。
- live probe、auth/provider、凭据、DPAPI、真实 Git publication 与历史兼容运行态属于中高风险；先 dry-run、影响和回滚。README/PRD/roadmap/plan/backlog 与 machine truth 不一致时先阻断。

## C. 门禁、证据与回滚
- planning fixed order：`build -> test -> contract/invariant -> hotspot`。build/hotspot 当前按 [acceptance-and-gates](docs/specs/acceptance-and-gates.md) 的完整 `gate_na` 记录；test=`uv run --project ./runtime/host-orchestrator python -m pytest`；contract=`python scripts/verify-planning-status.py`；quick=`python scripts/select-next-work.py`；release-style=`pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit`。
- 新 runtime 使用 `new_runtime_exact_v1`：显式 environment preparation `uv sync --exact --locked --offline --no-python-downloads --python <manifest-python>`；日常 gate 全部 `run --no-sync`；build 使用 manifest-bound `--build-constraint ... --require-hashes`；子进程回读解释器/distribution/plugin 身份；两次 clean-root build 对比 member manifest 与 artifact hash。
- 新 runtime 固定门序为 `supply_chain_identity -> build -> test -> contract_invariant -> hotspot`，每阶段都 fail closed；环境准备不是验证 gate，不得隐藏同步或下载。
- 证据记录命令、exit code、关键输出、输入身份、兼容、N/A、rollback；repo-level 写 `docs/change-evidence/`，task-level 写 `.ai/runs/...`。回滚只撤销本 task diff，不改写冻结 v3.23/v3.24 bytes 或既有 evidence。

## D. Global Rule -> Repo Action
- `R1-R5`：planning status/selector 定唯一任务；批准前不新增 runtime；按 machine scope、stop/prohibited/rollback 执行，拒绝预抽象和范围扩张。
- `R6`：门序固定；planning 的 build/hotspot 缺口按完整 N/A，P0D 起改用 `new_runtime_exact_v1` 真门禁。
- `R7`：保护 v3.17-v3.23 精确历史、冻结 v3.24、artifact/approval/plan generations、task/result/review、legacy compatibility、`.ai` 真源；B3 在 0.2 继续 deferred。
- `R8`：维护 `依据 -> 命令 -> 证据 -> 回滚`，严格区分 repo/task evidence。
- `E4`：status/selector/preflight 只承接健康，不替代批准门；`E5`：uv/Python/build/provider 等高漂移事实先查官方文档和本机 help；`E6`：contract/schema/runtime 变化必须同步 migration、compat、rollback 与新 generation。
