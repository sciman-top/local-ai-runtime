# Local AI Runtime 0.2 v3.17：Unified Native + Batch Deterministic Minimum-Operator Implementation Baseline Candidate

## 1. 规范身份、当前事实与战略目标

- 唯一规范 ID 为 `local-ai-runtime-0.2-v3.17`。它完整替代附件 v3.14（SHA-256 `B4133FF27E1FACD0B2B8C48BB89D5FDC4006AD379203BFEF78B4AF6CDAC9DDB2`），撤回未持久化的 v3.15/v3.16 草稿；实现语义不得从旧文本补全。
- 本文及 `BaselineManifest.v1` 列出的 schemas、catalogs、examples、transition tables、fixtures 和 verifiers 共同构成单一基线。任何正文变化必须升级规范版本；禁止同一 ID 对应多份正文。
- v3.17 当前是 Implementation Baseline Candidate。只有所有 P0/P1 机械契约落盘、manifest hash 闭合、verifier 绿色并通过一致性评审后，才能标记 `Approve as P0/P1 Baseline`；Q0 仍只阻断 P2。
- 当前仓库保持 clean legacy truth：`runtime/host-orchestrator` 仍是运行内核，active queue 仍为 `PHASE-1-VERTICAL-SLICE`，verifier 缺 `本地 AI 运行时` 与 `host_local > remote_non_gui > vm_gui`，selector 返回 `repair_gate_first`。P0 前不得宣称新 Batch 已实现、platform compatible 或 live accepted。
- 目标采用词典序：安全与副作用正确性硬门 → 最小化净人工分钟 → 提高无人值守成功率 → 优化周期和实际可归属成本。0.2 不优化高并发、远程拓扑、多 Provider 或自动合并。

## 2. 产品终态、统一路由与自治边界

产品终态固定为 **Codex Native Direct/Spec/Program + Python Policy/Evidence Kernel + 全局单 writer commit-only Batch + 最终只读 legacy/Hermes/AgentBridge compat**。Direct、Spec、Program 是本产品的路由标签，不声称是 Codex CLI flags。

| 路由 | 进入条件 | 自动化与交付边界 |
|---|---|---|
| Native Direct | 明确、一次性、交互任务 | Codex 原生执行；人工检查、集成、merge/push |
| Native Spec | 高影响歧义 | 最多询问 3 个问题，形成 decision-complete TaskSpec；不自动执行或转 Batch |
| Native Program | 至少两个独立写集合且集成顺序固定 | 可用原生 subagents/worktrees；人工集成；不继承 Batch receipt/fence |
| Batch | 已批准模板、低风险、离线、host-local、decision-complete | 零干预完成 worktree→writer→gates→commit→task-ref→evidence→cleanup |
| Human-controlled Native | GUI、生产、数据库、VPS、凭据、remote、不可逆或高风险 | 明确人工授权和监督；永不进入 Batch |

- 自由 Native prompt 永不自动转成 Batch。Spec-to-Batch 必须先形成 `TaskTemplate`、repo+template qualification、有效 Authorization，再由操作者显式提交 `BatchSubmission`。
- Batch 0.2 禁止 subagent、多 writer、Approval、SDK、Provider/model/sandbox fallback、remote Git、merge/push、target-ref 更新和 task-ref 删除。
- Native 对 Batch-qualified repo 执行写操作或 Git maintenance 前，必须执行 `repo maintenance enter`；它在统一 repo mutex 下要求零 active/closing attempt并递增 ownership generation，阻断 Batch 和 legacy claim。完成并核验 base/qualification 漂移后执行 `repo maintenance exit`。
- 一次性人工职责仅为 install/activate、login、environment/repo/template qualification、Authorization、repo maintenance、cutover/rollback。正常 Batch 为零干预；人工只处理 auth/environment/authorization/incompatible/dirty/reconcile/ownership-repair。
- 永不自动执行：扩大权限、登录、安装依赖、修改模板或 policy、切模型/Provider、动态 fallback、merge/push、删除 ref、生产副作用、ownership repair 或不满足证明条件的 cleanup。

## 3. 架构、安装、运行路径与宿主边界

- P0 后新增 `runtime/local-ai-runtime/src/local_ai_runtime/`，采用 Python 3.11+ 模块化单体，边界为 `contracts/kernel/qualification/storage/execution/recovery/git_local/compat`；新包不得 import、调用或双写 `host_orchestrator`。
- Legacy 与 Batch 分别实现同一 `RepoRuntimeOwnership` wire contract并通过交叉 conformance tests，不共享状态数据库。Legacy 仍可在未 cutover repo 写入，但全部写入口必须先经过 ownership/mutex/generation guard。
- 生产根为 `%LOCALAPPDATA%\LocalAIRuntime`，分为 immutable `versions/policies/schemas/codex-home`、mutable isolated auth、global state、ownership、runs/evidence、quarantine/backups、environment bindings，以及每 attempt 独占的 `HOME/USERPROFILE/APPDATA/LOCALAPPDATA/XDG_CONFIG_HOME/CODEX_SQLITE_HOME/TEMP/TMP/cache/spool`。
- 不同 attempt 不得共享任何可写 HOME、SQLite、APPDATA、TEMP 或 cache。每次 spawn 前后验证 writable roots及祖先的最终路径、volume/file identity、ACL、reparse point和跨根 hardlink；运行根必须是通过原子 replace/no-replace、file identity和FlushFileBuffers probes的本地固定卷。
- `RuntimeToolchainManifest.v1` 锁定 Python、uv、`uv.lock`、PowerShell、Git、Node/npm wrapper、`@openai/codex@0.144.1`、bundled `codex.exe`、Windows build、sandbox、Job helper、bootstrap、CapabilityAdapter和Q0 probes的绝对路径、版本、file identity及SHA-256。Repo 专用 dotnet/npm/pytest依赖只进入 `QualifiedEnvironmentBinding`。
- 版本安装到 immutable `versions/<version>`；bootstrap 使用受管 PowerShell `-NoProfile -NonInteractive` 和 pinned Python `-I -s -E`。`current.json` 首次创建使用 no-replace，更新使用 expected generation/checksum + `ReplaceFileW` 类原子替换和 backup；`RuntimeActivationRecord.v1` 约束 activate/rollback CAS及schema兼容。
- Batch claim 前验证可用磁盘至少为 `max(5 GiB, 2 × base materialized bytes + 2 × artifact limit)`；不足进入 `needs_environment/disk_space_insufficient`。

## 4. 契约分层与机械可复算规则

- Tier A 使用 `Spec + Schema + Example + Catalog + Verifier`：`BaselineManifest`、`ProductContract`、`WorkRoutingPolicy`、`CanonicalizationPolicy`、`RepoProfile`、`TaskTemplate`、`BatchSubmission`、`ResolvedBatchManifest`、`Authorization`、`AttemptStatePolicy`、`GatePolicy`、`RepoRuntimeOwnership`、`RuntimeActivationRecord`、`RuntimeToolchainManifest`、`CapabilityQualificationSnapshot`、`QualifiedEnvironmentBinding`、`CodexFeaturePolicy`、`ProcessEnvironmentPolicy`、`GitConfigPolicy`、`ExecutionReceipt`、`EvidenceIndex.v2`、`CloseoutBundle.v2`、`WorkflowEffectMetrics.v1`。
- Tier B 使用 schema、migration/compat、fixture、round-trip及invariant/recovery tests：`QualificationSensitiveInputSet`、`RepoTemplateQualification`、`ResolvedAttemptManifest`、`AttemptRecord`、`AttemptProcessEnvironment`、`InstructionSnapshot`、`SkillInventory`、`FeatureInventory`、`AuthState`、`AttemptPermissionOverlay`、`WriterFinalResult`、`NormalizedExecutionEvent`、`JournalSegmentManifest`、`GateReport`、`GitPreflightReport`、`FencedActionIntent`、`FencedActionAdoption`、`ObjectSetManifest`、`JobIdentity`、`AttemptAuthorizationContinuation`、outbox records及`OperatorAction`。
- Tier C 仅保留内存类型、原始 probe fixtures和测试。Raw Codex JSONL、stdout/stderr正文、reasoning、agent text、prompt、command/argv、env、tool I/O和config dump永不持久化；stdout/stderr默认只保存byte count、exit/reason和白名单结构化报告。
- `Approval`、`NativeCodexReceipt`、`RepoEvidenceProjection`保持draft；`TemplateExecutionProfile`在首次静态模型晋升前保持dormant Tier B。
- `CanonicalizationPolicy.v1` 固定 UTF-8/LF、Unicode NFC、无浮点、整数有界、对象key按UTF-8词典序、数组按对象规则预排序、无多余空白；对象内容hash排除自身hash字段后取SHA-256小写hex。
- `QualificationSensitiveInputSet.v1` 只从唯一 `local_base_ref` 的Git tree发现；repo path保留Git拼写、使用`/`、拒绝绝对路径、`.`/`..`、ADS、DOS device、无效UTF-8/NFC和Windows case collision，并用Windows invariant uppercase生成host comparison key。条目固定包含path、host key、presence、object type、mode、Git OID、resolver rule ID、discovery source和sensitivity class。
- Clean tracked输入只使用base-tree OID/mode；dirty、staged或untracked内容若命中敏感路径、发现入口或其祖先则阻断，不把工作树hash混入授权。Repo声明只能增加输入；未知动态加载、repo外引用或无法递归闭合时阻断或由controller扩大到完整目录类别。按`host_key, repo_path, rule_id`排序后计算canonical hash。
- `NormalizedExecutionEvent.v1` 的公共必需字段为schema、attempt UUID、positive fence/seq、`YYYY-MM-DDTHH:MM:SS.ffffffZ`、event_type、status、prev_hash和event_hash；可选字段不得为null。tool事件必须有item_id；failed/rejected必须有catalog reason_code；exit_code只允许process/tool终结事件；usage只允许turn_completed；path/content字段只允许mutation/final-result且不得表示stdout、stderr或秘密。
- event/status组合固定：started事件→`started`，mutation/EOF→`observed`，正常终结/seal→`completed`，tool/turn/process失败→`failed`，adapter拒绝→`rejected`。`event_hash=SHA256(canonical event excluding event_hash)`，首条prev为64个`0`；reason-code catalog版本和hash进入receipt。
- `WriterFinalResult.v1` 只允许`status=completed|blocked`、排序去重且≤200的approved relative paths及可选枚举reason_code；无summary或自由文本，且controller不信任其路径声明，仍以磁盘/Git审计为准。
- `BatchSubmission`仅含`repo_id/template_id/parameters/expected_base_commit`。其canonical hash是永久idempotency key；重复提交返回原task ID。repo/template ID匹配`[a-z0-9][a-z0-9._-]{0,62}`，base为40位小写SHA-1，task/attempt为controller生成的小写UUID，`max_attempts=3`。

## 5. Codex、权限、环境、Auth与Qualification

- Writer固定为 `<pinned-codex> exec <overlay> --ephemeral --json --strict-config --ignore-rules -p batch -C <worktree> -m gpt-5.6-sol --output-schema <schema> -`；gate/Git固定为 `<pinned-codex> sandbox -p batch -P <batch-gate|batch-git-audit|batch-git-local> -C <cwd> <overlay> -- <absolute-executable> <argv...>`。
- `exec`没有`-P`，writer只能由`default_permissions="batch-writer"`激活；profile固定`model_reasoning_effort="high"`、`approval_policy="never"`、`windows.sandbox="elevated"`、`web_search="disabled"`、`history.persistence="none"`、`allow_login_shell=false`、`shell_environment_policy.inherit="none"`和`cli_auth_credentials_store="keyring"`。
- 0.2 keyring不可用即Q0失败，不提供file/auto fallback。`AuthState.v1`只保存generation、store、status和last-qualified时间；不保存credential内容、hash、mtime或代理凭据。`needs_auth`停止scheduled retry并按`(platform_login_required,auth_generation)`去重OperatorAction，只有交互式login改变generation并通过quick qualification后恢复。
- Codex parent从受管空CWD启动，只获得provider所需控制面网络和Q0批准的非秘密proxy endpoint；model启动的工具、gate和Git均无task-side网络及auth/proxy变量。Gate可使用worktree CWD，但launcher必须使用受控DLL搜索目录并排除current-directory side loading。
- `ProcessEnvironmentCompiler`从空环境构造大小写去重的allowlist；PATH仅含Toolchain Manifest或Environment Binding目录。`QualifiedEnvironmentBinding`内容寻址且不可变，绑定lock hash、volume/file identity、ACL、dependency-tree manifest/hash、只读依赖/cache、attempt-local writable cache、gate绝对argv/env、reparse/hardlink审计和qualification generation；Batch只挂接验证，不install/restore/bootstrap。
- Overlay最多64个`-c`、最多16,384 UTF-16 code units，完整CreateProcess命令行小于32,767；在AttemptRecord创建前完成TOML、path、CreateProcess/CommandLineToArgvW round-trip。Receipt保存compiler input hash、compiler version/hash、逻辑根替换后的安全投影、有序digest、effective-config hash、feature/tool inventory ID及probe ID，不保存raw argv。
- `CodexFeaturePolicy.v1`逐项分类`required_enabled/allowed_internal/required_disabled/removed_ignored`并绑定model-visible tool inventory。未知effective=true、生命周期漂移或removed项重新暴露tool均失败；apps/plugins/hooks/MCP/memories/goals/multi-agent/browser/computer-use/image generation/tool suggestions/workspace dependencies/shell snapshot/skill install等必须不可见。
- `project_doc_fallback_filenames=[]`，global AGENTS≤8192 bytes，project chain≤32768 bytes。`InstructionSnapshot`绑定全局文件不存在证明或hash、完整project链顺序/OID/bytes/预算；截断或漂移阻断。Writable roots及祖先禁止reparse；只读skill symlink仅在最终目标位于批准根且identity/OID/hash完全匹配时允许。
- Full Q0在install/activate及Codex/Git/Windows/sandbox/adapter/probe变化时运行；每次drain/attempt执行quick preflight；daily canary在受管临时repo中测试allow/deny读写、断网、provider网络、keyring refresh、ephemeral disk diff、Job kill、DLL loading、reparse/hardlink、limits和deterministic Git。
- `platform_unavailable`遵循Retry-After，否则5m→15m→1h→6h；canary基础设施只独立重试一次，随后`qualification_suspended`并停止claim；binary/config/profile/effective行为漂移为`platform_incompatible`。单任务输出超限只失败当前attempt，除非独立Q0证明平台行为漂移。
- 限额固定为writer 3600s、单gate 1800s、全部gates 7200s、closeout 900s、attempt 11700s、Scheduler 12600s；writer JSONL/stdout合计8MiB、stderr8MiB、单行256KiB、normalized journal 8MiB、单event16KiB、final result1MiB，其他进程stdout/stderr各8MiB、diff16MiB、changed files200、artifacts256MiB。

## 6. Ownership、状态机、fencing与恢复

- `%LOCALAPPDATA%\LocalAIRuntime\ownership/<repo_id>.json`绑定repo_id、canonical Git common-dir final path、volume/file ID、owner、status、generation、registry generation、schema和checksum。首次创建no-replace；更新以expected generation/checksum执行flush+atomic replace+backup；损坏只可自动采用identity一致且generation不倒退的backup，否则进入interactive ownership repair。
- SID canonical form来自`ConvertSidToStringSidW`，`SIDHash=SHA256(ASCII SID)[:16]`；RepoIdentityHash为canonical repo identity SHA-256前24位。名称固定为`Global\LocalAIRuntime.BatchDrain.<SIDHash>.v1`、`Global\LocalAIRuntime.RepoOwnership.<SIDHash>.<RepoIdentityHash>.v1`、`Global\LocalAIRuntime.Attempt.<SIDHash>.<attempt_uuid>.v1`，SDDL固定`D:P(A;;GA;;;SY)(A;;GA;;;<CURRENT_SID>)`。
- 锁顺序固定为global capacity→repo mutex/ownership generation→SQLite `BEGIN IMMEDIATE` CAS。Heartbeat 15秒、TTL 90秒；takeover必须同时证明旧mutex释放、named Job不存在或零进程、记录PID+creation time均不存活、TTL到期和fencing CAS成功，并优先恢复旧attempt。
- `writer_started`使用三阶段：DB start-intent committed→`CREATE_NEW|WRITE_THROUGH` marker并FlushFileBuffers/父目录元数据→DB marker-terminal→spawn。Claim前扫描孤儿marker并CAS收录；任何terminal marker缺receipt都禁止重跑writer。
- `FencedActionIntent`不可变；新fence只能创建唯一`FencedActionAdoption` CAS连接旧intent，不能改旧记录或创建冲突intent。可收养动作仅限`create_worktree/checkout_base/materialize_object_set/artifact_publish/promote_objects/finalize_worktree_index/finalize_worktree_head/create_task_ref/remove_worktree`；writer永不收养或重跑。
- `AttemptStatePolicy.v1` 是checked-in transition table，逐行固定source、operation/event、guard、允许副作用、target、exit code、retry policy和scheduler priority。主路径为`submitted→admitted→queued→claimed→running→verifying→closing→completed`；terminal为`completed/failed/cancelled`；未知state、operation或resolution组合统一退出2。
- `recovery_pending`表示已耐久停放、可释放capacity且下次必须优先恢复；`recovery_required/reconcile_required/cleanup_required`等待对应受限动作；`needs_auth/needs_environment/needs_authorization/stale_base/qualification_suspended/platform_incompatible`均不可claim。只有due的`retry_wait/platform_unavailable`可自动回队。
- Cancel：pre-spawn直接cancelled；running/verifying关闭Job并在缺完整receipt时进入recovery_required；closing仅记录枚举`cancel_reason_code`与时间并返回`accepted_deferred`。Retry仅允许无marker，或完整pre-tool terminal failure且零tool/mutation/GitAction、工作树等于base；始终新attempt/worktree。
- Resolve只允许`continue_verify/continue_closeout/retry_cleanup/terminate_failed`；不得生成stale-base superseding task。Reconcile仅核对并持久化报告，不创建Git/object/ref副作用；stale base必须显式重新prepare/submit。
- Authorization默认30天，claim时剩余期限≥attempt deadline+5分钟；submit、claim、spawn、heartbeat、verify、commit、task-ref、evidence和cleanup前重验active generation、revoke、expiry、sensitive fingerprint、environment/toolchain及base ref。Writer后撤销仍允许kill、drain、seal、quarantine、只读reconcile和recovery handoff；新Authorization只能通过唯一`AttemptAuthorizationContinuation`续verify/closeout，不能重跑writer。
- 释放capacity前必须证明Job无进程、journal已seal或进入durable recovery segment、无executing fenced action，并已在SQLite进入terminal或recovery_pending；scheduler取得capacity后先处理该recovery attempt。

## 7. SQLite、Journal、Artifact、Evidence与Backup

- SQLite固定`journal_mode=DELETE`、`foreign_keys=ON`、`synchronous=FULL`、`busy_timeout=5000`和短事务。核心表为`schema_migrations/tasks/attempts/leases/writer_markers/events/journal_segments/artifacts/artifact_outbox/fenced_actions/fenced_action_adoptions/git_actions/object_sets/authorizations/authorization_activations/authorization_continuations/environment_bindings/qualifications/runtime_activations/operator_actions`。
- UNIQUE至少覆盖submission hash、`(task_id,attempt_no)`、单active attempt、单writer marker、`(attempt_id,event_seq)`、segment number、`(attempt_id,action_kind,input_hash)`、唯一adoption、task ref、artifact logical name、Authorization active generation和单global capacity lease；所有attempt副作用同时绑定attempt ID和fence。
- Normalized event顺序固定为append segment→FlushFileBuffers→SQLite cursor事务。DB只能落后journal；恢复验证完整chain并补录有效tail。损坏segment不截断，原始异常字节复制到sealed quarantine，`JournalSegmentManifest`记录segment number、previous segment hash、accepted end offset、seq range及seal；continuation segment从最后有效event hash继续。
- 完整换行但非法JSON/schema/event的输入表示adapter/CLI不兼容并关闭Job；cancel、timeout或Job kill留下的EOF partial buffer属于attempt recovery；正常process exit后仍有partial line才是CLI framing incompatibility。
- Terminal `ExecutionReceipt`只有在Codex process exit、JSONL EOF、final schema通过、所有limits未超、event chain seal完成且Job内无活进程六项同时成立后发布；verifier/invariant test不得允许旁路。
- Artifact顺序固定为确定性命名的immutable spool temp写入+flush→SQLite outbox intent→同目录final temp写入+flush→no-replace atomic rename→read-back hash/size→SQLite terminal。Intent前孤儿temp进入quarantine且不自动收养；final已存在只在同intent/hash/size时确认。
- Commit message不包含最终evidence ID，避免EvidenceIndex包含commit SHA时形成内容寻址环。Commit只绑定冻结manifest；`ExecutionReceipt/CloseoutBundle`在commit/ref创建后建立commit、ref和evidence的完整关联。
- Backup仅为quiescent state/evidence backup：按canonical repo identity排序取得global、ownership registry和所有被引用repo mutex，要求零active lease、零non-terminal/recovery attempt、零pending outbox。包含DB、activation、policy、ownership、terminal evidence及被terminal对象引用的sealed quarantine；不含auth、environment内容、worktree、非终态spool或普通quarantine。
- Restore drill只恢复到新隔离root并验证schema、activation、ownership、object references和evidence chains；不得覆盖生产root。Task refs、terminal evidence和closeout在0.2不自动删除。

## 8. Git确定性与安全收口

- 第一条Git命令已经位于final environment、Job Object、overlay和`batch-git-audit`中。环境固定空HOME/global/system/hooks，设置`GIT_CONFIG_NOSYSTEM=1`、`GIT_CONFIG_GLOBAL=NUL`、`GIT_CONFIG_SYSTEM=NUL`、`GIT_ATTR_NOSYSTEM=1`、`GIT_TERMINAL_PROMPT=0`、`GIT_OPTIONAL_LOCKS=0`、`GIT_NO_REPLACE_OBJECTS=1`，清除其余继承`GIT_*`；operation-scoped变量只能由Git adapter设置。
- Git policy采用默认deny。`allow_name_only`只匹配remote URL/fetch/push、branch tracking及LFS endpoint/access，value及可能含URL的raw key不落盘；`allow_safe_value`仅匹配repositoryformatversion=0、bare=false、objectformat=sha1、refstorage=files及catalog化boolean/enum。include、credential/http/proxy/header、filter、diff/textconv、merge driver、hooks、signing、fsmonitor、SSH、URL rewrite、protocol/submodule、alias/editor/pager、外部attributes/excludes及未知key全部deny；重复singleton和非法值阻断。
- 固定controller overrides包括空hooks/excludes、`commit.gpgSign=false`、`core.fsmonitor=false`、`core.logAllRefUpdates=false`、`gc.auto=0`、`maintenance.auto=false`；diff始终使用`--no-ext-diff --no-textconv`。审计`.git/info/attributes`、`.git/info/exclude`、hooks、config.worktree、alternates、replace/grafts、base tree全部`.gitattributes/.gitmodules/.lfsconfig`、LFS、submodule和touched-path attributes。
- 写入顺序为ownership/fence→原仓审计→fenced create_worktree→hardened checkout→writer→protected path/OID/mode及writable-root reparse/hardlink复核→offline gates→attempt-local index/object graph→seal `ObjectSetManifest`→promote objects→task-ref CAS→finalize index/HEAD→evidence→remove worktree。
- Changed blobs、trees和commit全部先在attempt-local `GIT_OBJECT_DIRECTORY`生成，并以base objects作为只读alternates；在触碰common object store前持久化输入/index hash、每个object的type/size/OID/payload hash及完整可达图。Promotion为create-if-absent；existing object按Git canonical type+size+payload/OID验证，不比较loose zlib字节。
- Commit identity固定为`Local AI Runtime <local-ai-runtime@localhost.invalid>`，author/committer时间为claim时持久化的UTC秒和`+0000`。Message固定为`batch(<template_id>): <task_uuid> attempt <n>`加`Manifest: sha256:<resolved_manifest_hash>`；controller预计算canonical payload和expected SHA。
- Task ref固定为`refs/heads/codex/batch/<task_uuid>-a<1..3>`并通过`git check-ref-format`；`update-ref <ref> <expected-commit> <zero-oid>`只允许精确ref及其lock写面，reflog关闭。Task-ref前必须在清除alternates后证明commit/tree/blobs在common store完整可达。
- `finalize_worktree`禁止`reset --hard`。使用expected-tree临时index与受控materialization证明tracked path、mode和工作树字节等价且无任何untracked/ignored额外文件，再更新真实worktree index metadata和detached HEAD；否则保留并进入cleanup_required。
- 自动remove仅在runtime-owned、Job终止、fence匹配、GitAction/evidence terminal、HEAD/index/worktree完全干净时执行；remove后核验目录及common-dir worktree admin记录均消失。Dirty、recovery或不确定状态永久保留待人工处理，task ref始终保留。

## 9. 公共CLI、工作流与Runbooks

- CLI固定为：`runtime install|status|activate|rollback`；`platform setup|login|logout|auth-status|model-probe|sandbox-probe|qualify|doctor`；`environment register|verify|status|retire`；`repo register|verify|qualify|cutover|rollback|ownership-status|ownership-repair|maintenance enter|status|exit`；`authorization activate|revoke|status|verify`；`policy evaluate`；`batch prepare|submit|drain|status|cancel|retry|reconcile|resolve|doctor`；`contracts catalog|verify`；`gates run|verify`；`evidence verify`；`backup create|verify|restore-drill`；`eval baseline|compare`；`schedule install|status|run-now|remove`；只读`compat verify`。
- 所有CLI支持稳定`--json`结果；scheduler强制JSON。退出码为0成功/无ready task、2输入或状态契约错误、3 policy/Authorization/ownership/environment/stale/manual-recovery阻断、4 gate/evidence/eval/attempt失败、5 unavailable/needs_auth/qualification_suspended、6 platform_incompatible；非零均包含稳定reason_code、evidence locator和唯一建议命令。
- 正常Batch工作流固定为prepare验证base/qualification→submit幂等入队→drain取得locks/fence→preflight和worktree→marker/writer→journal/receipt→protected scan/gates→object promotion/ref→finalize/evidence/cleanup→completed。
- Runbooks必须分别覆盖`needs_auth`、`needs_environment`、`platform_incompatible/qualification_suspended`、recovery/reconcile/cleanup、ownership repair、repo maintenance、activation rollback、backup restore drill、repo cutover/rollback；每份包含前置条件、精确命令、stop conditions、证据和回滚。
- Scheduler使用当前用户InteractiveToken、Limited、Hidden、StartWhenAvailable、IgnoreNew，每5分钟最多drain一个task，ExecutionTimeLimit 12600秒；scheduled runtime禁止login/logout、environment preparation、ownership repair和cutover。

## 10. 重基线、实施切片与迁移

1. **P0 Truth Reset**：落地`ProductContract.v1 + BaselineManifest.v1 + WorkRoutingPolicy.v1`，原子同步AGENTS、README、PRD、架构、roadmap、plan、backlog、acceptance、planning status、selector/verifier；active queue改为`MINIMUM-OPERATOR-COMMIT-ONLY-TRANSITION`，selector必须返回`implement_legacy_guard_first`，删除supplemental token扫描和旧queue硬编码。旧runtime_v2 cutover路径及runbook降为legacy历史入口，禁止继续晋升。
2. **P0 Legacy Guard**：先落地ownership schema/catalog和legacy adapter，再覆盖legacy claim、lease、worktree、executor、writer、repo mutation、commit、Git、closeout及cleanup入口；枚举所有现有repo并注册为legacy owner。交叉conformance、crash、cutover和rollback drill未通过前，新Batch claim硬阻断。
3. **P1 Contracts/Storage**：依次实现Canonicalization、QualificationSensitiveInputSet、AttemptStatePolicy、SQLite schema/migrations、ArtifactWriter、journal segments和recovery invariants；每片不超过5个主要文件并有独立fixture/verifier。
4. **P1 Platform/Execution**：实现immutable installer/activation、toolchain/environment binding、keyring AuthState、ProcessEnvironmentCompiler、overlay、Job/mutex/fence、CodexCapabilityAdapter和full/quick/daily Q0 harness。
5. **P1 Git/Operations**：实现GitConfigPolicy/audit、worktree actions、attempt-local object graph、promotion/ref/finalize/remove、FencedActionAdoption、CLI、scheduler定义及全部operator runbooks。
6. **Q0**：使用同一pinned 0.144.1 binary和Sol/high完成真实能力测试；任一mandatory probe失败阻断P2，不建设fallback。
7. **P2 Self-host**：以一个低风险模板完成单个端到端commit-only slice及全部关键崩溃点恢复。
8. **P3 Scheduler**：安装计划任务并完成至少5个self-host commit-ready任务。
9. **P4 Portfolio**：资格化至少两个真实目标仓；完成30个scheduled observations，最多5个probe-only、至少25个commit-ready，self-host和两个目标仓各至少5个writer任务。
10. **P5 Cutover/Retirement**：逐仓在统一mutex下CAS cutover；未cutover仓legacy DB继续可写。全部目标仓cutover、零legacy active/closing且rollback drill通过后旧DB只读；连续30天零legacy调用后删除旧写面，compat reader和历史evidence永久只读。

## 11. 门禁、测试、指标与晋升

- 新包门禁固定为：`uv build --offline --project runtime/local-ai-runtime runtime/local-ai-runtime` → `uv run --frozen --offline --project runtime/local-ai-runtime python -m pytest` → `... python -m local_ai_runtime contracts verify` → `... ruff check .` → `... pyright` → planning verifier、selector和`git diff --check`。触及legacy guard时先补跑`uv run --project runtime/host-orchestrator python -m pytest`。
- Crash injection覆盖claim、lease、marker三阶段、JSONL partial/invalid、event append/fsync、DB cursor、artifact spool/intent/publish、gate、object materialization/promotion、ref、finalize、evidence和remove；所有大小、时间、path、override和command-line限制均测试`limit-1/limit/limit+1`。
- 安全硬门为未授权写入、敏感泄漏、错误Git副作用、重复writer、冲突object/commit/ref、错误cleanup及`successful_unauthorized_egress`均为0；生产denied-network-attempt使任务失败并阻断模板晋升，Q0故意deny probe单独统计。
- 30-task cohort只证明安全、可靠性和无人值守：commit-ready≥25、无人值守≥80%、人工介入≤20%、mandatory gates/evidence verify/backup restore/recovery drill均100%，且不存在未恢复状态；不使用该cohort替代严格配对效率结论。
- 效率至少使用12个相同snapshot、controller prompt、gate、qualification和任务分布的严格配对case，运行顺序按固定seed counterbalance；每个已声明模板族至少3个case且不得退化。`net_operator_minutes_per_success = 窗口内提交、监控、auth、qualification、失败/取消/恢复、模板及runtime维护总人工分钟 / commit-ready成功数`；失败人工进入分子，纯排队和初始研发成本单列。要求下降≥50%，并满足成功任务/操作者小时提高≥50%或P50周期下降≥30%。
- 首轮Q0、原型和30任务固定`gpt-5.6-sol/high`。未来每模板至少12组配对case、每case/config至少3次；安全、成功率、mandatory gates和人工介入不得退化，且实际P50墙钟或可归属成本改善≥20%。成本为含失败/retry的实际费用除以commit-ready成功数；无法取得费用时只能使用墙钟，token仅作诊断。
- 晋升通过新的`TemplateExecutionProfile + Authorization generation`静态激活并运行10-task canary。任何安全/gate失败、新失败类型、新人工介入或candidate归因的成功率下降立即停止新claim并CAS恢复上一generation；运行中禁止动态fallback。
- 状态晋升严格为`repo-side green → Codex platform compatible → scheduled live accepted → portfolio promoted`。Native任务、legacy证据、probe-only和repo-side simulation不得计入后续层级。

## 12. 固定假设、治理与依据

- Windows-first、单操作者、当前SID已登录；信任hash-pinned controller、当前SID和宿主机。DACL、Authorization和sandbox防御模型、repo内容、scheduled误操作及配置漂移，不宣称抵御已攻陷的同SID controller。
- 目标repo必须是本地固定卷上的标准SHA-1/files Git仓库，具有唯一`RepoProfile.local_base_ref`；prepare、submit、claim、spawn均验证同一ref精确指向expected base。不支持historical detached base、SHA-256 object format、reftable、active submodule、LFS filter或外部Git driver。
- Repo qualification必须阻断已知secret paths及资格化secret scanner发现；对源码中未知、未被识别的秘密不作绝对保证，因此安全结论表述为“已声明与已检测敏感信息零泄漏”。
- 对binary、model、profile、permission、feature policy、Git policy、state policy、canonicalization、adapter、probe、environment或schema的任何变化，都必须新建contract generation、执行full Q0并重新qualification/Authorization；安全硬门不接受waiver。
- 官方能力依据为[Permissions](https://learn.chatgpt.com/docs/permissions#define-and-select-a-profile)、[Shell environment policy](https://learn.chatgpt.com/docs/config-file/config-advanced#shell-environment-policy)、[AGENTS discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md#how-codex-discovers-guidance)、[Skills locations](https://learn.chatgpt.com/docs/build-skills#where-to-save-skills)及[Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)。本机0.144.1 help只作为当前取证，最终能力必须由安装时Q0重新生成并绑定。
