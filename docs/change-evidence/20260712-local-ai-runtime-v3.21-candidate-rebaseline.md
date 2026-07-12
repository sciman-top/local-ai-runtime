# Local AI Runtime v3.21 Candidate Rebaseline

## Result

`local-ai-runtime-0.2-v3.21` is the current self-contained baseline candidate. Its narrative bytes, planning projection, normative-package inventory, 58-item machine work graph, selector, verifier, governance tests and human-readable planning documents are aligned.

The decision remains **Request changes**. The normative package has 15 required artifacts: one present narrative source and 14 missing artifacts. No `BaselineApprovalRecord`, Truth Reset, `runtime/local-ai-runtime` package, Implementation Acceptance, Full Q0/P2 Admission, Batch claim, scheduled task or live evidence was created.

## Goal And Scope

This change freezes the reviewed v3.21 narrative candidate, preserves v3.19 and v3.20 as exact superseded archives, closes the remaining specification-level safety ambiguities, and rebaselines the preapproval planning control plane so a later AI session can execute exactly one bounded work item at a time.

Changed scope is limited to:

- the v3.21 candidate and its non-normative package inventory;
- AGENTS/README and product, architecture, roadmap, plan, backlog and acceptance projections;
- the 58-item machine work graph and stage selector policy;
- the read-only planning verifier/selector, governance preflight and focused governance tests;
- repo-level change evidence.

Intentionally unchanged:

- `runtime/host-orchestrator` production behavior and its existing database contract;
- `.ai/config`, `.ai/state/control-plane.db`, provider/auth, scheduler and live processes;
- default runtime entrypoints, repo ownership, target-repo cutover and existing task evidence;
- `runtime/local-ai-runtime`, which does not exist before approved task `LAR-P0D-001`.

## Candidate And Archive Identity

| Artifact | Status | Bytes | SHA-256 |
|---|---|---:|---|
| `docs/specs/local-ai-runtime-0.2-v3.19-baseline-candidate.md` | superseded candidate archive | 111952 | `275306D2E88BAAFA803170EE4EF99FB822C4E13769721B806805B834BB9D7670` |
| `docs/specs/local-ai-runtime-0.2-v3.20-baseline-candidate.md` | frozen superseded candidate archive | 130890 | `43CB98737DAA5D171A9CDA2DCA49C8F118FB8BE92745B4076948D9178E56A130` |
| `docs/specs/local-ai-runtime-0.2-v3.21-baseline-candidate.md` | current baseline candidate | 158485 | `1BFB5CD2C92C036804A6005D5B36CDD5ACC6BEDC4D6BF4070CCFB7A70CE063FB` |

The v3.21 byte policy is UTF-8 without BOM, LF only, NFC, exactly one terminal LF, no disallowed control/noncharacter/bidi/zero-width code point, and no trailing SP/HTAB. The validator rejects non-conforming input and does not rewrite it. Python `hashlib` and PowerShell `Get-FileHash` independently reproduce the same SHA-256.

## Material Decisions Closed In v3.21

- Ordinary submission replay performs bounded public-envelope validation and a volatile existing-family lookup before current catalog, secret, qualification, Authorization, base and environment admission. An existing family permanently returns generation-0 `root_task_id`; an absent rejected family retains no input-derived oracle.
- Deterministic controller actions inherit one immutable root execution authority across a non-branching fenced-adoption chain. Every actual process still has a current-fence, at-most-once `AuthorizationExecutionGrant` or `SafetyOnlyExecutionRecord` authority.
- Every process-bearing stage uses `CREATE_SUSPENDED`, `PROC_THREAD_ATTRIBUTE_JOB_LIST`, an exact non-empty `PROC_THREAD_ATTRIBUTE_HANDLE_LIST`, `STARTF_USESTDHANDLES`, parent-end close and a durable execution-commit barrier. Ambient controller/auth/DB/Job handles are not inherited.
- Windows environment construction rejects `OrdinalIgnoreCase` aliases, hidden drive entries, malformed keys and NUL, then verifies the child-observed block before resume.
- Alias-aware NTFS 8.3 handling uses handle identity and bypass probes. `policy_query_denied` is explicit; global short-name disablement is not required.
- `sandbox.log` is an opaque bounded protected diagnostic. Runtime code does not parse it or retain its content/hash; managed export requires an operator session and secret scan.
- Raw prompt, Codex JSONL, stdout/stderr, argv/env/config dump and their content hashes never enter normal state, artifact, evidence or quarantine.
- `runtime_external_v1` evidence is runtime-managed and identity/ancestry/alias-disjoint from repo, Git, worktree, attempt and controller-sensitive roots.
- Quarantine and runtime-integrity key envelopes are purpose-separated and DPAPI wrapped. Restore is suspended-only, single-consumption and rejected after post-backup authoritative mutation.
- Mandatory resource protection is `accounting_kill_audit` plus a 1 GiB `EmergencyDiskReserveRecord`; `HardWriteQuotaCapability` remains an optional Full-Q0-qualified enhancement.
- Target implementation is pinned to Python 3.11.x and exactly the approved `contracts/kernel/qualification/storage/execution/recovery/git_local/operations/compat` source subpackages. Artifact/evidence persistence maps to `storage`; Batch/doctor orchestration maps to `operations`.
- Narrative ID, versioned normative artifact IDs and immutable final `BaselineManifest` are separate version layers. `package_review_head -> manifest closure review -> approval_review_head` is append-only and non-circular.

## AI Execution Projection

`docs/plans/local-ai-runtime-0.2-work-items.json` contains 58 ordered work items. P1A-P1F contains 33 single-session implementation slices with phase counts `4 + 5 + 6 + 6 + 6 + 6`. Each task declares dependencies, preconditions, in/out scope, concrete primary files, acceptance checks, repo-root commands, evidence, local rollback, stop conditions, prohibited actions and one successor boundary.

Current state is deliberately narrow:

- queue: `LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE`;
- current task: `LAR-P0A-001`;
- selector action: `close_baseline_normative_package_first`;
- package: 15 required / 1 present / 14 missing;
- Baseline Approval, Truth Reset, implementation, Full Q0/P2 and rollout: false.

`LAR-P0A-002` creates only the manifest schema, fixtures and verifier skeleton. It cannot create the final manifest. `LAR-P0A-013` runs the preliminary consistency review, freezes `package_review_head`, creates the final manifest once, appends the manifest-closure review and proves `approval_review_head` succession.

The selector additionally fails closed when `LAR-P0A-013` and the exact declared final-review missing-artifact set are not paired. The verifier reports malformed nested work-item/inventory collections instead of raising an unstructured exception.

The work graph verifier now fixes the schema/status set, validates phase/task-ID agreement, non-negative priority, closed verification-profile keys, unique non-empty string collections, approved source subpackages and `git diff --check` on every work item. The selector accepts a verifier subprocess only when its structured output says `status=pass` and attests the same baseline and current work-item identities; exit 0 with empty, malformed or mismatched output returns `repair_gate_first`.

## Five-Axis Review

| Axis | Result |
|---|---|
| Correctness | Closed the doc-contract projection gap, malformed machine-field acceptance, P3/P4 missing diff hygiene and selector exit-0/non-JSON false success. |
| Architecture | Removed planned `evidence/` and `commands/` source packages that violated the frozen module boundary; retained the nine approved subpackages only. |
| Security | High-risk handle/environment/evidence/restore requirements are projected into work items, implementation plan, acceptance and planning contracts; verifier/selector failure remains fail closed. |
| Readability | P1 phase-closing IDs are explicit, Python support is stated as pinned 3.11.x rather than ambiguous `3.11+`, and every task remains at five or fewer primary files. |
| Performance | Planning verifier and selector remain bounded read-only checks; no runtime hot path, dependency, scheduler or live process changed. |

## Changed Files

The change set updates:

- `AGENTS.md`, `README.md` and `docs/README.md`;
- `docs/product/orchestrator-prd.md`;
- `docs/architecture/orchestrator-target-architecture.md`;
- `docs/architecture/planning-status.json` and `next-work-selection-policy.json`;
- `docs/roadmap/orchestrator-roadmap.md`;
- `docs/plans/orchestrator-implementation-plan.md` and `local-ai-runtime-0.2-work-items.json`;
- `docs/backlog/orchestrator-task-list.md`;
- `docs/specs/acceptance-and-gates.md`, the v3.19/v3.20 archives, the v3.21 candidate and the normative-package inventory;
- `scripts/verify-planning-status.py`, `scripts/select-next-work.py` and `scripts/governance/preflight.ps1`;
- `runtime/host-orchestrator/tests/test_planning_governance.py`;
- the 2026-07-12 rebaseline evidence and evidence index.

## Verification Evidence

All commands ran from `D:\CODE\local-ai-dev-orchestrator` on 2026-07-12.

| Gate | Command | Exit | Key result |
|---|---|---:|---|
| JSON inventory | `python -m json.tool docs/specs/local-ai-runtime-0.2-normative-package.json` | 0 | valid JSON |
| JSON work graph | `python -m json.tool docs/plans/local-ai-runtime-0.2-work-items.json` | 0 | valid JSON |
| JSON planning state | `python -m json.tool docs/architecture/planning-status.json` | 0 | valid JSON |
| JSON selector policy | `python -m json.tool docs/architecture/next-work-selection-policy.json` | 0 | valid JSON |
| script parse | `python -m py_compile scripts/verify-planning-status.py scripts/select-next-work.py` | 0 | no syntax error |
| Python lint | `uv run --project ./runtime/host-orchestrator ruff check scripts/verify-planning-status.py scripts/select-next-work.py runtime/host-orchestrator/tests/test_planning_governance.py` | 0 | all checks passed |
| focused governance | `uv run --project ./runtime/host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_planning_governance.py -q` | 0 | 23 passed |
| full legacy test | `uv run --project ./runtime/host-orchestrator python -m pytest` | 0 | 181 passed |
| contract/invariant | `python scripts/verify-planning-status.py` | 0 | v3.21, 158485 bytes, 14 missing artifacts, 58 work items, `LAR-P0A-001` |
| read-only selector | `python scripts/select-next-work.py` | 0 | `close_baseline_normative_package_first`, no side effects, no preflight |
| governance preflight | `pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit` | 0 | test/contract/selector/scripts/diff passed |
| whitespace/error markers | `git diff --check` | 0 | no error |

Normative identity was also checked with Python `hashlib`, PowerShell `Get-FileHash`, and a byte-policy validator covering encoding, BOM, CR/LF, NFC, controls, trailing whitespace and terminal LF. Both hash paths returned `1BFB5CD2C92C036804A6005D5B36CDD5ACC6BEDC4D6BF4070CCFB7A70CE063FB`.

## N/A Gates

### Build

- `status`: `gate_na`
- `reason`: this v3.21 slice changes candidate planning artifacts and `runtime/local-ai-runtime` does not exist yet
- `alternative_verification`: full legacy pytest, planning verifier, selector and governance preflight
- `evidence_link`: `docs/specs/acceptance-and-gates.md` and this file
- `expires_at`: `LAR-P0D-001` creates `runtime/local-ai-runtime`

### Hotspot

- `status`: `gate_na`
- `reason`: this v3.21 slice changes planning contracts rather than executable runtime hot paths
- `alternative_verification`: focused planning governance tests, full legacy pytest, verifier, selector and `git diff --check`
- `evidence_link`: `docs/specs/acceptance-and-gates.md` and this file
- `expires_at`: the first executable runtime slice after `LAR-P0D-001`

## Residual Risks And Stop Conditions

- Fourteen normative artifacts are still missing. Planning green is not Baseline Approval.
- Exact v3.17 source bytes and both conflicted v3.18 texts must be archived during `LAR-P0A-001`; provisional transcript hashes cannot be promoted. Missing bytes stop closure.
- The planned contracts are intentionally more detailed than the current implementation. No implementation task may start before active, non-revoked Baseline Approval, Truth Reset and Legacy Ownership Guard prerequisites.
- Current host-orchestrator tests prove only legacy compatibility and planning-control correctness. They do not prove Codex/Windows/Git Full Q0 behavior.
- Any candidate narrative byte change requires a new candidate ID and synchronized planning identity. Any present normative artifact semantic change requires a new artifact version and manifest generation.

## Rollback

Revert only the v3.21 candidate-planning projection, selector/verifier tests and this evidence. Preserve exact v3.19/v3.20 archives, all legacy runtime behavior, `.ai` state/config, historical evidence and unrelated user changes. Do not create, revoke or supersede an approval record as part of rollback.
