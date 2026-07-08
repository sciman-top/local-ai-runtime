# 20260708 Remote Non-GUI Handoff Receipt

## Scope

This slice hardens the repo-side `remote_non_gui` fail-closed boundary. It does not wire a real remote runner, does not switch the default runtime entrypoint, does not change `current_active_queue`, and does not claim `live accepted`.

## What Changed

- Pre-worker handoff now writes `.ai/runs/<run_id>/<task_id>/handoff_receipt.json`.
- `result.json`, `dispatch_state.json`, `closeout_bundle.json`, and `evidence_index.json` now reference the handoff receipt when that path is used.
- `remote_non_gui` promotion summary now records `handoff_receipt_ref`, `handoff_reason_codes`, and `worker_execution_attempted`.
- Template/schema assets now include `handoff-receipt.example.json` and `handoff-receipt.schema.json`.

## Verification

- Target RED was observed first: `test_remote_non_gui_promotion.py` failed on missing `handoff_receipt_ref` / outcome fields.
- Target GREEN: `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_remote_non_gui_promotion.py runtime\host-orchestrator\tests\test_agent_work_assets.py` -> `10 passed`.

## Boundary

- repo-side done: structured handoff receipt and summary fields are implemented and tested.
- still open: real `remote_non_gui` runner wiring, platform compatibility green, and live acceptance.
