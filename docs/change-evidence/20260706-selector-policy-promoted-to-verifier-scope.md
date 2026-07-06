# 2026-07-06 Selector Policy Promoted To Verifier Scope

## Slice

- `next-work-selection-policy.json` 进入 authoritative/verifier 视野
- verifier 开始校验 `allowed_next_actions`、`selection_order`、`required_entrypoints`、`required_doc_refs`、`review_expires_at`

## Evidence

- `docs/architecture/planning-status.json`
- `docs/architecture/next-work-selection-policy.json`
- `scripts/verify-planning-status.py`

## Boundary

verifier 只校验 `review_expires_at` 的存在性与 ISO 日期形状；是否过期仍交给 `select-next-work.py` 的治理分支处理。
