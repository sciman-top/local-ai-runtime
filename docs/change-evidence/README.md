# Change Evidence Index

这个目录只存 **repo-level governance evidence**，不存 task-level `.ai/runs/<run_id>/<task_id>/` 正式工件。

边界：

- 这里记录 selector、preflight、reference governance、docs routing 这类仓级治理证据
- task-level `result.json`、`verification_summary.json`、`cost_summary.json`、`evidence_index.json` 仍属于 `.ai/runs/<run_id>/<task_id>/`
- 这里的索引只回答“当前仓的治理增强面何时、为何、如何被刷新”

当前入口：

- [20260706 Governed Governance Absorption](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-governed-governance-absorption.md)
- [20260706 Preflight Line-Ending Hygiene Closeout](D:/CODE/local-ai-dev-orchestrator/docs/change-evidence/20260706-preflight-line-ending-hygiene-closeout.md)

当前最新结论：

- Governance Overlay 已作为当前主线的 cross-cutting layer 落盘
- Python repo-level line-ending policy 已显式覆盖 `*.py -> LF`
- 当前 active queue 仍是 `PHASE-1-VERTICAL-SLICE`
- 当前预期 next action 仍是 `phase1_prereq_probe_first`
