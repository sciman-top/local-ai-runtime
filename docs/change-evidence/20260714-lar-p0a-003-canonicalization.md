# LAR-P0A-003 Canonicalization and Windows Path Identity Evidence

## 1. Identity and boundary

- Baseline: `local-ai-runtime-0.2-v3.23` (`baseline_candidate`)
- Task: `LAR-P0A-003`
- Artifact: `P0A-CANONICAL / CanonicalizationPolicy.v1`
- Artifact identity: `4264` bytes / `9cbc7295fb1cefdb651985cc81181ffa3a81db33ccf229535bf2e65438b71a7f`
- Successor: `LAR-P0A-004 / close_baseline_normative_package_first`

| File | Bytes | SHA-256 |
|---|---:|---|
| `CanonicalizationPolicy.v1.json` | 4264 | `9cbc7295fb1cefdb651985cc81181ffa3a81db33ccf229535bf2e65438b71a7f` |
| `CanonicalEnvelope.v1.schema.json` | 1363 | `0c77c1d310a4a92a46428a93bd8a666cc621d5aa202a760f38a90dea956e5374` |
| canonicalization `manifest.json` | 14873 | `bce05e5f6978b7a5da419fc1897a0637f766188fe65fdf47705b0ec98214b8e1` |
| `verify-local-ai-runtime-baseline.py` | 65117 | `ce0962fde76aeea459bf9db1aedb0f8df109b088eb035900b86480ee2af9367e` |
| `test_baseline_canonicalization.py` | 9772 | `f723cd54d753dc90dcead4b5d81f8f8ed64b2f88dc29c4f61c8c2336cbde8f76` |

This slice creates one normative canonicalization/path artifact plus its schema, fixtures and
component verifier. It does not create `BaselineManifest.v1.json`, approval, Truth Reset,
`runtime/local-ai-runtime`, Git execution, a Windows Job, live Batch evidence or remote effects.
The package remains incomplete and the frozen v3.23 narrative bytes are unchanged.

## 2. Contract closure

`CanonicalizationPolicy.v1` is itself canonical UTF-8 JSON with one terminal LF. It fixes:

- duplicate-key, float, null, non-NFC and disallowed Unicode rejection;
- UTF-8 byte-lexicographic object keys, preserved arrays and declared-set-only sorting;
- duplicate set-key rejection instead of deduplication;
- a domain-separated v1 envelope and lowercase SHA-256 identity;
- raw Git spelling preservation with independent Windows collision keys;
- invalid UTF-8, non-NFC, absolute/traversal, ADS, DOS device, control/format,
  trailing-dot/space and case-collision rejection;
- no-follow handle, volume, `FILE_ID_128`, root ancestry, owner/DACL and link policy as the
  authorization basis; string equality never grants authority;
- `policy_query_denied` plus mandatory non-elevated alias/identity probes, without requiring a
  global 8.3 disable policy;
- canonical `ConvertSidToStringSidW` input, full ASCII SID hash and six closed named-object
  templates.

## 3. Locale-independent collision catalog

The Windows collision-key algorithm is pinned to invariant Unicode 15.1.0 default uppercase
data. Official source identities checked on 2026-07-14:

| Source | Bytes | SHA-256 |
|---|---:|---|
| `https://www.unicode.org/Public/15.1.0/ucd/UnicodeData.txt` | 1914200 | `2fc713e6a31a87c4850a37fe2caffa4218180fadb5de86b43a143ddb4581fb86` |
| `https://www.unicode.org/Public/15.1.0/ucd/SpecialCasing.txt` | 16832 | `55a477efd933a52cd27e6a9bf70265bb2d8814af31aab07767abc8eb421f27ef` |

The Git path remains the original authorized value. The derived collision key is only a closed
set collision guard and never becomes a path or handle authority.

## 4. Fixture matrix

| Fixture class | Count | Coverage |
|---|---:|---|
| Canonical positive | 1 | object ordering, preserved `[2,1]`, declared set sorting |
| Canonical negative | 13 | duplicate key, float, null, NFC/category/zero-width/BOM/noncharacter and set failures |
| Git positive | 2 | exact ASCII and Unicode NFC spelling preservation |
| Git negative | 15 | invalid bytes, path grammar, ADS/device/control/trailing/collision |
| Alias/identity probes | 8 | explicit handle identities, denied policy, collision, link, bypass, drift |
| Boundary dimensions | 13 | declarative `limit-1 / limit / limit+1` matrix for every bound |
| Named-object templates | 6 | SID hash and closed ASCII name construction |

The schema adds explicit `x-local-ai-runtime-maxUtf8Bytes` and
`x-local-ai-runtime-maxDepth` keywords where standard JSON Schema length semantics cannot
express the byte/depth contract.

## 5. Red/green evidence

- Red: focused component test returned exit 1 because the verifier returned
  `standalone_verifier_not_frozen` with component exit 3.
- Robustness red: malformed nested policy/schema/fixture values leaked `AttributeError`,
  `TypeError` or `UnicodeEncodeError`; type-correct policy/schema semantic drift could pass; a
  malformed Git negative fixture leaked `TypeError`.
- Green: the component verifier now returns exit 0 with the exact artifact identity and closed
  fixture counts above. Four focused tests cover component closure, malformed-input fail-closed
  behavior, type-sensitive semantic drift and component-entry fixture validation.

## 6. Verification

- `python scripts/verify-local-ai-runtime-baseline.py --component canonicalization`: pass;
  exact policy identity and `1 / 13 / 2 / 15 / 8 / 13 / 6` fixture counts returned.
- `uv run --project ./runtime/host-orchestrator python -m pytest`: `239 passed in 54.09s`
  in release-style preflight.
- `python scripts/verify-planning-status.py`: pass; status SHA-256
  `278e4632cd6a167a3f32386a09e854fe1db523b0cebe6fd3135b4c97ed801d04`,
  current work item `LAR-P0A-004`, missing artifact count `12`.
- `python scripts/select-next-work.py`: pass; unique result
  `close_baseline_normative_package_first / LAR-P0A-004`, zero side effects.
- `python scripts/verify-local-ai-runtime-baseline.py --json`: expected exit `3`,
  `status=incomplete`, `reason=standalone_verifier_not_frozen`; implemented components are only
  `manifest_self_test` and `canonicalization`.
- JSON parsing, Python compilation and `git diff --check`: pass.
- `pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1
  -DisableAutoCommit`: pass; `build` and `hotspot` are the declared `gate_na`, while test,
  contract/invariant, planning selection, script parsing and `git diff --check` pass.
- Staged secret-value scan result: `NO_STAGED_SECRET_VALUE_PATTERNS`.

## 7. N/A and remaining truth

- Build: `gate_na`; `reason=preapproval contract slice and runtime/local-ai-runtime does not
  exist`; `alternative_verification=component verifier + host-orchestrator full pytest`;
  `evidence_link=this record`; `expires_at=LAR-P0D-001`.
- Hotspot: `gate_na`; `reason=no executable runtime hot path changed`;
  `alternative_verification=component/planning verifiers, selector, tests and diff review`;
  `evidence_link=this record`; `expires_at=first executable slice after LAR-P0D-001`.
- Normative package after routing: `15 required / 3 present / 12 missing`.
- `P0A-VERIFIER` remains `in_progress`; `P0A-MANIFEST` and `P0A-REVIEW` remain missing.
- Baseline Approval remains inactive and no model/profile/runtime authority changed.

## 8. Rollback

Revert only this slice: remove the canonical policy/schema/fixture and component verifier,
restore `P0A-CANONICAL` to missing, return `LAR-P0A-003` to ready and `LAR-P0A-004` to pending,
and restore current-task projections. Do not alter frozen v3.23/lineage bytes, earlier evidence,
`.ai/config`, live state or legacy runtime behavior.
