# LAR-P0A-004 Product, Routing and Submission Evidence

## 1. Identity and boundary

- Baseline: `local-ai-runtime-0.2-v3.23` (`baseline_candidate`)
- Task: `LAR-P0A-004`
- Artifact: `P0A-PRODUCT / ProductContract.v1`
- Artifact identity: `5003` bytes / `b239cee308681ac5972e494ad4ff76958623fbd558a47e03b95e0be4159fb1ef`
- Successor: `LAR-P0A-005 / close_baseline_normative_package_first`

| File | Bytes | SHA-256 |
|---|---:|---|
| `ProductContract.v1.json` | 5003 | `b239cee308681ac5972e494ad4ff76958623fbd558a47e03b95e0be4159fb1ef` |
| `TaskTemplate.v1.schema.json` | 3956 | `a9332c772cc64b4e3530ff52afa1f4137c696d500bf2a35cf9c02af58d489ab3` |
| `BatchSubmission.v1.schema.json` | 1424 | `4b7285427ac4878bca9e20a84f2774a31783a8499cccb71d1ebeac8e60c5b3fd` |
| submission `manifest.json` | 7411 | `cd9787660be95db2e1ce8ff8b303eee8e819f8567582cbc5f406e32cce715cf1` |
| `verify-local-ai-runtime-baseline.py` | 91308 | `95df93854e63d498d7b32067c53f5ecfae546875f69ebec6e7f06ee75a79631a` |
| `test_baseline_product_submission.py` | 6055 | `b897c104dd5abc36524710db0fa62cf3d57083a24a4ab3b0ca60d817918466dd` |

This slice materializes one normative product/routing/submission bundle plus two schemas,
closed fixtures and its verifier component. It does not create `BaselineManifest.v1.json`,
approval, Truth Reset, `runtime/local-ai-runtime`, task execution, live Batch evidence or any
remote effect. The frozen v3.23 narrative bytes remain unchanged.

## 2. Product and routing closure

`ProductContract.v1` replaces ambiguous speed/autonomy claims with an ordered objective:
safety/effect correctness/evidence first, then net operator minutes, unattended verified
closeout rate, Native latency and Batch cycle time, and attributable cost/rework. Epoch 1 Batch
is deterministic host-local commit-only throughput, not high-speed concurrency.

`WorkRoutingPolicy` returns only one of `native_direct`, `native_spec`, `native_program` or
`batch`. Model, reasoning effort, provider, execution interface and capability generation remain
owned by separately qualified `ExecutionProfile` generations. This slice adds neither a second
planner nor a runtime model-router service.

## 3. Template, submission and replay closure

- `TaskTemplate` permits only low-risk host-local Batch templates with versioned prompt identity
  and closed boolean/integer/enum/public-ID/approved-path-ID parameters or bounded arrays.
- Parameters cannot control executable, argv, environment, permission roots, gates, Git policy
  or refs, model/provider, sandbox, features, Authorization or contract generation.
- `BatchSubmission` has exactly four fields and a domain-separated canonical fingerprint. Before
  first successful admission the fingerprint stays volatile and rejected input is not retained.
- Existing-family lookup and authorized integrity-checked replay occur before later catalog,
  scanner, qualification, environment or Authorization guards. Ordinary duplicate submission
  permanently returns the immutable generation-0 root task.
- `TaskResubmission` checks an existing relation first; historical task-ref success permanently
  blocks another successor. A valid successor is generation+1 and is created atomically with the
  immutable resolution/relation and family-current CAS.

Positive submission fingerprint:
`2b5a0b0d6b69a20f22f87de73ed7311bfb26700b1a46a6b0ea4ae58b53eead20`.

## 4. Fixture matrix

| Fixture class | Count | Coverage |
|---|---:|---|
| TaskTemplate positive / negative | 1 / 4 | closed template, free text, top-level model, reserved parameter, duplicate parameter |
| BatchSubmission positive / negative | 1 / 5 | exact envelope, top-level model, free prompt, float, nested object, uppercase base |
| Work routing | 6 | eligible Batch, free prompt/high risk Native, direct/spec/program precedence |
| Existing-family replay | 4 | stable root replay, denied/integrity boundary, absent-family transaction/rejection |
| Resubmission | 5 | existing relation, non-current/completed/historical blockers, valid atomic successor |

Policy, both schemas and the fixture manifest are exact byte/hash identities. Malformed nested
fixture variants cannot replace a required coverage case or leak a Python implementation
exception; component verification rejects them as `ValidationFailure`.

## 5. Red/green and review evidence

- Red: before implementation, the CLI rejected `--component product-submission` as an unknown
  component.
- Initial green: five product component tests passed with the exact artifact identity, fixture
  counts and fingerprint.
- Review finding: the first green verifier pinned policy and schema bytes but not the fixture
  bytes even though closure evidence depended on the exact matrix. A structurally self-consistent
  fixture could therefore weaken coverage. The verifier now pins the fixture identity too, and
  three malformed nested fixture mutations extend the regression matrix.
- Final focused green: product tests report `11 passed`; product plus canonicalization report
  `15 passed`; planning governance reports `77 passed`.

## 6. Verification

- `python scripts/verify-local-ai-runtime-baseline.py --component product-submission`: pass;
  exact policy identity, fingerprint and `4 / 5 / 6 / 5 / 1 / 4 / 1` fixture counts returned.
- `uv run --project ./runtime/host-orchestrator python -m pytest`: pass in release-style
  preflight.
- `python scripts/verify-planning-status.py`: pass; status SHA-256
  `bb267f3b025d096f8afc29b5713b8471caf9382b186db9806df37ee38e5d5735`, current work item
  `LAR-P0A-005`, missing artifact count `11`.
- `python scripts/select-next-work.py`: pass; unique result
  `close_baseline_normative_package_first / LAR-P0A-005`, zero side effects.
- `python scripts/verify-local-ai-runtime-baseline.py --json`: expected exit `3`,
  `status=incomplete`, `reason=standalone_verifier_not_frozen`; implemented components are only
  manifest self-test, canonicalization and product/submission.
- JSON parsing, Python compilation and `git diff --check`: pass.
- `pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1
  -DisableAutoCommit`: pass on the evidence-complete tree; full tests, planning contract/selector,
  Python and PowerShell parsing and diff checks pass. Build and hotspot remain the declared
  `gate_na` below.

## 7. Five-axis review

- Correctness: acceptance clauses are represented by fixed policy fields and positive/negative
  fixtures; planning truth and selector advance only after artifact identity verification.
- Readability: product, template, submission, family and resubmission concepts remain separate in
  the normative payload; verifier helpers follow those same boundaries.
- Architecture: no runtime code, planner, router or live configuration was added. The standalone
  verifier remains the existing preapproval entry and `P0A-VERIFIER` remains `in_progress`.
- Security: closed parameters, volatile pre-admission fingerprints, no rejected-input retention,
  authorized replay and fixture integrity fail closed. No dependency or credential was added.
- Performance: all loops are bounded by fixed template/submission/fixture limits and this slice is
  outside the runtime hot path. No high-speed or concurrency claim is made.

## 8. N/A and remaining truth

- Build: `gate_na`; `reason=preapproval contract slice and runtime/local-ai-runtime does not
  exist`; `alternative_verification=component verifier + host-orchestrator full pytest`;
  `evidence_link=this record`; `expires_at=LAR-P0D-001`.
- Hotspot: `gate_na`; `reason=no executable runtime hot path changed`;
  `alternative_verification=component/planning verifiers, selector, tests and diff review`;
  `evidence_link=this record`; `expires_at=first executable slice after LAR-P0D-001`.
- Normative package after routing: `15 required / 4 present / 11 missing`.
- `P0A-VERIFIER` remains `in_progress`; `P0A-MANIFEST` and `P0A-REVIEW` remain missing.
- Baseline Approval remains inactive and no model/profile/runtime authority changed.

## 9. Rollback

Revert only this slice: remove the product policy, two schemas, fixture and product verifier
component; restore `P0A-PRODUCT` to missing; return `LAR-P0A-004` to ready and `LAR-P0A-005` to
pending; and restore current-task projections. Do not alter frozen v3.23/lineage/canonicalization
bytes, `.ai/config`, live state or legacy runtime behavior.
