# LAR-P0A-005 QualificationContractSet.v2 Exact Toolchain

## Scope and truth boundary

This atomic P0A closeout materializes the v3.24 exact-toolchain qualification contract. It creates `QualificationContractSet.v2`, the `RuntimeToolchainManifest.v1` schema, `VerificationExecutionProfile.v1`, offline fixtures and a stdlib-only component verifier. It does not edit the frozen v3.24 narrative or `QualificationContractSet.v1`, create `runtime/local-ai-runtime`, prepare or mutate a live environment, download Python or dependencies, run an actual build, read live auth/provider/sandbox state, issue approval or create live acceptance evidence.

## Closed toolchain decisions

- Environment preparation is an explicit non-gate step using `uv sync --locked --offline --no-python-downloads --python <manifest-python>`; uv sync is exact by default, `--inexact` is prohibited and validation never hides synchronization. The frozen v3.24 narrative's unsupported `uv sync --exact` spelling is a non-semantic CLI correction owned by `QualificationContractSet.v2` and `VerificationExecutionProfile.v1`; the frozen candidate bytes are not rewritten.
- Every uv gate binds the manifest-selected Python and denies automatic Python download. Child read-back covers executable path, patch, file identity/hash, uv identity, installed distributions, pytest plugins and build frontend/backend identities.
- Daily validation uses `run --no-sync`; fixed order is `supply_chain_identity -> build -> test -> contract_invariant -> hotspot`.
- Build requires offline/no-download/explicit-Python plus `--build-constraint` and `--require-hashes`; cached backend selection must equal the manifest hash set.
- Two clean roots share one `SOURCE_DATE_EPOCH` and must match normalized member-manifest and final artifact hashes; absolute roots and mtimes are excluded from the normalized identity.
- The v1 sensitive-input, repo/template qualification, auth, sandbox, Authorization, grant/revoke and continuation contracts remain frozen and are verified before v2.

## Frozen artifact identities

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `QualificationContractSet.v2.json` | 7936 | `4c873185b2eb293c23099d616fb1e754ce073e89491200dcc4e4ac0bb6fc4dac` |
| `RuntimeToolchainManifest.v1.schema.json` | 5314 | `96bfcba51d76d5539c3b37559ebd9e455d32482442442dc8add3ae86100e8a90` |
| `VerificationExecutionProfile.v1.json` | 3392 | `9744a431f0dedf1fe5c3503d83535ac4902b8e064bd4175bcf2cf56f70365d49` |
| `toolchain-v2/manifest.json` | 7143 | `91004d7915f331ef94579c1e0b34f34bf178eee3efefc956440f2cd51369b50f` |
| frozen predecessor `QualificationContractSet.v1.json` | 7336 | `089a60664188fdc86c0de56496c493339246c5b423ddc3271450fb01e4fd6a80` |

## Negative coverage

Twelve executable mutations fail closed: extraneous distribution, extraneous pytest plugin, wrong Python patch, wrong executable, download request, unconstrained extra backend, missing backend hash, normalized member mismatch, artifact mismatch, hidden sync in validation, missing `--require-hashes` and PATH-Python fallback. Every v2 member also has an independent identity-drift test.

## Verification

| Command | Result |
|---|---|
| `python scripts/verify-local-ai-runtime-baseline.py --component qualification` | pass; v2 `7936` bytes / `4c873185b2eb293c23099d616fb1e754ce073e89491200dcc4e4ac0bb6fc4dac`; frozen v1 `7336` bytes / `089a60664188fdc86c0de56496c493339246c5b423ddc3271450fb01e4fd6a80`; execution profile `3392` bytes / `9744a431f0dedf1fe5c3503d83535ac4902b8e064bd4175bcf2cf56f70365d49`; 14 active surfaces, 1 preparation command, 10 validation commands, 2 distributions, 1 pytest plugin, 2 backend requirements and 12 negative fixtures |
| `uv run --project ./runtime/host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_baseline_qualification.py -q` | pass; `21 passed` |
| `uv run --project ./runtime/host-orchestrator python -m pytest -q` | pass; `306 passed` |
| `python scripts/verify-planning-status.py` | pass; package `8/15`, 7 missing, current `LAR-P0A-009` |
| `python scripts/select-next-work.py` | pass; unique next item `LAR-P0A-009`, no side effects |
| `uv --version`; `uv sync --help` | pass; local `uv 0.10.2`; sync exposes `--inexact` but no `--exact`, matching the official default-exact contract |
| `python -m py_compile scripts/qualification_v2_contract.py scripts/verify-local-ai-runtime-baseline.py scripts/verify-planning-status.py scripts/select-next-work.py` | pass |
| `git diff --check` | pass |
| `pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit` | pass on the final evidence bytes; build/hotspot retain the approved planning-slice N/A records |

Primary references: [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/) defines `uv sync` as exact by default and `--inexact` as the opt-out; [uv building distributions](https://docs.astral.sh/uv/concepts/projects/build/) defines hash-checked build constraints.

## Compatibility and rollback

`QualificationContractSet.v1` remains byte-identical and is verified before v2 on every component run. Rollback reverts only the four v2 artifacts, `scripts/qualification_v2_contract.py`, verifier wrapper/tests and current inventory/status/docs/evidence projections. It must restore `LAR-P0A-005=ready`, `LAR-P0A-009=pending` and must not rewrite the frozen narrative, predecessor artifacts or earlier atomic commits.

## Residual boundary

The package becomes `8/15 present, 7 non-present`; it remains approval-ineligible and no actual environment has qualified. The next selector item is `LAR-P0A-009`, which materializes SQLite-authority state, guard, cleanup and operator-action catalogs. Bounded continuation stops here because this is the third completed item in the current kickoff.
