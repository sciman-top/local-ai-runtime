# 2026-07-06 Acceptance And Gates Contract

## Slice

- 固化 acceptance tiers 与 gate 顺序
- 显式声明 `mock green` / `live probe ready` 都不是新的顶层 acceptance tier
- preflight 与 PRD 改为引用同一套映射口径

## Evidence

- `docs/specs/acceptance-and-gates.md`
- `docs/product/orchestrator-prd.md`
- `scripts/governance/preflight.ps1`

## Boundary

这次只固化 contract，不代表 `build` / `hotspot` 已经升级为真实 gate。
