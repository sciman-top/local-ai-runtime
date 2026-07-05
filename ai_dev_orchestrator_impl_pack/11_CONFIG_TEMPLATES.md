# 配置模板

## `.ai/config/orchestrator.yaml`
```yaml
run:
  artifacts_root: ".ai/runs"
  max_parallel_readers: 4
  max_parallel_writers: 2
  dry_run: false

policies:
  default_merge_policy: "draft_pr_only"
  sensitive_paths:
    - ".env"
    - ".env.*"
    - ".ssh/"
    - ".git/config"
    - "secrets/"
    - "credentials.*"

verification:
  default_commands:
    test: ""
    lint: ""
    typecheck: ""
    build: ""
```

## `.ai/config/workers.yaml`
```yaml
workers:
  gpt54_direct:
    adapter: "gpt54_api"
    model: "gpt-5.4"
    role: ["planner", "judge", "report_writer"]
    write_access: false

  codex_gpt54_main:
    adapter: "codex"
    profile: "gpt54_main"
    model: "gpt-5.4"
    role: ["implementer", "bug_fixer", "test_writer"]
    write_access: true

  codex_gpt54_review:
    adapter: "codex"
    profile: "gpt54_review"
    model: "gpt-5.4"
    role: ["final_reviewer"]
    write_access: false

  claude_code_glm52:
    adapter: "claude_code"
    backend_model: "glm-5.2"
    role: ["adversarial_reviewer", "alternative_planner"]
    write_access: false
```

## `~/.codex/config.toml` 示例
```toml
model = "gpt-5.4"
model_provider = "proxy"

[model_providers.proxy]
name = "Third-party GPT-5.4 API"
base_url = "https://YOUR_GATEWAY_BASE_URL/v1"
env_key = "GPT54_API_KEY"
wire_api = "responses"

[profiles.gpt54_main]
model = "gpt-5.4"
model_provider = "proxy"
sandbox_mode = "workspace-write"
approval_policy = "never"

[profiles.gpt54_review]
model = "gpt-5.4"
model_provider = "proxy"
sandbox_mode = "read-only"
approval_policy = "never"
```

## PowerShell 启动命令示例
```powershell
pwsh scripts/run-orchestrator.ps1 -Plan .ai/tasks/sample_tasks.json -Mode run
```
