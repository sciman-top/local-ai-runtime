# AGENTS.md — local-ai-dev-orchestrator（共同项目规则 / Codex 直接读取）
**项目**: local-ai-dev-orchestrator
**承接来源**: `GlobalUser/AGENTS.md v9.54`
**适用范围**: 项目级（仓库根）
**最后更新**: 2026-07-06

## 1. 阅读指引
- 本文件只写本仓事实、门禁命令、证据路径、回滚入口和规则协同边界，不复述全局 `R/E` 正文。
- 本文件是 Codex / Claude 共同项目规则主体；Codex 直接读取，Claude 通过仓根 `CLAUDE.md` 的 `@AGENTS.md` thin wrapper 承接并只追加平台差异。
- 当前产品主线仍是 **通用本地 AI Dev Orchestrator**；`Governance Overlay` 是 cross-cutting 治理层，不替代 `Phase 1 -> Phase 6` 产品路线图。
- 全局规则真源在 `D:\CODE\governed-ai-coding-runtime`；本仓是受管目标仓试点，不负责全局规则分发，也不把自己改造成 governance hub。
- 四层边界固定为：`global rules -> project rules -> wrappers -> enforcement`。其中 deterministic enforcement 落在 `.codex`、`.claude/settings.json`、hooks、CI 或其他工具配置，不靠 prose 规则替代。

## A. 项目基线
### A.1 事实边界
- 机器可读规划真源：`docs/architecture/planning-status.json`。
- 当前产品 active queue：`PHASE-1-VERTICAL-SLICE`；当前 selector 预期结果：`promote_phase1_execution`；当前 live posture：`live_probe_ready`。
- 当前主线代码落点：`runtime/host-orchestrator`；不要新建平行顶层 `orchestrator/` 包。
- 调度真源：`.ai/state/control-plane.db`。
- 正式 task-level evidence 面：`.ai/runs/<run_id>/<task_id>/`。
- repo-level governance evidence index：`docs/change-evidence/README.md`；它不替代 task-level `evidence_index.json`。
- `.ai/config/orchestrator.yaml`、`.ai/config/workers.yaml`、`.ai/config/policies.yaml` 是 repo-owned runtime contract。
- `snapshots/agentbridge-20260628/` 与 `docs/platforms/hermes/` 只保留 Hermes/AgentBridge 兼容线与历史基线，不再定义当前主线实现真相。

### A.2 门禁命令与顺序（硬门禁）
- 固定顺序：`build -> test -> contract/invariant -> hotspot`。
- build：当前为 `gate_na`；替代验证是 `uv run --project .\runtime\host-orchestrator python -m pytest`，依据见 `docs/specs/acceptance-and-gates.md`。
- test：`uv run --project .\runtime\host-orchestrator python -m pytest`
- contract/invariant：`python .\scripts\verify-planning-status.py`
- hotspot：当前为 `gate_na`；替代验证是 repo-side `verifier + pytest + diff hygiene`，依据见 `docs/specs/acceptance-and-gates.md`。
- selector / governance quick feedback：`python .\scripts\select-next-work.py`
- release-style closeout：`pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`
- 若触及 `snapshots/agentbridge-20260628/`、兼容契约或 Hermes 历史面，还要补跑对应 snapshot gate：
  - `pwsh .\snapshots\agentbridge-20260628\scripts\test-agentbridge-contract.ps1`
  - `pwsh .\snapshots\agentbridge-20260628\scripts\test-hermes-bringup-gates.ps1`
  - `pwsh .\snapshots\agentbridge-20260628\scripts\test-known-good-snapshot.ps1`
  - `pwsh .\snapshots\agentbridge-20260628\scripts\verify-hermes-boundary.ps1`

### A.3 模块边界与失败分流
- `docs/`：authoritative product / architecture / roadmap / plan / backlog / specs。
- `runtime/host-orchestrator/`：当前 Python implementation seed 与测试面。
- `.ai/config/`：repo-owned config truth。
- `scripts/`：repo-level verifier、selector、reference refresh、governance preflight。
- `private-local/`：本机 secrets、探针、非正式 smoke；不提交其内容。
- 若 README、docs index、PRD、路线图、实施计划、任务清单、`AGENTS.md`/`CLAUDE.md` 口径不一致，直接阻断。
- 若用户级全局规则源与本仓项目规则冲突，先整合控制仓 `D:\CODE\governed-ai-coding-runtime` 的源文件、目标仓 `AGENTS.md` / `CLAUDE.md`、以及本仓真实 gate/evidence，再决定是否同步用户目录副本。

## B. Codex 平台差异
- Codex 项目规则真源是本文件；不要假定 `CLAUDE.md` 会被 Codex 自动加载。
- 规则变更后需要新 Codex run/session 复核；不要假定当前会话热加载。
- 最小诊断矩阵：`codex --version`、`codex --help`；需要追 rule load 时，再按当前 help / 日志能力取证。
- `.codex`、审批、沙箱、权限、exec policy 等属于 deterministic enforcement，不在本文件里复制配置正文。

## C. 项目规则协同契约
### C.1 四层边界
- global rules：`D:\CODE\governed-ai-coding-runtime\rules\global\codex\AGENTS.md` 与 `D:\CODE\governed-ai-coding-runtime\rules\global\claude\CLAUDE.md`。
- project rules：本仓根 `AGENTS.md`，负责 repo truth、真实 gate、证据路径、回滚入口。
- wrappers：本仓根 `CLAUDE.md`，只写 Claude 差异，不复制共同项目事实。
- enforcement：`.codex`、`.claude/settings.json`、`.claude/rules/`、hooks、CI、其他权限/工具配置；不提交 secrets 或个人 provider 实值。

### C.2 Global Rule -> Repo Action
- `R1`：改动前先定 `当前落点 -> 目标归宿`；本仓默认落点只能是 `runtime/host-orchestrator`、`docs/`、`.ai/config/`、`scripts/` 或兼容线历史面。
- `R2`：按小步闭环推进；docs/rules/scripts/evidence 必须同切片收口，不把无关 runtime lane 混进来。
- `R3`：若对 Hermes/AgentBridge 兼容线做止血补丁，必须明确它是兼容面临时收口，不得伪装成当前主线实现归宿。
- `R4`：低风险 docs/rules/evidence 可直接执行；live probe、provider/auth、本机凭据、历史兼容运行态改动必须先说明边界与回滚。
- `R5`：不新增平行顶层 orchestrator 包，不把本仓改写成 governance hub，不盲吸收控制仓的非必要 runtime 机制。
- `R6`：交付前遵守 `build -> test -> contract/invariant -> hotspot` 顺序；本仓当前 build/hotspot 真实 gate 缺席时按 `gate_na` 口径记录。
- `R7`：保持 canonical task/result/review 契约、`.ai` 目录真源、以及 Hermes 历史基线边界不被未授权破坏。
- `R8`：repo-level 变更留在 `docs/change-evidence/`；task-level 运行工件留在 `.ai/runs/<run_id>/<task_id>/`；两类证据不得混用。
- `E4`：`planning-status.json`、README/docs index、selector、preflight 一起承接当前 repo-side 健康/状态口径。
- `E5`：高漂移治理面先看 `references/` 与 `D:\CODE\governed-ai-coding-runtime` 的 companion 机制，再决定本仓是否吸收。
- `E6`：改动 contract/schema/runtime 或规则协同边界时，代码/文档/证据/回滚说明必须同切片更新。

### C.3 证据与回滚
- repo-level governance evidence：`docs/change-evidence/README.md`
- task-level runtime evidence：`.ai/runs/<run_id>/<task_id>/`
- 本仓项目规则回滚优先用 git：回滚 `AGENTS.md` / `CLAUDE.md` / README / docs / evidence 的同切片 diff，不把控制仓或用户目录副本的变更假装成已回滚。
- 控制仓协同命令：
  - `python D:\CODE\governed-ai-coding-runtime\scripts\verify-agent-rule-family.py`
  - `python D:\CODE\governed-ai-coding-runtime\scripts\verify-target-project-rules.py --targets local-ai-dev-orchestrator`

## D. 维护校验清单
- 结构保持 `1 / A / B / C / D`。
- `AGENTS.md` 保持共同项目规则主体；`CLAUDE.md` 必须是 thin wrapper，且首个非空行是独立 `@AGENTS.md`。
- 修改本仓项目规则后，最少复核：
  - `python .\scripts\verify-planning-status.py`
  - `python .\scripts\select-next-work.py`
  - `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`
- 修改控制仓全局规则源后，顺序固定为：
  - 先在 `D:\CODE\governed-ai-coding-runtime` 更新源文件与 verifier
  - 再同步用户目录级全局副本
  - 最后把 repo-specific truth 集成回本仓 `AGENTS.md` / `CLAUDE.md`
- 本仓不接受 blind overwrite：若控制仓 audit 报 drift，必须人工整合目标仓真实事实、wrapper 边界和 gate 证据后再收口。
