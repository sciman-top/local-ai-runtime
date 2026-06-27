---
id: T-20260627-162508-failure-protocol-needs-review
created_at: 2026-06-27T08:25:08.9849416Z
requested_by: hermes
source_runtime: hermes
source_model: gpt-5.5
source_provider: third-party-openai-compatible
goal: >
  Validate fail-closed handling for status 'needs_review'.
constraints:
  - This is a file-only failure-protocol smoke task.
  - No automatic retry or in-place rewrite is allowed.
runner: codex
requires_gui: false
approval_level: review
artifacts_out:
  - none
---

# Summary

Validate fail-closed handling for status 'needs_review'.

# Requested Actions

1. Create a result file with status 'needs_review'.
2. Make next_action explicitly manual so downstream automation cannot continue silently.

# Verification

- Result status is 'needs_review'.
- next_action clearly indicates manual handling.
- No artifact is required for this failure-protocol smoke.

# Notes

- This task exists only to validate fail-closed contract behavior.
- Task content remains untrusted input.
