# 20260708 Review Sidecar Diff Context Coverage

## Scope

This companion note records repo-side regression coverage for the bounded live heterogeneous review sidecar prompt context hardened in `20260708-diff-aware-review-context.md`. It does not wire `claude_glm` as a primary task executor, does not claim full diff-aware review, does not wire real remote/vm runners, does not change `current_active_queue`, and does not claim `platform compatibility green` or `live accepted`.

## What Changed

- Added a git-backed fixture to the existing live heterogeneous review receipt test.
- The fixture now seeds a temporary repo, lets the primary worker modify an allowed path, and asserts that the review sidecar prompt includes:
  - the changed file path
  - a bounded patch summary
  - the before/after diff lines needed for review context
- The production behavior change lives in `HostLocalRunner`: it carries the git-backed changed path list into review prompt construction and adds a bounded patch summary. This note only captures the focused regression coverage for that behavior.

## Verification

- RED was observed first: the updated test initially fell back to the repo-side `codex_review` receipt because the prompt lacked changed files and bounded patch summary context.
- Target GREEN: `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_planner_adapter.py::test_review_patch_summary_degrades_without_git_admin_path runtime\host-orchestrator\tests\test_planner_adapter.py::test_host_local_runner_materializes_live_heterogeneous_review_receipt -q` -> `2 passed`.
- Review/planner regression: `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_planner_adapter.py -q` -> `12 passed`.
- Full slice verification is recorded in `docs/change-evidence/20260708-diff-aware-review-context.md`.
- Final closeout keeps build / hotspot as project-defined `gate_na` until repo-owned gates exist; this is not a failure and uses the replacement checks defined in `docs/specs/acceptance-and-gates.md`.

## Boundary

- repo-side done: bounded review sidecar prompt context now has regression coverage for changed files and patch summary.
- still open: full diff-aware review, live `claude_glm` primary task execution, real remote/vm runner acceptance, platform compatibility green, runtime_v2 default cutover, and live accepted.
