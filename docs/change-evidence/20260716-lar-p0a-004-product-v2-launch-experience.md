# LAR-P0A-004 ProductContract.v2 and Launch Experience

## Scope and truth boundary

This atomic P0A closeout materializes the v3.24 product contract without implementing or approving the runtime. It creates `ProductContract.v2`, `FirstRunExperiencePolicy.v1`, `LaunchTemplateCatalog.v1`, `OperatorPresentationCatalog.v1`, positive/negative fixtures and a stdlib-only component verifier. It does not edit the frozen v3.24 narrative or `ProductContract.v1`, create `runtime/local-ai-runtime`, activate a template, issue an Authorization or approval, read live credentials, execute a Batch task, publish a real Git ref, use the network or change legacy runtime behavior.

## Closed product decisions

- The first-run journey has ten ordered CLI steps from read-only setup readiness through a reviewable deterministic local commit and runtime-owned task ref.
- Every mutation returns an effect summary, authority, expected generation, rollback entrypoint and challenge requirement; read-only commands never require approval.
- Stable JSON is the automation contract. Human output is rendered only from public machine state, reason codes and public locators through a versioned catalog.
- Exactly four candidate templates exist: `docs_contract_sync_v1`, `bounded_lint_type_repair_v1`, `focused_test_repair_v1` and `mechanical_repo_maintenance_v1`.
- Every template closes parameters, path/effect envelope, required/forbidden gates, expected outputs, stop reasons, recovery, rollback and an evaluation denominator retaining unknowns.
- Native Spec may create only a candidate definition. Promotion requires negative examples, disposable dry-run, repo/template qualification, explicit operator promotion and reusable Authorization.
- Eight launch product metrics define denominator, collection point and unknown handling; all targets remain `null` until measured and accepted.

## Frozen artifact identities

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `ProductContract.v2.json` | 14902 | `ef93061279accfd6af7a580d1eafbb3352bf8a8a4f610f7bcd86006643a9bcae` |
| `FirstRunExperience.v1.schema.json` | 5080 | `1f5ebdc4bc33bc5a145bdb6331e11275688e783ab895ab0bb5f9dece965ac462` |
| `LaunchTemplateCatalog.v1.json` | 9371 | `dd6d0065bc00aa13f4427c650050c39604c13e4c933966c6efe812590b5d861e` |
| `OperatorPresentationCatalog.v1.json` | 5701 | `c028d50742f1d55005310eb542875bfd00d255c3101a2cc08fcc4fc76fb2db8e` |
| `product-v2/manifest.json` | 3092 | `4775a5c0075a3c2146c9792930de15c058cd77e913ae3c15826df4de9f345ce5` |
| frozen predecessor `ProductContract.v1.json` | 5003 | `b239cee308681ac5972e494ad4ff76958623fbd558a47e03b95e0be4159fb1ef` |

## Negative coverage

Twelve executable mutations fail closed: free prompt, dynamic command, dependency installation, push/remote expansion, secret-bearing parameter, promotion bypass, raw model output, raw tool output, read-only approval, dropping unknowns, claiming an unmeasured target and adding a fifth BatchSubmission field. Independent identity-drift tests cover every v2 bundle member; legacy v1 drift tests remain green.

## Verification

| Command | Result |
|---|---|
| `python scripts/verify-local-ai-runtime-baseline.py --component product-submission` | pass; v2=`14902 / ef930612...9bcae`, v1 predecessor=`5003 / b239cee3...fb1ef`, 10 steps, 4 templates, 5 views, 8 reasons, 8 metrics, 5 positive and 12 negative fixtures |
| `uv run --project ./runtime/host-orchestrator python -m pytest` | pass; 301 tests |
| `python scripts/verify-planning-status.py` | pass; package `7/15`, 8 missing, current `LAR-P0A-005` |
| `python scripts/select-next-work.py` | pass; `close_baseline_normative_package_first / LAR-P0A-005`, no side effect, no nested preflight |
| `python -m py_compile ...` | pass for the baseline verifier, v2 helper, planning verifier, selector and changed tests |
| `pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit` | pass; build/hotspot explicit `gate_na`, all executable planning gates green |
| `git diff --check` | pass |

The first full-suite run found one stale governance-test token from the predecessor metric wording. The source contract and doc contract already used the v2 metric set, so the regression assertion was corrected to require `recovery_to_terminal_time`; the rerun passed all 301 tests. No gate, expected result or frozen artifact was weakened.

## Compatibility and rollback

`ProductContract.v1` remains byte-identical and is verified before v2 on every component run. Rollback reverts only the five v2 artifacts, `scripts/product_v2_contract.py`, the verifier wrapper/tests and current inventory/status/docs/evidence projections. It must restore `LAR-P0A-004=ready`, `LAR-P0A-005=pending` and must not rewrite the frozen v3.24 narrative, predecessor artifacts or prior rebaseline commit.

## Residual boundary

The package becomes `7/15 present, 8 non-present`; it remains approval-ineligible. The next selector item is `LAR-P0A-005`, which must materialize `QualificationContractSet.v2` and exact toolchain gates without preparing a live environment or downloading Python/dependencies.
