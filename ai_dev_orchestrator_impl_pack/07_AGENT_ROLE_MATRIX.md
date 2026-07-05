# Agent 角色矩阵

## 总原则
- GPT-5.4 是主力实现者和主裁判
- GLM-5.2 是异质模型反方评审
- Python 是真正的调度与治理核心

## 角色定义

| 角色 | 入口 | 默认权限 | 职责 |
|---|---|---|---|
| `gpt54_direct_planner` | Direct GPT-5.4 API | 只读 | 计划生成、任务拆分、裁决、总结 |
| `codex_gpt54_main` | Codex + GPT-5.4 | 写 | 实现、修复、测试补充 |
| `codex_gpt54_review` | Codex + GPT-5.4 | 只读 | 最终代码级审查 |
| `claude_code_glm52` | Claude Code + GLM-5.2 | 只读 | 反方评审、第二方案、diff 审查 |
| `python_supervisor` | Python | 最高 | 调度、日志、验证、PR 准备、清理 |

## 信任等级
### L1
- `python_supervisor`
- CI / 测试结果
- 人工确认

### L2
- `codex_gpt54_review`
- `gpt54_direct_planner`

### L3
- `codex_gpt54_main`

### L4
- `claude_code_glm52`

## 默认规则
- `claude_code_glm52` 默认 read-only
- `codex_gpt54_main` 只能写 `allowed_paths`
- 只有 Python 可以触发清理
- 默认不启用 auto-merge
