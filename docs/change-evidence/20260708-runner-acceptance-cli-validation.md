# 20260708 Runner Acceptance CLI Validation

## Scope

This slice adds an independent CLI validation entrypoint for candidate non-host-local runner acceptance JSON before changing committed `workers.yaml`. It does not wire a real remote runner, does not set committed `runner_wired=true`, does not create real operator acceptance evidence, does not switch `runtime.active_version`, does not change `current_active_queue`, and does not claim `platform compatibility green` or `live accepted`.

## What Changed

- Added `host-orchestrator --validate-runner-acceptance <candidate.json> --worker-profile <profile>`.
- Added the `host-orchestrator` console script declaration to package metadata so the documented CLI shape is directly runnable.
- The command loads the repo-owned worker profile, validates the candidate payload with the same `non_host_local_runner_acceptance.v1` rules used by runtime config loading, and prints a JSON result.
- CLI output explicitly includes `validation_only=true` and `runner_executed=false`.
- The reported `acceptance_ref` stays repo-style with `/` separators, while `acceptance_path` remains the local filesystem path.
- Mismatched profile/lane/runner kind returns `status=fail` without executing any runner.
- Added `*.toml text eol=lf` to keep the package metadata diff hygiene aligned with the repo's LF policy.

## Verification

- Target RED was observed first: the new CLI tests initially failed with argparse `unrecognized arguments` before the CLI entrypoint existed.
- Target failure after first implementation was also observed: `acceptance_ref` was rendered with Windows path separators, causing the CLI contract test to fail.
- Console script RED was observed: `uv run --project .\runtime\host-orchestrator host-orchestrator --help` failed with `program not found` before package metadata declared the script.
- Target GREEN: `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_remote_non_gui_promotion.py::test_cli_validates_runner_acceptance_ref_against_worker_profile runtime\host-orchestrator\tests\test_remote_non_gui_promotion.py::test_cli_runner_acceptance_validation_fails_on_profile_mismatch -q` -> `2 passed`.
- Console script metadata check: `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_cli_entrypoint.py -q` -> `1 passed`.
- CLI help smoke: `uv run --project .\runtime\host-orchestrator host-orchestrator --help` -> exit 0; help includes `--validate-runner-acceptance`.
- CLI validation smoke with example-only template: `uv run --project .\runtime\host-orchestrator host-orchestrator --repo-root . --worker-profile remote_non_gui_probe --validate-runner-acceptance templates\non-host-local-runner-acceptance.example.json` -> `status=pass`, `runner_wired=false`, `validation_only=true`, `runner_executed=false`.
- Remote runner readiness regression: `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_remote_non_gui_promotion.py -q` -> `13 passed`.
- Template asset check: `uv run --project .\runtime\host-orchestrator python .\scripts\validate-agent-work-assets.py` -> `status=pass`; includes `runner_acceptance`.
- Full test gate: `uv run --project .\runtime\host-orchestrator python -m pytest` -> `128 passed`.
- Contract / invariant gate: `python .\scripts\verify-planning-status.py` -> `status=pass`; `proof_ref=docs/change-evidence/20260708-runner-acceptance-cli-validation.md`.
- Next-work selector: `python .\scripts\select-next-work.py` -> `status=pass`; `next_action=promote_phase1_execution`; embedded preflight passed with `128 passed`.
- Release-style preflight: `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit` -> pass; test `128 passed`; contract/docs/scripts/diff hygiene passed.
- Diff hygiene after TOML LF normalization: `git diff --check` -> pass.
- Build gate: `gate_na`; reason and substitute verification remain governed by `docs/specs/acceptance-and-gates.md`; substitute verification is the host-orchestrator pytest suite above.
- Hotspot gate: `gate_na`; reason and substitute verification remain governed by `docs/specs/acceptance-and-gates.md`; substitute verification is verifier + pytest + diff hygiene.

## Boundary

- repo-side done: candidate `runner_acceptance_ref` payloads can be independently validated against a repo-owned non-host-local worker profile before enabling `runner_wired=true`.
- still open: real remote host runner, real remote host acceptance artifacts, platform compatibility green, vm_gui runner, GUI-only workload acceptance, runtime_v2 default cutover, and live accepted.
