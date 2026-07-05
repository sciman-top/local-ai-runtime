# AI Dev Orchestrator 实现包（交付给 Codex + GPT-5.4）

## 这是什么
这是一个**可直接交给 Codex + GPT-5.4 实施**的实现资料包。目标是落地一套本地 AI 软件工程编排系统：

- **Direct GPT-5.4 API**：规划、裁决、总结、结构化 JSON 输出
- **Codex + GPT-5.4**：主力编码、改代码、跑测试、修复问题
- **Claude Code + GLM-5.2**：异质模型反方评审、第二方案、辅助代码审查
- **Python Orchestrator**：确定性调度核心
- **PowerShell Launcher**：Windows 启动入口
- **Git worktree**：每任务独立工作区
- **GitHub CLI / Git**：分支、PR、清理

## 你要让 Codex 做什么
请让 Codex 先阅读本包中的以下文件，顺序如下：

1. `01_PRODUCT_REQUIREMENTS.md`
2. `02_TARGET_ARCHITECTURE.md`
3. `03_IMPLEMENTATION_ROADMAP.md`
4. `04_REPOSITORY_LAYOUT.md`
5. `05_TASK_CONTRACT_SCHEMA.json`
6. `06_STATE_MACHINE.md`
7. `07_AGENT_ROLE_MATRIX.md`
8. `08_AGENTS.md`
9. `09_CODEX_MASTER_PROMPT.md`
10. `10_GLM_REVIEW_PROMPT.md`
11. `11_CONFIG_TEMPLATES.md`
12. `12_ACCEPTANCE_CRITERIA.md`
13. `13_BOOTSTRAP_CHECKLIST.md`

## 建议实施顺序
### Phase 1 — MVP
先做最小闭环：
- 在现有 `runtime/host-orchestrator` 骨架上扩展 canonical `task.json` intake
- 创建 branch + worktree
- 调用 Codex 执行真实任务
- 运行 `build -> [lint -> typecheck] -> test -> contract -> hotspot`
- 记录 `.ai/state/control-plane.db` 与 `.ai/runs/<run_id>/<task_id>/` 工件
- 生成 `result.json` 与 markdown projection 的双写结果
- 不自动 merge

### Phase 2 — 双模型互评
- 接入 Claude Code + GLM-5.2
- 支持 plan 互评、diff 互评、第二方案竞赛
- 支持 GLM 输出 `review.json`

### Phase 3 — 产品化
- 状态机
- 扩展 SQLite 控制面与 per-run JSON evidence
- 重试 / 超时 / 恢复
- 报告生成
- worktree 清理
- PowerShell 启动器

## 重要边界
- 不要一开始上 OMX / OpenHands / OpenCode
- 不要做无闸门自动 merge
- 不要让多个写权限 worker 同时改同一个 worktree
- 不要读取或修改 `.env`、`.ssh/`、`secrets/`、`.git/config` 等敏感路径
- 默认以 **Codex + GPT-5.4** 为主力实现者
- **Claude Code + GLM-5.2** 默认是反方评审，不是最高权限 supervisor

## 建议让 Codex 的第一条任务
请先根据本实现包：
1. 识别现有 `runtime/host-orchestrator` 骨架中的可复用模块与新增落点；
2. 在该骨架上补齐 canonical `task.json` intake、`result.json` 输出与 markdown projection 双写；
3. 实现 `codex` adapter 与真实任务执行闭环；
4. 实现任务加载、worktree 创建、`.ai/state` / `.ai/runs` 落盘；
5. 提供一个本地 dry-run 与最小真实执行示例；
6. 不做自动 merge。
