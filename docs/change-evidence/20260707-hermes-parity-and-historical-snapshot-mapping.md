# 2026-07-07 Hermes Parity And Historical Snapshot Mapping

## Slice

- 本次切片合并收口 `P6-T01` 与 `P6-T02`
- 目标不是 live 重新 bring-up，而是把 Hermes certified baseline、historical snapshot mapping、以及 container lifecycle boundary 收进同一条 repo-owned 可重跑闭环

## Code Points

- `runtime/host-orchestrator/src/host_orchestrator/hermes_parity.py`
- `runtime/host-orchestrator/src/host_orchestrator/cli.py`
- `runtime/host-orchestrator/scripts/run-hermes-parity.ps1`
- `runtime/host-orchestrator/tests/test_hermes_parity.py`

## Evidence

- repo-owned summary:
  - `private-local/hermes-parity/hermes-parity-20260707-1/hermes-parity-summary.json`
- current mapped anchors:
  - `snapshots/agentbridge-20260628/docs/known-good-20260628-225738-431.json`
  - `snapshots/agentbridge-20260628/docs/verify-hermes-boundary-20260628-225841-414.json`
- boundary docs kept in sync:
  - `docs/platforms/hermes/README.md`
  - `docs/platforms/hermes/当前交接摘要.md`
  - `docs/platforms/hermes/接手检查单.md`
  - `snapshots/agentbridge-20260628/docs/implementation-status.md`

## What Verified

- `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_hermes_parity.py runtime/host-orchestrator/tests/test_scaffold.py`：pass
- `uv run --project .\runtime\host-orchestrator python -m host_orchestrator --repo-root D:\CODE\local-ai-dev-orchestrator --run-hermes-parity --hermes-parity-run-id hermes-parity-20260707-1`：pass
  - `contract_ok = true`
  - `known_good_snapshot_ok = true`
  - `anchor_alignment_ok = true`
  - `historical_snapshot_mapping_ok = true`
  - `container_lifecycle_ok = true`
  - current known-good / boundary anchor 三面一致
- `pwsh .\runtime\host-orchestrator\scripts\run-hermes-parity.ps1 -RunId hermes-parity-20260707-2`：pass

## Boundary

- 这次 closeout 只证明 repo-side Hermes parity / historical snapshot mapping verifier 已落地
- 当前 shell 中 `test-hermes-bringup-gates.ps1` 仍只缺 `independent_key / independent_base_url` 两个 env-sensitive gate
- 这不等于：
  - remote runner 已落地
  - `platform compatibility green`
  - `live accepted`
  - live planner/review sidecar 已接线

## Next

- `P6-T03 vm_gui conditional promotion evidence`
