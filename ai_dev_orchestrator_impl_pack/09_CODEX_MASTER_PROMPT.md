# 交给 Codex + GPT-5.4 的主实施提示词

> Status: non-authoritative operational prompt asset. Do not treat this file as runtime truth.

你现在要实现一个名为 **Local AI Dev Orchestrator** 的本地 AI 软件工程编排器。请按以下要求工作：

## 目标
构建一个 Python 主导、Git worktree 隔离、Codex 负责执行、GLM 负责异质评审的本地工程系统。

## 当前必须实现的范围（MVP）
1. 在现有 `runtime/host-orchestrator` 骨架上扩展，而不是新建平行顶层包
2. 实现配置加载
3. 实现 canonical `task.json` 解析、校验与派生字段盖章
4. 实现 git worktree 生命周期管理
5. 实现 `codex exec` / SDK adapter
6. 实现 `build -> [lint -> typecheck] -> test -> contract -> hotspot` 命令执行
7. 实现 `.ai/state/control-plane.db` 与 `.ai/runs/<run_id>/<task_id>/` 工件落盘
8. 生成 `result.json`、`verification_summary.json`、`cost_summary.json` 与 markdown projection
9. 不自动 merge

## 强约束
- 只允许使用本包文档中定义的目标架构和边界
- 以 Python 3.12+ 实现
- 必须模块化
- 必须写测试
- 不允许触碰敏感路径
- 默认 read-only；只有被授权的 task 才可写入
- 所有失败必须落盘
- 不要把未来功能混入 MVP

## 先做什么
请先：
1. 阅读全部资料；
2. 输出一个 `implementation_plan.md`；
3. 给出现有 `runtime/host-orchestrator` 的扩展落点与目标文件布局；
4. 再开始编码 Phase 1 MVP。

## 输出要求
- 先提交实施计划
- 再逐步实现模块
- 每完成一块，说明：
  - 实现了什么
  - 还缺什么
  - 下一步做什么
