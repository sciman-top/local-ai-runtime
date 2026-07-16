# Local AI Runtime

Local AI Runtime 的目标是把 Windows 本机 AI 开发从“会调用模型”提升为“能低人工、可预测、可恢复地交付本地 commit”。产品采用 Unified Native + Batch：Native Direct/Spec/Program 负责低延迟探索、澄清和模板候选；Batch 只执行已资格化的封闭模板，固定全局 `capacity=1`、deterministic commit-only，不 merge/push。

## 当前真值

当前规范候选是 `local-ai-runtime-0.2-v3.25`，状态为 `baseline_candidate`，`blocking_stage=baseline_approval`。它因 v3.24 要求 Windows 无法提供的 pre-resume child environment observation，且使用不存在的 exact-option sync spelling 而成为最小 successor。v3.24 candidate、preapproval inventory 和 machine plan 已按精确 byte/hash 归档，不能改写；产品范围、首发体验与总体架构不扩张。

规范包当前为 `15 required / 9 present / 6 non-present`，因此仍是 **Request changes**：

- present：v3.25 source、`BaselineLineage.v4`，以及从 v3.24 明确 byte/hash carry-forward 的 `CanonicalizationPolicy.v1`、`ProductContract.v2`、`QualificationContractSet.v2`、`ExecutionSafetyContractSet.v1`、`EvidenceContractSet.v1`、`DeterministicGitContractSet.v1`、`StatePolicyCatalog.v1`；
- present：`ProductContract.v2` 已固定十步 first-run journey、四个 launch templates、catalog-only human/JSON projection 与产品指标分母；
- present：`QualificationContractSet.v2` 已固定 exact/no-download/manifest-Python/hash-pinned-build/clean-root-repeatability contract；
- present：`StatePolicyCatalog.v1` 已固定七个独立状态域、83 条 transition、91 个 guards、确定性 recovery、不可绕过 cleanup finalizer 与 16 个 durable operator actions；
- non-present：Q0/migration/examples/verifier/final manifest/review；
- Baseline Approval、Truth Reset、`runtime/local-ai-runtime`、Implementation Acceptance、Full Q0、P2 和 rollout 全部未发生。

机器真值是 [planning-status.json](D:/CODE/local-ai-dev-orchestrator/docs/architecture/planning-status.json)。当前队列为 `LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE`，唯一工作项为 `close_baseline_normative_package_first / LAR-P0A-010`。它只创建 Q0/gate/feature/process/resource-limit catalogs 与 fixtures，不运行 live Q0、不实现 runtime、不触碰 live state。

稳定 [baseline candidate entry](D:/CODE/local-ai-dev-orchestrator/docs/specs/local-ai-runtime-0.2-baseline-candidate.md) 只是 `role=non_normative_navigation`、`approval_input=false` 的导航页，不是第二份规范、manifest 输入或批准证据。

## 首发产品体验

预资格化主机上的首条可用路径固定为：

1. `doctor --json`：证明 uv/Python/toolchain、Windows primitive、磁盘和秘密边界可用；
2. `repo qualify <path> --json`：只读建立 repo identity、policy generation 与 qualification evidence；
3. `template list/show`：只显示已批准模板、封闭参数、path/effect envelope、required/forbidden gates；
4. `batch dry-run --template ...`：输出 canonical `WorkDefinition`、effect preview、预计 gates、停止/回滚条件，不 claim、不写 repo；
5. `batch submit --confirm <challenge>`：仅在 qualification + Authorization + anti-replay challenge 成立后入队；
6. `status/action/evidence show`：人类文本由公开 machine state 目录化渲染，同时提供稳定 JSON；blocked/suspended 总有一个 durable operator action。

首发只提供四类高频、可机械约束的 template：

- `docs_contract_sync_v1`
- `bounded_lint_type_repair_v1`
- `focused_test_repair_v1`
- `mechanical_repo_maintenance_v1`

自由 prompt、动态命令、依赖安装、remote effect、自动模板 promotion 均不属于 Batch。Native Spec 只能产出候选；promotion 必须是受控 operator action，并重新资格化 generation。

## 工程终态与技术栈

0.2 的推荐终态是 Windows-local Python modular monolith，而不是微服务或第二个 planner/router：

- Python 3.11.x patch、uv executable、lockfile、installed distributions、pytest plugins 与 build backend 都由 `RuntimeToolchainManifest` 固定；
- `runtime/local-ai-runtime/src/local_ai_runtime/` 只允许 `__init__.py`、薄 `__main__.py` 和 `contracts/kernel/qualification/storage/execution/recovery/git_local/operations/compat` 九个子包，`required_source_owners` 一对一；
- SQLite 是唯一 policy/transition authority；append-only journal 是 observation、recovery 和 audit input，不是第二状态机；
- Windows Job Object、suspended launch、显式 handle list/stdio、fence/adoption 和 cleanup finalizer 控制进程副作用；
- Git 只物化 canonical local objects、single-parent execution commit 与 task ref，禁止 merge/push；
- evidence 使用结构化 event/receipt/artifact、secret-safe projection、外置大对象和 purpose-separated key envelope；
- Windows Task Scheduler 只触发受控入口；调度权仍在 SQLite state/guard policy；
- global writer capacity 固定为 1。B3 portfolio scheduling、multi-writer、remote/distributed runtime、SDK/App Server/managed Worktree/Automations 均 deferred beyond 0.2。

该架构对当前约束是更优解：单机单操作者无需分布式一致性成本；模块化单体保留清晰边界且便于一次性 transaction/recovery；CLI + JSON 可同时服务操作者和自动化；封闭模板让权限、证据、回滚和产品指标可验证。它不是“全场景最优”：若未来需要多机、多租户或并行 writer，应通过 architecture epoch successor 重新设计，而不是在 0.2 内预埋分布式抽象。

## 精确工具链门禁

P0D 起使用 machine profile `new_runtime_exact_v1`：

- 环境准备显式运行 `uv sync --locked --offline --no-python-downloads --python <manifest-python>`；`uv sync` 默认 exact，禁止 `--inexact`，且准备步骤不是验证 gate；
- 日常 gate 使用 `uv run --no-sync --offline --no-python-downloads --python <manifest-python>`，禁止隐式 sync/download/PATH fallback；
- build 使用 manifest-bound `--build-constraint <hashed-file> --require-hashes`；
- 子进程回读 `sys.executable`、patch、distribution、plugin 与 backend 身份；
- 两个 clean roots 在相同 `SOURCE_DATE_EPOCH` 下必须产出相同 member manifest 和 artifact hashes；
- 固定门序：`supply_chain_identity -> build -> test -> contract_invariant -> hotspot`。

## 路线与并行边界

P0A 关闭 normative package；独立授权后 P0B Truth Reset。P0B 完成后，P0C legacy ownership guard 与无副作用 P0D scaffold 可并行准备；P1 必须等待二者全部闭合。之后依次为 Implementation Acceptance、Full Q0/P2、single pilot、五次 scheduled self-host、30-task/two-repo P4 cohort、逐仓 P5 cutover。B3 不在 0.2 work-item graph 中。

机器图是 `local_ai_runtime_work_items.v4` 的 52 项 deterministic DAG、11 项 closed contract projections。顶层 `planning_optimization_policy` 规定 `one_selector_selected_work_item`：每项必须 acceptance、verification、evidence、status、一个 local commit 和 clean worktree 全闭合，才能同一 run 重新 selector；默认最多 3 项或 180 分钟，任何失败、阶段/批准、successor、live/auth/provider/remote/破坏性边界停止。

## 权威阅读顺序

1. [planning status](D:/CODE/local-ai-dev-orchestrator/docs/architecture/planning-status.json)
2. [v3.25 candidate](D:/CODE/local-ai-dev-orchestrator/docs/specs/local-ai-runtime-0.2-v3.25-baseline-candidate.md)
3. [normative inventory](D:/CODE/local-ai-dev-orchestrator/docs/specs/local-ai-runtime-0.2-normative-package.json)
4. [machine work items](D:/CODE/local-ai-dev-orchestrator/docs/plans/local-ai-runtime-0.2-work-items.json)
5. [PRD](D:/CODE/local-ai-dev-orchestrator/docs/product/orchestrator-prd.md) 与 [target architecture](D:/CODE/local-ai-dev-orchestrator/docs/architecture/orchestrator-target-architecture.md)
6. [roadmap](D:/CODE/local-ai-dev-orchestrator/docs/roadmap/orchestrator-roadmap.md)、[implementation plan](D:/CODE/local-ai-dev-orchestrator/docs/plans/orchestrator-implementation-plan.md)、[task list](D:/CODE/local-ai-dev-orchestrator/docs/backlog/orchestrator-task-list.md)
7. [acceptance and gates](D:/CODE/local-ai-dev-orchestrator/docs/specs/acceptance-and-gates.md)

## 当前检查

```powershell
uv run --project ./runtime/host-orchestrator python -m pytest
python scripts/verify-planning-status.py
python scripts/select-next-work.py
pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit
git diff --check
```

planning gate 绿色只证明控制面内部一致，不等于 Baseline Approval；Baseline Approval 不等于 Implementation Acceptance；Implementation Acceptance 不等于 Full Q0/P2；fixture、simulation、predecessor evaluation 和 legacy evidence 都不能替代新 runtime 的真实门禁。
