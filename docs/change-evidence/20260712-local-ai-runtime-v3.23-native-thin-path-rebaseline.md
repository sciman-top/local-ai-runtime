# Local AI Runtime v3.23 Native Thin-Path Rebaseline

## Result

`local-ai-runtime-0.2-v3.23` is the current frozen baseline candidate. The
candidate narrative remains exactly 188325 bytes with SHA-256
`80562322ebc744eda2a87a17c45f73a11982f4947c9d10e8628bb6f73ee9d5c6`.
`BaselineLineage.v2` remains exactly 3495 bytes with SHA-256
`49141a69c9aed6065ba063714fb2349750e500199ed8dfaf64fa6e2b198b9043`.

The decision remains **Request changes**. The package has 15 required
artifacts, 2 present artifacts, and 13 missing artifacts. No Baseline Approval,
Truth Reset, `runtime/local-ai-runtime`, Implementation Acceptance, Full Q0/P2
Admission, Batch claim, writer, task ref, scheduled run, provider change, or
live acceptance was created by this rebaseline.

## Scope

This planning-control-plane slice projects the already frozen v3.23 narrative
into the human-readable authority surfaces, selector, verifier, governance
tests, evidence index, and legacy overlay boundary. It does not change current
runtime behavior.

The planning verifier additionally fails closed for a future terminal Native
thin-path evaluation. `result_ref`, `decision_ref`, and `evidence_ref` must be
real JSON objects under the evaluation root; their baseline/status/decision and
cross-references must agree, and the evidence object must bind the exact result
and decision bytes by SHA-256. A path-shaped string alone cannot release P0A.

- The active queue remains `LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE`.
- The only selectable task is `LAR-P0A-EVAL-001` with
  `run_native_thin_path_evaluation_first`.
- The v3.23 machine graph has 65 tasks. The two evaluation tasks precede
  `LAR-P0A-002`; the 35 P1 implementation slices and the 11 closed contract
  projections remain bounded as before.
- `runtime/host-orchestrator`, `.ai/config`, `.ai/state/control-plane.db`,
  existing evidence, providers, credentials, runtime selection, and legacy
  behavior remain unchanged.

## Decisions Projected

### Product and Throughput

The product promise is low-human, predictable, recoverable development
throughput. Native direct/spec/program paths optimize lower interaction latency
through less waiting and less repeated context. Epoch 1 Batch keeps global
`capacity=1` as a reliability and recovery boundary. It is not a high-concurrency
throughput promise.

### Native Thin-Path Evaluation

Before Baseline Approval and remaining P0A closure, the evaluation must freeze a
single repo snapshot, task families, success oracles, model/effort, tool
inventory, sandbox, gates, repeats, counterbalancing, and human-intervention
minute definition. It compares:

1. thin Codex Native;
2. Native plus key gates;
3. Superpowers only where comparable;
4. Trellis only where comparable;
5. Hermes only where its remote/VPS/cron role is comparable.

Required metrics are task success, missed defect/regression, safety/gate/evidence
completeness, net human minutes, P50/P95 wall time, token/cost, conflict/rework,
recovery/rollback success, and sampled downstream outcome. Quality, security, or
evidence regression invalidates an efficiency gain. Unknown or unowned external
effects and unreproducible recovery/rollback stop the evaluation.

### Capability Generations

CLI and SDK execution interface, App Server client protocol, managed Worktree
isolation, and Automations scheduling are independent capability surfaces. A
surface must qualify its version/help/schema/tool inventory, sandbox/permission
behavior, state/effect boundary, recovery/rollback, and evidence projection.
Qualification never transfers across surfaces or merely because the same Codex
installation exposes them.

The only terminal decisions are:

- `preserve_v3_23_semantics`: record non-normative evidence and release P0A
  closure;
- `narrow_profile_or_adapter_candidate`: freeze v3.23 and select successor
  creation;
- `supersede_required`: freeze v3.23 and select successor creation.

Any result that changes a Batch prohibition, adapter, authority, concurrency,
Q0 trigger, quality promotion, or truth source must create v3.24 plus its
lineage, inventory, DAG, selector, verifier, and authority projections. It must
not rewrite v3.23.

### Long-Term Quality Signal

`commit-ready` is not an independent long-term quality signal. P4 promotion now
requires sampled `DownstreamOutcomeRecord` evidence for human review disposition,
merge/reject/rework, later CI, revert, or defect outcomes. The runtime does not
push, retrieve remote CI, or decide merge/reject. `censored|unknown` remains in
the denominator and is not a pass.

### Legacy Narrative Boundary

`docs/specs/adaptive-orchestration.md` is explicitly legacy, experimental, and
non-authoritative. Its historical `PHASE-1-VERTICAL-SLICE` and
`Hermes -> AgentBridge -> Codex` language cannot select current work or define
v3.23 semantics.

## Verification Record

The commands below are rerun after the final documentation, selector, test, and
evidence edits. Final results are recorded only after those fresh commands
complete:

| Gate | Result |
|---|---|
| Focused planning governance | `61 passed in 7.20s` |
| Full host-orchestrator pytest | `219 passed in 43.96s` |
| Planning verifier | exit 0; v3.23; 65 tasks; 13 missing; `LAR-P0A-EVAL-001`; `contract_pending` |
| Read-only selector | exit 0; `run_native_thin_path_evaluation_first`; no side effects or governance issues |
| Governance preflight | exit 0; 219 tests, verifier, selector, Python/PowerShell script parse and diff check passed |
| Diff hygiene | `git diff --check` exit 0 |

## N/A Gates

### Build

- `status`: `gate_na`
- `reason`: this slice changes candidate planning control-plane artifacts and
  `runtime/local-ai-runtime` does not exist
- `alternative_verification`: host-orchestrator pytest, planning verifier,
  selector, governance preflight, and diff hygiene
- `evidence_link`: `docs/specs/acceptance-and-gates.md` and this record
- `expires_at`: `LAR-P0D-001`

### Hotspot

- `status`: `gate_na`
- `reason`: this slice does not change a runtime hot path
- `alternative_verification`: planning governance tests, verifier, selector,
  preflight, and diff hygiene
- `evidence_link`: `docs/specs/acceptance-and-gates.md` and this record
- `expires_at`: first executable runtime slice after `LAR-P0D-001`

## Residual Risks and Rollback

The evaluation contract and execution are still pending. A green planning
verifier only proves the current planning projection is internally consistent;
it cannot grant Baseline Approval or infer any Codex surface qualification.

Rollback reverts only this v3.23 planning projection, selector/test alignment,
legacy-document warning, and repo-level evidence. It preserves frozen v3.17-v3.23
bytes and hashes, the v3.22 superseded inputs, current runtime behavior, `.ai`
state/config, and historical task evidence. It does not create, revoke, or
supersede an approval record.
