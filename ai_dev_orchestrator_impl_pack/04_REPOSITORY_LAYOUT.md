# 推荐仓库目录结构

```text
project-root/
  AGENTS.md
  README.md

  .ai/
    config/
      orchestrator.yaml
      workers.yaml
      policies.yaml
    tasks/
      sample_tasks.json
    runs/
      .gitkeep
    templates/
      plan.template.md
      pr_body.template.md
      review_report.template.md

  orchestrator/
    __init__.py
    main.py
    cli.py
    models.py
    exceptions.py

    adapters/
      __init__.py
      base.py
      codex_adapter.py
      gpt54_api_adapter.py
      claude_glm_adapter.py

    gitops/
      __init__.py
      worktree.py
      branches.py
      diffing.py

    execution/
      __init__.py
      runner.py
      subprocesses.py
      timeouts.py
      retries.py

    verification/
      __init__.py
      commands.py
      parser.py
      summary.py

    storage/
      __init__.py
      filesystem.py
      jsonl_log.py
      sqlite_state.py   # 阶段 3 再完成

    reporting/
      __init__.py
      plan_writer.py
      pr_writer.py
      review_writer.py
      merge_writer.py

    policies/
      __init__.py
      path_guard.py
      risk.py
      permissions.py

  scripts/
    run-orchestrator.ps1
    bootstrap.ps1
    cleanup.ps1

  tests/
    test_task_loader.py
    test_worktree_manager.py
    test_codex_adapter.py
    test_path_guard.py
    test_report_generation.py
```

## 说明
- `orchestrator/`：Python 主体代码
- `.ai/config/`：配置
- `.ai/tasks/`：输入任务
- `.ai/runs/`：所有运行工件
- `scripts/`：Windows 入口与运维脚本
