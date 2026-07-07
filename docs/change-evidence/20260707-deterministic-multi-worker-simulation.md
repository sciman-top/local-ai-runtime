# 20260707 Deterministic Multi-Worker Simulation

## Goal

完成 `P5-T02` 的 repo-side deterministic multi-worker simulation，但不把它写成 live 多 worker scheduler、`platform compatibility green`、或 `live accepted`。

## Repo-Side Changes

- 新增 `runtime/host-orchestrator/src/host_orchestrator/multi_worker_simulation.py`
- 新增 CLI entrypoint：
  - `uv run --project .\runtime\host-orchestrator python -m host_orchestrator --run-multi-worker-simulation`
- 新增脚本入口：
  - `runtime/host-orchestrator/scripts/run-multi-worker-simulation.ps1`
- deterministic simulation 现在会覆盖：
  - explicit `worker_profile` route
  - default `worker_profile` route
  - lease quota handoff
  - review handoff
  - retry request + attempt increment + rerun closeout

## Fresh Local Evidence

- command:
  - `pwsh -NoProfile -ExecutionPolicy Bypass -File .\runtime\host-orchestrator\scripts\run-multi-worker-simulation.ps1 -RunId multi-worker-sim-20260707-3`
- summary path:
  - `D:\CODE\local-ai-dev-orchestrator\private-local\multi-worker-simulations\multi-worker-sim-20260707-3\multi-worker-simulation-summary.json`
- key summary:
  - `scenario_count = 4`
  - `task_run_count = 5`
  - `terminal_task_count = 4`
  - `route_decision_count = 5`
  - `retry_event_count = 1`
  - `active_lease_count = 0`
  - `worker_statuses = 5 idle workers`
  - `state_counts = completed:2 / waiting_handoff:1 / needs_review:1`
  - `retried_task_ids = ["TASK-20260707-simulation-retry"]`
- notable task outcomes:
  - explicit route reason = `repo-owned worker_profile=wave1_smoke selected from canonical task`
  - quota handoff reason includes `lease_quota_exhausted worker_profile=local_maint active_leases=2 max_active_leases=1`
  - retry scenario final `attempt = 2` and `final_state = completed`

## Truth Boundary

- 这次完成的是 repo-side deterministic simulation
- 当前仍未落 live 多 worker scheduler
- 当前仍未落 `remote_non_gui` runner
- 当前仍未升级为 `live accepted`

## Verification

- `python .\scripts\verify-planning-status.py`
  - `status=pass`
  - `proof_ref=docs/change-evidence/20260707-deterministic-multi-worker-simulation.md`
- `uv run --project .\runtime\host-orchestrator python -m pytest`
  - `59 passed`
- `python .\scripts\select-next-work.py`
  - `status=pass`
  - `next_action=promote_phase1_execution`
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

- `P5-T02` deterministic multi-worker simulation suite 已落地
- simulation summary contract 已落地并可重跑
- planning/docs/evidence truth 已切到新的 next gap

## Still Open

- `P5-T03` `remote_non_gui` promotion evidence
- live planner wiring
- live heterogeneous review wiring
- platform compatibility green
- live accepted
