# Acceptance And Gates Contract

## 目的

定义当前仓的 authoritative acceptance tiers，以及固定 gate 顺序。

## 顶层 Acceptance Tiers

PRD 的四档继续是唯一顶层口径：

| tier | 说明 |
| --- | --- |
| `repo-side green` | 本仓代码、测试、契约与 repo-side evidence 已闭环 |
| `multi-worker simulation green` | 多 worker / 多仓仿真闭环通过 |
| `platform compatibility green` | 兼容面与历史基线 round-trip 通过 |
| `live accepted` | 真实网关、真实执行链与 acceptance 证据齐备 |

## Explicit Mapping

本文件新增的细分状态不是新 tier：

| 细分状态 | 归属 |
| --- | --- |
| `mock green` | `repo-side green` 的子状态 |
| `live probe ready` | 进入 `live accepted` 前的 readiness gate |

结论：

- `mock green` 不能单独升级成第五档
- `live probe ready` 不是与 `live accepted` 并列的 acceptance tier

## Fixed Gate Order

固定顺序：

`build -> [lint -> typecheck] -> test -> contract -> hotspot`

补充边界：

- experimental `runtime_v2` 的 `gate_report.json` 也固定按同一顺序留痕
- 当前仓的 build / hotspot 仍维持既有 `gate_na` truth；`runtime_v2` 已有骨架，不等于默认 gate 已切到 v2

当前 repo-level preflight 允许：

- `build = gate_na`
- `hotspot = gate_na`

但必须同时记录：

- `reason`
- `alternative_verification`
- `evidence_link`
- `expires_at`

## gate_na

只有以下情况允许 `gate_na`：

- 纯文档 / 纯注释 / 纯排版切片
- 仓库当前客观不存在该 gate 的 repo-owned entrypoint

`gate_na` 不能改变固定顺序，也不能伪装为 `pass`。

## Tier Evidence Mapping

### repo-side green

最低证据：

- `python .\scripts\verify-planning-status.py`
- `uv run --project .\runtime\host-orchestrator python -m pytest`
- `.ai/runs/<run_id>/<task_id>/result.json`
- `.ai/runs/<run_id>/<task_id>/verification_summary.json`
- `.ai/runs/<run_id>/<task_id>/cost_summary.json`
- `.ai/runs/<run_id>/<task_id>/evidence_index.json`

### multi-worker simulation green

额外需要：

- `leases / retry / route / quota` 仿真证据
- repo-owned simulation entrypoint，例如 `runtime/host-orchestrator/scripts/run-multi-worker-simulation.ps1` 的 summary output
- planner/review/handoff 基础契约已稳定

### topology promotion evidence（细分证明，不是新 tier）

额外需要：

- non-host-local `worker_profile` 在 `host_local` 上只能 fail closed 到 handoff，不能伪装成 remote/vm runner 已执行
- repo-owned promotion entrypoint，例如：
  - `runtime/host-orchestrator/scripts/run-remote-non-gui-promotion.ps1`
  - `runtime/host-orchestrator/scripts/run-vm-gui-promotion.ps1`
  的 summary output

### platform compatibility green

额外需要：

- `AgentBridge` round-trip parity
- Hermes historical snapshot mapping 仍为绿
- repo-owned `runtime/host-orchestrator/scripts/run-hermes-parity.ps1` 结果保持 baseline doc、current known-good / boundary anchor、snapshot contract、known-good validator、以及 non-env-sensitive bring-up gates 一致

说明：

- `run-hermes-parity.ps1` 绿，只能证明 repo-side baseline / snapshot mapping 没漂移
- 如果当前 shell 仍只缺 `independent_key / independent_base_url` 这类 env-sensitive bring-up gate，不影响 repo-side slice 收口，但也不能单凭这一步宣称 `platform compatibility green`

### live accepted

额外需要：

- 真实 GPT-5.4 gateway readiness evidence
- `codex exec` minimum probe readiness evidence
- 非 mock worker 完成真实任务运行

## Build / Hotspot Promotion Rule

当前 `build` 与 `hotspot` 还是 `gate_na`。

只有在以下条件满足后，才升级为真实 gate：

1. 仓内已有 repo-owned build/hotspot command
2. 命令已写入 canonical verification surface
3. preflight 与 docs truth 已同步
4. 至少有一条 repo-side regression 测试覆盖升级后的 gate
