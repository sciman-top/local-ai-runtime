# Hermes Docker Runbook

This runbook brings up `Hermes` as an on-demand CLI container behind `AgentBridge`.

Chinese quick guide:

- [中文操作说明.md](C:/Users/sciman/Documents/AgentBridge/docs/中文操作说明.md)

Path note:

- examples using `.\scripts\...` assume your current directory is `C:\Users\sciman\Documents\AgentBridge`
- from any other working directory, call the script by absolute path instead

## Scope

This v1 is intentionally narrow:

- Docker Desktop + WSL2 backend
- no gateway
- no dashboard
- no ports
- no desktop control
- no browser automation
- no MCP
- no community skill installs

## Stage 0: Docker Desktop

Prerequisites:

- `WSL >= 2.1.5`
- Docker Desktop installed
- Docker WSL integration enabled only for `Ubuntu-24.04`
- no conflicting distro-local Docker Engine or CLI in `Ubuntu` or `Ubuntu-24.04`

Suggested checks:

```powershell
.\scripts\check-docker-prereqs.ps1
.\scripts\test-agentbridge-contract.ps1
.\scripts\test-hermes-bringup-gates.ps1
```

Installer helper:

```powershell
.\scripts\install-docker-desktop.ps1
```

Notes:

- the installer requests Windows elevation
- a reboot may still be required after installation
- if installation is blocked by UAC or policy, stop here and resume after the host-level prerequisite is cleared
- after installation, run `.\scripts\verify-docker-install.ps1`
- to use `docker` directly inside `Ubuntu-24.04`, Docker's official path is `Settings -> Resources -> WSL Integration -> Apply`
- on this host, Docker Desktop CLI exposes engine and feature commands, but no supported per-distro WSL-integration subcommand was found

## Stage 1: Resolve the official image

On the day you actually bring Hermes up:

1. Choose the approved stable Hermes source release tag
2. Map it to the concrete published image tag
3. Resolve its digest from the registry
4. Record `source release tag + concrete image tag + digest + resolution date`
5. Run only by digest

Helper:

```powershell
.\scripts\resolve-hermes-image.ps1 -Tag <concrete-image-tag> -SourceReleaseTag <stable-source-release-tag>
```

Output:

- `docs/hermes-image-resolution.json`

Important truth boundary:

- Hermes upstream currently provides official source releases and first-class native installers
- Hermes upstream also publishes Docker images through its official Docker workflow
- the upstream workflow currently sets `IMAGE_NAME = nousresearch/hermes-agent`
- release workflows tag the image as `nousresearch/hermes-agent:<release_tag>`
- digest resolution can be proven directly from Docker Hub registry metadata even if local Docker pull is temporarily unhealthy

`docs/hermes-image-resolution.json` must end in `resolution_status = "resolved"` before stage 2 can continue.

## Stage 2: Determine the runtime bootstrap model

Inspect the official image:

```powershell
docker image inspect <official-image@sha256:...> --format '{{.Config.User}}'
```

Decision:

- If it is already non-root, record it and reuse the official image
- If it is `root`, prefer the official bootstrap model first:
  - keep container startup as root
  - pass `HERMES_UID` / `HERMES_GID` for the intended service uid/gid
  - verify that Hermes services and writable outputs run as the remapped non-root uid/gid
- Only build a derived image if the official bootstrap model fails your local boundary or a specific integration requirement

Current caveat:

- Hermes upstream source currently includes a Dockerfile and a Docker publish workflow, but upstream runtime behavior must still be checked against this bridge's stricter v1.6 boundary
- the upstream Dockerfile currently starts the container as `root` and relies on `s6-overlay` plus `s6-setuidgid hermes` to drop privileges for supervised services
- that means the correct v1.6 boundary is service-level non-root execution with explicit uid/gid remap, not blanket `user:` at the Compose service level

Helper:

```powershell
.\scripts\build-hermes-nonroot.ps1 -BaseImage '<official-image@sha256:...>' -PreferOfficialBootstrap
```

Outputs:

- `docs/hermes-runtime.json`
- either a derived local image reference, or a recorded reuse of the official non-root image

`docs/hermes-runtime.json` is the run-time source of truth for:

- `runtime_image`
- `runtime_user`
- `bootstrap_model`
- `volume_uid`
- `volume_gid`

## Stage 3: Prepare the one-shot init container

Run the init profile once before the first formal Hermes run:

```powershell
.\scripts\init-hermes.ps1
```

Purpose:

- create `/opt/data` directory structure
- set ownership for the runtime uid/gid
- satisfy the explicit v1.6 volume-initialization gate before the first formal run
- write `docs/hermes-volume-init.json` as auditable init evidence

The init container exits immediately after initialization.

## Stage 4: Inject the provider key safely

Do not write the key into:

- `.env`
- repo files
- profile files
- volume contents
- documentation

Instead, use a fresh PowerShell session and the session-only helper.

Recommended v1.6 pattern: load one or more named provider slots.

One slot:

```powershell
.\scripts\manage-hermes-provider-session.ps1 -Action load `
  -Slots 'primary=https://provider-a.example/v1'
```

Two slots:

```powershell
.\scripts\manage-hermes-provider-session.ps1 -Action load `
  -Slots 'primary=https://provider-a.example/v1','backup=https://provider-b.example/v1'
```

Three slots:

```powershell
.\scripts\manage-hermes-provider-session.ps1 -Action load `
  -Slots 'primary=https://provider-a.example/v1','backup=https://provider-b.example/v1','glm=https://provider-c.example/v1'
```

The script will securely prompt for one key per slot, in the same order.

Compatibility note:

- old two-slot parameters `-PrimaryBaseUrl` and `-BackupBaseUrl` still work
- they are kept only as a compatibility path
- the preferred path is `-Slots`

What it does:

- securely prompts for one key per configured slot
- stores all slot key/base-url pairs only in the current PowerShell process
- sets the active key into `HERMES_PROVIDER_API_KEY`
- sets the matching active base URL into `HERMES_PROVIDER_BASE_URL`
- records the active slot name in `HERMES_PROVIDER_ACTIVE_SLOT`
- never writes the keys into docs, repo files, profile files, or `/opt/data`

You can inspect the current in-memory state without exposing the key values:

```powershell
.\scripts\manage-hermes-provider-session.ps1 -Action status
```

If the active key is rate-limited or revoked during the same shell session, switch to another loaded slot:

```powershell
.\scripts\manage-hermes-provider-session.ps1 -Action switch -Slot backup
```

This switch moves both values together:

- `HERMES_PROVIDER_API_KEY`
- `HERMES_PROVIDER_BASE_URL`

To clear both keys and the provider session from the current shell:

```powershell
.\scripts\manage-hermes-provider-session.ps1 -Action clear
```

If you prefer explicit non-interactive parameter binding for a one-off local run, the helper also accepts:

- `-PrimaryKey <SecureString>`
- `-BackupKey <SecureString>`
- `-KeyMap <hashtable>`
- `-ModelPrimary`
- `-ModelFallback`

But the normal path is interactive secure prompt input inside your local shell.

## Stage 4.5: One-shot bring-up

If you want one controlled command that loads the session, reruns gates, starts Hermes, verifies the boundary, and writes the snapshot, use:

```powershell
.\scripts\invoke-hermes-bringup-once.ps1 `
  -Slots 'primary=https://provider-a.example/v1','backup=https://provider-b.example/v1'
```

If you only have one key today, pass one slot:

```powershell
.\scripts\invoke-hermes-bringup-once.ps1 `
  -Slots 'primary=https://provider-a.example/v1'
```

If you have three keys, pass three slots:

```powershell
.\scripts\invoke-hermes-bringup-once.ps1 `
  -Slots 'primary=https://provider-a.example/v1','backup=https://provider-b.example/v1','glm=https://provider-c.example/v1'
```

Behavior:

- prompts securely for one key per configured slot
- reruns the file contract and bring-up gates
- runs a one-shot smoke command by default so the flow can finish automatically
- verifies the running container boundary
- creates and validates a known-good snapshot unless `-SkipSnapshot` is set
- clears the session keys at the end unless `-KeepSession` is set

If you want an interactive Hermes session instead of the default smoke run:

```powershell
.\scripts\invoke-hermes-bringup-once.ps1 `
  -Slots 'primary=https://provider-a.example/v1','backup=https://provider-b.example/v1' `
  chat
```

To start another Hermes subcommand in the same one-shot flow:

```powershell
.\scripts\invoke-hermes-bringup-once.ps1 `
  -Slots 'primary=https://provider-a.example/v1','backup=https://provider-b.example/v1' `
  profile list
```

`HERMES_RUNTIME_IMAGE`, `HERMES_UID`, and `HERMES_GID` are loaded automatically from `docs/hermes-runtime.json` if present.

Optional tuning:

```powershell
$env:HERMES_CPUS = '2'
$env:HERMES_MEM_LIMIT = '2g'
$env:HERMES_PIDS_LIMIT = '256'
```

Compose uses the temporary environment variable to mount `/run/secrets/provider_api_key`.

The wrapper script reads that file and exports the runtime variables for Hermes.

Field choices are deliberate:

- `cpus`, `mem_limit`, and `pids_limit` stay at the Compose service level for this single-host setup
- `memswap_limit` stays out of the default file until the host proves support and stability
- the provider key comes from a host environment variable through Compose `secrets`, so it does not need to live in `.env`

## Stage 5: Start Hermes on demand

Default bring-up:

```powershell
.\scripts\start-hermes.ps1
```

Examples:

```powershell
.\scripts\start-hermes.ps1 profile list
.\scripts\start-hermes.ps1 chat
```

The default command is `chat`.

Before the first real bring-up, rerun:

```powershell
.\scripts\manage-hermes-provider-session.ps1 -Action status
.\scripts\test-agentbridge-contract.ps1
.\scripts\test-hermes-bringup-gates.ps1
```

## Stage 6: Validate the boundary

Run:

```powershell
.\scripts\verify-hermes-boundary.ps1
```

Expected:

- approved bootstrap model
- service-level non-root execution for the intended uid/gid
- no published ports
- no Docker socket
- only the approved mounts are present:
  - `/opt/data`
  - `/bridge`
  - `/run/secrets/provider_api_key`
- no mount source points at `~/.codex`, `~/.claude`, browser profiles, or a primary code workspace

## Stage 7: Capture a known-good snapshot

After the first successful closed loop:

```powershell
.\scripts\new-known-good-snapshot.ps1
.\scripts\test-known-good-snapshot.ps1
```

This records:

- current release tag
- image digest
- compose hash
- Dockerfile hash if used
- provider/model config hash
- actual `/opt/data` volume backup path, size, and sha256
- recommended volume backup command

## Self-evolution expectation

v1 supports only human-triggered batch review:

- Hermes writes tasks
- Codex executes
- Hermes reads results
- Hermes proposes memory and skill drafts

It does **not** promise:

- real-time self-improvement
- autonomous continuous operation
- always-on background learning

## Administrator PowerShell boundary

Most `AgentBridge` operations do **not** require an elevated PowerShell session.

Typical non-admin steps:

- contract validation
- Docker Desktop post-install verification
- image resolution metadata writes
- Compose file checks
- runtime profile generation
- volume init
- container start and boundary verification
- known-good snapshot generation

Typical admin or UAC-gated host steps:

- installing or upgrading Docker Desktop
- changing Docker Desktop host settings through its installer or privileged flows
- changing system-level WSL or host security configuration

## Reference basis

- Docker Compose services reference: [services](https://docs.docker.com/reference/compose-file/services/)
- Docker Compose secrets reference: [secrets](https://docs.docker.com/reference/compose-file/secrets/)
