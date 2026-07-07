# 20260707 Remote Non-GUI Promotion Evidence

## Goal

完成 `P5-T03` 的 repo-side `remote_non_gui` promotion evidence，但不把它写成 remote runner 已落地、`platform compatibility green`、或 `live accepted`。

## Repo-Side Changes

- `.ai/config/workers.yaml` 新增 repo-owned `remote_non_gui_probe` profile
- `HostLocalRunner` 现在会对 selected `worker_profile.lane != host_local` 的场景 fail closed 到 handoff
- 新增 deterministic promotion suite：
  - `runtime/host-orchestrator/src/host_orchestrator/remote_non_gui_promotion.py`
- 新增 CLI entrypoint：
  - `uv run --project .\runtime\host-orchestrator python -m host_orchestrator --run-remote-non-gui-promotion`
- 新增脚本入口：
  - `runtime/host-orchestrator/scripts/run-remote-non-gui-promotion.ps1`
- promotion suite 当前覆盖：
  - baseline `remote_non_gui` request + default local profile lane mismatch
  - explicit `remote_non_gui_probe` profile selection + fail-closed handoff before worker execution

## Fresh Local Evidence

- command:
  - `pwsh -NoProfile -ExecutionPolicy Bypass -File .\runtime\host-orchestrator\scripts\run-remote-non-gui-promotion.ps1 -RunId remote-non-gui-promotion-20260707-1`
- summary path:
  - `D:\CODE\local-ai-dev-orchestrator\private-local\remote-non-gui-promotions\remote-non-gui-promotion-20260707-1\remote-non-gui-promotion-summary.json`
- key summary:
  - `scenario_count = 2`
  - `task_run_count = 2`
  - `terminal_task_count = 2`
  - `route_decision_count = 2`
  - `active_lease_count = 0`
  - `worker_statuses = 2 idle workers`
  - `worker_lanes = host_local + remote_non_gui`
  - `state_counts = waiting_handoff:2`
- notable task outcomes:
  - baseline scenario keeps default route reason = `repo default worker_profile=local_maint selected from orchestrator.yaml`
  - baseline handoff reason includes `execution_lane=remote_non_gui`
  - explicit promotion scenario route reason = `repo-owned worker_profile=remote_non_gui_probe selected from canonical task`
  - explicit promotion scenario handoff reason includes `host_runtime=host_local selected_lane=remote_non_gui runner_not_wired worker_profile=remote_non_gui_probe`

## Truth Boundary

- 这次完成的是 repo-side `remote_non_gui` promotion evidence
- 当前仍未落 remote runner
- 当前仍未落 `platform compatibility green`
- 当前仍未升级为 `live accepted`

## Verification

- `python .\scripts\verify-planning-status.py`
  - `status=pass`
  - `proof_ref=docs/change-evidence/20260707-remote-non-gui-promotion-evidence.md`
- `uv run --project .\runtime\host-orchestrator python -m pytest`
  - `62 passed`
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

- `P5-T03` remote_non_gui promotion evidence suite 已落地
- non-host-local selected lane 当前不会被 `host_local` 伪装成本地已执行
- planning/docs/evidence truth 已切到新的 next gap

## Still Open

- remote runner implementation
- `P6-T01` Hermes parity closeout
- `P6-T02` historical snapshot mapping
- `P6-T03` vm_gui conditional promotion evidence
- live planner wiring
- live heterogeneous review wiring
- `platform compatibility green`
- `live accepted`
