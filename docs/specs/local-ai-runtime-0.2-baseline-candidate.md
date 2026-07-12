# Local AI Runtime 0.2 Baseline Candidate Entry

- `role=non_normative_navigation`
- `approval_input=false`

This short page is a stable discovery entry only. It is not a narrative specification,
a normative artifact, a `BaselineManifest.v1` input, review
evidence, or a `BaselineApprovalRecord` input. Do not copy candidate prose
into this page.

## Frozen Narrative Target

- Baseline ID: `local-ai-runtime-0.2-v3.22`
- Canonical path: [v3.22 baseline candidate](local-ai-runtime-0.2-v3.22-baseline-candidate.md)
- Canonical repo path: `docs/specs/local-ai-runtime-0.2-v3.22-baseline-candidate.md`
- Exact bytes: `178330`
- SHA-256: `8338a9dcf4bbbb40ca28f4f2ec6dca37587ee94fbfbbc6e3a0063c4de379569c`
- Status: `baseline_candidate`; `blocking_stage=baseline_approval`

Only the frozen narrative target above defines the v3.22 product and runtime
semantics. Any semantic or byte change to that target requires a new narrative
specification ID. Updating this navigation page must never be used to imply a
new baseline, alter the target hash, close a normative artifact, or authorize
implementation.

## Current Approval Boundary

The v3.22 candidate remains **Request changes**. Its normative package is
incomplete: the candidate source and v3.22-bound lineage are present, while
thirteen required artifacts are still missing. The historical v3.17 and both
conflicted v3.18 source bodies, plus the exact superseded v3.21 identity, are
bound by `BaselineLineage.v1`. The current ready work item is `LAR-P0A-002`,
selected as `close_baseline_normative_package_first`.

- [Planning status](../architecture/planning-status.json): machine truth for
  baseline identity, approval state, queue, and current work item.
- [Normative package inventory](local-ai-runtime-0.2-normative-package.json):
  required artifact closure and approval eligibility.
- [Machine work items](../plans/local-ai-runtime-0.2-work-items.json): bounded
  AI execution scopes, verification, evidence, rollback, and stop conditions.
- [Candidate rebaseline evidence](../change-evidence/20260712-local-ai-runtime-v3.22-candidate-rebaseline.md):
  frozen-byte and planning-projection evidence.

`python scripts/verify-planning-status.py` verifies this entry's binding to the
frozen target. A passing planning verifier only proves control-plane
consistency; it does not grant Baseline Approval, Truth Reset, Implementation
Acceptance, Full Q0, P2 Admission, Batch claim, or live acceptance.
