# Hermes v2 路线图

## 1. 目标

这份文档只承载：

- `Wave 0 ~ 5d` 顺序
- 并行关系
- 每波前置
- 每波产物
- 每波回滚

不定义接口字段，不定义状态机，不定义 runner 协议。

## 2. 波次总表

### Wave 0：Phase 0 收口

- 前置：当前即可开始
- 目标：
  - `P0-2 read_only rootfs + tmpfs`
  - `P0-1 cap_drop:[ALL]` 阻塞记录
  - `P0-3 Hermes 学习层网络探针`
- 产物：
  - probe 文档
  - 更新后的计划/清单/摘要
- 回滚：
  - compose 备份
  - known-good snapshot

### Wave 1：纯本地 SDK MVP

- 前置：
  - 开发/smoke 可与 `Wave 0` 并行
  - 正式 accepted 需 `Phase 0` 全绿
- 目标：
  - `single worker`
  - `single repo`
  - `pure local tasks`
  - `SDK first`
  - `codex exec fallback`
- 产物：
  - host-orchestrator 骨架
  - 最小 worker
  - smoke 样本
  - Wave 1 验收脚本
- 回滚：
  - `git tag`
  - 删除 `control-plane.db`

### Wave 2：编排 + 学习闭环

- 前置：
  - `Wave 1` accepted
  - `Phase 0` 全绿
- 目标：
  - watcher
  - lease
  - route
  - heartbeat 唤醒
  - Hermes 按需学习
- 产物：
  - `control-plane.db`
  - memory/skills 候选
  - 蒸馏报告
- 回滚：
  - 禁用 heartbeat
  - 切回 Wave 1

### Wave 3：Windows VM GUI lane

- 前置：
  - `Wave 2`
- 目标：
  - `vm-runner`
  - GUI 任务包分发
  - GUI 结果回写
- 产物：
  - VM 基线
  - GUI smoke
  - 主桌面不被占证据
- 回滚：
  - 保留本地非 GUI 路径

### Wave 4：多 lane + 网络 + PAD 评估

- 前置：
  - `Wave 3`
- 目标：
  - host/VM 并行
  - allowlist 网络 lane
  - PAD 代价评估
- 产物：
  - lane 测试套件
  - network 探针报告
  - PAD 评估报告
- 回滚：
  - 单 lane
  - `network off`

### Wave 5a：multi-repo

- 前置：
  - `Wave 4`
- 目标：
  - 多仓
- 产物：
  - 多仓 smoke
- 回滚：
  - 单仓配置

### Wave 5b：multi-worker

- 前置：
  - `Wave 5a`
- 目标：
  - 多 worker 并发
- 产物：
  - 并发冲突测试
- 回滚：
  - 单 worker

### Wave 5c：auto_continue

- 前置：
  - `Wave 5b`
- 目标：
  - 线性自动继续
- 产物：
  - 边界测试
- 回滚：
  - 禁用 auto_continue

### Wave 5d：增强候选

- 前置：
  - `Wave 5c` 稳定后
- 目标：
  - `LangGraph / AutoGen` 评估
- 产物：
  - 评估报告
- 回滚：
  - 不引入
