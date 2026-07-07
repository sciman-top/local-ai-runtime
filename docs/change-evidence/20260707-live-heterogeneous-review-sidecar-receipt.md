# 2026-07-07 Live Heterogeneous Review Sidecar Receipt

## Slice

- 当前 `host_local` review-gated 路径已可在配置 `review_worker_profile = claude_glm_review` 时 materialize live `review_result.json` receipt，并继续把正式结果停在 `needs_review`
- `ClaudeCodeStructuredWorker` 现在以 `--bare --no-session-persistence` 启动 `claude`，并显式按 UTF-8 解码；当前同时兼容 Claude CLI 返回的 wrapper JSON 与 direct schema-shaped JSON
- `HostLocalRunner` 现在会把 bounded primary worker output summary、runtime status、以及 verification 摘要送入 live reviewer，并在 isolated temp cwd 中运行 sidecar
- 当 primary worker output summary 缺失、live reviewer 失败、或返回的 payload 不满足 contract 时，runtime 仍 fail closed 回 repo-side blocking review receipt，而不是把 live review 伪装成成功

## Code Points

- `runtime/host-orchestrator/src/host_orchestrator/claude_code_worker.py`
- `runtime/host-orchestrator/src/host_orchestrator/process_guard.py`
- `runtime/host-orchestrator/src/host_orchestrator/host_local.py`
- `runtime/host-orchestrator/tests/test_claude_code_worker.py`
- `runtime/host-orchestrator/tests/test_planner_adapter.py`

## Boundary

- 这次接通的是 bounded live heterogeneous review receipt path，不是 live `claude_glm` primary task execution
- 这次没有接 non-host_local runner；`remote_non_gui / vm_gui` 仍停留在 repo-side promotion / fail-closed handoff 边界
- 当前 live review sidecar 只基于 runtime status + bounded primary worker output summary 产出 receipt，不等于 full diff-aware review 或 `live accepted`
- 当前 live review receipt 仍以 `needs_review` 为 authoritative runtime status；它不自动升级为 approval、merge、`platform compatibility green`、或 `live accepted`

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest runtime\host-orchestrator\tests\test_claude_code_worker.py runtime\host-orchestrator\tests\test_planner_adapter.py runtime\host-orchestrator\tests\test_wave1_execution.py runtime\host-orchestrator\tests\test_worker_exec.py`：pass（36 passed）
- `uv run --project .\runtime\host-orchestrator python -` real probe：pass
  - shape: fake primary worker + real `claude_glm_review` reviewer + `HostLocalRunner` + medium-risk write task
  - result: `result.status = needs_review`
  - result: `review_result.json.reviewer_kind = claude_glm`
  - result: `review_result.json.review_mode = blocking`
  - result: `review_result.json.model = glm-5.2`
