# Windows 主力机 AI Agent 分层架构 v1.6

## 1. 目标与边界

本方案服务于一台 Windows 主力机，目标不是追求“一个全能单体 agent”，而是构建一个：

- 可审计
- 可回滚
- 边界清楚
- 适合长期维护

的分层架构。

v1 的目标固定为：

`Hermes 生成任务 -> Codex 执行 -> Hermes 吸收结果`

也就是人工触发的批量学习闭环。

v1 **不承诺**：

- 实时自进化
- 常驻后台学习
- Hermes 直接碰 Windows 桌面
- Hermes 直接远控 Codex 会话
- 消息入口平台化运营

## 2. 分层角色

### 执行层

- 主体：`Codex`
- 角色：唯一允许直接碰主力 Windows 桌面的 agent
- 默认执行顺序：`MCP/结构化工具 -> 终端 -> 浏览器 -> Computer Use`

### 学习/编排层

- 主体：`Hermes`
- 角色：隔离学习层
- 运行方式：`Docker Desktop + WSL2 backend + 按需 CLI 容器`
- 权限限制：不开放桌面控制、不开放 browser automation、不开放 gateway/chat、不开放 MCP、不开放社区 skills 自动安装

### 固定 GUI 补件

- 主体：`Power Automate Desktop`
- 触发条件：重复至少 3 次、步骤稳定、值得固化
- 限制：必须在独立会话中运行

### 渠道层

- 主体：`OpenClaw`
- 当前策略：v1 暂缓
- 触发条件：仅在 Telegram / Slack / WhatsApp 等消息入口成为刚需时再评估

## 3. AgentBridge 契约

`AgentBridge` 是 `Codex` 与 `Hermes` 之间唯一批准的交接面。

固定目录：

- `tasks/`
- `results/`
- `skills-drafts/`
- `memory-promotions/`
- `artifacts/`
- `logs/`
- `docs/`

硬规则：

- task 一旦进入执行，不允许原地改写
- 范围变化必须新建 task
- 重跑必须新建 task
- 一个 task 只允许一个正式 result
- Hermes 产出的 task 文本属于不可信输入
- Hermes 文本从来不是执行授权
- 高风险动作仍需 Codex 侧 approval

## 4. Hermes 容器运行基线

Hermes v1.6 的容器基线如下：

- 使用 Docker Compose 管理
- 只允许 digest-pinned 的官方镜像
- 只允许两类挂载：
  - `/opt/data` named volume
  - `/bridge` bind mount
- 显式禁止：
  - 整块 `C:`
  - 主代码仓
  - 浏览器 profile
  - 密码库
  - `~/.codex`
  - `~/.claude`
  - Docker socket
- 首次正式运行前必须完成 `/opt/data` 卷初始化
- 正式 Hermes 容器只允许非 root 业务服务执行

固定硬约束：

- `restart: "no"`
- `cpus: 2`
- `mem_limit: 2g`
- `pids_limit: 256`
- `security_opt: ["no-new-privileges:true"]`

## 5. Provider 与密钥策略

首次 bring-up 的 provider 基线：

- 第三方 `OpenAI-compatible` 端点
- 主模型：`gpt-5.5`
- 同 provider 降级模型：`gpt-5.4`
- `GLM-5.2` 仅作为后续 fallback 候选，不进入首次 bring-up

密钥策略：

- 必须使用独立 Hermes key
- key 只允许存在于当前临时 shell 会话
- 不写 profile
- 不写 repo 文件
- 不写文档
- 不写 `/opt/data`

标准 `.env` 格式见根目录 [.env.example](D:/CODE/hermes-agent/.env.example)。

## 6. 安全边界

### 已保证

- 文件挂载边界
- 无 Windows GUI 控制权
- 无共享凭证
- 无公开端口
- 无 Docker socket
- 非 root 业务服务执行
- 资源限制

### 未保证

- 默认严格网络出站白名单
- 宿主级完全隔离

### 诚实边界

- `task/result` 文件本身没有密码学签名
- 完整性主要依赖窄写入路径、人工审阅和 `artifacts sha256`
- Hermes 产出的 task 属于不可信输入，不能被当作直接授权

## 7. 失败协议

- `failed`：本轮失败，停止自动推进，等待人工处理
- `blocked`：缺权限、缺凭证、缺前提条件，等待人工处理
- `needs_review`：结果已产出，但不允许自动流入下游

v1 明确不做：

- 自动重试
- 自动回滚
- 自动 task 改写

## 8. known-good 快照

阶段 2 首次成功闭环后，必须保存 `known-good` 快照，至少包含：

- Hermes release tag
- Hermes image digest
- 派生镜像 Dockerfile hash（如果存在）
- Compose 文件 hash
- `/opt/data` volume 备份
- provider endpoint、model 组合与配置 hash

当前已复制到仓内的本机快照见：

- [snapshots/agentbridge-20260628/docs/known-good-20260628-131518-032.json](D:/CODE/hermes-agent/snapshots/agentbridge-20260628/docs/known-good-20260628-131518-032.json)

## 9. 当前本机结论

截至 `2026-06-28`，Windows 侧 v1.6 bring-up 已经实跑通过，当前维护重点已经从“能不能 bring-up”转到：

- 如何长期保存方案、脚本、快照与证据
- 如何把上游参考仓和本机维护仓隔离
- 如何在升级 Hermes / provider / 运行模式时继续保持单变量变更与可回滚
