# 20260706 Layout Defaults To AI State

## Summary

`runtime/host-orchestrator` 的默认 runtime layout 已从 `private-local/control-plane` 切换到 `.ai/state` 与 `.ai/runs`，与当前 authoritative docs 保持一致。

## Changed surfaces

- `runtime/host-orchestrator/src/host_orchestrator/paths.py`
- `runtime/host-orchestrator/tests/test_scaffold.py`

## Why

- 当前主真源已将 `.ai/state/control-plane.db` 与 `.ai/runs/<run_id>/<task_id>/` 定义为正式默认布局
- 旧默认值会让 repo-side active truth 与代码默认行为不一致

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_scaffold.py -q`
- `python .\scripts\verify-planning-status.py`
- `python .\scripts\select-next-work.py`

## Boundary

- 本次只迁默认 layout
- `private-local/` 仍保留给 wave smokes、probe、密钥与非正式回放态
- `test_wave1_execution.py` 本次不重写；它通过 `RuntimeLayout` 跟随默认值
