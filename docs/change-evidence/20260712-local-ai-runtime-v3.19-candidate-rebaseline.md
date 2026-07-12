# Local AI Runtime v3.19 Candidate Planning Rebaseline

## Goal

把历次讨论收敛出的完整 v3.19 candidate 投影到仓库 PRD、架构、路线图、实施计划、任务清单、验收合同、planning status、selector 和 verifier，形成可由 AI 逐项执行的预批准控制面，同时不伪造 Baseline Approval、Truth Reset、runtime 实现或 P2 admission。

## Decision

- 唯一候选 ID：`local-ai-runtime-0.2-v3.19`
- 状态：`baseline_candidate`
- 决议：`request_changes_until_normative_package_closure`
- 阻断阶段：`baseline_approval`
- 当前队列：`LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE`
- 当前 selector：`close_baseline_normative_package_first`
- 当前唯一 ready task：`LAR-P0A-001`

v3.19 正文完整不等于 normative package 完整。当前 inventory 有 14 个 required artifact，其中只有 candidate source present，13 个仍 missing；因此 `approval_eligible=false`、`approval_state.active=false`。

## Changes

### Candidate source and planning truth

- 新增完整、自包含 v3.19 candidate 正文。
- 新增 non-normative preapproval package inventory，记录 source identity、lineage 状态、artifact producer 和真实缺口。
- 新增 31 个 machine work item，覆盖 P0A、独立 Baseline Approval、P0B-P1、独立 Full Q0 和 P2-P5；每项包含依赖、前置、范围、主要文件、逐项 acceptance、命令、evidence、rollback、stop conditions 和 prohibited actions。
- planning status 升级到 2.0，机械区分 approval、Truth Reset、Legacy Guard、implementation、Implementation Acceptance、Full Q0 和 P2。

### Product and engineering projection

- 重写 README/docs index、PRD、target architecture、roadmap、implementation plan、backlog 和 acceptance contract。
- 明确当前 `runtime/host-orchestrator` 仍是现行内核，experimental runtime_v2/AgentBridge/Hermes 只作 legacy/迁移输入。
- 明确批准后目标为 `runtime/local-ai-runtime` 的 Unified Native + Batch；批准和 Legacy Guard 前禁止创建或 claim。
- 最小更新根 AGENTS，只授权 candidate closure；该更新不是 P0B Truth Reset。

### Mechanical governance

- verifier 改为数据驱动校验 candidate bytes/hash、byte format、inventory、work-item DAG、producer links、selector policy、文档契约、filesystem truth 和非法阶段组合。
- selector 改为只读快速决策；不再内嵌 release preflight，不写状态。
- 新增 planning governance tests，覆盖 truthful state、expected selection、exact bytes/hash、forged approval、skipped Truth Reset 和 hash drift。
- preflight 改为记录 candidate-planning build/hotspot N/A 到期条件，并验证 selector。

## Truth Boundaries

- 没有创建 `BaselineApprovalRecord`、`ImplementationAcceptanceRecord` 或 `FullQ0Record`。
- 没有创建 `runtime/local-ai-runtime`。
- 没有修改 `.ai/config`、legacy DB、task evidence、worker profile、default runtime entrypoint、auth/provider 或 scheduled task。
- 没有执行 live Codex、Git publication、repo ownership、cutover 或 rollback。
- Planning verifier pass 只证明状态陈述真实，不证明后续门绿色。

## Verification

### Candidate identity

- `Get-Item`：`111952` bytes。
- `Get-FileHash -Algorithm SHA256`：`275306D2E88BAAFA803170EE4EF99FB822C4E13769721B806805B834BB9D7670`。
- Byte checks：UTF-8、无 BOM/CR/NUL/HTAB、NFC、无行尾空白、恰好一个末尾 LF。

### Structured assets

- PowerShell `ConvertFrom-Json` 解析以下 4 个文件：pass。
  - `docs/architecture/planning-status.json`
  - `docs/architecture/next-work-selection-policy.json`
  - `docs/specs/local-ai-runtime-0.2-normative-package.json`
  - `docs/plans/local-ai-runtime-0.2-work-items.json`
- `python -m py_compile scripts/verify-planning-status.py scripts/select-next-work.py`：exit 0。

### Targeted governance tests

Command：

```powershell
uv run --project ./runtime/host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_planning_governance.py -q
```

Result：`6 passed in 1.88s`。

### Full legacy regression

Command：

```powershell
uv run --project ./runtime/host-orchestrator python -m pytest
```

Result：`164 passed in 45.98s`。

### Planning invariant

Command：`python scripts/verify-planning-status.py`

Result：exit 0；`baseline_status=baseline_candidate`、`approval_active=false`、`missing_artifact_count=13`、`current_work_item_id=LAR-P0A-001`、`truth_reset_performed=false`、`implementation_started=false`、`p2_admitted=false`。

### Next-work selector

Command：`python scripts/select-next-work.py`

Result：exit 0；`next_action=close_baseline_normative_package_first`、`current_work_item_id=LAR-P0A-001`、`side_effects_performed=false`、`preflight_run=false`。

### Release-style preflight

Command：

```powershell
pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit
```

Final result：exit 0；inner pytest `164 passed in 47.74s`；contract/invariant、planning selection、script parse 和 diff hygiene pass。Verifier 同时确认 `work_item_count=31` 和完整 P2-P5 rollout flags。

N/A：

- build：当前是 candidate planning，新 package 不存在；替代验证为 host-orchestrator full pytest；到期 `LAR-P0D-001`。
- hotspot：当前不改 runtime hot path；替代验证为 planning tests + verifier + selector + diff hygiene；到期为 `LAR-P0D-001` 后首个 executable slice。

## Risks And Open Work

- v3.17 exact archived bytes 当前仍缺失，provisional transcript hash 不能升格；`LAR-P0A-001` 必须 fail closed 或取得真实 source。
- 13 个 normative artifact 仍缺失；现在不能批准或实现。
- 当前 project/runtime 文档中的旧 Phase 1/runtime_v2 内容作为 legacy 历史保留；它们不在 v3.19 authoritative target set 中，P0B/P0C 再按批准后的迁移边界处理。
- 本 evidence 是普通 repo-level change note，不是 v3.19 `ReviewEvidenceIndex.v1`，不能替代 P0A-REVIEW。

## Rollback

只回滚本次 candidate planning projection：v3.19 candidate、package inventory、machine work items、authoritative docs、planning status/policy、verifier/selector/preflight、planning tests、AGENTS 最小预批准更新和本 evidence/index。不要修改或恢复 `.ai` state、legacy evidence、runtime behavior 或用户其他变更。
