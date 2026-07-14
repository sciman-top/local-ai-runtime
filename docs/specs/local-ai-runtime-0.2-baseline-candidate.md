# Local AI Runtime 0.2 Baseline Candidate Entry

- `role=non_normative_navigation`
- `approval_input=false`

This short page is a stable discovery entry only. It is not a narrative specification,
a normative artifact, a `BaselineManifest.v1` input, review
evidence, or a `BaselineApprovalRecord` input. Do not copy candidate prose
into this page.

## Frozen Narrative Target

- Baseline ID: `local-ai-runtime-0.2-v3.23`
- Canonical path: [v3.23 baseline candidate](local-ai-runtime-0.2-v3.23-baseline-candidate.md)
- Canonical repo path: `docs/specs/local-ai-runtime-0.2-v3.23-baseline-candidate.md`
- Exact bytes: `188325`
- SHA-256: `80562322ebc744eda2a87a17c45f73a11982f4947c9d10e8628bb6f73ee9d5c6`
- Status: `baseline_candidate`; `blocking_stage=baseline_approval`

Only the frozen narrative target above defines the v3.23 product and runtime
semantics. Any semantic or byte change to that target requires a new narrative
specification ID. Updating this navigation page must never be used to imply a
new baseline, alter the target hash, close a normative artifact, or authorize
implementation.

## Current Approval Boundary

The v3.23 candidate remains **Request changes**. Its normative package is
incomplete: the candidate source and v3.23-bound lineage are present, while
seven required artifacts are still missing. The historical v3.17 and both
conflicted v3.18 source bodies, plus the exact superseded v3.21 identity, are
bound by `BaselineLineage.v2`. The sealed evaluation recorded an immutable
`preserve_v3_23_semantics` decision without promoting either evaluated
high-effort profile. `LAR-P0A-002` revalidated the non-final manifest fixture
and verifier skeleton against the frozen v3.23 source and `BaselineLineage.v2`.
`LAR-P0A-003` through `LAR-P0A-006` closed canonicalization/path identity,
product/submission, qualification/authorization and execution/fencing bundles
without opening live runtime authority. `LAR-P0A-007` then closed the
exhaustive event/status matrix, append-only journal and six-condition receipt,
no-replace artifact and runtime-managed external evidence rules, purpose-bound
key envelopes, and marker-before-mutation backup/restore anti-rollback protocol
as `EvidenceContractSet.v1`. `LAR-P0A-008` then closed the hardened Git
environment/config audit, controller-independent canonical object framing,
claim-time-bound single-parent commit, attempt-local object verification and
promotion, no-reflog worktree/HEAD/task-ref publication and ordered cleanup as
`DeterministicGitContractSet.v1`. Only offline fixtures and non-writing
`git hash-object` cross-checks were used; no Git operation targeted a real
repository. The unique ready work item is now `LAR-P0A-009`, selected as
`close_baseline_normative_package_first`. Baseline Approval remains
inactive; any later semantic change still requires a v3.24 successor instead
of rewriting this frozen target.

- [Planning status](../architecture/planning-status.json): machine truth for
  baseline identity, approval state, queue, and current work item.
- [Normative package inventory](local-ai-runtime-0.2-normative-package.json):
  required artifact closure and approval eligibility.
- [Machine work items](../plans/local-ai-runtime-0.2-work-items.json): bounded
  AI execution scopes, verification, evidence, rollback, and stop conditions.
- [Candidate rebaseline evidence](../change-evidence/20260712-local-ai-runtime-v3.23-native-thin-path-rebaseline.md):
  frozen-byte and planning-projection evidence.

`python scripts/verify-planning-status.py` verifies this entry's binding to the
frozen target. A passing planning verifier only proves control-plane
consistency; it does not grant Baseline Approval, Truth Reset, Implementation
Acceptance, Full Q0, P2 Admission, Batch claim, or live acceptance.
