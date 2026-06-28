# Phase 0 Cap Drop Probe 2026-06-28

## Scope

This note records the `P0-1 cap_drop:[ALL]` probe against the current accepted Hermes runtime model.

The important truth boundary is:

- static Compose edits are not enough
- the real Windows-side `start-hermes.ps1 -> docker run -> run-hermes-wrapper.sh` path is the truth source

## Probe summary

The probe was executed from an isolated worktree against the snapshot runtime assets.

What was tried:

1. add `cap_drop:[ALL]` to `compose.hermes.yml`
2. mirror that in the boundary helper container
3. run the real runtime path with the current upstream-style `official_root_bootstrap` model

## Result

`cap_drop:[ALL]` is **not** currently compatible with the real runtime path.

Observed runtime failures:

- `s6-applyuidgid: fatal: unable to set supplementary group list: Operation not permitted`
- `/opt/hermes/docker/main-wrapper.sh: 63: cd: can't cd to /opt/data`

The helper probe also confirmed that the container really had `CapDrop = ["ALL"]`, so this is not a false negative caused by an un-applied flag.

## Conclusion

For the current accepted runtime model:

- `P0-1 cap_drop:[ALL]` is **blocked**
- it must not be left enabled in the accepted baseline
- any future attempt must first change the runtime model enough to remove the current bootstrap dependency on operations that fail under `CapDrop=ALL`

## Planning impact

This changes the plan status from:

- `low-risk direct closeout`

to:

- `probe completed, currently blocked by runtime facts`

The next Phase 0 slice should move to another viable item instead of forcing `cap_drop:[ALL]` into the current baseline.
