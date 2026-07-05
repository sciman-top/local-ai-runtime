# AgentBridge 迁移与复用 Runbook

更新时间：`2026-06-28`

## 1. 这份 runbook 解决什么问题

这份文档解决的是：

- 以后如果要把 `AgentBridge` 从一个 live 路径迁到另一个 live 路径，怎么做
- 以后如果要在另一台机器上复用当前这套 `Codex + Hermes + AgentBridge` 主链，怎么做
- 以后如果要把这套能力交付给别人复用，应该交什么，不该交什么

这份文档不解决：

- Hermes upstream 自身版本升级策略
- `Phase 0 / P0-2` 当前运行模型阻塞的技术修复
- `Phase 1` watcher / lease / VM / network allowlist / PAD 的实现

## 2. 先记住三层边界

以后所有“转移 / 复用”都必须按三层边界理解，不要把三层混成一个目录。

### 2.1 维护仓

- `D:\CODE\local-ai-dev-orchestrator`

职责：

- 保存长期真源
- 保存实施计划、任务清单、交接材料
- 保存已验收快照
- 保存 repo-side 脚本与测试

它是：

- `可 clone`
- `可提交`
- `可长期追溯`

它不是：

- 当前 live 运行面
- 当前 `/opt/data` 现场
- 当前真实 provider 会话

### 2.2 live 运行面

- 当前默认：`C:\Users\sciman\Documents\AgentBridge`

职责：

- 当前 Windows 侧实际运行入口
- 实际执行 `contract / gates / start / boundary / snapshot`
- 持有当前 live 目录结构

它是：

- `可复制`
- `可重建`
- `可现场验证`

它不是：

- git 维护仓
- 真实 secrets 的持久归档位置

### 2.3 私有运行态

包含：

- 真实 `.env`
- provider key 会话
- `/opt/data` volume
- volume 备份
- 任何运行态认证与会话数据

它是：

- `本机私有`
- `允许单独备份`

它不是：

- 可直接进 git 的资产
- 可默认发给别人的交付物

## 3. 什么东西可以直接复用，什么不可以

### 3.1 可以直接复用

- 维护仓本身
- `snapshots/agentbridge-20260628/` 快照树
- 文档、脚本、测试
- 已提交的 known-good / boundary / implementation-status 元数据

### 3.2 可以复制，但复制后必须重验

- `snapshots/agentbridge-20260628/` 投影成新的 live `AgentBridge` 目录
- 旧机器上的 live 目录结构

复制后必须重验：

- `test-agentbridge-contract.ps1`
- `test-hermes-bringup-gates.ps1`
- `invoke-hermes-bringup-once.ps1`
- `verify-hermes-boundary.ps1`
- `new-known-good-snapshot.ps1`

### 3.3 不能直接当作已复用完成

- 真实 `.env`
- 当前 shell 里的 provider key
- live `/opt/data` volume
- volume 备份本体
- 任意旧机器上的 live 成功结果

这些只能：

- 单独导入
- 单独恢复
- 单独校验

不能因为“目录复制过去了”就当成迁移完成。

## 4. 标准复用顺序

所有场景默认都按下面顺序：

1. 先拿维护仓真源
2. 再从快照恢复 live 树
3. 再决定是否恢复私有 volume
4. 再注入 provider 会话
5. 再跑 `contract -> gates -> start -> boundary -> snapshot`
6. 只有新环境真的跑通后，才算迁移 / 复用完成

## 5. 场景 A：同一台机器上更换 live 路径

例子：

- 从 `C:\Users\sciman\Documents\AgentBridge`
- 迁到 `D:\RUNTIME\AgentBridge`

### 5.1 适用前提

- 仍是同一台 Windows 主机
- Docker / WSL / provider 侧环境不变
- 目标只是换 live 目录位置

### 5.2 推荐做法

1. 先保留旧 live 路径，不要覆盖删除
2. 在新位置创建空目录，例如 `D:\RUNTIME\AgentBridge`
3. 用快照同步脚本把仓内已验收快照投影到新 live 路径
4. 在新路径重新跑全部关键验证
5. 新路径验证通过后，再决定是否停用旧路径

### 5.3 建议命令

从维护仓快照同步到新 live 路径：

```powershell
& 'D:\CODE\local-ai-dev-orchestrator\snapshots\agentbridge-20260628\scripts\sync-agentbridge-to-documents.ps1' `
  -SourceRoot 'D:\CODE\local-ai-dev-orchestrator\snapshots\agentbridge-20260628' `
  -DestinationRoot 'D:\RUNTIME\AgentBridge'
```

如果确认目标目录里不需要保留额外文件，再加：

```powershell
-PruneExtraneous
```

### 5.4 同步后必须做的验证

在新 live 目录中执行：

```powershell
Set-Location 'D:\RUNTIME\AgentBridge'
.\scripts\test-agentbridge-contract.ps1
.\scripts\test-hermes-bringup-gates.ps1
```

如果本轮确实要验证 Hermes 可运行，再继续：

```powershell
.\scripts\invoke-hermes-bringup-once.ps1 -EnvFilePath '<你的真实 env 路径>'
```

### 5.5 何时算迁移完成

必须同时满足：

- 新目录 `contract` 通过
- 新目录 `gates` 通过
- 新目录 `bring-up` 通过
- 新目录 `boundary` 通过
- 新目录生成新的 `known-good snapshot`

只做到“文件复制完成”，不算迁移完成。

## 6. 场景 B：迁到另一台机器

### 6.1 适用前提

- 新机器不是当前这台 Windows 主机
- Docker / WSL / 文件路径 / provider 环境都可能不同

### 6.2 正确理解

跨机迁移本质上不是“搬 live 成品”，而是：

- 用维护仓恢复结构
- 用快照恢复安全基线
- 用新机器重建运行态

### 6.3 推荐步骤

1. 在新机器 clone 维护仓
2. 恢复 `snapshots/agentbridge-20260628/` 到新机器的 live 目录
3. 安装并验证 Docker Desktop / WSL
4. 恢复或重建 provider `.env` 路径
5. 决定是否恢复旧 `/opt/data` volume
6. 重跑 `contract -> gates -> start -> boundary -> snapshot`

### 6.4 需要单独决策的点

#### A. 不恢复旧 volume

优点：

- 更干净
- 风险更低
- 不会把旧机器运行态直接带过去

代价：

- Hermes 的学习态 / profile 状态相当于重新初始化

#### B. 恢复旧 volume

优点：

- 保留旧运行态

代价：

- 会带入旧认证与状态文件风险
- 必须额外做文件与 hash 校验

默认建议：

- **AI 推荐：先不恢复旧 volume，先在新机器完成 fresh bring-up**

理由：

- 这样最容易区分“结构恢复问题”与“运行态污染问题”。

### 6.5 新机器完成标准

必须重新生成：

- 新机器上的 boundary 证据
- 新机器上的 known-good snapshot

不能直接拿旧机器的 `known-good-20260628-131518-032.json` 当作新机器验收。

## 7. 场景 C：交付给别人复用

### 7.1 应交付什么

推荐交付包：

- 维护仓
- `snapshots/agentbridge-20260628/`
- 操作文档
- 接手检查单
- 当前状态说明

最关键入口：

- [README.md](D:/CODE/local-ai-dev-orchestrator/README.md)
- [接手检查单.md](D:/CODE/local-ai-dev-orchestrator/docs/接手检查单.md)
- [实施计划.md](D:/CODE/local-ai-dev-orchestrator/docs/实施计划.md)
- [当前交接摘要.md](D:/CODE/local-ai-dev-orchestrator/docs/当前交接摘要.md)
- [中文操作说明.md](D:/CODE/local-ai-dev-orchestrator/snapshots/agentbridge-20260628/docs/中文操作说明.md)
- [hermes-docker.md](D:/CODE/local-ai-dev-orchestrator/snapshots/agentbridge-20260628/docs/hermes-docker.md)

### 7.2 不应交付什么

- 真实 `.env`
- 当前 shell 会话 key
- `/opt/data` 现场 volume
- 私有 volume 备份本体
- 任何默认可直接执行高风险操作的 secret

### 7.3 正确交付口径

应明确说明：

- 这是“可恢复的维护仓 + 快照 + runbook”
- 不是“拿来即用的现场成品”
- 接收方必须自行注入 secrets，并在自己的机器上重验

## 8. volume 备份怎么处理

当前索引说明见：

- [docs/volume-backups/README.md](D:/CODE/local-ai-dev-orchestrator/snapshots/agentbridge-20260628/docs/volume-backups/README.md)

原则：

- 仓里只保留索引和校验值
- 不把 `.tgz` 本体提交进 git

如果以后要跨机恢复 volume：

1. 先记录当前要恢复的是哪一个备份
2. 先核对 `bytes` 与 `sha256`
3. 恢复后重新跑 bring-up / boundary
4. 恢复成功后生成新机器自己的 snapshot

## 9. 什么时候应该只复用快照，不动 live

下面这些场景，建议只在维护仓或隔离副本里做，不要直接改 live：

- 文档同步
- repo-side 脚本升级
- 单变量运行探针
- `P0-2` 这类隔离 rootfs / tmpfs 实验
- 只读核查

这也是当前 `Wave 0 / P0-2` 的做法。

## 10. 什么时候才应该改 live

只有在下面条件都满足时，才建议把变更真正投影到 live：

- repo-side 脚本已稳定
- 对应测试已通过
- 变更边界清楚
- 已说明回滚点
- 本轮目标本来就是 live-side 变更，而不是单纯探针

## 11. 建议的长期收口

以后如果经常要迁移 / 复用，建议进一步收口成：

1. `维护仓`
   - `D:\CODE\local-ai-dev-orchestrator`
2. `标准快照树`
   - `snapshots/agentbridge-<accepted-date>/`
3. `可切换的 live 根`
   - 不把 `Documents\AgentBridge` 当唯一不可变路径
   - 只把它当“当前默认 live 根”

也就是说，未来真正应该稳定的是：

- 结构
- 脚本
- 验证顺序
- 证据口径

而不是某个固定磁盘路径本身。

## 12. 最短迁移检查单

如果以后要做迁移 / 复用，至少先确认下面这些：

- 当前维护仓工作树干净
- 当前快照锚点清楚
- 当前 boundary 锚点清楚
- 不把真实 `.env` 带进 git
- 不把 private-local volume 备份误提交
- 新环境重跑 `contract -> gates -> start -> boundary -> snapshot`
- 明确这次是 `repo-side done` 还是 `live-side accepted`

## 13. 当前默认建议

如果以后再发生“要转移 / 复用”，默认建议是：

- **AI 推荐：先复制维护仓，再从快照恢复 live 树，再在目标环境重新生成 live 证据**

理由：

- 这样最不容易把旧机器运行态误当成新环境已验收状态。
