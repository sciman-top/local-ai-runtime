# 主控 + 子代理 + worktree 协作模式

> Status: repo-owned operator guide. Use together with the current planning truth and gate surfaces; do not treat this file as a replacement for `README.md` or `docs/architecture/planning-status.json`.

## 目的

把日常 AI 编码中的 `主控 + 子代理 + worktree` 协作模式固化成一套可复用的协议，目标不是“多开几个模型”，而是同时做到：

- 主控统一真源
- 子代理隔离上下文
- worktree 隔离写入
- 门禁统一收口

## 适用场景

- 多模块、弱耦合、可按 `write_set` 清晰拆分的开发任务
- 需要 `explore -> implement -> review -> merge -> closeout` 闭环的任务
- 需要把代码、README、planning、backlog、change-evidence 一起收口的任务

## 不适用场景

- 需求本身还在摇摆，最小切片说不清
- 多个任务必须同时修改同一个热点文件或同一组共享夹具
- 主要验收依赖人工感知、外部系统或不稳定 live 环境

## 文件入口

### 操作说明

- 本文件：[docs/主控-子代理-worktree-协作模式.md](D:/CODE/local-ai-dev-orchestrator/docs/主控-子代理-worktree-协作模式.md)

### Prompt 资产

- [prompts/subagent-worktree/README.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/README.md)
- [prompts/subagent-worktree/master.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/master.prompt.md)
- [prompts/subagent-worktree/explorer.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/explorer.prompt.md)
- [prompts/subagent-worktree/worker.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/worker.prompt.md)
- [prompts/subagent-worktree/spec-reviewer.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/spec-reviewer.prompt.md)
- [prompts/subagent-worktree/quality-reviewer.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/quality-reviewer.prompt.md)

### 模板资产

- [templates/agent-work-manifest.example.yaml](D:/CODE/local-ai-dev-orchestrator/templates/agent-work-manifest.example.yaml)
- [templates/agent-work-manifest.schema.json](D:/CODE/local-ai-dev-orchestrator/templates/agent-work-manifest.schema.json)
- [templates/closeout-checklist.md](D:/CODE/local-ai-dev-orchestrator/templates/closeout-checklist.md)

## 日常使用步骤

1. 先刷新真源。
   - 先看当前仓库的 `README.md`、`docs/README.md`、`docs/architecture/planning-status.json`，再决定这轮是 explore、implement、review 还是 docs/evidence sync。
2. 填一份 manifest。
   - 复制 [templates/agent-work-manifest.example.yaml](D:/CODE/local-ai-dev-orchestrator/templates/agent-work-manifest.example.yaml)，替换 `objective`、`truth_sources`、`tasks`、`write_set`、`done_when`、`tests`。
3. 用主控 prompt 开场。
   - 以 [prompts/subagent-worktree/master.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/master.prompt.md) 为骨架，把 manifest 贴给主控 agent。
4. 先派 explorer，只读分析。
   - explorer 只回答最小切片、建议写入集合、建议测试、冲突点。
5. 再派 worker，独立 worktree 最小修改。
   - 每个写任务一个 worktree。
   - `write_set` 重叠的任务禁止并行。
6. 做两层复核。
   - 先用 [spec-reviewer.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/spec-reviewer.prompt.md)
   - 再用 [quality-reviewer.prompt.md](D:/CODE/local-ai-dev-orchestrator/prompts/subagent-worktree/quality-reviewer.prompt.md)
7. 主控串行并回与收口。
   - cherry-pick 或 merge
   - 全量 gates
   - README / planning / backlog / evidence 同步
   - 删除临时 worktree 与分支

## 强约束

- 所有子代理统一使用 `gpt-5.4 + xhigh`
- explorer 一律只读
- worker 只允许修改 manifest 分配给它的 `write_set`
- `write_set` 重叠任务默认串行
- reviewer 不改代码，只给结论
- 主控负责最终 truth sync，不把代码局部完成说成全局完成

## 并发判定

允许并发：

- 多个只读 explorer
- `write_set` 完全不重叠的多个 worker

默认串行：

- 共享 schema
- 共享基类
- 共享测试夹具
- 共享状态机/调度器
- 同一批 authoritative docs 真源更新

## 完成定义

只有同时满足下面几件事，才算这轮真正完成：

- 代码已经并回主线
- 相关测试与门禁通过
- 相关 README / planning / backlog / evidence 已同步
- worktree 与临时分支已清理
- 最终结论清楚区分：
  - `repo-side done`
  - `platform/live/manual still open`

## 快速清单

- 先查真源，再拆任务
- 先 explorer，再 worker
- 先 spec review，再 quality review
- 先代码并回，再更新 docs/evidence
- 最后清理 worktree，恢复 trunk-only
