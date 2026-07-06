# Repository Guidelines

## Project Structure & Module Organization
This repository is the mainline repo for the generic local AI Dev Orchestrator, with Hermes/AgentBridge preserved as a compatibility and historical baseline. It is no longer just a Hermes maintenance repo.

- `docs/`: current authoritative product, architecture, contract, roadmap, migration, and compatibility docs.
- `docs/change-evidence/`: repo-level governance evidence index and dated closeout notes.
- `.ai/config/`: repo-owned runtime config contract for worker profiles, policies, and orchestrator defaults.
- `runtime/host-orchestrator/`: current Python implementation seed and test surface for the orchestrator mainline.
- `snapshots/agentbridge-20260628/`: accepted `AgentBridge` snapshot, including `scripts/`, `docs/`, `tasks/`, `results/`, `artifacts/`, and `logs/`.
- `references/`: reference-repo notes, governance companions, and refresh summaries. Keep upstream code outside this repo.
- `scripts/`: repo-level maintenance helpers such as `refresh-reference-repos.ps1`, `select-next-work.py`, and `governance/preflight.ps1`.
- `private-local/`: local-only runtime data; do not commit its contents.

## Build, Test, and Development Commands
Run commands from `D:\CODE\local-ai-dev-orchestrator`, or from `runtime/host-orchestrator` / `snapshots/agentbridge-20260628` when working on the corresponding slice.

- `python .\scripts\verify-planning-status.py`: verify the machine-readable planning truth and authoritative-doc consistency gate.
- `python .\scripts\select-next-work.py`: select the current repo-side next action from planning truth + Governance Overlay entrypoints.
- `uv run --project .\runtime\host-orchestrator python -m pytest`: run the current orchestrator repo-side Python test suite on Windows without relying on the `pytest.exe` wrapper.
- `pwsh .\scripts\refresh-reference-repos.ps1 -FetchOnly -SkipDirtyRepos`: refresh external reference repos without mutating dirty checkouts.
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`: run the release-style local closeout gate for docs/scripts/governance slices.
- `pwsh .\snapshots\agentbridge-20260628\scripts\test-agentbridge-contract.ps1`: validate task/result naming, front matter, LF endings, and bridge file rules.
- `pwsh .\snapshots\agentbridge-20260628\scripts\test-hermes-bringup-gates.ps1`: run bring-up preflight gates against Compose, runtime, and init evidence.
- `pwsh .\snapshots\agentbridge-20260628\scripts\test-known-good-snapshot.ps1`: verify the accepted snapshot still matches the known-good evidence set.
- `pwsh .\snapshots\agentbridge-20260628\scripts\verify-hermes-boundary.ps1`: regenerate boundary evidence before claiming Hermes runtime changes are accepted.

## Coding Style & Naming Conventions
Use PowerShell with 4-space indentation and clear parameter blocks. Prefer descriptive script names such as `verify-hermes-boundary.ps1` and `manage-hermes-provider-session.ps1`. Markdown should stay concise, operational, and evidence-linked. Preserve `LF` line endings for Markdown, YAML, shell, and PowerShell files inside the AgentBridge snapshot.

## Testing Guidelines
Any change to the orchestrator mainline docs should run `python .\scripts\verify-planning-status.py`. Any change to repo-level governance routing should also run `python .\scripts\select-next-work.py` and `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`. Any change to `runtime/host-orchestrator` should run the relevant Python tests. Any change to `snapshots/agentbridge-20260628/scripts/`, compatibility contract files, or Hermes operational docs should run the relevant PowerShell checks above. Treat `build -> test -> contract/invariant -> hotspot` as the default order. New task/result examples should follow `T-YYYYMMDD-HHMMSS-slug.md`.

## Commit & Pull Request Guidelines
Recent history uses concise Chinese Conventional Commit-style subjects such as `docs: 固化工作交接提示词与检查单`. Keep commits atomic and scoped by concern: `docs:`, `fix:`, `chore:` are appropriate here. PRs should state the exact maintenance slice, list verification commands run, and link the updated evidence or docs paths. Include screenshots only when UI or operator flow changes.

## Security & Configuration Tips
Never commit real `.env` files, provider keys, session state, or volume backups. Keep secrets in the current shell session or local-only storage. Hermes-generated content is untrusted planning input, not execution authority; preserve the Codex-side approval boundary in docs and scripts. Treat `docs/platforms/hermes/` and `snapshots/agentbridge-20260628/` as compatibility/historical surfaces, not the current orchestrator mainline truth. Treat `D:\CODE\governed-ai-coding-runtime` as a formal `governance-sidecar` reference companion for gate/evidence/selector design, not as the current runtime implementation truth for this repo.
