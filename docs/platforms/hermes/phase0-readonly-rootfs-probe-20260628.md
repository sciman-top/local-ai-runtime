# Phase 0 Read-only Rootfs Probe 2026-06-28

更新时间：`2026-06-28`

## 结论

当前 `Wave 0 / P0-2` 已从“文档计划”推进到“repo-side 真实隔离探针”，并已在 live `AgentBridge` 上完成正式 acceptance。

本轮 fresh evidence 结论是：

- `read_only rootfs` 不是天然不可行
- `tmpfs /run` 不能用默认挂载；最小必要条件是 `--tmpfs /run:exec`
- 当前 accepted 运行模型 `official_root_bootstrap + runtime remap 10001:10001` 与 `read_only rootfs` 组合仍稳定阻塞
- comparative probe 只把 runtime uid/gid 单变量切到 `10000:10000` 后，`usermod` 与 `/opt/data` 权限错误链已消失；在 probe-only fresh volume config bootstrap 对齐后，fresh volume 默认 `--oneshot` 已返回 `OK`
- 纯 `derived_non_root` 派生镜像如果直接以 `10001:10001` 启动容器，会更早失败在 `s6-overlay preinit` 的 `/run` 所有权检查
- 但 repo-side 混合候选运行模型 `derived_non_root image + runtime_user 10001:10001 + container_start_user 0:0` 已在隔离 probe 下完整通过 `bring-up -> boundary -> snapshot`
- 因此当前 `P0-2` 的最终状态应写成：
  - 旧 accepted 模型 `official_root_bootstrap + runtime remap 10001:10001` 在 `read_only rootfs` 下稳定阻塞
  - replacement 模型 `derived_non_root + runtime_user 10001:10001 + container_start_user 0:0` 已 live-side accepted
- `P0-2 accepted`
- 但这不等于“Phase 0 全绿完成”；后续还需要把 `P0-1/P0-3` 的边界口径写实，而不是把它们误说成已接受能力

## 本轮 scope

只在维护仓 `D:\CODE\local-ai-dev-orchestrator` 内做 repo-side 工作：

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
  - 新增 runtime profile override：
    - 可在 probe 内覆盖 `runtime_image / runtime_user / bootstrap_model / volume_uid / volume_gid`
  - 新增 `ContainerUserOverride`：
    - 仅限 probe / bring-up / boundary 的 Docker `--user` 临时单变量实验
  - 新增 `ContainerStartUserOverride`：
    - 用于把容器顶层启动身份写入 probe runtime profile，验证 `container_start_user` 这种更接近长期运行模型的语义
  - 新增 probe-only fresh volume config bootstrap：
    - 仅在隔离 probe volume 内写入命名 custom provider 配置
    - 把 fresh volume 默认 provider/config 口径对齐到当前 bridge session
    - 不改 live `AgentBridge`、不改 live `/opt/data`
- `Dockerfile.hermes-nonroot`
  - 不再假设上游镜像里一定不存在 `hermes` 用户/组
  - 当前镜像若已自带 `hermes:10000:10000`，改为复用并重写 uid/gid，而不是直接 `groupadd` 失败
- `build-hermes-nonroot.ps1`
  - 修复 strict-mode 下 `$bootstrapModel` 未初始化崩溃
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

- [phase0-readonly-rootfs-probe.json](D:/CODE/local-ai-dev-orchestrator/private-local/phase0-probes/phase0-readonly-rootfs-20260628-202120-338/phase0-readonly-rootfs-probe.json)

当前 accepted runtime profile：

- [hermes-runtime.json](D:/CODE/local-ai-dev-orchestrator/snapshots/agentbridge-20260628/docs/hermes-runtime.json)

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

### 3. comparative probe：`10000:10000` 只改 uid/gid 后，结构性阻塞被明显缩窄

本轮 fresh comparative probe 报告文件：

- [phase0-readonly-rootfs-probe.json](D:/CODE/local-ai-dev-orchestrator/private-local/phase0-probes/phase0-readonly-rootfs-20260628-212302-672/phase0-readonly-rootfs-probe.json)

探针方法保持同一条 repo-side 隔离链路：

- 仍使用 `read_only rootfs`
- 仍使用 `--tmpfs /run:exec --tmpfs /tmp`
- 仍使用 fresh isolated volume
- 只把 runtime uid/gid 从 `10001:10001` 改为 `10000:10000`

这次没有再出现旧的阻塞链：

- 没有 `usermod: cannot lock /etc/passwd`
- 没有 `PermissionError: [Errno 13] Permission denied: '/opt/data/gateway_state.json'`
- 没有 `PermissionError: [Errno 13] Permission denied: '/opt/data/.env'`

相反，容器已经能完整越过：

- `01-hermes-setup`
- `02-reconcile-profiles`
- `main-hermes` / `dashboard` supervised services startup

新的失败下沉为应用层：

- `hermes -z: no final response was produced; treating the run as failed.`

这说明两件事：

- 当前 `10001:10001` 线上的主 blocker，至少已经被缩窄到 runtime remap / volume-owner 协作问题，而不再只是“read_only rootfs 不可用”的笼统判断
- 但 `10000:10000` 这条线仍不能宣布 accepted，因为它只是 comparative probe；当前最多只能说明 repo-side 已把剩余问题继续缩窄到 fresh volume 默认 provider/config bootstrap

### 4. retained-volume follow-up：`10000:10000` 线上剩余失败属于默认 provider/bootstrap 组合，不再是 rootfs blocker

为了避免把 fresh volume 初始化噪声和 rootfs 结论混在一起，本轮对同一个 retained probe volume 再做了两次附加实验：

1. 直接检查 `/opt/data/config.yaml`
2. 在同一 volume 上显式加载 bridge session env，再跑显式 provider/model 的 `--oneshot`

结果是：

- fresh volume 中的 `config.yaml` 仍是 Hermes 默认值：
  - `model.provider: auto`
  - `model.base_url: https://openrouter.ai/api/v1`
  - `providers: {}`
- 同一 volume 内没有 `/opt/data/.env`
- 同一 volume 内没有 `/opt/data/auth.json`
- 在这个 retained volume 上，只要显式传：
  - `--provider openai-api`
  - `--model gpt-5.4`
  - 并保留当前 bridge session env 注入
  默认 `--oneshot` 就已经能返回 `OK`

这说明：

- `10000:10000 + read_only rootfs + /run:exec,/tmp` 这条 comparative 线当前并不是被 rootfs 或 volume 权限继续卡死
- 剩余失败更像是 **fresh volume 默认 provider/config bootstrap 与默认 oneshot 回退路径** 的组合问题
- 因此它仍不能直接替代 accepted 运行模型，但它已经把当前 blocker 从“容器起不来/权限不通”进一步缩窄成“fresh config 默认 provider 口径不匹配”

### 5. probe-only bootstrap follow-up：fresh volume 默认 `--oneshot` 已在 `10000:10000` comparative 线上返回 `OK`

为了验证剩余 blocker 是否真的只落在 fresh volume 默认 provider/config 初始态，本轮又补了一刀 **仅限 repo-side probe** 的最小适配：

- 仍使用 `read_only rootfs`
- 仍使用 `--tmpfs /run:exec --tmpfs /tmp`
- 仍使用 fresh isolated volume
- 仍只把 runtime uid/gid 设为 `10000:10000`
- 额外只在 probe volume 内预写一份最小 `config.yaml`：
  - `model.provider: custom:primary-gateway`
  - `providers.primary-gateway.base_url: https://ai.input.im/v1`
  - `providers.primary-gateway.key_env: OPENAI_API_KEY`
  - `model.default_headers.User-Agent: curl/8.7.1`

新的成功 evidence：

- [phase0-readonly-rootfs-probe.json](D:/CODE/local-ai-dev-orchestrator/private-local/phase0-probes/phase0-readonly-rootfs-20260628-215023-143/phase0-readonly-rootfs-probe.json)

结果：

- fresh isolated volume 默认 `--oneshot` 已直接返回 `OK`
- `main-hermes` / `dashboard` supervised services 正常起停
- `service_uidgid_present / observed_read_only_rootfs / rootfs_write_blocked / tmpfs_targets` 全部通过

配套对照也已补齐：

- 关掉 probe bootstrap 的 `10000:10000` 对照失败：
  - [phase0-readonly-rootfs-probe.json](D:/CODE/local-ai-dev-orchestrator/private-local/phase0-probes/phase0-readonly-rootfs-20260628-215117-133/phase0-readonly-rootfs-probe.json)
  - 仍回到 `hermes -z: no final response was produced`
- 保持 probe bootstrap、但回到 accepted `10001:10001` 运行模型的对照失败：
  - [phase0-readonly-rootfs-probe.json](D:/CODE/local-ai-dev-orchestrator/private-local/phase0-probes/phase0-readonly-rootfs-20260628-215117-179/phase0-readonly-rootfs-probe.json)
  - 仍回到 `usermod: cannot lock /etc/passwd` + `/opt/data/gateway_state.json` + `/opt/data/.env` 权限链

这把归因进一步钉死为：

- `10000:10000` comparative 线上的 fresh volume 默认 oneshot 失败，确实主要是 provider/config bootstrap 口径不一致
- 但 accepted `10001:10001` 线的真实 blocker 依旧是 remap / rootfs 结构性冲突
- 因此本轮新增进展仍只属于 `repo-side blocker 缩窄`，不是 `P0-2 accepted`

### 6. 纯 `derived_non_root` 直启线也不是现成替代：会更早死在 `/run` preinit

为了把“是否正式切换 runtime model”从抽象讨论推进到真实证据，本轮先把 repo 内已有的派生 non-root 运行模型链路补到可探针：

- 修复 `Dockerfile.hermes-nonroot` 对上游镜像结构的错误假设
  - 当前官方镜像里已存在 `hermes:x:10000:10000`
  - 原 Dockerfile 直接 `groupadd hermes` 会失败在 `group 'hermes' already exists`
- 修复 `build-hermes-nonroot.ps1` 的 strict-mode 漏洞后，成功构建：
  - `agentbridge/hermes-nonroot:p0-2-20260628`

随后做了第一条派生镜像运行模型探针：

- `runtime_image = agentbridge/hermes-nonroot:p0-2-20260628`
- `runtime_user = 10001:10001`
- `bootstrap_model = derived_non_root`
- 容器启动身份不覆盖，直接沿用镜像用户

失败 evidence：

- [phase0-readonly-rootfs-probe.json](D:/CODE/local-ai-dev-orchestrator/private-local/phase0-probes/phase0-readonly-rootfs-20260628-221127-659/phase0-readonly-rootfs-probe.json)

失败点不再是旧的 `usermod + /opt/data` 链，而是更早的：

- `/package/admin/s6-overlay/libexec/preinit: fatal: /run belongs to uid 0 instead of 10001`

这说明：

- 纯 `derived_non_root` 直启线虽然绕开了 `usermod`
- 但在 `read_only rootfs + tmpfs /run:exec` 下，`s6-overlay` 仍要求先以 root 进入 preinit 阶段处理 `/run`
- 所以“直接切成派生 non-root 镜像”本身不是现成 accepted 替代

### 7. 混合候选运行模型已拿到 repo-side 全链路绿色证据

在确认纯 `derived_non_root` 直启线被 `/run preinit` 卡住后，本轮再补了一刀更窄的单变量：

- 保留派生镜像：
  - `runtime_image = agentbridge/hermes-nonroot:p0-2-20260628`
- 保留服务落点：
  - `runtime_user = 10001:10001`
  - `volume_uid = 10001`
  - `volume_gid = 10001`
- 仅在 Docker 启动身份上额外覆盖：
  - 第一轮显式实验：`ContainerUserOverride = 0:0`
  - 随后已收束成 runtime profile 语义：`container_start_user = 0:0`

也就是：

- 容器 top-level 仍以 root 进入 `s6 preinit`
- 业务服务与可写输出仍落到 `10001:10001`
- 继续保持 `read_only rootfs + --tmpfs /run:exec + --tmpfs /tmp`

新的成功 evidence：

- 第一轮显式 override 成功样本：
  - [phase0-readonly-rootfs-probe.json](D:/CODE/local-ai-dev-orchestrator/private-local/phase0-probes/phase0-readonly-rootfs-20260628-222013-307/phase0-readonly-rootfs-probe.json)
  - [known-good-20260628-222042-261.json](D:/CODE/local-ai-dev-orchestrator/private-local/phase0-probes/phase0-readonly-rootfs-20260628-222013-307/bridge/docs/known-good-20260628-222042-261.json)
  - [hermes-data-20260628-222042-261.tgz](D:/CODE/local-ai-dev-orchestrator/private-local/phase0-probes/phase0-readonly-rootfs-20260628-222013-307/bridge/docs/volume-backups/hermes-data-20260628-222042-261.tgz)
- 更强的 runtime-profile 语义成功样本：
  - [phase0-readonly-rootfs-probe.json](D:/CODE/local-ai-dev-orchestrator/private-local/phase0-probes/phase0-readonly-rootfs-20260628-223400-954/phase0-readonly-rootfs-probe.json)

结果：

- `bring-up` 返回 `OK`
- `boundary` 直接观测到：
  - `bootstrap_model = derived_non_root`
  - `runtime_user = 10001:10001`
  - 第一轮显式样本里 `requested_container_user_override = 0:0`
  - `service_uidgid_present = true`
  - `service_uidgid_lines` 命中 `10001:10001` 的 `hermes chat`
  - `rootfs_write_blocked = true`
  - `tmpfs_targets = /run,/tmp`
- 更强的 `223400-954` 样本则把相同语义落到 runtime profile：
  - `bootstrap_model = derived_non_root`
  - `runtime_user = 10001:10001`
  - `container_start_user = 0:0`
  - 无需再依赖外部临时 `ContainerUserOverride`
- `snapshot` 与 `snapshot_test` 全部通过

这说明：

- 当前 repo-side 已经不只是“accepted 线阻塞被缩窄”
- 还额外拿到了一条可完整跑绿的 replacement runtime model
- 这条线随后又在 live `AgentBridge` 上完成了正式 acceptance

## 为什么现在可以宣称 P0-2 accepted

因为本轮已经补齐了此前缺的 live-side 条件：

- live `docs/hermes-runtime.json` 已切到：
  - `bootstrap_model = derived_non_root`
  - `runtime_image = agentbridge/hermes-nonroot:p0-2-20260628`
  - `runtime_user = 10001:10001`
  - `container_start_user = 0:0`
- live `invoke-hermes-bringup-once.ps1` 已完整通过：
  - `load -> contract -> gates -> start -> boundary -> snapshot -> snapshot_test`
- 最新 live snapshot：
  - [known-good-20260628-225738-431.json](D:/CODE/local-ai-dev-orchestrator/snapshots/agentbridge-20260628/docs/known-good-20260628-225738-431.json)
- 最新 live boundary：
  - [verify-hermes-boundary-20260628-225841-414.json](D:/CODE/local-ai-dev-orchestrator/snapshots/agentbridge-20260628/docs/verify-hermes-boundary-20260628-225841-414.json)

因此当前正确状态已经升级为：

- `P0-2 accepted`
- 旧 accepted 模型 `official_root_bootstrap + 10001:10001 remap` 保留为 blocked historical line
- comparative `10000:10000 + probe-only bootstrap` 继续只算 comparative evidence
- `Phase 0` 整体仍未完成，因为 `P0-1` 与 `P0-3` 还没关

## 与 earlier evidence 的关系

此前人工单变量实验已经提示：

- `10000:10000` 下基础启动可过
- 但 fresh init volume 上的 provider/config 初始态会混入 smoke 结果，不能直接拿来替代 accepted 结论

本轮 fresh repo-side probe 没有推翻这个判断；它只是把当前正式阻塞更清楚地锚定为：

- accepted model `10001:10001`
- read-only rootfs
- official root bootstrap

三者组合仍不兼容。

新的 `10000:10000` comparative probe 也没有推翻“不能直接替代 accepted 结论”这条边界。它只证明：

- 旧的 `usermod + /opt/data EACCES` 链并不是 `read_only rootfs` 的唯一必然结果
- fresh volume 默认 `--oneshot` 的剩余失败可以在 probe-only bootstrap 下被消掉，说明该部分 blocker 已被 repo-side 收口
- 但 accepted 所需的正式运行模型、boundary、snapshot 闭环仍然没有在 `10001:10001` 线上通过，因此不能把 `10000:10000` 直接升级为正式运行模型

新的混合候选运行模型在 live acceptance 之后，已经正式推翻了“当前 accepted truth 仍是 official_root_bootstrap”的旧口径。当前更准确的关系是：

- 派生镜像本身可以在当前官方镜像结构上成功构建
- 纯 `derived_non_root` 直启并不成立
- 但“派生镜像 + runtime_user 10001:10001 + container_start_user 0:0” 这条线已先在 repo-side 跑绿，再在 live-side 完成 acceptance
- 因此当前已经不再是“要不要升级候选”的问题，而是“后续 `P0-1 / P0-3` 应如何基于新 accepted 模型继续推进”

## 当前建议

下一步不要提前做 `watcher / lease / VM / PAD`。

优先顺序应是：

1. 把当前 `P0-2 accepted` 事实同步进状态文档与快照索引
2. 把 `P0-1 cap_drop:[ALL]` 的最新口径同步成：已在新 accepted runtime model 下复核，仍 blocked
3. 把 `P0-3 network allowlist` 的最新口径同步成：`platform_na / 非 Phase 1 前提`
4. 不要把“运行面已收口”误写成“Phase 0 全部能力 accepted”

## 本轮验证

本轮已通过：

- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/test-hermes-arg-forwarding.ps1`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/test-phase0-readonly-probe.ps1`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/test-phase0-readonly-probe-env-resolution.ps1`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/test-hermes-provider-session-env-load.ps1`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/test-agentbridge-contract.ps1`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/build-hermes-nonroot.ps1 -BaseImage 'nousresearch/hermes-agent@sha256:9f367c7756ef087661a361536a89f438d57a122b958dc23d82d456b1433e6e9e' -Tag 'agentbridge/hermes-nonroot:p0-2-20260628' -Uid 10001 -Gid 10001`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/invoke-phase0-readonly-probe.ps1 -RuntimeUid 10000 -RuntimeGid 10000 -SkipSnapshot -CleanupVolume`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/invoke-phase0-readonly-probe.ps1 -RuntimeUid 10000 -RuntimeGid 10000 -SkipProbeConfigBootstrap -SkipSnapshot -CleanupVolume`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/invoke-phase0-readonly-probe.ps1 -SkipSnapshot -CleanupVolume`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/invoke-phase0-readonly-probe.ps1 -RuntimeUid 10001 -RuntimeGid 10001 -RuntimeImageOverride 'agentbridge/hermes-nonroot:p0-2-20260628' -RuntimeUserOverride '10001:10001' -BootstrapModelOverride 'derived_non_root' -CleanupVolume`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/invoke-phase0-readonly-probe.ps1 -RuntimeUid 10001 -RuntimeGid 10001 -RuntimeImageOverride 'agentbridge/hermes-nonroot:p0-2-20260628' -RuntimeUserOverride '10001:10001' -BootstrapModelOverride 'derived_non_root' -ContainerUserOverride '0:0' -CleanupVolume`
- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/invoke-phase0-readonly-probe.ps1 -RuntimeUid 10001 -RuntimeGid 10001 -RuntimeImageOverride 'agentbridge/hermes-nonroot:p0-2-20260628' -RuntimeUserOverride '10001:10001' -BootstrapModelOverride 'derived_non_root' -ContainerStartUserOverride '0:0' -CleanupVolume`
- live acceptance：
  - `& 'C:\Users\sciman\Documents\AgentBridge\scripts\invoke-hermes-bringup-once.ps1' -EnvFilePath 'D:\CODE\qq-codex-bot\.env' -ReadOnlyRootfs -TmpfsMounts @('/run:exec','/tmp')`
  - `& 'C:\Users\sciman\Documents\AgentBridge\scripts\verify-hermes-boundary.ps1' -ReadOnlyRootfs -TmpfsMounts @('/run:exec','/tmp')`
- retained-volume follow-up：
  - 检查 comparative probe volume 内的 `/opt/data/config.yaml`
  - 在同一 volume 上显式加载 session env 后，执行 `start-hermes.ps1 -ReadOnlyRootfs -TmpfsMounts @('/run:exec','/tmp') --oneshot 'Reply with exactly OK.' --provider openai-api --model gpt-5.4`

本轮 fresh runtime probe：

- `pwsh -NoProfile -File snapshots/agentbridge-20260628/scripts/invoke-phase0-readonly-probe.ps1 -RuntimeUid 10000 -RuntimeGid 10000 -SkipSnapshot -CleanupVolume`

结果：

- probe-only config bootstrap 打开时，fresh isolated volume 默认 `--oneshot` 已返回 `OK`
- 关掉 bootstrap 的 `10000:10000` 对照会稳定回到 `hermes -z: no final response was produced`
- accepted `10001:10001` 运行模型的对照仍稳定回到 `usermod + /opt/data` 权限阻塞
- 纯 `derived_non_root` 直启线会更早失败在 `/run preinit`
- 混合候选运行模型 `derived image + runtime_user 10001:10001 + container_start_user 0:0` 已完整通过 `bring-up -> boundary -> snapshot`
- 因此 `P0-2` 已从 repo-side candidate 升级为 live accepted truth

## 回滚点

本轮变更分两部分：

- 脚本参数绑定修复
- probe 编排修复
- strict-mode 兼容修复
- 新增测试
- 文档更新
- live runtime profile 已从旧 accepted 模型切到新的 replacement 模型

如果需要回滚：

- repo-side：
  - 回退本仓本轮脚本与文档改动即可
- live-side：
  - 恢复本轮备份前的 `docs/hermes-runtime.json`
  - 恢复本轮备份前的运行模型相关脚本
  - 如需完全回到旧 accepted 历史线，再用旧 runtime profile 重跑 `bring-up -> boundary -> snapshot`
