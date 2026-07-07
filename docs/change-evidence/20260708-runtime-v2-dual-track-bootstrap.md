# 20260708 Runtime V2 Dual-Track Bootstrap

## Goal

把“同仓新内核 + 双轨迁移”的第一批真实落点收口到代码、配置、测试、文档与 verifier，同步明确 truth boundary：`runtime_v2` 已吸收，但默认入口未切换。

## Repo-Side Done

- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/` 已补齐 experimental runner、admission、storage、artifacts、migration、CLI 接线
- `.ai/config/orchestrator.yaml` 已增加 `runtime.active_version / experimental_v2_enabled / control_plane_db_v2 / artifact_root_v2`
- `.ai/config/policies.yaml` 已增加 `verification_profiles / continuation_policies / retry_policies`
- `runtime_v2` 测试已覆盖：
  - v2 config load
  - v2 canonical task reject legacy fields
  - 6 tables + `resume_point / retry_rewind`
  - dependency blocked
  - low-risk auto complete
  - medium-risk guarded pause
  - gate failure retryable
  - worker failure retryable
  - CLI run/resume/retry + cutover route switch
- authoritative docs / roadmap / implementation plan / backlog / specs / verifier 已开始承认 `Kernel V2`

## Still Open

- `runtime_v2` 仍是 experimental dual-track，不是默认入口
- `planning-status.current_active_queue` 仍保持 `PHASE-1-VERTICAL-SLICE`
- `WP4 / WP5 / WP6` 仍未完成
- 还没有用真实本地编码任务证明 v2 自动闭环达到稳定 cutover 条件

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_runtime_v2.py`
- `python -m compileall runtime/host-orchestrator/src/host_orchestrator`
- `python -m compileall runtime/host-orchestrator/tests`

## Naming Boundary

- 当前不改仓库名
- 当前不改远端 slug
- 当前不改本地目录名 `local-ai-dev-orchestrator`
- 当前终态重构通过同仓 `runtime_v2` 新内核完成，而不是 rename 完成
