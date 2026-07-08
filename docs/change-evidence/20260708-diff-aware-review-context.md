# 20260708 Diff-Aware Review Context

## Scope

This slice hardens the bounded live heterogeneous review sidecar context on `host_local`. It does not approve review outcomes, does not switch downstream flow out of `needs_review`, does not wire `claude_glm` as a primary task worker, does not wire real remote/vm runners, and does not claim `platform compatibility green` or `live accepted`.

## What Changed

- `HostLocalRunner` now keeps the changed-path list returned by the git-backed write-boundary guard after worker execution.
- Live review sidecar prompts now include:
  - runtime status and verification gate summary
  - primary worker output summary
  - changed files
  - bounded patch summary from `git diff --no-ext-diff`
- Non-git workspaces still degrade explicitly with `git_diff_unavailable` rather than inventing diff context.
- The authoritative review contract now describes the live review sidecar as diff-aware within the current git-backed host_local boundary.

## Verification

- Target RED was observed first: `test_host_local_runner_materializes_live_heterogeneous_review_receipt` failed because the review prompt did not contain changed files or a bounded patch summary, so the runtime fell back to a repo-side `codex_review` receipt.
- Target GREEN: `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_planner_adapter.py::test_host_local_runner_materializes_live_heterogeneous_review_receipt -q` -> `1 passed`.
- Diff fallback regression: `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_planner_adapter.py::test_review_patch_summary_degrades_without_git_admin_path runtime\host-orchestrator\tests\test_planner_adapter.py::test_review_patch_summary_degrades_when_git_diff_is_unavailable runtime\host-orchestrator\tests\test_planner_adapter.py::test_host_local_runner_materializes_live_heterogeneous_review_receipt -q` -> `3 passed`.
- Review/planner regression: `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_planner_adapter.py -q` -> `13 passed`.
- Path guard regression: `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_path_guard.py -q` -> `8 passed`.
- Claude structured worker regression: `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_claude_code_worker.py -q` -> `3 passed`.
- Full test gate: `uv run --project .\runtime\host-orchestrator python -m pytest` -> `130 passed`.
- Agent work asset validation: `uv run --project .\runtime\host-orchestrator python .\scripts\validate-agent-work-assets.py` -> `status=pass`.
- Planning-status verifier: `python .\scripts\verify-planning-status.py` -> `status=pass`; proof ref is this evidence file.
- Next-work selector: `python .\scripts\select-next-work.py` -> `status=pass`; next action remains `promote_phase1_execution`.
- Governance preflight: `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit` -> pass with test / contract / docs / scripts / diff hygiene pass.
- Build gate remains `gate_na` because the repo-owned build gate is not defined yet for the current Hermes -> AgentBridge -> Codex runtime mainline; alternative verification is the full pytest suite, per `docs/specs/acceptance-and-gates.md`.
- Hotspot gate remains `gate_na` because the repo-owned hotspot gate is not defined yet for the current Hermes -> AgentBridge -> Codex runtime mainline; alternative verification is verifier + pytest + diff hygiene, per `docs/specs/acceptance-and-gates.md`.
- Diff hygiene: `git diff --check` -> pass.

## Boundary

- repo-side done: host_local live review sidecar prompts now receive changed files, gate results, bounded patch summaries, and bounded primary worker output together.
- still open: review disposition / rework loop automation, real remote host runner, real remote host acceptance artifacts, platform compatibility green, vm_gui runner, GUI-only workload acceptance, runtime_v2 default cutover, and live accepted.
