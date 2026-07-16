# 2026-07-16 Local AI Runtime v3.24 Product/Toolchain Rebaseline

## Objective and truth boundary

Create a successor candidate that fixes the reviewed product/toolchain contract gaps without approving or implementing the runtime. This slice changes only planning/specification/verifier/test/evidence surfaces. It does not create `runtime/local-ai-runtime`, mutate `.ai/config` or `.ai/state`, read live auth/DPAPI/sandbox state, run a real Batch/Git publication, issue Baseline Approval, perform Truth Reset, or produce live acceptance evidence.

Task identity: `local-ai-runtime-0.2-v3.24-implementation-work-items + LAR-P0A-REBASELINE-V324`.

## Trigger and predecessor identity

The successor trigger is `V324-EXACT-TOOLCHAIN-AND-LAUNCH-EXPERIENCE-001`, disposition `supersede_required`, for four reviewed gaps:

1. predecessor validation used a locked run but did not prove removal of extraneous distributions/plugins;
2. offline build did not bind build-backend dependencies to approved hashes;
3. validation did not explicitly select and read back the manifest Python executable;
4. first-run CLI, launch templates, human/JSON projection and product metrics were not decision-complete.

Frozen predecessor inputs:

| Input | Bytes | SHA-256 |
|---|---:|---|
| v3.23 candidate | 188325 | `80562322ebc744eda2a87a17c45f73a11982f4947c9d10e8628bb6f73ee9d5c6` |
| v3.23 preapproval inventory archive | 12439 | `2771b750557c68002eb54c3681185395e7d2881632211a4bb0bd6de75644d620` |
| v3.23 work-item plan archive | 220533 | `4b146d79c0f99a9621a8f6a743e8ddab7e2eb6d19356d2152a1c7130c0adebfe` |

## Primary-source basis

- uv’s [sync documentation](https://docs.astral.sh/uv/reference/cli/#uv-sync) defines exact synchronization and the handling of extraneous packages.
- uv’s [run documentation](https://docs.astral.sh/uv/reference/cli/#uv-run) distinguishes lock checking from environment synchronization and supports no-sync validation.
- uv’s [Python management documentation](https://docs.astral.sh/uv/guides/install-python/) documents managed Python behavior; v3.24 denies automatic downloads and binds an explicit interpreter.
- Python packaging’s [repeatable installs guidance](https://pip.pypa.io/en/stable/topics/repeatable-installs/) supports hash-bound dependency inputs; v3.24 applies the same supply-chain requirement to build constraints.

Community projects and predecessor evaluations were treated as structural inputs only; no community behavior was accepted without a closed local contract and verifier.

## Product and architecture decisions

- Retain Windows-local, single-operator, Python modular-monolith, SQLite authority, global writer capacity=1, CLI-first, deterministic commit-only Batch and read-only legacy compatibility.
- Add a first-run journey: doctor, repo qualification, template discovery, dry-run, challenged submit, status/action, evidence.
- Define exactly four launch templates: docs contract sync, bounded lint/type repair, focused test repair and mechanical repo maintenance.
- Human output is a catalog projection of public machine state; stable JSON is the automation contract; raw model/tool output is never interpolated.
- Replace the ambiguous runtime gate list with `new_runtime_exact_v1`: explicit exact preparation, no-sync validation, manifest-selected Python, hash-pinned backend constraints, identity read-back and clean-root reproducibility.
- Make SQLite the sole transition authority; journal replay only proposes recovery through current guard/CAS; cleanup finalizers cannot be bypassed by missing rows/files/segments.
- After P0B, allow P0C legacy guard and no-side-effect P0D scaffold to prepare in parallel; join both before P1.
- Remove B3 portfolio activation from 0.2. P4 remains B2/per-repo and releases P5 directly.

## Changed control-plane surfaces

- v3.24 candidate, stable entry, `BaselineLineage.v3`, normative inventory and frozen v3.23 inventory/plan archives;
- PRD, target architecture, roadmap, implementation plan, task list, acceptance/gates, repository entry docs and AGENTS contract;
- v4 55-item machine DAG, 11 closed contract projections, planning status and selector policy;
- planning verifier/selector and governance tests;
- evidence index.

The package remains `6/15 present, 9 non-present`. Only source/lineage and four exact compatible predecessor artifacts are present. `ProductContract.v2` is the next ready artifact; the rebaseline did not create it.

## Verification record

Final verification was rerun against the completed write set:

| Order | Command | Result |
|---:|---|---|
| 1 | `uv run --project ./runtime/host-orchestrator python -m pytest` | pass, 296 tests |
| 2 | `python scripts/verify-planning-status.py` | pass; v3.24 candidate, `6/15 present`, 9 missing, 55 work items, current `LAR-P0A-004` |
| 3 | `python scripts/select-next-work.py` | pass; `close_baseline_normative_package_first`, no side effect, no nested preflight |
| 4 | `python scripts/verify-local-ai-runtime-baseline.py --component canonicalization` | pass |
| 5 | `python scripts/verify-local-ai-runtime-baseline.py --component execution-safety` | pass |
| 6 | `python scripts/verify-local-ai-runtime-baseline.py --component evidence` | pass |
| 7 | `python scripts/verify-local-ai-runtime-baseline.py --component deterministic-git` | pass |
| 8 | `python -m py_compile scripts/verify-planning-status.py scripts/select-next-work.py runtime/host-orchestrator/tests/test_planning_governance.py` | pass |
| 9 | `pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit` | pass; build/hotspot remain explicit `gate_na`, test/contract/selector/script parsing/diff-check pass |
| 10 | `git diff --check` | pass |

Review also closed two truth-boundary defects found during the final pass:

1. B3 activation is now rejected throughout 0.2, including after a green P4 cohort, instead of being conditionally accepted after P4.
2. release-style preflight N/A reasons no longer pin the superseded v3.23 candidate name; the wording now remains correct across successor candidates.

The frozen identities were read back after the write set: v3.24 candidate `199728` bytes / `13ee366152d47edec151f30619ccd068a030b63febf2d899ee822d08d4dc4e2a`; v3.23 inventory archive `12439` bytes / `2771b750557c68002eb54c3681185395e7d2881632211a4bb0bd6de75644d620`; v3.23 plan archive `220533` bytes / `4b146d79c0f99a9621a8f6a743e8ddab7e2eb6d19356d2152a1c7130c0adebfe`; lineage v3 `6700` bytes / `b769bb3460a83ba31ca28fe60cc6d4c44902063c69b01ff344942a04e62dc756`.

## Compatibility and rollback

Legacy runtime/config/state behavior is unchanged. The v3.23 candidate and archives remain byte-identical. Rollback reverts only v3.24 candidate/lineage/control-plane/docs/verifier/test/evidence diffs; it must never rewrite the frozen v3.23 inputs or prior evidence.

## Residual risks and next work

- v3.24 is not approved and no runtime gate has been exercised against a real new package.
- Exact toolchain semantics must be materialized as `QualificationContractSet.v2` fixtures/verifier in `LAR-P0A-005` before implementation evidence is admissible.
- Launch behavior must be materialized as `ProductContract.v2` in current task `LAR-P0A-004` before it is normative.
- SDK/App Server/managed Worktree/Automations, B3, multi-writer and remote/distributed execution remain unsupported/deferred.
