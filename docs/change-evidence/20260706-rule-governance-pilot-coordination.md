# 20260706 Rule Governance Pilot Coordination

## Summary

本次切片把本仓正式接入规则治理试点，但不改变当前产品主线和 active queue：

- 本仓继续是 **通用本地 AI Dev Orchestrator** 主仓
- 当前 active queue 仍然是 `PHASE-1-VERTICAL-SLICE`
- 当前 selector 预期结果仍然是 `promote_phase1_execution`
- 本仓只是受管目标仓试点，不承担控制仓职责

## Landed Surfaces

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/README.md`
- `docs/architecture/orchestrator-target-architecture.md`
- `docs/product/orchestrator-prd.md`
- `docs/roadmap/orchestrator-roadmap.md`
- `docs/plans/orchestrator-implementation-plan.md`
- `docs/backlog/orchestrator-task-list.md`
- `docs/change-evidence/README.md`

## Adopted Boundaries

- `AGENTS.md` 是共同项目规则真源，只写 repo truth、真实 gate、证据与回滚。
- `CLAUDE.md` 是 thin wrapper；首个非空行是独立 `@AGENTS.md`，不复制共同正文。
- 全局规则真源在 `D:\CODE\governed-ai-coding-runtime`；本仓只吸收 `Codex + Claude` global rule source 与 target-project audit 机制。
- settings / hooks / permissions / MCP / CI 属 deterministic enforcement，不作为普通规则副本同步。

## Not Absorbed

- 没有把本仓改造成规则控制仓或 governance hub。
- 没有恢复 target-repo blind rule distribution。
- 没有同步或提交任何带 secrets 的个人 settings 实值。
- 没有改写 `planning-status.json`、phase 编号或 selector 规则。

## Verification

- `python D:\CODE\governed-ai-coding-runtime\scripts\verify-target-project-rules.py --targets local-ai-dev-orchestrator`
- `python .\scripts\verify-planning-status.py`
- `python .\scripts\select-next-work.py`
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`

## Rollback

- `git revert` 本次 `AGENTS.md` / `CLAUDE.md` / README / docs / evidence 的同切片变更
- 不把控制仓或用户目录全局规则副本的状态假装成已在本仓回滚；控制仓与本仓分别回滚、分别复验
