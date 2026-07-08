# Local AI Runtime 任务清单

项目展示名是 `Local AI Runtime`，中文名是 `本地 AI 运行时`。当前主产品线是 `Hermes -> AgentBridge -> Codex`；历史仓库 slug / 当前本地目录仍为 `local-ai-dev-orchestrator`。

当前 active queue 仍然是 `PHASE-1-VERTICAL-SLICE`，当前预期 next action 仍是 `promote_phase1_execution`。

## Strategic Return Overlay

- [x] `A-T01` authoritative docs / planning-status / policy / verifier / change-evidence truth reset
  - Done when:
    - `Hermes -> AgentBridge -> Codex` 成为 authoritative docs 的主叙事
    - canonical intake / `result.json` / compatibility projection 当前事实仍被显式保留
    - `python .\scripts\verify-planning-status.py` 通过
  - Status note:
    - 2026-07-06 已完成 repo-side 落盘
- [x] `B-T01` host_local crash recovery and lease helpers
  - Done when:
    - worker crash 后 `task failed + worker idle`
    - 当前 `leases` 表具备 acquire / renew / release / reap 最小函数
  - Status note:
    - 2026-07-06 已落 `host_local` 失败收口、lease helpers、以及 exec fallback 进程守卫
- [x] `C-T01` verification runner
  - Done when:
    - `verification_summary.json` 不再默认 `no_commands_configured`
    - 最小 `test + contract` gate 真实执行
  - Status note:
    - 2026-07-06 已落最小真实 gate executor；`build / lint / typecheck / hotspot` 继续按 `gate_na` 或 `not_configured` 留痕
- [x] `D-T01` AgentBridge-first intake upgrade
  - Done when:
    - 合规 markdown task 可直接进入 `host_local` 主路径
    - markdown intake 先归一化到 repo-owned canonical 默认值
    - execution-critical override / markdown 侧 gate 命令输入 fail closed
  - Status note:
    - 2026-07-06 已落安全版 AgentBridge-first intake；随后推进到 `P2-T03`
- [x] `E-T01` Hermes parity and container lifecycle
  - Done when:
    - parity / historical mapping / container lifecycle 进入同一闭环
    - 是否做 `compatibility_projection_ref` 与 `lane` rename 有明确决策
  - Status note:
    - 2026-07-07 已完成 repo-side closeout；当前明确决定继续保留 `compatibility_projection_ref` 与 `lane` 现名，不在当前 repo-side parity / topology closeout 中做字段改名，待 non-host_local runner wiring 与后续 review 稳定性都真实落地后再复评
- [ ] `F-T01` topology expansion
  - Done when:
    - `remote_non_gui` 进入 simulation
    - `vm_gui` 只有在真实 GUI-only workload 证据下才升级

能力范围与晋升顺序固定为：`host_local > remote_non_gui > vm_gui`。

## Governance Overlay

- [x] `GOV-T01` formalize governed reference companion
- [x] `GOV-T02` split selector from verifier
- [x] `GOV-T03` add repo-level change-evidence index
- [x] `GOV-T04` add release-style preflight entrypoint
- [x] `GOV-T05` wire docs, AGENTS, and proof routing
- [x] `GOV-T06` selector policy verifier coverage
- [x] `GOV-T07` impl_pack stale demotion and machine checks
- [x] `GOV-T08` absorb control-repo global-only rule governance
- [x] `GOV-T09` add target-project `AGENTS.md + CLAUDE.md` coordination pilot
- [x] `GOV-T10` align docs, wrapper boundary, and repo-level evidence for the pilot

## Kernel V2

- [x] `K2-T01` runtime_v2 package skeleton + config fields + experimental CLI entrypoints
  - Status note:
    - 2026-07-08 已落 `runtime_v2/` 模块骨架、`--run-task-v2 / --resume-task-v2 / --retry-task-v2 / --migrate-control-plane-v2 / --cutover-v2`，以及 `runtime.active_version / experimental_v2_enabled / control_plane_db_v2 / artifact_root_v2`
- [x] `K2-T02` v2 canonical task / storage / attempt artifact skeleton
  - Status note:
    - 2026-07-08 已落 `dependency_refs / verification_profile / continuation_policy`，6 表 v2 控制面，`.ai/runs-v2/<run_id>/<task_id>/<attempt_id>/`，以及 `resume_point / retry_rewind` 的 attempt-level 收口
- [x] `K2-T03` docs / spec / verifier absorb Kernel V2 without switching active queue
  - Status note:
    - 2026-07-08 authoritative docs、路线图、实施计划、任务清单、spec、change-evidence、以及 verifier 已开始承认 `Kernel V2`，但默认入口与 active queue 仍未切换
- [x] `K2-T04` deepen autonomous scheduling / review / policy gates on runtime_v2
  - Status note:
    - 2026-07-08 已落第一批 autonomous scheduling 深化：dependency-blocked task 会持久化 repo-relative `tasks.task_path`，依赖满足后可通过 `--run-ready-blocked-v2` 批量续跑；非依赖原因的 `blocked` 不会被自动续跑
    - 2026-07-08 已落第一批 review / policy receipt 深化：v2 `review_result.json` 现在会 materialize 结构化 `blocking_reasons`、`changed_paths`、`gate_failed`、`policy_surface_touched`
    - 2026-07-08 已落 bounded review sidecar hook：显式 review worker / worker factory 路径可 materialize sidecar receipt，失败时仍 fallback 到 repo-side blocking receipt
    - 2026-07-08 已落 pre-worker policy guard：network/profile、non-host-local lane、GUI requirement、sensitive write scope 会在 worker 前 fail-closed blocked
    - `K2-T04` 按当前 scoped deepening 已完成；这不代表 default cutover、non-host_local runner wiring、vm_gui runner wiring 或 live accepted
- [x] `K2-T05` add trace / eval / regression fixtures for runtime_v2
  - Status note:
    - 2026-07-08 已落 attempt-level `regression_fixture.json` 核心状态覆盖：completed / reviewing / gate-retryable final-result、dependency-blocked、admission-paused、pre-worker policy-guard blocked、worker-failure retryable / failed、retry queued 路径都会写出可回放的 status/profile/gate/artifact refs 摘要，并记录到 v2 artifacts 表
    - 2026-07-08 已落最小 `--eval-regression-fixtures-v2`：从 v2 artifacts 表读取 `regression_fixture`，校验 schema / required fields / missing files，并写出 `.ai/runs-v2/_eval/regression-fixture-summary.json`
    - `K2-T05` 按当前 scoped trace / eval / regression fixture 闭环已完成；这不代表 default cutover、live accepted 或完整历史 corpus 评测平台
- [ ] `K2-T06` run cutover drill and switch the default entrypoint only after gates are green
  - Status note:
    - 2026-07-08 已落 `--cutover-drill-v2`：检查 `runtime_v2` enabled、默认入口仍为 v1、至少一条 completed v2 attempt、以及 regression fixture eval summary，并写出 `.ai/runs-v2/_cutover/cutover-drill-summary.json`
    - 2026-07-08 已让 `--cutover-v2` 先跑 drill；drill 未 ready 时 fail-closed，不修改 `runtime.active_version`
    - 2026-07-08 已开放 `runtime.experimental_v2_enabled=true`，并用真实 `local_maint` / Codex SDK v2 probe 完成一条低风险本地写入任务；`--eval-regression-fixtures-v2` 当前 `fixture_count=1 / ok=true`，`--cutover-drill-v2` 当前 `ready=true / cutover_performed=false`
    - 2026-07-08 已补 cutover review / rollback drill：drill ready 后，默认 `--cutover-v2` 只写 `.ai/runs-v2/_cutover/cutover-review-summary.json` 并返回 `manual_approval_required / cutover_performed=false`；只有显式 `--confirm-cutover-v2` 才允许进入默认入口切换路径
    - 2026-07-08 已补 `--cutover-rollback-drill-v2`：验证 review summary、恢复 `runtime.active_version = v1` 的配置目标、archive root 可用性和当前默认入口仍为 v1；该入口写出 `.ai/runs-v2/_cutover/cutover-rollback-drill-summary.json`，不执行 restore
    - 2026-07-08 已补 operator approval evidence gate：`--cutover-v2 --confirm-cutover-v2` 仍必须附带 `--cutover-approval-ref <approval.json>`，且 approval JSON 需校验 schema、`approved_by / approved_at`、当前 review / rollback summary 引用、以及 `default_entrypoint_switch / rollback_restore_required` 风险确认；缺失时返回 `approval_required / cutover_performed=false`
    - 2026-07-08 已补 operator approval template 入口：`--cutover-approval-template-v2` 会生成默认 `approved=false` 的可编辑 approval JSON，并引用当前 review / rollback drill summary；该入口不执行 cutover，不修改默认入口
    - 2026-07-08 已补 operator approval audit 留痕：approval validation 会记录 `approval_sha256 / approval_byte_count / approved_by / approved_at`，并写出 sanitized `operator-approval-audit.json`；该留痕不执行 cutover
    - `K2-T06` 未标完成：真实默认入口切换仍需满足 cutover 条件、门禁与人工边界，当前不声明 live accepted

## Phase 1

- [x] `P1-T01` 默认 layout 迁到 `.ai/state` 与 `.ai/runs`
- [x] `P1-T02` canonical task intake 落地
- [x] `P1-T03` 正式 `result.json` + markdown projection 双写
- [x] `P1-T03A` repo-owned config / worker-profile contract
- [x] `P1-T04` 一次真实 SDK 垂直切片
- [x] `P1-T05` `evidence_index.json` sha256 可重算
  - Status note:
    - 2026-07-07 已补 repo-owned `host_local` task entrypoint 与 worker factory；`host-orchestrator --run-task` / `run-host-task.ps1` 当前已直接消费 `local_maint` 的 `codex_sdk` 路径，并在结构上支持 `codex_exec`；built-in `codex_exec` profiles 仍保持 non-host-local handoff，而 `scripted / gpt54_direct / claude_glm` 继续 live task execution fail-closed

## Phase 2

- [x] `P2-T01` acceptance-and-gates authoritative spec
- [x] `P2-T02` run-state-and-handoff foundation
- [x] `P2-T03` AgentBridge round-trip parity
  - Done when:
    - markdown task 直连 `host_local` 主入口而不再依赖 canonical json sidecar
    - `result.json`、`verification_summary.json`、`cost_summary.json`、`evidence_index.json`、`AgentBridge/results/*.md`、`artifacts/*.txt` 构成 repo-side parity 闭环
  - Status note:
    - 2026-07-06 已完成 repo-side projection parity；仍未自动升级为 `platform compatibility green` 或 `live accepted`

## Phase 3

- [x] `P3-T01` verification runner 固定 gate 顺序
  - Done when:
    - verification runner 固定按 `build -> lint -> typecheck -> test -> contract -> hotspot` 顺序留痕
    - `gate_na / not_configured / pass / fail` 都在 `verification_summary.json` 中保持顺序稳定
  - Status note:
    - 2026-07-07 已完成 repo-side fixed gate order；当前真实执行仍只覆盖 `test / contract`，其余 gate 继续按 `gate_na / not_configured` 留痕
- [x] `P3-T02` path guard
  - Done when:
    - repo-escape path claim 在 worker 前 fail closed
    - declared `worktree_path` 与实际 `workspace_root` / Git root 不匹配时 fail closed
    - declared isolated worktree branch 与 `branch_name` 不匹配时 fail closed
  - Status note:
    - 2026-07-07 已完成 repo-side path guard；当前在具备 `.git` admin path 的 workspace 中，还会对 worker 结束后的新改动执行 `allowed_paths / forbidden_paths / write_access` fail-closed 审计
- [x] `P3-T03` worktree manager
  - Done when:
    - declared isolated worktree 任务可从 repo root 自动 create 或 reuse linked worktree
    - worker 与 verification 在 declared worktree `cwd` 中执行
    - `result.json.cleanup_status` 至少区分 `inline_only` 与 `deferred`
  - Status note:
    - 2026-07-07 已完成 repo-side worktree manager；cleanup automation 与 runtime ledger 现已同批落地，但 `worktree` 仍只代表写入隔离，不代表 memory/provider/session 隔离
- [x] `P3-T04` cleanup manager
  - Done when:
    - runtime-managed clean linked worktree 在成功且无需 handoff 的路径上自动 remove
    - review-pending、failed、dirty、或外部直接启动的 isolated worktree 显式保留，并写出 `worktree_cleanup` 事件
    - `result.json.cleanup_status` 能区分 `cleaned / deferred / cleanup_failed`
  - Status note:
    - 2026-07-07 已完成 repo-side cleanup manager；branch deletion 仍未自动化，但 cleanup 现在会与 `dispatch_state.json`、`result.json`、以及 `runtime_tasks` 的 cleanup 字段共同收口
- [x] `P3-T05` graded autonomy runtime ledger
  - Done when:
    - `host_local` 为每次运行写出 `.ai/runs/<run_id>/<task_id>/dispatch_state.json`
    - `result.json` 盖章 `cleanup_owner / status_reason / dispatch_state_ref`
    - `runtime_tasks` 索引 `run_id / attempt / state_reason / next_action / cleanup_status / cleanup_owner / dispatch_state_path`
  - Status note:
    - 2026-07-07 已完成 repo-side runtime ledger；当前主路径已稳定写出 `running / waiting_handoff / needs_review / completed / failed`，而 `queued / input_required / cancelled / stale / resumed` 仍留给后续 lifecycle ops
- [x] `P3-T06` ledger lifecycle ops and idempotent recovery
  - Done when:
    - heartbeat stale detection 可把 ledger 标成 `stale`
    - explicit cancel / retry / resume 可同步更新 DB 与 ledger
    - `cancelled / stale / resumed` 有 repo-side tests 覆盖
  - Status note:
    - 2026-07-07 已完成 repo-side lifecycle ops；`task_lifecycle.py` 与 CLI 现在可 materialize `stale / cancelled / resumed`，`retry` 通过 `attempt + retry_rewind` 收口，explicit cancel/resume/retry 会同步清理 active lease，resume/retry 也会刷新 `heartbeat_at / stale_after`

## Phase 4

- [x] `P4-T01` planner adapter
  - Done when:
    - `planner_required` 基于当前 risk/dependency 字段在 intake 后完成机器派生
    - planner-gated task 可先写 live `planner_result.json` receipt，并在主 worker 前停在 `waiting_handoff`
    - `result.json`、`verification_summary.json`、`cost_summary.json`、`evidence_index.json` 在 handoff 路径上保持齐全
  - Status note:
    - 2026-07-07 已完成 live planner sidecar receipt 边界；当前 planner-gated task 会先运行 codex-backed planner sidecar、写出 `planner_result.json`，然后仍停在 `waiting_handoff`；当前仍不是 live `Direct GPT-5.4 API` planner
- [x] `P4-T02` review adapter
  - Done when:
    - `review_required` 在当前 materialized 条件下完成 repo-side 派生
    - review-gated task 在 worker / verification 之后停在 `needs_review`
    - `result.json`、`verification_summary.json`、`cost_summary.json`、`evidence_index.json` 在 review 路径上保持齐全
  - Status note:
    - 2026-07-07 已完成 repo-side graded autonomy review gate；低风险任务默认自动推进，medium/high/critical 风险、policy surface、以及 force-on review 会停在 `needs_review`；当前仍不是 live `Claude Code + GLM-5.2` review adapter
- [x] `P4-T03` 正反触发谓词测试
  - Done when:
    - `planner_required` 与 `review_required` 的正反分支都有 repo-side 测试覆盖
    - `user_forced_planner / user_forced_review` force-on overrides 被 canonical task 与 manifest contract 实际承接
    - `false` force-off override 被明确拒绝，避免伪造“强制关闭 gate”
  - Status note:
    - 2026-07-07 已完成 repo-side 谓词正反覆盖；随后已补完 `P3-T02` path guard、`P3-T03` worktree manager、`P3-T04` cleanup manager、`P3-T05` runtime ledger、`P3-T06` lifecycle ops、`P4-T04` structured receipts、以及 `P5-T01` repo-side `leases / route / quota` 收口；下一最小切片转到 `multi-worker simulation`
- [x] `P4-T04` structured review receipt and closeout receipt
  - Done when:
    - review sidecar 路径可落 `review_result`
    - closeout bundle 可稳定引用 verification、cleanup、review receipt
    - `repo-side green` 能显式区分 structured review receipt、cleanup receipt、与 `live accepted`
  - Status note:
    - 2026-07-07 已完成 repo-side structured receipts；live planner-sidecar 路径现在会落 `planner_result.json`，review-gated 路径会落 `review_result.json`，当前 planner/review/completed runtime outcome 都会落 `closeout_bundle.json`，并由 `result.json / dispatch_state.json / evidence_index.json` 串起引用
    - 2026-07-07 follow-on closeout：配置 `review_worker_profile = claude_glm_review` 的 host_local review path 当前可 materialize bounded live heterogeneous review receipt；`claude_glm` primary task execution 与 non-host_local runner 仍未接线

## Phase 5

- [x] `P5-T01` leases / retry / route / quota 收口
  - Done when:
    - canonical task 显式 `worker_profile` 真正被 runtime 消费
    - explicit/default route reason 写入 `result.json / dispatch_state.json / route_decisions`
    - selected profile 的 `max_active_leases` 超额时在 worker 前 handoff
  - Status note:
    - 2026-07-07 已完成 repo-side route/quota closeout；当前仍不是 multi-worker scheduler，也不等于 `multi-worker simulation green`
- [x] `P5-T02` multi-worker simulation
  - Done when:
    - deterministic simulation 能覆盖 `retry / route / quota / review-handoff`
    - summary 明确给出 `scenario_count / task_run_count / route_decision_count / retry_event_count / worker_statuses / state_counts`
    - CLI/script entrypoint 可重跑并输出 JSON summary
  - Status note:
    - 2026-07-07 已完成 repo-side deterministic multi-worker simulation suite；当前仍不等于 live 多 worker scheduler 或 `live accepted`
- [x] `P5-T03` remote_non_gui promotion evidence
  - Done when:
    - repo-owned `remote_non_gui_probe` profile 已进入 `workers.yaml`
    - 选中 `remote_non_gui` lane/profile 时，`host_local` 会在 worker 前 fail closed 到 handoff，而不是伪装成 remote runner 已执行
    - CLI/script entrypoint 可重跑 promotion summary，并显式给出 `route_decision_count / worker_lanes / state_counts`
  - Status note:
    - 2026-07-07 已完成 repo-side `remote_non_gui` promotion evidence；当前仍未落 remote runner、`platform compatibility green`、或 `live accepted`

## Phase 6

- [x] `P6-T01` Hermes parity closeout
  - Done when:
    - repo-owned verifier 会把 certified baseline doc、current known-good / boundary anchors、snapshot contract、known-good validator、以及 historical container lifecycle boundary 收进同一可重跑 summary
    - verifier 结果明确区分 env-sensitive bring-up drift 与 repo-side regression，不把 repo-side proof 写成 remote runner、`platform compatibility green`、或 `live accepted`
  - Status note:
    - 2026-07-07 已完成 repo-side Hermes parity closeout；`runtime/host-orchestrator/scripts/run-hermes-parity.ps1` 当前会把 baseline boundary、snapshot anchors、以及 container lifecycle guard 放进同一闭环，当前 shell 中只剩 `independent_key / independent_base_url` 两个 env-sensitive bring-up gate 为红
- [x] `P6-T02` historical snapshot mapping
  - Done when:
    - `implementation-status.md`、`当前交接摘要.md`、以及 `接手检查单.md` 对当前 known-good / boundary anchor 一致
    - current known-good snapshot 与 AgentBridge contract validator 继续为绿，并与 accepted runtime profile / boundary evidence 一致
  - Status note:
    - 2026-07-07 已完成 repo-side historical snapshot mapping；当前 anchor 固定到 `known-good-20260628-225738-431.json` 与 `verify-hermes-boundary-20260628-225841-414.json`
- [x] `P6-T03` vm_gui conditional promotion evidence
  - Done when:
    - repo-owned `vm_gui_probe` profile 已进入 `workers.yaml`
    - `requires_gui=true` 的默认请求会在 `host_local` 上因 GUI-only 条件 handoff，而不是静默降级成 host-local 已执行
    - 显式 `vm_gui_probe` 也只会 fail closed 到 handoff，并把 `selected_lane=vm_gui + runner_not_wired` materialize 到 summary
    - CLI/script entrypoint 可重跑 promotion summary，并显式给出 `route_decision_count / worker_lanes / state_counts`
  - Status note:
    - 2026-07-07 已完成 repo-side `vm_gui` conditional promotion evidence；当前仍未落 vm runner、真实 GUI-only workload acceptance、`platform compatibility green`、或 `live accepted`
