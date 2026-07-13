# LAR-P0A-EVAL-001 Native Thin-Path Evaluation Contract

## Result

`LAR-P0A-EVAL-001` froze the preapproval Native thin-path / capability
comparative evaluation contract for `local-ai-runtime-0.2-v3.23`. The contract
does not grant Baseline Approval, change the frozen v3.23 narrative, create a
runtime package, execute a comparative trial, qualify a Codex capability
surface, create a Batch task, change provider/auth, contact a remote, or create
live acceptance evidence.

The only next selectable work item is `LAR-P0A-EVAL-002`, with selector action
`run_native_thin_path_evaluation_first` and status `execution_pending`.

## Sealed Identity

The comparison source snapshot is the committed repository state:

- commit: `6fd6cd54037f17e44192bc272306b137def7f8a4`
- tree: `11c8ab770769b3aeff5c111063a316e712fa7241`
- contract set: `local-ai-runtime-0.2-v3.23-native-thin-path-evaluation-v1`
- contract task: `LAR-P0A-EVAL-001`
- execution task: `LAR-P0A-EVAL-002`

| Contract | Bytes | SHA-256 |
| --- | ---: | --- |
| `native-thin-path-capability-evaluation.v1.json` | 13775 | `e4129a743a976e2e286c43e6ebcb9c3a1d634079d3188e18292a147c06499b39` |
| `native-thin-path-task-family-manifest.v1.json` | 8996 | `27965825d8ba79ae008d876992ea70a380b213578fc8ed14fc3af8a0016bc6b0` |
| `native-thin-path-evidence-schema.v1.json` | 6827 | `a82b869eae6b64aed51e847cb5835a69e98e91095fdf832fb5391beaea501721` |

`planning-status.json` carries this exact identity. The verifier rejects a
missing contract, non-object JSON, duplicate key, changed bytes/hash, changed
snapshot, changed cross-reference, incomplete surface/metric/hard-floor set, or
terminal result/decision/evidence artifact that binds a different identity.

## Contract Scope

The contract fixes three task families and their inputs, success oracles,
repeat counts, eligible variants, counterbalancing, denominator treatment, and
rollback expectations. Historical `wave1-smokes` fixtures provide task-shape
context only; their fake-first outputs and Hermes-era metadata are not
comparative results or live acceptance evidence.

The core variants are `thin_codex_native` and `native_plus_key_gates`.
`superpowers_when_applicable` and `trellis_when_applicable` are conditional
local workflow comparisons, not repository control planes. `hermes_when_applicable`
is eligible only for an explicitly comparable remote/VPS/cron/message-gateway
task family. A local corpus without such a task records `not_applicable`; it
does not establish that Hermes was replaced.

All write trials in `EVAL-002` must start from a newly created disposable
detached worktree at the sealed commit/tree. The primary worktree cannot be a
trial workspace. The fixed initial model configuration is `gpt-5.6-sol/high`;
this is an experiment configuration, not a claim that high effort is globally
optimal. Any model, effort, tool inventory, sandbox, SDK/App Server behavior,
managed worktree behavior, automation behavior, or external-effect change
requires a new capability generation and its declared Q0 path.

## Findings Projected

The contracts make the following review conclusions enforceable inputs to the
next evaluation rather than unsupported product claims:

1. v3.23 control-plane direction is retained, but native platform-surface
   detail must be assessed before Baseline Approval. CLI, App Server, SDK,
   managed Worktree, and Automations are independent surfaces with no
   qualification inheritance.
2. The product promise remains low-human, predictable, recoverable development
   throughput. Native targets interaction latency; the Epoch 1 Batch global
   `capacity=1` boundary targets reliability, recovery, and auditability rather
   than concurrent high throughput.
3. The legacy/experimental `adaptive-orchestration.md` route remains
   non-authoritative and cannot select work or establish v3.23 semantics.
4. `commit-ready` is insufficient for long-term quality. EVAL evidence and P4
   promotion retain sampled `DownstreamOutcomeRecord` observations, including
   `censored` and `unknown`, in the declared denominator. The runtime does not
   push, read remote CI, or decide merge/reject; an operator may later attach
   secret-safe external evidence locators.

The hard floor is non-negotiable: a quality, security, or evidence regression
invalidates efficiency gain. An unknown/unowned external effect or an
unreproducible required recovery/rollback stops the evaluation. The only future
decision values are `preserve_v3_23_semantics`,
`narrow_profile_or_adapter_candidate`, and `supersede_required`; the latter two
freeze v3.23 and require a v3.24 successor rather than an in-place edit.

## Official Basis

The evaluation contract cites official guidance as evaluation basis, not as a
qualification result: [Using GPT-5.6](https://developers.openai.com/api/docs/guides/latest-model.md),
[Codex App Server](https://learn.chatgpt.com/docs/app-server),
[Git worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees), and
[Automations](https://learn.chatgpt.com/docs/automations). Local qualification
still requires the frozen task corpus, environment capture, effect/recovery
evidence, and `EVAL-002` result decision.

## Verification Record

The final command results for this contract slice are appended only after they
run against the final bytes:

| Gate | Result |
| --- | --- |
| Build | `gate_na`: no `runtime/local-ai-runtime` package exists; host-orchestrator test suite is the alternative verification. |
| Test | `uv run --project ./runtime/host-orchestrator python -m pytest`: `229 passed in 46.97s`. |
| Contract/invariant | `python scripts/verify-planning-status.py`: exit 0; v3.23 remains approval-inactive with 13 missing artifacts and `LAR-P0A-EVAL-002 / execution_pending`. `python scripts/select-next-work.py`: exit 0; `run_native_thin_path_evaluation_first`, no side effects. |
| Hotspot | `pwsh -NoProfile -NonInteractive -File scripts/governance/preflight.ps1 -DisableAutoCommit`: exit 0; `229 passed`, verifier/selector, Python/PowerShell parsing, and `git diff --check` passed. Hotspot remains `gate_na` because no executable runtime hot path changed. |

## Rollback

Revert only the EVAL-001 contract files, planning-status/work-item state,
verifier/test changes, documentation projections, and this evidence record. Do
not alter frozen v3.17-v3.23 narrative or lineage bytes, `.ai/config`,
`.ai/state/control-plane.db`, `runtime/host-orchestrator`, provider/auth, host
Codex processes, or any historical evidence.
