# Hermes v2 runner 协议

## 1. 目标

定义三条 lane 的任务包与结果回写格式：

- `host_local`
- `remote_non_gui`
- `vm_gui`

## 2. host_local

- 输入：
  - `AgentBridge/tasks/*.md`
- 执行：
  - host-orchestrator 本地调用 `Codex SDK`
  - 失败时退到 `codex exec`
- 输出：
  - `AgentBridge/results/*.md`
  - 必要 `artifacts/`

## 3. remote_non_gui

- 任务包：
  - 从 `AgentBridge/tasks` 复制/投影到目标主机 runner 可见位置
- 执行：
  - 目标主机本地 `remote-runner`
  - 通过 `SSH` 触发/回传
- 输出：
  - 最终正式 result 仍回写 `AgentBridge/results`

## 4. vm_gui

- 任务包：
  - 由 host-orchestrator 写入共享 `AgentBridge/tasks`
  - 或共享映射目录中的 GUI 任务包
- 执行：
  - VM 内本地 `vm-runner`
  - 本地调用 `Codex SDK / Computer Use`
- 输出：
  - 正式 result 回写 `AgentBridge/results`
  - GUI 证据进入 `artifacts/`

## 5. 文件命名

- task：
  - 继续沿用现有 `T-YYYYMMDD-HHMMSS-slug.md`
- result：
  - 与 task 一一对应
- artifacts：
  - `task_id` 前缀

## 6. 协议约束

- 不新增第二证据总线
- 不引入第二控制协议
- 不直接暴露 `app-server` 远程接口
- VM runner 只做“本地执行 + 回写”
