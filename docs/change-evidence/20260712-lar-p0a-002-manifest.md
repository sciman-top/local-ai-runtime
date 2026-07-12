# LAR-P0A-002 BaselineManifest Contract Evidence

## 1. Identity and boundary

- Baseline: `local-ai-runtime-0.2-v3.22`
- Task: `LAR-P0A-002`
- Queue: `LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE`
- Result scope: manifest schema, non-final fixtures, byte validator and fail-closed standalone verifier skeleton
- Successor: `LAR-P0A-003 / close_baseline_normative_package_first`

This slice does not create `BaselineManifest.v1.json`, an approval record, Truth Reset, `runtime/local-ai-runtime`, Q0, a Batch claim, a writer, a commit or live evidence. `P0A-MANIFEST` remains missing and `P0A-VERIFIER` remains approval-blocking as `in_progress`. The package therefore remains 15 required / 2 present / 13 missing and the decision remains Request changes.

## 2. Files and immutable inputs

Created contract files:

| File | Bytes | SHA-256 |
|---|---:|---|
| `docs/specs/local-ai-runtime-0.2/normative/BaselineManifest.v1.schema.json` | 3475 | `d8bb03fc470c334ce9c8bfd5176a359bfaa7a44d59e0a60ac58de04febbc3709` |
| `docs/specs/local-ai-runtime-0.2/fixtures/baseline-bytes/manifest.json` | 3895 | `2e0012a79030364cc8c932e993285fbd0e3ad96ecbfbcd2c2dbf9a6355d95b3e` |
| `scripts/verify-local-ai-runtime-baseline.py` | 17556 | `5269d97ae81e981088f703b109969e6f0b405217a1ed6076d2da9b12a04617f9` |

Python `hashlib` and PowerShell `Get-FileHash` independently reproduced each hash. These identities describe this task result; the verifier skeleton remains mutable until `LAR-P0A-012` freezes `P0A-VERIFIER`.

Frozen inputs were read back unchanged:

| Input | Bytes | SHA-256 |
|---|---:|---|
| v3.22 narrative | 178330 | `8338a9dcf4bbbb40ca28f4f2ec6dca37587ee94fbfbbc6e3a0063c4de379569c` |
| `BaselineLineage.v1.json` | 3134 | `8bb29e0fbc4990749424e07368e5b1c0f09cf378e78d1ada38b8fe998fb97b35` |

## 3. Contract decisions

- The manifest is a domain-separated envelope with domain `local-ai-runtime/BaselineManifest/v1` and schema version 1.
- Every artifact entry binds artifact ID, artifact version, role, repo-relative path, byte count, lowercase SHA-256, schema version and verifier ID.
- Artifact IDs and paths are independently unique.
- Arrays preserve manifest order. This task does not introduce canonical set sorting; `LAR-P0A-003` owns canonicalization semantics.
- `package_review_head` binds `ReviewEvidenceIndex.v1`, a positive sequence, an entry hash and `frozen=true`.
- The payload has `additionalProperties=false` and contains no manifest self-hash field. The closed file hash is computed externally after creation.
- The manifest artifact, review index and approval record are forbidden artifact entries. The manifest binds only the earlier frozen `package_review_head`; the later closure review cannot self-reference.
- The validator rejects rather than rewrites source bytes. It has no network, locale or auto-fix path.
- Default package verification returns `incomplete / standalone_verifier_not_frozen` with exit 3 until later P0A tasks implement and freeze the complete verifier.

## 4. Acceptance mapping

| Acceptance | Mechanical evidence |
|---|---|
| Reject BOM, CR, non-NFC, trailing SP/HTAB, controls and bad terminal LF | Eight byte-negative fixtures execute through `validate_normative_bytes`; manifest self-test reports `byte_negative_fixture_count=8`. |
| Reject duplicate artifact IDs and paths | `duplicate_artifact_id` and `duplicate_artifact_path` structural fixtures must return their exact stable reasons. |
| Require complete entry identity | Schema `artifact_entry.required` and runtime `_require_exact_fields` both require all eight identity fields. |
| Exclude manifest self-hash | Closed payload schema plus `self_hash_field` negative fixture reject `manifest_sha256`. |
| Freeze review head and prevent cycles | Schema fixes `frozen=true`; manifest/review/approval self-reference and unfrozen-head fixtures are rejected. |
| No final manifest; P0A-MANIFEST missing | Self-test checks file absence; inventory keeps `P0A-MANIFEST=missing`. |
| Skeleton validates fixtures but is not final verifier | Component self-test returns pass; default package mode returns exit 3; inventory uses `P0A-VERIFIER=in_progress`, not present. |

## 5. Verification

The final verified command set and exact results are recorded after the complete repository gate in section 8.

Initial focused evidence:

| Command | Result |
|---|---|
| `python scripts/verify-local-ai-runtime-baseline.py --component manifest --self-test` | exit 0; 1 positive, 7 structural-negative and 8 byte-negative fixtures; final manifest absent |
| `python scripts/verify-local-ai-runtime-baseline.py --json` | exit 3; `status=incomplete`, `reason=standalone_verifier_not_frozen` |
| `uv run --project ./runtime/host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_planning_governance.py -q` | 55 passed before final planning projection |
| `git diff --check` | exit 0 before final projection |

## 6. N/A and unchanged surfaces

- Build: `gate_na`; reason=`P0A-002 is a preapproval contract slice and runtime/local-ai-runtime does not exist`; alternative=`legacy full pytest plus schema/verifier self-test`; evidence=`this record`; expires_at=`LAR-P0D-001`.
- Runtime hotspot: `gate_na`; reason=`no runtime execution path changed`; alternative=`planning governance tests, verifier, selector, preflight and diff review`; evidence=`this record`; expires_at=`first executable slice after LAR-P0D-001`.
- `.ai/config`, `.ai/state/control-plane.db`, legacy runtime behavior, host-local Codex processes, auth/provider state and live repositories were not changed.

## 7. Rollback

Revert only the atomic `LAR-P0A-002` commit. That removes the manifest schema/fixtures/skeleton, regression and planning-verifier support, restores `P0A-VERIFIER=missing`, returns task 002 to ready/task 003 to pending and restores prior current-task documentation. Frozen v3.22/lineage/history bytes, legacy runtime, `.ai/config` and live state remain untouched.

## 8. Final gate evidence

| Gate | Result |
|---|---|
| Manifest component self-test | exit 0; 1 positive, 7 structural-negative and 8 byte-negative fixtures; final manifest absent |
| Full-package fail-closed probe | exit 3; `status=incomplete`, `reason=standalone_verifier_not_frozen` |
| Focused planning governance | 55 passed |
| Full legacy suite | 213 passed |
| Ruff | `All checks passed!` |
| Planning verifier | exit 0; status SHA-256 `051113db3c52421caba856d672389e0670ee3ab9b7664dddc610a3cc93f5cdbc`; 13 missing; current task `LAR-P0A-003` |
| Read-only selector | exit 0; `close_baseline_normative_package_first / LAR-P0A-003`; no governance issues or side effects |
| Governance preflight | exit 0; build/hotspot N/A as declared; test, contract, selector, script parse and diff gates pass |
| JSON parse | six changed control/contract JSON files parse |
| Secret scan | no password, token, API key, secret or private-key assignment pattern in diff |
| `git diff --check` | exit 0 |

Five-axis review found and fixed two forward-state defects before closeout: the planning verifier now allows `P0A-VERIFIER` to become present only after `LAR-P0A-012`, and it stops enforcing final-manifest absence once `LAR-P0A-013` legitimately begins. Runtime path validation now independently enforces the schema's identifier and repo-relative-path constraints. No unresolved Critical or Required finding remains in this bounded slice.
