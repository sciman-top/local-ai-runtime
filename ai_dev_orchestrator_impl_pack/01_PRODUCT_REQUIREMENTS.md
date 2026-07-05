# 产品需求文档（PRD）

## 产品名
**Local AI Dev Orchestrator**

## 产品目标
构建一套本地优先、可审计、可恢复、可并发的 AI 软件工程编排系统，用于让：
- `Direct GPT-5.4 API`
- `Codex + GPT-5.4`
- `Claude Code + GLM-5.2`

围绕一个 Git 仓库协作完成：
- 需求分析
- 方案设计
- 任务拆分
- 编码实现
- 测试与验证
- 代码审查
- PR 准备
- 清理收尾

## 产品定位
不是聊天机器人，也不是纯 IDE 插件，而是一个：
- **本地 AI 工程编排器**
- **多 worker 调度器**
- **Git/worktree 驱动的执行系统**
- **可审计的软件交付流水线**

## 核心用户
- 使用 Codex + GPT-5.4 作为主力编码 agent 的高级用户
- 偶尔使用 Claude Code + GLM-5.2 做第二意见与互评的用户
- 需要高并发、高可控、可回放、可恢复的本地工程工作流用户

## 核心需求
### 必须实现（P0）
1. 读取结构化任务计划（tasks.json / yaml）
2. 为每个任务创建独立 branch + git worktree
3. 调用 `codex exec` 处理具体任务
4. 跑 test / lint / typecheck / build
5. 保存 stdout / stderr / result.json / test.log
6. 生成 draft PR 所需材料
7. 提供清理 worktree 与分支的能力
8. 支持 dry-run
9. 具备失败重试与恢复基础

### 次优先级（P1）
1. 支持 `Claude Code + GLM-5.2` 对计划和 diff 互评
2. 支持 plan A / plan B 方案竞赛
3. 支持 `Direct GPT-5.4 API` 输出结构化评审 JSON
4. 支持风险分级
5. 支持报告生成

### 后续增强（P2）
1. SQLite 状态机
2. Web/TUI 仪表盘
3. 定时任务
4. 报告模板
5. 历史 run 检索
6. 自动归档

## 非目标
以下内容不是第一版目标：
- 自动 merge 到 main
- 自动删除远程分支且无人工确认
- 全自动 release
- 多编排器互套（如 Hermes + OMX + OpenHands 同时上）
- 云端多租户平台
- 远程多人协同 SaaS

## 功能模块
### 1. Intake
输入来源：
- 本地 markdown spec
- issue 文本
- 任务模板
- `Direct GPT-5.4 API` 生成的 `tasks.json`

### 2. Planner
- 把需求转成 `plan.md`
- 生成 `tasks.json`
- 标记依赖关系
- 标记风险等级
- 标记可并行任务

### 3. Worktree Manager
- 创建 worktree
- 绑定 branch
- 记录 worktree 路径
- 移除 worktree
- prune

### 4. Adapter Layer
- `codex` adapter
- `direct_gpt54` adapter
- `claude_code_glm52` adapter

### 5. Execution Engine
- 调用 worker
- 超时控制
- 日志采集
- 异常捕获
- 结果落盘

### 6. Verification
- test
- lint
- typecheck
- build
- 统一结果汇总

### 7. Review Layer
- GLM 反方评审
- GPT-5.4 裁决
- 生成 review.json / merge_report.md

### 8. Integration Prep
- 生成 PR 标题/正文建议
- 生成 merge 风险报告
- 生成 cleanup 计划

## 成功标准
### MVP 成功条件
- 能读取 2~3 个任务并顺序或有限并行执行
- 每个任务都能创建独立 worktree
- Codex 能在 worktree 中完成指定任务
- 执行日志完整落盘
- 所有失败可追溯
- 最终能输出 merge-ready 的本地工件

### 质量标准
- 默认不碰敏感路径
- 没有 silent failure
- 所有自动行为均可审计
- 没有无闸门改 main 的路径
