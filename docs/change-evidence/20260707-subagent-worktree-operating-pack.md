# 2026-07-07 Subagent Worktree Operating Pack

## Slice

- 本次只把 `主控 + 子代理 + worktree` 的通用/泛化协作模式落成 repo-owned 操作资产
- 新增一份中文使用说明、一组 prompt 资产、manifest/schema/checklist 模板
- 本次不改当前 runtime 行为，不改 planning queue，不把操作资产写成运行时真源

## Files

- `docs/主控-子代理-worktree-协作模式.md`
- `prompts/subagent-worktree/README.md`
- `prompts/subagent-worktree/master.prompt.md`
- `prompts/subagent-worktree/explorer.prompt.md`
- `prompts/subagent-worktree/worker.prompt.md`
- `prompts/subagent-worktree/spec-reviewer.prompt.md`
- `prompts/subagent-worktree/quality-reviewer.prompt.md`
- `templates/agent-work-manifest.example.yaml`
- `templates/agent-work-manifest.schema.json`
- `templates/closeout-checklist.md`

## Boundary

- 当前只是 repo-owned 操作资产与模板包
- 当前没有修改 `docs/architecture/planning-status.json`
- 当前没有修改 `.ai/config/*.yaml`
- 当前没有修改 runtime code、`lane`、`compatibility_projection_ref`
- 当前没有把 prompt 资产升级成 authoritative runtime truth

## Verification

- `python .\scripts\verify-planning-status.py`：pass
- `python .\scripts\select-next-work.py`：pass（`next_action = promote_phase1_execution`）
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit -Json`：pass
