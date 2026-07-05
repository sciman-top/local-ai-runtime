# 20260706 Governed Governance Absorption

## Summary

本次切片把 `governed-ai-coding-runtime` 中对当前主线真正有用的治理机制正式吸收进 `local-ai-dev-orchestrator`，但没有把本仓改写成 governance hub。

当前保持不变的边界：

- 当前产品 active queue 仍然是 `PHASE-1-VERTICAL-SLICE`
- 当前主线实现仍在 `runtime/host-orchestrator`
- `governed-ai-coding-runtime` 只是 `governance-sidecar` reference companion

## 吸收的机制

- `planning truth / selector split`
- `repo-level change-evidence index`
- `release-style preflight`
- `formal reference governance companion`

## 没有直接照搬的部分

- 没有复制完整 `current_live_posture / effect feedback / target-run freshness` 体系
- 没有把本仓改写成 `Continuous-Execution` 或多层治理中心
- 没有新增 CI workflow
- 没有新增 repo-root Python 项目

原因：

- 当前仓真正紧迫的是 `Phase 1` prerequisite probes 与 product mainline，不是完整复刻 governed runtime 的自有治理体系

## 关键文件

- `docs/architecture/planning-status.json`
- `docs/architecture/next-work-selection-policy.json`
- `scripts/verify-planning-status.py`
- `scripts/select-next-work.py`
- `scripts/governance/preflight.ps1`
- `references/reference-shelf.manifest.json`

## 验证命令

- `python .\scripts\verify-planning-status.py`
- `python .\scripts\select-next-work.py`
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`
- `pwsh .\scripts\refresh-reference-repos.ps1 -FetchOnly -SkipDirtyRepos -RepoNames governed-ai-coding-runtime`

## 当前结果边界

- Governance Overlay 已落盘
- selector 当前预期输出应为 `phase1_prereq_probe_first`
- 只有在 GPT-5.4 gateway 与 `codex exec` prerequisite probes 被刷新为 ready 后，才应推进 `promote_phase1_execution`

## Rollback

- `git revert` 本次 Governance Overlay 文档、脚本、manifest 与 evidence bundle
