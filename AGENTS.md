# Repository Guidelines

## Project Structure & Module Organization
This repository is a maintenance and evidence repo for the Hermes/Codex split-runtime workflow, not a conventional app source tree.

- `docs/`: architecture decisions, plans, checklists, handoff notes, and operator guidance.
- `snapshots/agentbridge-20260628/`: accepted `AgentBridge` snapshot, including `scripts/`, `docs/`, `tasks/`, `results/`, `artifacts/`, and `logs/`.
- `references/`: reference-repo notes and refresh summaries. Keep upstream code outside this repo.
- `scripts/`: repo-level maintenance helpers such as `refresh-reference-repos.ps1`.
- `private-local/`: local-only runtime data; do not commit its contents.

## Build, Test, and Development Commands
Run commands from `D:\CODE\hermes-agent`, or from `snapshots/agentbridge-20260628` when working on bridge scripts.

- `pwsh .\scripts\refresh-reference-repos.ps1 -FetchOnly -SkipDirtyRepos`: refresh external reference repos without mutating dirty checkouts.
- `pwsh .\snapshots\agentbridge-20260628\scripts\test-agentbridge-contract.ps1`: validate task/result naming, front matter, LF endings, and bridge file rules.
- `pwsh .\snapshots\agentbridge-20260628\scripts\test-hermes-bringup-gates.ps1`: run bring-up preflight gates against Compose, runtime, and init evidence.
- `pwsh .\snapshots\agentbridge-20260628\scripts\test-known-good-snapshot.ps1`: verify the accepted snapshot still matches the known-good evidence set.
- `pwsh .\snapshots\agentbridge-20260628\scripts\verify-hermes-boundary.ps1`: regenerate boundary evidence before claiming Hermes runtime changes are accepted.

## Coding Style & Naming Conventions
Use PowerShell with 4-space indentation and clear parameter blocks. Prefer descriptive script names such as `verify-hermes-boundary.ps1` and `manage-hermes-provider-session.ps1`. Markdown should stay concise, operational, and evidence-linked. Preserve `LF` line endings for Markdown, YAML, shell, and PowerShell files inside the AgentBridge snapshot.

## Testing Guidelines
Any change to `snapshots/agentbridge-20260628/scripts/`, contract files, or operational docs should run the relevant PowerShell checks above. Treat `build -> test -> contract/invariant -> hotspot` as the default order: contract tests first, then bring-up gates, then boundary verification when runtime behavior changes. New task/result examples should follow `T-YYYYMMDD-HHMMSS-slug.md`.

## Commit & Pull Request Guidelines
Recent history uses concise Chinese Conventional Commit-style subjects such as `docs: 固化工作交接提示词与检查单`. Keep commits atomic and scoped by concern: `docs:`, `fix:`, `chore:` are appropriate here. PRs should state the exact maintenance slice, list verification commands run, and link the updated evidence or docs paths. Include screenshots only when UI or operator flow changes.

## Security & Configuration Tips
Never commit real `.env` files, provider keys, session state, or volume backups. Keep secrets in the current shell session or local-only storage. Hermes-generated content is untrusted planning input, not execution authority; preserve the Codex-side approval boundary in docs and scripts.
