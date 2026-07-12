# Local AI Runtime 0.2 Acceptance And Gates

## 1. 状态

本合同投影 `local-ai-runtime-0.2-v3.22`。当前为 baseline candidate；source 与 v3.22-bound lineage present，其他 13 项仍 missing，尚未达到 Baseline Approval。

## 2. 三层不可替代的门

### 2.1 Baseline Approval

要求：

- v3.22 原始 bytes、byte count 和 SHA-256 双路径验证；
- v3.14-v3.21 谱系闭合，含 v3.17 exact archive、两份 conflicted v3.18、精确 v3.19-v3.21；
- narrative ID、独立 artifact ID/version/hash 和 immutable BaselineManifest 的版本边界一致；已 present artifact 无原地改写；
- 全部 Tier A/B 所需 schema、catalog、transition row、example、fixture、verifier 落盘；
- BaselineManifest hash closure；
- standalone verifier 绿色；
- ReviewEvidenceIndex hash chain 绿色；
- P0/P1 规范 finding 为零；
- controlled external operator action 验证 InteractiveToken/session、authority SID、command envelope、manifest/review head、expected generation 和一次性 anti-replay challenge；响应丢失重放返回同一 result；
- append-only `BaselineApprovalRecord` 存在且未被 revocation/supersession。该记录证明受控同 SID operator action，不声称密码学证明物理人类在场。

Baseline Approval 不要求 runtime code 存在。当前 `blocking_stage=baseline_approval`。

### 2.2 Implementation Acceptance

要求：

- approved baseline generation 仍 active；
- Truth Reset 与 Legacy Ownership Guard 绿色；
- `runtime/local-ai-runtime/src/local_ai_runtime/` 满足 `approved_root_files=["__init__.py","__main__.py"]`、`approved_subpackages=["contracts","kernel","qualification","storage","execution","recovery","git_local","operations","compat"]` 和一对一 `required_source_owners`，批准序列为 `contracts/kernel/qualification/storage/execution/recovery/git_local/operations/compat`；`__main__.py` 只能转发 contracts verifier。任何其他包根功能模块、未批准首级子包、重复源码 owner、缺失 marker、symlink/reparse source entry 或 legacy import 都使验收失败；
- 新包、migrations、CLI、runbooks、legacy conformance、crash matrix、key-envelope backup/restore drill 与 suspended-only production-restore state machine 完整；
- 固定 offline build/test/contracts/ruff/pyright/planning/diff 门全部绿色；
- 不以 repo-side simulation、legacy evidence 或 probe-only 结果替代；
- `RuntimeCompositionManifest C` 绑定 architecture epoch、approved baseline、capability set、ExecutionProfile、staged installation 和 implementation/toolchain/adapter/schema/probe hashes；
- append-only `ImplementationAcceptanceRecord I` 绑定 C 和 acceptance evidence，不绑定尚不存在的 Q/B/A。

Implementation Acceptance 不等于 Full Q0 / P2 Admission。

### 2.3 Full Q0 / P2 Admission

Full Q0 必须在 `current.json` 仍指向旧版本时，对 staged installation 验证 pinned Codex/Git/Windows/sandbox/adapter/policy/model/profile/keyring/network/Job/filesystem 行为，并创建 `Q(C,I,staged_identity)`。之后才可组装 `B(C,I,Q,expected_previous_active)`，持 activation named mutex 写 durable intent、锁内重验 expected head、ReplaceFileW/read-back pointer 并立即 quick preflight。指针选择成功只创建 `SelectedRuntimeIdentity`；只有 terminal A 为 `activated_and_preflight_passed` 时 `ActiveRuntimeIdentity` 才存在并允许 P2。`selected_not_admitted` 或未终结 activation intent 必须 suspended/recovery-first。Scheduled/B3/cutover 仍需后续阶段证据。

## 3. 规划门语义

```powershell
python scripts/verify-planning-status.py
python scripts/select-next-work.py
```

Planning verifier exit 0 表示：候选 bytes、inventory、work-item graph、阶段 flags、文档引用和 selector policy 与仓库事实一致。它明确不表示 normative package、approval、implementation 或 Q0 绿色。

Selector 是只读、快速、无副作用入口；不运行 full preflight，不修改状态。当前预期：

```json
{
  "next_action": "close_baseline_normative_package_first",
  "current_work_item_id": "LAR-P0A-003"
}
```

## 4. 固定开发门顺序

仓库级顺序保持：`build -> test -> contract/invariant -> hotspot`。

当前 candidate/planning 切片：

1. build：`gate_na`，当前 legacy 主线无独立 build gate；替代为 host-orchestrator pytest；到新 package scaffold 时失效。
2. test：`uv run --project ./runtime/host-orchestrator python -m pytest`
3. contract/invariant：`python scripts/verify-planning-status.py`
4. hotspot：`gate_na`，替代为 planning tests + verifier + `git diff --check`；到新 package execution slice 时失效。
5. release-style：`pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit`
6. hygiene：`git diff --check`

新 package 出现后固定为：

```powershell
uv lock --check --offline --project runtime/local-ai-runtime
uv build --offline --project runtime/local-ai-runtime runtime/local-ai-runtime
uv run --locked --offline --project runtime/local-ai-runtime python -m pytest
uv run --locked --offline --project runtime/local-ai-runtime python -m local_ai_runtime contracts verify
uv run --locked --offline --project runtime/local-ai-runtime ruff check runtime/local-ai-runtime
uv run --locked --offline --project runtime/local-ai-runtime pyright --project runtime/local-ai-runtime
python scripts/verify-planning-status.py
python scripts/select-next-work.py
git diff --check
```

触及 legacy guard 时额外运行完整 host-orchestrator pytest。

## 5. `gate_na`

仅纯文档/注释/排版或门客观不存在时允许，必须记录：

- `reason`
- `alternative_verification`
- `evidence_link`
- `expires_at`

`gate_na` 不改变门顺序，不能用于跳过已存在 gate，也不能把整套测试标成 N/A。至少运行相关 verifier、selector、script parse 和 diff hygiene。

## 6. Contract acceptance

规范包必须覆盖：

- byte format、全部 Unicode Cc/Cf/noncharacter/bidi/zero-width policy、duplicate JSON key、NFC、array order/set semantics、domain separation；
- Git path、NTFS case collision、alias-aware 8.3 handle identity、`policy_query_denied` 和 bypass probe；
- qualification present/absent/expanded/blocked union；
- base-bound `QualificationObservation` 与排除普通 base/task/submission identity 的 reusable sensitive set refresh；
- closed parameters、64 KiB、path/command-line/resource boundaries；
- submission bounded parse/canonicalize/volatile lookup/authorized replay/absent-only admission 的顺序、root稳定性、零oracle和resubmission uniqueness；
- `WorkDefinition`/`TaskFamily` closed goal/effect/evaluation、`EffectPlan` logical effect/authority/postcondition/recovery class、bounded `GateGraph` DAG；
- state transition completeness、guard acyclicity、unknown exit 2；
- event/status required/forbidden matrix；
- writer/StageJob suspended launch、`ProcessHandlePolicy`、`PROC_THREAD_ATTRIBUTE_JOB_LIST + PROC_THREAD_ATTRIBUTE_HANDLE_LIST`、`STARTF_USESTDHANDLES` 精确 stdio、`ChildHandleManifest`、parent-end close/EOF、root/child/safety execution authority、grant/revoke、adoption/continuation；
- Windows environment `OrdinalIgnoreCase` 唯一键、case alias/hidden `=X:`/NUL 拒绝、canonical UTF-16 排序、double-NUL 与 child read-back；
- opaque sandbox diagnostic、deny-read、bounded rotation、OperatorWorkSession + secret-scan export；
- mandatory write accounting、watcher/fallback/final audit、emergency reserve lifecycle、optional hard quota 与 disk_pressure 分流；
- object promotion、claim-time binding、no-reflog finalize/ref/remove；
- `git_hybrid_materialization_v1`：controller canonical payload/expected OID、pinned Git `hash-object -w` attempt-local materialization、`cat-file` type/size/payload read-back；
- activation-bound `runtime_external_v1`、`EvidenceProjectionAcceptance`、evidence root与repo/Git/worktree/attempt/controller-sensitive roots的identity/ancestry/alias隔离；
- purpose-separated `QuarantineKeyEnvelope`/`RuntimeIntegrityKeyEnvelope`、same-SID DPAPI unwrap、`BackupRestoreEligibility`、`BackupPostActivity` marker-before-mutation、immutable `BackupRestoreIntent` 与single consumption；
- profile generation -> capability generation -> architecture epoch 的升级分类、`Q0TriggerPolicy`、Full/quick/daily Q0 和 reason-code catalogs；
- `durable_local_status_v1` action inbox 与 optional `qualified_windows_toast_v1` transport 分离；`portfolio_data_only_v1` 拒绝 repo executable selector content。
- source-layout contract：包根只允许 `__init__.py` 和薄 `__main__.py`，每个功能模块属于批准子包，规划清单与实际 source tree 使用同一 allowlist verifier。

每个大小、时间、path、override 和 command-line limit 必须有 limit-1/limit/limit+1。

## 7. At-most-once acceptance

Verifier 和 crash tests必须证明：

- 同一 task generation 恰有一个稳定 `writer_effect_id`，`writer_execution_committed` count 为 0 或 1；commit 后不得创建替代 writer；
- 同一 attempt 最多一个 `writer_launch_id` 和 writer process；只有 prior suspended process 在 execution commit 前被证明终止，fresh attempt 才可复用 effect ID 并创建新 launch；
- 同一 StageJob run 最多一个 process identity/execution commit；
- 同一 attempt/effect 最多一个 AuthorizationExecutionGrant 或 SafetyOnlyExecutionRecord，且不能同时存在；
- inherited child process grant 恰好引用一个 parent action grant、current fenced head 和 exact StageJob，且不能用于 writer/gate/model/arbitrary command；
- 同一 fenced action 最多一个 terminal result；
- 同一 resubmission source 最多一个 successor；
- 同一 backup generation 最多一个 production restore intent/consumption，且 post-backup authoritative activity 后永远不可恢复 eligibility；
- ordinary submit 永远返回 root task；
- 任何响应丢失重放返回原 ID/result；
- `writer_execution_committed` 后零 mutation 也不能触发 writer retry。
- `resume_outcome_unknown` 必须继续跟踪原 PID/Job、drain/terminate/seal；无法证明 final result 时写稳定 unresolved，不生成 receipt/commit/ref。

## 8. Crash matrix

覆盖 ownership replace、claim/lease、marker 各阶段、effect/launch identity、suspended spawn、JOB_LIST/HANDLE_LIST 与 `STARTF_USESTDHANDLES` 构造、parent child-end close/EOF、root/child/safety execution authority、resume barrier、same-name Job、partial/invalid JSONL、event append/flush/DB cursor、segment continuation、artifact intent/publish、连续 adoption、Authorization continuation、gate、Git hybrid materialization/read-back、object promotion、index、HEAD、task ref、evidence、remove、write accounting/limit、emergency reserve release/rebuild、optional quota、key-envelope copy/unwrap、eligible/stale marker、restore intent与restoring/consumed CAS，以及 activation intent/pointer CAS/read-back/immediate-preflight/response-loss recovery。

每点必须给出：pre-state、durable writes、injected crash、restart observation、allowed recovery、forbidden duplicate side effect 和 terminal evidence。

## 9. Security hard gates

以下必须全部为 0，且不接受 waiver：

- unauthorized write；
- declared/detected secret leakage；
- duplicate writer；
- conflicting object/commit/ref；
- incorrect cleanup；
- unaccounted Git side effect；
- successful unauthorized egress。

失败按 GuardCatalog scope 暂停 attempt/template/repo/platform。普通资源和进程失败不能默认升级为 platform incompatible。

## 10. Q0、quick 与 daily

- Full Q0：由 `Q0TriggerPolicy` 对 composition diff 决定。新 adapter/provider/runtime engine、sandbox/token/permission/tool inventory、Git/network/delivery、Windows helper、canonicalization/persistence/schema/migration/probe或 unknown diff 必须 Implementation Acceptance + Full Q0；同一已证明 envelope 内的收窄 timeout/resource/path/gate 可 scoped requalification + new Authorization + canary。真实 Q0 验证 Windows environment block、JOB_LIST/HANDLE_LIST stdio inheritance与EOF、runtime-managed evidence root、DPAPI purpose separation和suspended-only restore eligibility。
- Quick preflight：每 drain/attempt，复核 hashes、effective config、inventory、auth generation、repo/base/ownership、writable roots、evidence root identity、write-accounting mode 和 emergency-reserve generation。
- Daily canary：临时 repo 真实验证 allow/deny、untrusted project、config/hooks、opaque sandbox log boundary、provider vs task network、keyring refresh、feature/tool inventory、ephemeral diff、Job kill、handle leakage/EOF、DLL、alias/reparse/hardlink、external evidence isolation、write limits/reserve、Git object 和 deterministic commit。

## 11. Pilot 与 cohort

P2：一个人工启动 low-risk self-host task，commit-ready、安全硬门零、无 unresolved state。

P3：5 个 scheduled self-host writer task，全部完成或 phase 失败。

P4 30-task cohort：Autonomy 全程保持 B2/per-repo；最多 5 probe-only、至少 25 commit-ready；self-host 和两个目标 repo 各至少 5 writer；unattended >=80%，manual <=20%；mandatory gates/evidence/backup/recovery 100%；结束无 unresolved state。每条记录必须标记 `evidence_scope=declared_profile_pilot`，不声明跨 profile 或一般最优。

只有 P4 terminal green 后，`LAR-P4-002` 才能通过受控 action 激活 B3 `portfolio_data_only_v1` generation；global capacity仍为1。P5 从 P4 独立继续，不依赖 B3 激活。

效率：至少 12 个相同 snapshot/controller prompt/gate/qualification/task distribution 的严格配对 case，每模板族至少 3 个。`net_operator_minutes_per_success` 下降至少 50%，并且成功/操作者小时提高至少 50%或 P50 周期下降至少 30%。

## 12. Evidence acceptance

每个 acceptance record 必须可独立验证，绑定 generation、hash、命令、exit、时间、环境和 evidence locator。Raw prompt、JSONL、stdout/stderr、argv/env/config dump 不进入 evidence；stdout/stderr content hash 也禁止。

任何后续阻断发现通过 append-only revocation/supersession 使旧 approval/acceptance 失效，不能删除或修改旧记录。
