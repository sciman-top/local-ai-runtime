# LAR-P0A-009 State, Guard And Operator Policy

## Scope and truth boundary

This atomic P0A closeout materializes the v3.24 state-policy bundle. It creates `StatePolicyCatalog.v1`, `GuardCatalog.v1`, `OperatorActionCatalog.v1`, deterministic positive/negative fixtures and a stdlib-only component verifier. It does not edit the frozen v3.24 narrative, create `runtime/local-ai-runtime`, mutate `.ai` or legacy runtime behavior, read live state/auth/provider/DPAPI data, run a process or Git effect, issue approval, perform Truth Reset or create live acceptance evidence.

## Closed policy decisions

- Seven state domains remain independent rather than forming a cartesian state machine: platform, repository, template, task, attempt, cleanup and operator-action inbox.
- SQLite is the only policy and transition authority. Journal records are accepted-cursor/current-fence/immutable-action-history-bound observation and recovery inputs; they cannot create or overwrite authoritative state.
- Equal accepted history under one policy generation produces the same recovery disposition independent of observation time, restart count or scan count.
- Guard evaluation uses 13 fixed precedence levels. Its 17 declared dependencies are acyclic and cannot point from an earlier guard to a later-precedence prerequisite.
- Recovery-eligible publication, deterministic closeout and cleanup outrank due retry and new promoted work. Global writer capacity remains one.
- Cleanup finalizers derive from durable effect/action history and cannot be bypassed by deleting a guard row, marker, journal segment or database row.
- Global resume can clear only the platform pause it owns; repository and template qualification blocks require their scoped actions and evidence.
- B3 portfolio scheduling is data-only and deferred beyond 0.2. No 0.2 transition or operator action can activate it.

## Frozen bundle identities

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `StatePolicyCatalog.v1.json` | 41279 | `423f90a0550630b0d413cc82a53f98b6602d05cd6b7a9072f2a65759e15189de` |
| `GuardCatalog.v1.json` | 10131 | `17b2022df58299ded4ca9897df2de236b8e73f3707d5e288e017635aafede31b` |
| `OperatorActionCatalog.v1.json` | 9644 | `14f98ab03f4884736ea3b3a443ec3641aec7768cdce708d48f072bb49d860c87` |
| `state-policy/manifest.json` | 5761 | `03afaef9f99f2b7152c335b058a32279c84fd815567ed0f7e929f13daf0c276b` |

The bundle contains 7 policy tables, 83 transition rows, 91 guards, 17 guard-dependency edges, 13 precedence levels, 16 operator actions, 5 positive fixtures and 18 negative fixtures.

## Negative coverage

Eighteen executable mutations fail closed, covering missing legal operations, unknown combinations, row completeness, duplicate transitions, guard absence, dependency cycles and precedence violations, journal authority expansion, nondeterministic recovery inputs, cleanup bypass, global-resume scope expansion, recovery priority inversion, capacity drift, operator-action drift and B3 activation. Identity drift is independently checked for every bundle member.

## Primary basis

- [SQLite transactions](https://www.sqlite.org/lang_transaction.html) defines `BEGIN IMMEDIATE` as starting a write transaction immediately and returning `SQLITE_BUSY` when another write transaction is active. This supports a single serialized policy-authority writer.
- [SQLite locking](https://www.sqlite.org/lockingv3.html) defines hot-journal recovery before database reads continue. The journal restores database consistency; it is not an independent policy authority.
- [SQLite atomic commit](https://www.sqlite.org/atomiccommit.html) describes writing the rollback journal before database pages and using it to restore the prior state after failure. The contract therefore treats recovery observations as inputs to a transactionally accepted decision, not as permission to invent a transition.

## Verification

| Command | Result |
|---|---|
| `python scripts/verify-local-ai-runtime-baseline.py --component state-policy` | pass; exact four-member identities; 7 tables, 83 rows, 91 guards, 17 dependency edges, 13 precedence levels, 16 actions, 5 positive and 18 negative fixtures |
| `uv run --project ./runtime/host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_baseline_state_policy.py -q` | pass; `5 passed` |
| `uv run --project ./runtime/host-orchestrator python -m pytest -q` | pass; `311 passed` |
| `python scripts/verify-planning-status.py` | pass; package `9/15`, 6 missing, current `LAR-P0A-010` |
| `python scripts/select-next-work.py` | pass; unique next item `LAR-P0A-010`, no governance issue or side effect |
| `python -m py_compile scripts/state_policy_contract.py scripts/verify-local-ai-runtime-baseline.py scripts/verify-planning-status.py scripts/select-next-work.py runtime/host-orchestrator/tests/test_baseline_state_policy.py runtime/host-orchestrator/tests/test_planning_governance.py` | pass |
| `git diff --check` | pass |
| `pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit` | pass on the final evidence bytes; `311 passed`, planning/current selector=`LAR-P0A-010`, scripts/diff green; build/hotspot retain the approved planning-slice N/A records |

Build is `gate_na`: reason=this preapproval slice creates data contracts and verifier code but no new runtime package/build entry; alternative=component verifier, host-orchestrator tests and planning preflight; evidence=this record; expires_at=`LAR-P0D-001`; recovery_condition=P0D creates the manifest-bound build entry. Hotspot is `gate_na`: reason=no runtime hot path changes; alternative=component/full tests, `py_compile` and diff checks; evidence=this record; expires_at=the first executable post-P0D slice; recovery_condition=that slice runs the real hotspot profile.

## Compatibility and rollback

The current `runtime/host-orchestrator`, `.ai/state/control-plane.db`, `.ai/config`, frozen v3.24 narrative and all predecessor artifacts remain unchanged. Rollback reverts only the four state-policy artifacts, `scripts/state_policy_contract.py`, the baseline verifier wrapper/test additions and current inventory/status/docs/evidence projections. It restores `LAR-P0A-009=ready`, `LAR-P0A-010=pending`, package `8/15 present` and the previous stable-entry identity; it must not rewrite frozen narrative/history or user-owned `.codex/config.toml` changes.

## Residual boundary

The package becomes `9/15 present, 6 non-present`; it remains approval-ineligible and no runtime state machine has been implemented or exercised. The next selector item is `LAR-P0A-010`, which must materialize Q0/gate/effective-feature/process/resource-limit catalogs and fixtures without running a live Q0.
