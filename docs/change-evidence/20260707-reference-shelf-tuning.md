# 2026-07-07 Reference Shelf Tuning

## Slice

- 不调整 `default_refresh_set`
- 保持 `codex / plugins / modelcontextprotocol / servers` 作为当前主线默认刷新集合
- 把 `modelcontextprotocol/registry` 补成 `conditional-not-cloned` 候选，而不是立即加入本机 clone 集合
- 明确 `skills / hermes-agent-self-evolution / openclaw` 继续保留为 `archive-on-demand`，并作为以后本机参考架瘦身时的第一批本地删除候选

## Why

- 当前项目主线仍是 `Codex-first hot path + Hermes sidecar + optional Claude review sidecar`
- `registry` 对 MCP server discovery、registry publish、catalog sync、trust policy 很有价值，但还不是当前日常主线默认排查面
- `skills / hermes-agent-self-evolution / openclaw` 已经不在默认刷新集合里；先保留分层真相，但不要求长期保留本地 clone

## Files

- `references/reference-shelf.manifest.json`
- `references/README.md`
- `docs/参考项目清单.md`
- `docs/社区参考源码策略.md`
- `D:/CODE/external/local-ai-dev-orchestrator-references/README.md`

## Boundary

- 这次只更新参考架治理口径，不刷新上游仓，不改 `default_refresh_set`
- 这次不删除任何本地参考 clone；archive 仓只被标记为未来瘦身优先候选
- 这次不把 `registry` 写成当前主线默认参考面

## Verification

- `Get-Content references/reference-shelf.manifest.json -Raw | ConvertFrom-Json`：pass
- `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit -Json`：pass
- `build` / `hotspot` 继续按 repo-owned `gate_na` 记录；替代验证仍分别落在 `pytest` 与 `verifier + pytest + diff hygiene`
