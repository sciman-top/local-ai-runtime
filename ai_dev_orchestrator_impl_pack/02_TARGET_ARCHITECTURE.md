# 目标架构

## 总体架构

```text
PowerShell Launcher
  ↓
Python Orchestrator
  ├─ Direct GPT-5.4 API
  │    ├─ 计划生成
  │    ├─ 任务拆分
  │    ├─ 风险评级
  │    ├─ A/B 方案比较
  │    └─ 总结报告
  │
  ├─ Codex + GPT-5.4
  │    ├─ 主力实现
  │    ├─ 测试补充
  │    ├─ bug 修复
  │    └─ 最终代码级 reviewer
  │
  └─ Claude Code + GLM-5.2
       ├─ 反方方案
       ├─ diff 审查
       ├─ 计划互评
       └─ 辅助代码审查
```

## 设计原则
1. **确定性调度**：Python 负责调度，不把调度逻辑交给 LLM
2. **写操作隔离**：所有写权限任务必须在独立 worktree 内执行
3. **读多写少**：大多数并行任务应为只读分析；写权限 worker 数量受控
4. **默认安全**：默认 read-only，逐级提升权限
5. **日志优先**：所有执行、失败、修复、测试都要落盘
6. **无隐式合并**：默认只到 draft PR / merge-ready，不自动进 main
7. **异质模型互评**：GLM 用于发现 GPT 的盲点；GPT 用于裁决 GLM 反馈

## 为什么这样分层
### Direct GPT-5.4 API
适合：
- 生成 `plan.md`
- 生成 `tasks.json`
- 比较 A/B 方案
- 生成 risk report
- 对 review 结果进行裁决
- 输出严格 JSON

不适合：
- 直接改本地仓库文件
- 直接做 git 操作

### Codex + GPT-5.4
适合：
- 读代码
- 改代码
- 跑测试
- 修复 bug
- 基于仓库上下文做实现

### Claude Code + GLM-5.2
适合：
- 从不同模型视角审查 GPT 方案
- 提供第二实现方案
- 分析 diff 风险
- 找遗漏测试
- 输出“反方意见”

## 数据流
1. 用户 / Hermes / 本地文档提供需求
2. Python 调用 Direct GPT-5.4 生成 `plan.md` 与 `tasks.json`
3. Python 创建 task 对应 branch + worktree
4. Python 启动 Codex worker 执行编码任务
5. Python 运行验证命令
6. Python 生成 diff 工件
7. Python 调用 Claude Code + GLM-5.2 做计划/差异审查
8. Python 调用 Direct GPT-5.4 对 GLM 反馈进行裁决
9. 产出 review report / PR body / cleanup plan

## 核心组件
### A. Launcher
- PowerShell 7
- 负责：
  - 环境检查
  - 入口命令
  - 调用 Python orchestrator
  - 传参

### B. Orchestrator Core
- Python 3.12+
- 负责：
  - 任务解析
  - worktree 管理
  - adapter 调用
  - 状态跟踪
  - 日志落盘
  - 报告生成

### C. Adapter Layer
- `codex_adapter.py`
- `gpt54_api_adapter.py`
- `claude_glm_adapter.py`

### D. Storage
- 第一版：JSON + JSONL + 文件系统
- 后续：SQLite

### E. Verification Layer
- test / lint / typecheck / build runners

### F. Policy Layer
- 允许路径
- 禁止路径
- 权限级别
- merge policy

## 权限模型
- `read_only`
- `workspace_write`
- `test_runner`
- `pr_prepare`
- `merge_manager`（默认不启用）

## 并发策略
- read-only worker：可 4~8
- write worker：默认 1~2
- reviewer：1~2
- merge：永远单线程

## 最终产物
- `.ai/runs/<run_id>/plan.md`
- `.ai/runs/<run_id>/tasks.json`
- `.ai/runs/<run_id>/task-*/stdout.log`
- `.ai/runs/<run_id>/task-*/stderr.log`
- `.ai/runs/<run_id>/task-*/result.json`
- `.ai/runs/<run_id>/review/review.json`
- `.ai/runs/<run_id>/reports/merge_report.md`
- `.ai/runs/<run_id>/reports/pr_body.md`
