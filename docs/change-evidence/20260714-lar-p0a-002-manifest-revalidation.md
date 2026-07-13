# LAR-P0A-002 v3.23 BaselineManifest Revalidation Evidence

## 1. Identity and boundary

- Baseline: `local-ai-runtime-0.2-v3.23`
- Task: `LAR-P0A-002`
- Queue: `LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE`
- Result scope: revalidate the retained manifest schema, non-final fixture and fail-closed verifier skeleton against frozen v3.23 identities
- Successor: `LAR-P0A-003 / close_baseline_normative_package_first`

This slice does not create `BaselineManifest.v1.json`, an approval record, Truth Reset, `runtime/local-ai-runtime`, Q0, a Batch claim, a writer, a publication action or live evidence. `P0A-MANIFEST` remains missing and `P0A-VERIFIER` remains `in_progress` until `LAR-P0A-012`. The normative package therefore remains 15 required / 2 present / 13 missing and the decision remains **Request changes**.

## 2. Frozen inputs and revalidated files

Frozen inputs were read without normalization:

| Input | Bytes | SHA-256 |
|---|---:|---|
| v3.23 narrative | 188325 | `80562322ebc744eda2a87a17c45f73a11982f4947c9d10e8628bb6f73ee9d5c6` |
| `BaselineLineage.v2.json` | 3495 | `49141a69c9aed6065ba063714fb2349750e500199ed8dfaf64fa6e2b198b9043` |

Revalidated contract files after the focused implementation:

| File | Bytes | SHA-256 | Disposition |
|---|---:|---|---|
| `docs/specs/local-ai-runtime-0.2/normative/BaselineManifest.v1.schema.json` | 3475 | `d8bb03fc470c334ce9c8bfd5176a359bfaa7a44d59e0a60ac58de04febbc3709` | unchanged; contract remains sufficient |
| `docs/specs/local-ai-runtime-0.2/fixtures/baseline-bytes/manifest.json` | 3895 | `f0a1f01c4ce285c4be3f73babd84543a907a23202eef2b44cd062a2af75a2b10` | rebound from v3.22 to v3.23/Lineage.v2 |
| `scripts/verify-local-ai-runtime-baseline.py` | 20518 | `fae0617255e19fcc4afdca082106d7659b7c4f2f3b568f9c3174a88df215da70` | exact fixture and on-disk identity checks added |

The schema and verifier skeleton remain mutable preapproval contract machinery. They are not present normative artifacts merely because this component self-test passes.

## 3. Contract decisions

- The positive fixture uses `manifest_id=local-ai-runtime-0.2-v3.23-fixture` and `narrative_specification_id=local-ai-runtime-0.2-v3.23`.
- The fixture contains exactly `P0A-SOURCE` and `P0A-LINEAGE`; every field must match the v3.23/`BaselineLineage.v2` binding table.
- The verifier reads both repository files, applies the normative byte policy and compares byte count plus SHA-256 to their frozen identities.
- The existing domain envelope, closed payload fields, unique artifact IDs/paths, frozen `package_review_head`, self-reference prohibition and 1/7/8 positive/structural-negative/byte-negative fixture semantics are unchanged.
- Default package verification continues to return `incomplete / standalone_verifier_not_frozen` with exit 3. This is required fail-closed behavior, not a failed task result.

## 4. Acceptance mapping

| Acceptance | Mechanical evidence |
|---|---|
| Reject BOM, CR, non-NFC, trailing SP/HTAB, controls and bad terminal LF | Eight byte-negative fixtures execute through `validate_normative_bytes`. |
| Reject duplicate artifact IDs and paths | Seven structural fixtures include exact duplicate-ID/path rejection and closure-cycle cases. |
| Require complete entry identity | Schema and runtime validator require all eight artifact identity fields. |
| Bind the retained fixture to v3.23 | `_verify_fixture_bindings` requires exact manifest/spec IDs, exact `P0A-SOURCE`/`P0A-LINEAGE` entries and actual file identities. |
| No final manifest; package remains incomplete | Component self-test proves absence; inventory remains `P0A-MANIFEST=missing`, `P0A-VERIFIER=in_progress`. |

## 5. Red-green evidence

| Command | Result |
|---|---|
| focused test before implementation | exit 1; expected payload lacked `bound_artifact_count` and `narrative_specification_id` |
| focused test after implementation | exit 0; `1 passed` |
| binding identity/byte-drift regression | exit 0; v3.22 identity and altered source bytes both fail with their stable reasons |
| `python scripts/verify-local-ai-runtime-baseline.py --component manifest --self-test` | exit 0; v3.23, 2 bound artifacts, 1/7/8 fixtures, final manifest absent |
| `python scripts/verify-local-ai-runtime-baseline.py --json` | exit 3; `status=incomplete`, `reason=standalone_verifier_not_frozen` |

## 6. N/A and unchanged surfaces

- Build: `gate_na`; `reason=preapproval contract slice and runtime/local-ai-runtime does not exist`; `alternative_verification=legacy full pytest plus schema/verifier self-test`; `evidence_link=this record`; `expires_at=LAR-P0D-001`.
- Runtime hotspot: `gate_na`; `reason=no runtime execution path changed`; `alternative_verification=planning governance tests, verifier, selector, preflight and diff review`; `evidence_link=this record`; `expires_at=first executable slice after LAR-P0D-001`.
- `.ai/config`, `.ai/state/control-plane.db`, legacy runtime behavior, host-local Codex processes, auth/provider state and live repositories were not changed.

## 7. Rollback

Revert only this task slice: restore the v3.22-bound positive fixture and prior verifier skeleton, return `LAR-P0A-002` to ready and `LAR-P0A-003` to pending, and restore the prior current-task documentation. Frozen v3.23/lineage bytes, the historical 2026-07-12 v3.22 evidence, inventory, legacy runtime, `.ai/config` and live state remain untouched.

## 8. Final gate evidence

| Gate | Result |
|---|---|
| Manifest focused regressions | exit 0; 2 passed, including stale identity and byte-drift rejection |
| Manifest component self-test | exit 0; v3.23, 2 bound artifacts, 1 positive, 7 structural-negative and 8 byte-negative fixtures; final manifest absent |
| Full-package fail-closed probe | exit 3; `status=incomplete`, `reason=standalone_verifier_not_frozen` |
| Focused planning governance | 74 passed |
| Full legacy suite | 232 passed |
| Planning verifier | exit 0; status SHA-256 `d8a7cba79cd429ec3e2fbc1b7b3c579e37641979a75006b93defcae69d1f2470`; 13 missing; current task `LAR-P0A-003` |
| Read-only selector | exit 0; `close_baseline_normative_package_first / LAR-P0A-003`; no governance issues or side effects |
| Governance preflight | exit 0; build/hotspot N/A as declared; test, contract, selector, script parse and diff gates pass |
| JSON parse | planning status, work items, manifest fixture and retained schema parse |
| Secret scan | no password, token, API key, secret or private-key assignment pattern in diff |
| `git diff --check` | exit 0 |

Five-axis review covered correctness, readability/simplicity, architecture, security and performance. It found one required test-coverage gap: the first regression only proved the positive self-test output. The final change adds direct rejection evidence for a v3.22 identity rollback and on-disk artifact byte drift. No unresolved Critical or Required finding remains in this bounded slice; no dependency, network, runtime hot path, `.ai` state or external effect was added.
