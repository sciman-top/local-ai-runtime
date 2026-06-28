# Implementation Status

## Completed on 2026-06-27

- created the full `AgentBridge` directory scaffold
- created contract templates for `tasks/`, `results/`, `skills-drafts/`, and `memory-promotions/`
- created the v1.6 operational docs:
  - `docs/codex-checklist.md`
  - `docs/hermes-docker.md`
  - `docs/security-boundaries.md`
- created Docker Compose, non-root image, init, start, verify, and snapshot helper scripts
- added executable contract validation and Docker post-install verification helpers
- added a sync-back helper from the validated workspace mirror to `Documents\\AgentBridge`
- added an offline scenario 1 smoke flow that creates one task, one artifact-backed result, and one memory-promotion record without Docker
- added an offline failure-protocol smoke flow for `failed`, `blocked`, and `needs_review`
- tightened contract validation to catch orphan result files and memory-promotion linkage errors
- added a bring-up gate checker for the explicit v1.6 stage-2 preconditions
- added a known-good snapshot validator for post-bring-up evidence
- verified all created files use `LF`
- verified all PowerShell scripts parse cleanly
- verified both shell scripts parse cleanly under `Ubuntu-24.04`
- verified the offline scenario 1 loop in the workspace mirror:
  - task file generated
  - result file generated with artifact checksum
  - memory-promotion file generated
  - expanded contract validator passed against generated files
- verified the offline failure-protocol loop in the workspace mirror:
  - `failed`, `blocked`, and `needs_review` task/result pairs generated
  - manual-only next actions were recorded
  - expanded contract validator passed against generated files
- removed the debug-only orphan result and re-verified that both the workspace mirror and the real `Documents\\AgentBridge` tree pass the stricter validator
- verified the bring-up gate checker in the workspace mirror:
  - it reports the bridge as not ready
  - it pinpoints the current missing gates as unresolved release tag, unresolved digest, and missing independent key
- verified the bring-up gate checker in the real `Documents\\AgentBridge` tree with the same result:
  - the bridge is not yet ready for first Hermes bring-up
  - the current missing gates are unresolved release tag, unresolved digest, and missing independent key
- verified the known-good snapshot validator in the workspace mirror:
  - with no snapshot present, it returns a structured not-ready result instead of failing unclearly
- verified host prechecks:
  - `WSL = 2.6.1.0`
  - no Windows `docker` or `dockerd` found before install
  - no conflicting distro-local `docker` or `dockerd` found in `Ubuntu` or `Ubuntu-24.04`
- verified Docker Desktop runtime after installation:
  - Windows Docker client/server are reachable
  - `docker run --rm hello-world` succeeds on Windows
  - `Ubuntu-24.04` still reports Docker Desktop WSL integration is not enabled
- verified Hermes upstream packaging truth from primary sources:
  - latest source release is `v2026.6.19`
  - official Docker workflow publishes release tags to `nousresearch/hermes-agent:<release_tag>`
  - Docker Hub registry metadata for `nousresearch/hermes-agent:v2026.6.19` resolves to manifest digest `sha256:9f367c7756ef087661a361536a89f438d57a122b958dc23d82d456b1433e6e9e`
  - the official upstream Dockerfile starts as `root` and drops supervised services to `hermes` via `s6-overlay`
- confirmed local Docker Desktop state:
  - Desktop engine is running
  - Docker Desktop local logs show `wslIntegration.distros = []`
  - no supported Docker Desktop CLI subcommand was found for enabling per-distro WSL integration on this host
- tightened v1.6 bring-up implementation:
  - `compose.hermes.yml` now uses an explicit named volume default: `agentbridge-hermes-data`
  - `build-hermes-nonroot.ps1` now writes `docs/hermes-runtime.json`
  - `init-hermes.ps1` now writes `docs/hermes-volume-init.json` after successful one-shot init verification
  - `start-hermes.ps1` now fails closed if volume init evidence is missing
  - `test-hermes-bringup-gates.ps1` now checks actual runtime-profile and volume-init evidence instead of only checking script presence
  - `new-known-good-snapshot.ps1` is prepared to create a real `/opt/data` backup and record its hash in the snapshot
  - Docker-facing scripts now fail closed on nonzero external exit codes instead of assuming success from `ErrorActionPreference`
  - `resolve-hermes-image.ps1` now records structured blocked state instead of writing empty digest/config fields as if resolution had succeeded
- the runtime model is now aligned to upstream reality:
  - official image digest is resolved and recorded
  - runtime profile uses the official root-bootstrap plus `HERMES_UID` / `HERMES_GID` remap model
  - volume init is completed and evidenced in `docs/hermes-volume-init.json`
  - session-only provider slot handling is now implemented through `scripts/manage-hermes-provider-session.ps1`
  - one-shot bring-up orchestration is now implemented through `scripts/invoke-hermes-bringup-once.ps1`
  - fixed `scripts/start-hermes.ps1` PowerShell argument assembly so one-shot bring-up no longer fails at the `+ $HermesArgs` parsing step
- verified the mixed-application `.env` path with the real `D:\CODE\qq-codex-bot\.env` file:
  - the parser now treats `HERMES_SLOTS` as authoritative
  - unrelated app env vars are no longer misread as Hermes slot definitions
  - `manage-hermes-provider-session.ps1 -Action load -EnvFilePath ...` now loads only the declared Hermes slots
- hardened the first formal run path:
  - `manage-hermes-provider-session.ps1` now projects `HERMES_INFERENCE_MODEL` and `HERMES_INFERENCE_PROVIDER`
  - `run-hermes-wrapper.sh` now exports those runtime values before calling Hermes
  - `start-hermes.ps1` now pre-creates and `chmod 666`s the current day/month JSONL log files so the non-root service can append on the Windows bind mount
- verified the real Windows-side bring-up path with the actual provider file:
  - `start-hermes.ps1 profile list` succeeds after loading the real `.env`
  - `invoke-hermes-bringup-once.ps1 -EnvFilePath 'D:\CODE\qq-codex-bot\.env' -SkipSnapshot` succeeds
  - full `invoke-hermes-bringup-once.ps1 -EnvFilePath 'D:\CODE\qq-codex-bot\.env'` succeeds
  - the full run generated `docs/known-good-20260628-000717.json`
  - `test-known-good-snapshot.ps1` passes against that snapshot

## Completed on 2026-06-28

- improved `verify-hermes-boundary.ps1` so the helper container now follows the real `sh /bridge/scripts/run-hermes-wrapper.sh chat` path instead of `sleep 300`
- replaced the one-shot `ps` check with bounded `docker top` polling so boundary evidence waits for the supervised Hermes process tree to settle
- verified the real Windows-side boundary result now reports:
  - `service_uidgid_present = true`
  - `service_uidgid_lines` includes `/opt/hermes/.venv/bin/python3 /opt/hermes/.venv/bin/hermes chat`
- recorded the current boundary evidence at:
  - `docs/verify-hermes-boundary-20260628-005239.json`
- fixed the live custom-gateway runtime for `ai.input.im`:
  - switched the live config from bare `provider: custom` to a named custom provider with explicit `key_env: OPENAI_API_KEY`
  - pinned the gateway base URL to `https://ai.input.im/v1`
  - added `model.default_headers.User-Agent: curl/8.7.1` to avoid gateway/WAF blocks on the default OpenAI SDK headers
- fixed the wrapper fail-closed behavior:
  - `run-hermes-wrapper.sh` now marks the run as failed when Hermes prints known fatal markers even if the process exit code was `0`
- fixed Hermes non-interactive output handling in the bridge:
  - `start-hermes.ps1` now forwards stdout for non-interactive commands instead of swallowing successful `chat -q` / `--oneshot` replies
- fixed interactive classic CLI TTY handling in the bridge:
  - root cause: `run-hermes-wrapper.sh` captured interactive `hermes` output via command substitution, so `chat --cli` inherited stdin TTY but non-TTY stdout and looked hung with no visible prompt
  - bridge fix: interactive `chat` / `auth` / `model` / `setup` with attached tty now `exec hermes "$@"` directly instead of buffering output
- fixed the default bring-up `--oneshot` regression:
  - root cause: Hermes upstream oneshot treats `HERMES_INFERENCE_MODEL` as an explicit model override, auto-detects `gpt-5.4` from a custom OpenAI-compatible endpoint to the non-routable group alias `openai`, then fails with `Unknown provider 'openai'`
  - bridge mitigation: `run-hermes-wrapper.sh` now clears `HERMES_INFERENCE_MODEL` and `HERMES_INFERENCE_PROVIDER` only for `--oneshot/-z` runs that do not explicitly pass `--model/--provider`, forcing Hermes back onto the persisted config provider pair
- hardened known-good snapshot creation against same-second collisions:
  - `new-known-good-snapshot.ps1` now uses millisecond-resolution snapshot filenames
- re-verified the full default bring-up after the interactive wrapper fix:
  - `invoke-hermes-bringup-once.ps1 -EnvFilePath 'D:\CODE\qq-codex-bot\.env'` succeeds
  - the post-fix run generated `docs/known-good-20260628-131518-032.json`
  - `test-known-good-snapshot.ps1` passes against that snapshot

## Current Status

- Windows-side v1.6 bring-up is now operational end-to-end
- the latest verified known-good snapshot is:
  - `docs/known-good-20260628-131518-032.json`
- the latest verified boundary evidence is:
  - `docs/verify-hermes-boundary-20260628-005239.json`
- `docs/known-good-20260628-124819-747.json` is now historical pre-chat-cli-fix evidence, not the current anchor
- the older `docs/known-good-20260627-214819.json` should be treated as stale pre-fix evidence, not the current anchor
- `invoke-hermes-bringup-once.ps1` now returns the final `session_cleared` state after the cleanup step, instead of emitting the summary too early
- the verified non-interactive smoke commands are now:
  - `start-hermes.ps1 --oneshot 'Reply with exactly OK.'` -> prints `OK`
  - `start-hermes.ps1 chat -Q -q 'Reply with exactly OK.'` -> prints `OK`
  - `invoke-hermes-bringup-once.ps1 -EnvFilePath 'D:\CODE\qq-codex-bot\.env'` -> prints `OK` and completes boundary + snapshot validation

## Remaining limitations

- `Ubuntu-24.04` still does not have Docker Desktop WSL integration enabled
  - Windows-side bring-up is already working
  - only in-distro `docker` use inside `Ubuntu-24.04` remains unavailable
- the Hermes oneshot provider bug is mitigated in AgentBridge, not fixed upstream
  - if the upstream Hermes code path changes, re-validate the wrapper mitigation before removing it

## Resume Point

1. Verified shortest path:
   - `& 'C:\Users\sciman\Documents\AgentBridge\scripts\invoke-hermes-bringup-once.ps1' -EnvFilePath 'D:\CODE\qq-codex-bot\.env'`
2. If you only want a start-and-boundary check without snapshot:
   - `& 'C:\Users\sciman\Documents\AgentBridge\scripts\invoke-hermes-bringup-once.ps1' -EnvFilePath 'D:\CODE\qq-codex-bot\.env' -SkipSnapshot`
3. If you want to inspect the current slot projection only:
   - `& 'C:\Users\sciman\Documents\AgentBridge\scripts\manage-hermes-provider-session.ps1' -Action load -EnvFilePath 'D:\CODE\qq-codex-bot\.env' -SkipBackupPrompt`
4. If you want the classic interactive REPL explicitly:
   - `& 'C:\Users\sciman\Documents\AgentBridge\scripts\invoke-hermes-bringup-once.ps1' -EnvFilePath 'D:\CODE\qq-codex-bot\.env' chat --cli`
5. If Linux-side `docker` usage inside `Ubuntu-24.04` is still desired, enable Docker Desktop WSL integration for that distro.
6. If you want the current boundary evidence anchor directly:
   - `docs/verify-hermes-boundary-20260628-005239.json`
