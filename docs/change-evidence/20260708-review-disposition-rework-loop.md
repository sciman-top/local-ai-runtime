# 20260708 Review Disposition Rework Loop

## Scope

This slice adds a repo-side operator/reviewer disposition entrypoint for tasks that already stopped at `needs_review`. It does not create or sign real operator approval evidence, does not claim `live accepted`, does not approve non-host-local runner acceptance, and does not switch `runtime.active_version`.

## What Changed

- `task_lifecycle.py` now supports `record_review_disposition` for `needs_review` tasks.
- `host-orchestrator --record-review-disposition <task_id> --review-disposition approve|revise|reject` records the disposition without bypassing the live acceptance boundary.
- `approve` marks the repo-side review hold as `completed` while keeping `live accepted` explicitly open.
- `revise` increments `attempt`, records `resume_point / retry_rewind = worker_execution`, and requeues the task through the existing `resumed` retry path.
- `reject` records the review outcome as `cancelled`, leaving explicit operator resume/retry as the follow-up path.
- `dispatch_state` schema and validator now allow optional `review_disposition` and `review_disposition_at` fields.

## Verification

- Lifecycle target: `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_lifecycle_ops.py -q` -> `6 passed`.
- Asset/schema target: `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_agent_work_assets.py -q` -> `8 passed`.
- Asset validator: `uv run --project .\runtime\host-orchestrator python .\scripts\validate-agent-work-assets.py` -> `status=pass`.
- Full test gate: `uv run --project .\runtime\host-orchestrator python -m pytest` -> `133 passed`.
- Planning-status verifier: `python .\scripts\verify-planning-status.py` -> `status=pass`; proof ref is this evidence file.
- Next-work selector: `python .\scripts\select-next-work.py` -> `status=pass`; next action remains `promote_phase1_execution`.
- Governance preflight: `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit` -> pass with test / contract / docs / scripts / diff hygiene pass.
- Diff hygiene: `git diff --check` -> pass.
- Build gate remains `gate_na` because the repo-owned build gate is not defined yet for the current Hermes -> AgentBridge -> Codex runtime mainline; alternative verification is the full pytest suite, per `docs/specs/acceptance-and-gates.md`.
- Hotspot gate remains `gate_na` because the repo-owned hotspot gate is not defined yet for the current Hermes -> AgentBridge -> Codex runtime mainline; alternative verification is verifier + pytest + diff hygiene, per `docs/specs/acceptance-and-gates.md`.

## Boundary

- repo-side done: a `needs_review` task now has an auditable disposition path for approve / revise / reject, and revise feeds the existing retry/rework loop.
- still open: real remote host runner acceptance, real remote host artifacts, platform compatibility green, vm_gui runner, GUI-only workload acceptance, runtime_v2 default cutover, and live accepted.
