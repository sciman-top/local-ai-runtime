# 2026-07-06 Run State And Handoff Foundation

## Slice

- 补齐 `run_id / attempt / resume_point / retry_rewind / handoff_required / next_action` 的契约基础
- 明确 `run-state-and-handoff.md` 属于 `Phase 1-4` foundation

## Evidence

- `docs/specs/run-state-and-handoff.md`
- `docs/specs/state-and-db.md`

## Boundary

这不表示 `Phase 5` 已开始；multi-worker 扩展 gate 仍以 `state-and-db.md` 的条件为准。
