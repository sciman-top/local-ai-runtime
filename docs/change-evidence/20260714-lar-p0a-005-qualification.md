# LAR-P0A-005 Qualification, Sandbox and Authorization Evidence

## 1. Identity and boundary

- Baseline: `local-ai-runtime-0.2-v3.23` (`baseline_candidate`)
- Task: `LAR-P0A-005`
- Artifact: `P0A-QUALIFICATION / QualificationContractSet.v1`
- Artifact identity: `7336` bytes / `089a60664188fdc86c0de56496c493339246c5b423ddc3271450fb01e4fd6a80`
- Successor: `LAR-P0A-006 / close_baseline_normative_package_first`

| File | Bytes | SHA-256 |
|---|---:|---|
| `QualificationContractSet.v1.json` | 7336 | `089a60664188fdc86c0de56496c493339246c5b423ddc3271450fb01e4fd6a80` |
| `QualificationSensitiveInputSet.v1.schema.json` | 5043 | `e3a85cdec3ef2f1b2ed079366bbc12e490fa3d0015a2b18ca205fe6f724ba063` |
| `Authorization.v1.schema.json` | 3165 | `c911db9d05009c892bce01f4b241fd6cad2bb043a77279d7c73f2026407f8558` |
| qualification `manifest.json` | 13387 | `8074b2fa4a529190d2bb9bc8cc0b5c8020adc878b899e6a2676824468d046b68` |
| `verify-local-ai-runtime-baseline.py` | 127464 | `d4ade223752302d5ba7d77ba4ab8a19c33a23c21f7204683f9444c6a866167f2` |
| `test_baseline_qualification.py` | 7464 | `81fe71d6c2b84deffd2f5a6e1f8e97a4fc597426615f5cf9c3e8bdc508742c7a` |

This slice materializes qualification, immutable environment/public sandbox binding, auth-state,
reusable Authorization, exact effect-grant and continuation contracts. It does not inspect or
change the live keyring, `CODEX_HOME`, `.sandbox`, `.sandbox-secrets`, auth/provider config,
runtime state or any process. It creates no Authorization, grant, approval, Truth Reset,
`runtime/local-ai-runtime`, Batch run or live evidence.

## 2. Official-source boundary

The current Codex manual was refreshed through the official manual helper on 2026-07-14. The
relevant public facts are:

- [Environment variables](https://learn.chatgpt.com/docs/config-file/environment-variables.md):
  `CODEX_HOME` is a composite root for config, auth, logs, sessions, skills and other state.
- [Authentication](https://learn.chatgpt.com/docs/auth): credential storage supports
  `file`, `keyring` and `auto`; `auth.json` contains tokens when file storage is used.
- [Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox.md): the preferred
  elevated native sandbox uses dedicated lower-privilege sandbox users and OS boundaries.

The public manual does not establish a field schema for the Windows helper's
`.sandbox/sandbox.log`. Therefore this baseline does not parse or depend on one. Keyring-only
Batch auth, the three-role `CODEX_HOME` projection, secret-metadata non-export and opaque bounded
diagnostic policy are narrower Local AI Runtime requirements that still require real Full-Q0
qualification; they are not claims about undocumented Codex internals.

## 3. Qualification and environment closure

- `QualificationSensitiveInputSet` has a closed present/absent/expanded/blocked entry union,
  ordered by entry kind, subject and rule ID. Resolver catalog, negative discovery and collision/
  alias policy generation are bound; ordinary source, observation base, task and submission IDs
  are excluded.
- `QualificationObservation` owns expected base commit/tree, dirty-tree and alias/identity probe
  evidence. Byte-identical safety bindings on a fresh base CAS-refresh observation/base without
  incrementing qualification or Authorization generation.
- Sensitive/protected/approved paths or ancestors that are staged, modified, deleted, untracked
  or ignored block qualification. Unrelated dirty state is retained only as aggregate class/count,
  never as a working-tree content hash in Authorization.
- `QualifiedEnvironmentBinding` is immutable and content addressed. Batch may verify/attach it but
  cannot install, restore, bootstrap, run package-manager setup or use a shared writable dependency
  cache.

## 4. Sandbox, auth and Authorization closure

- Public sandbox binding separates read-only content-addressed config, mutable `.sandbox` state and
  broker-only `.sandbox-secrets`; secret content and metadata have no public projection.
- `sandbox.log` is opaque, task-deny-read, limited to 8 MiB/file and 32 MiB aggregate with retention
  four. Content/hash never enters ordinary state/evidence; over-limit rotation failure stops new
  claim and creates an operator action. Export is interactive, temporary and secret-scanned.
- Batch auth permits only `cli_auth_credentials_store=keyring`; `file` and `auto` fallback fail.
  Public AuthState excludes credential content/hash/mtime and keyring/proxy metadata.
- Authorization excludes task, submission, ordinary base, derived commit/ref and evidence ID. Its
  independently recomputed domain-separated fingerprint is
  `a166aedb3c65e4bcf3d0e2cde0d798f6d646b44df50b2d5cd45386841d84b1eb`.
- Revoke and root effect grant share repo-lock/transaction linearization. Root basis is
  `active_authorization`; a committed grant can only complete, terminate or read-only reconcile
  its exact effect. Inherited fenced-action basis cannot authorize writer, GateRun, model decision,
  qualification, auth refresh or arbitrary command.
- Continuation can resume only the eight closed controller closeout stages, with one successor per
  prior head. It cannot expand path/parameter/gate/model/policy or restart writer/terminal stages.

## 5. Fixture matrix

| Fixture class | Count | Coverage |
|---|---:|---|
| Sensitive entry kinds | 4 | present, absent, expanded and qualification-blocking entry |
| Observation refresh | 4 | byte-identical CAS refresh, binding change, alias drift, stale observation |
| Working tree | 4 | clean, sensitive dirty, approved-path dirty, unrelated aggregate-only dirty |
| Auth store | 4 | keyring pass, file/auto reject, keyring unavailable Q0 failure |
| Sandbox projection | 6 | public pass, secret/log export, read bypass, whole-root immutability, log limit |
| Grant/revoke | 5 | later revoke, revoke-first, effect mismatch, duplicate resume, inherited writer |
| Continuation | 5 | valid closeout, writer restart, expansion, head conflict, terminal reopen |

Policy, both schemas and the fixture manifest have exact identities. Direct validator regressions
also cover base/task identity injection, entry reordering, `.lock`/`..` Git refs, unknown discovery
state, invalid Authorization fingerprint/UTC, sandbox secret metadata and Batch install expansion.

## 6. Red/green evidence

- Red: the first focused test failed because `qualification` was not a valid verifier component.
- Canonicalization red: the first policy draft had one pair of `qualifi...` object keys in the wrong
  UTF-8 order. Mechanical recursive key sorting retained all values and produced the final identity.
- Boundary red: review found incomplete checked-in Git-ref rejection and non-calendar Authorization
  timestamp acceptance. The verifier/schema/tests now reject both classes.
- Green: the qualification component returns the exact artifact identity, Authorization fingerprint
  and fixture counts above; `test_baseline_qualification.py` reports `16 passed`.

## 7. Verification

- `python scripts/verify-local-ai-runtime-baseline.py --component qualification`: pass.
- Qualification, product and planning focused tests: `102 passed` before the final boundary cases;
  final qualification-only matrix: `16 passed`.
- `uv run --project ./runtime/host-orchestrator python -m pytest`: `266 passed in 56.61s`.
- `python scripts/verify-planning-status.py`: pass; status SHA-256
  `ad8bfbd90198032109d90c870772afd1684ed1bbda986d2eaba0a3ba0a8fc76e`, current work item
  `LAR-P0A-006`, missing artifact count `10`.
- `python scripts/select-next-work.py`: pass; unique result
  `close_baseline_normative_package_first / LAR-P0A-006`, zero side effects.
- `python scripts/verify-local-ai-runtime-baseline.py --json`: expected exit `3`,
  `status=incomplete`, with only manifest self-test, canonicalization, product/submission and
  qualification components implemented.
- JSON parsing, Python compilation, stale-current-truth scan and `git diff --check`: pass.
- `pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1
  -DisableAutoCommit`: pass on the evidence-complete tree; full tests, planning contract/selector,
  script parsing and diff checks pass. Build and hotspot remain the declared `gate_na` below.

## 8. Five-axis review

- Correctness: every machine acceptance clause has a fixed policy field and/or bounded case; IDs,
  UTC values and Authorization fingerprint are independently recomputed.
- Readability: sensitive set, environment, sandbox/auth, Authorization grant and continuation are
  distinct records and helpers rather than a generic policy engine.
- Architecture: no runtime, planner, router, auth broker or new dependency was added. The existing
  standalone verifier remains `in_progress`; its final freeze/decomposition decision stays with the
  dedicated verifier closure task rather than adding another preapproval control plane now.
- Security: exact fields reject task/base coupling, file/auto auth, secret metadata, opaque-log
  content/hash, contract expansion and wrong effect identity. No credential material was read.
- Performance: traversal/resource limits are fixed and case loops are bounded; this contract-only
  slice is outside the runtime hot path and makes no throughput claim.

## 9. N/A and remaining truth

- Build: `gate_na`; `reason=preapproval contract slice and runtime/local-ai-runtime does not
  exist`; `alternative_verification=component verifier + host-orchestrator full pytest`;
  `evidence_link=this record`; `expires_at=LAR-P0D-001`.
- Hotspot: `gate_na`; `reason=no executable runtime hot path changed`;
  `alternative_verification=component/planning verifiers, selector, tests and diff review`;
  `evidence_link=this record`; `expires_at=first executable slice after LAR-P0D-001`.
- Normative package after routing: `15 required / 5 present / 10 missing`.
- `P0A-VERIFIER` remains `in_progress`; `P0A-MANIFEST` and `P0A-REVIEW` remain missing.
- Baseline Approval remains inactive. Full Q0 has not proved keyring, sandbox principal/ACL,
  secret deny-read, opaque-log rotation or live Authorization behavior.

## 10. Rollback

Revert only this slice: remove the qualification policy, two schemas, fixture and qualification
verifier component; restore `P0A-QUALIFICATION` to missing; return `LAR-P0A-005` to ready and
`LAR-P0A-006` to pending; and restore current-task projections. Do not alter frozen v3.23,
lineage/canonicalization/product bytes, `.ai/config`, live auth/sandbox state or legacy runtime.
