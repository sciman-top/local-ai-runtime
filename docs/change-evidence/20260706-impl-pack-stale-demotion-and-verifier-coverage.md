# 2026-07-06 impl_pack Stale Demotion And Verifier Coverage

## Slice

- `impl_pack` 中的 stale/legacy 文件完成降级标识
- verifier 开始机器检查这些标识与 `00_README_FIRST.md` 的阅读顺序

## Evidence

- `ai_dev_orchestrator_impl_pack/00_README_FIRST.md`
- `ai_dev_orchestrator_impl_pack/03_IMPLEMENTATION_ROADMAP.md`
- `ai_dev_orchestrator_impl_pack/05_TASK_CONTRACT_SCHEMA.json`
- `ai_dev_orchestrator_impl_pack/05_SAMPLE_TASKS.json`
- `ai_dev_orchestrator_impl_pack/06_STATE_MACHINE.md`
- `ai_dev_orchestrator_impl_pack/07_AGENT_ROLE_MATRIX.md`
- `ai_dev_orchestrator_impl_pack/08_AGENTS.md`
- `ai_dev_orchestrator_impl_pack/09_CODEX_MASTER_PROMPT.md`
- `ai_dev_orchestrator_impl_pack/10_GLM_REVIEW_PROMPT.md`
- `ai_dev_orchestrator_impl_pack/14_HANDOFF_MESSAGE_TO_CODEX.md`
- `scripts/verify-planning-status.py`

## Boundary

`impl_pack` 仍可作为参考资产，但不再定义 runtime truth，也不替代 `P1-T01/T02/T03` 的代码切片。
