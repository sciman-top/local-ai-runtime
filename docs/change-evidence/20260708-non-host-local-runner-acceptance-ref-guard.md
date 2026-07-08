# 20260708 Non-Host-Local Runner Acceptance Ref Guard

## Scope

This slice hardens the follow-on boundary after `remote_non_gui` runner wiring readiness. It does not wire a real remote host runner, does not switch the default runtime entrypoint, does not change `current_active_queue`, and does not claim `platform compatibility green` or `live accepted`.

## What Changed

- `WorkerProfile` now accepts optional `runner_acceptance_ref`.
- Non-host-local profiles with `runner_wired=true` must bind a repo-relative, existing `runner_acceptance_ref` during runtime config loading.
- Missing, absolute, escaping, or missing-on-disk acceptance refs fail closed before task execution.
- The temporary fake-runner tests now create a repo-relative acceptance stub before enabling `runner_wired=true`.
- Committed `remote_non_gui_probe` and `vm_gui_probe` still keep `runner_wired=false`.

## Verification

- Target RED was observed first: `test_non_host_local_runner_wired_requires_acceptance_ref` failed because `runner_wired=true` without `runner_acceptance_ref` did not raise `RuntimeConfigError`.
- Target GREEN: `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_remote_non_gui_promotion.py` -> `6 passed`.
- Full test gate: `uv run --project .\runtime\host-orchestrator python -m pytest` -> `119 passed`.
- Contract / invariant gate: `python .\scripts\verify-planning-status.py` -> `status=pass`; `proof_ref=docs/change-evidence/20260708-non-host-local-runner-acceptance-ref-guard.md`.
- Next-work selector: `python .\scripts\select-next-work.py` -> `status=pass`; `next_action=promote_phase1_execution`; embedded preflight passed.
- Build gate: `gate_na`; reason and substitute verification remain governed by `docs/specs/acceptance-and-gates.md`; substitute verification is the host-orchestrator pytest suite above.
- Hotspot gate: `gate_na`; reason and substitute verification remain governed by `docs/specs/acceptance-and-gates.md`; substitute verification is verifier + pytest + diff hygiene.

## Boundary

- repo-side done: acceptance-ref guard prevents a non-host-local profile from bypassing handoff by setting only `runner_wired=true`.
- still open: real remote host runner, real remote host acceptance artifacts, platform compatibility green, vm_gui runner, GUI-only workload acceptance, runtime_v2 default cutover, and live accepted.
