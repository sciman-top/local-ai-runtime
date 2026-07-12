# Baseline Candidate Entry Guard

## Result

Added the stable discovery page
`docs/specs/local-ai-runtime-0.2-baseline-candidate.md` without creating a
second narrative specification or changing the frozen v3.21 candidate bytes.

The page is explicitly `role=non_normative_navigation` and
`approval_input=false`. It only points to
`local-ai-runtime-0.2-v3.21`, whose frozen target remains:

- path: `docs/specs/local-ai-runtime-0.2-v3.21-baseline-candidate.md`
- bytes: `158485`
- SHA-256:
  `1bfb5cd2c92c036804a6005d5b36cdd5acc6bedc4d6bf4070ccfb7a70ce063fb`

## Controls Added

- `planning-status.json` declares the entry path, role, target identity,
  exact target bytes/hash, `approval_input=false`, a 4096-byte maximum, and
  the entry page's own exact byte count/hash without making it normative.
- `verify-planning-status.py` fails closed if the entry path, role, approval
  boundary, target mapping, maximum, validated UTF-8/LF/NFC byte policy,
  entry bytes/hash, required safety markers, or frozen-target link drift.
- The selector policy requires the exact guarded entrypoint set, including this
  page, and the planning verifier rejects using the page as either the
  normative inventory's candidate source or an artifact path.
- Governance tests cover the truthful entry plus rejected approval-input,
  target-hash, real oversized-content, inventory-inclusion, and selector-entry
  exactness cases.
- Root and documentation indexes route discovery through the guarded page,
  while continuing to identify v3.21 as the unique frozen narrative source.

## Deliberately Unchanged

- `docs/specs/local-ai-runtime-0.2-v3.21-baseline-candidate.md` bytes and hash.
- The 15-artifact normative inventory: one source remains present and fourteen
  artifacts remain missing.
- `LAR-P0A-001`, `close_baseline_normative_package_first`, Baseline Approval,
  Truth Reset, implementation, Q0/P2 admission, legacy runtime behavior,
  `.ai` state, provider/auth, scheduler, and live evidence.

## Verification

All commands ran from `D:\CODE\local-ai-dev-orchestrator` on 2026-07-12.

| Gate | Command | Exit | Result |
|---|---|---:|---|
| Focused governance | `uv run --project ./runtime/host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_planning_governance.py -q` | 0 | 35 passed |
| Planning contract | `python scripts/verify-planning-status.py` | 0 | v3.21 remains frozen; 14 artifacts missing; `LAR-P0A-001` remains ready |
| Selector | `python scripts/select-next-work.py` | 0 | `close_baseline_normative_package_first`; no side effects or preflight |
| Ruff | `uv run --project ./runtime/host-orchestrator ruff check scripts/verify-planning-status.py runtime/host-orchestrator/tests/test_planning_governance.py` | 0 | All checks passed |
| Full legacy tests | `uv run --project ./runtime/host-orchestrator python -m pytest` | 0 | 193 passed |
| Governance preflight | `pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit` | 0 | test, contract, selector, script parse, and diff gates passed |
| Diff hygiene | `git diff --check` | 0 | no whitespace errors |

The entry page is 2,287 bytes. .NET `SHA256.HashData` and PowerShell
`Get-FileHash` independently returned
`728013566b8d879373ad2addaf7f619f516c3eaf3e7478ce361b82a3aedf5274`.
The frozen v3.21 narrative was independently re-read as 158,485 bytes with
SHA-256
`1bfb5cd2c92c036804a6005d5b36cdd5acc6bedc4d6bf4070ccfb7a70ce063fb`.

Build remains `gate_na` because this slice does not create
`runtime/local-ai-runtime`; hotspot remains `gate_na` because it changes only
planning/document discovery controls. Both N/A conditions retain their existing
expiry in `docs/specs/acceptance-and-gates.md`.

## Rollback

Revert only this entry page, its planning-status/verifier/test/index/evidence
references, and the corresponding commit. Do not alter the frozen v3.21
narrative, the normative package inventory, approval records, `.ai` state, or
runtime behavior.
