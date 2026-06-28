## Summary

- Probe session root: D:\CODE\hermes-agent\private-local\phase1-probes\phase1-capability-probe-20260628-143744
- Artifacts root: D:\CODE\hermes-agent\private-local\phase1-probes\phase1-capability-probe-20260628-143744\artifacts
- Temporary workspace: C:\Users\sciman\AppData\Local\Temp\codex-phase1-probe-20260628-143744\workspace
- Isolated CODEX_HOME used for sandbox/network probes: C:\Users\sciman\AppData\Local\Temp\codex-phase1-probe-20260628-143744\codex-home
- Host auth/control plane reused only for codex exec and SDK probes; repo worktree and AgentBridge were not used as experiment targets.
- Codex version: codex-cli 0.142.3
- Final MVP conclusion: **network_proxy 未在本机证实，Phase 1 应收紧为纯本地任务自动执行；后台入口优先 SDK，必要时退回 codex exec。**

## Host Facts

- approval_policy = untrusted / on-failure / on-request / never
- sandbox_mode = read-only / workspace-write / danger-full-access
- sandbox entrypoint fact: Usage: codex sandbox [OPTIONS] [COMMAND]...
- features fact: network_proxy                        experimental       false

## Capability Matrix

| Capability | Conclusion | Key note |
| --- | --- | --- |
| workspace-write sandbox | 可直接用于 MVP | inside write succeeded = True; outside write blocked = True |
| network_proxy | 当前不可用，需 platform_na | network-off blocked = False; deny blocked = False; selected candidate = probe-allow; host feature line = network_proxy                        experimental       false |
| Codex SDK / execution control | 可直接用于 MVP | SDK probe plus codex exec fallback both exercised |
| Codex automations | 可用但需降级 | current app surface exposes native automation management, but dedicated watcher semantics for AgentBridge/tasks are still unproven |

## Sandbox Boundary Answer

- OS-enforced boundary: inside workspace write succeeded; outside workspace write did not create D:\CODE\_codex-phase1-outside-probe-20260628-143744\outside.txt.
- Raw sandbox protected-path note: raw sandbox 在 :workspace permissions profile 下拒绝写入 .codex，说明该路径已经被 profile 直接保护。
- Agent/control-plane protected-path note: agent 层对 .git/.codex/.agents 的写入未成功，符合“protected paths 属于上层控制面”的判断。

## Phase 1 Answers

- `workspace-write` 是否足够作为默认安全地基：**可直接用于 MVP**
- `network_proxy` 是否足够支撑最小 allowlist：**当前不可用，需 platform_na**
- SDK 是否足以作为首版后台控制入口：**可直接用于 MVP**
- automations 是否能减少自建 watcher：**可用但需降级**。当前只能确认原生 automation 管理入口存在，不能把它直接等同于已覆盖文件总线 watcher。
- MVP 范围收敛结论：**network_proxy 未在本机证实，Phase 1 应收紧为纯本地任务自动执行；后台入口优先 SDK，必要时退回 codex exec。**

## Artifacts

- Probe records JSON: artifacts/probe-records.json
- Each record keeps: cmd, exit_code, key_output, timestamp, active_rule_path.
