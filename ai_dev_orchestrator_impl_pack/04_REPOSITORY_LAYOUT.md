# 当前仓库目录落点（2026-07-06 重基线后）

```text
local-ai-dev-orchestrator/
  AGENTS.md
  README.md

  docs/
    README.md
    architecture/
      planning-status.json
      orchestrator-target-architecture.md
    product/
      orchestrator-prd.md
    roadmap/
      orchestrator-roadmap.md
    plans/
      orchestrator-implementation-plan.md
    backlog/
      orchestrator-task-list.md
    specs/
      task-contract.md
      result-contract.md
      review-contract.md
      state-and-db.md
    migrations/
      hermes-compatibility-demotion.md
    platforms/
      hermes/

  runtime/
    host-orchestrator/
      pyproject.toml
      README.md
      src/
        host_orchestrator/
          __init__.py
          __main__.py
          cli.py
          paths.py
          db.py
          host_local.py
          worker.py
          exec_fallback.py
          agentbridge.py
          wave1_smoke.py
      tests/
        test_scaffold.py
        test_wave1_execution.py
      fixtures/
        wave1-smokes/
      scripts/
        README.md
        run-wave1-smokes.ps1
        test-wave1-acceptance.ps1

  ai_dev_orchestrator_impl_pack/
    00_README_FIRST.md
    01_PRODUCT_REQUIREMENTS.md
    ...
    14_HANDOFF_MESSAGE_TO_CODEX.md

  snapshots/
    agentbridge-20260628/

  references/
  scripts/
    verify-planning-status.py
    refresh-reference-repos.ps1

  private-local/
```

## 目录说明

- `docs/`：当前主线 authoritative docs。先看这里，再决定编码切片。
- `runtime/host-orchestrator/`：当前唯一受支持的 Python 实现骨架。后续实现一律在这里就地演进。
- `ai_dev_orchestrator_impl_pack/`：交给 AI 的补充说明包，不是新的代码根目录。
- `snapshots/agentbridge-20260628/`：Hermes/AgentBridge 兼容与历史基线。
- `private-local/`：本机运行态与 smoke 产物，不进入 git。

## 对 Codex 的硬约束

- 不新建平行顶层 `orchestrator/` 包。
- 不把 `tests/`、`scripts/`、`.ai/` 重新搬到另一个绿地结构。
- Phase 1 只在 `runtime/host-orchestrator/src/host_orchestrator/`、对应 `tests/`、以及必要的 repo-level docs/specs 上增量扩展。

## Phase 1 建议扩展落点

- 路径与工件：`runtime/host-orchestrator/src/host_orchestrator/paths.py`
- 控制面与状态：`runtime/host-orchestrator/src/host_orchestrator/db.py`
- canonical task intake：`runtime/host-orchestrator/src/host_orchestrator/host_local.py`
- Codex SDK / fallback worker：`runtime/host-orchestrator/src/host_orchestrator/worker.py`、`exec_fallback.py`
- AgentBridge 兼容投影：`runtime/host-orchestrator/src/host_orchestrator/agentbridge.py`
- 回归测试：`runtime/host-orchestrator/tests/`
- repo-side 验收脚本：`runtime/host-orchestrator/scripts/`

## 当前目标目录约定

- `.ai/state/control-plane.db`：调度真源
- `.ai/runs/<run_id>/<task_id>/`：正式 evidence 面
- `private-local/wave-smokes/`：repo-side deterministic smoke 验收产物
