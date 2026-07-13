# Local AI Runtime 0.2 路线图

## 状态

当前 baseline `local-ai-runtime-0.2-v3.23` 未批准。冻结正文与 v3.23-bound lineage、manifest schema/fixtures/verifier skeleton 和 `CanonicalizationPolicy.v1` 已完成，但最终 manifest 仍不存在，规范包仍为 `15 required / 3 present / 12 missing`。`LAR-P0A-EVAL-002` 已完成固定比较并记录 `preserve_v3_23_semantics`；路线图下一步是 `LAR-P0A-004` product/submission contract slice。不把评测结果、历史 `PHASE-1-VERTICAL-SLICE`、experimental runtime_v2 或 legacy probe 当作新实现完成证据。

## 总依赖链

```text
Native thin-path / capability comparative evaluation
 -> P0A Normative Package Closure
 -> Baseline Approval
 -> P0B Truth Reset
 -> P0C Legacy Ownership Guard
 -> P0D Isolated Package/Harness
 -> P1 Implementation
 -> Implementation Acceptance
 -> Full Q0
 -> P2 One Pilot
 -> P3 Five Scheduled Self-host Tasks
 -> P4 under B2: Two Repos + 30-task Cohort
    -> P4-002 Activate B3 Portfolio Generation
    -> P5 Per-repo Cutover + Legacy Retirement
```

每个箭头是硬门，不能以文档、fixture、simulation、legacy evidence 或人工口头判断替代。

Baseline Approval 由独立人工治理工作项 `LAR-GOV-001` 执行；它不与 P0A review 或 P0B Truth Reset 合并。

执行节奏由现有 machine plan 的 `same_run_reselect_after_verified_atomic_closeout` 控制：每次 selector 仍只返回一个 work item，但一个 bounded run 可在该项 evidence/commit/status/clean-worktree 闭合后重新 selector，默认最多 3 项或 180 分钟。它不新增 roadmap 阶段、不改变 DAG 顺序；阶段/批准、successor、live/auth/provider/remote/破坏性边界和任一失败都停止。

## P0A：规范包闭包

目标：把完整 prose candidate 变成可以批准和实现的机械 contract package。

工作项：已完成 `LAR-P0A-001`、`LAR-P0A-REBASELINE-V322`、`LAR-P0A-REBASELINE-V323`、`LAR-P0A-EVAL-001`、`LAR-P0A-EVAL-002`、`LAR-P0A-002` 和 `LAR-P0A-003`；评测决定为 `preserve_v3_23_semantics`，当前唯一 selectable 项为 `LAR-P0A-004`。`LAR-P0A-004` 至 `LAR-P0A-013` 继续按 DAG 闭合；后续若出现规范语义变化，仍须创建 successor，不能改写 v3.23。

交付：

- 版本谱系、v3.17 exact-byte archive、两份 conflicted v3.18、精确 v3.19-v3.22 archives 与冻结 v3.23 identity；
- 固定 snapshot、TaskFamily、model/effort、tool inventory、sandbox、gates、人工介入定义的 Native thin-path 比较，及 CLI、App Server、SDK、managed Worktree、Automations 的独立 capability probe；
- narrative/artifact/package 三层版本语义、manifest schema/byte verifier，以及 P0A-013 冻结 `package_review_head` 后一次性生成的最终 BaselineManifest；
- WorkDefinition/TaskFamily/EffectPlan/GateGraph、canonicalization/path/alias、永久 submission replay、qualification/auth、writer effect/launch identity、execution-authority/fencing、durable operator inbox、Git hybrid、state/guard、Q0TriggerPolicy、write-accounting/optional-quota bundles；
- 所有 schema、catalog、transition row、positive/negative examples、crash/limit fixtures；
- standalone baseline verifier；
- append-only ReviewEvidenceIndex、preliminary consistency review、manifest-closure review 与 `approval_review_head` 后继证明。

出口：Native thin-path 评测具有可审计结果，且若继续 v3.23 必须为 `preserve_v3_23_semantics`；package inventory 零 missing，verifier 绿色，P0/P1 规范 finding 为零，`approval_eligible=true`。Baseline Approval 仍需独立授权记录。

## P0B：Truth Reset

工作项：`LAR-P0B-001`。

入口：active、未撤销、hash 匹配的 BaselineApprovalRecord。

动作：原子同步 AGENTS、README、PRD、architecture、roadmap、plan、backlog、acceptance、planning status、selector/verifier 和 evidence index。队列切为 `MINIMUM-OPERATOR-COMMIT-ONLY-TRANSITION`，selector 切为 `implement_legacy_guard_first`。

出口：所有 authoritative surfaces 指向同一 approved generation；现有 runtime 仍是当前可执行真值，新包仍未 claim。

## P0C：Legacy Ownership Guard

工作项：`LAR-P0C-001` 至 `LAR-P0C-003`。

目标：在新 runtime 出现前，先关闭 legacy/new 双 writer 风险。

- 定义共享 ownership wire、SID/repo identity 和 mutex/SDDL。
- 枚举并守卫 legacy claim、lease、worktree、executor、writer、repo mutation、Git、commit、closeout、cleanup。
- 注册现有 repo 为 legacy owner。
- 完成 cross-runtime conformance、crash/takeover、cutover/rollback drill。

出口：不存在未守卫副作用入口；新 claim 仍关闭。

## P0D：独立包和验收 harness

工作项：`LAR-P0D-001`。

目标：创建 `runtime/local-ai-runtime` 的 Python 3.11.x 模块化单体，具体 patch 由 `RuntimeToolchainManifest` 锁定；建立 offline lock/build/test/contracts/ruff/pyright 门，禁止 import `host_orchestrator`，禁止执行 Batch。

源码布局同时成为机械出口：`approved_root_files=["__init__.py","__main__.py"]`；`approved_subpackages=["contracts","kernel","qualification","storage","execution","recovery","git_local","operations","compat"]`；`required_source_owners` 固定 bootstrap/marker 的唯一任务。P0D 只创建包根 marker、薄 contracts-verifier bootstrap 和 harness；后续每个子包的首个实现任务创建其 `__init__.py`，所有功能模块必须位于批准子包内。

出口：纯 scaffold 和 approved contracts 可离线验证。

## P1：实现

机器图总计 65 项；下表 P1A-P1F 合计 35 个 AI 编码切片，使用确定性 DAG。独立验证分支可以并行准备；每个原子 closeout 只关闭 selector 指向的唯一任务，闭合后才可在同一 bounded run 继续，且 Epoch 1 真实 writer capacity 始终为 1。

| 阶段 | 工作项 | 交付 | 关键出口 |
|---|---|---|---|
| P1A | `LAR-P1A-001` 至 `LAR-P1A-004` | canonical/path primitives、typed schemas、state/guard、cross-contract verifier | fixtures 全闭合、未知组合 exit 2 |
| P1B | `LAR-P1B-001` 至 `LAR-P1B-005` | SQLite/migration、submission、lease/fence、journal/outbox、storage crash replay | migration/rollback、CAS、response-loss 绿色 |
| P1C | `LAR-P1C-001` 至 `LAR-P1C-007` | install/activation、toolchain/env、repo/Auth、sandbox、write accounting/reserve、offline Q0、adapter no-write smoke | isolated-root/resource/qualification/adapter probes 绿色 |
| P1D | `LAR-P1D-001` 至 `LAR-P1D-006` | named Job、writer launch、StageJob authority、stream/journal、recovery、gate runner | at-most-once、handle/EOF、revoke/safety、crash matrix 绿色 |
| P1E | `LAR-P1E-001` 至 `LAR-P1E-007` | Git audit、worktree/mutation、hybrid objects、finalize/ref、artifact/evidence、cleanup/backup、provider-free rehearsal | deterministic closeout 与 anti-rollback restore 绿色 |
| P1F | `LAR-P1F-001` 至 `LAR-P1F-006` | CLI、Batch commands、scheduler、managed Native、operator/runbooks、compat/eval | stable JSON/exit/reason，所有 dry-run 零 live 副作用 |
| P1G | `LAR-P1G-001` | Implementation Acceptance | 全 offline gate 和 drill 绿色；P2 仍阻断 |

## Q0：真实平台资格化与 P2 Admission

工作项：`LAR-Q0-001`。

入口：Implementation Acceptance active。只运行 staged install/Codex/Git/Windows/sandbox/adapter/model/profile/keyring/network/filesystem probes；禁止 writer。按非循环 `C -> I -> Q -> B -> A` 链完成 pointer CAS 和 immediate preflight，只有 terminal `ActiveRuntimeIdentity` 才打开 P2 Admission。

出口：FullQ0Record 可验证、P2 admitted、仍无 writer/task ref。

## P2：单个 pilot

工作项：`LAR-P2-001`。

入口：Full Q0/P2 Admission active + repo/template qualification + Authorization。

范围：一个 low-risk self-host task，人工显式启动，B1，commit-only，不 scheduled、不 merge/push。

出口：commit-ready、evidence verify、所有安全硬门为零、无悬挂恢复状态。

## P3：五个 scheduled self-host

工作项：`LAR-P3-001`。

范围：一个 promoted template，B2，全局单 writer，5 个 scheduled observations。

出口：5 个 commit-ready、零 unresolved state、完整 OperatorWorkSession 计量。

## P4：真实 repo cohort

工作项：`LAR-P4-001`，之后并列后继为 `LAR-P4-002` 和 `LAR-P5-001`。

范围：Autonomy 保持 B2/per-repo，至少两个 target repo、self-host，总计 30 个 observation；最多 5 probe-only、至少 25 commit-ready；另做至少 12 个严格配对效率 case。每条记录标记 `evidence_scope=declared_profile_pilot`。`commit-ready` 不能单独构成长期质量：每个 promotion cohort 必须抽样附回 `DownstreamOutcomeRecord`，覆盖 human review disposition、merge/reject/rework、后续 CI、revert 或 defect evidence；`censored|unknown` 留在分母且不算 pass。

出口：安全硬门零；无人值守 >=80%；人工介入 <=20%；mandatory gates/evidence/backup/recovery=100%；净人工分钟/成功下降 >=50%；抽样 `DownstreamOutcomeRecord` 无质量下降结论且 unknown/censored 分母可见；无 unresolved state。

`LAR-P4-002` 仅在上述出口全绿后，通过受控 operator action 激活一个 data-only `portfolio_data_only_v1` AutonomyPolicy/Authorization generation。Repo 只能提供 qualification-bound、content-addressed、closed-schema backlog snapshot，不执行 repo selector code。B3 激活失败不否定 cohort，也不阻断独立 P5。

## P5：逐仓切换和退休

工作项：`LAR-P5-001`。

每 repo：maintenance/drain -> zero active -> backup -> rollback drill -> ownership generation CAS -> verify -> observe。失败只回滚该 repo。

全部 repo cutover 且 legacy zero active/closing 后，legacy DB 只读。连续 30 天零 legacy 调用后移除写面；compat reader、历史 evidence 和 task refs 永久保留。

## 升级规则

- B0：contracts/doctor/prepare。
- B1：单个人工启动 pilot。
- B2：promoted template 的单项 scheduled drain。
- B3：多个 qualified repo 的 data-only portfolio selection；全局 capacity 仍为 1。

Profile generation、capability generation、architecture epoch 是不同升级层；运行时只激活一个完整 bundle。升级不扩大 Batch 禁止边界，必须由静态 generation、qualification、Authorization 和阶段验收激活。CLI/SDK execution interface、App Server client protocol、managed Worktree isolation、Automations scheduling 各自是独立 capability generation。任何安全/gate失败、新失败类型、新人工介入或 profile 归因成功率下降立即停止新 claim。跨 repo 多 writer 不是 CapacityProfile 开关，而是 successor architecture epoch。
