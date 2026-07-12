# Local AI Runtime 0.2 Acceptance And Gates

## 1. 状态

本合同投影 `local-ai-runtime-0.2-v3.21`。当前为 baseline candidate，规范包不完整，尚未达到 Baseline Approval。

## 2. 三层不可替代的门

### 2.1 Baseline Approval

要求：

- v3.21 原始 bytes、byte count 和 SHA-256 双路径验证；
- v3.14-v3.20 谱系闭合，含 v3.17 exact archive、两份 conflicted v3.18、精确 v3.19 和冻结 v3.20；
- narrative ID、独立 artifact ID/version/hash 和 immutable BaselineManifest 的版本边界一致；已 present artifact 无原地改写；
- 全部 Tier A/B 所需 schema、catalog、transition row、example、fixture、verifier 落盘；
- BaselineManifest hash closure；
- standalone verifier 绿色；
- ReviewEvidenceIndex hash chain 绿色；
- P0/P1 规范 finding 为零；
- append-only `BaselineApprovalRecord` 存在且未被 revocation/supersession。

Baseline Approval 不要求 runtime code 存在。当前 `blocking_stage=baseline_approval`。

### 2.2 Implementation Acceptance

要求：

- approved baseline generation 仍 active；
- Truth Reset 与 Legacy Ownership Guard 绿色；
- `runtime/local-ai-runtime/src/local_ai_runtime/` 只包含 `contracts/kernel/qualification/storage/execution/recovery/git_local/operations/compat` 这组批准的首级子包，且不 import legacy package；
- 新包、migrations、CLI、runbooks、legacy conformance、crash matrix、key-envelope backup/restore drill 与 suspended-only production-restore state machine 完整；
- 固定 offline build/test/contracts/ruff/pyright/planning/diff 门全部绿色；
- 不以 repo-side simulation、legacy evidence 或 probe-only 结果替代；
- append-only `ImplementationAcceptanceRecord` 绑定代码、baseline、toolchain 和 evidence hashes。

Implementation Acceptance 不等于 Full Q0 / P2 Admission。

### 2.3 Full Q0 / P2 Admission

Full Q0 必须在真实安装上验证 pinned Codex/Git/Windows/sandbox/adapter/policy/model/profile/keyring/network/Job/filesystem 行为。通过后只允许一个人工启动的 P2 pilot；scheduled/B3/cutover 仍需后续阶段证据。

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
  "current_work_item_id": "LAR-P0A-001"
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
uv build --offline --project runtime/local-ai-runtime runtime/local-ai-runtime
uv run --frozen --offline --project runtime/local-ai-runtime python -m pytest
uv run --frozen --offline --project runtime/local-ai-runtime python -m local_ai_runtime contracts verify
uv run --frozen --offline --project runtime/local-ai-runtime ruff check runtime/local-ai-runtime
uv run --frozen --offline --project runtime/local-ai-runtime pyright --project runtime/local-ai-runtime
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
- state transition completeness、guard acyclicity、unknown exit 2；
- event/status required/forbidden matrix；
- writer/StageJob suspended launch、`ProcessHandlePolicy`、`PROC_THREAD_ATTRIBUTE_JOB_LIST + PROC_THREAD_ATTRIBUTE_HANDLE_LIST`、`STARTF_USESTDHANDLES` 精确 stdio、`ChildHandleManifest`、parent-end close/EOF、root/child/safety execution authority、grant/revoke、adoption/continuation；
- Windows environment `OrdinalIgnoreCase` 唯一键、case alias/hidden `=X:`/NUL 拒绝、canonical UTF-16 排序、double-NUL 与 child read-back；
- opaque sandbox diagnostic、deny-read、bounded rotation、OperatorWorkSession + secret-scan export；
- mandatory write accounting、watcher/fallback/final audit、emergency reserve lifecycle、optional hard quota 与 disk_pressure 分流；
- object promotion、claim-time binding、no-reflog finalize/ref/remove；
- activation-bound `runtime_external_v1`、`EvidenceProjectionAcceptance`、evidence root与repo/Git/worktree/attempt/controller-sensitive roots的identity/ancestry/alias隔离；
- purpose-separated `QuarantineKeyEnvelope`/`RuntimeIntegrityKeyEnvelope`、same-SID DPAPI unwrap、`BackupRestoreEligibility`、`BackupPostActivity` marker-before-mutation、immutable `BackupRestoreIntent` 与single consumption；
- Full/quick/daily Q0 和 reason-code catalogs。

每个大小、时间、path、override 和 command-line limit 必须有 limit-1/limit/limit+1。

## 7. At-most-once acceptance

Verifier 和 crash tests必须证明：

- 同一 task generation 最多一个 `writer_execution_committed`；
- 同一 attempt 最多一个 writer process；
- 同一 StageJob run 最多一个 process identity/execution commit；
- 同一 attempt/effect 最多一个 AuthorizationExecutionGrant 或 SafetyOnlyExecutionRecord，且不能同时存在；
- inherited child process grant 恰好引用一个 parent action grant、current fenced head 和 exact StageJob，且不能用于 writer/gate/model/arbitrary command；
- 同一 fenced action 最多一个 terminal result；
- 同一 resubmission source 最多一个 successor；
- 同一 backup generation 最多一个 production restore intent/consumption，且 post-backup authoritative activity 后永远不可恢复 eligibility；
- ordinary submit 永远返回 root task；
- 任何响应丢失重放返回原 ID/result；
- `writer_execution_committed` 后零 mutation 也不能触发 writer retry。

## 8. Crash matrix

覆盖 ownership replace、claim/lease、marker 各阶段、suspended spawn、JOB_LIST/HANDLE_LIST 与 `STARTF_USESTDHANDLES` 构造、parent child-end close/EOF、root/child/safety execution authority、resume barrier、same-name Job、partial/invalid JSONL、event append/flush/DB cursor、segment continuation、artifact intent/publish、连续 adoption、Authorization continuation、gate、write accounting/limit、emergency reserve release/rebuild、optional quota、object materialization/promotion、index、HEAD、task ref、evidence、remove、key-envelope copy/unwrap、eligible/stale marker、restore intent 与 restoring/consumed CAS。

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

- Full Q0：install/activate 及 binary/model/profile/permission/feature/Git/state/canonicalization/adapter/probe/environment/schema 变化；真实验证 Windows environment block、JOB_LIST/HANDLE_LIST stdio inheritance与EOF、runtime-managed evidence root、DPAPI purpose separation和suspended-only restore eligibility。
- Quick preflight：每 drain/attempt，复核 hashes、effective config、inventory、auth generation、repo/base/ownership、writable roots、evidence root identity、write-accounting mode 和 emergency-reserve generation。
- Daily canary：临时 repo 真实验证 allow/deny、untrusted project、config/hooks、opaque sandbox log boundary、provider vs task network、keyring refresh、feature/tool inventory、ephemeral diff、Job kill、handle leakage/EOF、DLL、alias/reparse/hardlink、external evidence isolation、write limits/reserve、Git object 和 deterministic commit。

## 11. Pilot 与 cohort

P2：一个人工启动 low-risk self-host task，commit-ready、安全硬门零、无 unresolved state。

P3：5 个 scheduled self-host writer task，全部完成或 phase 失败。

P4 30-task cohort：最多 5 probe-only、至少 25 commit-ready；self-host 和两个目标 repo 各至少 5 writer；unattended >=80%，manual <=20%；mandatory gates/evidence/backup/recovery 100%；结束无 unresolved state。

效率：至少 12 个相同 snapshot/controller prompt/gate/qualification/task distribution 的严格配对 case，每模板族至少 3 个。`net_operator_minutes_per_success` 下降至少 50%，并且成功/操作者小时提高至少 50%或 P50 周期下降至少 30%。

## 12. Evidence acceptance

每个 acceptance record 必须可独立验证，绑定 generation、hash、命令、exit、时间、环境和 evidence locator。Raw prompt、JSONL、stdout/stderr、argv/env/config dump 不进入 evidence；stdout/stderr content hash 也禁止。

任何后续阻断发现通过 append-only revocation/supersession 使旧 approval/acceptance 失效，不能删除或修改旧记录。
