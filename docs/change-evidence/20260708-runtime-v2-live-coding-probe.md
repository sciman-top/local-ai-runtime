# 20260708 Runtime V2 Live Coding Probe

## Goal

在不切换默认入口的前提下，验证 `runtime_v2` experimental lane 能运行一条真实 `local_maint` / Codex SDK 本地写入任务，并让 regression eval 与 cutover drill 基于真实 completed attempt 变绿。

## Repo-Side Done

- `.ai/config/orchestrator.yaml` 已设为 `runtime.experimental_v2_enabled=true`
- `runtime.active_version` 仍保持 `v1`
- 新增受控 v2 task fixture：`runtime/host-orchestrator/fixtures/runtime-v2/tasks/T-20260708-000001-live-coding-probe.yaml`
- 真实 v2 run `runtime-v2-live-coding-probe-20260708-1` 已完成，status 为 `completed`，`next_action=none`
- worker 只写入允许文件：`runtime/host-orchestrator/fixtures/runtime-v2/live-coding-probe-output.md`
- `--eval-regression-fixtures-v2` 当前 `ok=true / fixture_count=1`
- `--cutover-drill-v2` 当前 `ready=true / cutover_performed=false`

## Still Open

- 默认入口仍未从 `v1` 切到 `v2`
- 没有执行 `--cutover-v2`
- 没有推进 `remote_non_gui` / `vm_gui` primary runner wiring
- 不声明 `live accepted`

## Verification

- `uv run --project .\runtime\host-orchestrator python -m pytest .\runtime\host-orchestrator\tests\test_runtime_v2.py -k "experimental_lane_is_enabled or live_coding_probe_fixture" -q`：先红后绿，最终 `2 passed`
- `uv run --project .\runtime\host-orchestrator python -m host_orchestrator --run-task-v2 .\runtime\host-orchestrator\fixtures\runtime-v2\tasks\T-20260708-000001-live-coding-probe.yaml --run-id runtime-v2-live-coding-probe-20260708-1`：`status=completed`
- v2 gate report：`108 passed`
- `uv run --project .\runtime\host-orchestrator python -m host_orchestrator --eval-regression-fixtures-v2`：`ok=true / fixture_count=1`
- `uv run --project .\runtime\host-orchestrator python -m host_orchestrator --cutover-drill-v2`：`ready=true / cutover_performed=false`

## Rollback

用 git 回滚本切片涉及的同批 diff：

- `.ai/config/orchestrator.yaml`
- `runtime/host-orchestrator/tests/test_runtime_v2.py`
- `runtime/host-orchestrator/fixtures/runtime-v2/tasks/T-20260708-000001-live-coding-probe.yaml`
- `runtime/host-orchestrator/fixtures/runtime-v2/live-coding-probe-output.md`
- `docs/architecture/planning-status.json`
- `docs/specs/config-and-worker-profiles.md`
- `docs/specs/runtime-v2-kernel.md`
- `docs/roadmap/orchestrator-roadmap.md`
- `docs/plans/orchestrator-implementation-plan.md`
- `docs/backlog/orchestrator-task-list.md`
- `docs/change-evidence/README.md`
- `docs/change-evidence/20260708-runtime-v2-live-coding-probe.md`
