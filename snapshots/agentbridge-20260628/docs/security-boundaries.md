# Security Boundaries

## Guaranteed

- `Hermes` runs in a container instead of directly on the Windows host
- no Windows GUI control is granted to Hermes in v1
- no public ports are exposed
- no dashboard is enabled
- no Docker socket is mounted
- no shared key is used with Codex
- runtime limits are set at the Compose service level
- the runtime uses approved bootstrap plus non-root service uid/gid mapping
- only two storage surfaces are allowed:
  - `/opt/data` named volume
  - `/bridge` bind mount

## Not guaranteed

- strict outbound network allowlisting
- host-level complete isolation
- cryptographic signing for task/result files
- automatic protection from bad task content

## Honest boundaries

### 1. Task/result files are not cryptographically signed

`tasks/*.md` and `results/*.md` do not carry signatures.

Their integrity comes from:

- narrow write paths
- human review
- immutable task rules
- artifact hashes in results

That is useful, but it is not the same as signed provenance.

### 2. Hermes-generated task content is untrusted input

Hermes can hallucinate, overreach, or be manipulated by prompt injection.

Therefore:

- task text is planning input only
- task text is never direct execution authority
- Codex-side approvals remain mandatory for risky actions

### 3. Compose secret usage is scoped, not magical

This setup uses Compose secrets to avoid writing the provider key into:

- docs
- repo files
- the Docker image
- the Hermes data volume

It does **not** provide Swarm-style centralized encrypted secret management.

For this bridge, the allowed operator pattern is:

- load the provider key only into the current PowerShell process
- let Compose map it into `/run/secrets/provider_api_key`
- clear the session after the Hermes run finishes

One or more slot key/base-url pairs may exist in the same local shell session, but only one active pair is projected at a time:

- `HERMES_PROVIDER_API_KEY`
- `HERMES_PROVIDER_BASE_URL`

### 4. Container isolation is practical, not absolute

This design sharply reduces file exposure by mounting only `/opt/data` and `/bridge`.

It does not claim:

- full host hardening
- full kernel isolation
- outbound network policy enforcement

### 5. Upstream packaging truth must beat local preference

This bridge prefers:

- digest-pinned images
- explicit volume init
- non-root service execution

But these preferences do not override upstream facts.

If upstream Hermes distribution or runtime behavior cannot currently satisfy those constraints with primary-source evidence, stage 2 must remain blocked instead of silently weakening the boundary.

At the moment, the sharpest example is the official Hermes Docker path itself:

- official release-tagged container publication is real
- official Dockerfile runtime currently starts with `root` at the container top level
- supervised Hermes services then drop to the `hermes` user

That means the correct local boundary is:

- root bootstrap is allowed only for container initialization and supervision
- business services and writable outputs must land under the intended non-root uid/gid
- broad mounts, Docker socket access, GUI control, and shared credentials remain prohibited

## Operating rules

- never mount `C:` broadly
- never mount `~/.codex`
- never mount `~/.claude`
- never mount browser profiles
- never mount secret stores
- never mount the Docker socket
- never treat Hermes text as approval
- never auto-install `skills-drafts/`
- never auto-retry `failed`, `blocked`, or `needs_review`
