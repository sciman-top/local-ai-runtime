# 20260708 Non-Host-Local Runner Acceptance Schema

## Scope

This slice hardens `runner_acceptance_ref` from an existence-only guard into a machine-checkable acceptance payload contract. It does not wire a real remote runner, does not set committed `runner_wired=true`, does not switch `runtime.active_version`, does not change `current_active_queue`, and does not claim `platform compatibility green` or `live accepted`.

## What Changed

- Added `host_orchestrator.runner_acceptance` with reusable validation for `non_host_local_runner_acceptance.v1`.
- Runtime config loading now requires a non-host-local `runner_wired=true` profile to reference a JSON object with:
  - `schema_version = non_host_local_runner_acceptance.v1`
  - `acceptance_status = accepted`
  - `worker_profile / lane / runner_kind` matching the selected worker profile
  - non-empty `accepted_by / accepted_at / acceptance_scope`
  - non-empty `evidence_refs`
- Added `templates/non-host-local-runner-acceptance.schema.json` and `templates/non-host-local-runner-acceptance.example.json`.
- Extended `scripts/validate-agent-work-assets.py` to validate the runner acceptance example.
- The fake injected-runner tests now use the same acceptance payload shape.

## Verification

- Target RED was observed first: `test_non_host_local_runner_wired_requires_valid_acceptance_payload` failed because invalid `acceptance_status / worker_profile / lane / runner_kind / evidence_refs` payloads did not raise `RuntimeConfigError`.
- Target GREEN: `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_remote_non_gui_promotion.py::test_non_host_local_runner_wired_requires_valid_acceptance_payload -q` -> `5 passed`.
- Remote runner readiness regression: `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_remote_non_gui_promotion.py -q` -> `11 passed`.
- Template asset check: `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_agent_work_assets.py::test_runner_acceptance_template_aligns_with_non_host_local_guard -q` -> `1 passed`.
- Asset validator: `uv run --project .\runtime\host-orchestrator python .\scripts\validate-agent-work-assets.py` -> `status=pass`; includes `runner_acceptance`.
- Full test gate: `uv run --project .\runtime\host-orchestrator python -m pytest` -> `125 passed`.
- Contract / invariant gate: `python .\scripts\verify-planning-status.py` -> `status=pass`; `proof_ref=docs/change-evidence/20260708-non-host-local-runner-acceptance-schema.md`.
- Next-work selector: `python .\scripts\select-next-work.py` -> `status=pass`; `next_action=promote_phase1_execution`; embedded preflight passed with `125 passed`.
- Release-style preflight: `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit` -> pass; test `125 passed`; contract/docs/scripts/diff hygiene passed.
- Build gate: `gate_na`; reason and substitute verification remain governed by `docs/specs/acceptance-and-gates.md`; substitute verification is the host-orchestrator pytest suite above.
- Hotspot gate: `gate_na`; reason and substitute verification remain governed by `docs/specs/acceptance-and-gates.md`; substitute verification is verifier + pytest + diff hygiene.

## Boundary

- repo-side done: `runner_acceptance_ref` now needs a schema-valid payload bound to the selected non-host-local worker profile before `runner_wired=true` can bypass handoff.
- still open: real remote host runner, real remote host acceptance artifacts, platform compatibility green, vm_gui runner, GUI-only workload acceptance, runtime_v2 default cutover, and live accepted.
