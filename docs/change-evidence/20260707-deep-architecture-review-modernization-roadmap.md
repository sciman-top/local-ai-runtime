# 2026-07-07 Deep Architecture Review And Modernization Roadmap

## Scope

- This document captures an evidence-backed product and architecture review of `Local AI Runtime`.
- It turns the review conclusion into a bounded modernization roadmap and prioritized backlog.
- It is advisory and repo-owned, but it is **not** a replacement for:
  - `docs/architecture/planning-status.json`
  - `docs/roadmap/orchestrator-roadmap.md`
  - `docs/plans/orchestrator-implementation-plan.md`
  - `docs/backlog/orchestrator-task-list.md`
- Current active queue, selector result, and acceptance posture remain whatever the authoritative surfaces say after verification.

## Repo-Side Verdict

As of `2026-07-07`, the project is **strong on repo-side truth, evidence, fail-closed boundaries, and operator discipline**, but **not yet strong on real autonomous continuation, real multi-executor execution, or real high-concurrency throughput**.

What is already strong:

- authoritative repo truth and drift control
- canonical task/result contracts
- repo-side path/worktree/cleanup/receipt boundaries
- deterministic simulation and promotion evidence
- planner/review fail-closed behavior
- explicit `repo-side done` versus `still open` boundary language

What is still structurally weak for the intended end-state:

- `depends_on` currently becomes planner pause, not durable dependency scheduling
- `max_active_leases` is enforced through repo-side counting/handoff, not atomic admission control
- `build / lint / typecheck / hotspot` are not yet real default gates
- `remote_non_gui / vm_gui` remain promotion evidence, not true runner lanes
- planner/review receipts exist, but auto-continue and low-friction autonomous execution are still shallow
- runtime observability is receipt-heavy but trace-light
- product scope still overlaps with capabilities already native to Codex / Claude Code

## Current Truth Snapshot

The review was grounded first in current repo truth:

- `README.md`
- `docs/architecture/planning-status.json`
- `docs/product/orchestrator-prd.md`
- `docs/architecture/orchestrator-target-architecture.md`
- `docs/specs/acceptance-and-gates.md`
- `runtime/host-orchestrator/src/host_orchestrator/host_local.py`
- `runtime/host-orchestrator/src/host_orchestrator/worker_factory.py`
- `runtime/host-orchestrator/src/host_orchestrator/db.py`
- `runtime/host-orchestrator/src/host_orchestrator/verification.py`
- `.ai/config/workers.yaml`

Verification run used for this review:

- `python .\scripts\verify-planning-status.py` -> pass
- `python .\scripts\select-next-work.py` -> pass, `promote_phase1_execution`
- `uv run --project .\runtime\host-orchestrator python -m pytest` -> pass, `79 passed`
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit` -> pass, with `build=gate_na`, `hotspot=gate_na`

## External Basis

The recommendations below were cross-checked against current official or high-signal references:

- [OpenAI Agents SDK starting point](https://developers.openai.com/api/docs/guides/agents#choose-your-starting-point)
- [OpenAI SDKs and when to use the Agents SDK](https://developers.openai.com/api/docs/libraries#use-the-agents-sdk)
- [OpenAI GPT-5.5 reasoning-model guidance](https://developers.openai.com/api/docs/guides/latest-model#using-reasoning-models)
- [OpenAI Codex config reference](https://developers.openai.com/codex/config-reference#configtoml)
- [OpenAI Codex glossary](https://developers.openai.com/codex/glossary)
- [Claude Code settings](https://docs.anthropic.com/en/docs/claude-code/settings)
- [Claude Code sub-agents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)
- [Model Context Protocol lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle)
- [Model Context Protocol tasks utility](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/tasks)
- [Aider modes](https://aider.chat/docs/usage/modes.html)
- [Aider lint/test workflow](https://aider.chat/docs/usage/lint-test.html)
- [OpenHands sandboxes overview](https://docs.openhands.dev/openhands/usage/sandboxes/overview)

## Recommended Product End-State

The recommended end-state is **not** “generic everything-orchestrator”. It is:

`single-user, local-first, codex-first, evidence-heavy orchestration runtime`

with the following boundaries:

1. Trusted host runtime owns policy, routing, approvals, evidence, tracing, and rollback.
2. Execution surfaces are minimized and explicit:
   - `host_local` is the primary lane
   - risky code execution progressively moves toward sandbox-as-a-tool or isolated runner lanes
   - `remote_non_gui / vm_gui` stay demoted until they are real, not promotional
3. Native platform abilities should be reused rather than cloned:
   - worktrees
   - subagents
   - hooks
   - permissions
   - automations
   - MCP transport and tool ecosystem
4. Repo-specific value should stay concentrated in:
   - canonical task/result normalization
   - policy-aware routing
   - evidence and closeout semantics
   - truth-boundary verification
   - provider/lane compatibility policy

## Strategic Direction

### Recommended

- Keep `Codex-first` as the default daily execution path.
- Treat `Hermes` as historical baseline plus compatibility and governance context, not as a second daily runtime core.
- Keep `Claude Code + GLM-5.2` as bounded review sidecar until there is a stronger proof that it reduces real operator load.
- Reduce “receipt-first” expansion and shift effort toward “autonomous continuation with stronger gates”.

### Not Recommended

- expanding remote/vm topology before the local scheduler is truly autonomous
- presenting simulation/promotion evidence as if it were live throughput capability
- building a parallel internal session/worktree/control UX that duplicates Codex/Claude platform capabilities
- promoting high-concurrency claims while admission control and durable scheduling remain handoff-oriented

## Modernization Roadmap

### Wave 1: Close The Autonomy Gap

Goal:

- turn planner/review/depends_on from “better receipts” into “less human relay”

Must land:

- durable dependency scheduling instead of `depends_on -> waiting_handoff`
- operator-configurable auto-continue rules after planner/review outcomes
- explicit `input_required / paused / resumable` state handling aligned with durable task semantics
- lower-friction continuation path for low-risk tasks

Exit:

- a task with bounded dependencies can queue, wait, resume, and continue without manual state stitching

### Wave 2: Harden The Real Gates

Goal:

- make automation safe enough that higher autonomy is justified

Must land:

- promote `build`, `lint`, `typecheck`, and `hotspot` from `gate_na` where repo-owned entrypoints exist
- normalize gate execution so commands are repo-owned presets, not arbitrary per-task shell strings by default
- add differential fast gates versus full gates
- preserve current truth boundary around `gate_na` with expiry and recovery rules

Exit:

- the default autonomous path runs real gates strong enough to catch most regressions before closeout

### Wave 3: Make Scheduling Real

Goal:

- replace symbolic concurrency with correct concurrency control

Must land:

- atomic admission control for worker-profile concurrency
- execution-attempt rows that are separate from logical task identity
- explicit queue semantics for `queued / running / blocked / paused / retryable / completed`
- retry/backoff policy with reason taxonomy
- fair scheduling across task classes

Exit:

- `1-2` true writers and several read-heavy workers can run without false handoff churn or quota races

### Wave 4: Move Risky Execution Toward Isolated Compute

Goal:

- stop treating `host_local` as the permanent answer for all write execution

Must land:

- sandbox-as-a-tool design for higher-risk tasks
- scoped workspace mounts and reduced host exposure
- clearer separation of trusted harness versus execution environment
- consistent policy on secrets, network, and writable roots

Exit:

- high-risk execution is isolated by design, not only by repo policy and post-run receipts

### Wave 5: Make Observability First-Class

Goal:

- move from file receipts only to durable traceability plus evaluation

Must land:

- run/attempt/sidecar trace IDs
- OpenTelemetry-compatible or equivalent trace export
- planner/review/worker correlation view
- evaluation loops that promote recurring failures into regression suites

Exit:

- the runtime can answer not only “what file was written” but also “why the workflow paused, retried, or degraded”

### Wave 6: Decide Topology Honestly

Goal:

- either wire `remote_non_gui` for real or demote it from near-term product messaging

Must land:

- a concrete `remote_non_gui` runner design with lifecycle, auth, workspace model, and proof plan
- a yes/no product decision on whether `vm_gui` stays deferred until real GUI-only workload evidence appears

Exit:

- topology claims and actual execution topology are aligned

## Priority Backlog

### P0: Highest Return, Lowest Ambiguity

1. Replace lease-count handoff with atomic worker-profile admission control.
2. Turn `depends_on` into queueable dependency state, not immediate planner pause.
3. Add resumable auto-continue after planner/review outcomes where policy allows.
4. Promote real `build / lint / typecheck / hotspot` gates where repo-owned commands can be defined.
5. Split logical task identity from execution-attempt identity in the control-plane schema.
6. Add first-class trace IDs across worker, planner, review, and closeout artifacts.

### P1: Important Next-Stage Improvements

1. Replace free-form per-task verification shell strings with repo-owned verification profiles plus task-level overrides.
2. Add diff-aware review context so the review sidecar sees changed files, gate results, and bounded patch summaries together.
3. Introduce a host-managed sandbox execution lane for higher-risk write tasks.
4. Consolidate scheduler policy into one explicit state machine instead of scattered handoff logic.
5. Decide whether `remote_non_gui` is a real next milestone or should be demoted from near-term messaging.

### P2: Valuable, But Only After P0/P1

1. Re-evaluate `compatibility_projection_ref` / `lane` rename only after runner and review maturity increase.
2. Clarify memory/provider/session isolation semantics instead of relying on worktree language alone.
3. Integrate stronger eval loops and failure clustering for recurring orchestration mistakes.
4. Explore app-server or MCP task-surface alignment after the local scheduler becomes durable.

## Explicit De-Scopes For Now

These should stay out of the near-term core:

- multi-tenant SaaS control plane
- blind provider fan-out for its own sake
- `vm_gui` as a co-equal near-term lane without real workload pressure
- broad platform-clone UX for thread/worktree/session management
- aggressive schema churn while execution semantics are still moving

## Suggested Local Truth Boundary

If this roadmap is later absorbed into official planning, do it in this order:

1. prove the repo-side deficiency with tests or reproducible traces
2. land the narrowest runtime fix
3. upgrade authoritative roadmap/plan/backlog surfaces
4. re-run verifier, selector, pytest, and preflight
5. keep `repo-side done / still open / live accepted` boundaries explicit

Until then, this file should be read as:

- a bounded modernization recommendation
- not a silent rewrite of the current active queue
- not a claim that the recommended phases are already approved
