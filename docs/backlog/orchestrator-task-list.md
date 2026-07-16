# Local AI Runtime 0.2 任务清单

## 1. 当前真值

Baseline=`local-ai-runtime-0.2-v3.24`；plan=`local_ai_runtime_work_items.v4`；机器图总计 55 项；状态分布为 `completed=2 / ready=1 / pending=5 / blocked=47`。当前队列 `LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE`，唯一 selectable=`LAR-P0A-005`，action=`close_baseline_normative_package_first`。

本页只读投影 [machine work items](D:/CODE/local-ai-dev-orchestrator/docs/plans/local-ai-runtime-0.2-work-items.json)。`[x]` completed、`[ ]` ready/pending、`[!]` blocked。状态只能在 acceptance + declared verification + evidence + machine/doc sync + local commit + clean worktree 后改变。

`bounded continuation` 采用 `same_run_reselect_after_verified_atomic_closeout`：一次只关闭一个 selector-selected item，完整 closeout 后可同一 run 继续；默认最多 3 项/180 分钟，不跨阶段/批准/successor/live 边界。

## 2. P0A / Governance / Bootstrap

- [x] `LAR-P0A-REBASELINE-V324` completed：v3.24 product/toolchain successor；冻结 v3.23 candidate/package/plan，创建 Lineage.v3，carry forward 四项，切换 55-task graph。
- [x] `LAR-P0A-004` completed：ProductContract.v2、FirstRunExperiencePolicy、LaunchTemplateCatalog、OperatorPresentationCatalog、四 launch templates 与 fixtures。
- [ ] `LAR-P0A-005` ready：QualificationContractSet.v2、RuntimeToolchainManifest、VerificationExecutionProfile、exact uv/Python/build gates 与 clean-root repeatability。
- [ ] `LAR-P0A-009` pending：SQLite-authority/journal-observation state/guard/operator catalogs、cleanup finalizer、durable inbox、B3 deferred。
- [ ] `LAR-P0A-010` pending：GateGraph、Q0/capability/activation/resource/process/toolchain gate catalogs。
- [ ] `LAR-P0A-011` pending：migration specification、cross-contract examples、negative/crash/limit fixtures。
- [ ] `LAR-P0A-012` pending：standalone normative package verifier 与 tamper tests。
- [ ] `LAR-P0A-013` pending：preliminary review、package head、final manifest、closure review、approval readiness。
- [!] `LAR-GOV-001` blocked：controlled v3.24 Baseline Approval；要求 explicit authority/expected generation/anti-replay，AI 不自签。
- [!] `LAR-P0B-001` blocked：approved Truth Reset；不创建 writer/claim。
- [!] `LAR-P0C-001` blocked：ownership wire contract 与 legacy side-effect inventory。
- [!] `LAR-P0C-002` blocked：guard 全部 legacy writer/repo side effects。
- [!] `LAR-P0C-003` blocked：legacy/new ownership conformance 与 rollback。
- [!] `LAR-P0D-001` blocked：no-side-effect `runtime/local-ai-runtime` scaffold + exact acceptance harness。

P0D source layout 是关闭集合：`approved_root_files=[__init__.py,__main__.py]`、`approved_subpackages=[contracts,kernel,qualification,storage,execution,recovery,git_local,operations,compat]`、一对一 `required_source_owners`。P0C/P0D 仅在 P0B 后可并行，P1A-001 同时依赖 P0C-003 与 P0D-001。

## 3. P1A — Contracts and kernel

- [!] `LAR-P1A-001` blocked：canonical bytes/hash/path primitives。
- [!] `LAR-P1A-002` blocked：schema registry、typed contracts、WorkDefinition/TaskFamily/launch product bindings。
- [!] `LAR-P1A-003` blocked：state/guard/operator catalog evaluation。
- [!] `LAR-P1A-004` blocked：cross-contract policy bundle verification。

## 4. P1B — Persistence

- [!] `LAR-P1B-001` blocked：SQLite bootstrap/schema migrations；single transition authority。
- [!] `LAR-P1B-002` blocked：submission-family/resubmission transactions。
- [!] `LAR-P1B-003` blocked：leases/fences/execution-authority CAS。
- [!] `LAR-P1B-004` blocked：event/journal/outbox/artifact cursors。
- [!] `LAR-P1B-005` blocked：crash recovery 与 response-loss replay。

## 5. P1C — Composition, qualification and limits

- [!] `LAR-P1C-001` blocked：immutable installation/activation rollback；RuntimeCompositionManifest -> SelectedRuntimeIdentity -> ActiveRuntimeIdentity。
- [!] `LAR-P1C-002` blocked：exact toolchain/environment binding；RuntimeToolchainManifest + no-sync gates + hash-pinned backend。
- [!] `LAR-P1C-003` blocked：repo/template qualification、auth state、Authorization。
- [!] `LAR-P1C-004` blocked：Codex sandbox state/effective-config qualification。
- [!] `LAR-P1C-005` blocked：write accounting 与 emergency reserve lifecycle。
- [!] `LAR-P1C-006` blocked：Full/quick/daily qualification probes 与 Q0TriggerPolicy。
- [!] `LAR-P1C-007` blocked：CLI Codex CapabilityAdapter 与 provider-free no-write smoke。

## 6. P1D — Execution and recovery

- [!] `LAR-P1D-001` blocked：named-object identity/empty Job lifecycle。
- [!] `LAR-P1D-002` blocked：writer marker/atomic suspended launch；writer_effect_id/writer_launch_id。
- [!] `LAR-P1D-003` blocked：StageJobs/execution-authority enforcement；ProcessHandlePolicy、ChildHandleManifest、HANDLE_LIST/STARTF_USESTDHANDLES。
- [!] `LAR-P1D-004` blocked：bounded stream drain/normalized journal。
- [!] `LAR-P1D-005` blocked：adoption/continuation/recovery handoff 与 cleanup finalizer。
- [!] `LAR-P1D-006` blocked：exact offline gate runner。

## 7. P1E — Deterministic Git and evidence

- [!] `LAR-P1E-001` blocked：hardened Git identity/preflight audit。
- [!] `LAR-P1E-002` blocked：fenced worktree setup/mutation closure。
- [!] `LAR-P1E-003` blocked：controller canonical object plan、pinned Git materialization/read-back/promotion。
- [!] `LAR-P1E-004` blocked：finalize index/HEAD/task-ref，no reflog。
- [!] `LAR-P1E-005` blocked：artifact/external evidence/receipt closeout。
- [!] `LAR-P1E-006` blocked：safe cleanup 与 anti-rollback backup/restore。
- [!] `LAR-P1E-007` blocked：provider-free fixture closeout rehearsal。

## 8. P1F/P1G — Product operations and acceptance

- [!] `LAR-P1F-001` blocked：stable CLI kernel/human+JSON envelope。
- [!] `LAR-P1F-002` blocked：Batch prepare/dry-run/submit/status/recovery。
- [!] `LAR-P1F-003` blocked：single-capacity scheduling/parking；四 template 运行约束。
- [!] `LAR-P1F-004` blocked：managed Native maintenance/emergency kill。
- [!] `LAR-P1F-005` blocked：durable operator actions、runbooks、work-session/product metrics。
- [!] `LAR-P1F-006` blocked：compat/cutover/evaluation command surfaces。
- [!] `LAR-P1G-001` blocked：Implementation Acceptance；闭合 11 projections、first-run、templates、exact toolchain、migration/crash/backup/compat。

## 9. Q0 and rollout

- [!] `LAR-Q0-001` blocked：staged Full Q0、atomic activation、P2 Admission。
- [!] `LAR-P2-001` blocked：one low-risk self-host pilot。
- [!] `LAR-P3-001` blocked：five scheduled self-host observations。
- [!] `LAR-P4-001` blocked：B2/per-repo，显式资格化两个 repo，30-task cohort；不激活 B3。
- [!] `LAR-P5-001` blocked：per-repo CAS cutover、rollback drill、legacy read-only 与 30-day retirement。

B3 portfolio scheduling、multi-writer、remote/distributed runtime、SDK/App Server/managed Worktree/Automations 全部 deferred beyond 0.2，机器图不存在 `LAR-P4-002`。

## 10. 当前 task 的可执行摘要

`LAR-P0A-005` 只允许修改 QualificationContractSet.v2、RuntimeToolchainManifest schema、VerificationExecutionProfile catalog、toolchain-v2 fixtures、component verifier、inventory/status/evidence。验收必须证明 exact locked offline sync、manifest Python read-back、no-download、hash-pinned build backend 与 clean-root repeatability；不得准备 live environment、下载 Python/依赖、创建 runtime/final manifest/approval 或运行 live probe。
