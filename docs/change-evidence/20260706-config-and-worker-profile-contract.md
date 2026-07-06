# 2026-07-06 Config And Worker Profile Contract

## Slice

- 新增 repo-owned config authoritative spec
- `host_local.py`、`worker.py`、`exec_fallback.py` 不再依赖散落硬编码默认值
- `.ai/config/*.yaml` 成为正式运行时配置入口

## Evidence

- `docs/specs/config-and-worker-profiles.md`
- `.ai/config/orchestrator.yaml`
- `.ai/config/workers.yaml`
- `.ai/config/policies.yaml`
- `runtime/host-orchestrator/src/host_orchestrator/config_runtime.py`

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_wave1_execution.py -q`

## Boundary

当前只完成 repo-owned abstraction 与 deterministic config errors；实际用户侧 Codex config 仍需以宿主环境事实为准。
