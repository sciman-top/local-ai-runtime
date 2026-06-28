# Phase 0 Read-only Rootfs Probe 2026-06-28

更新时间：`2026-06-28`

## 结论

当前 `Wave 0 / P0-2` 已从“文档计划”推进到“repo-side 真实隔离探针”，但 **尚未 accepted**。

本轮 fresh evidence 结论是：

- `read_only rootfs` 不是天然不可行
- `tmpfs /run` 不能用默认挂载；最小必要条件是 `--tmpfs /run:exec`
- 当前 accepted 运行模型 `official_root_bootstrap + runtime remap 10001:10001` 与 `read_only rootfs` 组合仍稳定阻塞
- 因此 `P0-2` 当前真实状态应写成：`repo-side probe done, runtime blocker confirmed, not live-side accepted`

## 本轮 scope

只在维护仓 `D:\CODE\hermes-agent` 内做 repo-side 工作：

- 补 `read_only rootfs + tmpfs` 探针入口
- 补行为级回归测试，守住既有 `start-hermes.ps1` / `invoke-hermes-bringup-once.ps1` 参数兼容性
- 修复 `manage-hermes-provider-session.ps1` 在 strict-mode 下的单对象 `.Count` 崩溃
- 用隔离复制树 + 独立 volume 跑真实 Docker probe

本轮 **没有** 改：

- `C:\Users\sciman\Documents\AgentBridge`
- live `.env`
- live `/opt/data` volume
- Hermes 常驻运行方式

## 关键脚本变更

本轮 repo-side 新增/修改的最小闭环如下：

- `start-hermes.ps1`
  - 增加 `CmdletBinding(PositionalBinding = $false)`
  - 支持 `-ReadOnlyRootfs`
  - 支持 `-TmpfsMounts`
  - 修复未显式传 `-TmpfsMounts` 时把 Hermes 位置参数误吞成 tmpfs 的回归
- `invoke-hermes-bringup-once.ps1`
  - 支持 `-ReadOnlyRootfs`
  - 支持 `-TmpfsMounts`
  - 仅在 `TmpfsMounts` 非空时转发该参数
  - 修复 strict-mode 下单对象 slot 定义访问 `.Count` 的兼容问题
- `verify-hermes-boundary.ps1`
  - 支持 `-ReadOnlyRootfs`
  - 支持 `-TmpfsMounts`
- `invoke-phase0-readonly-probe.ps1`
  - 新增 `P0-2` 隔离 probe 入口
  - 默认 tmpfs 组合为 `'/run:exec'` 与 `'/tmp'`
  - 改为 splat 调用 bring-up，避免 tmpfs 数组在脚本层被字符串化
- 新增测试
  - `test-hermes-arg-forwarding.ps1`
  - `test-phase0-readonly-probe.ps1`
  - `test-phase0-readonly-probe-env-resolution.ps1`
  - `test-hermes-provider-session-env-load.ps1`

## Fresh evidence

### 1. `/run` 必须 `exec`

最初探针已证明，`docker --tmpfs /run` 默认会带 `noexec`，会直接打断 Hermes 镜像的 `s6-overlay` 启动。

因此当前最小必要 tmpfs 组合不是：

- `/run`
- `/tmp`

而是：

- `/run:exec`
- `/tmp`

本轮 fresh probe 也再次证实，带 `--tmpfs /run:exec --tmpfs /tmp` 时，容器已能越过最早的 `/run` 执行权限阻塞，进入后续 bootstrap / profile reconcile 阶段。

### 2. 当前真正阻塞点是 `10001:10001 remap + read_only rootfs`

本轮 fresh 隔离 probe 报告文件：

- [phase0-readonly-rootfs-probe.json](D:/CODE/hermes-agent/private-local/phase0-probes/phase0-readonly-rootfs-20260628-202120-338/phase0-readonly-rootfs-probe.json)

当前 accepted runtime profile：

- [hermes-runtime.json](D:/CODE/hermes-agent/snapshots/agentbridge-20260628/docs/hermes-runtime.json)

其中关键运行模型仍是：

- `bootstrap_model = official_root_bootstrap`
- `volume_uid = 10001`
- `volume_gid = 10001`

在此模型下，本轮 fresh probe 的真实错误链路是：

1. `01-hermes-setup`
   - `[stage2] Changing hermes UID to 10001`
   - `usermod: cannot lock /etc/passwd; try again later.`
2. `02-reconcile-profiles`
   - `PermissionError: [Errno 13] Permission denied: '/opt/data/gateway_state.json'`
3. 主 CLI 入口
   - `PermissionError: [Errno 13] Permission denied: '/opt/data/.env'`

这说明：

- 只读 rootfs 下，镜像内部现有 `usermod` / runtime remap 路径仍会尝试触碰只读系统层
- 即使容器继续往后走，`/opt/data` 上当前 remap / bootstrap 协作模式也没有完成稳定兼容
- 当前阻塞不是 tmpfs 参数写错，而是 **只读 rootfs 与 accepted remap 模型的结构性冲突**

## 为什么当前还不能宣称 P0-2 accepted

因为当前只拿到了下面这些结论：

- repo-side 探针入口与测试已经落地
- `/run:exec` 是必要条件
- `10001:10001 remap + read_only rootfs` 仍会稳定失败

但还 **没有** 拿到下面这些条件：

- 在 accepted runtime model 下完整通过 `start -> boundary -> snapshot`
- live-side 验收
- 对 remap 模型的正式替代方案或正式回滚口径

因此当前正确状态只能是：

- `P0-2 probe established`
- `P0-2 blocker confirmed`
- `P0-2 not accepted`

## 与 earlier evidence 的关系

此前人工单变量实验已经提示：

- `10000:10000` 下基础启动可过
- 但 fresh init volume 上的 provider/config 初始态会混入 smoke 结果，不能直接拿来替代 accepted 结论

本轮 fresh repo-side probe 没有推翻这个判断；它只是把当前正式阻塞更清楚地锚定为：

- accepted model `10001:10001`
- read-only rootfs
- official root bootstrap

三者组合仍不兼容。

## 当前建议

下一步不要直接碰 live 运行面，也不要提前做 `watcher / lease / VM / network allowlist / PAD`。

优先顺序应是：

1. 把当前 `P0-2` 事实同步进状态文档
2. 继续 repo-side 单变量 probe，明确未来要选哪条路：
   - 保留 `10001:10001`，改 bootstrap / remap 机制
   - 或明确切换 runtime model，再重新跑 bring-up / boundary / snapshot
3. 在新的 runtime model 真正跑绿前，不把 `Phase 0` 写成完成

## 本轮验证

本轮已通过：

- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/test-hermes-arg-forwarding.ps1`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/test-phase0-readonly-probe.ps1`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/test-phase0-readonly-probe-env-resolution.ps1`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/test-hermes-provider-session-env-load.ps1`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/test-agentbridge-contract.ps1`

本轮 fresh runtime probe：

- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/invoke-phase0-readonly-probe.ps1 -SkipSnapshot -CleanupVolume`

结果：

- 探针成功进入真实 Docker/runtime 阻塞点
- `P0-2` 仍失败
- 失败原因已明确记录到本文件与 probe JSON

## 回滚点

本轮变更全部是 repo-side：

- 脚本参数绑定修复
- probe 编排修复
- strict-mode 兼容修复
- 新增测试
- 文档更新

如果需要回滚，本轮无需触碰 live：

- 仅回退本仓本轮脚本与文档改动即可
