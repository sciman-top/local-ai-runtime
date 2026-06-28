# scripts

`host-orchestrator` 的本地开发、smoke 与验收脚本。

- `run-wave1-smokes.ps1`：运行 deterministic `W1-T06` smoke 样本任务集，产物写到 `private-local/wave-smokes/`
- `test-wave1-acceptance.ps1`：串起 `pytest -> contract -> smoke` 的 `W1-T07` repo-side fake-first 验收链

这些脚本只证明 repo-side smoke/acceptance 资产已落地，不证明 live `Codex SDK` 真机执行已验收。
