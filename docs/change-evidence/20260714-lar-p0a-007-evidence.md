# LAR-P0A-007 Evidence And Backup Contract Closeout

## Goal And Boundary

- Work item: `LAR-P0A-007` from `LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE`.
- Frozen narrative: `local-ai-runtime-0.2-v3.23`, `188325` bytes, SHA-256
  `80562322ebc744eda2a87a17c45f73a11982f4947c9d10e8628bb6f73ee9d5c6`.
- Result: close offline event, journal, artifact, receipt, external evidence, key-envelope,
  backup and restore contracts without starting the new runtime.
- Out of scope: raw process persistence, live evidence publication, DPAPI/keyring access,
  backup/restore execution, `.ai/config`, approval, Truth Reset, remote writes and final
  `BaselineManifest.v1.json` creation.

## Frozen Artifacts

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `EvidenceContractSet.v1.json` | 9656 | `d9cea69a4680a0229b5680ea0de503e9d6f9d24eb6232893b727e11c1e52e9e0` |
| `NormalizedExecutionEvent.v1.schema.json` | 10832 | `45ab72fca886dca978473de0d9b43c3475a64bb0104a4f30bd8c4556f8b99591` |
| `EventStatusMatrix.v1.json` | 13212 | `7508aa4061f9526d53b7e547125792016f08748078fb2cffbbcafb517fc6d7d7` |
| `fixtures/evidence/manifest.json` | 22916 | `92c649b58d25391c5968fc0f64e6344e40933a91fa5957dcd346f052d67461aa` |

The canonical policy is exact-byte pinned. The schema and catalog close all 16 v1
event/status pairs, including separate completed and failed `process_exited` rows. Every
row explicitly partitions the 26 event-specific fields into required, optional and
forbidden sets.

## Closed Decisions

### Secret-Safe Event And Journal

- `NormalizedExecutionEvent.v1` is append-only, rejects null optional values and hashes the
  canonical event excluding `event_hash` under
  `local-ai-runtime/NormalizedExecutionEvent/v1`.
- Before path/content scan, mutation persistence is limited to a random observation ID,
  byte count, enum path class and an approved path ID only after successful mapping.
- Raw JSONL/stdout/stderr, prompt, reasoning, argv/environment, tool text, partial bytes and
  their content hashes remain forbidden in normal state and quarantine.
- Journal ordering is event append -> `FlushFileBuffers` -> short SQLite cursor transaction;
  the database may lag but cannot lead the flushed journal.
- `ExecutionReceipt.v1` requires the conjunction of process exit, stdout JSONL EOF, final
  schema pass, no output/resource overflow, sealed normalized chain/segments and Job
  zero-process.

### Artifact, External Evidence And Keys

- Artifact publication is immutable spool flush -> durable outbox/fenced intent ->
  no-replace publish -> read-back identity -> immutable terminal. `os.replace` is forbidden.
- `runtime_external_v1` is bound to the current `ActiveRuntimeIdentity` composition and the
  managed `%LOCALAPPDATA%\LocalAIRuntime\evidence` root. It is no-follow identity/ancestry/
  alias-disjoint from repo, Git, worktrees, attempts and controller-sensitive roots.
- Writer/gate/task payloads cannot read or write evidence. Only the current-fence controller
  publisher may publish, and target-repo contract acceptance is mandatory.
- `QuarantineKeyEnvelope.v1` and `RuntimeIntegrityKeyEnvelope.v1` use independent 256-bit
  keys, distinct purposes and current-user DPAPI scope. Plaintext keys and ordinary key
  hashes never enter state, evidence or logs.

### Backup And Restore Anti-Rollback

- Backup capture excludes credentials, sandbox mutable material, environment content,
  worktrees, raw output, ordinary quarantine, live spool and nonterminal state.
- A production-eligible head requires suspension before backup, an unchanged control
  generation through capture and no later resume. Online backups are restore-drill-only.
- Every later authoritative mutation creates and flushes immutable
  `BackupPostActivity.v1`, then CAS-stales the eligible head before the mutation begins.
- Production restore creates and flushes one immutable `BackupRestoreIntent.v1`, then uses
  the single `eligible -> restoring -> consumed` CAS chain. Response loss can continue only
  the same intent.
- Missing sidecars, copied backups, post-activity markers, generation/identity drift,
  ambiguous state or a second intent fail closed to restore-drill-only. Deleting markers,
  rolling back heads, copying old backup roots and force restore are forbidden.

## Verification Evidence

| Check | Result |
| --- | --- |
| `python scripts/verify-local-ai-runtime-baseline.py --component evidence` | exit `0`; exact four-file identities; 16 event/status pairs; 3-event hash chain; 57 transition/security cases |
| Draft 2020-12 schema self-check and all pair examples | exit `0`; 16 pairs plus hash chain valid |
| evidence-focused pytest | exit `0`; `17 passed in 1.33s` |
| evidence plus planning-governance pytest | exit `0`; `94 passed in 13.36s` |
| `python scripts/verify-planning-status.py` | exit `0`; status SHA-256 `153d1ec410b1dc2e320b52328dac49ac41d1cb7fcb7ceb5e77d3b0d37bf2a62f` |
| `python scripts/select-next-work.py` | exit `0`; `LAR-P0A-008`; `side_effects_performed=false` |
| `pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit` | exit `0`; `295 passed in 61.94s`; planning contract, selector, Python/PowerShell parsing and diff checks passed |
| `git diff --check` | exit `0` |

Build is `gate_na`: `reason=runtime/local-ai-runtime does not exist before LAR-P0D-001`;
`alternative_verification=host-orchestrator pytest plus component/planning verifiers`;
`evidence_link=this record`; `expires_at=LAR-P0D-001`. Hotspot is `gate_na`:
`reason=no executable runtime hot path changed`;
`alternative_verification=component fixtures, planning verifier, selector, tests and diff review`;
`evidence_link=this record`; `expires_at=first executable slice after LAR-P0D-001`.

## Truth Projection

- Normative package: `15 required / 7 present / 8 missing`.
- `LAR-P0A-007`: `completed`.
- `LAR-P0A-008`: `ready` and uniquely selected by
  `close_baseline_normative_package_first`.
- `P0A-VERIFIER` remains `in_progress`; `P0A-MANIFEST` and `P0A-REVIEW` remain missing.
- Baseline Approval remains inactive; Truth Reset and implementation remain not started.

## Safety And Rollback

No process output, credential, DPAPI/keyring value, evidence root, backup directory,
`CODEX_HOME`, sandbox state, `.ai` runtime state or remote system was read or changed. The
Windows host exposed an extensionless `jq` executable as a document; the resulting open-with
dialog was closed and canonical formatting used the existing Python runtime instead. This did
not alter contract content or host associations.

Rollback is `git revert <LAR-P0A-007 commit>`. It removes only this contract bundle,
component verifier/tests, evidence and planning projections while preserving earlier P0A
artifacts and the frozen v3.23 narrative bytes.
