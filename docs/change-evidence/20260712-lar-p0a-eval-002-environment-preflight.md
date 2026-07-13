# LAR-P0A-EVAL-002 Environment Preflight

## Result

`LAR-P0A-EVAL-002` remains `execution_pending`. This preflight did not execute
any declared comparative task, create a terminal evaluation decision, qualify a
Codex capability surface, change v3.23 semantics, create a Batch task, or
change provider/auth, a pre-existing host Codex process, remote state, or the
primary worktree.

The exact `gpt-5.6-sol/high` CLI probe could not start because the installed
Codex CLI (`0.144.1`) rejects the configured provider before agent execution:

```text
Error: Model provider `codex_local_access` not found
```

This is an environment qualification failure, not a model-quality result. It
does not establish a comparison winner, a capability replacement claim, or a
v3.23 semantic-change decision. The selector therefore remains on
`run_native_thin_path_evaluation_first`.

One additional non-contract environment drift was observed and recorded: the
SDK initialize-only probe invoked `uv run` in a fresh detached worktree. `uv`
created a temporary virtual environment and downloaded `pydantic-core` before
the SDK client initialized. The initialization then started and closed a new
local App Server child process. That was not a model turn or repository
mutation, but it means this preflight cannot claim to have enforced the sealed
`network_access=disabled` environment. The generated virtual environment was
removed with the disposable worktree; the package-cache/network effect is not
treated as evaluation evidence or a passing sandbox observation. SDK
initialization persistence outside the disposable worktree was not qualified,
so it is likewise not used as a recovery or effect-boundary claim.

## Sealed Context

The preflight binds the unchanged v3.23 evaluation contract identity:

- snapshot commit: `6fd6cd54037f17e44192bc272306b137def7f8a4`
- snapshot tree: `11c8ab770769b3aeff5c111063a316e712fa7241`
- contract set: `local-ai-runtime-0.2-v3.23-native-thin-path-evaluation-v1`
- detailed environment record: [native-thin-path-environment-preflight-20260712T142336Z.json](../evaluations/local-ai-runtime-0.2/native-thin-path-environment-preflight-20260712T142336Z.json)

The three sealed contract bytes and hashes remained identical to the
`LAR-P0A-EVAL-001` record. The target model/effort was explicitly supplied to
the failed probe, so the existing user configuration's `medium` default was not
silently used as a substitute.

## Observations

| Surface | Preflight result | Evidence boundary |
| --- | --- | --- |
| CLI execution | `unqualified` | Fixed `gpt-5.6-sol/high`, workspace-write, deny-all probe failed before an agent turn because `codex_local_access` is unknown. |
| App Server protocol | `inconclusive` | Experimental schema generation succeeded, but no target-model job lifecycle, sandbox effect, or recovery was run. |
| SDK execution | `inconclusive` | `openai-codex 0.1.0b2` initialized a local protocol client, but it bundles CLI `0.132.0`; no turn or target-model behavior was exercised. |
| Managed worktree | `inconclusive` | A disposable Git detached worktree isolated the probe; that does not qualify Codex-managed worktree lifecycle behavior. |
| Automations | `inconclusive` | CLI `app` help was discoverable, but no distinct CLI scheduler lifecycle was available and no scheduled task was created. |

`Superpowers` and `Trellis` were not run because their sealed local identities
were not established and the core fixed-model CLI prerequisite failed. Hermes
is `not_applicable` to this local corpus: no declared task family requires
remote, VPS, cron, or message-gateway behavior.

## Isolation And Cleanup

The only probe workspace was a newly created detached Git worktree at the
sealed snapshot. It was never the primary worktree. App Server schema output and
the temporary Python virtual environment were removed after the probes; a clean
tracked diff was confirmed before `git worktree remove --force` removed the
worktree. No pre-existing Codex process was changed. The `uv`
package-resolution network effect was known and bounded, while SDK persistence
outside the worktree was not qualified; neither is silently treated as a
network-disabled or recovery-passing observation. This blocks formal trial
execution rather than being silently ignored.

## Required Recovery Path

Do not repair this provider/auth/configuration condition inside the comparative
evaluation or by restarting Codex. A separately authorized host-local repair
must first establish a valid provider configuration. Because provider, tool
inventory, sandbox, SDK/App Server behavior, and model/effort are generation
inputs, the repair then requires a fresh capability generation/Q0 path before
the sealed EVAL-002 corpus can start. The comparison may only resume from newly
created disposable worktrees and must preserve every sealed task, repeat,
counterbalance, gate, denominator, and evidence rule.

## Verification

The planning control plane was rechecked immediately before this preflight:

- `pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit`: pass; `229 passed`, verifier, selector, script parsing, and diff hygiene passed.
- Fixed CLI probe: exit `1`, provider error above; no agent execution.
- App Server schema generation: exit `0`; output was confined to and removed from the disposable worktree.
- SDK initialize-only probe: exit `0`; no thread or turn was started. The
  fresh-worktree `uv run` dependency resolution downloaded `pydantic-core`, so
  this probe is explicitly non-contract for the network-disabled criterion.
- Worktree cleanup: clean tracked diff before removal; `git worktree list` afterwards showed only the primary worktree.

## Rollback

This evidence is additive and non-terminal. Reverting it only removes the
preflight record and index entry; it must not modify `planning-status.json`, the
sealed contracts, frozen v3.23 candidate/lineage, `.ai` control-plane state,
provider/auth configuration, or host Codex processes.
