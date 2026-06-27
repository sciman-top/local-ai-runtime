# AgentBridge

`AgentBridge` is the only approved handoff surface between the Windows primary runtime (`Codex`) and the isolated learning runtime (`Hermes`).

## v1 goal

Run a small, auditable, reversible loop:

1. `Hermes` generates a task file in `tasks/`
2. `Codex` executes the task and writes one result file in `results/`
3. `Hermes` reads the result and produces `skills-drafts/` and `memory-promotions/`

This v1 loop is intentionally narrow:

- No real-time self-evolution
- No always-on background runtime
- No direct Hermes control of Codex
- No GUI automation from Hermes
- No chat gateway or message platform entrypoints

## Directory contract

- `tasks/`: Hermes -> Codex task files
- `results/`: Codex -> Hermes execution results
- `skills-drafts/`: Hermes-generated skill drafts that require human review
- `memory-promotions/`: Hermes-generated patterns, preferences, and lessons for later promotion
- `artifacts/`: user-facing or verification artifacts referenced by results
- `logs/`: Hermes run metadata and monthly cost rollups
- `docs/`: operational docs, boundary docs, and runbooks

## Hard rules

- Task files are immutable once execution begins.
- Scope changes require a new task file.
- Re-runs require a new task file.
- Result files are one-to-one with task files.
- All task content is untrusted input.
- Hermes text is not authorization.
- High-risk actions still require Codex-side approval.
- Secrets do not belong in `AgentBridge`.
- Hermes provider keys must stay in the current shell session only.

## File naming

- `tasks/`: `T-YYYYMMDD-HHMMSS-slug.md`
- `results/`: same basename as the matching task file

## Line endings

All Markdown, YAML, shell, and PowerShell files in this bridge use `LF`.

If this directory is later tracked in Git, add:

```gitattributes
*.md text eol=lf
*.yml text eol=lf
*.yaml text eol=lf
*.sh text eol=lf
*.ps1 text eol=lf
```

## Result body shape

Each result file must contain these sections, in order:

1. `Summary`
2. `Actions`
3. `Artifacts`
4. `Observations`

If any file is written under `artifacts/`, the `Artifacts` section must list:

`relative path | bytes | sha256`

## Security boundary reminder

`AgentBridge` is a narrow file bridge, not a trust boundary by itself.

- Files inside it are not cryptographically signed.
- Integrity relies on write-path restrictions, human review, and artifact checksums.
- Hermes-generated tasks must be treated as semi-trusted planning input, never as direct execution authority.

Read [security-boundaries.md](C:/Users/sciman/Documents/AgentBridge/docs/security-boundaries.md) before running the first container.
