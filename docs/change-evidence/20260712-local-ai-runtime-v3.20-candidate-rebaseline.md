# Local AI Runtime v3.20 Candidate Rebaseline

## Goal

Preserve the exact v3.19 candidate as reviewable lineage evidence, create a new self-contained v3.20 candidate for normative changes, and keep the preapproval planning control plane truthful without approving or implementing the runtime.

## Candidate identity

- Specification ID: `local-ai-runtime-0.2-v3.20`
- Candidate path: `docs/specs/local-ai-runtime-0.2-v3.20-baseline-candidate.md`
- Byte count: `130890`
- SHA-256: `43CB98737DAA5D171A9CDA2DCA49C8F118FB8BE92745B4076948D9178E56A130`
- Status: `baseline_candidate`
- Blocking stage: `baseline_approval`

The retained v3.19 archive remains exactly 111,952 bytes with SHA-256 `275306D2E88BAAFA803170EE4EF99FB822C4E13769721B806805B834BB9D7670`. It is a `superseded_candidate`, not a source from which implementations may fill v3.20 gaps.

## Review findings absorbed

The v3.20 candidate closes the following specification-level gaps:

- separates immutable Codex config from managed `.sandbox` state and broker-only `.sandbox-secrets` through `CodexSandboxStateBinding.v1`;
- requires suspended atomic Job attachment, durable launch identity and execution barriers for every process-bearing StageJob;
- linearizes Authorization revoke and effect grants with immutable `AuthorizationExecutionGrant.v1` records;
- fixes submission admission order to bounded parse, closed schema/public-ID membership, secret scan, canonicalization, fingerprint and only then transaction;
- defines no-reflog Git publication, including per-worktree `logs/HEAD` handling and `--no-create-reflog` ref updates;
- fails closed on NTFS 8.3 state and long/short alias ambiguity;
- binds `claim_epoch_seconds` once at claim and includes it in attempt/Git manifests;
- adds hard write-budget enforcement and separates `disk_pressure/resource_exhausted` from `needs_environment`;
- expands the byte policy to reject unapproved Unicode control/format, bidi, zero-width, BOM and noncharacter code points;
- makes `batch retry` suggestions state-specific rather than always recommending resubmission;
- updates the candidate's repository facts to the current baseline-closure queue, passing planning verifier and baseline-closure selector.

## Planning state

- Queue: `LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE`
- Selector: `close_baseline_normative_package_first`
- Current work item: `LAR-P0A-001`
- Normative inventory: 15 required artifacts, 1 present, 14 missing
- Approval active: false
- Truth Reset performed: false
- New runtime package exists: false
- New Batch claims allowed: false

This evidence is repo-level governance evidence. It is not `ReviewEvidenceIndex.v1`, a BaselineApprovalRecord, Implementation Acceptance, Full Q0 evidence or live Batch evidence.

## Verification

Final command results are recorded after the repository gates complete in this same change.

## Rollback

Revert only the v3.20 candidate and its planning, inventory, selector/verifier test, documentation and evidence projection. Preserve the exact v3.19 archive, legacy runtime behavior, `.ai` state/config, historical evidence and unrelated user changes.
