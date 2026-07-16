# Local AI Runtime 0.2 验收与门禁合同

## 1. 当前边界

本合同投影 `local-ai-runtime-0.2-v3.24`。当前为 `baseline_candidate`，package=`9/15 present, 6 non-present`，`blocking_stage=baseline_approval`，唯一 task=`LAR-P0A-010`。v3.23 candidate/package/plan 是 superseded history；predecessor Native comparison 是 non-normative evidence，不是当前 gate、profile promotion 或 approval input。

门禁通过只证明对应层级，不得跨层宣称：

1. planning integrity；
2. Baseline Approval；
3. Implementation Acceptance；
4. Full Q0 / P2 Admission；
5. P2/P3/P4 rollout；
6. P5 cutover/retirement。

## 2. Baseline Approval

Baseline Approval 必须同时满足：

- v3.24 narrative byte_count/SHA-256 与 stable entry target 精确一致；
- `BaselineLineage.v3` 绑定 v3.23 candidate/package/plan archives，carry-forward 仅四项且 focused verifier green；
- 15 个 artifact 全部 present，artifact ID/version/path/bytes/hash/dependency/verifier 闭合；
- `ProductContract.v2` 包含 FirstRunExperiencePolicy、LaunchTemplateCatalog、OperatorPresentationCatalog、四 launch templates、positive/negative fixtures；
- `QualificationContractSet.v2` 包含 RuntimeToolchainManifest、VerificationExecutionProfile、hashed build constraints、toolchain negative fixtures；
- state/Q0/migration/examples/standalone verifier 完整；
- preliminary review P0/P1 findings=0，冻结 `package_review_head`；final BaselineManifest 只创建一次；manifest-closure review 证明 `approval_review_head` 是后继；
- 独立 controlled approval action 绑定 authority/session、expected generation 与 anti-replay challenge。

Baseline Approval 不要求 runtime code 存在，也不允许 AI 自签。v3.24 semantic change 必须先创建 v3.25 successor。

## 3. Product/launch acceptance

首发 first-run 旅程必须端到端机器定义：

`doctor --json -> repo qualify -> template list/show -> batch dry-run -> batch submit --confirm -> status/action -> evidence show`

每步具备 closed inputs、human projection、stable JSON schema、exit code、required authority、no-side-effect/effect boundary、evidence locator、next safe command 和 rollback。Human text 只能由 public state + `OperatorPresentationCatalog` 映射，raw prompt/model/tool/stdout/stderr 与 secret-derived fields 不得插入或持久化。

`LaunchTemplateCatalog` 恰好包含：

- `docs_contract_sync_v1`
- `bounded_lint_type_repair_v1`
- `focused_test_repair_v1`
- `mechanical_repo_maintenance_v1`

每项定义 closed parameters、path/effect envelope、required/forbidden gates、timeout/resource limits、stop/recovery、evaluation denominator、success oracle 和 promotion generation。Native Spec 只能创建 candidate；受控 operator action + review/fixtures/pilot/canary/requalification 才能 promotion。free prompt、dynamic command、dependency install、remote effect、envelope expansion、promotion bypass、secret-bearing fixture 必须 fail closed。

ProductContract.v2 的首发指标精确为：`prequalified_host_to_first_dry_run_net_human_minutes`、`first_commit_ready_pilot_net_human_minutes`、`template_qualification_lead_time`、`eligible_template_coverage`、`operator_action_age`、`policy_false_block_review_rate`、`recovery_to_terminal_time`、`template_maintenance_minutes_per_success`。每项固定 denominator、collection point、unknown handling，target 在实测与接受前必须为 `null`；unknown 必须保留，不能静默记零或移出分母。`completed_work_items_per_operator_kickoff`、`unattended_verified_closeout_rate` 与 `net_operator_minutes_per_success` 仍是更高层 work-session/rollout 指标，不属于本 artifact 的首发八项。

## 4. Planning slice gate

固定顺序仍是 `build -> test -> contract/invariant -> hotspot`：

1. build：`gate_na`；reason=当前是 candidate planning 且新 package 不存在；alternative=`uv run --project ./runtime/host-orchestrator python -m pytest`；evidence=本合同；expires_at=`LAR-P0D-001`；recovery_condition=P0D 建立真实 build 入口。
2. test：`uv run --project ./runtime/host-orchestrator python -m pytest`。
3. contract/invariant：`python scripts/verify-planning-status.py`，然后 `python scripts/select-next-work.py`。
4. hotspot：`gate_na`；reason=planning 不改 runtime hot path；alternative=planning tests + verifier + selector + `git diff --check`；expires_at=first executable slice after P0D；recovery_condition=首个 executable slice 使用真实 hotspot profile。
5. release-style：`pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit`。

Selector 是 read-only、无副作用、不会运行 full preflight。当前期望：

```json
{
  "action": "close_baseline_normative_package_first",
  "current_work_item_id": "LAR-P0A-010"
}
```

## 5. New runtime exact gate profile

### 5.1 Environment preparation（不是验证 gate）

```powershell
& <uv.absolute_path> sync --locked --offline --no-python-downloads --python <python.absolute_path> --project runtime/local-ai-runtime
```

Preparation 必须显式调用且单独留 evidence；验证命令不得自动 sync/download。`python.absolute_path`、patch、file identity/SHA-256 与 `uv.absolute_path`/version/hash 必须来自 `RuntimeToolchainManifest`。

### 5.2 固定门序

1. supply-chain identity

```powershell
& <uv.absolute_path> lock --check --offline --no-python-downloads --python <python.absolute_path> --project runtime/local-ai-runtime
& <python.absolute_path> -I -s -E -m local_ai_runtime toolchain verify-environment --profile new_runtime_exact_v1 --json
```

2. build

```powershell
& <uv.absolute_path> build --offline --no-python-downloads --python <python.absolute_path> --build-constraint <hashed_build_constraints.absolute_path> --require-hashes --project runtime/local-ai-runtime runtime/local-ai-runtime
```

3. test

```powershell
& <uv.absolute_path> run --no-sync --offline --no-python-downloads --python <python.absolute_path> --project runtime/local-ai-runtime python -I -s -E -m pytest
```

4. contract/invariant

```powershell
& <uv.absolute_path> run --no-sync --offline --no-python-downloads --python <python.absolute_path> --project runtime/local-ai-runtime python -I -s -E -m local_ai_runtime contracts verify
python scripts/verify-planning-status.py
python scripts/select-next-work.py
```

5. hotspot

```powershell
& <uv.absolute_path> run --no-sync --offline --no-python-downloads --python <python.absolute_path> --project runtime/local-ai-runtime ruff check runtime/local-ai-runtime
& <uv.absolute_path> run --no-sync --offline --no-python-downloads --python <python.absolute_path> --project runtime/local-ai-runtime pyright --project runtime/local-ai-runtime
git diff --check
```

### 5.3 Exactness / reproducibility assertions

- child `sys.executable`、Python patch/file identity/hash 精确匹配 manifest；
- installed distributions 与 pytest plugins 无 extraneous/missing/drift；
- uv 不下载 Python/dependency，不使用 PATH fallback；
- build backend/frontend/constraints 都由 manifest hash 绑定，cache 中多 backend 不得影响选择；
- 两个 clean roots、同 source/lock/manifest/`SOURCE_DATE_EPOCH` 产生相同 wheel/sdist member manifest 和 artifact hashes；
- wrong Python、extraneous package/plugin、download request、unhashed constraint、cache ambiguity、repeat mismatch fixtures 都必须失败。

## 6. Architecture/contract invariants

- `approved_root_files=[__init__.py,__main__.py]`；`approved_subpackages=[contracts,kernel,qualification,storage,execution,recovery,git_local,operations,compat]`；每个 `required_source_owners` 唯一。
- SQLite 是唯一 policy/transition authority；journal 只作 accepted-cursor/fence-bound observation/recovery input。同 accepted history + policy generation 必须 deterministic replay。
- ProcessHandlePolicy/ChildHandleManifest 使用 suspended launch、Job list、`PROC_THREAD_ATTRIBUTE_HANDLE_LIST`、`STARTF_USESTDHANDLES` 精确 stdio/EOF；未知 process identity 禁止 adoption。
- Windows environment catalog key 使用 `OrdinalIgnoreCase` 唯一性，拒绝 aliases、hidden `=X:`、NUL，输出排序 UTF-16 double-NUL block 并 child read-back。
- 每 task generation 的 writer execution commit 为 0 或 1；`writer_effect_id` 稳定，`writer_launch_id` attempt-scoped；commit 后不重跑。
- Git controller 独立计算 canonical payload/OID，pinned Git materialize，`cat-file` read-back；single parent、no reflog、task ref only，不 merge/push。
- EvidenceProjectionAcceptance、`runtime_external_v1`、QuarantineKeyEnvelope、RuntimeIntegrityKeyEnvelope、BackupRestoreEligibility、BackupPostActivity、BackupRestoreIntent 全部 purpose/activation/generation-bound；raw output/content hash 不持久化。
- Cleanup finalizer 不得因 guard/marker/journal/file row 缺失而跳过；不确定状态进入 durable recovery/operator action。
- global writer capacity=1；B3 portfolio scheduling、multi-writer、remote/distributed runtime、SDK/App Server/managed Worktree/Automations 不属于 0.2。

## 7. Implementation Acceptance

必须验证：

- P0C legacy ownership guard 与 P0D isolated scaffold 均闭合；new package 不 import/double-write legacy；
- 55-task graph 的 P1 implementation 与 11 contract projections 双向闭合；
- migrations/rollback/crash windows/response-loss/backup restore/cross-conformance green；
- first-run human+JSON journey、four templates、operator inbox/runbooks green；
- `new_runtime_exact_v1` 与 clean-root reproducibility green；
- provider-free fixture closeout 无 unauthorized effect；
- `RuntimeCompositionManifest C` 与 ImplementationAcceptanceRecord 精确绑定。

通过不自动启用生产 runtime，也不等于 Full Q0。

## 8. Full Q0 / P2 Admission

staged installation 在 current pointer 未切换时完成真实 Windows/Codex/Git/sandbox/toolchain/adapter/profile probes。Full Q0 绑定 `C + I + staged_identity`；activation bundle 绑定 expected previous active；pointer CAS 先生成 SelectedRuntimeIdentity，只有 immediate quick preflight 成功后才形成 ActiveRuntimeIdentity。

Full Q0 至少覆盖：Job/handle/stdio/EOF、named objects、environment、sandbox/secret/keyring、repo/path/Git config/object/ref、process/gate timeout、SQLite/journal recovery、evidence/backup restore、write accounting/emergency reserve、exact toolchain、first-run/four templates、legacy ownership、task-side network deny。Full Q0 green 与 P2 Admission 同 gate，只开放一个 pilot。

## 9. P2/P3/P4/P5 acceptance

- P2：one low-risk self-host 完整 commit/task-ref/evidence/recovery/rollback；无隐式人工。
- P3：five scheduled self-host；验证 scheduler trigger、recovery priority、daily canary、operator action dedupe/age。
- P4：B2/per-repo；two explicitly qualified repos、30 tasks、至少 25 commit-ready、最多 5 probe-only、12 paired cases；security hard failures=0、mandatory gates/evidence/backup/recovery=100%、unattended >=80%、manual <=20%、无 unresolved state；DownstreamOutcomeRecord 保留 censored/unknown 分母。
- P5：每 repo zero-active + rollback drill + ownership CAS；全部 cutover 后 legacy read-only；30-day zero legacy calls 后 retire writer；保留 compat/evidence/task refs。

P4 不激活 B3；B3 deferred beyond 0.2。P5 直接依赖 P4。

源码 contract marker 为 `contracts/kernel/qualification/storage/execution/recovery/git_local/operations/compat`；它与 `approved_root_files`、`approved_subpackages`、`required_source_owners` 的 machine projection 必须完全一致。

## 10. Evidence 与 truth boundary

每项证据写 objective/identity/write-set、实际 command/exit/output/hash、acceptance mapping、N/A、compat、risk/unknown、rollback、fresh selector。planning green、phase closeout、repo-side done、Implementation Acceptance、Full Q0、live accepted 必须分别表述；任何 simulation/predecessor/legacy evidence 都不能冒充新 runtime live acceptance。
