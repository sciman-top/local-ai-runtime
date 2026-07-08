# 20260708 Runtime V2 K2-T05 Regression Fixture Seed

## Goal

为 `runtime_v2` 增加第一批可机器回放的 attempt-level regression fixture，使后续 eval / regression suite 能稳定比较 v2 attempt 的状态、gate、policy 与 artifact refs。

## Repo-Side Done

- `V2Artifacts` 增加 `regression_fixture.json`
- low-risk auto completed attempt 会写出 `regression_fixture.json`
- pre-worker policy-guard blocked attempt 会写出 `regression_fixture.json`
- `result.json` 会写出 `regression_fixture_ref`
- v2 `artifacts` 表会记录 `kind = regression_fixture`
- fixture 当前包含 status、next_action、worker / verification / continuation profile、execution_profile、risk / network / gui / write flags、dependency refs、review flag、policy guard reasons、gate status、gate names、changed paths、以及核心 artifact refs

## Still Open

- 后续 `20260708-runtime-v2-k2-t05-regression-fixture-state-coverage.md` 已继续扩展 failure / retry / admission / dependency-blocked 等路径的 regression fixture 覆盖
- `K2-T05` 仍未整体完成；独立 eval corpus runner / summary 仍待继续
- 尚未新增独立 eval 汇总入口或 regression corpus runner
- `runtime_v2` 仍是 experimental dual-track，默认入口仍未从 v1 切换
- `planning-status.current_active_queue` 仍保持 `PHASE-1-VERTICAL-SLICE`
- 本次没有推进 `remote_non_gui` / `vm_gui` runner wiring，也不声明 `live accepted`

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_runtime_v2.py -k regression_fixture -q`
- `uv run --project .\runtime\host-orchestrator python -m pytest runtime/host-orchestrator/tests/test_runtime_v2.py -q`
- `uv run --project .\runtime\host-orchestrator python -m pytest`
- `python .\scripts\verify-planning-status.py`
- `python .\scripts\select-next-work.py`
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`
- `git diff --check`

## Rollback

用 git 回滚本切片涉及的同批 diff：

- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/artifacts.py`
- `runtime/host-orchestrator/src/host_orchestrator/runtime_v2/runner.py`
- `runtime/host-orchestrator/tests/test_runtime_v2.py`
- `docs/specs/runtime-v2-kernel.md`
- `docs/roadmap/orchestrator-roadmap.md`
- `docs/plans/orchestrator-implementation-plan.md`
- `docs/backlog/orchestrator-task-list.md`
- `docs/change-evidence/README.md`
- `docs/change-evidence/20260708-runtime-v2-k2-t05-regression-fixture-seed.md`
