# LAR-P0A-EVAL-002 Native Thin-Path Comparative Results

## Goal

在 Baseline Approval 前执行冻结的 Native thin-path / capability comparative evaluation，保留全部失败、停止、unknown downstream、recovery 和 conditional disposition 分母，并只产生合同允许的 machine-readable decision。

当前落点仍是 `runtime/host-orchestrator` 与 `.ai/state/control-plane.db`；目标归宿仍是批准后的 `runtime/local-ai-runtime`。本切片不创建新 runtime、Batch claim、approval、Truth Reset、remote effect 或 live delivery。

## Frozen Inputs

- snapshot commit：`6fd6cd54037f17e44192bc272306b137def7f8a4`
- snapshot tree：`11c8ab770769b3aeff5c111063a316e712fa7241`
- model/effort：`gpt-5.6-sol / high`
- core CLI generations：`b3f5c328...741b36`（10 trials）、`9f137a1c...a2b1`（5 trials）、`ffb9c5c4...34f2d`（3 trials）；均在被选择前具有 generation/Q0 evidence
- current qualified CLI generation：`ffb9c5c40e7ac30769409818f17d0426f4260a328971a50074acbd7d11934f2d`
- contract SHA-256：`e4129a74...b39 / 27965825...6b0 / a82b869e...721`
- sandbox/effect：`workspace-write`、network disabled、approval never、disposable detached worktree、无 push/remote CI/external delivery

## Results

| Metric | Thin Codex Native | Native + agent-side key gates | Overall |
|---|---:|---:|---:|
| normalized success | 4/9 | 1/9 | 5/18 |
| P50 wall | 793.613s | 603.442s | 603.442s |
| P95 wall | 1446.966s | 995.069s | 1446.966s |
| input tokens | 9,697,000 | 8,073,559 | 17,770,559 |
| output tokens | 109,652 | 159,878 | 269,530 |
| command failures | 47 | 40 | 87 |
| retries / rework | 26 / 0 | 23 / 2 | 49 / 2 |

合并指标跨 3 个 append-only generation，只用于冻结 corpus 的保守结论，不是同 generation A/B 或 profile promotion 证据：

| Generation | Core trials | Success / failed / stopped | Thin Native | Native + key gates |
|---|---:|---:|---:|---:|
| `b3f5c328...741b36` | 10 | 4 / 4 / 2 | 3/5 | 1/5 |
| `9f137a1c...a2b1` | 5 | 1 / 4 / 0 | 1/2 | 0/3 |
| `ffb9c5c4...34f2d` | 3 | 0 / 3 / 0 | 0/2 | 0/1 |

两次外部 host drift 均先写 generation transition，再为新 generation 完成 Q0，只继续未执行 trial；`NTPE-TF-002-thin_codex_native-r2` 作为 drift stop 留在原分母且未重跑。中间 generation `478f4e2c...68edc` 的 Q0 后又观察到 host restart/auth/provider projection 变化，在任何 core trial 前失效，因此没有 denominator entry。

TF-003 两个 variant 均为 `0/3`，六次都没有按 oracle 直接调用 `_load_json`。独立 evaluator gate 集 `18/18` 完整，说明“patch 可通过 tests”不能替代冻结 task oracle。两项 append-only normalization 保留原始收据：`NTPE-NORM-001` 把 agent-side required test gate 失败归一为 failed；`NTPE-NORM-002` 以最终 worktree removal/host proof 把诊断性 pre-clean stop 归一为 success。

13 次 rollback/recovery attempt 均由原始 receipt 或 append-only follow-up evidence 收口。18 个 downstream outcome 均为 `unknown/not_recorded`，继续保留在分母；provider cost 未查询，记录为 unavailable，不记 0。trial 内 active human minutes 为 0，passive model/command wait 单列于 wall time。

## Conditional Harnesses

- Superpowers：TF-001 预声明 applicable，但执行前 sealed `skills-manager HEAD` 从 `81d6026...` 漂移为 `0b47567...`。即使两个计划调用的 skill hash 未变，也不能选择性忽略整体 sealed identity；3 个 repeat 记 `excluded_by_stop/inconclusive`，不重封、不补跑。TF-002/003 共 6 个 slot 按预声明 not_applicable。
- Trellis：本机无可封装 callable installation，9 个 slot 预声明 not_applicable；没有初始化第二 control plane。
- Hermes：corpus 无 remote/VPS/cron/message-gateway requirement，9 个 slot not_applicable；不推出 Hermes 已被替代或应退休。
- `grill-me` / `grill-with-docs`：不在 frozen variant set；只保留为按需设计澄清工具。

## Decision

machine decision 为 `preserve_v3_23_semantics`。实测没有要求改变 Batch 禁止面、adapter family、authority、并发、Q0 trigger、quality promotion 或 truth source，因此不创建 v3.24。

该决定不是 profile promotion：

- 保留 Native-first 快路径，但不把 `gpt-5.6-sol/high` 作为已证明的默认 profile；
- 保留独立 policy/evaluator gates、evidence、generation/Q0 和 recovery/rollback；
- 不把 agent-side 重复全门禁 prompt 设为默认；
- CLI execution interface 资格只绑定本次 generation，不外推到 App Server、SDK、managed Worktree 或 Automations；
- 不把 Superpowers、Trellis、Hermes 或 Grill 设为产品控制面。

正式结果、决定、交叉哈希证据分别为：

- `docs/evaluations/local-ai-runtime-0.2/native-thin-path-capability-results.v1.json`
- `docs/evaluations/local-ai-runtime-0.2/native-thin-path-capability-decision.v1.json`
- `docs/evaluations/local-ai-runtime-0.2/native-thin-path-capability-evidence.v1.json`

## Verification

2026-07-13 按固定顺序完成收口验证：

- build：`gate_na`；`runtime/local-ai-runtime` 不存在，当前仍是 candidate planning slice；替代验证为 host-orchestrator pytest，缺口到 `LAR-P0D-001` 恢复真实 build；
- test：`uv run --project ./runtime/host-orchestrator python -m pytest`，exit 0，`230 passed in 53.15s`；
- contract/invariant：`python scripts/verify-planning-status.py`，exit 0，`status=pass`，evaluation decision=`preserve_v3_23_semantics`，missing artifact count=`13`；
- selector：`python scripts/select-next-work.py`，exit 0，唯一下一项为 `LAR-P0A-002 / close_baseline_normative_package_first`，`side_effects_performed=false`；
- hotspot alternative：`git diff --check`，exit 0；当前切片不修改 executable runtime hot path；
- release-style：`pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit`，exit 0；内含 `231 passed in 54.68s`、planning verifier/selector、Python/PowerShell script parsing 和 `git diff --check`；未自动提交；
- artifact integrity：三份 terminal JSON 均可解析，results SHA-256=`6168db2aa1657d34c1b38f71b6abce0d6250a1a5eb0ab749ca5057b4078adf27`，decision SHA-256=`b242cf86c85ecf48fff1d137380f8ce9a98fc4023d866416d0d6a2ef81bf8eeb`，evidence 内两项交叉引用均匹配；
- receipt audit：18 个 tracked trial projection、14 个 supporting record、3 个 core generation 与 2 个 transition 的 286 项字段/哈希/分层检查通过，4 个 generation-record mapping 的 48 项绑定检查通过，既有 pooled 指标的 81 项聚合复算通过；generation fail-closed verifier 定向测试 `73 passed`；聚焦 changed-file secret scan 覆盖 21 个文本文件、8 类模式，无发现；
- final review hardening（2026-07-14）：planning verifier 进一步要求每个 core generation 恰好一条 trial projection、所有 trial/transition locator 位于无 traversal 的 `private-local/`，并拒绝 boolean、负数或非有限 wall/token/count；反例加入既有定向测试，`73 passed`。全量 preflight 再次 exit 0，内含 `231 passed in 55.75s`；不改变 terminal JSON、决定或 v3.23 规范语义；
- boundary：封存时 `git worktree list --porcelain` 仅 1 个主 worktree，`D:\\CODE` 下残留评测目录为 0，Codex PID `20396` 与 code-mode host PID `23824` 保持存活。封存后的 2026-07-14 观察到宿主外部换代，当前 PID 为 `5412 / 6660`；本任务未执行任何 stop/restart/network/auth/provider 动作，Windows 日志也未提供可归因的 Codex crash 或 AppX update。新宿主 generation 不继承评测终态 generation 资格，且未运行新 trial；全量 preflight 同期 12 次采样中两进程与 WLAN 均 `12/12` 在线。

## Rollback

冻结的 raw receipts、normalization、recovery 和 terminal artifact 不原地重写。若仅回滚 planning projection，恢复 `LAR-P0A-EVAL-002` 前必须先创建新的 supersession evidence，不能让已存在 terminal result 与 pending 状态矛盾。不得回滚 v3.23 candidate bytes、`.ai/config`、live state、auth/provider 或 Codex processes。
