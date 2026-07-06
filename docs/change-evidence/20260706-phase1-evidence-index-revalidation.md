# 2026-07-06 Phase 1 Evidence Index Revalidation

## Slice

- 为 `P1-T05` 新增独立 `evidence_index.json` 重算入口
- 让 canonical result writer 与 revalidation 入口共用同一套 digest / relative-path 规则
- 对一次真实 `Codex SDK` vertical slice 产物回放 sha256 / byte_count

## Implementation

- 新增 `runtime/host-orchestrator/src/host_orchestrator/evidence_index.py`
- `runtime/host-orchestrator/src/host_orchestrator/canonical_result.py` 改为复用该模块构建 `evidence_index.json`
- `runtime/host-orchestrator/src/host_orchestrator/cli.py` 新增：
  - `--revalidate-evidence-index`
- `runtime/host-orchestrator/tests/test_wave1_execution.py` 新增：
  - 重算通过断言
  - 篡改后失败断言
  - CLI entrypoint 断言

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest`
- `uv run --project .\runtime\host-orchestrator python -m host_orchestrator --repo-root . --revalidate-evidence-index .ai/runs/phase1-live-sdk-20260706-043202/TASK-20260706-live-sdk-probe/evidence_index.json`

结果：

- `pytest`: `15 passed`
- real SDK evidence replay:
  - `checked_entry_count = 7`
  - `issue_count = 0`
  - `ok = true`

目标 real SDK evidence：

- `.ai/runs/phase1-live-sdk-20260706-043202/TASK-20260706-live-sdk-probe/evidence_index.json`

## Boundary

- 这补齐了 `Phase 1` repo-side `evidence_index.json` integrity 校验缺口
- 这不把当前 posture 升级成 `live accepted`
- `network_proxy` 仍然是 `platform_na`
