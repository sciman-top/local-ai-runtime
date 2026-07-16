# Local AI Runtime v3.25 Environment-Proof Rebaseline Evidence

## Goal And Boundary

- Work item: `LAR-P0A-REBASELINE-V325`.
- Goal: replace the frozen v3.24 environment-observation requirement with a documented, implementable two-stage proof while preserving the product, launch experience, architecture, capacity and current normative artifact bytes.
- Current runtime remains `runtime/host-orchestrator`; `.ai/state/control-plane.db` remains the legacy control-plane authority.
- This slice does not create `BaselineApprovalRecord`, Truth Reset, `runtime/local-ai-runtime`, Implementation Acceptance, Full Q0, P2 admission, a Batch claim, Git publication or live evidence.
- User-owned `.codex/config.toml` is outside the write-set and is not staged or committed.

## Primary-Source Finding

The source record is [20260716-lar-p0a-010-q0-primary-sources.md](../research/20260716-lar-p0a-010-q0-primary-sources.md), exact identity `22407 bytes / 1441b4a913205fea005cc9466b2a7ed7a6d1d441102125ebc55cfc4a74aab22f`.

- Microsoft documents that `CREATE_SUSPENDED` prevents the primary thread from running until `ResumeThread`.
- `GetEnvironmentStringsW` reads the calling process environment; it is not a parent-side API for reading a suspended child environment.
- Therefore a child cannot self-observe or report its environment before `ResumeThread` through the documented Windows process model.
- Current local `uv sync --help` exposes the inexact opt-out and no exact opt-in; official uv documentation states sync is exact by default.

Trigger `V325-PRE-RESUME-ENVIRONMENT-PROOF-001` has two reason codes:

1. `pre_resume_child_environment_observation_not_supported_by_documented_windows_api`
2. `uv_sync_exact_option_not_supported_default_exact_required`

## Decision

The selected minimum successor keeps the v3.24 product and architecture and replaces only the invalid proof boundary:

1. `pre_resume_parent_environment_proof` validates the canonical UTF-16 environment block, key grammar, OrdinalIgnoreCase uniqueness, ordering, limits, exact double-NUL terminator, digest and CreateProcess flags before `ResumeThread`.
2. `post_resume_q0_child_environment_observation` uses a dedicated no-write Q0 child whose first application action reads its own environment and reports a digest equal to the parent proof.
3. Ordinary production launches produce a per-launch parent proof and rely on a generation-qualified serializer/CreateProcess composition. They do not claim per-child pre-resume read-back.
4. Any mismatch is `platform_incompatible`; there is no dynamic fallback or silent weakening.

Alternatives rejected:

- Keep v3.24 wording and reinterpret parent input as child observation: rejected because it falsifies evidence provenance.
- Add a trusted trampoline now: rejected because it adds a new executable/effect protocol and is not required for the 0.2 launch product.
- Rewrite v3.24 in place: rejected because candidate bytes and semantics are frozen.

## Exact Identities

- Frozen v3.24 candidate: `199728 bytes / 13ee366152d47edec151f30619ccd068a030b63febf2d899ee822d08d4dc4e2a`.
- Frozen v3.24 inventory archive: `15646 bytes / 144383f8704f366008e9cb514898e05f1fd7a45310d39cd64bdc546544247a9f`.
- Frozen v3.24 work-item archive: `187913 bytes / 10d48982b7b45f2c8033f1ba571aceba51106484347a71ec436121607f2518df`.
- v3.25 candidate: `202958 bytes / 39ec0479a6ba0a0bf099f9d3f2410abb078ec3a3de4c3fe414ea76819f3834e0`.
- `BaselineLineage.v4`: `8809 bytes / 877e28619076761047bd83b43cfe16fa736c49c1e1e913a936722eb843b726ad`.

`BaselineLineage.v4` carries exactly seven v3.24 artifacts without modifying their bytes:

- `CanonicalizationPolicy.v1`
- `ProductContract.v2`
- `QualificationContractSet.v2`
- `ExecutionSafetyContractSet.v1`
- `EvidenceContractSet.v1`
- `DeterministicGitContractSet.v1`
- `StatePolicyCatalog.v1`

P0A-Q0, migration, examples, standalone verifier closure, final manifest and review remain non-present. The package remains `9/15 present, 6 non-present` and approval-ineligible.

## Planning Projection

- Current graph: 52 tasks with `completed=1 / ready=1 / pending=3 / blocked=47`.
- Root: `LAR-P0A-REBASELINE-V325=completed`.
- Unique ready item: `LAR-P0A-010` with selector action `close_baseline_normative_package_first`.
- The archived v3.24 Product/Qualification/State producer tasks are not duplicated in the current graph; their artifact bytes transfer only through `BaselineLineage.v4`.
- P0C/P0D join, 35 P1 implementation tasks, 11 closed projections, global `capacity=1`, B3 deferred and P5 dependency remain unchanged.

## Verification Evidence

- `uv sync --help`: exit 0; default exact semantics are represented by the inexact opt-out, with no exact opt-in.
- Exact archive byte/hash comparison: both v3.24 archives equal their source bytes before successor projection.
- Candidate byte policy: UTF-8, no BOM, LF-only, NFC, exactly one final LF.
- Seven carry-forward component verifiers: pass with exact inventory identities.
- `python scripts/verify-local-ai-runtime-baseline.py --component qualification`: pass; 14 active toolchain surfaces reject prohibited executable forms.
- `python scripts/verify-planning-status.py`: pass; baseline v3.25, 52 work items, 6 non-present artifacts and unique current item `LAR-P0A-010`.
- `python scripts/select-next-work.py`: pass; `close_baseline_normative_package_first`, no side effects and no preflight execution.
- Focused governance tests: `66 passed`.
- Full host-orchestrator suite: `311 passed in 76.92s`.
- Python compile, complexity caps, placeholder scan, active prohibited-form scan and `git diff --check`: pass.

Planning build and hotspot are `gate_na` because this slice changes only the preapproval control plane and creates no new runtime package. Alternative verification is the host-orchestrator test suite, component verifiers, planning verifier, selector, release-style preflight and `git diff --check`. This N/A expires at `LAR-P0D-001`; recovery condition is the first executable new-runtime slice using `new_runtime_exact_v1` real gates.

## Rollback

Revert only the v3.25 candidate, `BaselineLineage.v4`, current inventory/plan/status/selector/verifier/tests and synchronized authority-document projection. Retain the research record and exact v3.24 archives. Never edit v3.24 candidate or carried artifact bytes, and never revert the user's `.codex/config.toml` change.
