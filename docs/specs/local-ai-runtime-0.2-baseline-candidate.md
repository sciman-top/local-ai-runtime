# Local AI Runtime 0.2 Baseline Candidate Entry

- `role=non_normative_navigation`
- `approval_input=false`

This short page is a stable discovery entry only. It is not a narrative specification,
normative artifact, `BaselineManifest.v1` input, review
evidence or `BaselineApprovalRecord` input. Do not copy candidate prose here.

## Frozen Narrative Target

- Baseline ID: `local-ai-runtime-0.2-v3.24`
- Canonical path: [v3.24 baseline candidate](local-ai-runtime-0.2-v3.24-baseline-candidate.md)
- Canonical repo path: `docs/specs/local-ai-runtime-0.2-v3.24-baseline-candidate.md`
- Exact bytes: `199728`
- SHA-256: `13ee366152d47edec151f30619ccd068a030b63febf2d899ee822d08d4dc4e2a`
- Status: `baseline_candidate`; `blocking_stage=baseline_approval`

Only the frozen narrative target above defines the v3.24 product and target
runtime semantics. Any semantic or byte change requires a successor narrative
ID. Updating this navigation page cannot alter the target hash, close an
artifact, authorize implementation or approve the baseline.

## Current Approval Boundary

v3.24 supersedes v3.23 because the predecessor gate commands could not prove an
exact uv environment, manifest-pinned Python or hash-pinned build backend, and
because its first-launch product experience was not decision-complete. The
v3.23 narrative, preapproval inventory and machine plan remain exact frozen
history.

The v3.24 package is still **Request changes**: 15 artifacts are required,
9 are present and 6 are non-present. Source and `BaselineLineage.v3` are
present. `CanonicalizationPolicy.v1`, `ExecutionSafetyContractSet.v1`,
`EvidenceContractSet.v1` and `DeterministicGitContractSet.v1` are present
only through the lineage's explicit byte/hash carry-forward. `ProductContract.v2`
is present with the first-run journey, four launch templates and operator
presentation contracts. `QualificationContractSet.v2` is present with exact
uv/Python/build gates. `StatePolicyCatalog.v1` is present with seven independent
state domains, fixed guard precedence, deterministic recovery, non-bypassable
cleanup finalizers and durable operator actions. The next ready work item is
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
- [v3.24 rebaseline evidence](../change-evidence/20260716-local-ai-runtime-v3.24-product-toolchain-rebaseline.md):
  successor trigger, frozen predecessor identities and verification evidence.

`python scripts/verify-planning-status.py` verifies this entry's binding to
the frozen target. A passing planning verifier proves only internal
control-plane consistency; it does not grant approval or live authority.
