# 20260706 Preflight Line-Ending Hygiene Closeout

## Summary

本次切片收敛了当前仓唯一剩余的 `git diff --check` 非阻塞 CRLF warning，但没有扩展成全仓 Python 归一化。

保持不变的边界：

- `planning-status.json` 未改写
- 当前 active queue 仍然是 `PHASE-1-VERTICAL-SLICE`
- 当前预期 next action 仍然是 `phase1_prereq_probe_first`
- 本次只做 repo hygiene closeout，不宣称 Phase 1 live prerequisite probes 已 ready

## 触发原因

- 当前机器的 Git 全局配置为 `core.autocrlf=true`
- 仓库 `.gitattributes` 之前没有显式覆盖 `*.py`
- `scripts/verify-planning-status.py` 因此在 `git diff --check` 中持续产生“LF will be replaced by CRLF”告警

## 本次吸收的修整动作

- 在 `.gitattributes` 中把规则文件自身也显式固定为 `LF`
- 在 `.gitattributes` 中新增 `*.py text eol=lf`
- 采用“规则 + 定向修复”边界，不做全仓 Python `renormalize`
- 只收敛当前治理脚本切片中的 warning，不把无关 Python 文件卷入本次变更面

## 关键文件

- `.gitattributes`
- `scripts/verify-planning-status.py`
- `docs/plans/orchestrator-implementation-plan.md`
- `docs/backlog/orchestrator-task-list.md`

## 验证命令

- `git diff --check`
- `git ls-files --eol -- "*.py"`
- `python .\scripts\verify-planning-status.py`
- `python .\scripts\select-next-work.py`
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`

## 当前结果边界

- 当前 warning 已收敛为零噪声 closeout 目标
- repo-level Python line-ending policy 现已显式固定为 `LF`
- Governance Overlay 结论不变，selector 仍应返回 `phase1_prereq_probe_first`

## Rollback

- `git revert` 本次 `.gitattributes`、计划/任务清单与 evidence bundle
