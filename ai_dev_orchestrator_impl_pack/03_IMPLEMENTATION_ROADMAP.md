# 实施路线图

> Status: superseded by roadmap/plan/task-list/planning-status. Keep only as historical greenfield roadmap.

## 阶段 1：MVP（必须先完成）
### 目标
在单仓库中跑通 1~3 个结构化任务的最小闭环。

### 范围
1. 目录初始化
2. 读取 `tasks.json`
3. 创建 git worktree
4. 执行 `codex exec`
5. 跑 test/lint/typecheck
6. 保存日志
7. 汇总结果
8. 生成 draft PR 文案
9. 清理 worktree（手动确认后）

### 不做
- 自动 merge
- GLM 审查
- SQLite
- Dashboard
- 自定义 UI

## 阶段 2：互评与异质模型审查
### 目标
让 `Claude Code + GLM-5.2` 参与：
- 计划互评
- diff 审查
- 第二方案生成

### 范围
1. 实现 `claude_glm_adapter.py`
2. 输出 `glm_review.json`
3. 实现 GPT-5.4 对 GLM 意见的裁决流程
4. 生成 `review_report.md`

## 阶段 3：产品化稳态
### 范围
1. SQLite 状态表
2. 租约 / 重试 / 续租机制
3. 历史 run 检索
4. 完整报告系统
5. 清理策略
6. CLI 交互优化

## 阶段 4：增强能力
### 可选
1. Hermes 作为入口和记忆层
2. Dashboard / TUI
3. GitHub PR 直接创建
4. 分层任务 DAG

## 优先级排序
1. `codex` adapter
2. task loader
3. worktree manager
4. verification runners
5. log + artifact persistence
6. report generation
7. `claude_glm` adapter
8. state machine
9. dashboard
