# 2026-07-14 Planning Optimization Rebaseline

## Scope and truth boundary

- Baseline: `local-ai-runtime-0.2-v3.23` (`baseline_candidate`)
- Current runtime truth: `runtime/host-orchestrator` and `.ai/state/control-plane.db`
- Current selector result: `close_baseline_normative_package_first / LAR-P0A-003`
- Change class: pre-approval planning control-plane alignment
- Frozen v3.23 semantic change: `false`
- Active model/profile promotion: `none`

This slice corrects implementation-planning semantics only. It does not create or modify
`runtime/local-ai-runtime`, `.ai/config`, live state, provider/auth, a Baseline Approval,
Truth Reset, Implementation Acceptance, Full Q0, a Batch claim, a remote effect or a new
runtime authority. The frozen v3.23 candidate bytes and lineage remain unchanged.

## Problems closed by contract

1. A work item remains the atomic acceptance/evidence/commit/rollback unit, but it is no
   longer equated with an AI session. After verified closeout, one run may reselect and
   continue sequentially within a default budget of 3 completed items or 180 minutes.
2. Continuation stops on the first failed closeout, budget exhaustion, a non-unique or red
   selector, missing dependency/authorization, phase or approval transition, successor
   baseline need, or live/auth/provider/remote/destructive/external-write scope.
3. Planning complexity now has machine-enforced caps. No new authoritative document, work
   item, contract projection or normative artifact can be added without replacement or a
   successor baseline.
4. Planning model routing is role/risk/task-family/surface/generation keyed and candidate-only.
   It cannot activate a model/effort/provider route without paired evaluation and generation
   qualification, and it has no silent or dynamic fallback.
5. Autonomy, speed, efficiency and optimality now have separate measurable meanings. Missing
   or unavailable data remains unknown; optimality is limited to a declared cohort/profile.
6. `LAR-P0A-004` explicitly keeps `WorkRoutingPolicy` work-class routing separate from
   qualified `ExecutionProfile` model/effort selection and forbids a second planner/router.

## Official basis checked on 2026-07-14

| Source | Relevant current guidance | Planning consequence |
|---|---|---|
| [OpenAI GPT-5.6 guide](https://developers.openai.com/api/docs/guides/latest-model.md) | Sol is the flagship candidate; Terra targets lower latency/cost; Luna targets efficient high-volume work. Model/effort changes must be tested on representative workloads. Lean prompts, explicit autonomy boundaries and measured success/completeness/tokens/latency/cost remain required. | Record role candidates, not active routes. Require paired evaluation, hard quality floors and bounded autonomy. |
| [OpenAI building agents](https://developers.openai.com/tracks/building-agents#how-to-choose) | Start with a flagship model, test Terra/Luna for simpler or latency-sensitive work, and do not merely swap model names without evaluation. | Use qualification-driven role routing and no global best-model claim. |
| [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) | Parallel agents can reduce wall time for independent work but consume more tokens; read-heavy exploration is a safer starting point than parallel write-heavy work. | Keep sequential atomic closeout and global single-writer authority; parallelism is not the definition of speed. |
| [Codex best practices](https://learn.chatgpt.com/guides/best-practices) | Keep `AGENTS.md` short and practical, use reusable guidance only for repeated needs, and test/review changes. | Cap instruction/planning surfaces and prefer existing machine contracts over another harness. |
| [Codex long-running work](https://learn.chatgpt.com/docs/long-running-work) | Related multi-step work can stay in one task with explicit outcome, constraints and verification; new authority is not implied. | Allow same-run continuation while preserving stop and approval boundaries. |

The official sources support thinner prompting and native long-running/subagent/model-selection
capabilities. They do not prove that third-party harnesses are universally obsolete, that the
highest effort is optimal, or that a single-writer Batch is a high-concurrency system.

## Machine policy and projections

- `docs/plans/local-ai-runtime-0.2-work-items.json` adds exactly one top-level
  `planning_optimization_policy` with execution, complexity, model-routing and outcome-metric
  sections. The work-item count remains 65 and the contract-projection count remains 11.
- `scripts/verify-planning-status.py` validates the canonical policy contract, measures actual
  repository complexity against its caps, and validates the planning-status projection.
- `docs/architecture/planning-status.json` records `status=active`,
  `complexity_health=warning_all_dimensions`, `frozen_v323_semantics_changed=false` and
  `active_profile_change=none`.
- Existing README/PRD/architecture/roadmap/plan/backlog/acceptance/AGENTS surfaces project the
  same semantics. No new authoritative planning document or task directory was added.

## Complexity measurements

| Dimension | Before | After policy implementation | Hard cap | Health |
|---|---:|---:|---:|---|
| Authoritative docs | 14 | 14 | 14 | at cap |
| Machine work items | 65 | 65 | 65 | at cap |
| Contract projections | 11 | 11 | 11 | at cap |
| Normative artifacts | 15 | 15 | 15 | at cap |
| Root `AGENTS.md` bytes | 6238 | 6565 | 8192 | warning |
| Machine-plan bytes | 215502 | 220527 | 230000 | warning |
| Planning-verifier lines | 3951 | 4090 | 4200 | warning |
| Planning-governance-test lines | 2375 | 2577 | 2600 | warning |

The current control plane has not become lightweight. All dimensions are at or above the 80%
warning threshold, so the truthful health is `warning_all_dimensions`. This slice prevents
further unchecked growth; a later slice that grows these surfaces must first remove or merge
at least equivalent complexity.

## Red/green evidence

- Red: targeted tests initially returned `2 failed, 74 deselected`; both failed because
  `planning_optimization_policy` did not exist.
- Green: the final targeted policy/status/doc projection run returned
  `3 passed, 74 deselected`.
- A first verifier implementation reached 4222 lines and failed its new 4200-line hard cap.
  Root-cause review found duplicated per-field verifier branches; it was replaced with one
  canonical structured-policy check plus actual complexity measurement, reducing the verifier
  to 4063 lines without raising the cap.

## First complete verification pass

| Gate | Result |
|---|---|
| Build | `gate_na`; candidate-planning slice and target package does not exist. Alternative: full host-orchestrator pytest. Expires at `LAR-P0D-001`. |
| Test | exit 0; `235 passed in 55.04s` |
| Contract/invariant | exit 0; baseline remains candidate, 13 artifacts missing, current task `LAR-P0A-003` |
| Read-only selector | exit 0; `close_baseline_normative_package_first / LAR-P0A-003`; no side effects |
| Hotspot | `gate_na`; no runtime hot path changed. Alternative: planning tests/verifier/selector/diff. Expires at first executable slice after `LAR-P0D-001`. |
| Release-style preflight | exit 0; embedded test `235 passed in 53.63s`, contract/selector/scripts/diff all pass |

## Post-routing revalidation

After this file was added to the evidence index and selected as
`current_evidence_ref`, the full repository sequence was rerun:

- full pytest: exit 0, `235 passed in 57.41s`;
- planning verifier: exit 0, final routed status SHA-256
  `1dfd39549d412ea92cf0c573abe627a4c3cf20b85fc87ee0d7007a60c794e45a`;
- read-only selector: exit 0, no governance issues or side effects,
  `close_baseline_normative_package_first / LAR-P0A-003`;
- release-style preflight: exit 0, embedded test `235 passed in 58.81s`,
  contract/selector/script parsing/diff all pass.

## Post-review revalidation

The five-axis review fixed localized JSON indentation and verifier readability, then found and
closed one fail-closed boundary: a missing or non-integer complexity cap can no longer raise an
uncaught `KeyError`/`TypeError`; it now produces a verifier failure. The regression remains
within the declared caps and adds no new planning surface.

- targeted planning-optimization tests: exit 0, `3 passed, 74 deselected`;
- standalone full pytest: exit 0, `235 passed in 63.65s`;
- planning verifier: exit 0, status SHA-256
  `1dfd39549d412ea92cf0c573abe627a4c3cf20b85fc87ee0d7007a60c794e45a`;
- selector: exit 0, no governance issue or side effect,
  `close_baseline_normative_package_first / LAR-P0A-003`;
- release-style preflight: exit 0, embedded test `235 passed in 57.57s`,
  contract/selector/script parsing/diff all pass.

## Acceptance mapping

| Requirement | Evidence |
|---|---|
| Work item and session are decoupled without batch status closure | Atomic closeout + fresh selector + bounded continuation contract and tests |
| Minimum-operator has measurable meaning | kickoff, unattended closeout and operator-minute metrics in machine policy/PRD/acceptance |
| Speed is not conflated with writer concurrency | separate Native and Batch P50/P95; capacity=1 and no runtime change |
| Model routing is useful but fail-closed | role candidates, paired cohort qualification, no profile promotion or fallback |
| Planning control plane cannot silently grow | machine caps, current measurements, warning health and verifier failure proof |
| No unsupported optimality claim | generation stratification, unknown retention and declared-cohort-only scope |

## Remaining truth

- Existing evaluation results still do not prove that the project is efficient, fast or optimal.
  They remain `5/18` overall success, P95 `1446.966s`, cross-generation, all downstream
  outcomes unknown and provider cost unavailable.
- This slice makes the missing proof measurable and prevents invalid claims; it does not invent
  the missing cohort evidence.
- The normative package remains `15 required / 2 present / 13 missing`.
- The next selectable work item remains `LAR-P0A-003`; this slice does not complete it.

## Rollback

Revert only this slice: remove the planning optimization policy and its verifier/tests/status
projection, restore the prior AI-session wording in existing authoritative docs, restore
`LAR-P0A-004` planning wording and remove this evidence/index entry. Do not alter frozen v3.23
bytes, lineage, normative artifacts, `.ai/config`, live state or legacy runtime behavior.
