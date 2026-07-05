# Hermes v2 实施规格

## 1. 目标

这份文档定义：

- 项目结构
- 模块边界
- 进程边界
- 配置位置
- 状态持久化位置
- 日志与证据输出位置

## 2. 目录结构

建议在本仓内新增以下目录：

```text
runtime/
  host-orchestrator/
    src/
    tests/
    scripts/
  remote-runner/
    src/
    tests/
  vm-runner/
    src/
    tests/
docs/
  Hermes-v2-*.md
private-local/
  control-plane/
  wave-smokes/
```

## 3. 模块边界

### host-orchestrator

- 负责：
  - 读取 `AgentBridge/tasks`
  - 原子认领
  - lease
  - 路由
  - 执行 host_local lane
  - 分发 remote_non_gui / vm_gui 任务包
  - 回写最终 result
- 不负责：
  - 直接 GUI 控制
  - 直接改动 live `AgentBridge` 契约

### remote-runner

- 运行在目标主机本地
- 负责：
  - 接收来自 host 的任务包
  - 本地调用 `Codex SDK / codex exec fallback`
  - 回写结果包

### vm-runner

- 运行在 Windows VM 内
- 负责：
  - 读取 host 分发任务包
  - VM 内本地调用 `Codex SDK / Computer Use`
  - 回写结果到 `AgentBridge`

## 4. 持久化与路径

- `control-plane.db`：
  - 默认放在 `private-local/control-plane/control-plane.db`
- Host Orchestrator 日志：
  - `private-local/control-plane/logs/`
- Smoke 产物：
  - `private-local/wave-smokes/`
- 正式任务/结果证据：
  - 继续只进 `AgentBridge`

## 5. 配置边界

- `CODEX_HOME`：
  - 主机 worker 独立
  - VM worker 独立
  - 不共享
- Git 身份：
  - 主机 / VM / remote runner 各自可独立配置
- 凭证：
  - 不共享
  - 不写仓库

## 6. 进程边界

- 常驻的只有：
  - `Host Orchestrator`
- 按需启动的有：
  - `Hermes` 学习容器
  - `remote-runner` 任务进程
  - `vm-runner` 任务进程

## 7. 网络边界

- 默认：
  - 主机 `network=off`
- 三层独立治理：
  - `Codex sandbox network_proxy`
  - `Hermes P0-3`
  - `VM worker 网络治理`

## 8. 不做

- 不新增第二证据总线
- 不把 `app-server` 当正式远程协议
- 不在 `Wave 1` 引入 `FastAPI` 公网接口
