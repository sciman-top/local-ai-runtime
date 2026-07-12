# Local AI Runtime historical source archive evidence

## Scope

This evidence closes only `LAR-P0A-001`: recovery and independent verification
of the exact v3.17 and both conflicted v3.18 message/content bodies. It does not
create `BaselineLineage.v1`, approve v3.21, create v3.22, perform Truth Reset or
change runtime behavior.

## Source boundary

- Session ID: `019f5081-9022-7681-9378-fa14e695131b`.
- Session basename: `rollout-2026-07-11T17-28-21-019f5081-9022-7681-9378-fa14e695131b.jsonl`.
- The original session was opened read-only. No session bytes were changed or
  copied wholesale into the repository.
- v3.17 came from response-item line 7409, assistant `output_text`, excluding
  exactly `<proposed_plan>\n` and `</proposed_plan>`.
- v3.18-A came from response-item line 8408 with the same exact envelope
  exclusion.
- v3.18-B came from response-item line 8429, user `input_text`, starting at the
  unique complete v3.18 title and continuing through the message-terminal LF.

## Exact identities

| Archive | Bytes | SHA-256 |
|---|---:|---|
| v3.17 | 32,825 | `a285f5f421a8ccd4debd8794609a2aa0eb07bb1bf651c2467a95f7cad25a5f81` |
| v3.18-A | 66,328 | `6924ba562dda8e69274eb80fef9e3a9699eb493570ee08330fcad5ec4bc3baa5` |
| v3.18-B | 43,908 | `8da5aa20fb44d95503e443822163397a2aa1df590e1916d1a5a10a6c24ea06b7` |

Every body is UTF-8 without BOM, LF-only, Unicode NFC, has exactly one terminal
LF, has no CR/NUL/disallowed control/noncharacter, and has no trailing SP/HTAB.

## Commands and outcomes

- `python scripts/extract-local-ai-runtime-history.py --session-path <exact-session>`:
  exit 0; all three expected identities matched before no-replace publication.
- `python hashlib.sha256`: independently recomputed the three identities above.
- PowerShell `Get-FileHash -Algorithm SHA256`: independently recomputed the same
  three identities.
- `uv run --project ./runtime/host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_planning_governance.py -q`:
  boundary/no-replace/tamper regressions passed.

## Boundary and next action

`P0A-LINEAGE` intentionally remains missing because the v3.22 candidate identity
does not yet exist. The only legal successor is `LAR-P0A-REBASELINE-V322 /
draft_v3_22_candidate_first`. Rollback removes only these archive files, their
source record and this evidence; it never edits the original session or any
frozen candidate.
