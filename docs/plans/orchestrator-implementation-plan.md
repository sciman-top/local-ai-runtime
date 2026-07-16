# Local AI Runtime 0.2 实施计划

## 1. 目标、当前落点与真值

目标是在 Baseline Approval 后，把现行 `runtime/host-orchestrator` 逐步迁移到 `runtime/local-ai-runtime`：Windows-local、single-operator、Python modular monolith、Unified Native + global capacity=1 deterministic commit-only Batch。当前仍是 v3.25 preapproval planning：package `10/15 present, 5 non-present`，唯一 task 为 `LAR-P0A-011`，不得创建 runtime、approval、claim 或 live evidence。

机器执行真源是 [local-ai-runtime-0.2-work-items.json](D:/CODE/local-ai-dev-orchestrator/docs/plans/local-ai-runtime-0.2-work-items.json)。本文件说明如何执行；若 task scope/acceptance/dependency/status 与 machine plan 冲突，以 verifier 通过的 machine plan 为准并先修正文档漂移。

## 2. AI 原子执行协议

每次只处理 selector 返回的 `one_selector_selected_work_item`：

1. 运行 `python scripts/verify-planning-status.py` 和 `python scripts/select-next-work.py`；必须均绿且 selector cardinality=1。
2. 读取 task 的 `depends_on/preconditions/scope/acceptance/verification/evidence_path/rollback/stop_conditions/prohibited_actions/next_task_ids`，以及顶层 `graph_policy`、`contract_projection_policy`、`planning_optimization_policy`、`verification_profiles`、`runtime_source_layout`。
3. 在 evidence note 记录 baseline/plan/task identity、当前落点、目标归宿、计划写集、门序、N/A、回滚和风险边界。
4. 只修改 `scope.in/primary_files`；任何 `scope.out`、prohibited action、授权/live 边界立即停止。发现新语义缺口时，不顺手改冻结 candidate；先判断是否要求 successor。
5. 先更新 normative/machine source，再同步 PRD/architecture/roadmap/plan/backlog/status/selector/verifier/tests，禁止只改 prose。
6. 按 task 声明的固定顺序验证；失败先定位根因，不能删 gate、改 expected result 或把 unknown 记为 pass。
7. 独立检查 contract projection 的 producer/implements/accepts 双向关系、artifact identity、DAG reciprocity、source owner 与阶段组合。
8. Evidence 写实际命令、exit code、关键输出/identity、未运行项、N/A、compat 与 rollback；不得写伪 live evidence。
9. task status、inventory/status count、current work、docs 和 selector 一次性同步；fresh verifier/selector 必须指向唯一后继。
10. `git diff --check`、全量 gate、diff review 通过后创建一个可回滚 local commit；worktree clean 才算 closeout。

完整 closeout 后可在同一 run 重新 selector，默认最多 3 个 completed items 或 180 分钟。失败、预算耗尽、gate/selector 红、依赖/授权缺失、阶段/批准转换、v3.25 semantic successor、live/auth/provider/remote/破坏性/外部写或非当前 diff 均停止；`cross_phase_continuation=false`。

## 3. P0A normative closure

### 3.1 已完成 successor slice

`LAR-P0A-REBASELINE-V325` 已完成：

- v3.24 candidate `199728 / 13ee3661...e2a`、package inventory `15646 / 144383f8...7a9f`、machine plan `187913 / 10d48982...18df` 精确归档；
- v3.25 candidate 与 `BaselineLineage.v4` 冻结；
- carry forward `CanonicalizationPolicy.v1`、`ProductContract.v2`、`QualificationContractSet.v2`、`ExecutionSafetyContractSet.v1`、`EvidenceContractSet.v1`、`DeterministicGitContractSet.v1`、`StatePolicyCatalog.v1` 七项；
- 环境证明拆为 `pre_resume_parent_environment_proof` 与 `post_resume_q0_child_environment_observation`，并删除可执行命令中的无效 exact-option sync spelling；
- 机器图降为 52 项，保持 0.2 B3 deferred、P0C/P0D join 与 exact toolchain projection。

### 3.2 `LAR-P0A-004` — ProductContract.v2（已完成）

写集：`ProductContract.v2.json`、`FirstRunExperience.v1.schema.json`、`LaunchTemplateCatalog.v1.json`、`OperatorPresentationCatalog.v1.json`、product-v2 fixtures、inventory/status/evidence。

必须关闭：

- first-run `doctor -> repo qualify -> template list/show -> batch dry-run -> submit -> status/action -> evidence show`，逐步规定 input/output/exit/authority/evidence/rollback；
- 四个 launch templates：`docs_contract_sync_v1`、`bounded_lint_type_repair_v1`、`focused_test_repair_v1`、`mechanical_repo_maintenance_v1`；每项含 closed parameters、path/effect envelope、required/forbidden gates、limits、stop/recovery、denominator/oracle；
- `WorkDefinition`、`TaskFamily`、`TaskTemplate`、`BatchSubmission` v2 绑定；Native Spec 只能创建 candidate，promotion 为 controlled operator action；
- human projection 只由 public machine state + `OperatorPresentationCatalog` 渲染，stable JSON 为自动化接口，raw output/secret-derived data 禁止插值；
- 首发指标及 unknown handling。free prompt、dynamic command、dependency install、remote effect、promotion bypass、secret-bearing fixtures 必须失败。

### 3.3 `LAR-P0A-005` — QualificationContractSet.v2（已完成）

写集：qualification v2、`RuntimeToolchainManifest` schema、`VerificationExecutionProfile` catalog、hashed build constraints、toolchain negative fixtures、baseline verifier component。

必须证明：显式 `uv sync --locked --offline --no-python-downloads --python <manifest-python>` 只作 environment preparation；`uv sync` 默认 exact，`--inexact` 必须拒绝；daily validation `run --no-sync`；child `sys.executable`/patch/file identity/hash、installed distributions/plugins 精确；build frontend/backend/constraints hash-bound；同一 `SOURCE_DATE_EPOCH` 的两个 clean roots 具有相同 member manifest/artifact hashes。wrong patch、extraneous package/plugin、download request、multi-backend cache、missing hashes、repeat mismatch 全部拒绝。

### 3.4 `LAR-P0A-009` — State/guard/operator catalogs（已完成）

SQLite 是唯一 policy/transition authority；journal 只提供 accepted-cursor/fence-bound observation/recovery input。相同 accepted history + policy generation 必须 deterministic replay；journal 缺口/重复/越界/fence drift 都 suspended。Cleanup finalizer 不能因 guard row、marker、journal segment 删除而绕过。

状态域保持独立表，GuardCatalog precedence/DAG 固定；每行含 source、operation/event、guards、effects、target、exit、capacity、priority、retry。`durable_local_status_v1` 必需，`qualified_windows_toast_v1` 可选。B3 状态与 operator action 均 deferred。

### 3.5 `LAR-P0A-010..013`（`010` completed，当前 `011` ready）

- `010`（已完成）：GateGraph、three-level evolution、Q0TriggerPolicy、RuntimeCompositionManifest/SelectedRuntimeIdentity/ActiveRuntimeIdentity、ProcessHandlePolicy/ChildHandleManifest、`PROC_THREAD_ATTRIBUTE_HANDLE_LIST`、`STARTF_USESTDHANDLES`、Windows `OrdinalIgnoreCase` environment、resource/write accounting、emergency reserve、exact toolchain gate evaluation；component verifier 与 84 个 resource boundary cases 已绿，未运行 live Q0。
- `011`：完整 positive/cross-contract/negative/crash/limit fixtures，覆盖 BackupRestoreEligibility、BackupPostActivity、BackupRestoreIntent、QuarantineKeyEnvelope、RuntimeIntegrityKeyEnvelope、`runtime_external_v1` 与 EvidenceProjectionAcceptance。
- `012`：standalone verifier，验证 bytes/domain/schema/dependency/carry-forward/projection/fixtures/tamper；不得改写输入。
- `013`：preliminary review -> `package_review_head` -> 一次性 final `BaselineManifest.v1.json` -> manifest-closure review -> successor `approval_review_head`；只有 15/15 present + review green 才 approval eligible。

## 4. Approval、P0B、P0C/P0D join

`LAR-GOV-001` 由显式 authority + expected generation + anti-replay challenge 签发 Baseline Approval；AI 不自签。`LAR-P0B-001` 只执行 Truth Reset 与 generation projection，不创建 writer。

P0B 后允许最大安全并行：

- P0C 建立 legacy side-effect inventory、shared ownership wire、repo mutex/generation 和 fail-closed guard；证明 legacy 仍 owner；
- P0D 创建 no-side-effect package scaffold，不能 claim/write repo 或 production state；
- P1A-001 同时依赖 `LAR-P0C-003` 与 `LAR-P0D-001`，两者任一未闭合都阻断。

## 5. P0D/P1 工程实现终态

源码布局是关闭集合：`approved_root_files=[__init__.py,__main__.py]`，`approved_subpackages=[contracts,kernel,qualification,storage,execution,recovery,git_local,operations,compat]`，`required_source_owners` 为每个 bootstrap/marker 指定唯一 owner。禁止第二 planner/router、平行 evidence/commands 顶层包和 legacy import。

| Stream | 目标 | 关键验收 |
|---|---|---|
| P1A (`LAR-P1A-001..LAR-P1A-004`) contracts/kernel | typed contracts、canonical envelope、state/guard/reason/capacity | unknown combination exit 2；projection tokens 全闭合 |
| P1B storage | SQLite/migrations/CAS/leases/outbox/artifact/evidence/backup | single authority；atomic/no-replace；migration+rollback |
| P1C qualification/operations | composition/activation、toolchain/repo/template qualification、Authorization、CLI | first-run human+JSON；exact identity；anti-replay |
| P1D execution/recovery | claim、Job/suspended process、pipe/journal/gates、adoption/finalizer | zero-or-one writer commit；EOF/receipt；deterministic recovery |
| P1E git_local | config audit、canonical object/OID、commit/index/HEAD/task-ref/finalize | no reflog；single parent；read-back；no merge/push |
| P1F (`LAR-P1F-001..LAR-P1F-006`) product/compat | scheduler、four templates、managed Native drain、operator inbox、legacy reader | B2 only；no free prompt/B3；compat read-only |

P1G 集成后才可请求 Implementation Acceptance。每项 primary file 必须具体到文件，verification 使用 `profile:new_runtime_exact_v1 focus="..."`，不得把安装/sync 隐藏进 gate。

机器源码边界的紧凑标识为 `contracts/kernel/qualification/storage/execution/recovery/git_local/operations/compat`；该标识与 `approved_root_files`、`approved_subpackages`、`required_source_owners` 必须在 plan/verifier 中保持一致。

## 6. Fixed gate profiles

Planning slice：build/hotspot 依据 acceptance contract 记录 `gate_na`；实际顺序仍是 build -> host-orchestrator pytest -> planning verifier/selector -> hotspot alternative -> preflight -> diff check。

New runtime：

1. preparation：exact/locked/offline/no-download sync + manifest Python；
2. supply-chain identity：lock check + environment read-back；
3. build：offline/no-download + hashed build constraints/require-hashes；
4. test：no-sync isolated Python/pytest；
5. contract/invariant：runtime contracts + planning verifier/selector；
6. hotspot：ruff + pyright + diff check；
7. clean-root reproducibility：两根 member manifest/artifact hash 对比。

任何 `uv run --locked --offline`、unsupported exact-option sync、无 `--require-hashes` build、PATH Python 或自动 Python download 都不构成 v3.25 acceptance evidence。parent buffer proof 不得冒充 child observation；post-resume Q0 child mismatch 直接 `platform_incompatible`。

## 7. Acceptance、rollout 与迁移

Implementation Acceptance 覆盖 code/migration/CLI/first-run/templates/crash/backup/compat/exact toolchain。Full Q0/P2 Admission 覆盖真实 Windows/Codex/Git/sandbox/toolchain/adapters；只有 `ActiveRuntimeIdentity` 才可授权 production attempt。

随后顺序为：P2 one pilot -> P3 five scheduled self-host -> P4 two explicitly qualified repos/30 tasks under B2/per-repo -> P5 per-repo CAS cutover -> legacy read-only -> 30-day zero-call retirement。B3 portfolio scheduling deferred beyond 0.2。

## 8. Evidence、review 与 definition of done

每 task evidence 至少包含：objective/identity/write-set；commands + exit codes + salient output/hash；acceptance mapping；N/A 完整字段；compatibility；risks/unknowns；rollback；fresh selector。repo evidence 写 `docs/change-evidence/`，runtime task evidence 写 `.ai/runs/...`。

完成必须同时满足：task acceptance 全绿；declared gates 实跑；machine/doc/status 同步；diff 无意外；无 approval/live truth overclaim；一个 rollbackable local commit；clean worktree；fresh selector 唯一。阶段 closeout 不能表述成项目整体完成。

## 9. 当前下一步

执行 `LAR-P0A-011`，只创建 persistence migration specification、cross-contract examples 与 negative/crash fixtures，并闭合每个 Tier A schema 的正负例和 crash boundary。不得运行 runtime simulation/live Q0，创建 final manifest、approval、Truth Reset、`runtime/local-ai-runtime`、真实 Git publication，修改 `.ai` live state，读取 live auth/DPAPI/sandbox state，remote push 或 CI retrieval。
