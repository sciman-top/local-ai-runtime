# Hermes v2 测试规格

## 1. Wave 0

- 前置：
  - 当前 known-good
- 测试：
  - `P0-2 read_only rootfs + tmpfs`
  - `P0-3` 网络探针
- 产物：
  - probe 文档
- 失败口径：
  - 阻塞项保留为正式记录

## 2. Wave 1

- 前置：
  - 文档已同步
- 测试链路：
  - `SDK path`
  - `codex exec fallback path`
- 三类任务：
  - `代码小修/重构`
  - `文档生成/整理`
  - `本地脚本执行 + 契约校验`
- 验收：
  - 连续 `20` 任务成功
  - 覆盖三类任务
  - `0` 重复认领
  - `0` 主树误写
  - `0` 契约破坏
  - `0` 人工回滚

## 3. Wave 2

- 测试：
  - 原子认领
  - lease 过期回收
  - worker 崩溃恢复
  - handoff 停点
  - 低/高风险写回分级

## 4. Wave 3

- 测试：
  - VM 任务包分发
  - VM 内本地执行
  - 结果回写
  - 主桌面不被占

## 5. Wave 4

- 测试：
  - lane 并行
  - network allowlist 探针
  - PAD 代价评估

## 6. Wave 5

- `5a`：
  - 多仓 smoke
  - `0` 跨仓误写
- `5b`：
  - 并发冲突
  - `0` 重复认领
- `5c`：
  - auto_continue 边界测试
- `5d`：
  - LangGraph/AutoGen 评估报告
