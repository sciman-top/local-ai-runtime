# Phase 0 Cap Drop Probe 2026-06-28

更新时间：`2026-06-28`

## 结论

`P0-1 cap_drop:[ALL]` 已经不是“只在旧运行模型上做过一次历史探针”的状态。

本轮已在 **当前 accepted replacement runtime model** 上完成两次真实单变量探针：

- repo-side：`D:\CODE\hermes-agent\snapshots\agentbridge-20260628`
- live-side：`C:\Users\sciman\Documents\AgentBridge`

两边结论一致：

- `cap_drop:[ALL]` 在当前 accepted runtime model 下仍然 **blocked**
- 这不是 Compose 静态配置问题，而是当前真实 `docker run -> s6 -> Hermes bootstrap` 路径的运行时事实
- 因此 `P0-1` 当前正确口径应从“等待运行模型变化后再评估”升级为：
  - `replacement runtime model re-probed`
  - `still blocked`
  - `not accepted`

## 当前作用域

本轮没有修改 accepted baseline 的默认运行方式。

只做了两类动作：

1. 补齐真实运行路径的最小参数通路
   - `start-hermes.ps1`
   - `verify-hermes-boundary.ps1`
   - `invoke-hermes-bringup-once.ps1`
   - 现在都支持 `-CapDropAll`
2. 新增隔离 probe 入口
   - `invoke-phase0-cap-drop-probe.ps1`
   - 通过 cloned volume 在当前 accepted runtime model 上只增加 `cap_drop:[ALL]`
   - 不污染 accepted named volume

## 真实探针边界

关键 truth boundary 仍然不变：

- 不能只看 `compose.hermes.yml`
- 不能只看 helper 容器静态 inspect
- 真值必须来自真实 Windows-side：
  - `start-hermes.ps1`
  - `docker run`
  - `run-hermes-wrapper.sh`
  - `s6-overlay`
  - `Hermes --oneshot`

因此本轮 probe 采用的都是同一条真实执行链，而不是旁路 shell 片段。

## 探针方法

### 第一轮：repo-side 隔离真实 probe

位置：

- `D:\CODE\hermes-agent\snapshots\agentbridge-20260628`

命令：

```powershell
pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/invoke-phase0-cap-drop-probe.ps1 `
  -EnvFilePath 'D:\CODE\qq-codex-bot\.env' `
  -SourceVolumeName 'agentbridge-hermes-data' `
  -SkipSnapshot `
  -CleanupVolume
```

结果文件：

- [phase0-cap-drop-probe.json](D:/CODE/hermes-agent/private-local/phase0-probes/phase0-cap-drop-20260628-233607-514/phase0-cap-drop-probe.json)

### 第二轮：live-side 最小投影真实 probe

位置：

- `C:\Users\sciman\Documents\AgentBridge`

命令：

```powershell
& 'C:\Users\sciman\Documents\AgentBridge\scripts\invoke-phase0-cap-drop-probe.ps1' `
  -EnvFilePath 'D:\CODE\qq-codex-bot\.env' `
  -SourceVolumeName 'agentbridge-hermes-data' `
  -SkipSnapshot `
  -CleanupVolume
```

结果文件：

- `C:\Users\sciman\private-local\phase0-probes\phase0-cap-drop-20260628-233841-949\phase0-cap-drop-probe.json`

live-side 本轮只投影了 `cap_drop` 相关脚本与测试；accepted volume 没被直接改写。

## 当前 accepted runtime model

这两轮 probe 使用的都不是旧历史线，而是当前正式 accepted 线：

- `runtime_image = agentbridge/hermes-nonroot:p0-2-20260628`
- `bootstrap_model = derived_non_root`
- `runtime_user = 10001:10001`
- `container_start_user = 0:0`

也就是说，本轮已经把“运行模型变化后再评估”的条件真正兑现了。

## 结果

repo-side 与 live-side 的失败签名一致：

- `s6-applyuidgid: fatal: unable to set supplementary group list: Operation not permitted`
- `/opt/hermes/docker/main-wrapper.sh: 63: cd: can't cd to /opt/data`

同时 probe 也直接证明：

- `--cap-drop ALL` 确实已经进入真实 `docker run`
- 容器启动身份仍是当前 accepted 线要求的 `--user 0:0`
- 所以这不是“参数没生效”的假阴性

## 解释

这说明：

- `P0-2` 的 accepted replacement runtime model 解决了 `read_only rootfs + tmpfs` 问题
- 但它 **没有** 自动解决 `cap_drop:[ALL]`
- 当前 Hermes / s6 路径仍依赖在 `CapDrop=ALL` 下不可用的 supplementary groups / `/opt/data` 进入链

因此当前更准确的判断是：

- `P0-1` 不是“旧模型 blocker”
- 而是“当前 accepted runtime model 仍然存在的独立 blocker”

## 计划影响

这会把 `P0-1` 的计划口径从：

- `等待运行模型变化后再评估`

更新为：

- `已在 replacement runtime model 下复核，仍 blocked`

因此当前 `Phase 0` 的正确状态是：

- `P0-2 accepted`
- `P0-1 blocked after re-probe`
- `P0-3 只保留为平台边界/探针口径`

## 当前建议

- 不要把 `cap_drop:[ALL]` 留在 accepted baseline
- 不要把 repo-side 或 live-side 的这次失败再包装成“只是旧证据复述”
- 当前如果要继续推进 `Phase 0`，不应再重复同类 `P0-1` 真实探针
- 更合理的收口方式是：
  - 把 `P0-1` 固化为“当前 accepted 模型下仍 blocked”
  - 把 `P0-3` 固化为“platform_na / 不作为 Phase 1 前提”

## 本轮验证

已通过：

- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/test-hermes-arg-forwarding.ps1`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/test-phase0-readonly-probe.ps1`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/test-phase0-readonly-probe-env-resolution.ps1`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/test-agentbridge-contract.ps1`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/invoke-phase0-cap-drop-probe.ps1 -EnvFilePath 'D:\CODE\qq-codex-bot\.env' -SourceVolumeName 'agentbridge-hermes-data' -SkipSnapshot -CleanupVolume`
- `pwsh -NoProfile -File C:\Users\sciman\Documents\AgentBridge\scripts\test-hermes-arg-forwarding.ps1`
- `pwsh -NoProfile -File C:\Users\sciman\Documents\AgentBridge\scripts\test-phase0-readonly-probe.ps1`
- `& 'C:\Users\sciman\Documents\AgentBridge\scripts\invoke-phase0-cap-drop-probe.ps1' -EnvFilePath 'D:\CODE\qq-codex-bot\.env' -SourceVolumeName 'agentbridge-hermes-data' -SkipSnapshot -CleanupVolume`

## 回滚点

如果要回滚本轮 `P0-1` 相关 live 脚本投影：

- live 备份目录：
  - `D:\CODE\hermes-agent\private-local\live-projection-backups\agentbridge-live-p0-1-20260628-233808-669`

如果只回滚 repo-side：

- 回退本轮新增的 `CapDropAll` 参数通路
- 回退 `invoke-phase0-cap-drop-probe.ps1`
- 回退相关测试与文档同步
