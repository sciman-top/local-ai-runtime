# Local AI Runtime v3.22 Candidate Rebaseline

## Result

`local-ai-runtime-0.2-v3.22` is the current self-contained baseline candidate. The candidate narrative is frozen at 178330 bytes with SHA-256 `8338A9DCF4BBBB40CA28F4F2EC6DCA37587EE94FBFBBC6E3A0063C4DE379569C`. `BaselineLineage.v1` is frozen at 3134 bytes with SHA-256 `8BB29E0FBC4990749424E07368E5B1C0F09CF378E78D1ADA38B8FE998FB97B35`.

The decision remains **Request changes**. The normative package has 15 required artifacts: `P0A-SOURCE` and `P0A-LINEAGE` are present, while 13 artifacts remain missing. No `BaselineApprovalRecord`, Truth Reset, `runtime/local-ai-runtime` package, Implementation Acceptance, Full Q0/P2 Admission, Batch claim, writer, task ref, scheduled run or live evidence was created.

## Scope

This rebaseline supersedes v3.21 without reopening the proven single-machine architecture. It updates only the preapproval narrative and planning control plane:

- one frozen v3.22 candidate and one v3.22-bound `BaselineLineage.v1`;
- the non-normative package inventory and stable baseline navigation entry;
- AGENTS/README plus PRD, architecture, roadmap, implementation plan, backlog and acceptance projections;
- the machine work-item DAG, planning state, selector policy, verifier, governance tests and preflight wording;
- this repo-level evidence and its index.

Intentionally unchanged:

- `runtime/host-orchestrator`, `.ai/config`, `.ai/state/control-plane.db` and all live runtime behavior;
- provider/auth/keyring, scheduler, installed runtime selection and live processes;
- repository ownership, cutover state, task evidence and target refs;
- `runtime/local-ai-runtime`, which remains absent until the approved implementation sequence reaches `LAR-P0D-001`.

## Decisions Absorbed

### Long-Term Product Boundary

The long-term target is a Windows-local, single-operator-trust-domain, general-purpose governed AI development execution platform. It covers qualified repositories and future explicitly admitted local development workspaces, but not cross-platform operation, multi-tenancy, distributed workers, organization RBAC, billing or general desktop automation.

Epoch 1/v0.2 remains `qualified_git_repo_v1`, one Python/SQLite control plane, one Codex agent runtime and global capacity exactly one. Unimplemented capabilities are `unsupported`; configuration cannot make an absent protocol safe.

### Three-Level Evolution And One Activation Unit

Changes are classified as `profile_generation`, `capability_generation` or `architecture_epoch`, but runtime authority activates one non-circular composition:

`C = RuntimeCompositionManifest -> I(C) -> Q(C,I,staged_identity) -> B(C,I,Q,expected_previous_active) -> A(B,pointer_result,quick_preflight)`.

`SelectedRuntimeIdentity` exists after the guarded `current.json` pointer update. `ActiveRuntimeIdentity` exists only after a terminal `activated_and_preflight_passed` record. Qualification, Authorization and attempts bind the admitted identity; selected-but-not-admitted or unfinished activation recovery cannot claim work.

### Writer And Controller Effects

`writer_effect_id` is stable for one task generation and resolved writer intent. `writer_launch_id` is unique per fresh attempt. `writer_execution_committed` is zero or one per task generation; after commit, no replacement or speculative writer may start. A provably terminated suspended process before execution commit may be retried only in a fresh attempt.

Adoptable controller/Git actions retain their own root logical-effect authority, non-branching adoption chain, deterministic postcondition and read-back rules. This does not claim process-level exactly-once execution.

### Capability And Delivery Boundaries

The v0.2 capability set is `codex_exec_v1`, `sha1_files_refs_v1`, `local_commit_task_ref_v1` and `task_egress_denied_v1`. Codex 0.144.1, the initial model/effort, exact limits and gates belong to an execution profile. New Provider, network, remote delivery, Git format or workspace authority requires a capability protocol and acceptance; multi-writer concurrency requires a successor architecture epoch.

Git publication uses `git_hybrid_materialization_v1`: the controller creates canonical payloads, graph and expected OIDs; pinned Git `hash-object -w` materializes attempt-local objects; `cat-file` reads type, size and payload back. Git is not the only oracle, and the controller does not implement loose-object zlib.

### Governed Autonomy

The required action surface is `durable_local_status_v1`; `qualified_windows_toast_v1` is an optional push transport and cannot own action durability. Portfolio inputs are content-addressed, qualification-bound closed-schema data. Repository-provided selector code is never executed in v0.2.

P4 runs under B2/per-repository scheduling. A green P4 cohort independently unlocks `LAR-P4-002` for controlled B3 activation and `LAR-P5-001` for cutover; P5 does not depend on B3. Epoch 1 global capacity remains one.

## Machine Execution Projection

`docs/plans/local-ai-runtime-0.2-work-items.json` is `local_ai_runtime_work_items.v3` and contains 62 tasks. P1A-P1F has 35 implementation slices with counts `4 + 5 + 7 + 6 + 7 + 6`. The graph is a deterministic DAG with one declared root, reciprocal dependency/successor edges, full root reachability, no cycle and stable ready ordering by priority then UTF-8 task ID.

Eleven closed projections bind one normative producer to implementation and acceptance consumers:

1. `work_definition_task_family_v1`
2. `effect_plan_v1`
3. `gate_graph_v1`
4. `three_level_evolution_v1`
5. `writer_effect_launch_identity_v1`
6. `durable_operator_action_inbox_v1`
7. `git_hybrid_materialization_v1`
8. `q0_trigger_policy_v1`
9. `controlled_baseline_approval_v1`
10. `activation_admission_chain_v1`
11. `portfolio_data_only_v1`

The verifier checks the frozen catalog, exact task roles, reverse declarations and per-task token sets. It also binds the superseded v3.21 plan identity, rejects `uv run --frozen`, requires `uv lock --check --offline` plus `uv run --locked --offline`, rejects completed history actions as selector choices and mechanically enforces the P4/B3/P5 order.

The final five-axis review closed three additional fail-closed issues in the mutable planning control plane without changing the frozen narrative or lineage bytes:

- inventory lineage must be an exact role-derived projection of `BaselineLineage.v1`, not a separately editable summary;
- selector consumption is bound to the verifier-attested raw status/policy paths and SHA-256 values, so a policy copy or post-verification status drift returns `repair_gate_first`;
- P4 can select `LAR-P4-002 / activate_b3_portfolio_generation_first` or independently select `LAR-P5-001 / cut_over_repositories_first`; the B3 state is explicit, and the reviewed action/condition catalog rejects structurally valid unknown actions.

Current state is deliberately narrow:

- queue: `LOCAL-AI-RUNTIME-0.2-BASELINE-CLOSURE`;
- current task: `LAR-P0A-002`;
- selector action: `close_baseline_normative_package_first`;
- package: 15 required / 2 present / 13 missing;
- Baseline Approval, Truth Reset, implementation, Full Q0/P2 and rollout: false.

## Five-Axis Review

| Axis | Review result |
|---|---|
| Correctness | Candidate, lineage, inventory, planning status, stable entry and machine graph use one v3.22 identity. The activation chain is non-circular, writer effect and launch identities are distinct, and P4 releases separately routable B3 and P5 work without making either depend on the other. |
| Readability | Product constants, capability boundaries, task roles, stop conditions, evidence paths and rollback scopes are explicit. The 62-task DAG remains bounded by concrete primary files and verification commands. |
| Architecture | Stable authority/fencing/evidence semantics remain in one Python/SQLite modular monolith. Profile choices cannot create capabilities; capability protocols and architecture epochs are separate change classes. No cross-platform, tenant, distributed or plugin-market abstractions were added. |
| Security | Approval is a controlled external operator action with authority/session/generation/anti-replay semantics; activation uses a durable intent and mutex; repo content is treated as untrusted and its effects are contained without claiming prompt-injection elimination. Writer zero-or-one and controller-action adoption are not conflated. Lineage, status, policy and selector action identities fail closed under drift or substitution. |
| Performance | The planning verifier and selector remain bounded local reads over 62 tasks and 11 projections. Epoch 1 capacity remains one; no runtime hot path, scheduler or provider process changed. |

## Verification Record

Fresh verification on the final reviewed implementation state before this evidence-only update:

| Gate | Result |
|---|---|
| Focused planning governance | `51 passed in 6.06s` |
| Full legacy `host-orchestrator` pytest | `209 passed in 48.05s` |
| Ruff on changed Python surfaces | `All checks passed!` |
| Planning verifier | exit 0; v3.22; 62 tasks; 13 missing; `LAR-P0A-002`; status SHA-256 `c21ae9733df9f1e1609f9f317d515b296b8abac5deb464bb2a83f28d1562b3c6`; policy SHA-256 `c8125973e5521e76de5a6932edb542b35ebd6774e986e1c15c4763c1846ba6b8` |
| Read-only selector | exit 0; `close_baseline_normative_package_first`; no governance issues or side effects |
| Governance preflight | exit 0; build/hotspot N/A with bounded reasons; 209 tests, verifier, selector, script parse and diff check passed |
| JSON parse | planning status, selector policy, package inventory, work items and lineage parsed |
| Candidate identity | Python and PowerShell independently returned 178330 bytes / `8338a9dcf4bbbb40ca28f4f2ec6dca37587ee94fbfbbc6e3a0063c4de379569c` |
| Lineage identity | Python and PowerShell independently returned 3134 bytes / `8bb29e0fbc4990749424e07368e5b1c0f09cf378e78d1ada38b8fe998fb97b35` |
| Diff hygiene | `git diff --check` passed; staged-diff and secret review are repeated immediately before commit |

Because this record is an authoritative planning reference, verifier, selector, focused tests, Ruff and diff hygiene are rerun after its final bytes are written. The preflight result above remains the last full release-style run; no executable or control-plane behavior changes in this evidence-only edit.

## N/A Gates

### Build

- `status`: `gate_na`
- `reason`: this slice changes candidate planning artifacts and `runtime/local-ai-runtime` does not exist
- `alternative_verification`: full legacy pytest, planning verifier, selector and governance preflight
- `evidence_link`: `docs/specs/acceptance-and-gates.md` and this record
- `expires_at`: `LAR-P0D-001` creates `runtime/local-ai-runtime`

### Hotspot

- `status`: `gate_na`
- `reason`: this slice changes planning contracts rather than executable runtime hot paths
- `alternative_verification`: focused governance tests, full legacy pytest, verifier, selector and `git diff --check`
- `evidence_link`: `docs/specs/acceptance-and-gates.md` and this record
- `expires_at`: the first executable runtime slice after `LAR-P0D-001`

## Residual Risks And Stop Conditions

- Thirteen normative artifacts remain missing; planning green cannot authorize Baseline Approval.
- `P0A-LINEAGE` being present does not make any later artifact present and cannot be inherited by a successor narrative identity.
- The planned safety contracts are not implementation evidence. No implementation task may start before controlled Baseline Approval, Truth Reset and Legacy Ownership Guard prerequisites.
- Legacy tests and planning checks cannot substitute for staged Full Q0 on the eventual pinned Windows/Codex/Git/toolchain composition.
- Any v3.22 candidate byte change requires a successor narrative ID. Any frozen lineage byte change requires a successor lineage artifact version and synchronized inventory/manifest identity.

## Rollback

Revert only the v3.22 candidate-planning projection, verifier/tests and this evidence. Preserve the exact historical archives, existing legacy runtime behavior, `.ai` state/config, historical evidence and unrelated user changes. Rollback does not create, revoke or supersede an approval record.
