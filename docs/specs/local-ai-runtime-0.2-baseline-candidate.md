# Local AI Runtime 0.2 Baseline Candidate Entry

- `role=non_normative_navigation`
- `approval_input=false`

This short page is a stable discovery entry only. It is not a narrative specification,
normative artifact, `BaselineManifest.v1` input, review
evidence or `BaselineApprovalRecord` input. Do not copy candidate prose here.

## Frozen Narrative Target

- Baseline ID: `local-ai-runtime-0.2-v3.25`
- Canonical path: [v3.25 baseline candidate](local-ai-runtime-0.2-v3.25-baseline-candidate.md)
- Canonical repo path: `docs/specs/local-ai-runtime-0.2-v3.25-baseline-candidate.md`
- Exact bytes: `202958`
- SHA-256: `39ec0479a6ba0a0bf099f9d3f2410abb078ec3a3de4c3fe414ea76819f3834e0`
- Status: `baseline_candidate`; `blocking_stage=baseline_approval`

Only the frozen narrative target above defines the v3.25 product and target
runtime semantics. Any semantic or byte change requires a successor narrative
ID. Updating this navigation page cannot alter the target hash, close an
artifact, authorize implementation or approve the baseline.

## Current Approval Boundary

v3.25 minimally supersedes v3.24 because a `CREATE_SUSPENDED` child cannot run
`GetEnvironmentStringsW` or report its own environment before `ResumeThread`,
and because the predecessor's exact-option sync spelling is not supported. The successor
uses `pre_resume_parent_environment_proof` plus a dedicated no-write
`post_resume_q0_child_environment_observation`, and uses default-exact
`uv sync` with `--inexact` forbidden. The v3.24 narrative, preapproval inventory
and machine plan remain exact frozen history.

The v3.25 package is still **Request changes**: 15 artifacts are required,
9 are present and 6 are non-present. Source and `BaselineLineage.v4` are
present. The seven existing `CanonicalizationPolicy.v1`, `ProductContract.v2`,
`QualificationContractSet.v2`, `ExecutionSafetyContractSet.v1`,
`EvidenceContractSet.v1`, `DeterministicGitContractSet.v1` and
`StatePolicyCatalog.v1` artifacts are present only through the lineage's
explicit v3.24 byte/hash carry-forward. The next ready work item is
`LAR-P0A-010`, which must create Q0, gate, effective-feature and resource-limit
catalogs without running a live Q0.
The selector action is `close_baseline_normative_package_first`.

Baseline Approval, Truth Reset, `runtime/local-ai-runtime`, Implementation
Acceptance, Full Q0, P2 and live rollout remain inactive.

- [Planning status](../architecture/planning-status.json): machine truth for
  baseline identity, package state, queue and current work item.
- [Normative package inventory](local-ai-runtime-0.2-normative-package.json):
  artifact closure, carry-forward and approval eligibility.
- [Machine work items](../plans/local-ai-runtime-0.2-work-items.json): bounded
  AI execution scopes, dependencies, acceptance, verification and rollback.
- [v3.25 rebaseline evidence](../change-evidence/20260716-local-ai-runtime-v3.25-environment-proof-rebaseline.md):
  successor trigger, frozen predecessor identities and verification evidence.

`python scripts/verify-planning-status.py` verifies this entry's binding to
the frozen target. A passing planning verifier proves only internal
control-plane consistency; it does not grant approval or live authority.
