# Local AI Runtime 0.2 v3.22：Windows-Local Governed AI Development Runtime Baseline Candidate

## 0. 结论与状态

- 本文的 narrative specification ID 为 <code>local-ai-runtime-0.2-v3.22</code>；它只与本文最终归档的精确字节一对一绑定。本文字节或本文声明的语义发生变化时必须创建新的 narrative specification ID，禁止同一 ID 对应不同正文。
- 当前状态为 <code>baseline_candidate</code>，阻断阶段为 <code>baseline_approval</code>。
- 本文在产品、架构、协议、工作流、迁移、治理、自治、恢复、验收和最少人工约束上自包含；但最终可批准基线是一个多文件规范包，而不是只靠一篇 Markdown。
- 规范包由本文、Tier A/Tier B schema、catalog、完整 transition table、example、negative fixture、migration specification 和 verifier 组成；每个非本文 artifact 使用自己的稳定 artifact ID、schema/version 和 content hash，最终由不可变 <code>BaselineManifest.v1</code> 内容寻址。
- 本文不声称基线已批准、P0/P1 已实现、Codex/Windows/Git 已通过 Q0、Batch 已上线或目标仓已切换。
- v3.22 语义上完整替代 v3.14-v3.21。实现者不得查阅旧正文或旧评审来补全缺失字段。
- 产品长期定位是：面向 Windows 本机、单操作者信任域、以受资格化开发 authority 为锚的通用受控 AI 开发执行平台。Architecture Epoch 1 / Runtime 0.2 只实现 <code>qualified_git_repo_v1</code> authority、全局 capacity=1 和单一 SQLite 控制面；不预建跨平台、多租户、分布式或第二 agent runtime 空壳。
- 0.2 冻结的 capability set 是 <code>codex_exec_v1/sha1_files_refs_v1/local_commit_task_ref_v1/task_egress_denied_v1</code>；初始 ExecutionProfile 固定 Codex 0.144.1、<code>gpt-5.6-sol/high</code>、commit-only、keyring-only 和确定性 Git object。它们是已资格化 generation，不是不可演进的产品身份。
- 目标采用词典序：安全和副作用正确性为硬门；其次最小化净人工分钟；再提高无人值守完成率；最后优化周期和可归属成本。0.2 不追求并发。

## 1. 规范身份、谱系、字节与批准

### 1.1 版本谱系

- <code>canonical_predecessor</code>：v3.14，SHA-256 为 <code>B4133FF27E1FACD0B2B8C48BB89D5FDC4006AD379203BFEF78B4AF6CDAC9DDB2</code>。
- <code>withdrawn_draft</code>：v3.15，无独立归档的 canonical hash。
- <code>withdrawn_candidate</code>：v3.16，45,316 bytes，SHA-256 为 <code>6EAF5320495247661052974333023B1131A1B12A6BFD60BD730975489BB1A9ED</code>。
- <code>superseded_candidate</code>：v3.17，32,825 bytes，SHA-256 为 <code>A285F5F421A8CCD4DEBD8794609A2AA0EB07BB1BF651C2467A95F7CAD25A5F81</code>。该身份已从原始 session 的单一 message/content boundary 精确归档，并由 pinned Python hashlib 与 PowerShell Get-FileHash 独立复算；它不再标记为 provisional。
- v3.18 出现两份不同正文却使用同一 ID，固定记为 <code>conflicted_candidate_id</code>，不得选一份静默当作 canonical。归档 A 为 66,328 bytes、SHA-256 <code>6924BA562DDA8E69274EB80FEF9E3A9699EB493570EE08330FCAD5EC4BC3BAA5</code>；归档 B 为 43,908 bytes、SHA-256 <code>8DA5AA20FB44D95503E443822163397A2AA1DF590E1916D1A5A10A6C24EA06B7</code>。两份均已从原始 session 单一 message/content boundary 精确归档并双路径复算。
- <code>superseded_candidate</code>：v3.19，111,952 bytes，SHA-256 为 <code>275306D2E88BAAFA803170EE4EF99FB822C4E13769721B806805B834BB9D7670</code>。该 hash 直接覆盖仓库中保留的 v3.19 原始字节，不对其执行 canonicalization。
- <code>superseded_candidate</code>：v3.20，130,890 bytes，SHA-256 为 <code>43CB98737DAA5D171A9CDA2DCA49C8F118FB8BE92745B4076948D9178E56A130</code>。v3.20 冻结前曾出现多个中间字节序列；它们只进入非规范 review evidence，只有上述已归档最终字节进入 candidate lineage。
- <code>superseded_candidate</code>：v3.21，158,485 bytes，SHA-256 为 <code>1BFB5CD2C92C036804A6005D5B36CDD5ACC6BEDC4D6BF4070CCFB7A70CE063FB</code>。该文件保持冻结，只作为 v3.22 的精确规范前身，不接受原地修改。
- 评审文件只进入独立、append-only、hash-chained 的 <code>ReviewEvidenceIndex.v1</code>，不得混入规范前身链或改变运行语义 hash。

### 1.2 规范字节

- 规范文件必须已经是 UTF-8、无 BOM、LF-only、Unicode NFC、恰好一个末尾 LF。
- 禁止 CR、NUL、除 LF 之外的全部 Unicode <code>Cc</code>、全部 Unicode <code>Zl/Zp</code> line/paragraph separator、未由 schema/catalog 明确批准的全部 <code>Cf</code>、BOM、bidi controls、zero-width characters、Unicode noncharacters、行内 HTAB 和行尾 SP/HTAB。Markdown 强制换行使用 <code>&lt;br&gt;</code>。
- Validator 只验证并拒绝，不得改写编码、Unicode、空白、换行、JSON key 或数组后再计算 hash。
- SHA-256 直接计算通过验证的原始字节。规范正文不嵌自身 hash；关闭文件后由 BaselineManifest 记录。
- JSON parser 必须拒绝重复 key，canonicalizer 不得通过修复输入掩盖非法数据。
- 相同字符策略同时适用于所有 canonical JSON string、ID、reason code、Git ref 和公开 evidence string；需要保留的格式字符必须按字段在版本化 allowlist 中逐项批准，不能用 Unicode category 整类放行。

### 1.3 规范包与批准记录

BaselineManifest 至少绑定：

- 本文；
- 全部 Tier A schema/catalog/policy/transition/example/fixture/verifier；
- P0/P1 所需 Tier B persistence schema、migration specification 和 migration fixture；
- 0.144.1 Codex feature policy；
- process environment、permission overlay、Git config、reason code、secret scan、quarantine crypto 和 guard catalog；
- 已归档谱系及组装 manifest 前冻结的 <code>package_review_head</code>。Manifest closure review 在其后 append，不能形成自引用。

规范包版本语义固定为：

- 本文已声明但当前缺失的 artifact，首次按其声明的 artifact ID/version 物化，只是关闭 package inventory 中的 missing 项，不改变 v3.22 narrative bytes 或 ID；
- artifact 一经标记 present，其精确 bytes/hash 即不可原地改写。修正文档语义、修改已存在规范 artifact 的行为、替换 schema/catalog/transition/verifier 安全默认值，必须创建新的 artifact version；若该变化与本文声明不一致或改变 baseline 行为，同时创建新的 narrative candidate；
- preapproval inventory 是非规范、可更新的工作记录，不是 BaselineManifest。BaselineManifest 只能在全部 artifact present、逐项验证和 review head 固定后一次性创建；创建后 immutable，任何替代使用新 manifest generation 和显式 supersession；
- artifact 文件名、artifact ID、schema version 和 manifest entry 必须一一对应。不得通过覆盖同路径、复用旧 version 或只更新 hash 来隐藏语义变化。

只要存在缺失条目、可变字节、未验证 hash、未裁决占位标记或不完整 transition row，就不得开始 runtime 实现。

- <code>BaselineApprovalRecord.v1</code> 是不可变记录，绑定 narrative specification ID/hash、BaselineManifest ID/hash、全部 artifact ID/version/hash、<code>approval_review_head</code>、批准 authority、批准者 SID hash、UTC 微秒时间和 generation。Approval head 必须是 manifest 中 <code>package_review_head</code> 的可验证后继，并包含 manifest closure review；后续 review 继续 append，但不改既有 manifest/approval bytes。
- Approval 只能由 BaselineManifest 锁定的独立 governance entrypoint <code>scripts/approve-local-ai-runtime-baseline.py</code> 执行受控、外部、交互式 <code>baseline approve</code> operator action；它在新 runtime 尚未实现时也可由 pinned Python <code>-I -s -E</code> 启动，但不是普通脚本直接写 JSON。<code>BaselineApprovalCommandPolicy.v1</code> 固定 entrypoint bytes/hash、允许的 InteractiveToken/session、operator SID、command envelope hash、一次性 challenge、expected inactive generation、manifest/review head、UTC expiry 和 response-loss replay key；同一 <code>approval_request_id</code> 由 UNIQUE 和 active-head CAS 保证最多一个 terminal result。重放先返回既有记录，再评估仅适用于首次创建的 challenge/current guards。Verifier 必须拒绝 scheduled/service token、过期或重复 challenge、authority 不匹配、expected generation 漂移和绕过 command handler 的文件注入。
- 该记录只证明一个已授权的同 SID operator action按协议发生；字段、hash、session 或 challenge 不构成对物理人类在场的密码学证明。职责分离、组织级审批或外部签名只有在未来独立 governance capability 中实现后才可声称，不是 0.2 默认要求。
- 撤销/替代使用 append-only 的 <code>BaselineApprovalRevocationRecord.v1</code>/<code>BaselineApprovalSupersessionRecord.v1</code>，并通过 active-approval generation CAS 生效。旧 approval 文件存在不代表仍有效。
- 三层门固定为：
  1. Baseline Approval：允许 Truth Reset 和 P0/P1 实现。
  2. Implementation Acceptance：确认代码、迁移、runbook、conformance、crash、backup 和 rollback 证据。
  3. Full Q0 / P2 Admission：证明当前宿主与 pinned toolchain 的真实行为，且只有它允许 P2 writer vertical slice。
- Q0 只阻断 P2；Baseline Approval 阻断 Truth Reset/P0/P1；Implementation Acceptance 不等于 platform compatible。

## 2. 产品终态、战略与信任边界

### 2.1 统一产品面

产品终态是一个 Windows-local、single-operator、general-purpose governed AI development runtime，长期承载代码、文档、构建、测试、静态检查、Git、制品和本地开发工具等受控工作流。每个无人值守任务仍必须绑定已资格化的 repo/workspace authority、封闭输入、明确可观察副作用、机械验收和可恢复交付；任意桌面自动化、生产操作或自由 prompt 不属于该产品声明。

0.2 是该终态的 Epoch 1 首个受治理 profile，包含四个入口：

1. Codex Native Direct：明确的一次性交互任务，由人控制执行和集成。
2. Codex Native Spec：最多询问三个真正影响结果的问题，然后生成 decision-complete 的 <code>TaskSpec.v1</code>，不自动执行。
3. Codex Native Program：仅用于至少两个独立写集合且集成顺序已固定的任务；可使用 Native subagents/worktrees，但由人工集成，不继承 Batch receipt/fence。
4. Batch：只接受 allowlisted、低风险、host-local 模板，全局同时最多一个 writer，只交付确定性本地 commit 和 runtime-owned task ref。

Python Policy/Evidence Kernel 负责 qualification、Authorization、状态、隔离、恢复、Git 发布、evidence 和治理。稳定内核长期冻结 task/attempt/generation/lease/fence/CAS、single-authority writer grant、可恢复副作用、secret-safe evidence、approval/acceptance/Q0/activation 分层、canary 和 rollback；模型输出永远不是 truth。Legacy/Hermes/AgentBridge 最终仅保留只读兼容。

~~~mermaid
flowchart LR
    N["Native Direct / Spec / Program"] --> H["Human-controlled integration"]
    S["Closed BatchSubmission"] --> K["Python Policy / Evidence Kernel"]
    K --> Q["SQLite queue + global capacity 1"]
    Q --> P["Runtime composition + active identity"]
    P --> C["ExecutionProfile / Codex adapter"]
    P --> X["Windows / Git / toolchain capabilities"]
    C --> W["Detached worktree"]
    W --> G["Offline sandboxed gates"]
    G --> O["Planned deterministic Git objects"]
    O --> R["Task ref"]
    R --> E["External evidence + cleanup/recovery"]
~~~

### 2.2 路由和禁止边界

- 自由 prompt 永不自动进入 Batch。
- Native Spec 只有先被操作者固化为版本化 TaskTemplate，并完成 repo/template qualification 和 Authorization，才可提交 Batch。
- GUI、生产、数据库迁移、VPS/remote、凭据、破坏性、不可逆、高风险或含糊任务始终走 Human-controlled Native。
- BatchSubmission 只含 <code>repo_id/template_id/parameters/expected_base_commit</code>。
- Batch 禁止多 writer、subagent、task Approval、SDK、多 Provider、动态 fallback、controller/gate dependency install/restore/bootstrap、task-side network、remote Git、fetch/merge/push、target-ref 更新和 task-ref 删除；writer 侧按 QualifiedEnvironment、permission、network、path、write-budget 与 delta policy机械约束，不宣称能语义识别所有名为 setup/install 的源码操作。
- Batch 唯一交付为 local deterministic commit 与 <code>refs/heads/codex/batch/&lt;task_uuid&gt;-a&lt;attempt_no&gt;</code>。人工负责最终检查和 merge/push。
- <code>batch_commit_only_v1</code> 的禁止项是 0.2 generation 的硬安全边界，不是暗示未来能力已存在。新模型、effort、工具版本、已证明 envelope 内的收窄资源参数和 gate 选择可由新 ExecutionProfile generation 表达；新 Provider、受限网络、remote delivery、其他 Git object/ref format 或 workspace authority 必须先有新的 capability protocol、adapter、schema、effect ledger、recovery matrix、Implementation Acceptance 与 Full Q0；多 writer、多操作者、多信任域或同一 effect domain 并行必须创建 successor architecture epoch。协议未实现并验收前一律 <code>unsupported</code>，不得以配置开关启用。
- 生产变更、不可逆外部副作用、凭据代理和 GUI 默认长期保持 Human-controlled。即使未来 capability 存在，也不得自动继承普通 Batch 的 Authorization 或安全声明。

### 2.3 最少人工约束

- 正常 scheduled task 不得要求逐任务 prompt、approval、qualification 或 Authorization。
- Authorization 必须可在 <code>repo_id + template_id + policy generation</code> 上复用，不能绑定单一 submission 或普通源码 commit。
- 人工只处理 login、environment/repo/template qualification、Authorization 生命周期、受管 Native maintenance、cutover/rollback、显式 resubmission，以及无法自动证明的 recovery/repair。
- 新 OperatorAction 必须减少的重复人工多于新增人工；一个原子审计命令能完成的操作不得拆成两步 permit。
- 总体无人值守比例由“可进入已晋升 TaskFamily 的工作占比 x 该 TaskFamily 无人值守成功率”共同决定。平台不得为提高该比例自行发明项目目标、扩大 risk/effect envelope、修改 gate 或把自由 prompt 晋升为 Batch；持续收益来自可复用 WorkDefinition/TaskFamily、可靠 gate 和有界 Authorization。

### 2.4 信任与安全声明

- 信任 hash-pinned controller/toolchain、当前 Windows SID、OS keyring、runtime integrity key 和宿主 OS。
- Repo 内容、project config/instructions/skills 和模型输出均不受信任；runtime 通过封闭输入、permission/network/path budget、authority/fence/intent/read-back、gate 和 deterministic publication 机械限制它们可造成的副作用，并检测已声明的漂移、重放、path escape 和不确定 Git 结果。
- 不声称消除 prompt injection、语义误导、错误 patch、恶意但仍落在已授权写集内的内容，或证明模型理解了操作者意图。只有机械 gate、human review 和后续 outcome evidence 能分别提供其声明范围内的质量证据。
- 不声称抵御已攻陷的同 SID controller/operator、内核、管理员/SYSTEM、firmware、物理访问或 memory/pagefile 提取。
- 安全结论只使用“已声明与已检测敏感信息零泄漏”，不声称证明未知秘密不存在。

## 3. 架构、安装与运行根

### 3.1 当前真值与新模块

- Truth Reset 前，运行真值仍是 <code>runtime/host-orchestrator</code> 与 <code>.ai/state/control-plane.db</code>；预批准 planning queue 是 <code>LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE</code>，它只管理候选规范闭包，不代表新 runtime 已实现。
- Truth Reset 后，新代码归宿为 <code>runtime/local-ai-runtime/src/local_ai_runtime/</code>，采用 Python 3.11.x 模块化单体；具体 patch、absolute path、version、file identity 和 SHA-256 由 RuntimeToolchainManifest 锁定。
- 模块边界为 <code>contracts/kernel/qualification/storage/execution/recovery/git_local/operations/compat</code>。
- 新包不得 import、调用或双写 host_orchestrator。
- Legacy 与新 runtime 只共享 checked-in ownership wire schema、repo mutex naming algorithm 和 generation 语义，不共享数据库或 Python module。
- Epoch 1 的长期实现形态保持 Python 模块化单体 + 单机 SQLite authority + 外置 evidence + 极薄、版本化、内容寻址的 Windows native helper。Native helper 只封装 token、Job、handle、ACL、原子文件和 DPAPI 等已批准 Win32 调用，不承载 policy；不引入本地 Web 服务、微服务、RPC、通用 storage/OS abstraction、插件市场或分布式 workflow engine。

### 3.2 生产根与 attempt 拓扑

生产根固定为 <code>%LOCALAPPDATA%\LocalAIRuntime</code>：

~~~text
versions/                 immutable installed versions
policies/                 content-addressed policy packages
schemas/                  content-addressed schemas
codex-home/               managed Codex config plus sandbox state roots
state/                    SQLite and controller state
authorization/            immutable Authorization objects and active map
ownership/                per-repo ownership registries
environments/             immutable qualified dependency bundles
evidence/                 immutable external evidence
backups/                  quiescent state/evidence backups
quarantine/               ACL-restricted encrypted incident material
reserve/                  controller-owned preallocated emergency disk reserve
runs/<attempt_uuid>/       attempt-local writable state
locks/                     diagnostics only, never lock truth
temp/                      controller-only replace/publish staging
~~~

每个 attempt 独占 <code>profile/xdg-config/codex-sqlite/tmp/cache/spool/gate-runs/object-store/worktree/empty</code>。不同 attempt 不得共享任何可写 HOME、SQLite、APPDATA、TEMP、cache、spool 或 gate output。Codex Windows sandbox 的受管可写状态不属于 attempt HOME，而由 <code>CodexSandboxStateBinding.v1</code> 单独约束。

| Class | Roots | Writer/gate view | Lifecycle |
|---|---|---|---|
| immutable_shared | versions, policies, schemas, codex-home/config, environments | exact allowlisted read/execute only | offline staged, content-addressed, activation 后不就地修改或删除 |
| sandbox_mutable | codex-home/.sandbox | 仅 pinned Codex sandbox helper 与受管低权限 sandbox SID/group 按 Q0 证明的最小权限访问 | 绑定 setup generation、ACL、owner、root identity、opaque 日志上限和轮换结果；不得被误当 immutable config |
| sandbox_secret | codex-home/.sandbox-secrets | 仅 sandbox broker/helper 按官方协议访问，writer/gate/Git/controller evidence projection 均不可读 | 永不进入 manifest、evidence、backup、content hash 或普通诊断；删除/重建只经交互式 platform setup |
| controller_mutable | state, authorization, ownership, evidence, backups, quarantine, reserve, temp | denied，或只暴露明确 external evidence locator | controller 通过 fence/no-replace/atomic replacement 管理 |
| auth_mutable | Windows current-user keyring | 仅 Codex parent 通过 qualified auth adapter 使用 | 只由 interactive login/logout 改变；无 file fallback |
| attempt_writable | runs/&lt;attempt&gt;/profile/xdg-config/codex-sqlite/tmp/cache/spool/gate-runs/object-store/worktree | 按 process permission profile 的精确子集 | CREATE_NEW tree，绑定 attempt/fence，terminal 后 fenced cleanup |
| managed_empty | runs/&lt;attempt&gt;/empty 及每个 operation 的专用 empty root | allowlisted read/list，始终 deny write | spawn 前后都证明为空且 identity 不变；任何 entry 都使 operation 失败 |

所有 runtime-owned root 首次创建都应用并 read-back current SID + SYSTEM 的 protected DACL、owner、volume/file identity 和 non-reparse ancestors。身份角色必须分开建模：controller、交互式 operator process 和 pinned Codex parent 运行在当前用户 SID；由 qualified Windows sandbox 启动的 writer tool、gate、Git 和 task-side helper payload 使用 <code>CodexSandboxStateBinding</code> 绑定的专用低权限 sandbox SID/group，不得把它记录为 current SID。只有明确列入 controller helper catalog、无 repo/task effect 且不进入 sandbox 的 host helper可继续使用 current SID。普通 current-SID DACL 只能保护 controller roots免受其他账户访问，不能在 controller 与同 SID Codex parent/host helper之间形成授权边界；sandbox token、permission profile、空 environment、Job、handle/path identity和spawn verifier共同承担task隔离。若实际 token user/group 与 Binding 不同，或 sandbox payload仍能以current SID权限打开controller/auth/evidence handle，立即判 <code>platform_incompatible</code>。

### 3.3 Immutable install 与 activation

- <code>RuntimeToolchainManifest.v1</code> 锁定 Python 3.11.x 的具体 patch、uv、uv.lock、PowerShell、Git、Node/npm wrapper、<code>@openai/codex@0.144.1</code>、bundled codex.exe、Windows build、sandbox、Job helper、CapabilityAdapter、bootstrap 和 Q0 probes 的 absolute path、version、SHA-256、volume/file identity 及必要 publisher。
- 版本安装到 <code>versions/&lt;content_hash&gt;</code>，activation 前变为只读。
- Task Scheduler 运行受管绝对 PowerShell <code>-NoProfile -NonInteractive</code>，验证 manifest 后以绝对 pinned Python <code>-I -s -E</code> 启动。
- 不运行源码 checkout，不通过 PATH 发现 Python、Node、uv、Git 或 Codex。
- Runtime composition 的非循环链固定为：

~~~text
RuntimeCompositionManifest C
  = architecture_epoch + approved normative baseline + capability set
    + ExecutionProfile + implementation/toolchain/adapter/schema/probe hashes
    + staged_installation_identity
-> ImplementationAcceptanceRecord I(C)
-> FullQ0Record Q(C, I, staged_installation_identity)
-> RuntimeActivationBundle B(C, I, Q, expected_previous_active)
-> RuntimeActivationRecord A(B, pointer_result, immediate_preflight_result)
~~~

- Q 在 <code>current.json</code> 仍指向旧版本时测试 staged immutable installation；它绑定 C、I 和 staged identity，不绑定尚不存在的 B/A，因而无 hash 自引用。B 是 C/I/Q 的唯一完整组合，禁止分别维护 architecture/profile/capability active heads。
- <code>current.json</code> 是唯一版本选择指针。首次创建使用 CREATE_NEW；升级/回滚必须持有 <code>Global\LocalAIRuntime.Activation.&lt;SIDHash&gt;.v1</code> 专用 named mutex并验证第 8.2 节同等的 type/owner/DACL/name policy，在锁内重读并验证 expected previous generation/checksum，写 durable <code>RuntimeActivationIntent.v1</code> 并 flush，重新核验 staged identity，使用 durable temp、FlushFileBuffers、ReplaceFileW 类原子替换，最后 read-back pointer generation/checksum。ReplaceFileW 本身不是 compare-and-swap；mutex、expected-head 重验、intent 和 read-back 共同构成 CAS 协议。
- 指针成功后立即运行 bounded quick preflight，再写 immutable A。<code>SelectedRuntimeIdentity</code> 是 domain-separated canonical envelope <code>{bundle_hash,resulting_generation,current_pointer_checksum}</code> 的 SHA-256；只有 A 的 terminal result 为 <code>activated_and_preflight_passed</code> 时，<code>ActiveRuntimeIdentity</code> 才作为 envelope <code>{selected_runtime_identity,activation_record_hash}</code> 的 SHA-256 存在。指针 CAS 成功但 preflight 失败时结果为 <code>selected_not_admitted</code>，平台 suspended，禁止新 production qualification、Authorization 或 attempt。
- SQLite 只保存 activation intent、immutable result 和查询索引，不保存第二个 active-version head。未终结 intent 使 activation recovery 优先并阻断下一 activation 和正常 claim；recovery 必须补写同一个稳定 terminal result或明确 rollback，不得因 observation UTC、重试次数等非确定字段生成不同 result identity。<code>UNIQUE(activation_request_id)</code>、bundle/resulting generation 唯一约束和 response-loss replay 保证每个请求至多一个 terminal A。
- Staged qualification、I 和 Q 可以绑定 C/staged identity；任何作为生产 authority 输入的 Repo/TemplateQualification、Authorization、ResolvedAttemptManifest、receipt 和 evidence 都必须绑定 ActiveRuntimeIdentity。旧 active identity 在新指针被选择后不自动授权新 claim；rollback 也必须形成新的 B/A 和 resulting generation。
- Rollback 要求零 active/nonterminal attempt，并证明 state/schema/toolchain 向后兼容。

### 3.4 文件系统范围

- 0.2 只支持通过 no-replace、ReplaceFileW、FlushFileBuffers、identity、ACL、hardlink、reparse、alias-aware 8.3 verification 和 power-loss probe 的本地固定 NTFS 卷。
- 不声称通用 Windows parent-directory fsync。
- Network share、ReFS、FAT、removable、cloud-synced root、subst alias 和未知 filter driver 均不支持，除非新 contract generation 和 Full Q0 明确资格化。
- 0.2 不要求管理员全局禁用 NTFS 8.3 short-name creation，也不把卷级策略可查询性当作普通用户运行的必要条件。Qualification 记录能够观测到的 volume policy、每个受管 component 的 long/short alias 和 probe outcome；无法读取卷级策略时记录 <code>policy_query_denied</code>，并转由不提权的 alias/identity Q0 证明补足，不能伪写为 disabled。
- 所有 path authorization 最终以 no-follow handle、volume identity、FILE_ID_128、expected root ancestry、owner/DACL 和 reparse/hardlink policy 判定；long path、short alias、case variant 或字符串 final path 都不能单独授予权限。Q0 必须证明使用现存或 probe 创建的 short alias 无法绕过 protected root、approved path、deny path、cleanup ownership 或 evidence boundary。
- Alias set、volume policy observation、final identity 或 alias-bypass probe 结果在 qualification 后漂移时，目标 repo/runtime volume 进入 requalification_required 并停止对应新 effect。只有无法建立 handle identity、alias 指向冲突对象或 alias 能绕过 policy 时才判 incompatible；不能仅因系统允许生成 8.3 名称而永久阻断 P2。

## 4. 契约分层与 canonicalization

### 4.1 Tier A

每个 Tier A 对象必须同时提供 Spec、JSON Schema、positive/negative example、catalog/policy 和 verifier。至少包括：

- <code>BaselineManifest/ProductContract/WorkRoutingPolicy/NativeSessionPolicy/TaskSpec/CanonicalizationPolicy</code>；
- <code>SpecificationBytePolicy/BaselineLineage/ReviewEvidenceIndex/BaselineApprovalCommandPolicy/BaselineApprovalRecord/BaselineApprovalRevocationRecord/BaselineApprovalSupersessionRecord</code>；
- <code>RepoProfile/WorkDefinition/TaskFamily/TaskTemplate/BatchSubmission/ResolvedBatchManifest/EffectPlan/GateGraph/EvaluationProfile</code>；
- <code>Authorization/AuthorizationRevocation/ResubmissionPolicy/GatePolicy/GitConfigPolicy/GitObjectPolicy</code>；
- <code>ArchitectureEpochPolicy/CapabilitySetManifest/ExecutionProfile/RuntimeCompositionManifest/ImplementationAcceptanceRecord/FullQ0Record/RuntimeActivationBundle/RuntimeActivationRecord</code>；
- <code>RuntimeToolchainManifest/QualifiedEnvironmentBinding/CodexSandboxStateBinding/CapabilitySnapshot</code>；
- <code>OwnershipWirePolicy/NamedObjectPolicy/ProcessHandlePolicy/ResourceLimitPolicy/WriteAccountingPolicy/HardWriteQuotaCapability/SchedulerPolicy/BackupPolicy</code>；
- <code>CodexFeaturePolicy/ProcessEnvironmentPolicy/PermissionOverlayPolicy/SecretPolicyCatalog/QuarantineCryptoPolicy</code>；
- <code>CapabilityAdapter/Q0TriggerPolicy/Q0ProbeCatalog/ResolverCatalog/ReasonCodeCatalog</code>；
- <code>ExecutionReceipt/EvidenceIndex.v2/CloseoutBundle.v2/WorkflowEffectMetrics.v1</code>；
- <code>SubmissionFamilyStatePolicy/BatchTaskStatePolicy/AttemptStatePolicy/PlatformOperationalStatePolicy/RepoCutoverMaintenancePolicy/TemplateLifecyclePolicy/AutonomyPolicy/GuardCatalog/OperatorActionCatalog</code>。

这些名称不是插件接口。<code>WorkDefinition</code> 固定目标、closed parameters、允许 effect 和完成条件；<code>TaskFamily</code> 版本化同类任务的 qualification、risk、evaluation 和 promotion rules；<code>RepoProfile</code> 固定 authority identity、protected surface、toolchain 和 gate；<code>EffectPlan</code> 在执行前枚举 file/process/Git/evidence 的 logical effect identity、authority、postcondition 和 recovery class；<code>ExecutionProfile</code> 只选择 CapabilitySet 已实现并证明的 provider/model/effort/permission/sandbox/resource envelope；<code>CapabilitySnapshot</code> 记录某代 Codex/Windows/Git/toolchain 的实测能力；<code>GateGraph</code> 是有界 DAG，不是自由命令；<code>EvaluationProfile</code> 固定分母、人工分钟、质量观察和停止规则。0.2 只物化 Codex、qualified Git repo 和 commit-only 所需实例，不建设动态 provider loader、通用 IStorageBackend、IOperatingSystem 或插件市场。

Provider 术语必须分开：<code>ModelProfile</code> 是 model/effort 参数；<code>ModelProviderCapability</code> 是 auth/control-plane/network/event contract；<code>AgentRuntimeCapability</code> 是 Codex CLI execution/config/tool protocol。0.2 catalog 三者都只有经过 Q0 的 Codex/OpenAI 实例；不得把第二 model 名称误当第二 Provider，也不得为未来 Provider/agent runtime 建空 adapter。

演进分为三个机械层级：

1. Profile generation：在既有 CapabilitySet 已证明 envelope 内选择 model/effort、工具版本、timeout、resource limit、allow path 和 GateGraph；按 Q0TriggerPolicy 执行 scoped requalification、Authorization、canary 或 Full Q0。
2. Capability generation：引入新 Provider、network、delivery、Git format、workspace authority 或其他新外部 effect protocol；必须有 adapter/schema/effect/recovery/migration、Implementation Acceptance 和 Full Q0，不能只改 profile。
3. Architecture epoch：改变 writer concurrency、operator/trust domain、authority topology 或控制面一致性模型；必须创建 successor baseline、migration 和完整 crash/conformance matrix。Epoch 1 固定单控制面、单 SQLite authority、全局 capacity=1。

运行态只有一个 RuntimeActivationBundle 和一个 ActiveRuntimeIdentity。Profile 只能引用已经出现在同一 C/I/Q 中的 capability；未实现或未共同验收的组合即使 schema 可表达也必须拒绝。

### 4.2 Tier B 与 Tier C

Tier B 至少包括：

- qualification：<code>QualificationObservation/QualificationSensitiveInputSet/RepoTemplateQualification/InstructionSnapshot/SkillInventory/FeatureInventory</code>；
- execution：<code>ResolvedAttemptManifest/AttemptRecord/AttemptProcessEnvironment/AttemptPermissionOverlay/WriterFinalResult/GateRun/GateReport</code>；
- process/recovery：<code>JobIdentity/WriterLaunchRecord/StageLaunchRecord/ChildHandleManifest/WriteAccountingSnapshot/EmergencyDiskReserveRecord/JournalSegmentManifest/NormalizedExecutionEvent/AttemptAuthorizationContinuation/AuthorizationExecutionGrant/SafetyOnlyExecutionRecord</code>；启用 optional hard-quota mode 时另有 <code>HardWriteQuotaReservation</code>；
- Git：<code>GitPreflightReport/GitObjectPlan/ObjectSetManifest/GitAction</code>；
- fencing：<code>FencedActionIntent/FencedActionAdoption/FencedActionHead/FencedActionResult</code>；
- storage/evidence：<code>ArtifactOutboxRecord/QuarantineSeal/QuarantineKeyEnvelope/RuntimeIntegrityKeyEnvelope/BackupManifest/BackupRestoreEligibility/BackupPostActivity/BackupRestoreIntent/EvidenceProjectionAcceptance</code>；
- governance：<code>AuthState/TaskResolution/TaskResubmission/OperatorAction/OperatorWorkSession/RepoMaintenanceRecord/CutoverRecord/RuntimeActivationIntent/SelectedRuntimeIdentity/ActiveRuntimeIdentity/BaselineApprovalRequest/BaselineApprovalCommandResult</code>。

Tier C 只保存内存类型和 test fixtures。

### 4.3 Canonical JSON

- 拒绝 duplicate key、float、非 NFC string、越界 integer、nullable optional 和 unknown field。
- Object key 按 UTF-8 byte lexicographic order 排序，使用最小 JSON escaping，无多余空白。
- Array 默认保序。只有 schema 明确标记 <code>set_semantics</code> 并声明唯一 sort key 才能排序；重复 key 直接拒绝，不能静默去重。
- 可复算对象使用 domain-separated envelope：

~~~json
{"domain":"local-ai-runtime/<object-type>/v1","schema_version":1,"payload":{}}
~~~

- Hash 为 canonical UTF-8 envelope 的 lowercase SHA-256；对象自身 hash 字段不进入 payload。
- Durable timestamp 为精确六位小数的 UTC Z；live deadline 使用 monotonic clock，durable record 同时绑定 boot identity。

### 4.4 Git path 与 Windows path

- Git path 保留原始 UTF-8 spelling、case 和 <code>/</code>，只验证 NFC，不做规范化改写。
- 拒绝 invalid UTF-8、non-NFC、absolute、empty component、<code>.</code>/<code>..</code>、backslash、ADS、DOS device、控制字符、trailing dot/space alias 和 Windows case collision。
- <code>windows_collision_key</code> 由版本化 invariant-uppercase catalog 单独生成，不替代 Git path。
- Host path 必须由 handle 得到 absolute final path、volume/file identity；字符串相等不能证明 ownership 或无 escape。任何 Win32/DOS/8.3 alias 只有解析到同一受管 root 和同一预期 FILE_ID_128 后才可继续，且权限决策仍使用原始请求 class 与 approved path ID，不能因 alias 等价扩大 allowlist。

## 5. Template、submission family 与显式重提

### 5.1 封闭参数

- <code>TaskTemplate.parameters</code> 固定 <code>additionalProperties=false</code>。
- 只允许有界 enum、bool、integer、public ID、approved-relative-path ID 及其有界数组。
- 禁止任意 string/free object、secret、prompt、command、argv fragment、environment、URL、Git ref、model/provider name 和无界 path interpolation。
- Canonical parameters 最多 64 KiB；每个字段同时有 item count、UTF-8 byte、UTF-16 code unit 和语义边界。
- 完整 rendered writer stdin 最多 256 KiB UTF-8，在有界内存中构造；超限在 claim 前作为输入错误。
- 参数不得直接或间接选择 executable、argv、environment、permission root、gate set、Git policy/ref、model/provider、sandbox、feature、Authorization 或 contract generation。
- Template compiler 只把参数编码为固定 schema 的 canonical data block，再嵌入 immutable versioned prompt template。Rendered prompt/stdin 永不持久化。

### 5.2 Submission identity

- BatchSubmission 恰好四个字段：<code>repo_id/template_id/parameters/expected_base_commit</code>。
- Repo/template ID 匹配 <code>[a-z0-9][a-z0-9._-]{0,62}</code>。
- 0.2 base commit 恰好为 40 位 lowercase SHA-1。
- Task/attempt ID 为 controller 生成的 lowercase UUID。
- Domain-separated canonical submission fingerprint 是永久 family key。
- 普通重复 <code>batch submit</code> 永久返回 generation 0 的 <code>root_task_id</code>，不能因后来 resubmission 改为 current task；<code>batch status</code> 才展示 mutable current task。

Submission admission 必须同时满足“新输入先扫描”和“既有 family 永久 replay”。固定顺序为：

~~~text
bounded byte parse
-> closed top-level schema, bounded parameter shape and public-ID syntax validation
-> canonicalization
-> compute volatile domain-separated lookup fingerprint in memory
-> read-only existing-family lookup
   -> if found: verify caller read permission and record integrity, return immutable root_task_id
-> only if absent: active catalog membership, current template parameter/path schema, secret scan and admission guards
-> BEGIN IMMEDIATE recheck lookup fingerprint and create-or-replay
~~~

- Bounded parser 在完整输入上同时执行总 bytes、nesting、item count、UTF-8、Unicode 和 duplicate-key 限制；不得先 canonicalize 或 hash 未验证输入。Replay 前只验证固定四字段 envelope、参数的通用有界 JSON shape，以及 repo/template/public path ID 的公开 grammar；current catalog membership 和 template-specific parameter schema 只用于 absent family 的新 admission。
- Volatile lookup fingerprint 是 canonical four-field submission 的 domain-separated SHA-256，只在当前进程内用于 indexed lookup。若没有既有 family 且后续 admission 失败，立即丢弃，不写 DB、日志、evidence 或 telemetry；不引入需要备份/轮换的 installation secret。只有首次成功 admission 创建 family 时，才把同一 fingerprint 作为 durable family key 保存。
- 命中既有 family 后，在任何 current SecretPolicyCatalog、active repo/template membership、qualification、Authorization、base 或 environment guard 前返回 generation 0 的 immutable root task；只复核调用者是否有权读取该 repo/family，以及 family/root/fingerprint 记录是否完整。Catalog 后来新增 secret pattern、template 退休、Authorization 过期或 successor 已创建，均不能改变 ordinary replay 的 root_task_id。
- 未命中时才按当前 active catalog 做 membership、template parameter/path schema、secret scan、qualification/base/Authorization admission。Unknown ID、malformed input 和 scan failure 使用稳定枚举 reason，但不得指出与秘密 catalog 的相似部分。
- Absent-family admission 失败不创建 SubmissionFamily/task、不保存 parameters、普通 hash、prefix、path digest、lookup fingerprint、candidate fingerprint 或可供离线枚举的稳定 oracle；只允许保存非输入派生的 request observation UUID、byte count bucket、reason code 和 rate-limit telemetry。
- 首次 admission 成功后进入 BEGIN IMMEDIATE，并必须再次按 lookup fingerprint 查询。并发创建或 response loss 已留下 family 时返回其原 root；否则原子写 family、root task 和 fingerprint unique row。任何 handler 都不得在 replay 命中后重新解释 raw parameters 或偷偷选择 current successor。

### 5.3 原子 resubmission

合法重新执行只有一个显式命令：

~~~text
batch resolve <source_task_id> --code create_resubmission_v1
~~~

它在一个 BEGIN IMMEDIATE 中完成：

1. 先按 source task 查询既有 TaskResubmission。若存在，只验证记录完整性和读取权限，然后在检查 source-current、base 或后来失效的 Authorization 之前返回同一 successor。
2. 不存在时，要求 source 是 family current、terminal state 为 failed 或 cancelled，且 immutable terminal snapshot 未变。
3. 证明 Job 已死、journal/evidence 已封存、无 executing fenced action、无 pending outbox 或未裁决 quarantine。
4. 证明 family 历史从未成功 create_task_ref；即使 ref 后来被外部删除也永久阻断。
5. 重验 current base、qualification、Authorization 剩余期限和 environment binding。Stale base 必须用新 expected_base_commit 重新四字段 submit，形成新 fingerprint。
6. 写 immutable TaskResolution、创建 generation+1 successor、写 TaskResubmission，并 CAS SubmissionFamily.current_task_id。

TaskResubmission 必填 <code>source_task_id/successor_task_id/resolution_record_id/root_task_id/resubmission_generation</code>，对前三者分别唯一，并唯一约束 root_task_id + resubmission_generation。TaskResolution 绑定 source terminal snapshot hash、stable <code>resolution_family=resubmission</code> 和 versioned code；唯一域只属于 resubmission，不阻断其他 resolution family。Completed、commit-ready、stale、non-current 或曾发布 ref 的 family 永不重提。不引入 ResubmissionPermit，也没有 batch resubmit 命令。

## 6. Base、qualification、外置环境与 Authorization

### 6.1 唯一 base ref

- RepoProfile 必须声明唯一完整 <code>local_base_ref</code>，只允许 <code>refs/heads/&lt;branch&gt;</code>，UTF-8 总长 11-255 bytes，且通过 pinned <code>git check-ref-format</code> 和 checked-in equivalent verifier。
- 禁止 HEAD、symbolic ref、remote/tag/notes/replace、<code>refs/heads/codex/batch/</code>、控制字符、backslash、空 component、<code>.</code>/<code>..</code> component、<code>@{</code>、尾点、重复 slash 和 lock-file collision。
- 0.2 不支持多个 allowed refs 或 historical detached base。
- Expected base 必须是存在、可剥离为 commit、恰好 40 位 lowercase SHA-1 的 direct ref target；不接受 tag peel 或 replace object。
- Prepare、submit、claim、writer spawn 和首次 common-store side effect 前均要求该 ref 精确指向 expected_base_commit。
- Ref 漂移进入 stale_base，不能静默重定向 task。

### 6.2 QualificationSensitiveInputSet

<code>QualificationObservation.v1</code> 绑定本次 observation 的 base commit/tree、working-tree audit、repo volume 8.3 policy observation outcome、每个可观测路径 component 的 long/short-name mapping、no-follow final identity 与 alias-bypass probe result；可复用的 <code>QualificationSensitiveInputSet.v1</code> hash 不包含整个 base commit/tree。

Canonical entry union 为：

- present：Git path、Windows collision key、object type、mode、blob/tree OID、rule ID、source 和 class；
- absent：candidate path、rule/source/class 和 absence result；absence proof 所依赖的 base 只在 QualificationObservation；
- expanded：directory/glob rule 及有序 child-entry hashes；
- blocked：path/reference class、rule/source/reason；任何 blocked entry 使 qualification 失败。

Set envelope 绑定 repo identity、local_base_ref 名称、resolver catalog ID/hash、Windows collision/alias-verifier policy generation、negative-discovery result 和完整有序 entry union；明确排除普通源码、observation base commit/tree、task ID 和 submission ID。QualificationObservation 中的 alias mapping、policy outcome、final identity 或 bypass-probe result 变化使旧 observation 失效并要求对应 scope requalification；<code>policy_query_denied</code> 只有在不提权 alias/identity probe 已证明等价路径不能扩大权限时才可通过。

Active <code>RepoTemplateQualification</code> 把安全语义 generation 与 observation 分离：新 expected base 上的 QualificationObservation 若重算得到相同 sensitive-set、environment、instruction/skill、policy 和 resolver hashes，只 CAS 更新 <code>last_observation_id/last_observed_base</code>，不递增 qualification generation；任一绑定 hash 改变才使旧 qualification/Authorization 失效并创建新 generation。Submit、claim 和 writer spawn 都要求存在针对各自 expected base 的 fresh successful observation。

因此：

- 普通源码变化只要重算 sensitive set byte-identical，就不使 qualification 或 Authorization 失效；
- sensitive file/OID、absence、expansion、AGENTS、skill、gate/build entry、lockfile、policy 或 external binding 变化立即失效；
- Controller discovery rule 可增加路径；RepoProfile/TaskTemplate 只能增加，不能排除 controller 发现项；
- unknown dynamic loading、递归闭包不完整、repo-external reference、collision 或 unsupported object type 均 fail closed。

Discovery 从 expected-base Git tree 取证。敏感候选或其祖先存在 dirty/staged/untracked 状态时阻断；working-tree hash 不能替代 Git-tree 证据。

Working-tree policy 固定为：sensitive/protected/discovery path、TaskTemplate approved read/write path 及其祖先上的 staged、modified、deleted、untracked 或 ignored entry 都阻断 qualification/prepare；这些集合之外的 unrelated dirty entry 可存在，因为 Batch 只从 expected commit materialize detached worktree，但只保存 aggregate class/count，不保存 path/hash，也不进入 Authorization fingerprint。Base ref、common-dir config、worktree admin 和 protected surface 仍在每个副作用 checkpoint 复核。

Qualification 资源上限固定为：最多 256 条 discovery rule、访问 200,000 个 Git-tree entry、10,000 个 sensitive union entry、128 个 path component、单 Git path 4,096 UTF-8 bytes、检查 256 MiB sensitive content。Streaming traversal 在 limit+1 立即停止；超大或歧义 repo/template 不得部分 fingerprint。

### 6.3 QualifiedEnvironmentBinding

<code>QualifiedEnvironmentBinding.v1</code> 不可变且内容寻址，绑定：

- repo/template qualification generation 和 lock hashes；
- bundle identity、volume/file identity、owner/DACL、reparse/hardlink audit；
- dependency/runtime writable volume 的 8.3 policy observation、existing component alias/final-identity audit、WriteAccountingPolicy mode，以及可选 HardWriteQuotaCapability binding；
- Python/Node/NuGet 等完整 dependency-tree manifest/hash；
- absolute read-only dependency roots/caches；
- 每次 gate run 的 fresh attempt-local writable cache/output mapping；
- 每个 gate 的 absolute executable/argv、cwd policy、允许 environment、timeout 和 report schema；
- detached worktree、offline sandbox 中的成功 qualification evidence。

Controller 和 gate 只验证和挂接 binding，不 install/restore/bootstrap，也不执行 package-manager setup。QualifiedEnvironmentBinding 在 attempt 期间不可变；缺失、retired 或漂移进入 needs_environment。Retire 只阻止新引用；0.2 不物理删除 immutable bundle。既有 attempt 只有在原 binding identity 完整且仍获 Authorization 时才可继续。

Writer 不获得 installer network、package-manager credential、共享可写 dependency cache 或修改 immutable binding 的权限。0.2 不声称能从任意 repo 脚本的语义识别所有“setup/install”行为；它机械阻断的是未授权 executable/network/path、超出写入预算的持久化副作用以及未经 GatePolicy 声明的输出。若 approved writer command 在允许 worktree 内生成普通源码，仍按 path、secret、budget 和 Git delta policy 审计，不能只因文件名类似 setup 就作语义判断。

### 6.4 可复用 Authorization

- Authorization 是 immutable、content-addressed、write-once 对象，默认有效 30 天。
- 唯一 active map 为 <code>(repo_id,template_id) -&gt; authorization_id,generation</code>，通过 CAS 更新；revoke 使用 append-only record 并递增 generation。
- Authorization 绑定 ActiveRuntimeIdentity、operator SID、repo/template/profile、允许 parameter schema/risk class、sensitive-set hash、instruction/skill inventory、qualification/environment/toolchain generation、model/effort、permission/config/feature/tool inventory、gates、Git policy、evidence mode 和资源上限。
- Authorization 不绑定单一 task、submission、普通 base commit 或 derived commit/ref/evidence ID。
- Task-specific ResolvedAttemptManifest 必须证明自己是该授权模板、风险和资源 envelope 的子集，并单独绑定 current expected base。
- Claim 时剩余有效期必须不少于 attempt deadline + 5 分钟。
- Submit admission、claim、writer spawn、每个新 gate、object plan/promotion、index/HEAD finalize、task-ref、normal evidence publish 和 worktree removal 前重验 generation、revoke 和 sensitive fingerprint。

每个可能启动进程或产生新外部副作用、且不属于下述 <code>safety_only</code> 闭集的 stage，在实际 effect 前还必须创建 immutable <code>AuthorizationExecutionGrant.v1</code>。Revoke 与基于 active Authorization 的 root grant 都遵守第 8.2 节的全局偏序且不得逆序：effect grant 已持有 BatchDrain，并取得 repo mutex、attempt mutex 后进入 BEGIN IMMEDIATE；revoke 不创建 attempt effect，可跳过 capacity/attempt 层，但必须取得同一 repo mutex 后进入 BEGIN IMMEDIATE。最终由 active-map/revoke head 所在的写事务决定线性化先后，而不是由 wall-clock 或预检查决定。事务只允许以下二选一：

1. revoke 插入 append-only AuthorizationRevocation、CAS active-map/revoke head，因而阻止尚未 grant 的 effect；
2. root grant 读取并绑定当前 Authorization ID/generation、active-map generation、revoke head hash/version、<code>basis_kind=active_authorization</code>、稳定 <code>effect_identity</code>、immutable effect/intent spec hash、input snapshot hash、initial fence 和 grant UTC；process-bearing effect 还绑定已 suspended 的完整 JobIdentity，deterministic controller action 则绑定 FencedActionIntent hash、initial FencedActionHead kind/hash/version 和 <code>adoptable=true</code>，然后插入唯一 grant。

同一 <code>attempt_id + effect_identity</code> 最多一个 Authorization grant；root grant 与 revoke 不得跨不同锁序竞态。Grant 已提交后，后续 revoke 不能授权新的 logical effect，但 controller 可且只能完成、安全终止或只读 reconcile 该 grant 已绑定的同一 effect。Process-bearing grant 永远绑定其创建时 fence、exact argv/Job/input/effect hash，不能跨 fence、resume 第二次或创建替代 process。可收养 deterministic controller action 不创建第二个 root grant；新 fence 只能通过第 10.2 节连续 FencedActionAdoption 继承同一 root grant、intent 和 logical effect identity。

若一个已 grant、可收养的 controller action 必须通过 Git 或受管 helper process 完成，则每个实际 StageJob 使用独立 child effect identity 和新的 process-bearing AuthorizationExecutionGrant，固定 <code>basis_kind=inherited_fenced_action</code>，并绑定 parent action grant ID/hash、current FencedActionHead kind/hash/fence/version、精确 StageLaunchRecord/argv/JobIdentity 和确定的 next-checkpoint/postcondition。该 child grant 不重新授权 logical effect；即使原 Authorization 后来 revoke，也只可在 postcondition verifier 已排除前一 process 仍在运行或结果未知、且当前 transition row 明确允许同一 action 的下一确定步骤时创建。Writer、GateRun、model decision、qualification、auth refresh 和 arbitrary command 永远不能使用 inherited basis。每条 child grant 仍只属于当前 fence 和单一 process，不得 adoption 或重放 ResumeThread。

<code>safety_only</code> effect 不得伪造 Authorization grant。它们只限于 exact existing JobIdentity 的 terminate/close、既有 pipe drain、journal seal、read-only reconcile、durable recovery handoff、exact EmergencyDiskReserve 的一次 release/rebuild，以及 GuardCatalog 明确列出的 host-preserving helper。实际副作用前必须写 immutable <code>SafetyOnlyExecutionRecord.v1</code>，绑定 safety reason/guard、effect identity、input/Job/reserve identity、current fence、允许副作用、OperatorAction/WorkSession（如需要）和 terminal postcondition；除精确绑定的 emergency-reserve file 外，它不能创建 writer、GateRun、Git publication、artifact/evidence publication、cleanup/delete 或任何扩大 repo/task 状态的 effect。需要 process 的 safety helper 仍遵守第 10.1 节 suspended StageJob、execution-commit 和 at-most-once 规则，其 StageLaunchRecord 引用 safety record 而非 Authorization grant。Fenced <code>terminate_job/release_emergency_reserve/rebuild_emergency_reserve</code> 可以跨 fence 收养同一 safety record；其他 safety record 不能被用作正常 action 的授权。

Authorization grant 与 SafetyOnlyExecutionRecord 构成封闭的 <code>execution_authority_kind</code> union。每个 StageLaunchRecord、FencedActionResult 和 terminal receipt/result 必须引用恰好一个适用 authority kind/ID/hash；fenced result 还必须引用写入时的 current head kind/hash/fence/version。除第 10.1 节明确允许的原子创建 suspended、Job-bound process 外，无 execution authority 的 process execution/ResumeThread、Git write、artifact/evidence publish 或 cleanup 都是未授权副作用硬失败。

Heartbeat 本身不创建外部 effect grant；Job termination、pipe drain、journal seal、read-only reconcile、local recovery evidence 和 durable recovery handoff 是上述 safety-only 闭集。即使 Authorization 过期或撤销也必须继续 heartbeat，按需先写 SafetyOnlyExecutionRecord，记录失效观察，并在安全 checkpoint 停止；不得让活进程因失租被错误 takeover。

Writer execution committed 后 Authorization 失效时：

- 先 durable 记录 observed Authorization ID/generation/revoke hash 和 safety termination intent，再终止当前 Job process tree，持续 drain，seal journal，只读 reconcile，并 park 为 recovery_pending；
- 不启动新 gate，不创建新的 commit/ref/evidence-removal 副作用；
- 获得新 Authorization 后写 AttemptAuthorizationContinuation，只续同一 frozen attempt，永不重跑 writer。

Admission 已要求自然 expiry 晚于完整 attempt deadline+5分钟，因此正常 attempt 不会跨自然到期。显式 revoke、active-map generation mismatch、clock rollback 或 expiry invariant 被破坏都执行上述固定终止路径，不允许 handler 自由选择“让 writer 跑完”。若进程在 termination intent 前已经自然退出，只能按原 PID/exit/EOF/receipt 事实收口，不能 resume 或创建替代进程。

Continuation 绑定 prior/new Authorization ID/generation、prior/new fence、非空 prior continuation head 或初始 attempt checkpoint hash、frozen manifest、writer marker/receipt、toolchain/environment hash 和精确允许阶段集合：

~~~text
gate_verify
object_plan
object_promote
finalize_index
finalize_head
create_task_ref
evidence_publish
worktree_remove
~~~

它不能扩大 path、parameter、gate、model 或 policy。

Continuation record immutable、append-only；插入与 <code>AttemptAuthorizationContinuationHead</code> 的 expected hash/fence/version CAS 位于同一 BEGIN IMMEDIATE。第一次 head 从 immutable attempt checkpoint 开始，禁止 SQL NULL 分支；同一 prior head 只有一个 successor。只有列出的未完成 controller stage 可被新 Authorization 接续，既有 terminal stage 不重开，writer stage 永不出现于 allowed set。

## 7. Codex 能力、auth、process environment 与 sandbox

### 7.1 Pinned 命令

Writer argv 是数组，不是 shell string：

~~~text
<pinned-codex> exec <writer-overlay-argv>
  --ephemeral --json --strict-config --ignore-rules
  -p batch -C <worktree> -m gpt-5.6-sol
  --output-schema <absolute-writer-final-schema> -
~~~

Gate/Git argv 为：

~~~text
<pinned-codex> sandbox -p batch
  -P <batch-gate|batch-git-audit|batch-git-local>
  --include-managed-config
  -C <logical-cwd> <overlay-argv>
  -- <absolute-executable> <argv-array>
~~~

Exec 不使用 -P；writer 通过 <code>default_permissions="batch-writer"</code>。禁止 legacy sandbox_mode、sandbox_workspace_write、--sandbox 和 -s。

<code>gpt-5.6-sol</code> 是初始 ExecutionProfile 中的 pinned model slug，不是由本文推断的公共别名；安装时 model probe、pinned 0.144.1 help/schema 和 Q0 必须共同证明其可用且映射到预期 provider/behavior。任何 unknown、renamed 或 inventory mismatch 都阻断 activation，不自动替换为相近 model。

### 7.2 Static config 与 effective allowlist

Managed batch profile 至少固定：

- <code>default_permissions="batch-writer"</code>；
- <code>model_reasoning_effort="high"</code>；
- <code>approval_policy="never"</code>；
- <code>windows.sandbox="elevated"</code>；
- <code>web_search="disabled"</code>；
- <code>history.persistence="none"</code>；
- <code>allow_login_shell=false</code>；
- <code>shell_environment_policy.inherit="none"</code>；
- <code>cli_auth_credentials_store="keyring"</code>；
- update check、analytics、feedback 和 telemetry exporter 关闭；
- 不显式设置会启用 plaintext TUI log 的 log_dir；managed config projection 中的普通 log root 不存在或只读，Q0 必须证明除已批准 <code>.sandbox/sandbox.log</code> 外无未知日志。

Overlay 无条件生成 <code>projects."&lt;canonical-worktree&gt;".trust_level="untrusted"</code>。Quick preflight/Q0 验证 project-local .codex config、hooks、rules 被跳过；--ignore-rules 只是 defense in depth。

<code>CodexFeaturePolicy.v1</code> 把 0.144.1 每个 feature 分类为 required_enabled、allowed_internal、required_disabled 或 removed_ignored，并绑定 model-visible tool inventory。Unknown effective=true、removed feature 复活或 inventory drift 均为 platform_incompatible。

MCP、apps/connectors、plugins、marketplaces、hooks、browser/computer-use、goals、memories、image generation、multi-agent、remote plugin、tool suggestions、workspace dependencies、shell snapshot、skill dependency installation 等非必要能力必须 disabled/absent。

### 7.3 CodexSandboxStateBinding

<code>CODEX_HOME</code> 是一个受管复合根，不能整体声明 immutable。<code>CodexSandboxStateBinding.v1</code> 必须把它拆为：

- immutable config projection：pinned config/profile/AGENTS/policy，只读且内容寻址；
- mutable <code>.sandbox</code>：Windows elevated sandbox helper 的受管状态与 <code>sandbox.log</code>；
- secret <code>.sandbox-secrets</code>：官方 sandbox broker 所需秘密状态，禁止 controller 通用读取和任何 evidence projection。

公开 Binding 绑定 Codex/toolchain generation、platform setup generation、专用低权限 sandbox SID/group、config 与 <code>.sandbox</code> root 的 final identity/owner/group/DACL/reparse/hardlink policy、允许 writer/gate/Git profile、<code>sandbox.log</code> 单文件 8 MiB/aggregate 32 MiB 上限、qualified rotation procedure/retention=4，以及 Q0 probe IDs。Setup/read-back 不匹配即 platform_incompatible；不得临时 chmod、继承用户 CODEX_HOME 或把 mutable sandbox bytes 纳入 immutable toolchain hash。

<code>.sandbox-secrets</code> 的内容、size、mtime、file identity、ACL digest 和任何派生 hash 永不进入 BaselineManifest、RuntimeToolchainManifest、公开 Binding、receipt、evidence、backup 或 diagnostic archive。Controller protected state只保存随机 local setup attestation ID 和枚举 read-back outcome；实际 ACL/identity 检查由不导出值的 pinned helper完成。Full Q0 必须以真实 sandbox child证明其无法读取当前用户 keyring/DPAPI material、controller auth handles 或 <code>.sandbox-secrets</code>；只有 pinned broker/helper能按官方协议使用。

官方没有承诺 <code>sandbox.log</code> 的字段 schema，因此它固定视为受保护的 opaque diagnostic：runtime 不解析字段、不保存内容或 content hash、不把它放入 evidence/backup，也不因其中出现 task path、parameter-like bytes、invalid UTF-8 或未知行就判 platform incompatible。日常状态只记录 byte count、枚举 rotation outcome 和与内容/路径无关的随机 attestation ID。Writer/gate/Git/task process 必须 deny-read；rotation 使用 Q0 资格化的 file-handle-safe procedure，失败或超限时停止新 claim并生成 OperatorAction，不得通过删除未审计日志继续运行。只有显式交互式 diagnostic export 可在受管临时区读取副本，且必须先做 secret scan、记录 OperatorWorkSession，并禁止导出未通过扫描的 bytes。

<code>.sandbox</code> 除日志外的允许 entry、type、producer、reader、最大 size 和跨 attempt retention 由 pinned-binary generation 的 opaque entry catalog 封闭声明；catalog 只记录安全元数据，不推断官方未公布的内部语义。Spawn 前后做目录 diff，unknown entry/type 进入 <code>sandbox_state_requalification_required</code> 并停止新 claim；只有 deny-read、root identity/ACL、size/retention 或 broker boundary 被绕过时才升级 platform_incompatible。Writer/gate/Git 不能直接读取该目录；只有 pinned helper 和 controller 的白名单 verifier 能访问。共享 mutable sandbox state 是 global capacity=1 下经 Q0 证明的特殊系统状态，不得扩展为共享 writable HOME/cache。

### 7.4 Permission profiles

- batch-writer：仅 template approved paths 和 attempt cache/temp 可写；qualified source/dependency/instruction 可读；Git admin/common、policy、skill、protected surface 和 secret pattern 拒绝。
- batch-gate：source/Git 只读；仅 fresh gate-run output/cache 可写。
- batch-git-audit：original repo 和 Git metadata 只读。
- batch-git-local：仅 attempt index/object、runtime worktree admin/index/HEAD、common object promotion target 和 exact task-ref lock/ref 可写；禁止其他 ref/reflog。
- 四类 task-side network 全部关闭。

### 7.5 Instructions、skills 与 prompt evidence

- <code>project_doc_fallback_filenames=[]</code>。
- Managed global AGENTS 最多 8,192 bytes；完整 project AGENTS chain 最多 32,768 bytes。Unknown file 或 truncation 阻断。
- InstructionSnapshot 绑定 global presence/hash、完整 project chain 的 order/path/OID/byte count、truncation 和 controller prompt-template/data-block hashes。
- SkillInventory 覆盖 system/admin/user/repo scope 和 final target。Managed HOME 消除真实用户 skill；除精确授权且 Q0 证明生效的 repo skill 外，全部显式 disabled。
- Read-only skill symlink 只在 final target 位于 approved immutable root 且 identity/OID/hash 匹配时允许；任何 writable root 或祖先不允许 reparse point。
- 0.2 不声明 final_prompt_input_sha256。只保存 controller prompt template/data hash、ordered instruction inventory hash、skill inventory hash、effective-config hash 和 feature/tool inventory hash。debug prompt-input 仅作可选 Q0 诊断。

### 7.6 Empty environment 与路径复核

Writer、gate、Git、probe、recovery helper 从空 environment 构造。公共 allowlist 恰好为：

~~~text
CODEX_HOME CODEX_SQLITE_HOME HOME USERPROFILE APPDATA LOCALAPPDATA
XDG_CONFIG_HOME TEMP TMP SYSTEMROOT WINDIR COMSPEC PATHEXT PATH
~~~

<code>ProcessEnvironmentPolicy.v1</code> 还必须固定 Windows environment block 的字节级构造：key 使用 ASCII catalog spelling并在 <code>OrdinalIgnoreCase</code> map 中唯一；任意大小写 alias、重复 key、空 key、含 <code>=</code>/NUL 的 key或含NUL的value均拒绝。Windows drive-current-directory pseudo variables（例如 <code>=C:</code>）以及其他以 <code>=</code> 开头的hidden entry一律不生成、不继承。序列化只使用catalog中的canonical key spelling，按Windows case-insensitive ordinal comparator排序为 <code>key=value\0</code>，最后恰好再写一个NUL；总UTF-16 code units、单value长度和CreateProcess总命令行/environment边界均由ResourceLimitPolicy给出 <code>limit-1/limit/limit+1</code> fixture。任何 inherited block、case-fold collision、parser与实际child观测不一致都在ResumeThread前阻断。

- CODEX_HOME 指向 CodexSandboxStateBinding 管理的复合根；config projection只读，<code>.sandbox</code>/<code>.sandbox-secrets</code> 仅按 binding ACL 和进程身份可见，不能映射到 attempt HOME。
- HOME/USERPROFILE/APPDATA/LOCALAPPDATA/XDG/CODEX_SQLITE/TEMP/TMP/cache/spool 全部 attempt-local。
- PATH 只含 ordered ToolchainManifest 和 QualifiedEnvironmentBinding dirs。
- 清除 proxy、credential/API-key、PYTHON*、NODE*、shell-profile 和 inherited GIT_*。
- VIRTUAL_ENV、NODE_PATH、NUGET_PACKAGES 等只可由 gate binding 显式加入。
- Git-specific vars 仅由 Git adapter 在单次 operation 注入。
- Receipt 只保存无秘密的 environment policy projection/hash，不保存 auth、token、proxy credential 或其 hash。

Codex parent 只可获得 Q0 批准的 provider control-plane connectivity 和必要的非秘密 proxy endpoint；sandboxed tools/gates/Git 不获得 auth/proxy vars，也无 network。

Codex/Git CreateProcess 的 lpCurrentDirectory 指向 attempt empty；逻辑 repo 通过 -C 选择。Gate 只有在 sandbox 和 binding 中才可使用 worktree logical cwd。Absolute executable、安全 DLL search、binary identity before/after 和 side-loading canary 为硬门。

每次实际 writer/gate/Git/probe/recovery-helper spawn 前后，controller 重新 handle-open 所有 writable roots 及祖先，复核 final path、volume/file identity、owner/DACL、reparse 和 file hardlink count。Post-run 漂移必须终止或 quarantine 结果，不能进入下一阶段。

### 7.7 Overlay evidence、auth 与限额

- PermissionOverlayCompiler 最多输出 64 个 -c、合计 16,384 UTF-16 code units；完整 CreateProcess command line 小于 32,767。
- 必须通过 TOML、Windows path、quoting 和 CreateProcess round-trip fixtures。
- Raw argv/env 不落盘；ResolvedAttemptManifest/ExecutionReceipt 绑定 compiler input hash、compiler version/binary hash、logical-root 替换后的 safe projection、ordered overlay digest、effective-config hash、inventory ID 和 qualification probe ID。
- 0.2 keyring-only；不可用即 Q0 失败，无 file/auto fallback。
- AuthState 只保存 provider、auth generation、store=keyring、status 和 qualified time，不保存 credential/hash/mtime 或 keyring content。
- needs_auth 全局停止新 provider claim，并按 <code>(platform_login_required,auth_generation)</code> 去重 OperatorAction。Scheduled runtime 禁止 login/logout。
- Interactive login 必须改变 auth generation 并通过 quick qualification 才关闭旧 action、恢复 claim。
- Rate limit/service transient 优先 Retry-After，否则 5m -> 15m -> 1h -> 6h；auth 失败不进入该循环。

## 8. Ownership、named objects、legacy、Native maintenance 与 cutover

### 8.1 Ownership registry

<code>ownership/&lt;repo_id&gt;.json</code> 绑定 repo ID、canonical Git common-dir final path、volume/file identity、owner SID、status、ownership generation、registry generation、schema 和 checksum。

- 首次 CREATE_NEW/no-replace。
- 更新要求 expected generation/checksum、durable temp、flush、atomic replacement 和 backup。
- Primary 损坏时只可使用 identity 一致且 generation 不倒退的 backup；否则交互式 ownership-repair。
- Repair 要求真实 interactive OperatorWorkSession、global offline lock、零 active/closing/recovery、verified backup 和明确 rollback。

### 8.2 Named objects、SDDL 与 lease

- SID canonical form 来自 ConvertSidToStringSidW。
- SIDHash 为 ASCII SID 的完整 lowercase SHA-256。
- Canonical repo identity 只从以 no-follow ancestor audit 后打开的 Git common-dir directory handle 取得，payload 恰好为 canonical volume GUID path、16 位 lowercase volume serial hex 和 32 位 lowercase <code>FILE_ID_128</code> hex。Final common-dir path 作为 ownership observation 单独绑定，不进入 identity hash，因此同卷 rename 不创建第二 owner。
- Volume GUID 必须匹配 <code>\\?\Volume{8-4-4-4-12 lowercase hex}</code> 的唯一拼写且无末尾反斜杠；serial/file ID 固定宽度、zero-padded。无法取得任一字段、路径祖先含 reparse、identity 为全零或两个 repo_id 映射同 identity 均阻断 registration。
- RepoIdentityHash 为 <code>local-ai-runtime/repo-identity/v1</code> canonical envelope 的完整 lowercase SHA-256。Legacy/new adapter 必须使用同一 checked-in test vectors，禁止用 path string、repo_id 或 Git remote 代替。
- 名称固定为：

~~~text
Global\LocalAIRuntime.BatchDrain.<SIDHash>.v1
Global\LocalAIRuntime.OwnershipRegistry.<SIDHash>.v1
Global\LocalAIRuntime.RepoOwnership.<SIDHash>.<RepoIdentityHash>.v1
Global\LocalAIRuntime.Attempt.<SIDHash>.<attempt_uuid>.v1
Global\LocalAIRuntime.Job.<SIDHash>.<attempt_uuid>.v1
Global\LocalAIRuntime.StageJob.<SIDHash>.<attempt_uuid>.<run_uuid>.v1
~~~

Attempt-level <code>Job</code> 名称只属于 writer execution；每个 gate、Git、probe 和 recovery-helper run 使用先 durable 分配的 run UUID 与 <code>StageJob</code> 名称。名称分配、process kind 和 run UUID 都进入 JobIdentity，禁止随机改名绕过既有对象。

- Expanded SDDL 为 <code>O:&lt;CURRENT_SID&gt;G:SYD:P(A;;GA;;;SY)(A;;GA;;;CURRENT_SID)</code>。复用前验证 object type、owner、group、canonical DACL、name 和 Job limits；不匹配为 platform_incompatible。
- Lock order：BatchDrain -> OwnershipRegistry -> 按 canonical repo identity 排序的 repo mutex/ownership generation -> attempt mutex -> SQLite BEGIN IMMEDIATE。单仓 operation 可跳过未涉及层，但不得逆序；多仓 backup/cutover 必须先取得 registry 再依序取得全部 repo mutex。BatchDrain mutex 是 global capacity=1 的唯一 named-object 实现。
- Global Batch writer capacity 固定为 1；heartbeat 15 秒，TTL 90 秒。
- Takeover 同时要求旧 attempt/controller mutex released、PID+creation time dead、TTL expired、Job state explainable、fencing-token CAS success，并优先恢复旧 attempt。
- Boot identity 改变、monotonic discontinuity 或 wall-clock rollback 使 lease freshness 无效并进入 recovery proof，不能授权盲接管。
- Capacity 持有到 terminal closeout，或 durable recovery handoff 证明 Job 零进程、journal seal/continuation、无 executing action、SQLite state committed。

### 8.3 Same-name Job

在同一 attempt mutex 内：

1. OpenJobObject，验证 type/security/limits/process list。
2. 关闭本次 probe handle。
3. 只有看似不存在时才 CreateJobObject。
4. 若返回 ERROR_ALREADY_EXISTS，关闭返回 handle，park 为 recovery_pending/job_handle_still_open。

零进程同名 Job 也不能复用、换名绕过或强制“删除”。Interactive repair 只能通过 executable hash、PID、creation time 证明 runtime-owned 后显式终止 holder；否则等待其退出或重启宿主，然后重新证明对象消失。

### 8.4 Legacy guard 与 cutover

- 新 Batch claim 前，legacy 所有写入口必须使用同一 repo identity、mutex、ownership generation 和 guard。
- 覆盖 claim、lease、worktree、executor/writer、repo mutation、Git、commit、closeout、evidence、cleanup。
- 先把现有 repo 注册为 legacy owner；未 cutover legacy DB 继续在 guard 后可写。
- Repo cutover 是 guarded_legacy -> batch 的 generation CAS，要求零 active/closing 和 conformance/crash/rollback drill 全绿。
- Rollback 通过 CAS 回 guarded_legacy，永不 dual-write。
- 全部目标 repo cutover、零 legacy active/closing、rollback drill 通过后，旧 DB 才只读。
- 连续 30 天零 legacy call 后可删除旧写代码；compat reader、历史 evidence 和 task refs 永久只读保留。

### 8.5 Managed Native

对 Batch-owned 或 guarded-legacy repo，write-capable Native 固定流程：

~~~text
durable maintenance_drain_requested
-> stop new Batch claims
-> wait current attempt naturally terminal
-> acquire global capacity + repo mutex
-> maintenance begin
-> native run --mode direct|program
-> maintenance-end sensitive scan
-> quick verify or repo/template requalification
-> release locks
-> resume unaffected scheduling
~~~

- <code>native run --mode spec</code> 是 read-only，不需要 write maintenance。
- Normal maintenance 不 kill 当前 attempt，也不按 TTL 自动解除。
- RepoMaintenanceRecord 在 begin 时保存 prior ownership/lifecycle/qualification generations 和 sensitive observation。End scan 若 sensitive-set、protected surface、environment/toolchain policy 均未漂移，则恢复保存的 prior owner/lifecycle、完成 quick verify 并 terminal maintenance；不能默认切成 batch owner。
- Sensitive drift 必须撤销该 repo/template 的 qualification 与 active Authorization，目标 repo 进入 repo_requalification_required；scan 不完整、identity 改变或结果歧义时保持 maintenance=repair_required，并生成去重 OperatorAction，禁止 platform resume 把它清除。
- <code>platform kill-current</code> 是独立 emergency command；必须先 durable 写 OperatorWorkSession、OperatorAction、FencedActionIntent(terminate_job) 和匹配的 SafetyOnlyExecutionRecord，再关闭 Job、持续 drain、seal journal、handoff recovery。
- Repo qualification 失败只阻断该 repo；template 失败只 suspend 该 template；global resume 只清 control lane，不能覆盖 repo/template blocker。
- Plain Codex/Git 在未注册 repo 外仍是合法人工工具，但不享受 runtime guarantees。对已注册 repo 未经 managed maintenance 的写操作 unsupported，并强制 requalification；不安装 global hook。
- TaskSpec、NativeSessionPolicy、OperatorWorkSession 绑定 mode、repo scope、write/read-only、integration responsibility、start/end、SID/generation 和 enum reason。Runtime 不接收或持久化 Native prompt/reasoning/transcript；独立 Native Codex surface 遵循自己的显式 persistence config，不计入 Batch evidence。

## 9. 状态、guard 与自治

### 9.1 Mechanical policy package

每张 machine-readable transition table 的每行必须包含：

~~~text
source_state
operation_or_event
guard_ids
allowed_effects
target_state
exit_code
capacity_disposition
scheduler_priority
retry_policy
~~~

Unknown CLI state/operation/resolution 退出 2 且零副作用。Codex runtime stream 违反 qualified adapter schema 属于不同边界：关闭 Job，进入 platform_incompatible，退出 6。

GuardCatalog 为每个 guard 固定 scope、immutable input snapshot、precedence、reason code 和 cross-policy dependency，并由 verifier 证明 DAG 无环。优先级为：

~~~text
baseline approval
implementation acceptance
P2 Q0
platform incompatible
manual drain/suspend
needs_auth
platform unavailable/qualification suspended
disk_pressure
repo ownership/maintenance/requalification
template qualification/authorization
task base/environment/limits
due recovery
writer capacity
~~~

Heartbeat、terminate、drain、seal、read-only reconcile 和 recovery handoff 使用显式 safety_only guard，不构成 Authorization 通用旁路。

### 9.2 SubmissionFamilyStatePolicy

| Source | Operation/Event | Guarded result |
|---|---|---|
| absent | new submit | 创建 open family 和 generation-0 root |
| any | ordinary replay | 状态不变，返回 root task |
| open | current failed/cancelled 且 eligible | awaiting_resolution |
| open | task ref 成功但 closeout 未完 | publication_recovery |
| publication_recovery | evidence/cleanup terminal | commit_ready |
| awaiting_resolution | atomic create_resubmission | CAS 新 current，回 open |
| awaiting_resolution | stale/ref-history/explicit close | closed |
| commit_ready/closed | reopen/resubmit | 拒绝 |

### 9.3 BatchTaskStatePolicy

主路径为 <code>submitted -> queued -> active -> closing -> completed</code>。

- Preclaim external guard 阻断时进入 parked，不创建 writer attempt；guard 恢复后回 queued。
- Active attempt 只有通过 RetryEligibility 才能创建 fresh attempt 并回 queued，否则 task failed。
- Pre-spawn cancel 直接 cancelled。
- Running/verifying cancel 先 durable 记录 intent；有 live process Job 时安全终止并 drain/seal。若 deterministic controller action 正执行，只能等待或只读 reconcile 同一个 action，禁止启动冲突 action。
- Closing cancel 只记录 enum cancel_reason_code 并返回 accepted_deferred。先等待或 reconcile 当前 fenced action；若 task-ref 从未成功且到达无 executing action 的安全 checkpoint，可停止后续 publication、完成 cleanup 并 terminal cancelled；若 task-ref 已成功或结果证明成功，必须完成 evidence/cleanup 的 publication recovery 并 terminal completed/commit-ready，不能伪装已取消或删除 ref。
- Source task 在 successor 创建后仍保持 immutable terminal。

### 9.4 AttemptStatePolicy 与 launch substate

主路径：

~~~text
created -> claimed -> preparing -> writer_launching -> writer_running
-> verifying -> closing -> succeeded
~~~

恢复状态为 <code>recovery_pending/recovery_required/reconcile_required/cleanup_required/failed/cancelled</code>。

Writer launch substate 恰好为：

~~~text
launch_intent
-> durable_marker
-> spawned_suspended
   -> terminated_before_execution_commit
   -> writer_execution_committed
      -> resume_observed | resume_outcome_unknown
      -> process_exited
~~~

- 只有 launch_intent 或 durable_marker 且 Job/PID 均不存在时，可继续同一 launch intent。
- spawned_suspended -> terminated_before_execution_commit 要求原线程仍 suspended、Job 已终止、PID 已退出、terminal record 已 durable；之后只能创建新 attempt，不能复用旧 attempt。
- <code>writer_effect_id = stable(task_generation,resolved_writer_intent)</code>；<code>writer_launch_id = unique(writer_effect_id,attempt_id)</code>。WriterEffect identity 跨 pre-commit attempt 稳定，WriterLaunch identity 只属于一个 attempt；二者不得共用唯一键。
- writer_execution_committed 必须在 ResumeThread 前 flush，并由 <code>UNIQUE(task_generation) WHERE writer_execution_committed=1</code> 与每个 attempt 唯一 process identity 机械保证。一旦存在，该 task generation 永久禁止启动第二个 writer，即使零 tool、零 mutation 或 resume outcome unknown。
- <code>resume_outcome_unknown</code> 只表示 ResumeThread 调用结果的观察不确定，不表示可以放弃或替换原进程。Controller 必须继续跟踪 exact PID/creation time/Job、drain 到 EOF、按 deadline 安全终止并 seal；六项 receipt 条件全部成立时仍可继续 gates/Git closeout。若最终事实无法证明，写稳定 <code>writer_result_unresolved</code>，不得生成 ExecutionReceipt、commit 或 task ref，只能通过显式 resubmission 创建新 task generation。
- Startup 和每次 claim 必须扫描 orphan marker/DB/PID；只可 CAS 收录可证明的 pre-process marker，歧义状态 park。
- Recovery 只有在 Job 零进程、journal sealed/durable continuation、无 executing action、SQLite handoff committed 后才释放 capacity。
- Due recovery 优先于新 task。

同 task generation 自动 retry 还必须同时满足：无 writer_execution_committed、先前 suspended process 已被证明终止、零 tool/mutation/GitAction、worktree/index/tree 等于 base、attempt_no 小于 3。Fresh attempt 可以复用稳定 writer_effect_id，但必须创建新的 writer_launch_id；其他情况只能 terminal failure 或显式 successor。

V1 resolution code 只有：

~~~text
continue_verify_v1
continue_closeout_v1
retry_cleanup_v1
terminate_failed_v1
create_resubmission_v1
~~~

Resolve 永不启动 writer。Reconcile 严格只读，不能创建 stale-base successor、object、commit、ref、artifact 或 evidence publish。

### 9.5 Platform、repo、template lanes

Platform 使用独立 lanes，避免状态笛卡尔积：

- auth：unknown | ready | needs_auth；
- control：running | drain_requested | suspended；
- qualification：unqualified | qualified | suspended | incompatible；
- availability：available | unavailable。
- resource：normal | disk_pressure。

Canary infrastructure failure 独立重试一次，仍失败则 qualification suspended 并停止 claim。Binary/config/profile/permission/sandbox/adapter behavior drift 直接 incompatible。单 task resource limit 不升级为全局 incompatible。

Stop-the-line 按 scope 分流：repo/template policy 或 gate failure 只 suspend 对应 qualification/Authorization；只有 CLI、permission、Windows sandbox、feature/tool inventory、auth adapter 或 CapabilityAdapter 行为可疑时才全局 suspend/incompatible。

Repo lanes：

- ownership：legacy -> guarded_legacy -> batch -> retired；batch 可在 guard 下 rollback；
- maintenance：idle -> drain_requested -> active -> idle | repair_required；
- qualification：qualified | repo_requalification_required。

Template lifecycle：

~~~text
draft -> qualifying -> awaiting_authorization -> pilot -> canary -> promoted
~~~

任一运行态可因安全、gate、新 failure type 或人工介入进入 suspended；只能重新 qualification/Authorization/canary，或 retired。运行中无动态 fallback。

### 9.6 AutonomyPolicy

- B0：仅 contracts、doctor、qualification、prepare。
- B1：操作者显式启动一个 pilot Batch；deterministic closeout 自动。
- B2：scheduler 对 promoted template 每次 drain 一个 task。
- B3：跨多个 qualified repo 的 portfolio scheduling，global capacity 仍为 1。

升级只激活 static generation 和 Authorization，永不扩大 Batch 禁止边界。

Portfolio selection 留在同一 Python/SQLite control plane，由 AutonomyPolicy 与 SchedulerPolicy 的版本化 rows 机械执行。每个 repo 只可提供 qualification-bound、content-addressed、closed-schema 的 backlog snapshot：公开 work ID、TaskFamily/Template ID、dependency IDs、ready predicates、priority class、expected base 和 expiry；0.2 不执行 repo 自带 selector code、脚本、表达式或 prompt。Controller 只从当前 ActiveRuntimeIdentity 下已 qualification、已 Authorization、依赖满足且 guard 允许的 ready set 按稳定排序选择；不得自行扩展项目目标、风险、permission、effect envelope 或交付目的地。Native Spec 可产出 TaskSpec/模板候选，但首次 TaskFamily/Template promotion 始终需要受控 operator action。

P4 cohort 在 B2/per-repo scheduling 下运行。只有 P4 全绿后，独立的 <code>activate_b3_portfolio_generation</code> governance action 才可 CAS 激活 B3；P5 repo cutover 可从 P4 独立继续，不依赖 B3。B3 激活失败或未执行不否定已通过的 per-repo cohort，也不能阻塞独立 P5 cutover。

## 10. Process、Job、marker、fencing 与 gate recovery

### 10.1 JobIdentity、writer 与 StageJob 原子 launch

JobIdentity 绑定 Job name、process kind、optional run UUID、security/limit hashes、controller PID/creation time、process PID/creation time、executable identity、attempt、task generation、fence 和 boot identity。

- Writer root grant 的 logical identity 使用稳定 writer_effect_id；具体 suspended process、JobIdentity、marker、argv digest 和 execution barrier 使用 attempt-scoped writer_launch_id。Pre-commit fresh attempt 不能创建第二个 logical effect，但可创建新的 launch；execution commit 后 effect 与 launch 均冻结，禁止新 writer process。
- Writer 使用 CREATE_SUSPENDED + PROC_THREAD_ATTRIBUTE_JOB_LIST，原子加入预建 kill-on-close/no-breakaway Job。
- 持久化 PID 和 creation time 后才进入 spawned_suspended。
- Marker 固定为 <code>&lt;attempt&gt;/writer-start.v1</code>，绑定 task generation、attempt、fence、launch-intent hash 和 checksum。
- Marker 使用 CREATE_NEW | FILE_FLAG_WRITE_THROUGH，FlushFileBuffers 后 close。
- DB protocol 为 start-intent -> durable marker -> DB marker terminal；claim 在任何新 writer 决策前扫描 orphan marker。
- writer_execution_committed 是 ResumeThread 前的 durable irreversible barrier。
- Writer 与 StageJob 的 process launch期间必须连续持有第 8.2 节相关 OS mutex：在锁内重验适用 execution-authority 前置条件（writer/正常 GateRun 的 active Authorization、controller child 的 parent action grant + current head、或 safety helper 的 safety guard/record），创建已原子入 Job 的 suspended process，取得完整 PID/creation time JobIdentity，再在同一锁序的 BEGIN IMMEDIATE 中写适用 authority record/link 和 execution-commit barrier；提交并 flush 前禁止 ResumeThread。不得跨 CreateProcess 持有开放 SQLite transaction。若在 authority commit 前崩溃，recovery 只能终止仍 suspended 的 Job并记录未执行，不得 resume或事后补授 authority。

Writer 进入固定 attempt-level Job；每个 gate、每个 Git sandbox command、probe 和 process-bearing recovery helper 进入自己的 durable StageJob。两类均为 kill-on-close/no-breakaway，并按规定 deadline 终止完整进程树；StageJob 不得承载 writer。

所有 StageJob 与 writer 使用相同的不可逆 spawn 原则：

1. 在 attempt mutex 和 current fence 下先创建并核验 fresh named Job，writer 写 immutable <code>WriterLaunchRecord.v1</code> launch intent，其他 process-bearing run 写 <code>StageLaunchRecord.v1</code> launch intent；各自 effect identity 唯一。
2. 用 <code>STARTUPINFOEXW + EXTENDED_STARTUPINFO_PRESENT + CREATE_SUSPENDED</code>，同时设置 <code>PROC_THREAD_ATTRIBUTE_JOB_LIST</code> 与 <code>PROC_THREAD_ATTRIBUTE_HANDLE_LIST</code>；在 CreateProcess 时原子加入该预建 Job并把继承集封闭到精确stdio child ends。禁止先启动后 AssignProcessToJobObject，也禁止 breakaway或依赖ambient inheritable handle。
3. 在任何 ResumeThread 前持久化并 flush process PID、creation time、executable identity、argv safe digest、JobIdentity、恰好一个 execution authority kind/ID/hash，以及相应 <code>writer_execution_committed|stage_execution_committed</code> barrier；writer和正常 GateRun必须使用 active-authorization grant，controller-action child process按本节只能使用 inherited-fenced-action grant，明确的 safety helper只能使用 SafetyOnlyExecutionRecord。
4. ResumeThread 后只记录 <code>resume_observed|resume_outcome_unknown</code>，持续跟踪原 PID/Job、drain 到 EOF，并以 terminal report/result 收口；unknown 不能重启 writer 或同一 stage，只能按 effect-specific policy收口原进程、只读 reconcile，或对明确 rerunnable 的 gate 在前一进程 terminal proof 后创建 fresh GateRun。

<code>ProcessHandlePolicy.v1</code> 对每次spawn固定如下不变量：<code>bInheritHandles=TRUE</code> 只允许与非空 <code>PROC_THREAD_ATTRIBUTE_HANDLE_LIST</code> 同时使用；列表恰好包含本process需要的stdin read、stdout write、stderr write child handles，或catalog声明的NUL替代handle，且三种role不得重复或方向颠倒。Child end在创建前显式标记inheritable；controller end、Job、mutex、process/thread、SQLite/file、keyring/auth、policy、evidence、backup、quarantine和directory handles全部创建为non-inheritable并不得出现在列表。CreateProcess返回后controller在同一临界区立即关闭自身持有的child ends，再启动reader/feeder；任何多余handle、handle type/access-mask不符、EOF owner不唯一或父端未按时关闭都在ResumeThread前终止suspended Job。

每次spawn写 immutable <code>ChildHandleManifest.v1</code>，绑定process/stage identity、三个stdio role、Windows object type、pipe direction、granted access、inheritability read-back、parent/child ownership、attribute-list digest和expected EOF condition；不保存raw handle数值、pipe内容或其hash。Q0与crash verifier必须证明child无法枚举/使用未列的Job、mutex、DB、auth、evidence或controller file handle，并证明正常exit、kill、controller crash和response-loss下stdout/stderr都能到EOF，未知继承者不能让pipe永久不闭合。

<code>StageLaunchRecord</code> 至少包含 stage_run_id、action/effect identity、attempt/initial fence、JobIdentity hash、execution_authority_kind/ID/hash、optional parent action grant/head、launch-intent hash、PID/creation time、execution-commit hash、resume observation、terminal result ID 和 prior-record hash。任何新 process-bearing run 前，都必须证明前一 JobIdentity terminal、Job 零进程、named object 已消失或处于可解释的 same-name park、pipes 已 EOF、record 已 terminal；仅 TTL 到期或零进程不构成许可。Process stage 不进入 adoption graph；controller takeover 只能终止或只读收口原进程事实。

同一 StageLaunchRecord 一旦写入 stage_execution_committed 就不得启动第二个 process。GatePolicy 允许 rerun 时必须创建新的 gate-run UUID、effect identity、StageJob、grant 和 isolated roots；Git/action recovery优先收养或 reconcile同一 fenced action，不能通过新 StageJob重做未知副作用。At-most-once verifier同时检查每个 stage_run_id 最多一个 execution commit 和 process identity。

### 10.2 Fenced controller actions

四类记录固定为：

- FencedActionIntent：immutable desired effect、input snapshot、fence、effect/postcondition spec hash，以及可选 fully predictable terminal fingerprint；
- FencedActionAdoption：immutable append-only takeover link；
- FencedActionHead：mutable CAS pointer，保存 head kind/hash/fence/version；
- FencedActionResult：immutable terminal observation/result/verifier evidence。

初始 head 指向 intent hash，不使用 SQL NULL。插入 adoption 与 CAS 更新 head 必须在同一 BEGIN IMMEDIATE；<code>UNIQUE(action_id,prior_head_hash)</code> 防分叉。Result 每 action 唯一；terminal 后禁止继续 adoption。

FencedActionAdoption 必填 <code>action_id/prior_head_kind/prior_head_hash/prior_fence/new_fence/takeover_proof_hash/effect_spec_hash/postcondition_verifier_id/created_at_utc/adoption_hash</code>；<code>prior_head_hash</code> 非空，第一次指向 intent，之后指向前一 adoption。事务同时要求 FencedActionHead 的 kind/hash/fence/version 与 prior 值完全一致，再 CAS 到新 adoption/new fence/version+1。FencedActionResult 写入前再次 CAS 验证当前 head、fence、effect spec 和 verifier generation。

每个可收养 action 在首次 effect 前必须已有唯一 root execution authority。除 <code>terminate_job/release_emergency_reserve/rebuild_emergency_reserve</code> 外，它必须是 AuthorizationExecutionGrant，绑定稳定 logical effect identity、FencedActionIntent hash、effect spec、Authorization/revoke snapshot 和 initial fence；三个 safety action 必须使用分别绑定 exact JobIdentity 或 EmergencyDiskReserve identity/generation、safety guard/reason 和同一 intent 的 SafetyOnlyExecutionRecord，不能要求 active Authorization。Adoption transaction 必须验证 authority 与 intent/effect 完全一致，并把 <code>inherited_authority_kind/id/hash</code> 写入 adoption；它只移动 mutable head，不修改 authority、intent 或 Authorization snapshot。FencedActionResult 同时引用 inherited authority 和当时 current head。若 authority 缺失、intent/effect 不同、head分叉或 action kind 不在 allowlist，takeover只能只读 reconcile/park，不能补授正常授权或创建新 effect。

FencedActionIntent 以 action_id 为主键，并在 <code>attempt_id + action_kind + logical_effect_identity</code> 上唯一；旧 intent 永不修改。发现 nonterminal intent、未知 OS result 或响应丢失时，只能 adoption/read-only reconcile 同一 effect，禁止创建冲突 intent。<code>terminate_job</code> intent/adoption 必须绑定完整 JobIdentity hash；任何 PID/name-only 终止都不具可收养性。

OS result 不一定预先可知，所以 effect_spec_hash 必填，expected_terminal_fingerprint 仅在 byte-deterministic 时可选使用。只有 versioned postcondition verifier 能唯一归因或完成同一 effect 时才允许 adoption。

可收养 action 严格限定为：

~~~text
create_worktree
checkout_base
materialize_object_set
artifact_publish
promote_objects
finalize_worktree_index
finalize_worktree_head
create_task_ref
remove_worktree
terminate_job
release_emergency_reserve
rebuild_emergency_reserve
~~~

Writer/spawn、auth refresh、qualification、arbitrary command 和 model/gate decision 永不可收养。

### 10.3 GateRun

- 每个 gate run 有 durable start intent、unique gate-run UUID、fresh output/temp/cache roots、source snapshot hash、process JobIdentity 和 terminal GateReport。
- Gate 不得修改 source/Git。Ambiguous run 的可写 cache/output quarantine，永不复用。
- 只有 GatePolicy 声明 rerunnable=true、source/frozen manifest 未变、使用新 isolated gate root 且 cumulative limit 未超时，才可新跑一次。
- 这是新的 gate run，不是 adoption；否则进入人工 recovery。

## 11. Event、journal、artifact、evidence 与 backup

### 11.1 Output handling

- 独立 async reader 持续有界排空 stdout/stderr，防 pipe deadlock。
- 到 limit+1 立即终止对应 Job，不能截断后判成功。
- Raw JSONL/stdout/stderr、agent text、reasoning、command、argv、environment、tool I/O、config dump 及其 content hash 不进入普通 state/artifact/evidence。
- 上述 raw process material 无 quarantine 例外；invalid/partial framing buffer 只在 bounded memory 中用于分类和计数，随后丢弃正文。
- 普通持久化只含 byte count、exit/reason code 和白名单结构化报告。
- Output overflow 默认只失败 attempt；只有独立证据证明 adapter/platform drift 才 suspend platform。

### 11.2 NormalizedExecutionEvent

公共 required fields：

~~~text
schema_version
attempt_uuid
positive fence
positive seq
observed_at_utc = YYYY-MM-DDTHH:MM:SS.ffffffZ
event_type
status
prev_hash
event_hash
~~~

Optional field 不得为 null，只能按 per-event matrix 出现。V1 exhaustive event/status pairs：

- process_started | tool_started -> started；
- mutation_observed | stream_eof -> observed；
- content_validated | tool_completed | turn_completed | final_result | journal_sealed -> completed；
- tool_failed | turn_failed | resource_limit_exceeded | process_terminated -> failed；
- adapter_rejected -> rejected；
- expected zero-exit 且 framing 完整的 process_exited -> completed；
- 其他 process_exited -> failed。

除公共字段外，V1 per-event matrix 固定如下；Required 与 Allowed optional 之外的字段全部 forbidden：

| Event | Required | Allowed optional |
|---|---|---|
| process_started | job_identity_id, process_kind, run_id | none |
| tool_started | item_id, tool_kind | none |
| mutation_observed | mutation_observation_id, byte_count, path_class | approved_path_id |
| stream_eof | stream_kind, byte_count, partial_byte_count, termination_class | none |
| content_validated | mutation_observation_id, approved_path_id, canonical_relative_path, content_sha256, byte_count | none |
| tool_completed | item_id, tool_kind, exit_code | report_projection_hash |
| turn_completed | bounded_usage | none |
| final_result | final_state, validated_result_projection_hash | reason_code |
| journal_sealed | segment_no, accepted_end_offset | none |
| tool_failed | item_id, tool_kind, reason_code | exit_code |
| turn_failed | reason_code | none |
| resource_limit_exceeded | resource_kind, configured_limit, observed_at_least, reason_code | job_identity_id |
| process_terminated | job_identity_id, process_kind, reason_code | exit_code |
| adapter_rejected | framing_class, reason_code | stream_kind, partial_byte_count |
| process_exited | job_identity_id, process_kind, exit_code | reason_code |

<code>none</code> 表示无 event-specific optional field。ID/enum/hash/usage/count 都由 schema 给出长度、字符集、范围和 catalog；<code>report_projection_hash</code> 与 <code>validated_result_projection_hash</code> 只允许引用已经 secret scan 的白名单 projection。Completed process_exited 禁止 reason_code，failed process_exited 必须有 reason_code；final_state=blocked 必须有 reason_code，completed 时禁止。Tool event 必须有 bounded item_id；exit_code 只在 process/tool terminal；numeric usage 只在 turn_completed。Failed/rejected 必须引用 version/hash-bound reason catalog。

Runtime 收到 complete line 但 JSON/schema/event/type-status 不合法时，关闭 Job、platform_incompatible、exit 6。Exit 2 只用于 operator input 或 checked-in state/catalog request 非法。

首 event prev_hash 为 64 个零；event hash 是排除 event_hash 后的 domain-separated canonical event hash。

### 11.3 Secret-safe mutation 与 final result

Secret/path scan 前，mutation_observed 只能持久化：

- CSPRNG mutation_observation_id；
- byte_count；
- enum path_class；
- 仅在成功映射时的 public versioned approved_path_id。

Unknown/deny/out-of-bound/reparse path 不保存原文、ordinary hash 或可字典枚举 digest。Scan 失败只保存 random quarantine ID、byte_count 和 enum reason。Path/content 全通过后，后续 content_validated 才可携带 canonical relative path 和 content SHA-256；旧 event 永不修改。

WriterFinalResult raw data 在 controller validation 前只存在内存。其 pre-scan persistence projection 只含 completed|blocked、optional enum reason、最多 200 个 sorted unique approved_path_id，无 summary/free text。Canonical path/content hash 只在后续 validated report 中出现。Controller 以 filesystem/Git audit 为准，不信任 model 声明。

### 11.4 Journal、segment 与 ExecutionReceipt

- Normalized event append -> FlushFileBuffers -> short SQLite cursor transaction；DB 只能落后 journal，不能领先。
- JournalSegmentManifest 绑定 segment_no、previous_segment_hash、accepted_end_offset、first_seq、last_seq、seal_hash。
- 损坏 segment 不截断也不继续 append；原字节进入 encrypted sealed quarantine，continuation 从最后 accepted event hash 开始并记录 prior segment/offset。
- Complete invalid raw JSONL line 或 normal process exit 后仍有 partial line 为 adapter incompatibility。
- Cancel、timeout、Job kill 或 abnormal crash 留下的 EOF partial buffer 只属于 attempt recovery，不暂停平台。
- 两类 partial/invalid buffer 都只持久化 byte count、framing class、termination class 和 enum reason，不持久化 bytes、prefix/suffix 或 content hash。
- ExecutionReceipt 只有六项同时满足才可发布：process exited、stdout JSONL EOF、final schema passed、无 output/resource limit overflow、normalized chain/segments sealed、Job zero-process。
- Receipt 绑定 frozen manifest、config/overlay、feature/tool inventory、reason catalog、writer marker/launch barrier 和 journal chain；不保存 raw-output hash。

### 11.5 Artifact 与 quarantine

- Approved artifact 顺序：immutable spool temp write+flush -> SQLite outbox/fenced intent -> no-replace publish -> read-back size/hash -> immutable terminal。
- Final 已存在时，只在同 intent、logical name、size 和 validated hash 时确认；禁止 os.replace。
- Intent 前 orphan temp 只有在 content scan 后才可使用 deterministic attempt/logical ID；一律 quarantine，不自动收养。
- Raw/possibly-secret incident bytes 使用与 path/content 无关的 random quarantine ID。
- Quarantine payload 只允许来自 filesystem mutation、artifact/outbox、normalized controller journal 或 database/integrity incident；process JSONL/stdout/stderr、prompt、argv/env、agent/tool text 永远不得进入 quarantine。
- QuarantineCryptoPolicy 固定 Windows CNG AES-256-GCM、每对象 fresh 96-bit CSPRNG nonce、128-bit tag，AAD 绑定 policy generation、installation ID、attempt ID、random quarantine ID、byte count 和 enum reason。
- Random 256-bit quarantine encryption key 由 current-user DPAPI 保护为 immutable <code>QuarantineKeyEnvelope.v1</code>；另一个独立的random 256-bit runtime integrity key保护controller state/backup wrapper，保存为 <code>RuntimeIntegrityKeyEnvelope.v1</code>。两者使用不同domain/purpose、installation ID和key generation，明文及其普通hash永不持久化或进入evidence/log。Envelope只允许current-user DPAPI scope，绑定wrapper bytes hash、owner SID hash、creation generation和rotation predecessor；key unwrap failure、purpose混用、nonce reuse或tag failure均为hard integrity error。
- Public evidence 只保存 random ID、size、enum reason 和 seal version，不保存 content hash。

### 11.6 External evidence

- RepoProfile.evidence_mode 必须为 runtime_external_v1。External仅表示位于目标repo之外；root必须精确等于当前 ActiveRuntimeIdentity 所绑定 composition 的 <code>%LOCALAPPDATA%\LocalAIRuntime\evidence</code> 受管root或其controller分配的repo/task descendant，不接受operator提供的任意绝对路径。
- Qualification以no-follow directory handles证明evidence root的volume/FILE_ID_128/owner/DACL/ancestry，且它与target repo root、Git common/admin dir、任何worktree、runtime state/authorization/ownership/backup/quarantine/reserve/temp以及全部attempt writable root两两不相等、互非ancestor/descendant、无reparse/hardlink/8.3/case alias overlap。Writer/gate/Git/task payload对该root始终deny-read/write；只有持有current fence的controller evidence publisher获得精确publish child权限。任一identity/ancestry/alias漂移在publish前阻断并进入repo requalification或platform incompatible，不能退回repo内evidence。
- Target repo contract 必须明确接受 external evidence ID/hash，否则 writer qualification 失败。
- Commit message 不含 evidence ID。Commit/ref 后由 ExecutionReceipt、EvidenceIndex.v2、CloseoutBundle.v2 建立关联，避免 hash 环。
- 只有持有 current fence 的 Batch closing state machine 可发布 closeout；diagnostic gates run 永不创建 closeout。

### 11.7 SQLite 与 quiescent backup

- SQLite 固定 journal_mode=DELETE、foreign_keys=ON、synchronous=FULL、busy_timeout=5000、short transactions 和 backup API。
- Uniqueness 至少覆盖 family fingerprint/root、root+generation、task+attempt_no、每 task generation 一个 writer execution commit、每 stage_run 一个 process/execution commit、attempt+effect AuthorizationExecutionGrant、safety-only effect record、write-accounting snapshot sequence、emergency-reserve generation、optional hard-quota reservation、attempt+event_seq、segment sequence、fenced head/result、resubmission source/successor、artifact logical name、object plan/set、task ref、active Authorization/revoke head 和 global capacity lease。
- Backup 是 state/evidence backup。按 canonical repo identity 排序获取 global、registry 和所有 referenced repo mutex；要求零 active lease、零 nonterminal/recovery attempt、零 executing action、零 pending outbox。
- 先 SQLite backup API，再收集 terminal referenced immutable evidence、ownership/activation/policy 和 terminal-referenced sealed quarantine，最后写/验 backup manifest。
- 排除 auth content、<code>.sandbox-secrets</code> 全部内容/metadata、<code>.sandbox</code> mutable bytes、其他 mutable Codex state、environment bundle content、worktree、ordinary quarantine 和 nonterminal spool。
- Backup必须包含被引用sealed quarantine所需的DPAPI-wrapped <code>QuarantineKeyEnvelope</code> 和验证state/manifest所需的 <code>RuntimeIntegrityKeyEnvelope</code>，并在manifest中绑定envelope ID/generation/wrapper hash/owner SID hash/installation ID；不包含任何明文key。Restore drill必须在same-SID隔离root实际unwrap、验证至少一个fixture seal与integrity wrapper，然后立即清除明文内存；缺envelope、wrong SID/purpose/generation或unwrap失败均使backup不可恢复。
- 每个sealed backup generation发布后，在backups controller root维护唯一mutable CAS <code>BackupRestoreEligibility.v1</code> head；它绑定backup ID/generation、captured state mutation generation、manifest hash、backup时的platform control generation和状态 <code>eligible|stale|restoring|consumed</code>。只有backup开始前platform已经suspended、整个capture期间保持同一control generation、publish后没有resume，才能标记eligible；普通running状态创建的backup仍可verify/restore-drill，但head直接为stale。除下述restore-start分支外，任何后续authoritative mutation，包括task/attempt/ref-history、Authorization/revoke、ownership/cutover、activation、evidence index、operator action、platform resume或新backup开始，必须先对当前eligible generation用 <code>CREATE_NEW|FILE_FLAG_WRITE_THROUGH</code> 写入并FlushFileBuffers/close immutable <code>BackupPostActivity.v1</code>，再CAS head为stale，之后才允许原mutation。Marker先写而mutation未发生只会保守失效；绝不允许mutation先于marker。
- Production restore只接受platform仍处于backup绑定的同一suspended control generation、head仍指向同一generation且状态eligible、<code>BackupPostActivity</code>不存在、manifest/envelopes/owner SID/installation identity全匹配的backup。Restore-start是marker-before-mutation的唯一互斥替代分支：先CREATE_NEW并flush immutable <code>BackupRestoreIntent.v1</code>，其中预绑定interactive token proof、OperatorAction/OperatorWorkSession IDs和expected eligibility head；再CAS head从eligible到restoring；只有CAS成功后才写对应DB operator records并开始restore effect。Crash在intent与CAS之间时，只能由相同intent完成CAS或将该backup永久stale；响应丢失只能按同一intent继续，不能创建第二restore。Restore完成后head进入consumed，platform保持suspended，并在任何claim前重验全部repo identity/base/ref-history、qualification、Authorization、ownership和activation generation。缺eligibility sidecar、已导出的静态旧副本、marker存在或状态歧义均只允许restore drill，生产restore fail closed；禁止通过删除marker、回退head或复制旧backups目录恢复资格。
- Restore drill 只写新 isolated root，验证 DB/integrity/evidence 和 missing-environment 行为，不覆盖 production。

## 12. Deterministic Git protocol

### 12.1 支持范围

- 只支持 local fixed-NTFS、SHA-1 object format、files refs 的标准 Git repo。
- 不支持 SHA-256 object format、reftable、active submodule、LFS filter、external filter/diff/merge driver、replace/graft/alternate substitution、remote operation 或 historical detached base。
- Task ref 恰好为 <code>refs/heads/codex/batch/&lt;lowercase-task-uuid&gt;-a&lt;attempt_no&gt;</code>，attempt_no 只能 1-3；完整 UTF-8 bytes 同时通过 pinned <code>git check-ref-format</code> 与 checked-in verifier。
- 任何 Git side effect 前枚举 loose/packed refs 和 ref-directory components，按 exact spelling 与 Windows invariant collision key 双重检查。Exact task ref、case alias 或 file/directory prefix collision 已存在都禁止首次创建；只有同一 fenced intent 的 response-loss reconcile 可以确认既有 expected OID。
- 0.2 采用无 reflog publication policy。<code>core.logAllRefUpdates=false</code> 只阻止缺失 reflog 的自动创建，不能证明已有 reflog 不会被追加；因此每个会被 runtime 更新的 HEAD/ref 都必须单独执行 exact reflog path absence proof，并使用 <code>--no-create-reflog</code>。

### 12.2 Hardened Git environment 与 first call

第一条 Git 命令前，controller 用 Win32 no-follow 解析 .git file/admin/common-dir identity。第一条 Git process 已处于 final empty env、Job、overlay 和 batch-git-audit，禁止先在普通 subprocess 跑 rev-parse。

Git adapter 清除 inherited GIT_*，设置：

~~~text
GIT_CONFIG_NOSYSTEM=1
GIT_CONFIG_GLOBAL=NUL
GIT_CONFIG_SYSTEM=NUL
GIT_ATTR_NOSYSTEM=1
GIT_TERMINAL_PROMPT=0
GIT_OPTIONAL_LOCKS=0
GIT_NO_REPLACE_OBJECTS=1
GIT_CONFIG_COUNT=9
~~~

并按顺序设置 GIT_CONFIG_KEY_n/GIT_CONFIG_VALUE_n：

~~~text
core.hooksPath=<attempt-managed-empty>
core.excludesFile=NUL
core.attributesFile=NUL
commit.gpgSign=false
core.fsmonitor=false
core.logAllRefUpdates=false
gc.auto=0
maintenance.auto=false
core.autocrlf=false
~~~

GIT_DIR、GIT_WORK_TREE、GIT_COMMON_DIR、GIT_INDEX_FILE、GIT_OBJECT_DIRECTORY、GIT_ALTERNATE_OBJECT_DIRECTORIES、GIT_EXEC_PATH、GIT_TEMPLATE_DIR、GIT_NAMESPACE 只由 adapter 为单次 operation 设置。Git adapter 禁止 <code>GIT_REFLOG_ACTION</code>，也不接受 command/env/profile 覆盖无 reflog policy。Batch-git-local permission overlay 对 common-dir <code>logs/**</code> 默认 deny write；唯一例外是 create_worktree fenced action 对本次新建、runtime-owned per-worktree admin 目录中 exact <code>logs/HEAD</code> 的验证后移除。

第一条 audit command 恰好为：

~~~text
<git> config --local --no-includes --null --name-only --list
~~~

完成 key-name classification 后才可读取 allow_safe_value 的值。Remote/LFS 等 allow_name_only value 永不读入 process output/evidence。随后精确运行 rev-parse --path-format=absolute --git-common-dir，与 Win32 resolution 交叉验证。

### 12.3 GitConfigPolicy 与 protected surface

- 默认 deny。Include/includeIf、credential、HTTP/proxy/header、filter/process、diff/textconv、merge driver、hooks、fsmonitor、signing、SSH、URL rewrite、protocol/submodule、alias/editor/pager、external attributes/excludes、alternate 和 unknown key 全阻断。
- allow_name_only 仅限未使用的 remote URL/fetch、branch tracking、LFS endpoint/access key name。
- allow_safe_value 是完整版本化 catalog，覆盖实际需要的 repo/object format、bare=false、filemode、logAllRefUpdates、symlinks、ignorecase、NTFS/HFS protection、longpaths、autocrlf/eol/safecrlf 等有界 boolean/enum；runtime 仍用 controller override。
- Duplicate singleton 或 invalid value fail closed。
- Audit .git/info/attributes、.git/info/exclude、default hooks、config.worktree、alternates、replace refs、grafts、base-tree .gitattributes/.gitmodules/.lfsconfig、Git link entries、touched-path attrs 和全部 protected path/mode/OID。

Protected surface 至少包括 .git、.codex、.agents、skills、.local-ai-runtime、AGENTS chain、gates/build scripts、lockfiles、profiles/templates、Git policy 和全部 qualification-sensitive input。优先 immutable-read；secret path deny-read/write。

Writer 前后及每个实际 spawn 前后扫描全部 writable paths/ancestors 的 final identity、ACL、reparse、hardlink。任何新 junction/symlink/hardlink escape 阻断。

### 12.4 Controlled index 与 GitObjectPlan

- 使用 attempt-owned index，从 expected base 执行 read-tree。
- 只 stage approved validated delta。全部 diff 强制 --no-ext-diff --no-textconv，并把 ignored/untracked 纳入 cleanliness。
- Runtime 禁止 git add 或 filtered/path-aware blob write。Blob OID 从 secret-scan 后精确 bytes 计算，通过 controlled update-index --cacheinfo stage；删除使用 controlled index removal。
- Writable/touched path 上 active filter、ident、working-tree-encoding 或其他 content-transforming attribute 阻断 qualification/closeout。
- 写任何 Git object 前，GitObjectPlan canonically 计算 expected blobs/trees/commit 的 type/size/OID 和完整 graph，并绑定 validated bytes 与 index-input hash。
- Controller 独立生成 canonical blob/tree/commit raw payload、tree ordering、完整 graph 和 expected OID，并在 contract test/Q0 与 pinned Git fixtures 交叉验证；controller 不实现或持久化 loose-object zlib representation。
- Fenced materialize_object_set intent 先绑定 plan hash；pinned Git 对精确 controller payload 使用 <code>git hash-object -t &lt;type&gt; -w --stdin</code> 写入 attempt-local GIT_OBJECT_DIRECTORY，base common objects 只读 alternate。每次返回 OID 必须等于 controller expected OID，再用 <code>git cat-file --batch</code> read-back type、size 和 payload bytes，与原 canonical payload 逐字节一致。
- Git plumbing 不是唯一 oracle：任何 Git-returned OID/read-back 与 controller framing/OID 不一致都判 adapter/platform incompatible；controller 也不得绕过 pinned Git 自行写 loose zlib object。
- ObjectSetManifest 必须与 plan 完全一致，并记录每个 object type、size、OID、post-secret-scan payload SHA-256 和 reachability edge。只有 sealed matching set 可 promotion。
- Claim CAS 成功时生成一次 <code>claim_epoch_seconds</code>：读取可信 UTC，向下取整到整数秒，并在同一 claim transaction 写入 immutable ResolvedAttemptManifest；不得在 Git closeout 时重新读取时钟。GitObjectPlan 必须包含同一值并绑定 ResolvedAttemptManifest hash。相同 manifest 的 author/committer time 必须相同；改变 claim time 必然创建不同 ResolvedAttemptManifest/GitObjectPlan/commit OID，不能只改 commit payload。

### 12.5 Commit bytes

Commit raw payload headers 恰好按以下顺序：

~~~text
tree <expected_tree_oid>
parent <expected_base_commit>
author Local AI Runtime <local-ai-runtime@localhost.invalid> <claim_epoch_seconds> +0000
committer Local AI Runtime <local-ai-runtime@localhost.invalid> <claim_epoch_seconds> +0000

batch(<template_id>): <task_uuid> attempt <attempt_no>

Manifest: sha256:<resolved_manifest_hash>
~~~

- 恰好一个 parent；禁止 encoding、signature、mergetag 和额外 header。
- Message 为 UTF-8 且恰好一个末尾 LF。
- ResolvedBatchManifest 排除 derived commit/ref/evidence IDs，避免 hash cycle。
- Controller 在写入前计算 <code>SHA1("commit &lt;size&gt;\0" + payload)</code> 并写入 GitObjectPlan。

### 12.6 Promotion、finalize、ref 与 cleanup

固定顺序：

~~~text
seal object plan/set
-> promote objects
-> verify common-store reachability with alternates cleared
-> finalize worktree index
-> finalize detached HEAD
-> create task ref
-> publish evidence
-> remove worktree
~~~

- 除 safety-only read reconcile 外，每步都有 fenced intent/result 和 current Authorization check。
- <code>create_worktree</code> intent 覆盖 Git 创建 admin/worktree、识别 runtime-owned per-worktree admin path、验证任何新 <code>logs/HEAD</code> 只属于本次动作并将其移除、read-back absence 的完整 effect。动作前若 exact per-worktree admin/log path 已存在，或动作后无法证明 <code>logs/HEAD</code> 不存在，则失败并保留供 recovery；不得沿用或清理 unknown path。
- Promotion create-if-absent。Existing object 按 canonical type、size、payload 和 Git OID 验证，禁止比较 loose zlib bytes。
- Finalize 前证明 tracked worktree path/mode/bytes 等于 expected tree，且无 unapproved untracked/ignored file。
- finalize_worktree_index 在 expected/old-index hash 验证后原子替换真实 worktree index，并 read-back。
- finalize_worktree_head 先证明 per-worktree <code>logs/HEAD</code> 不存在，再单独执行 <code>git update-ref --no-create-reflog --no-deref HEAD &lt;expected-commit&gt; &lt;expected-base&gt;</code>，随后再次证明该 log path 不存在并验证 HEAD。禁止 reset --hard。
- Task ref 只在 common reachability、index finalize 和 HEAD finalize 全绿后，先证明 loose/packed ref collision 与 exact common-dir reflog path 均不存在，再执行 <code>git update-ref --no-create-reflog &lt;exact-task-ref&gt; &lt;expected-commit&gt; &lt;zero-oid&gt;</code>；随后同时验证 ref OID 和 reflog absence。任何 reflog 出现都使 publication 进入 reconcile_required，不得删除 unknown/existing log 后伪装成功。
- 不确定结果只按 expected plan/tree/commit/ref reconcile，不搜索任意 dangling commit，也不生成不同 object。
- Runtime 永不删除 task ref。
- 自动 remove 要求 runtime-owned、Job zero-process、fence 一致、所有 action/evidence terminal、HEAD/index/worktree clean、Authorization current。删除后验证目录和 common-dir worktree admin entry 都消失；否则保留并进入 cleanup_required。

## 13. 资源上限、capacity 与 scheduler

### 13.1 固定 ResourceLimitPolicy

0.2 的默认上限固定如下；TaskTemplate 只能在 Authorization envelope 内收紧，不能放宽：

| Resource | 0.2 ceiling |
|---|---:|
| writer wall time | 3,600 s |
| each gate wall time | 1,800 s |
| all gates cumulative wall time | 7,200 s |
| deterministic closeout wall time | 900 s |
| attempt wall time | 11,700 s |
| scheduled invocation wall time | 12,600 s |
| writer JSONL/stdout aggregate | 8 MiB |
| writer stderr | 8 MiB |
| one JSONL line before LF | 256 KiB |
| normalized journal aggregate | 8 MiB |
| one normalized event | 16 KiB |
| WriterFinalResult | 1 MiB |
| each non-writer stdout/stderr stream | 8 MiB |
| validated diff representation | 16 MiB |
| changed paths | 200 |
| one validated changed regular file | 32 MiB |
| validated changed-file bytes aggregate | 256 MiB |
| published artifacts aggregate | 256 MiB |
| each gate-run writable cache/output aggregate | 512 MiB |
| each gate-run writable filesystem entries | 20,000 |
| attempt writable growth beyond qualified base materialization | 2 GiB |
| attempt writable filesystem entries | 50,000 |
| attempt-local Git object-store growth | 512 MiB |
| common-store promoted-object growth per attempt | 512 MiB |
| attempts per task generation | 3 |
| process tree active processes | 64 |
| per-process committed memory | 4 GiB |
| each process-bearing Job committed memory | 8 GiB |

- <code>ResourceLimitPolicy.v1</code> 为每项声明 <code>enforcement_class</code>：pipe/structured-input 使用 bounded reader/parser，process/memory 使用 Job/controller deadline，controller-owned file/publish 使用 bounded writer，task-created filesystem growth 使用 <code>accounting_kill_audit</code>，只有资格化增强能力才使用 <code>hard_quota</code>。表中 ceiling 都是 terminal acceptance hard gate，但只有前四类和可选 hard_quota 能声称在 effect 完成前原子阻止越界。
- Job 固定启用 kill-on-close、no-breakaway、no-silent-breakaway、die-on-unhandled-exception、active-process 和 memory limits；不使用不可恢复的 CPU-time Job limit，wall deadline 由 controller monotonic timer 执行。
- Full Q0 必须证明当前 Windows build 支持并实际执行这些 limits；宿主无法设置或 read-back 不一致属于 platform_incompatible，不允许静默降级。
- 所有 count 以原始 bytes/path/process 为单位，不使用压缩后大小。MiB 为 1,048,576 bytes，GiB 为 1,073,741,824 bytes。
- JSONL/stdout aggregate 包含 LF 和被判定为 partial 的末尾 bytes；normalized journal 独立计数，不能因 raw bytes 已丢弃而绕过。
- Diff limit 只限制 evidence/report representation；controller 仍必须完整审计最多 200 个 changed paths 的真实 bytes、mode 和 object。
- Artifact limit 包括 outbox temp 和 final payload，不包括加密 sealed quarantine；quarantine 另受每 attempt 256 MiB、全局 2 GiB retention budget 约束，超限时停止新 claim 并生成 OperatorAction，禁止删除仍被 terminal record 引用的对象。
- Changed-file aggregate 按 secret-scan 后逻辑 file bytes 计数；attempt/gate/object budget 按文件系统实际 allocation delta 与逻辑 bytes 两者较大者计费，hardlink/reparse/alternate 不得抵扣。Common-store existing object 经 canonical verification 后计零新增，new object 按实际 allocation 计入 promotion growth。

### 13.2 Limit enforcement

每个 pipe 都由独立异步 reader 从 process 创建时开始持续读取。Reader 必须先观察第 <code>limit+1</code> byte，才能断言超限；随后按固定顺序执行：

~~~text
persist resource_limit_exceeded intent
-> close/terminate Job under current fence
-> continue draining all pipes to EOF
-> persist final byte counts and enum reason
-> seal journal segment
-> durable recovery handoff
~~~

超限后不保存截断正文、prefix/suffix、普通 digest 或可恢复 payload。计数器使用 checked unsigned 64-bit arithmetic；溢出按 resource limit failure 处理。单 task 资源超限默认只失败该 attempt/template observation，不自动升级 platform scope；若 limit enforcement、Job kill 或 pipe drain 行为偏离 Q0 才进入 platform_incompatible。

所有大小、数量、时间、path、parameter、overlay、command-line 和 process 限制都必须有 <code>limit-1/limit/limit+1</code> fixtures。时间边界使用 fake monotonic clock 做 contract test，并在 Q0 用真实短限额 probe 验证，不通过长时间 sleep 模拟。

0.2 mandatory <code>WriteAccountingPolicy.v1</code> 不伪装成目录级原子 quota，固定执行：

1. claim 和每次 process spawn 前，以 no-follow handle 固定全部 writable root identity，记录 logical bytes、allocated bytes、entry count、free-space reserve、EmergencyDiskReserveRecord 和 high-water marks 的 immutable <code>WriteAccountingSnapshot.v1</code>；适用的 execution authority 绑定 policy generation、mode 和 pre-effect snapshot hash；
2. controller/Git/artifact writer 使用有界 streaming/no-replace API，在每次 extend/publish 前检查本 stage ceiling；task process root 使用 ReadDirectoryChangesW 作为 rescan trigger，并以不超过 500 ms 的 monotonic fallback 重新核算 logical/allocated bytes、entry count 和 free reserve。Watcher overflow、scan gap、identity漂移或算术溢出与 limit+1 等价；
3. 首次观察到 per-file、aggregate、object、gate、artifact、entry-count 或 emergency-reserve limit+1 时，先 durable 写 resource-limit intent，再关闭/终止对应 Job，持续 drain，seal journal，并在进程退出后对全部 writable root 做 no-follow 完整审计；
4. final audit 未证明每个 entry 的 path class、identity、logical/allocated size、link/reparse/ADS policy 和 aggregate ceiling时，attempt 不得进入 object plan、promotion、ref、evidence publish 或自动 cleanup；超限/未知内容 quarantine或保留 worktree，不能靠删除掩盖；
5. accounting mode 明确承认：没有 qualified hard-quota primitive 时，task process 在观察与 Job termination 之间可能产生瞬时 overrun。因此安全声明是“越界结果不得发布，并以磁盘 reserve、持续核账和 fail-closed termination 限制主机风险”，不得宣称每个 write 在内核提交前都被拒绝。

<code>HardWriteQuotaCapability.v1</code> 是 optional enhancement，而非 0.2 P2 永久前置条件。只有宿主存在经独立 Full Q0 证明的 per-root/per-sandbox-user primitive 时，才可启用 <code>hard_quota</code> mode，并通过 <code>HardWriteQuotaReservation</code> 绑定 primitive type/version、volume、sandbox SID、quota generation、charge unit、reserve/release/recovery 和 bypass probes。NTFS per-volume/per-user quota、Windows Server FSRM folder quota 或 Job I/O rate 不能未经适用性证明就冒充 attempt-directory atomic quota。Capability 缺失时保持 accounting_kill_audit；capability 存在但漂移时停止新 claim并回到 requalification，不能静默降级正在运行的 attempt。

Mandatory Q0 必须验证 accounting watcher/fallback、limit+1 terminate/drain、稀疏/压缩/hardlink/rename/mmap/ADS 审计、controller crash 恢复、reserve 与 disk_pressure 分流；只有启用 hard_quota mode 时才额外要求“write 生效前 deny”的 bypass matrix。两种 mode 都必须在 Authorization、receipt 和 evidence safe projection 中显式记录，不能由实现自动选择。

Runtime state volume 必须在允许 claim 前存在一个 controller-only、non-sparse、non-compressed、fully allocated 的 emergency reserve file；默认 1 GiB，identity/allocated bytes/DACL/generation 记录在 <code>EmergencyDiskReserveRecord.v1</code>，task/writer/gate/Git 均 deny-read/write/delete。正常运行不得把该文件计入可用空间或自动释放。只有已经 durable 进入 disk_pressure/safety recovery、当前 Job 已收到 termination intent且controller自身无法完成 seal/handoff 时，才可通过 fenced safety-only action释放一次 reserve；释放后 platform 保持 suspended，直到受管 maintenance 在零 active attempt 时重新完整预分配、read-back并 CAS 新 reserve generation。Repo common-store volume 只允许 controller 的 bounded promotion/ref writes，每次 extend 前独立检查其 free-space floor；task process 的所有非 Git-object writable roots必须位于拥有该 emergency reserve 的 runtime volume。

### 13.3 Deadline、lease 与磁盘

- 活进程 deadline、heartbeat interval 和 retry delay 使用 monotonic clock；审计时间使用 UTC 微秒格式 <code>YYYY-MM-DDTHH:MM:SS.ffffffZ</code>。
- Attempt 持久化 boot identity、monotonic origin、UTC origin 和 last observed UTC。Boot 改变或 wall clock 回退超过 1 s 时，旧 lease 失效但不能直接 takeover，必须先完成 Job/PID/fence recovery proof。
- Heartbeat 每 15 s durable 更新，lease TTL 为 90 s。Controller event loop 若连续两次错过 heartbeat，先停止创建新副作用并执行 safety handoff。
- Claim 前 runtime volume 的 reserve 文件必须完整，且 reserve 之外的可用磁盘必须至少为 <code>max(5 GiB, 2 * base_materialized_bytes + 2 * artifact_limit + 2 * attempt_writable_growth_limit)</code>；每个将接收 bounded controller write 的 repo volume也必须满足该 operation ceiling + 1 GiB floor。模板只能在 Authorization envelope 内下调写入预算。
- 运行中 reserve 外的 free bytes 低于 1 GiB、reserve identity/allocation 不完整或 repo-volume operation floor 不满足时，platform resource lane 进入 <code>disk_pressure</code>，停止新 claim/gate/object/artifact，安全终止或收口活进程、seal 并把当前 attempt 标记 <code>resource_exhausted/recovery_pending</code>；不得误报 needs_environment，也不得靠删除当前或其他未终态 attempt 恢复空间。只有受管清理、容量恢复、reserve重建和quick preflight都成功后才能 CAS 回 normal。

### 13.4 Global capacity 与调度

- Batch global writer capacity 恰好为 1。Capacity 覆盖 preparing 中第一次可写 worktree materialization，直到 writer/gates/object/ref/evidence 的不可冲突部分 terminal 并完成 recovery handoff；纯 parked task 不占 capacity。
- Recovery queue 优先级固定为：live-process safety、publication recovery、deterministic closeout、cleanup、due retry、new promoted task。相同优先级按 <code>ready_at_utc, root_task_id, generation, attempt_no</code> 排序。
- 等待 auth、environment、Authorization、repo maintenance 或人工 resolution 的项 durable park、释放 capacity，并按 OperatorAction dedup key 通知；轮询不得制造新通知或新 attempt。
- Platform unavailable 退避为 Retry-After，否则 5 min、15 min、1 h、6 h；成功 quick preflight 后清零。Canary infrastructure failure 只立即重试一次。
- Scheduler 使用当前用户的 Windows Task Scheduler：InteractiveToken、LeastPrivilege/Limited、Hidden、StartWhenAvailable、IgnoreNew、每 5 min 触发、ExecutionTimeLimit 12,600 s。它每次最多 claim/drain 一个 task，不执行循环守候。
- Scheduled invocation 只允许 <code>batch drain --max-tasks 1 --json</code>、safety recovery 和只读 status/doctor；禁止 login/logout、environment preparation、Authorization activation、ownership repair、cutover/rollback、Native maintenance 和 kill-current。
- Scheduler definition、executable identity、argv、working directory、environment policy、task XML hash 和 owner SID 纳入 RuntimeCompositionManifest，并由 ActiveRuntimeIdentity 共同绑定；漂移停止 scheduled claim。

## 14. 公共 CLI、退出码与 OperatorAction

### 14.1 命令面

0.2 公共命令固定为：

~~~text
runtime install|status|activate|rollback
platform setup|login|logout|auth-status|model-probe|sandbox-probe|qualify|doctor|suspend|resume|kill-current
environment register|verify|status|retire
repo register|verify|qualify|cutover|rollback|ownership-status|ownership-repair
repo maintenance enter|status|exit
native run
authorization activate|revoke|status|verify
batch prepare|submit|drain|status|cancel|retry|reconcile|resolve|doctor
contracts catalog|verify
gates run|verify
evidence verify
backup create|verify|restore-drill|restore
eval baseline|compare
schedule install|status|run-now|remove
compat verify
~~~

任何未列命令或 option 都是 contract input error。所有命令提供稳定 <code>--json</code>；scheduler 强制 JSON。Machine response 是 canonical JSON envelope，至少含 <code>schema_version/command/outcome/reason_code/object_ids/evidence_locators/suggested_action_id</code>；不存在的 optional field 省略，禁止 null 和自由文本 reason。Human-readable 输出只从同一 envelope 和 checked-in message catalog 渲染。

- <code>batch submit</code> 的普通重放永远返回 generation-0 root task，并另列当前 <code>family_state/current_task_id/current_generation</code>；不能把 mutable current 当作 submit 返回身份。
- <code>batch status &lt;root-or-member&gt;</code> 返回完整 family lineage 和当前 task，但默认不展开敏感 evidence。
- <code>batch retry</code> 自身只在第 9.4 节 same-generation RetryEligibility 通过时创建 fresh attempt；否则绝不创建 task/attempt，而由 GuardCatalog 按确定性优先级返回恰好一个分流：<code>create_resubmission_v1</code> guards 通过时建议 <code>batch resolve &lt;source_task_id&gt; --code create_resubmission_v1</code>；stale base 建议重新 <code>batch prepare</code> 后执行新的四字段 <code>batch submit</code>；已有/不确定 publication 建议 <code>batch status</code> 或只读 <code>batch reconcile</code> 进入 publication recovery；其余不可自动证明状态返回唯一 OperatorAction ID。不得把所有 retry 拒绝都误导到 resubmission。
- <code>batch resolve</code> 只接受 checked-in resolution code 和 code-specific fixed arguments；<code>create_resubmission_v1</code> 不接受重新提交 repo/template/parameters/base。
- <code>batch reconcile</code> 只读；<code>batch cancel</code> 接受枚举 cancel_reason_code；不得在 argv 中接受 prompt、secret、credential 或自由文本 reason。
- Login 使用受管交互子进程和 keyring；登录材料不经过 controller argv/stdin、数据库或 evidence。
- <code>backup restore &lt;backup_id&gt;</code> 是interactive-only高风险命令，只接受已登记的公开backup ID，不接受自由目标路径、marker override或force option；它必须执行第11.7/17.4节的eligibility、intent、same-SID unwrap、generation CAS和post-restore suspended verification。Scheduled/service token永远拒绝该命令。

### 14.2 退出码

| Code | Meaning |
|---:|---|
| 0 | 成功；或 drain 时没有 ready task |
| 2 | Operator/checked-in input、CLI state 或 contract 组合非法，零未授权副作用 |
| 3 | Policy、Authorization、ownership、environment、stale base 或 manual recovery 阻断 |
| 4 | Gate、evidence、evaluation、resource 或当前 attempt 失败 |
| 5 | Temporarily unavailable、needs_auth、qualification_suspended 或 disk_pressure |
| 6 | Platform/adapter/toolchain/config/sandbox 行为 incompatible |

退出 2 不得用于 Codex 运行时 JSONL/schema 漂移；该边界必须 safety terminate 并退出 6。每个非零 machine response 都必须给稳定 reason_code、非敏感 evidence locator 和最多一个 suggested action。无法给出安全自动动作时，suggested action 是对应的 OperatorAction ID，而不是自然语言命令猜测。

### 14.3 OperatorActionCatalog

Catalog 至少定义以下 action family：

| Action | Scope | Dedup key |
|---|---|---|
| platform_login_required | provider/global | action + auth_generation |
| environment_requalification_required | environment | action + binding_id + observed_generation |
| disk_pressure_remediation | installation/volume | action + volume_identity + resource_generation |
| authorization_activation_required | repo/template | action + repo + template + sensitive_set_hash |
| repo_requalification_required | repo | action + repo + ownership_generation |
| template_suspension_review | template | action + template + failure_type + policy_generation |
| recovery_required | attempt | action + attempt + recovery_checkpoint_hash |
| reconcile_required | fenced action | action + action_id + head_hash |
| cleanup_required | attempt | action + attempt + expected_cleanup_hash |
| ownership_repair_required | repo | action + repo + observed_registry_hash |
| maintenance_recovery_required | repo | action + repo + maintenance_generation |
| activation_rollback_required | installation | action + activation_generation |
| backup_restore_required | installation/backup | action + backup_id + eligibility_generation |
| cutover_or_rollback_required | repo | action + repo + ownership_generation |
| platform_suspend_review | platform | action + control_generation |
| emergency_kill_current | attempt | action + attempt + JobIdentity hash |

每个条目固定 <code>reason_code/scope/precondition_guard_ids/allowed_command/dedup_key/notification_policy/capacity_disposition/terminal_conditions</code>。OperatorAction row immutable；状态变化通过 append-only resolution 和 mutable generation CAS head 表示。DB 不保存操作者自由文本说明。

需要人工副作用的命令必须创建 <code>OperatorWorkSession.v1</code>，绑定 session ID、SID hash、action ID、scope、reason code、start/end UTC、active minutes、result、evidence locator 和 superseded session。Interactive console presence 通过启动 token/session identity 证明；scheduled/service token 禁止执行这些命令。

每个 active OperatorAction 必须投影到 <code>durable_local_status_v1</code> action inbox，供 <code>runtime status</code> 和对应 scope status 命令稳定 pull/query；该 surface 是必需的 durable 状态面，不得伪称主动通知。<code>qualified_windows_toast_v1</code> 等 push adapter 是可选 transport，只有 capability snapshot、operator opt-in 和 Q0/quick preflight 均有效时才可发送；失败只记录 transport outcome，不丢失或关闭 durable action，也不扩大 action scope。

Push 最多在 dedup key 首次出现、状态升级或 generation 变化时发送；重复 scheduler run 只更新 last_observed/count。Inbox/push 正文只含公开 ID、reason code、状态和唯一命令，不含 path、output、prompt、parameter 或 digest oracle。

## 15. Qualification Q0 与运行期 preflight

### 15.1 三类验证

| Class | Trigger | Scope | Admission effect |
|---|---|---|---|
| Full Q0 | 新 composition；binary/adapter/sandbox/permission/model-visible inventory、Git/Windows capability、canonicalization、persistence/schema/probe behavior 变化 | staged immutable installation + clean managed probe repos | 产生 Q(C,I,staged identity)，但不自行选择或准入 runtime |
| Quick preflight | 每次 drain、claim、continuation、Native maintenance exit | identity/config/auth/network denial/paths/clock/disk/ownership 的有界子集 | 阻断当前 scope，不替代 Full Q0 |
| Daily canary | B2/B3 每日首次 scheduled run | production activation 的独立临时 repo | 失败一次重试；再失败按原因 suspend platform/repo/template |

Full Q0 必须在 <code>versions/&lt;candidate&gt;</code> staged installation 上执行，使用其 pinned bootstrap/controller/Codex/Git/config/schema，而 <code>current.json</code> 仍指向旧版本。只有 Q、I 和 activation guards 均绿色后，才可组装 B 并执行第 3.3 节的 pointer CAS + immediate preflight。不得先激活再测试，也不得用 repo-side simulation 或 legacy runtime 结果代替。

<code>Q0TriggerPolicy.v1</code> 以旧/新 RuntimeCompositionManifest 的结构化 diff 决定验证范围：

- 新 adapter/provider/runtime engine、sandbox/token/permission 行为、model-visible tool inventory、Git object/ref capability、network/delivery protocol、Windows helper、canonicalization/persistence/schema/migration/probe或 unknown diff：必须 Implementation Acceptance + Full Q0。
- 同一已证明 ExecutionProfile envelope 内，单纯收窄 timeout、resource budget、approved path、gate subset 或模板参数范围，且 capability/adapter/effect protocol不变：可只做 scoped requalification、new Authorization 和 canary。
- Model/effort、tool version、feature/config key 即使 schema 不变，只要可能改变 agent-visible behavior，都执行 Full Q0；未知分类同样一律 Full Q0。

操作者、profile 或 CLI 不能覆盖 trigger classification；不能把所有变化一律跳过 Full Q0，也不能用一律 Full Q0 掩盖缺失的 scoped policy。

### 15.2 Full Q0 matrix

Full Q0 至少覆盖：

1. Binary/toolchain：absolute path、version、SHA-256、file/volume identity、owner/DACL、Authenticode policy、DLL search 和 before/after identity。
2. Codex config：strict-config、profile、<code>trust_level=untrusted</code>、project config/hooks/rules skip、AGENTS/skills discovery、feature catalog、model-visible tool inventory、ephemeral/history/logging disk diff，以及 Gate/Git <code>--include-managed-config</code> 生效证明。
3. Sandbox/auth：Codex parent/current SID与sandbox payload专用低权限SID/group的token角色分离、CodexSandboxStateBinding、<code>.sandbox</code> ACL/root identity、opaque <code>sandbox.log</code> deny-read/size/rotation/export-scan、sandbox child 对controller handles、<code>.sandbox-secrets</code> 与 current-user keyring/DPAPI deny-read；keyring-only login/refresh/generation、needs_auth 分类、Codex parent 最小 control-plane connectivity、secret-free evidence。不得假设 sandbox.log 字段 schema。
4. Permission/network：writer/gate/git allow/deny path matrix；provider network allow；task/tool/gate/git DNS/TCP/HTTP deny；任何 successful unauthorized egress 为全局安全硬失败。
5. Process isolation：case-insensitive unique empty-environment block、拒绝case alias和<code>=C:</code> hidden entry、attempt-local HOME/APPDATA/SQLite/TEMP/cache、safe DLL loading、no profile/login shell、command-line/overlay boundaries；writer/gate/Git/probe/recovery helper全部使用suspended atomic Job join、<code>PROC_THREAD_ATTRIBUTE_HANDLE_LIST</code>精确stdio继承、parent child-end及时关闭、pipe EOF和StageLaunchRecord execution barrier。
6. Windows objects：SDDL、mutex collision、Job limits、no-breakaway、kill-on-close、same-name zero-process fail-closed、PID creation-time validation、Authorization revoke/grant linearization。
7. Filesystem/resource：fixed local NTFS、no-replace、ReplaceFileW、FlushFileBuffers、power-loss probes、reparse/junction/symlink/hardlink escape、ACL drift、alias-aware 8.3 handle-identity enforcement、runtime-managed external evidence root与repo/common-dir/worktree/attempt roots不相交、WriteAccountingPolicy watcher/fallback/final audit、EmergencyDiskReserve preallocation/release/rebuild、limit+1 Job termination、disk reserve/disk_pressure 分流；HardWriteQuotaCapability 仅在启用时追加原子 deny bypass matrix。
8. Stream/adapter：valid JSONL、complete invalid line、normal-exit partial line、cancel/timeout partial buffer、UTF-8 boundaries、pipe backpressure、limit+1、event matrix、segment continuation 和 receipt six-condition invariant。
9. Gate/environment：offline dependency binding、fresh writable cache、no install/restore、absolute argv、timeout/kill/drain 和 report schema。
10. Git：config deny catalog、protected surface、controlled index、tree ordering、object framing、existing-object canonical verification、claim_epoch_seconds、unique parent/header order、create-worktree <code>logs/HEAD</code> cleanup、<code>--no-create-reflog</code>、index/HEAD/task-ref order、deterministic repeated commit。
11. Recovery：每个 writer marker barrier、controller crash、multi-fence adoption、Authorization continuation、artifact/outbox、object promotion、finalize/ref/evidence/remove 和 response-loss replay。
12. Operations：managed Native maintenance、emergency kill ordering、ownership cutover/rollback、backup/restore drill、suspended-only production restore anti-rollback和activation rollback。

每个 probe 有 versioned probe ID、input fixture hash、expected observation、scope 和 failure classification。Q0 report 保存白名单结构化结果和 hashes，不保存未知 stdout/stderr 正文或其 hash。

### 15.3 Failure scope 与 canary

- Binary、CLI、effective config、permission、sandbox、feature/tool inventory、Job atomicity、adapter framing或 successful unauthorized egress 异常：platform qualification -> incompatible，停止全部新 claim，退出 6。
- Provider 临时故障：availability -> unavailable，退出 5 并退避；凭据需要交互：auth -> needs_auth，全局停止 provider claim。
- Repo path/config/protected surface 异常：仅该 repo -> repo_requalification_required。
- Template gate、denied-network attempt 或新 mutation class：仅该 template -> suspended；successful egress 例外，升级全局。
- 单 attempt timeout/output/memory/disk budget failure：attempt failed/recovery，除非 enforcement 机制本身偏离 probe。

Daily canary 只使用 runtime-owned disposable repo 和无秘密 fixture；必须验证 allow/deny write、provider/tool network split、keyring refresh、trust isolation、Job kill、DLL/reparse/hardlink、stream limits、Git object 和 deterministic commit。Canary 永不引用真实任务参数或目标仓内容。

### 15.4 Capability evidence

官方文档定义允许声称的配置语义；pinned 本机 <code>--help</code>、config schema、binary inventory 和行为 probe 决定该 installation 是否兼容。<code>CapabilityAdapter.v1</code> 必须绑定官方 reference locator/date、help/schema hashes、probe IDs、config compiler generation 和 known removed/renamed keys。

任何未知 key、help/schema 与行为不一致、removed feature 复活或 model/tool/profile 漂移都禁止动态 fallback。修复必须产生新的 composition/profile/capability generation，并按 Q0TriggerPolicy 执行 Implementation Acceptance、Full/专项 Q0、repo/template qualification、Authorization 和 canary 的确定集合。

## 16. 重基线、实现、迁移与逐仓切换

### 16.1 总体依赖链

~~~text
v3.22 narrative candidate
-> P0A normative package closure
-> Baseline Approval
-> P0B Truth Reset
-> P0C Legacy Ownership Guard
-> P0D new runtime skeleton and acceptance harness
-> P1 implementation slices
-> Implementation Acceptance
-> Full Q0
-> P2 pilot vertical slice
-> P3 scheduled self-host
-> P4 real-repo qualification and cohort
-> P5 per-repo cutover and legacy retirement
~~~

任何后续阶段不能用“计划完成”代替上一门的机器证据。一个切片尽量不超过 5 个主要文件，但这是审查和可回滚目标，不是机械 gate；schema、fixture、migration 和 test 的配套文件不为凑数而合并。

### 16.2 P0A：规范包闭包

- 归档 v3.14、v3.16、v3.17、每份冲突 v3.18、精确 v3.19 和冻结的 v3.20，登记无 canonical hash 的 v3.15 withdrawn draft；完成双路径 hash 和 ReviewEvidenceIndex。
- 将本文的 Tier A/Tier B schema、catalog、完整 transition rows、examples、negative fixtures、migration specs 和 verifiers 实际落盘。
- 先对除最终 manifest instance 外的完整 package 运行一致性评审并冻结 <code>package_review_head</code>；随后一次性生成 BaselineManifest、关闭全部 hash/依赖并运行字节/canonicalization/catalog/transition/verifier，再 append manifest closure review。
- 只有 manifest closure review 无阻断项、<code>approval_review_head</code> 可证明继承 package head 时，才由独立治理动作生成 active BaselineApprovalRecord；批准者不得通过修改本文隐藏 waiver，安全硬门无 waiver。

### 16.3 P0B：Truth Reset

在 Baseline Approval 后，以一个原子、可回滚的文档/规划切片同步：

- 根 AGENTS、README、PRD、architecture、roadmap、plan、backlog、acceptance-and-gates、planning-status、selector/verifier 和 change-evidence index；
- active queue 从预批准的 <code>LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE</code> 改为 <code>MINIMUM-OPERATOR-COMMIT-ONLY-TRANSITION</code>；
- selector 首个结果固定为 <code>implement_legacy_guard_first</code>；
- 删除过期 supplemental token/旧 queue 硬编码；将 runtime_v2、Hermes/AgentBridge 写面和 snapshot 明确为 legacy/compat，而不是新 runtime 实现。

Truth Reset 只改变已批准的仓库计划真值，不创建新 runtime、迁移数据库或宣称 live。Verifier 必须执行真实 selector、schema 和文档 cross-reference tests，不能把整个旧 test suite 标为 gate_na。

### 16.4 P0C：Legacy Ownership Guard

- 实现 checked-in OwnershipRecord wire schema、canonical repo identity、named mutex/SDDL、generation CAS 和 legacy adapter。
- Guard 必须覆盖 legacy claim、lease、worktree、executor/writer、repo mutation、Git object/ref/commit、closeout 和 cleanup 的每个写入口；不能只包 scheduler 入口。
- 枚举当前 legacy 管理 repo，以 no-replace 注册 <code>owner=legacy</code>；identity/collision/unknown active process 有歧义时停止而不是猜测。
- Legacy/new cross-conformance、mutex collision、crash takeover、cutover/rollback drill 未绿前，新 runtime 的 repo claim 保持硬阻断。
- 新旧数据库永不双写。Legacy DB 继续只是真实 legacy task 的真源；ownership registry 是唯一共享 wire contract。

### 16.5 P0D 与 P1：新 runtime 实现

P0D 先建立 <code>runtime/local-ai-runtime</code> package、offline build、contracts CLI、empty state root、migration harness 和 no-side-effect doctor。随后 P1 按可执行 vertical slices 推进：

1. Contracts/canonicalization/reason catalog/transition verifier。
2. SQLite storage、migrations、family/resubmission、lease/fence/adoption/continuation/effect grant。
3. Installer/activation/backup、toolchain/environment/sandbox state/write-accounting monitor、optional hard-quota capability、emergency reserve、ownership/legacy conformance。
4. Qualification/Authorization/Codex overlay/auth/permission/Q0 probes。
5. Writer/StageJob/marker/stream/journal/artifact/recovery。
6. Gate runner、secret scan、deterministic Git object/no-reflog finalize/ref/evidence/cleanup。
7. CLI/operator actions/managed Native/scheduler/cutover/evaluation。

每片必须从 schema 到 command 到 persistence 到 crash/replay test 闭环，并只回滚本片。禁止先接真实 writer 再补 fence、marker、Git 或 evidence。

在 sandbox/overlay/CapabilityAdapter 完成后，必须运行 <code>adapter_no_write_smoke_v1</code>：只使用 runtime-owned disposable repo、无真实 task、无 writer execution grant，验证 pinned Codex <code>exec --json --ephemeral --output-schema</code> framing、effective config、tool inventory、network/path deny 和零 worktree/common-store mutation。它不是 live claim、Q0 或 Implementation Acceptance。

在 deterministic Git + external evidence closeout 完成后，必须运行 <code>fixture_closeout_rehearsal_v1</code>：无 provider、无 model、无 live Batch claim，以 checked-in fixture mutation 驱动 GateGraph、canonical payload、<code>hash-object</code>/cat-file read-back、attempt-local objects、index/HEAD/ref/evidence/remove 的完整 fenced chain。Rehearsal 只写 disposable fixture repo，不得创建 production task ref，也不能替代真实 writer、Implementation Acceptance 或 Full Q0。

### 16.6 P2-P4：有限自治扩展

- P2：Full Q0 后，在低风险 self-host repo 由操作者显式提交一个 B1 commit-only task；完整生成 task ref/evidence/cleanup，人工验证但不让 runtime merge/push。
- P3：至少 5 个 B2 scheduled self-host writer tasks，包含一次 auth park、一次 controller crash recovery 和一次 response-loss replay；无未恢复终态后才继续。
- P4：资格化至少两个真实目标 repo，完成第 19 节定义的 30-task cohort 和配对效率评估；每个 repo 独立 Authorization/canary，不因另一个 repo 成功扩大权限。
- B3 portfolio scheduling 只有 P4 全绿且 capacity 仍为 1 时才可激活。

### 16.7 P5：逐仓 cutover、rollback 与退休

每个 repo 的 cutover 固定为：

~~~text
durable drain request
-> stop legacy and new claims for repo
-> prove zero live/closing/recovery process and action
-> quiescent state/evidence backup
-> acquire global then repo mutex
-> verify ownership identity and expected legacy generation
-> write CutoverRecord intent
-> CAS ownership legacy/guarded_legacy -> batch
-> quick qualification and canary
-> terminal CutoverRecord
-> release repo scheduling
~~~

- 不迁移或复制 legacy task 到新 DB；cutover 后只让新 submission 进入新 runtime。Legacy terminal evidence 保持原位只读。
- Cutover 响应丢失必须先按 ownership generation/CutoverRecord 重放；禁止再次递增或创建第二 owner。
- Rollback 只在 repo 零 active/closing/recovery、所有新 task ref/evidence terminal、两个 runtime schema 都能保护现存 runtime-owned refs 时执行；CAS <code>batch -> guarded_legacy</code>，不删除新 commit/ref/evidence。
- Legacy 在 guarded_legacy 下必须拒绝修改或删除 <code>refs/heads/codex/batch/*</code> 和新 runtime worktree admin records；发现未知记录进入 ownership repair。
- Activation rollback 与 repo ownership rollback 是两个独立动作：前者切 installation generation，后者切 repo owner，不能用一个命令暗含另一个。
- 全部目标 repo cutover、legacy 零 active/closing、rollback drill 绿色后，legacy DB/write surface 进入 read-only。连续 30 天零 legacy 调用后才移除 legacy writer；compat reader、历史 evidence、ownership/cutover records 和 task refs 永久只读保留。

## 17. 实现门禁、运行门禁与 runbook

### 17.1 新包开发门禁

P0D 创建新包后，仓库根目录固定按以下顺序运行，不得用 setup/install 代替验证：

~~~powershell
uv lock --check --offline --project ./runtime/local-ai-runtime
uv build --offline --project ./runtime/local-ai-runtime ./runtime/local-ai-runtime
uv run --locked --offline --project ./runtime/local-ai-runtime python -m pytest
uv run --locked --offline --project ./runtime/local-ai-runtime python -m local_ai_runtime contracts verify
uv run --locked --offline --project ./runtime/local-ai-runtime ruff check ./runtime/local-ai-runtime
uv run --locked --offline --project ./runtime/local-ai-runtime pyright --project ./runtime/local-ai-runtime
python scripts/verify-planning-status.py
python scripts/select-next-work.py
git diff --check
~~~

顺序映射为：supply-chain lock check；build；test；contract/invariant；ruff/pyright/planning/selector/diff hotspot。<code>uv lock --check --offline</code> 只验证现有 lock 与 project metadata，不更新 lock 或访问网络；后续 <code>--locked</code> 禁止隐式 lock 变化。<code>uv build</code> 的 dist 输出必须由 checked-in ignore/cleanup policy 管理，并由 verifier 证明未覆盖 tracked file。触及 legacy ownership guard、wire schema 或 compat adapter 时，在新包 test 后补跑：

~~~powershell
uv run --project ./runtime/host-orchestrator python -m pytest
~~~

触及 repository-wide governance 时，再运行当前 release-style preflight：

~~~powershell
pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit
~~~

- Offline 是硬门。缺少 pinned dependency 不是跳过理由，而是 environment preparation 阻断。
- Ruff、Pyright、pytest、build backend 和 contract verifier 都必须来自 <code>uv.lock</code>；禁止从 PATH 偶然选择全局工具。
- 真实命令、exit code、关键白名单报告、Git diff 和 gate generation 写入 repo-level change evidence；不得保存工具未知输出正文/hash。
- 纯规范切片可以对不存在的新包 build/test 记录 <code>gate_na</code>，但必须给 reason、替代验证、evidence 和到期点；一旦 P0D 创建包，N/A 自动失效。

### 17.2 Runtime GatePolicy

每个 TaskTemplate 的 <code>GatePolicy.v1</code> 必须逐 gate 固定：

~~~text
gate_id and schema generation
absolute executable identity and argv array
logical cwd and resolved final identity policy
empty-environment additions and digest
QualifiedEnvironmentBinding ID
permission profile=batch-gate
offline/network-deny expectation
timeout, stdout/stderr/report limits
success exit-code set and report schema
required ordering and fail-fast behavior
secret-scan policy before evidence
~~~

Gate 不得调用 shell、package manager install/restore、repo-local executable、unqualified plugin 或动态 discovery。确需 PowerShell/Python bootstrap 时使用 ToolchainManifest 中的绝对 PowerShell <code>-NoProfile -NonInteractive</code> 或 Python <code>-I -s -E</code>，并以固定 script OID/hash 作为 argv 输入。

初始 self-host template 必须实际执行 offline pytest、contracts verifier、ruff、pyright、planning verifier、selector 和 <code>git diff --check</code>。GatePolicy 不能写省略号、自由命令字符串或“运行全部测试”；每个 argv 和 expected report 都是 schema data。

### 17.3 Runbook 契约

以下 runbook 必须在 Implementation Acceptance 前实际落盘：

1. needs_auth/login/logout/keyring generation；
2. needs_environment/register/requalify/retire、WriteAccountingPolicy drift 与 optional HardWriteQuotaCapability requalification；
3. platform unavailable/suspended/incompatible、Codex sandbox setup 和 disk_pressure；
4. repo/template requalification 与 Authorization revoke/activate；
5. recovery_pending/recovery_required/reconcile_required/cleanup_required；
6. ownership repair 和 same-name Job handle still open；
7. managed Native maintenance enter/exit/repair；
8. emergency kill-current；
9. activation rollback；
10. quiescent backup/verify/restore drill、suspended-only production restore与anti-rollback recovery；
11. repo cutover/rollback；
12. model/profile canary rollback；
13. opaque sandbox diagnostic export、secret-scan rejection、rotation failure 和 <code>sandbox_state_requalification_required</code>。

每份 runbook 必须包含 exact CLI argv、允许的 token/session、precondition guard、expected state hash、可观察证据、stop condition、响应丢失重放方式、只撤销本动作的 rollback，以及“不得做什么”。Runbook 不得要求直接编辑 SQLite/ownership JSON、删除 Job/ref/worktree/quarantine、换 named-object 名称、reset --hard 或跳过 verifier。

Interactive repair 可以定位持有 Job handle 的进程；只有在 operator 明确选择 emergency action、并证明目标 PID/executable/creation time 属于 runtime 时才可终止。无法证明时只能等待持有者退出或重启宿主，之后在 attempt mutex 下重新证明同名 object 已消失。

### 17.4 Backup 与 restore gate

Backup 按 canonical repo identity 排序取得 global capacity、registry mutex 和所有被备份 terminal state 引用的 repo mutex。要求：零 active lease、零 nonterminal/recovery attempt、零 pending outbox、全部 referenced segment/quarantine sealed。

Backup 仅包含 controller DB、migration/activation/policy manifests、ownership、terminal external evidence、terminal record引用的encrypted sealed quarantine，以及恢复这些条目所必需的DPAPI-wrapped QuarantineKeyEnvelope/RuntimeIntegrityKeyEnvelope；不包含明文key、keyring/auth material、immutable environment bytes、worktree、ordinary quarantine、live spool 或 raw output。

Manifest 逐文件记录 relative path、size、content SHA-256、ACL projection、schema/generation、key-envelope dependency和restore disposition。Restore drill 只能恢复到新的隔离 root，执行same-SID envelope unwrap、migration/read-only integrity/evidence/ownership verification，不覆盖 production root、不注册 scheduler、不打开真实 repo。

Backup发布、post-activity与restore固定为 <code>already suspended -> manifest seal -> publish eligible head -> marker-before-any-later-mutation OR restore-intent consuming branch -> restoring CAS -> verified restore -> consumed CAS</code>。Crash injection必须覆盖marker的before-write/after-write-before-flush/after-flush-before-state-mutation、restore intent response loss和restoring/consumed CAS；任一窗口只能得到保守stale、同intent继续或完整consumed，不能复活已revoke Authorization、遗忘task-ref history或产生第二restore。生产restore要求platform从backup前至restore-start始终保持同一suspended control generation，并创建独立OperatorAction/OperatorWorkSession；期间任何resume、marker存在、head/manifest不一致、key envelope不可验证或backup并非唯一eligible generation时无override路径。

## 18. 验证策略与故障注入

### 18.1 Contract 与 schema tests

Contract suite 至少覆盖：

- 规范字节：UTF-8/no-BOM/LF/NFC/terminal-LF、全部非 LF Cc、未批准 Cf、bidi/zero-width/BOM/noncharacter、trailing-space；
- Canonical JSON：重复 key、integer bounds、object order、preserved arrays、set_semantics unique sort key、domain separation、所有 string field 的 Unicode category allowlist；
- Git/Windows path：raw Git spelling、NFC validation、ADS/device/reserved/case collision、8.3 short/long alias、policy_query_denied、alias-bypass与权限/状态漂移、no-follow final identity、reparse/hardlink；
- Qualification union：present/absent/expanded/blocked、negative discovery、ancestor dirtiness、resolver/catalog hash；
- Closed parameters：type/range/count/64 KiB、secret scan、no execution-plane interpolation；
- Submission family：bounded parse、公开 grammar、canonicalize、volatile lookup、authorized existing replay、absent-only current membership/secret-scan/admission、transaction recheck 的严格顺序；secret catalog 漂移后仍返回原 root；失败新输入零family/零oracle；另覆盖 atomic successor、response loss、v1/v2 resolution-family uniqueness和historical-ref prohibition；
- Authorization/execution authority：reusable scope、sensitive-set change invalidation、ordinary base change non-invalidation、expiry/revoke/checkpoint continuation、revoke/root-grant linearization、process grant不跨fence、controller adoption继承同一root grant、derived child-process grant闭包、safety-only effect不依赖Authorization且不能扩大副作用，以及terminal result引用current head；
- Process/environment/resource：writer和每类StageJob suspended atomic join、JOB_LIST+HANDLE_LIST、只继承精确stdio child ends、无ambient/sensitive handle、parent close/EOF、execution-commit barrier、previous Job terminal proof、execution-authority union；Windows environment key大小写alias、hidden drive entry、NUL、排序和UTF-16边界；WriteAccountingSnapshot、EmergencyDiskReserve lifecycle、watcher overflow/fallback、sparse/mmap/link/rename/ADS final audit、limit+1 kill与disk_pressure分流；启用 HardWriteQuotaCapability 时才测原子 quota bypass；
- Evidence/backup boundary：external evidence root必须由runtime管理并与repo/common-dir/worktree/attempt/controller敏感roots无identity/ancestry/alias overlap；QuarantineKeyEnvelope与RuntimeIntegrityKeyEnvelope purpose隔离、same-SID unwrap和缺失/错代失败；post-backup marker-before-mutation、stale snapshot拒绝、restore intent response-loss和single-consumption；
- Sandbox diagnostic：opaque sandbox.log 可含 arbitrary/invalid UTF-8/task-like bytes但不得进入普通 evidence/hash；task进程 deny-read；rotation/export 必须走 bounded procedure、OperatorWorkSession和secret scan；unknown opaque entry只触发有作用域的requalification，除非安全边界被绕过；
- Complete state tables、GuardCatalog precedence/DAG、unknown operator combination exit 2、runtime adapter violation exit 6；
- Schema/example/negative-fixture round trip、migration forward/rollback compatibility 和 reason-code completeness。

Verifier 必须枚举 policy 中的全部 state、event、operation、resolution、guard、effect 和 reason code；声明但不可达、可达但无 terminal path、跨域 guard cycle 或 handler 中未声明 branch 都失败。

### 18.2 At-most-once 与 response-loss invariants

必须机械证明：

~~~text
per task generation: exactly one stable writer_effect_id and writer_execution_committed count <= 1
per attempt: writer_launch_id count <= 1 and writer process identity count <= 1
pre-commit writer retry: only a fresh attempt/launch after prior suspended-process terminal proof
per stage_run_id: stage_execution_committed count <= 1 and process identity count <= 1
per attempt/effect identity: AuthorizationExecutionGrant count <= 1 or SafetyOnlyExecutionRecord count <= 1, never both
per inherited process grant: exactly one parent action grant and current fenced head, with no writer/gate use
per adopted controller effect: every adoption/result references the same root execution authority and immutable intent
per fenced action: immutable terminal result count <= 1
per action head: one non-branching adoption successor
per submission source: resubmission successor count <= 1
per root/generation: task count <= 1
per task: successful task-ref publication identity count <= 1
per artifact logical name: accepted final payload identity count <= 1
per backup generation: production restore intent/consumption count <= 1 and zero restore after post-backup activity
~~~

每个 externally visible command 都要在“事务提交后、响应发送前”注入 crash/connection loss。重放必须先读取既有 identity/result，再评估只适用于首次创建的 current guards。Authorization 后来过期、source 后来非 current 或 caller 重复点击，不能把已存在成功结果误报为新失败；读取权限仍需复核。

SQLite unique/foreign/check constraints、BEGIN IMMEDIATE 和 OS no-replace/CAS 共同承担证明。只靠 Python <code>if not exists</code> 或日志搜索不算 at-most-once。

### 18.3 Crash matrix

Crash injection 至少在下列每个 durable step 的 before、after-write-before-flush、after-flush-before-DB、after-DB-before-response 四个窗口执行：

1. install/current activation replace 与 ownership replace；
2. claim、lease、fence takeover、capacity disposition；
3. DB launch intent、CREATE_NEW marker、writer/StageJob spawned_suspended PID、JOB_LIST/HANDLE_LIST construction、parent child-handle close、AuthorizationExecutionGrant/SafetyOnlyExecutionRecord、derived process authority、execution-committed barriers、ResumeThread result、pipe EOF、process exit；
4. same-name Job inspect/close/recreate 和 emergency terminate intent；
5. pipe read、partial line、event append、segment flush、DB cursor、seal/continuation；
6. gate/Git/probe/recovery-helper StageLaunchRecord、old Job terminal proof、intent/process/report/terminal result；
7. artifact temp/intent/no-replace/read-back/outbox terminal；
8. adoption across at least three fences 和 Authorization continuation；
9. GitObjectPlan、claim_epoch_seconds、object materialization/set seal、promotion/existing-object verify/reachability、write-accounting snapshot/limit/recovery、emergency-reserve release/rebuild，以及optional hard-quota reservation；
10. create-worktree reflog cleanup、index replace、HEAD no-reflog CAS、task-ref no-reflog CAS、evidence publish、worktree removal；
11. resubmission transaction、maintenance begin/end、cutover/rollback；
12. backup manifest/file/key-envelope copy/terminal publish、eligible head、post-activity marker-before-mutation、restore intent/restoring/consumed CAS 和 restore-drill/production-restore verification。

每次恢复只能产生以下之一：同一确定结果、明确 terminal failure、durable park/OperatorAction。不得出现第二 writer、分叉 action、冲突 object/ref、未记账 write、删除未知文件或自动选择新 base。

### 18.4 Boundary、security 与 conformance

- 每个 limit 运行 limit-1/limit/limit+1；每个 path rule 同时测 Git spelling、Windows collision key、长路径、UTF-8/UTF-16 length 和 CreateProcess total length。
- Secret fixtures 包括高熵 token、低熵 credential、路径/文件名秘密、内容相同不同 zlib object、stdout/stderr、JSON field、artifact、quarantine 和 failed scan。Public evidence 必须不存在原文、普通 digest 或可验证 oracle。
- Permission matrix 对每个 profile 做 allow read/write/execute、deny read/write/network、project config/hooks/rules、AGENTS/skills 和 Git admin tests。
- Legacy/new conformance 使用相同 repo identity、mutex name、SDDL、ownership generation 和 task-ref protection fixtures；任一实现产生不同 bytes/name/decision 即阻断 cutover。
- Git determinism 在同一 manifest 上至少独立运行三次，要求 plan/tree/commit OID 完全相同；再改变普通 source、sensitive input、claim time、parameter 和 policy，分别验证应变与不应变字段。
- Windows Q0 测试必须使用真实 CreateProcessW、Job、mutex、NTFS、ACL、reparse、hardlink 和 pinned Codex/Git；mock 只证明 unit logic，不可替代 Implementation Acceptance/Q0。

### 18.5 Evidence acceptance

每个 gate/test/probe report 都必须能从 immutable input manifest、checked-in verifier 和 external evidence root 独立复算。EvidenceIndex/CloseoutBundle verifier 至少检查 schema、hash chain、Authorization checkpoint、ExecutionReceipt、Git plan/object/ref、gate reports、operator actions、cleanup disposition 和 sensitive-field allowlist。

以下不能作为接受证据：repo-side 自报成功、模型 summary、raw CLI output、legacy projection、只跑 mock、只跑 probe 不跑 verifier、被修改的 terminal row、无 generation 的截图，或因测试难而标记 gate_na。

## 19. 验收、指标、成本、支持范围与最终裁决

### 19.1 三层验收

Baseline Approval 要求：

- v3.22 本文及全部规范性 schema/catalog/table/example/fixture/verifier 实际落盘；
- BaselineManifest hash 闭合，谱系归档、package_review_head、manifest closure review 和 approval_review_head 的非循环后继关系一致；
- 无 placeholder、不完整 row、隐含旧版本依赖或未裁决冲突；
- 独立一致性评审无 P0/P1 阻断，并创建未撤销的 active approval。

它不要求运行时代码已完成，也不得据此宣称 Batch 可运行。

Implementation Acceptance 要求：

- P0B-P1 代码、migrations、CLI、runbooks、legacy guard/conformance、backup/restore 和 rollback 已实现；
- 第 17 节全部固定门禁绿色，第 18 节 contract/crash/boundary/at-most-once 证据绿色；
- 新包不 import/双写 legacy，Truth Reset 与实际 selector/queue 一致；
- staged installation 可重复安装和 activation rollback。

它仍不允许 P2 writer。P2 Admission 还必须让当前 staged immutable installation 的 Full Q0 绿色，完成 RuntimeActivationBundle 的一次 pointer CAS 和 immediate quick preflight，并形成 terminal <code>activated_and_preflight_passed</code> ActiveRuntimeIdentity。

### 19.2 安全硬门与可靠性 cohort

以下计数必须恒为 0：

~~~text
unauthorized writes
declared-or-detected sensitive information disclosures
duplicate writer execution commits
conflicting Git objects/commits/refs
incorrect cleanup or deletion
unaccounted Git/controller side effects
successful unauthorized egress
~~~

任何安全硬门失败都不接受 waiver。暂停范围由 GuardCatalog 决定；不能为了降低失败率把普通资源失败升级为 platform failure，也不能为了保持调度把 platform 漂移降为 task failure。

30-task live cohort 的 <code>evidence_scope=declared_profile_pilot</code>，只证明该 ActiveRuntimeIdentity、TaskFamily、repo cohort 和观察窗口内的安全、可靠性、恢复和无人值守率，不证明一般最优、跨 profile 泛化或未来 capability：

- 固定观察窗口和 admission rules；最多 5 个 probe-only，至少 25 个 commit-ready；
- self-host 与两个真实目标 repo 各至少 5 个实际 writer tasks；
- 所有 submitted generation，包括 failed/cancelled/recovered，均进入分母，禁止事后剔除困难任务；
- unattended commit-ready rate 至少 80%；需要人工 action 的 task family 不超过 20%；
- mandatory gates、evidence verify、backup restore drill 和指定 recovery drill 通过率 100%；
- 窗口结束时零 live/unknown/recovery_required/reconcile_required/cleanup_required、零 pending outbox 和零未处理 OperatorAction。

Probe-only 不计 commit-ready 成功，也不能稀释人工介入分母。由故意 crash drill 触发且完全按 runbook 自动恢复的任务仍算无人值守；操作者执行命令则计人工介入和分钟。

### 19.3 最少人工、效率与可归属成本

效率使用至少 12 个严格配对 case，对比当前 human-controlled Native baseline 与候选 Batch：

- 同一 immutable repo snapshot、TaskSpec/controller data、gate policy、qualification assumption 和任务分布；
- 固定 seed、counterbalanced 执行顺序；每个声明 template family 至少 3 个 case；
- 失败、取消、恢复和维护不能从候选窗口删除；两边都必须达到相同 commit-ready acceptance。

核心公式固定为：

~~~text
net_operator_minutes_per_success =
  window 内 submission、monitoring、auth、qualification、failure、cancel、recovery、
  template maintenance 和 runtime maintenance 的 operator active minutes 总和
  / commit-ready successes
~~~

OperatorWorkSession 以活动区间计量；重叠区间只计一次。纯机器等待、初始产品研发和与本 cohort 无关的维护单列，不进入分子。人工查看但未执行动作仍计 monitoring；失败任务人工进入分子。分母为 0 时指标为 infinity。

通过阈值为 <code>net_operator_minutes_per_success</code> 至少下降 50%，且 <code>commit-ready successes/operator-hour</code> 提高至少 50%或 P50 admission-to-commit-ready 周期下降至少 30%。Safety/reliability 未过时，效率改善无效。

可归属成本另报 controller/Codex/gate CPU time、peak committed memory、disk byte-hours、provider usage、artifact/evidence bytes 和 operator minutes。无法从 provider 得到可靠 token/价格时标记 unavailable，不用估算值驱动 profile promotion。成本只在安全、人工和可靠性之后优化。

### 19.4 Model/profile canary 与质量反馈

首次 Q0、P2、P3 和 30-task cohort 固定 <code>@openai/codex 0.144.1 + gpt-5.6-sol/high</code>，作为首个安全基线，不声称 high 永久最优。P2/P3 之后可按 EvaluationProfile 对同 model 的 medium/high 做严格配对；任何结果只用于创建候选 ExecutionProfile，不能运行时动态调整 effort。未来 binary/model/effort/profile/permission/feature/tool/adapter 候选都创建新 generation，并按 Q0TriggerPolicy 要求：

- 每 template 至少 12 个配对 cases，每 case/config 至少 3 次；
- 通过 Full Q0 后执行 10-task canary；
- 任一安全/gate失败、新 failure type、新人工 intervention 或 candidate-attributable success-rate 下降，立即停止 candidate claim。

回滚必须 CAS 到仍安装、未撤销、qualification/Authorization 仍有效的旧 generation；否则 platform/template suspended。禁止在同一 task 或 runtime failure 后动态 fallback 到旧 model/profile。

Commit-ready 不是长期质量真值。未来 <code>DownstreamOutcomeRecord</code> 可作为非 0.2 Tier A 阻断的演进契约，绑定 ActiveRuntimeIdentity、task commit、可验证 final integration commit lineage、source identity、观察窗口、human review disposition、merge/reject、后续 CI、revert 和 defect evidence locator。没有下游反馈必须记为 <code>censored|unknown</code>，不能算 pass；TaskFamily/profile promotion 不能只按 commit-ready 自循环优化。0.2 只预留该演进语义，不实现组织集成或自动读取 remote CI。

### 19.5 支持与不支持范围

0.2 只支持：

- Windows 上当前用户、固定本地 NTFS volume；
- standard SHA-1/files Git repo、非 bare、唯一 local_base_ref；
- 无 active submodule/LFS filter/external Git driver；
- checked-in closed template、pinned offline dependency environment；
- local commit/task ref/external evidence，不触碰 remote。

<code>qualified_git_repo_v1</code> 是 0.2 唯一 authority anchor，不是产品永久上限。未来受控 local workspace authority 必须通过新的 capability generation、identity/EffectPlan/delivery contracts、Implementation Acceptance 和 Full Q0 引入；在此之前无 Git workspace 仍 unsupported。

不支持 SHA-256 object format、reftable、network/removable/cloud-synced worktree、remote/fetch/push、historical detached base、automatic merge/ref deletion、multi-writer、subagent Batch、controller/gate runtime dependency install、GUI/production/database/credential mutation 和 unattended Native。发现 unsupported condition 必须在 prepare/qualification 阶段退出 3 或 6，不能半程适配。跨 repo 多 writer 也不是 CapacityProfile 开关：它属于 successor Architecture Epoch，必须新增 concurrency/resource/auth/backup/maintenance/recovery protocol；同 repo 并行或多操作者/多信任域属于更晚独立 epoch。

### 19.6 官方依据与当前仓库事实

规范性行为只依据批准时归档的官方文档、本机 pinned help/schema 和 Q0 probe。初始参考至少包括：

- [Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference#configtoml)
- [Permissions](https://learn.chatgpt.com/docs/permissions#define-and-select-a-profile)
- [Shell environment policy](https://learn.chatgpt.com/docs/config-file/config-advanced#shell-environment-policy)
- [AGENTS discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md#how-codex-discovers-guidance)
- [Skills locations](https://learn.chatgpt.com/docs/build-skills#where-to-save-skills)
- [Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox)
- [Git update-ref](https://git-scm.com/docs/git-update-ref)
- [Git core.logAllRefUpdates](https://git-scm.com/docs/git-config#Documentation/git-config.txt-corelogAllRefUpdates)
- [Microsoft: Short vs. Long Names](https://learn.microsoft.com/windows/win32/fileio/naming-a-file#short-vs-long-names)
- [Microsoft: UpdateProcThreadAttribute](https://learn.microsoft.com/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute)
- [Microsoft: CreateProcess environment block](https://learn.microsoft.com/windows/win32/procthread/changing-environment-variables)
- [Microsoft: Data Protection API](https://learn.microsoft.com/windows/win32/secauthn/data-protection)
- [Microsoft: Disk Quota Limits](https://learn.microsoft.com/windows/win32/fileio/disk-quota-limits)
- [Microsoft: Sparse Files and Disk Quota](https://learn.microsoft.com/windows/win32/fileio/sparse-files-and-disk-quota)
- [Microsoft: FSRM Quota Management](https://learn.microsoft.com/windows-server/storage/fsrm/quota-management)

文档 URL 不是永久能力证明；BaselineManifest 必须归档抓取时间、content hash、适用 binary generation 和本机行为 probe。社区项目、旧对话、模型记忆和评审正文只能提供设计线索。

本文冻结时的仓库事实与后续状态边界是：

- 当前可信内核为 <code>runtime/host-orchestrator</code>；<code>runtime/local-ai-runtime</code> 尚不存在；
- active queue 是 <code>LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE</code>；
- v3.17 与两份冲突 v3.18 源字节已经归档并双路径验证；v3.21 已以 158,485 bytes 和 SHA-256 <code>1BFB5CD2C92C036804A6005D5B36CDD5ACC6BEDC4D6BF4070CCFB7A70CE063FB</code> 冻结为 superseded candidate；
- 本文与 v3.22-bound BaselineLineage 落盘后，preapproval inventory 应如实报告 15 required / 2 present / 13 missing，approval inactive、Truth Reset/implementation/P2 均未开始；selector 的唯一 ready work item 应为 <code>LAR-P0A-002 / close_baseline_normative_package_first</code>；
- 上述动态 package/task 状态不嵌入本文 hash 继续更新；后续变化只进入 stable entry、planning status、inventory、machine work items 和 evidence，并受各自 verifier 约束；
- 本文落盘不构成 Truth Reset、Baseline Approval、Implementation Acceptance、Full Q0 或 live acceptance。

### 19.7 最终裁决

本文的决策状态是 <code>candidate / Request changes until normative package closure</code>。总体架构讨论已收口；下一步是从 <code>LAR-P0A-002</code> 开始完成 P0A 的 schema/catalog/transition/example/fixture/verifier 多文件规范包并做一致性评审。只有受控 external operator action 创建的 active BaselineApprovalRecord 存在且未撤销，才允许执行 Truth Reset 和实现；只有 Implementation Acceptance、staged Full Q0、activation pointer CAS 和 immediate preflight 共同形成 ActiveRuntimeIdentity，才允许创建第一个 P2 writer task。
