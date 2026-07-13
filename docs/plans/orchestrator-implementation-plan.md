# Local AI Runtime 0.2 实施计划

## 1. Goal

依据 `local-ai-runtime-0.2-v3.23`，从当前 legacy `runtime/host-orchestrator` 迁移到 Windows-local single-operator general-purpose governed AI development execution platform，同时保持副作用可归属、writer zero-or-one execution commit、Git publication deterministic、证据 secret-safe、迁移可逐仓回滚。产品目标是低人工、可预测、可恢复的开发吞吐；Native 快路径追求低交互延迟，Epoch 1 全局 capacity=1 的 Batch 不承诺高速并发。

当前只执行 P0A normative closure。机器任务真源是 [local-ai-runtime-0.2-work-items.json](D:/CODE/local-ai-dev-orchestrator/docs/plans/local-ai-runtime-0.2-work-items.json)；本文解释如何执行，不复制每个字段。

## 2. 阶段门

| 门 | 允许之前 | 通过后首次允许 | 不代表 |
|---|---|---|---|
| Baseline Approval | P0A contract authoring/review | P0B Truth Reset | 代码已实现 |
| Truth Reset | 只读规划和 approved artifact | P0C legacy guard | 新 Batch 可 claim |
| Legacy Guard | legacy 行为保持 | P0D/P1 实现 | live qualification 绿色 |
| Implementation Acceptance | isolated implementation/test | Full Q0 | P2 admission |
| Full Q0 | 无 live writer | 一个 P2 pilot | scheduled/B3/cutover |

## 3. AI 执行算法

每次只执行一个 machine work item：

1. 运行 `python scripts/verify-planning-status.py`。非零先修规划，不做产品任务。
2. 运行 `python scripts/select-next-work.py`，确认 `next_action` 和 `current_work_item.task_id`。
3. 读取 JSON 中该项全部字段及顶层 `runtime_source_layout`、`graph_policy`、`contract_projection_policy`。任务身份是 `plan_id + task_id`；superseded v3.22 plan 的同名结果不能关闭 v3.23 任务。依赖、前置条件、projection role、停止条件、授权或目标源码路径不能证明时停止。
4. 在 evidence note 先记录目标归宿、当前落点、计划修改文件、回滚和验证命令。
5. 对 contract 任务先写 negative fixture/verifier；对实现任务先写 failing test。
6. 只做满足 acceptance 的最小切片，不顺手实现后继 phase。
7. 按任务 `verification` 执行，再按仓库固定门顺序补全。
8. 逐条把 acceptance 映射到命令和证据；不能映射即未完成。
9. 把该项改为 completed；按 `priority_ascending + task_id_utf8_ascending` 从依赖完全满足的 ready set 选择唯一 current task，DAG 中未选中的可运行兄弟保持 pending/blocked。
10. 更新 planning-status 的 current work item、package counts/flags 和 evidence ref；重新运行 selector。

状态不能一次批量“全部完成”。工作项响应丢失时先读当前文件事实和既有 evidence，幂等补齐同一结果。

## 4. P0A 规范闭包计划

### 已完成：`LAR-P0A-001`、`LAR-P0A-REBASELINE-V322` 与 `LAR-P0A-REBASELINE-V323`

原始 session 中 v3.17 与两份 conflicted v3.18 已按唯一 message/content 边界归档并双路径复算；v3.21 精确 `158485 / 1bfb5cd2...63fb` 与 v3.22 精确 `178330 / 8338a9dc...569c` 均作为 superseded candidate 保留。v3.23 精确 `188325 / 80562322...d5c6` 与 `BaselineLineage.v2` 已冻结。它们只作为 completed DAG history，不再是 selector 可选分支。

### 已完成：`LAR-P0A-EVAL-002` Native thin-path / capability comparative evaluation

`LAR-P0A-EVAL-001` 冻结的 exact byte/hash/snapshot contract 已执行：18 个 core trial 均使用固定 repo snapshot、TaskFamily、模型/effort、tool inventory、sandbox、gates、成功 oracle、重复/交叉顺序和人工介入定义。精简 Native 为 `4/9`，Native + agent-side mandatory gate prompt 为 `1/9`；Superpowers 条件 lane 因 sealed VCS identity 漂移 fail-closed，Trellis/Hermes 对本 corpus not_applicable。结果记录 `preserve_v3_23_semantics`，不 promotion 当前 high-effort profile，不把任何第三方 harness 变成控制面。

硬指标已保留全部分母：总体成功 `5/18`，TF-003 稳定语义漏检 `6/6`，独立 evaluator gate 集 `18/18` 完整，P95 `1446.966s`，累计 input token `17770559`，13 次 recovery/rollback 均由原始或 append-only follow-up evidence 收口；18 个 downstream outcome 均为 unknown/not_recorded，成本 unavailable 而非 0。外部 host 漂移触发两份 transition record、新 generation 与 Q0，18 个 core trial 分布在 3 个 admitted generation；另一个中间 generation 在 Q0 后、core trial 前失效。质量 floor 和跨 generation 边界共同使任何观察到的效率收益不能 promotion，但不要求改变 v3.23 规范语义。

`grill-with-docs` 可用于低频、高不确定、不可逆设计决策的人类术语/ADR 对齐；不作为日常自动执行、Batch admission 或本仓控制面的前门。

### 后续：`LAR-P0A-002` Manifest

固定规范字节、domain envelope、artifact path/hash/schema/verifier closure。Validator 只拒绝，不改写。Narrative ID 只绑定本文精确 bytes；每个 schema/catalog/transition/verifier 使用自己的 artifact ID/version/hash；preapproval inventory 可更新但非规范。本任务只创建 `BaselineManifest.v1` schema、非最终 fixtures 和 verifier skeleton，禁止创建最终 `BaselineManifest.v1.json`，`P0A-MANIFEST` 保持 missing。已 present artifact 禁止原地覆盖，语义修正必须新 artifact version，和 narrative 不一致时同时新建 candidate。

### `LAR-P0A-003` 至 `010` Contract bundles

按依赖顺序完成：

1. `LAR-P0A-003` canonicalization/path：preserved arrays、set duplicate rejection、Git spelling 与 Windows collision key分离、alias-aware 8.3 handle identity、`policy_query_denied` 行为 probe。
2. `LAR-P0A-004` product/submission：`WorkDefinition`、`TaskFamily`、封闭参数；bounded parse -> canonicalize -> volatile lookup -> authorized replay -> absent-only secret/admission -> transaction recheck；ordinary submit 永久返回 root；原子 successor。
3. `LAR-P0A-005` qualification/auth/sandbox：完整 sensitive-input union、base-independent reusable set、base-bound observation refresh、opaque `sandbox.log`、Authorization continuation、root effect grant 与 revoke 线性化。
4. `LAR-P0A-006` execution/fencing：`EffectPlan`、稳定 `writer_effect_id` 与 attempt-scoped `writer_launch_id`、Writer/StageJob suspended launch、`ProcessHandlePolicy`、`PROC_THREAD_ATTRIBUTE_JOB_LIST + PROC_THREAD_ATTRIBUTE_HANDLE_LIST`、`STARTF_USESTDHANDLES` 精确 stdio、`ChildHandleManifest`/parent-end close/EOF、execution-commit barrier、Authorization/SafetyOnly authority union、controller-action child process grant、same-name Job、连续 adoption。
5. `LAR-P0A-007` evidence：append-only event matrix、pre-scan secret-safe projection、journal/segment/receipt、artifact/quarantine、`runtime_external_v1`、`EvidenceProjectionAcceptance`、purpose-separated `QuarantineKeyEnvelope`/`RuntimeIntegrityKeyEnvelope`，以及 `BackupRestoreEligibility`/`BackupPostActivity`/`BackupRestoreIntent` anti-rollback 协议。
6. `LAR-P0A-008` Git：`git_hybrid_materialization_v1`，controller canonical payload/expected OID + pinned Git `hash-object -w` + `cat-file` read-back；config deny、claim time、no-reflog index/HEAD/ref/evidence/remove 顺序。
7. `LAR-P0A-009` state/guard：family/task/attempt/platform/repo/template/autonomy/operator tables、`durable_local_status_v1` 与 optional `qualified_windows_toast_v1`、`portfolio_data_only_v1`，完整 rows、GuardCatalog precedence/DAG 和未知组合分流。
8. `LAR-P0A-010` Q0/resource：`GateGraph`、profile generation -> capability generation -> architecture epoch、`Q0TriggerPolicy`、非循环 activation admission、feature/process/gate catalogs、Windows environment `OrdinalIgnoreCase` 唯一键与 hidden-entry 拒绝、handle/EOF/evidence/DPAPI/restore probes、mandatory `accounting_kill_audit`、1 GiB emergency reserve、optional HardWriteQuotaCapability、limit-1/limit/limit+1。

后一个 bundle 可以引用前一个已固定的 identity，不允许循环引用、隐藏 defaults 或用 narrative prose 代替 machine row。

### `LAR-P0A-011` Examples/fixtures

每个 Tier A schema 至少一正一负；每个 crash window 有 pre/post；每个 limit 有 limit-1/limit/limit+1；每个拒绝有稳定 reason code。

### `LAR-P0A-012` Standalone verifier

验证 bytes、hash、schema、catalog、transition completeness、guard acyclicity、examples、negative fixtures 和引用闭包。任何 auto-fix、network、host locale 依赖都不允许。

### `LAR-P0A-013` Review

先运行覆盖全部 narrative/artifact/fixture/verifier 的 preliminary consistency review，清零 P0/P1 finding 并冻结 `package_review_head`；再一次性创建最终 `BaselineManifest.v1.json`，运行 closure verifier，随后 append manifest-closure review，使 `approval_review_head` 成为 package head 的可验证后继。只有 `P0A-MANIFEST` 与 `P0A-REVIEW` 都 present 且 closure review 绿色才把 package 标为 approval eligible。批准是独立外部授权动作，不由 verifier 自签。

### Contract projection 闭包

v3 machine plan 的 11 项 projection 都必须形成“唯一 P0A producer -> P1 implements -> P1G/Q0/P4 accepts”的双向机器关系：WorkDefinition/TaskFamily、EffectPlan、GateGraph、三级演进、writer effect/launch identity、durable operator inbox、Git hybrid、Q0TriggerPolicy、controlled approval、activation admission 和 data-only portfolio。Verifier 检查 projection ID、role、task phase、token 和引用闭包；只在自然语言中提到契约不算完成。

## 5. P0B/P0C 迁移护栏

P0B 只改 repository truth，不改 runtime 行为。必须保留“current executable kernel=host-orchestrator”直到逐仓 cutover。

P0C 的顺序固定：

1. wire schema/name/SDDL；
2. legacy entrypoint inventory；
3. 在 side effect 前加 guard；
4. 注册 repo legacy owner；
5. cross-runtime name/byte/generation conformance；
6. concurrent claim/crash/takeover；
7. non-destructive cutover/rollback drill。

只要一个 mutation path 未守卫，新 package/scheduler claim 继续硬阻断。

## 6. P0D/P1 实现切片

### 包与依赖

目标归宿 `runtime/local-ai-runtime/src/local_ai_runtime/`，机器布局固定为 `approved_root_files=["__init__.py","__main__.py"]`、`approved_subpackages=["contracts","kernel","qualification","storage","execution","recovery","git_local","operations","compat"]` 和 bootstrap/marker 到任务的一对一 `required_source_owners`；批准首级子包序列即 `contracts/kernel/qualification/storage/execution/recovery/git_local/operations/compat`。`__main__.py` 只转发 contracts-verifier CLI，包根不承载其他功能代码；installer、activation、CLI、Batch、doctor、scheduler、managed Native 和 evaluation 全部归 `operations`，Artifact/evidence 持久化归 `storage`。固定 Python 3.11.x，具体 patch version 由 `RuntimeToolchainManifest` 锁定；先执行 `uv lock --check --offline`，后续 gate 使用 `uv run --locked --offline`，且不得 import legacy package。

### 开发顺序

机器图总计 65 项。P1A-P1F 共 35 个编码切片，数量为 `4 + 5 + 7 + 6 + 7 + 6`；依赖图是确定性 DAG，不再伪装成单链。独立 fixture/adapter 分支可并行准备，但当前任务未 completed 时不得顺手关闭后继任务；每次 AI 会话只执行 selector 返回的一项，其精确文件、projection role、验收和命令以 machine work item 为准。真实 writer 仍须位于 Implementation Acceptance + Full Q0 之后。

#### P1A Contracts/kernel

| Work item | 单一交付 | 退出证明 |
|---|---|---|
| `LAR-P1A-001` | canonical bytes/hash、Git path、Windows collision/alias primitives | canonical/path fixtures 绿色，无输入改写 |
| `LAR-P1A-002` | immutable schema registry 与 typed contract models | positive round-trip、negative reason code 全闭合 |
| `LAR-P1A-003` | state/guard/operator catalog evaluator | 唯一 row、Guard DAG、unknown exit 2 |
| `LAR-P1A-004` | cross-contract policy-bundle verifier | foreign ID/hash、limit fixtures、authority union 全闭合 |

#### P1B Storage

| Work item | 单一交付 | 退出证明 |
|---|---|---|
| `LAR-P1B-001` | SQLite bootstrap、schema、forward/rollback migrations | isolated create/upgrade/rollback/crash 绿色 |
| `LAR-P1B-002` | submission family 与 atomic resubmission | permanent root replay、single successor、零 rejected oracle |
| `LAR-P1B-003` | lease/fence/authority/action CAS repositories | grant/revoke 同序、head 不分叉、唯一 terminal result |
| `LAR-P1B-004` | event/journal cursor、outbox/artifact metadata | DB 不领先 flush、raw/secret digest 不入库 |
| `LAR-P1B-005` | persistence failpoint/response-loss matrix | 每个 failpoint 只落在合法 pre/post state |

#### P1C Platform/qualification

| Work item | 单一交付 | 退出证明 |
|---|---|---|
| `LAR-P1C-001` | `operations` 内 immutable install、activation CAS、compatible rollback | replace/flush crash matrix 绿色，包根无功能模块 |
| `LAR-P1C-002` | pinned toolchain 与 immutable environment binding | absolute identity/hash/offline verification |
| `LAR-P1C-003` | repo/template qualification、AuthState、Authorization | sensitive closure 可复算、keyring-only、revoke 线性化 |
| `LAR-P1C-004` | untrusted overlay、effective config、opaque sandbox state | tool inventory 和 sandbox boundary 绿色 |
| `LAR-P1C-005` | `accounting_kill_audit` 与 emergency reserve lifecycle | 500 ms fallback、fenced release/rebuild、optional quota 不冒充 |
| `LAR-P1C-006` | Full/quick/daily offline Q0 harness | exact probe IDs、generation binding、scope-aware report |
| `LAR-P1C-007` | Codex CapabilityAdapter + `adapter_no_write_smoke_v1` | disposable repo、无 writer grant/process、零 Git/control-plane mutation |

#### P1D Execution/recovery

| Work item | 单一交付 | 退出证明 |
|---|---|---|
| `LAR-P1D-001` | named mutex/Job identity 与 empty-Job lifecycle | SDDL/type/limits/process list、same-name fail closed |
| `LAR-P1D-002` | writer marker、JOB_LIST/HANDLE_LIST suspended launch | durable pre-resume barrier、task generation 单 writer |
| `LAR-P1D-003` | StageJob 与 root/inherited/safety authority | exact stdio/handle manifest、authority 不越权 |
| `LAR-P1D-004` | bounded pipe draining、normalized events、segment journal | EOF/framing 分类、append-only、DB cursor 不领先 |
| `LAR-P1D-005` | takeover/adoption/continuation/recovery | head 不分叉、writer 不重跑、recovery 优先 |
| `LAR-P1D-006` | exact offline gate runner | no shell/fallback、bounded report、deadline/limit+1 |

所有 writer、gate、Git、probe 和 recovery helper 共用一个受测 spawn primitive：exact environment、`PROC_THREAD_ATTRIBUTE_JOB_LIST + PROC_THREAD_ATTRIBUTE_HANDLE_LIST`、`STARTF_USESTDHANDLES`、`ChildHandleManifest`、parent child-end close、pre-resume execution commit；禁止各 stage 自行拼接 CreateProcess。

#### P1E Git/evidence

| Work item | 单一交付 | 退出证明 |
|---|---|---|
| `LAR-P1E-001` | repo/common-dir identity 与 hardened Git audit | config/attribute/hook/driver/protected surface 全拒绝闭包 |
| `LAR-P1E-002` | fenced worktree/checkout 与 mutation closure | path/mode/bytes、secret/protected surface、root identity 闭合 |
| `LAR-P1E-003` | local object plan、deterministic commit、promotion | canonical object verify、clear-alternates reachability |
| `LAR-P1E-004` | finalize index -> HEAD -> task-ref | 三个独立 CAS action，ref 永不提前 |
| `LAR-P1E-005` | artifact、`runtime_external_v1` evidence、receipt | no-replace、六项 receipt、无 hash 环或 secret oracle |
| `LAR-P1E-006` | cleanup 与 quiescent backup/restore drill | 不删未知文件、anti-rollback、isolated restore |
| `LAR-P1E-007` | provider-free `fixture_closeout_rehearsal_v1` | GateGraph + Git hybrid + evidence/cleanup 全链，fixture-only |

#### P1F CLI/operations

| Work item | 单一交付 | 退出证明 |
|---|---|---|
| `LAR-P1F-001` | `operations` 内 stable command tree、JSON envelope、exit/reason mapping | strict parser/read-only commands 零副作用，包根无 CLI 模块 |
| `LAR-P1F-002` | Batch prepare/submit/status/recovery handlers | policy-first transition、permanent replay |
| `LAR-P1F-003` | single-capacity scheduler、parked waits 与 data-only portfolio selector | recovery-first、外部等待释放 capacity、repo selector code拒绝、未安装 scheduler |
| `LAR-P1F-004` | managed Native maintenance 与 emergency kill | normal drain 不 kill、kill intent 先于 termination |
| `LAR-P1F-005` | OperatorAction/WorkSession、`durable_local_status_v1` inbox、runbooks、人工分钟计量 | 唯一建议命令、optional toast不影响 action、无 prompt/secret/free-text reason |
| `LAR-P1F-006` | compat/cutover/evaluation dry-run surfaces | 不改 ownership/live state，固定 paired/cohort 公式 |

`LAR-P1G-001` 单独冻结 `RuntimeCompositionManifest C` 并执行 Implementation Acceptance `I(C)`：运行全套 offline gate、migration、crash、conformance、backup/restore 和 rollback drill；不运行 live writer，也不创建 Full Q0/P2 Admission。`LAR-Q0-001` 再执行 staged `Q(C,I,staged)`，组装 `B(C,I,Q,expected_previous_active)`，持 activation mutex/durable intent 完成 `current.json` expected-head CAS/read-back和 immediate preflight；只有 terminal `ActiveRuntimeIdentity` 可打开 P2。

每片尽量不超过 5 个主要文件，但这是 review 目标，不是机械失败门。需要跨模块时先增加明确接口/fixture，再拆后继项。

## 7. Test strategy

### Contract

- duplicate JSON key、NFC、ordered/set array、domain separation；
- Git path/NTFS collision、long/short alias handle identity、policy-query-denied probe；
- qualification union、absent proof、base-bound observation 与 base-independent reusable set refresh；
- closed parameters、64 KiB、existing-family replay在current secret/catalog变化后仍稳定、absent rejection零oracle；
- opaque sandbox diagnostic、execution-authority union、root/child grant与safety-only闭集；
- `ProcessHandlePolicy`、exact `STARTF_USESTDHANDLES`/HANDLE_LIST role mapping、parent child-end close/EOF、无 ambient sensitive handle；
- Windows environment case-insensitive alias、hidden `=X:` entry、NUL、排序、double-NUL 与 child read-back；
- activation-bound `runtime_external_v1` root identity/ancestry/alias separation、`EvidenceProjectionAcceptance`、purpose-separated DPAPI key envelopes；
- suspended-only `BackupRestoreEligibility`、post-activity marker-before-mutation、immutable restore intent与single consumption；
- write accounting watcher/fallback/final audit、emergency reserve lifecycle、optional hard-quota mode；
- transition completeness、guard acyclicity、unknown exit 2。

### At-most-once

- task generation 恰有一个稳定 `writer_effect_id`，writer execution commit 为 0 或 1；
- attempt 最多一个 `writer_launch_id` 和 writer process；pre-commit fresh attempt使用同一 effect ID、新 launch ID；
- stage run 最多一个 process/execution commit；
- attempt/effect 恰好一种 execution authority；inherited child grant只能引用同一 parent action grant和current head；
- action 最多一个 terminal result；
- source 最多一个 successor；
- backup generation 最多一个 production restore intent/consumption，且任何 post-backup activity 后为零；
- response loss 重放返回原 ID/result。

### Crash

Ownership replace、claim、marker每阶段、suspended spawn、JOB_LIST/HANDLE_LIST 构造、parent child-end close/EOF、root/child/safety execution authority、resume barrier、same-name Job、event/segment/cursor、artifact publish、adoption takeover、Authorization continuation、gate、write-accounting watcher/limit、emergency-reserve release/rebuild、optional quota、object promotion、index、HEAD、task ref、evidence、remove、key-envelope copy、eligible/stale marker、restore intent和restoring/consumed CAS。

### Security/boundary

Network deny、secret scan、unknown path、reparse/hardlink、Git config、protected surface、command line、environment block、output/resource limit、pipe drain/EOF、handle inheritance、named object SDDL、external evidence root separation、DPAPI purpose isolation、backup anti-rollback、DLL/tool identity。

## 8. Evidence discipline

每个任务 evidence note 至少记录：

- baseline/task ID 和 before/after state；
- 修改文件和不在范围内的文件；
- acceptance -> evidence 映射；
- 每条命令、exit code、关键输出；
- N/A 的 reason/alternative/evidence/expires；
- observed risks 和 unresolved items；
- rollback 只撤销本切片的精确方法。

不得保存 prompt、raw JSONL、stdout/stderr、argv/env/config dump 或未知内容/path digest。

## 9. 风险与停止条件

全局停止：baseline hash 漂移、approval/revocation 不可验证、schema 需要新增未批准字段、双 writer 可能、未授权 egress、secret oracle、Git publication 顺序不确定、cleanup 会删除未知文件、rollback 需要破坏证据。

局部停止：repo identity/ownership 不一致、environment/toolchain drift、template suspended、auth generation 变化、base stale、same-name Job 存活、recovery checkpoint 不可证明。

停止后只允许 safety drain、seal、read-only reconcile 和明确 operator action；禁止通过重跑 writer 或换 Job 名恢复。

## 10. 当前下一步

当前 action 是 `close_baseline_normative_package_first`，task 是 `LAR-P0A-002`。Native thin-path 结果、决定和证据已交叉绑定；下一步只重验 manifest schema/fixtures/verifier skeleton 与 v3.23 的一致性，最终 `BaselineManifest.v1.json` 仍不得创建。不得运行 live Batch、创建批准记录、Truth Reset、`runtime/local-ai-runtime`、remote push/CI retrieval，或修改 `.ai/config`。
