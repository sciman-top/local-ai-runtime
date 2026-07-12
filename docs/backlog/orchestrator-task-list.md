# Local AI Runtime 0.2 任务清单

## 使用规则

机器真源是 `docs/plans/local-ai-runtime-0.2-work-items.json`。本文件只作可读索引；状态、依赖、验收、命令、证据、回滚、停止条件和 prohibited actions 必须从机器真源读取。

当前：`local-ai-runtime-0.2-v3.22` 为 `baseline_candidate`；队列 `LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE`；唯一 ready 项 `LAR-P0A-003`。机器图是 `local_ai_runtime_work_items.v3` 确定性 DAG，共 62 项，其中 P1A-P1F 的 35 项是单次只领取一个的编码任务；顶层 11 项 contract projection 机械绑定规范 producer、实现 consumer 与 acceptance consumer。

目标源码使用关闭布局：`approved_root_files=["__init__.py","__main__.py"]`；`approved_subpackages=["contracts","kernel","qualification","storage","execution","recovery","git_local","operations","compat"]`；`required_source_owners` 固定 bootstrap/marker 的唯一任务。`__main__.py` 只转发 contracts verifier；任务若计划其他包根功能模块、第十个首级子包、重复源码 owner 或缺失 marker，planning verifier 必须先阻断。

状态含义：

- `[ ] ready`：当前唯一允许执行。
- `[ ] pending`：依赖未完成，不得提前做。
- `[!] blocked`：阶段门未通过。
- `[x] completed`：全部 acceptance 有证据且 verification 绿色。

## P0A：Normative Package Closure

- [x] `LAR-P0A-001` completed：从原始 session 归档 v3.17 exact bytes 和两份 conflicted v3.18，并完成 byte policy 与双路径 hash。
- [x] `LAR-P0A-REBASELINE-V322` completed：冻结 v3.22、重发 v3.22-bound lineage、终结 v3.21 plan identity 并切换 v3 machine DAG。
- [x] `LAR-P0A-002` completed：Narrative/artifact/package 三层版本语义、manifest schema、规范字节和 fail-closed verifier skeleton；最终 manifest 未创建，`P0A-MANIFEST` 保持 missing，`P0A-VERIFIER` 保持 in_progress。
- [ ] `LAR-P0A-003` ready：Canonical JSON、Git path、Windows identity/collision、alias-aware 8.3 与 `policy_query_denied` probe。
- [ ] `LAR-P0A-004` pending：Product/routing/template、`WorkDefinition`/`TaskFamily`、永久 ordinary replay、absent-only secret/admission、原子 resubmission。
- [ ] `LAR-P0A-005` pending：base-bound QualificationObservation、base-independent QualificationSensitiveInputSet、environment、opaque sandbox state/log、Authorization continuation、root/child effect grant。
- [ ] `LAR-P0A-006` pending：`EffectPlan`、`writer_effect_id`/`writer_launch_id`、Writer/StageJob、marker、JOB_LIST/HANDLE_LIST、精确 stdio/EOF、suspended execution barrier、Authorization/SafetyOnly authority union、fencing/adoption。
- [ ] `LAR-P0A-007` pending：event/status matrix、journal、receipt、artifact、runtime-managed external evidence、key envelopes、anti-rollback backup/restore。
- [ ] `LAR-P0A-008` pending：Git config/audit、`git_hybrid_materialization_v1`、claim time、no-reflog commit/finalize/ref/remove。
- [ ] `LAR-P0A-009` pending：SubmissionFamily/Task/Attempt/Platform/Repo/Template/Autonomy/Operator policies、durable action inbox、data-only portfolio。
- [ ] `LAR-P0A-010` pending：`GateGraph`、三级演进、`Q0TriggerPolicy`、activation admission、feature/process/gate、mandatory write accounting、emergency reserve、optional hard quota 和 resource-limit catalogs。
- [ ] `LAR-P0A-011` pending：cross-contract examples、negative/crash/limit fixtures。
- [ ] `LAR-P0A-012` pending：standalone normative package verifier 和 tamper tests。
- [ ] `LAR-P0A-013` pending：preliminary review -> 冻结 `package_review_head` -> 一次性最终 BaselineManifest -> manifest-closure review -> `approval_review_head` 后继证明与 approval readiness。

P0A 完成不自动批准。必须另有显式、append-only、可撤销/替代的 BaselineApprovalRecord。

## Governance Approval

- [!] `LAR-GOV-001` blocked by P0A review and explicit authority：通过 `BaselineApprovalCommandPolicy`、authority/session、expected generation 与 anti-replay challenge 批准或拒绝 v3.22；不得与 review、Truth Reset 或实现合并，AI 不得自签。

## P0B：Truth Reset

- [!] `LAR-P0B-001` blocked by Baseline Approval：同步 AGENTS/README/PRD/architecture/roadmap/plan/backlog/acceptance/planning/selector/verifier；切换到 `MINIMUM-OPERATOR-COMMIT-ONLY-TRANSITION` 和 `implement_legacy_guard_first`。

## P0C：Legacy Ownership Guard

- [!] `LAR-P0C-001` blocked：ownership wire、SID/repo identity/mutex/SDDL、legacy entrypoint inventory。
- [!] `LAR-P0C-002` blocked：在所有 legacy claim/lease/worktree/writer/Git/closeout/cleanup side effect 前接 guard。
- [!] `LAR-P0C-003` blocked：legacy/new conformance、concurrent claim、crash/takeover、cutover/rollback drill。

P0C 前新 Batch claim 始终禁止。

## P0D：Package Scaffold

- [!] `LAR-P0D-001` blocked：以 manifest 锁定 Python 3.11.x patch，创建 `runtime/local-ai-runtime`、包根 marker、薄 `__main__.py` contracts-verifier bootstrap 和 offline lock/build/test/contracts/ruff/pyright harness；不执行 writer，不 import legacy，不创建其他包根功能模块。

## P1：Implementation

- [!] `LAR-P1A-001` blocked：canonical bytes/hash、Git path 和 Windows collision/alias primitives。
- [!] `LAR-P1A-002` blocked：immutable schema registry、typed contract models、positive/negative fixtures。
- [!] `LAR-P1A-003` blocked：state/guard/operator catalog evaluator、唯一 row、Guard DAG、unknown exit 2。
- [!] `LAR-P1A-004` blocked：cross-contract policy bundle、foreign ID/hash、limit 与 execution-authority union verifier。
- [!] `LAR-P1B-001` blocked：SQLite bootstrap、approved schema、forward/rollback/interrupted migration。
- [!] `LAR-P1B-002` blocked：submission family permanent replay 与 atomic `TaskResubmission`。
- [!] `LAR-P1B-003` blocked：lease/fence、grant/revoke、fenced action/continuation CAS repositories。
- [!] `LAR-P1B-004` blocked：event/journal cursor、outbox/artifact/receipt metadata，DB 不领先 flush。
- [!] `LAR-P1B-005` blocked：persistence failpoint、tamper audit 与 response-loss matrix。
- [!] `LAR-P1C-001` blocked：在 `operations/installer.py` 与 `operations/activation.py` 实现 content-addressed install、activation CAS 与 compatible rollback，并首次创建 `operations/__init__.py`。
- [!] `LAR-P1C-002` blocked：pinned toolchain 与 immutable qualified environment binding。
- [!] `LAR-P1C-003` blocked：repo/template qualification、global AuthState、Authorization/revoke。
- [!] `LAR-P1C-004` blocked：untrusted overlay、effective config/tool inventory、opaque sandbox state/log。
- [!] `LAR-P1C-005` blocked：mandatory `accounting_kill_audit`、emergency reserve、optional quota interface。
- [!] `LAR-P1C-006` blocked：Full/quick/daily offline Q0 probe dispatcher 与 immutable report。
- [!] `LAR-P1C-007` blocked：Codex CapabilityAdapter 与 `adapter_no_write_smoke_v1`；无 task、writer grant/process、Git publication 或 raw model evidence。
- [!] `LAR-P1D-001` blocked：named mutex/Job identity、SDDL/limits/process-list 与 same-name fail closed。
- [!] `LAR-P1D-002` blocked：attempt environment、durable writer marker、稳定 effect/attempt launch identity、JOB_LIST/HANDLE_LIST suspended launch 与 resume barrier。
- [!] `LAR-P1D-003` blocked：StageJob、exact stdio/ChildHandleManifest、root/inherited/safety authority。
- [!] `LAR-P1D-004` blocked：bounded pipe drain、EOF/framing 分类、normalized events 与 segment journal。
- [!] `LAR-P1D-005` blocked：takeover、adoption、Authorization continuation、recovery priority/handoff。
- [!] `LAR-P1D-006` blocked：catalog-exact offline gate runner、bounded reports、deadline/limit+1。
- [!] `LAR-P1E-001` blocked：repo/common-dir identity、Git config/attribute/hook/driver/protected-surface audit。
- [!] `LAR-P1E-002` blocked：fenced worktree/checkout、root identity、mutation/secret/protected closure。
- [!] `LAR-P1E-003` blocked：controller canonical payload/expected OID、pinned Git materialization/read-back、deterministic commit、canonical promotion/reachability。
- [!] `LAR-P1E-004` blocked：finalize index -> detached HEAD -> task-ref 三步 CAS publication。
- [!] `LAR-P1E-005` blocked：artifact、`runtime_external_v1` evidence、six-condition receipt 与 no-hash-cycle closeout。
- [!] `LAR-P1E-006` blocked：safe cleanup、quiescent backup、key envelopes、anti-rollback isolated restore drill。
- [!] `LAR-P1E-007` blocked：provider-free `fixture_closeout_rehearsal_v1`，覆盖 GateGraph、Git hybrid、ref/evidence/cleanup，全程 fixture-only。
- [!] `LAR-P1F-001` blocked：在 `operations/cli.py` 与 `operations/cli_output.py` 实现 strict command tree、stable JSON envelope、exit/reason mapping；禁止回到包根创建 CLI 模块。
- [!] `LAR-P1F-002` blocked：Batch prepare/submit/status/cancel/retry/reconcile/resolve/doctor handlers。
- [!] `LAR-P1F-003` blocked：single-capacity recovery-first scheduler、parking/dedupe、data-only portfolio selection、task definition dry run。
- [!] `LAR-P1F-004` blocked：managed Native maintenance 与 intent-before-termination emergency kill。
- [!] `LAR-P1F-005` blocked：OperatorAction/WorkSession、`durable_local_status_v1`、optional qualified toast、runbooks、人工分钟计量。
- [!] `LAR-P1F-006` blocked：read-only compat、cutover/rollback dry run、paired/cohort evaluation；不执行 live cutover/cohort。
- [!] `LAR-P1G-001` blocked：冻结 `RuntimeCompositionManifest C`，运行全 offline gates、crash/conformance/migration/restore，创建 `ImplementationAcceptanceRecord I(C)`。

`LAR-P1G-001` 完成后仍不得进入 P2；Full Q0 是独立门。

## Q0 与 P2-P5：有限自治、验证与迁移

- [!] `LAR-Q0-001` blocked：staged Full Q0、`B(C,I,Q,expected previous)` activation bundle、pointer CAS/immediate preflight 与 terminal `ActiveRuntimeIdentity`；禁止 writer，不能用 legacy probe/simulation 替代。
- [!] `LAR-P2-001` blocked：Q0/P2 Admission 后一个人工启动、low-risk、commit-only self-host pilot。
- [!] `LAR-P3-001` blocked：一个 promoted template 的 5 个 scheduled self-host observations。
- [!] `LAR-P4-001` blocked：在 B2/per-repo 下执行两个真实 repo、30-task cohort、12+ 严格配对效率 case，标记 `evidence_scope=declared_profile_pilot`。
- [!] `LAR-P4-002` blocked：P4 全绿后独立激活 `portfolio_data_only_v1` B3 generation；global capacity仍为1，repo selector code禁止。
- [!] `LAR-P5-001` blocked：逐仓 CAS cutover、rollback drill、legacy read-only、30 天零调用后退休写面。

## 完成定义

任务只有同时满足以下条件才可标记 completed：

1. dependencies 和 preconditions 在耐久记录中可验证；
2. scope 没有未经记录的扩大；
3. 每条 acceptance 都有命令/文件/evidence 映射；
4. 任务 verification 全部按固定顺序通过；
5. evidence note 完整且不含敏感正文；
6. rollback 可只撤销本切片；
7. 无 stop condition 未解决；
8. planning verifier 绿色，selector 稳定指向唯一后继任务。

禁止为了“推进队列”一次性修改多个任务状态、跳过人工批准或把缺失 artifact 标成 present。
