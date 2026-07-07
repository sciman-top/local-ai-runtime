# 20260707 Route Selection And Quota Closeout

## Goal

完成 `P5-T01` 的 repo-side `leases / retry / route / quota` 最小收口，但不伪装成已具备 live multi-worker scheduler 或 `multi-worker simulation green`。

## Repo-Side Changes

- canonical task 现在会真正消费显式 `worker_profile`
- runtime 在未显式指定时继续回落到 repo-owned `default_worker_profile`
- `result.json`、`dispatch_state.json`、以及 `route_decisions` 现在会 materialize `route_reason`
- `workers.yaml` 现在要求每个 profile 显式声明 `max_active_leases`
- selected profile 的 active lease 数超过 `max_active_leases` 时，runtime 会在 worker 前 fail closed 到 handoff

## Key Surfaces Updated

- `runtime/host-orchestrator/src/host_orchestrator/canonical_task.py`
- `runtime/host-orchestrator/src/host_orchestrator/config_runtime.py`
- `runtime/host-orchestrator/src/host_orchestrator/db.py`
- `runtime/host-orchestrator/src/host_orchestrator/host_local.py`
- `runtime/host-orchestrator/src/host_orchestrator/canonical_result.py`
- `runtime/host-orchestrator/src/host_orchestrator/agent_work_assets.py`
- `runtime/host-orchestrator/tests/test_wave1_execution.py`
- `.ai/config/workers.yaml`
- `docs/specs/*.md` truth surfaces
- `docs/architecture/planning-status.json`
- `README.md` / `docs/README.md`

## Truth Boundary

- 这次只完成 repo-side route/quota closeout
- 当前仍未落 live multi-worker scheduler
- 当前仍未升级到 `multi-worker simulation green`
- 当前仍未改变 `live probe ready` 与 `live accepted` 的边界

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest`
  - `57 passed`
- `python .\scripts\select-next-work.py`
  - `status=pass`
  - `next_action=promote_phase1_execution`
  - nested verifier `proof_ref=docs/change-evidence/20260707-route-selection-and-quota-closeout.md`
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit -Json`
  - `exit_code=0`
  - `build=gate_na`
  - `test=pass`
  - `contract/invariant=pass`
  - `hotspot=gate_na`
  - `Docs=pass`
  - `Scripts=pass`
  - `git diff --check=pass`

## Repo-Side Done

- `P5-T01` repo-side `leases / route / quota` 最小收口已完成
- 显式/默认 `worker_profile` 选择与 route reason 已进入正式证据面
- quota exhaustion 当前会在 worker 前 handoff，而不是伪装成多 worker 已调度

## Still Open

- `P5-T02` `multi-worker simulation`
- live planner wiring
- live heterogeneous review wiring
- `remote_non_gui` promotion evidence
- `live accepted`
