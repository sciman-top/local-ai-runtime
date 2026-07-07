# 2026-07-07 VM-GUI Conditional Promotion Evidence

## Slice

- 本次切片收口 `P6-T03`
- 目标不是落 vm runner，而是把 GUI-only 条件晋升边界固定成 repo-owned 可重跑证据

## Code Points

- `runtime/host-orchestrator/src/host_orchestrator/vm_gui_promotion.py`
- `runtime/host-orchestrator/src/host_orchestrator/cli.py`
- `runtime/host-orchestrator/scripts/run-vm-gui-promotion.ps1`
- `runtime/host-orchestrator/tests/test_vm_gui_promotion.py`
- `.ai/config/workers.yaml`

## Evidence

- repo-owned summary:
  - `private-local/vm-gui-promotions/vm-gui-promotion-20260707-1/vm-gui-promotion-summary.json`
- current proof points:
  - default GUI-only request now fails closed with `execution_lane=vm_gui; requires_gui=true`
  - explicit `vm_gui_probe` now fails closed with `requires_gui=true; host_runtime=host_local selected_lane=vm_gui runner_not_wired worker_profile=vm_gui_probe`

## What Verified

- `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_vm_gui_promotion.py runtime/host-orchestrator/tests/test_scaffold.py`：pass
- `uv run --project .\runtime\host-orchestrator python -m host_orchestrator --repo-root D:\CODE\local-ai-dev-orchestrator --run-vm-gui-promotion --vm-gui-promotion-run-id vm-gui-promotion-20260707-1`：pass
  - `scenario_count = 2`
  - `task_run_count = 2`
  - `route_decision_count = 2`
  - `active_lease_count = 0`
  - `worker_lanes = {host_local, vm_gui}`
  - `state_counts = {waiting_handoff: 2}`
- `pwsh .\runtime\host-orchestrator\scripts\run-vm-gui-promotion.ps1 -RunId vm-gui-promotion-20260707-2`：pass

## Boundary

- 这次 closeout 只证明 repo-side `vm_gui` conditional promotion evidence 已落地
- 这不等于：
  - vm runner 已落地
  - 真实 GUI-only workload acceptance 已完成
  - `platform compatibility green`
  - `live accepted`

## Next

- live planner/review sidecar 与 non-host_local runner wiring
