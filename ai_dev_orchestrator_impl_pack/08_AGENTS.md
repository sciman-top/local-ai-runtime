# AGENTS.md

## 角色
你正在实现一个本地 AI 软件工程编排器。请严格遵守以下目标与边界。

## 核心目标
实现一套本地优先、可审计、可恢复、可并发的工程编排系统，围绕以下三类能力：
1. `Direct GPT-5.4 API`
2. `Codex + GPT-5.4`
3. `Claude Code + GLM-5.2`

## 设计原则
1. Python 负责确定性调度
2. Git worktree 负责并发隔离
3. Codex + GPT-5.4 是主力实现者
4. Claude Code + GLM-5.2 是异质模型反方评审
5. 默认只到 draft PR / merge-ready，不自动 merge main
6. 所有执行、失败、修复、测试都必须落盘
7. 任何写操作都必须受 `allowed_paths` 约束

## 不允许做的事
- 不要一开始接入 OMX / OpenHands / OpenCode
- 不要实现无闸门 auto-merge
- 不要让多个写权限 worker 同时改同一个 worktree
- 不要读取或修改以下路径：
  - `.env`
  - `.env.*`
  - `.ssh/`
  - `.git/config`
  - `secrets/`
  - `credentials.*`
- 不要把调度逻辑写进 prompt 里而忽略 Python 代码实现
- 不要把所有逻辑堆在单文件里

## 必须优先实现
1. 配置加载
2. 任务契约解析
3. worktree 生命周期管理
4. Codex adapter
5. 验证命令执行
6. 日志与工件落盘
7. 报告生成基础能力

## 输出风格
- 代码应当清晰、模块化、可测试
- 使用 Python 3.12+
- 优先标准库；如需第三方依赖，最小化
- 每个模块都要有明确职责
- 所有副作用操作要显式封装
- 对 subprocess、git、路径操作添加防御性检查

## 测试
至少为以下内容编写测试：
- task loader
- path guard
- worktree manager
- codex adapter（可 mock）
- report generation

## 实施顺序
先做 Phase 1 MVP，再做 Phase 2；不要跳步骤。
