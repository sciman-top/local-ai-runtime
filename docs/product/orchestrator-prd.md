# Local AI Runtime 0.2 PRD

## 1. 文档状态

- Product baseline：`local-ai-runtime-0.2-v3.24`
- 当前状态：`baseline_candidate`
- 当前阻断：`baseline_approval`
- 产品方向：`Unified Native + Batch` 的 Windows-local single-operator general-purpose governed AI development execution platform
- 优化目标：安全与副作用正确性硬门下的 `minimum-operator`、低人工、可预测、可恢复的开发吞吐；Native 快路径优化交互延迟，Batch 优化可恢复的无人值守交付，不承诺高速并发

本文是 v3.24 的产品投影，不补写规范语义。字段、状态、哈希、崩溃窗口和安全边界以候选正文及批准后的 normative package 为准。v3.24 narrative、独立 versioned artifacts 与最终 immutable BaselineManifest 是三个层次；正文和 lineage 完整不代表 package 已闭合。v3.23 candidate/package/plan 是精确 superseded inputs，不能被当作当前实现要求。当前 package 为 `6/15 present, 9 non-present`，下一项是 `LAR-P0A-004 / ProductContract.v2`。

## 2. 问题与机会

本地 AI 编码目前有两个互补需求：

1. 人需要处理模糊、高风险、交互式、GUI、凭据、远端和不可逆任务。
2. 大量边界明确、低风险、重复的 repo-local 工作可以无人值守完成，但必须可证明地限制写入、避免重复 writer、产生 deterministic commit，并把异常收口为少量明确人工动作。

单纯增加 agent 自治不能解决副作用归属、崩溃恢复、授权延续、Git object publication 和证据泄漏问题。产品必须把决策面与执行面分开，把自然语言自由度留在受控 Native，把 Batch 限定为已批准模板和机械合同。

## 3. 目标用户

- 单机 Windows 开发者：希望夜间或空闲时批量完成低风险仓库任务。
- Runtime operator：负责安装、login、qualification、Authorization、maintenance、cutover、rollback 和 recovery。
- Template owner：把重复需求收敛为封闭参数的 `TaskTemplate`，维护 gates 和 canary。
- Reviewer/integrator：检查本地 commit 和 evidence，决定 merge/push。
- Runtime engineer：按机器任务清单实现、验证和演进 runtime。

## 4. 产品终态

长期范围是 Windows 本机、单操作者信任域内，以受资格化 repo 或后继受控 workspace authority 为锚的开发执行平台。它承载代码、文档、构建、测试、静态检查、Git、制品和本地开发工具工作流；不承载跨平台、多租户、云集群、组织级 RBAC/计费或通用桌面自动化。Epoch 1/v0.2 只实现 `qualified_git_repo_v1`、单 SQLite authority、全局 capacity=1 和一个 Codex agent runtime。产品承诺是低人工、可预测、可恢复的开发吞吐：Native 通过更少等待、精简上下文和低交互延迟提升体验；单 writer Batch 通过确定性本地 commit、恢复和证据提高可预测性，而不是作为高吞吐并发系统。

### 4.1 Codex Native

- **Native Direct**：明确的一次性交互任务；允许操作者实时判断，不继承 Batch receipt/fence。
- **Native Spec**：最多询问三个关键问题，输出 decision-complete `TaskSpec`；不自动执行。
- **Native Program**：仅在至少两个独立写集合且集成顺序已固定时使用原生 subagents/worktrees；人工集成，不冒充 Batch 的 at-most-once 或 commit-only 证据。
- **Managed Native launcher**：与 Batch 共存时必须走耐久 maintenance drain、repo mutex 和 requalification；裸 Codex/Git 写操作属于 unsupported external Native。

### 4.2 Deterministic Commit-Only Batch

Batch 只接受四字段 `BatchSubmission`：repo、template、closed parameters、expected base commit。运行前必须具备：

- 已批准的 `TaskTemplate`；
- repo/template qualification；
- immutable environment/toolchain binding；
- 当前 generation 的 Authorization；
- 全局单 writer capacity；
- ownership、fence、attempt-local writable roots 和 quick preflight。

唯一交付是本地 deterministic commit 和 `refs/heads/codex/batch/<task_uuid>-a<attempt_no>`。用户负责最终审查、集成、merge 和 push。

### 4.3 Python Policy/Evidence Kernel

可信 controller 负责 canonicalization、qualification、Authorization、state/guard、Job、fencing、journal、artifact、Git object、evidence、backup、scheduler 和 operator action。模型输出永远不是磁盘/Git事实真源。

目标源码布局是关闭集合：`approved_root_files=["__init__.py","__main__.py"]`；`approved_subpackages=["contracts","kernel","qualification","storage","execution","recovery","git_local","operations","compat"]`；`required_source_owners` 把两个 bootstrap 文件和九个子包 marker 各绑定到唯一任务。`__main__.py` 仅转发稳定 contracts-verifier CLI；包根不得新增 installer、activation、CLI、evidence、commands 或其他功能模块。安装、激活、CLI、Batch、doctor、scheduler、managed Native 和 evaluation 的应用编排统一归 `operations`，证据/Artifact 持久化归 `storage`。

稳定内核长期负责 authority、task/attempt/generation、lease/fence/CAS、qualification/Authorization、operator action、单 writer scheduling、recovery、evidence、secret handling、backup/migration/rollback 和 effect reconcile。Codex CLI/SDK execution interface、App Server client protocol、managed Worktree workspace isolation、Automations scheduling、model/effort、Windows sandbox、Git format、toolchain 和 gate 都是版本化 capability/profile 输入，不是可在运行中猜测兼容的插件。

### 4.4 Legacy compatibility

Hermes、AgentBridge、现有 `host-orchestrator`、旧 DB 和历史 evidence 先受 ownership guard 保护，再逐仓 cutover。最终只保留只读 compat reader、历史 evidence 和 task refs；不双写数据库。

### 4.5 声明式工作与演进

- `WorkDefinition` 固定任务目标、封闭参数、允许 effect 和完成条件；`TaskFamily` 版本化同类工作的 qualification、risk、promotion 和 evaluation。
- `RepoProfile` 固定 authority identity、protected surface 和 toolchain；`EffectPlan` 在执行前枚举 file/process/Git/evidence logical effects；`GateGraph` 是有界 DAG；`EvaluationProfile` 固定分母、人工分钟、质量信号和停止规则。
- profile generation（`profile_generation`）只能在已实现且共同验收的 capability envelope 内选择 model/effort、工具版本、超时、预算、路径和 gate。
- capability generation（`capability_generation`）引入或改变 CLI/SDK execution interface、App Server client protocol、managed Worktree isolation、Automations scheduling、Provider、network、delivery、Git format、workspace authority、tool inventory、sandbox/permission behavior 或其他 external effect protocol，必须增加 adapter/schema/effect/recovery/migration、Implementation Acceptance 和 Full Q0。
- architecture epoch（`architecture_epoch`）改变 writer concurrency、operator/trust domain、authority topology 或一致性模型。跨 repo 多 writer 属于后继 epoch；多操作者、多信任域和同 effect domain 并发不在当前长期终态内。
- 未实现相应协议的能力始终是 `unsupported`，不能作为 dormant feature flag 或普通 profile 开关启用。

### 4.6 Exact toolchain 与平台资格化

v3.24 不把 `uv run --locked` 当作 exact environment 证明。`RuntimeToolchainManifest` 必须绑定 Python 3.11.x patch、解释器 absolute path/file identity/SHA-256、uv absolute path/version/hash、lockfile、installed distributions、pytest plugins、build frontend/backend 和 hashed build constraints。环境准备显式使用 `uv sync --exact --locked --offline --no-python-downloads --python <manifest-python>`；日常 gate 使用 `run --no-sync`，不得隐藏 sync、download 或 PATH fallback。

`VerificationExecutionProfile` 固定 `supply_chain_identity -> build -> test -> contract_invariant -> hotspot`。build 必须使用 `--build-constraint <manifest-bound-file> --require-hashes`；两个 clean roots 在同一 `SOURCE_DATE_EPOCH` 下产生相同 member manifest 与 artifact hashes。错误 patch、extraneous package/plugin、Python download request、unconstrained backend cache、missing hash、repeat-build mismatch 都是 fail-closed negative fixtures。

CLI execution interface 是 0.2 唯一入选的受控 execution surface；SDK、App Server、managed Worktree 和 Automations 仍是独立 capability candidates，不因同一安装包或 predecessor evaluation 自动获得资格。v3.23 Native comparative result 仅作为 non-normative predecessor evidence：不 promotion profile、不删除 evaluator gates，也不驱动当前 selector。任何 v3.24 语义变更必须建立 v3.25 successor。

### 4.7 Planning execution、模型路由与可测目标

repo 实施控制面只保留一个 `planning_optimization_policy`，不建设第二套 task/spec 目录或新的 planner service。work item 是唯一原子 acceptance/evidence/commit/rollback 单元，不是 AI 会话单元；一次 operator kickoff 可在每项完整 closeout 后重新 selector，按 3 项/180 分钟默认预算顺序继续，失败或阶段、批准、successor、live/auth/provider/remote/破坏性边界立即停止。

planning model routing 只产生待资格化角色候选：复杂、高风险 controller/writer 偏向旗舰能力，独立 reviewer 偏向高推理配置，read-heavy explorer 偏向快速高效配置，封闭重复转换偏向高吞吐配置。候选必须在 declared role/task family/surface/profile generation/cohort 内通过配对评测、质量/安全/证据硬门、成功与 downstream outcome、人工分钟、P50/P95、token/cost/rework 和 generation qualification，才能成为静态 profile；当前 `active_profile_change=none`，禁止静默 dynamic model/effort/provider fallback。

## 5. 路由规则

| 任务特征 | 路由 |
|---|---|
| 模糊需求、需要追问或一次性交互 | Native Direct/Spec |
| 多个独立写集合且顺序固定 | Native Program |
| GUI、生产、数据库迁移、VPS、凭据、remote、不可逆/高风险 | Human-controlled Native |
| 已批准模板、封闭参数、repo-local、低风险、deterministic gates | Batch |
| 自由 prompt 希望自动排队 | 拒绝；先 Spec，再模板化和 Authorization |

Batch 0.2 的 `batch_commit_only_v1` 禁止多 writer、subagent、task Approval、未资格化的 CLI/SDK execution interface、未资格化的 App Server/Worktree/Automations surface、多 Provider、动态 fallback、依赖安装、task-side network、remote Git、merge、push、target-ref 更新和 task-ref 删除。这些是当前 generation 的硬边界；未来 capability 只能在其独立 protocol、effect ledger、recovery matrix、Implementation Acceptance 和 Full Q0 都通过后才可能进入封闭 Batch envelope，而多 writer 必须进入 successor architecture epoch。

## 6. 核心工作流

### 6.0 First-run journey 与 launch templates

预资格化主机的首发旅程固定为 `doctor --json -> repo qualify -> template list/show -> batch dry-run -> batch submit --confirm -> status/action -> evidence show`。每步同时定义 human projection、stable JSON、exit code、authority、evidence locator、下一条安全命令和 rollback；human 文本只能由公开 machine state + `OperatorPresentationCatalog` 渲染，不能插入 raw model/tool output。

`LaunchTemplateCatalog` 恰好包含四个模板：`docs_contract_sync_v1`、`bounded_lint_type_repair_v1`、`focused_test_repair_v1`、`mechanical_repo_maintenance_v1`。每个模板必须声明 closed parameters、allowed path/effect envelope、required/forbidden gates、timeout/resource limits、stop reasons、recovery policy、evaluation denominator 与 success oracle。自由 prompt、动态 command、依赖安装、remote effect、超 envelope 写入和 promotion bypass 一律拒绝。

Native Spec 可生成 template candidate，但不能自动 promotion。promotion 是 durable controlled operator action，要求 owner、review evidence、positive/negative fixtures、pilot/canary result、new template generation 和 repo requalification。首发体验的产品指标至少包括 `prequalified_host_to_first_dry_run_operator_minutes`、`first_commit_ready_pilot_operator_minutes`、`eligible_template_coverage`、`template_qualification_lead_time`、`operator_action_age` 与 `policy_false_block_review_rate`；unknown/unavailable 不得记 0。

### 6.1 模板准备

1. Template owner 提交封闭 schema、固定 prompt compiler、allowed paths、gates 和 limits。
2. Controller 从唯一 base Git tree 计算 qualification input closure。
3. Qualification、environment binding、model/profile/policy generation 均通过后，操作者激活 Authorization。
4. Template 依次经过 pilot、canary、promoted；失败进入 suspended，不动态 fallback。

### 6.2 Batch submit 与重放

1. 对四字段输入执行总字节、深度、数量、UTF-8、duplicate-key、closed envelope、公开 ID grammar 和 canonicalization；只在内存中计算 domain-separated lookup fingerprint。
2. 先只读查既有 family。命中时只验证读取权限和记录完整性，永久返回 generation 0 root task；后来 catalog、Authorization、template 或 base 变化不改变 ordinary replay。
3. 只有未命中时才执行 current membership、template-specific schema、secret scan、qualification、base、Authorization 和 environment admission；拒绝输入不保存参数、普通 hash、lookup fingerprint 或可枚举 oracle。
4. 首次成功 admission 在 `BEGIN IMMEDIATE` 内重查 fingerprint，再原子创建 generation 0 root；并发或 response loss 已创建时返回原 root。
5. failed/cancelled 的合法重做只经显式 `create_resubmission_v1` 原子创建唯一 successor。历史 task-ref 成功、completed、stale base 或非 current source永久阻断当前重提路径。

### 6.3 Attempt 与 closeout

1. Scheduler 在 recovery priority、guard 和 capacity 下 claim。
2. Controller 创建 attempt-local worktree/environment、预建 Job、durable marker，并原子 suspended spawn。
3. `writer_effect_id=stable(task_generation,resolved_writer_intent)`，`writer_launch_id=unique(writer_effect_id,attempt_id)`；`writer_execution_committed` 在 `ResumeThread` 前持久化。每个 task generation 的 execution commit 为 0 或 1；commit 后永久禁止再启动 writer。只有 suspended process 在 commit 前被证明终止时，fresh attempt 才可使用同一 effect ID 和新的 launch ID。
4. Controller 验证 journal、磁盘、secret、gates 和 protected surfaces。
5. Controller 先生成 canonical blob/tree/commit payload、reachability graph 和 expected OID；pinned Git `hash-object -w` 只负责 attempt-local materialization，再由 `cat-file` read-back type/size/payload。seal manifest 后才 promote；Git plumbing 不是唯一 oracle，controller 也不自行维护 loose-object zlib。
6. 顺序固定为 promote -> reachability -> finalize index -> finalize HEAD -> task ref -> evidence -> remove worktree。
7. 任一不确定状态进入 recovery/reconcile/cleanup 或 operator action，不猜测成功。

### 6.4 Managed Native maintenance

正常流程是 durable drain -> 停新 claim -> 等当前 attempt 自然 terminal -> global capacity -> repo maintenance -> Native -> scan/requalification -> 恢复不受影响调度。`kill-current` 是独立紧急动作，必须先耐久写入 operator session、reason 和 terminate intent。

## 7. Minimum-Operator 约束

- 正常 Batch 从 claim 到 commit-ready 零人工。
- 人工只处理 login、environment/repo/template qualification、Authorization、maintenance、cutover/rollback 和明确 recovery/repair。
- 每个阻断只生成一个去重 `OperatorAction`，包含稳定 reason code 和唯一建议命令，不保存自由文本原因。
- 每个 action 必须进入 `durable_local_status_v1` inbox，供 status 命令稳定 pull；`qualified_windows_toast_v1` 只是经资格化且 opt-in 的可选 push transport，发送失败不能关闭或丢失 action。
- 等待 auth/environment/Authorization 的 attempt park 并释放 capacity；可恢复 attempt 优先于新 task。
- 普通失败只影响 attempt；平台、repo、template stop-the-line 必须按 GuardCatalog scope 分流。

## 8. 功能需求

### 8.1 安全与授权

- keyring-only auth；不可用即 qualification 失败。
- attempt 之间不共享任何可写 HOME、SQLite、APPDATA、TEMP、cache 或 spool。
- Codex sandbox config、mutable state 和 sandbox secrets 分离；秘密状态不进入 manifest、backup、evidence、content hash 或普通诊断。`sandbox.log` 作为官方未承诺字段的 opaque diagnostic，不解析、不保存正文/hash；只允许受管轮换和经过 OperatorWorkSession + secret scan 的交互导出。
- project overlay 无条件 `trust_level=untrusted`，同时继续审计 AGENTS、skills、Git attributes 和 repo content。
- 平台不信任 repo 内容，并机械限制其可造成的副作用；不声称消除 prompt injection、语义误导或错误 patch，最终交付仍需人工 review/merge。
- task-side network 禁止；成功未授权 egress 是 global security hard failure。
- 参数不能控制执行面；raw prompt/stdout/stderr/argv/env/config dump 不持久化。
- Submission 固定为 bounded parse -> closed envelope/public grammar -> canonicalization -> volatile lookup -> authorized existing replay -> absent-only current schema/secret scan/admission -> transactional recheck/create；拒绝新输入不形成 family 或可枚举 oracle。
- Authorization revoke 与每个正常 process/controller root effect grant 线性化；已 grant 结果只能完成、终止或 reconcile 同一 logical effect。可收养 controller action 的 Git/helper process 只能使用绑定 parent action grant、current fenced head 和 exact StageJob 的派生 child grant。
- Heartbeat、exact Job termination、pipe drain、journal seal、read-only reconcile 和 recovery handoff 是封闭 `safety_only` 集合；它们使用 `SafetyOnlyExecutionRecord`，不依赖有效 Authorization，也不能被借来创建 writer、gate、publication 或 cleanup/delete。

### 8.2 At-most-once 与恢复

- 每 task generation 恰有一个稳定 `writer_effect_id`，`writer_execution_committed` 次数为 0 或 1；commit 后不得替代或推测性重跑 writer。
- 每 attempt 最多一个 `writer_launch_id` 和 writer process identity；合法 pre-commit retry 必须进入 fresh attempt。
- 每 StageJob run 最多一个 process identity 和 execution commit。
- 每 attempt/effect 只能有一种 execution authority：一个 `AuthorizationExecutionGrant` 或一个 `SafetyOnlyExecutionRecord`，不得二者并存。
- 每个 inherited process grant 必须唯一引用 parent action grant 和 current fenced head，且不得用于 writer、GateRun、model decision 或 arbitrary command。
- 每 fenced action 最多一个 terminal result。
- 每 resubmission source 最多一个 successor。
- 所有响应丢失重放返回同一 ID/result。

### 8.3 Git 与交付

- 只支持本地固定 NTFS、SHA-1/files、唯一 local base ref 的标准 Git repo。
- Qualification 不要求管理员全局禁用 8.3。所有授权以 no-follow handle、volume identity、FILE_ID_128、root ancestry、owner/DACL 和 reparse/hardlink policy 判定；long/short alias、case variant 或字符串 final path 都不能扩大 allowlist。无法查询卷策略时由非提权 alias-bypass Q0 补足；只有身份冲突、alias 能绕过 policy 或无法建立安全证明才 incompatible。
- 禁止 remote、submodule/LFS filter、外部 driver、SHA-256 object format、reftable。
- Commit bytes、parent、identity、timestamp、message grammar 和 object graph 全部可预计算。
- `git_hybrid_materialization_v1` 要求 controller 独立计算 canonical payload/expected OID，pinned Git materialize，随后 `cat-file` read-back；任一不一致阻断 publication。
- Claim time 只在 claim CAS 生成一次；HEAD/task-ref publication 禁止创建或追加 reflog。
- 不使用 `reset --hard` 掩盖额外文件。

### 8.4 证据

- Event append-only；secret scan 前不保存未知 path/content digest。
- Raw process output 和其 content hash 均不保存。
- ExecutionReceipt 必须满足 process exit、EOF、final schema、limits、journal seal、Job zero-process 六项。
- Evidence 外置，commit message 不含 evidence ID，避免内容寻址环。

## 9. 非功能需求

- Python 3.11.x 模块化单体；具体 patch、解释器绝对路径、版本、file identity 和 SHA-256 由 `RuntimeToolchainManifest` 锁定。环境 preparation 使用 exact/locked/offline/no-download sync，validation 使用 no-sync，build backend 使用 manifest-bound hashes，并通过 clean-root repeatability。
- Windows NTFS crash behavior 必须通过 no-replace、atomic replace、FlushFileBuffers 和 power-loss probes 证明。
- SQLite `DELETE + FULL + short transaction`。
- 单 writer capacity=1，scheduler 每五分钟最多 drain 一项。
- ResourceLimitPolicy 的每个边界具备 limit-1/limit/limit+1 测试。
- 写入预算的 0.2 必需模式是 `accounting_kill_audit`：spawn 前快照 logical/allocated bytes、entry count、identity 与 reserve，使用 `ReadDirectoryChangesW` + 最多 500 ms monotonic fallback 重算，limit+1 先耐久记录再 kill/drain/seal，最后做完整 no-follow audit。它明确不宣称无瞬时 overrun；越界或未知结果绝不发布。
- Runtime volume 必须保持 task 不可访问、non-sparse/non-compressed、实际分配的 1 GiB emergency reserve。只有 durable disk-pressure safety recovery 可 fenced 释放；释放后 platform 保持 suspended，直至零 active attempt 下重建并 CAS 新 generation。
- `HardWriteQuotaCapability` 只是经独立 Full Q0 证明的可选增强；NTFS per-user quota、FSRM 或 Job I/O rate 不得未经适用性证明冒充 attempt-directory atomic quota。低磁盘进入 `disk_pressure/resource_exhausted`，不冒充 environment 缺失。
- 所有 transition、guard、reason code、feature 和 operator action 必须版本化并可机器验证。

## 10. 成功指标

安全硬门始终为零：未授权写入、已声明/已检测敏感信息泄漏、重复 writer、冲突 object/commit/ref、错误 cleanup、未记账 Git 副作用和 successful unauthorized egress。

“高度自主”以 `completed_work_items_per_operator_kickoff`、`unattended_verified_closeout_rate` 和 `net_operator_minutes_per_success` 衡量；“高速”分别报告 Native `latency_p50_p95` 与单 writer Batch `verified_cycle_time_p50_p95`；“高效”还必须报告成功/downstream outcome、token/cost/rework 和 recovery/rollback。任何 unknown/unavailable 保留原值，不能记为 0；“最优”只允许在 declared role/task family/surface/profile generation/cohort 内陈述。

30-task cohort：

- 最多 5 个 probe-only，至少 25 个 commit-ready；
- self-host 与两个真实目标 repo 各至少 5 个 writer task；
- 无人值守成功率至少 80%，人工介入不超过 20%；
- mandatory gates、evidence verify、backup restore、recovery drill 100%；
- 结束时无未恢复状态。

`commit-ready` 不是长期质量真值。P4 与任何 TaskFamily/profile/capability promotion 必须抽样收集 `DownstreamOutcomeRecord`：绑定 ActiveRuntimeIdentity、task commit、可验证 final integration commit lineage、human review disposition、merge/reject/rework、后续 CI、revert 或 defect evidence locator。runtime 不自动 push、不读取 remote CI、不替人决定 merge/reject；操作者只附回 secret-safe 结果证据。`censored|unknown` 必须保留在分母，不能算 pass 或静默删除。

效率至少 12 个严格配对 case：

`net_operator_minutes_per_success = 窗口内全部人工活动分钟 / commit-ready 成功数`

失败、取消、恢复、auth、qualification、模板和 runtime 维护均进入分子；重叠区间只计一次。要求该指标下降至少 50%，且成功任务/操作者小时提高至少 50%或 P50 周期下降至少 30%。

## 11. 发布与批准边界

1. **Baseline Approval**：v3.24 正文、15 项 normative package、standalone verifier、preliminary/manifest-closure review 全部绿色并由独立明确授权签发；不要求代码存在。v3.23 predecessor evaluation 不是批准输入；任何 v3.24 语义变化先创建 v3.25。
2. **Implementation Acceptance**：代码、migration、CLI/first-run、四个 launch templates、runbook、legacy conformance、crash、backup/restore、exact toolchain 与 clean-root repeatability 绿色。
3. **Full Q0 / P2 Admission**：真实安装、Codex/Git/Windows/sandbox/adapter/profile 行为绿色后，才允许一个 P2 pilot。

当前仅允许 P0A normative closure。任何把 repo-side simulation、legacy test、probe 或 candidate prose 当作后三层门证据的做法都不符合 PRD。
