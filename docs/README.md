# Local AI Runtime 文档入口

## 规划真值

当前候选为 `local-ai-runtime-0.2-v3.24`，`blocking_stage=baseline_approval`。它是 v3.23 的 successor，不是已批准基线；原因是 predecessor gate 未证明 exact uv environment、manifest Python 与 hash-pinned build backend，且 launch product experience 不完整。v3.23 candidate/package/plan 仅作为冻结历史，Native thin-path comparative result 仅为 non-normative predecessor evidence。

当前 package 是 `8/15 present, 7 non-present`。`ProductContract.v2` 与 `QualificationContractSet.v2` 已创建并通过 component verifiers；state/Q0/migration/examples/verifier/final manifest/review 尚未闭合，`runtime/local-ai-runtime` 不存在。当前唯一 machine work item 是 `LAR-P0A-009`；selector action 是 `close_baseline_normative_package_first`。

`planning_optimization_policy` 使用 `one_selector_selected_work_item` 和 `same_run_reselect_after_verified_atomic_closeout`：一个 work item 必须 acceptance、verification、evidence、status、local commit、clean worktree 全闭合后，同一 run 才能继续；默认最多 3 个或 180 分钟，阶段/批准/successor/live 边界停止。

## 权威文档

| 文档 | 回答什么 | 不证明什么 |
|---|---|---|
| [planning-status.json](architecture/planning-status.json) | 当前 baseline/package/queue/work item/阶段门 | 产品语义本身 |
| [v3.24 candidate](specs/local-ai-runtime-0.2-v3.24-baseline-candidate.md) | 自包含目标语义、首发体验、架构和门禁 | 已批准或已实现 |
| [stable candidate entry](specs/local-ai-runtime-0.2-baseline-candidate.md) | 稳定发现路径与 exact target identity | normative input |
| [normative package inventory](specs/local-ai-runtime-0.2-normative-package.json) | 15 artifacts、carry-forward、缺口、approval eligibility | runtime completion |
| [machine work items](plans/local-ai-runtime-0.2-work-items.json) | 55 项 DAG、11 projections、AI scope/acceptance/gates/rollback | 自动授权跨阶段 |
| [PRD](product/orchestrator-prd.md) | 用户、目标、功能、首发流程、指标、非目标 | 组件实现细节 |
| [target architecture](architecture/orchestrator-target-architecture.md) | 模块、数据、信任、状态、进程、Git、迁移 | 当前代码已存在 |
| [roadmap](roadmap/orchestrator-roadmap.md) | P0A-P5 阶段和 join/barrier | 单 task 精确写集 |
| [implementation plan](plans/orchestrator-implementation-plan.md) | AI 执行协议、工程拆分和 closeout | machine plan 的替代品 |
| [task list](backlog/orchestrator-task-list.md) | 可读状态和下一步 | 机器状态真源 |
| [acceptance and gates](specs/acceptance-and-gates.md) | Baseline/Implementation/Q0/rollout 与 exact gate 口径 | 授权记录本身 |

## 产品与工程摘要

目标是 Windows-local、single-operator 的 Unified Native + deterministic commit-only Batch。首发 CLI 旅程为 `doctor -> repo qualify -> template list/show -> batch dry-run -> submit -> status/action -> evidence show`；只提供四个闭合模板：`docs_contract_sync_v1`、`bounded_lint_type_repair_v1`、`focused_test_repair_v1`、`mechanical_repo_maintenance_v1`。Native Spec 只能创建 template candidate，promotion 需要受控 operator action。

目标技术栈是 Python 3.11.x modular monolith + uv exact offline environment + SQLite authority + append-only evidence/journal + Windows Job Object/process fencing + deterministic local Git objects/task refs + Windows Task Scheduler trigger。源码根只允许 `__init__.py`、`__main__.py` 与 `contracts/kernel/qualification/storage/execution/recovery/git_local/operations/compat`；`approved_root_files`、`approved_subpackages`、`required_source_owners` 由 machine plan/verifier 关闭。

新 runtime gate profile 为 `new_runtime_exact_v1`：环境准备 `uv sync --locked --offline --no-python-downloads --python <manifest-python>`，依赖 uv sync 默认 exact 并禁止 `--inexact`；验证使用 `run --no-sync`；build backend 用 `--build-constraint` 与 `--require-hashes`；固定门序为 supply-chain identity、build、test、contract/invariant、hotspot，并要求 clean-root repeatability。

SQLite 是唯一 policy/transition authority；journal 是观察/恢复输入，不可成为第二状态机。global writer capacity=1。B3 portfolio scheduling、multi-writer、remote/distributed runtime、SDK/App Server/managed Worktree/Automations deferred beyond 0.2。

## 当前与目标边界

- 现行可执行内核仍是 `runtime/host-orchestrator`；`.ai/state/control-plane.db` 与既有 evidence 仍是 runtime truth。
- v3.24 只定义目标；P0A 完成后仍需显式 Baseline Approval。
- P0B Truth Reset 后，P0C legacy guard 与 no-side-effect P0D scaffold 可并行；P1 等待二者。
- Implementation Acceptance、Full Q0/P2、P2/P3/P4 evidence、P5 per-repo cutover 缺一不可。
- `complexity_health=warning_all_dimensions` 仍保留：权威面数量固定 14，machine plan 55 项、projection 11、artifact 15；后续新增机制必须替换既有面或创建 successor，并优先删除重复逻辑。

## 快速核验

```powershell
python scripts/verify-planning-status.py
python scripts/select-next-work.py
uv run --project ./runtime/host-orchestrator python -m pytest
pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit
git diff --check
```

通过 planning verifier 只代表文档、机器图、identity 和阶段组合一致；不代表 approval、runtime implementation、live provider 或 rollout 已完成。
