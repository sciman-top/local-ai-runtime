# 20260708 Remote Non-GUI Runner Wiring Readiness

## Scope

This slice adds the repo-side readiness contract for future `remote_non_gui` runner wiring. It does not wire a real remote host runner, does not switch the default runtime entrypoint, does not change `current_active_queue`, and does not claim `platform compatibility green` or `live accepted`.

## What Changed

- `WorkerProfile` now accepts an optional `runner_wired` boolean, defaulting to `false`.
- Committed `remote_non_gui_probe` and `vm_gui_probe` profiles explicitly keep `runner_wired: false`.
- `HostLocalRunner` continues to fail closed to pre-worker handoff when a non-host-local profile is selected without `runner_wired=true`.
- Temporary test config can set `runner_wired=true` to prove the runtime calls an injected runner instead of stopping at handoff.
- Runner failure on that wired branch records failed dispatch and does not write a successful `result.json`.

## Verification

- Target RED was observed first: `test_remote_non_gui_promotion.py` failed because the wired profile still stopped before worker execution.
- Target GREEN: `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_remote_non_gui_promotion.py` -> `5 passed`.
- Full test gate: `uv run --project .\runtime\host-orchestrator python -m pytest` -> `118 passed`.
- Contract/invariant: `python .\scripts\verify-planning-status.py` -> `status=pass`, `proof_ref=docs/change-evidence/20260708-remote-non-gui-runner-wiring-readiness.md`.
- Selector: `python .\scripts\select-next-work.py` -> `status=pass`, `next_action=promote_phase1_execution`.
- Governance preflight: `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit` -> `exit_code=0`.
- Diff hygiene: `git diff --check` -> pass.
- Build gate is `gate_na` by current repo policy; substitute verification is full pytest plus planning verifier.
- Hotspot gate is `gate_na` by current repo policy; substitute verification is verifier plus pytest plus diff hygiene.

## Boundary

- repo-side done: runner wiring readiness branch, fail-closed default, and fake-runner success/failure proofs are implemented and tested.
- still open: real remote host runner, remote host acceptance, platform compatibility green, vm_gui runner, GUI-only workload acceptance, runtime_v2 default cutover, and live accepted.
