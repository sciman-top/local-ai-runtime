@AGENTS.md

# CLAUDE.md — Local AI Runtime（Claude 项目级 wrapper）
**项目展示名**: `Local AI Runtime`
**中文名**: `本地 AI 运行时`
**历史仓库 slug / 当前本地目录**: `local-ai-dev-orchestrator`
**承接来源**: `GlobalUser/CLAUDE.md v9.54`
**共同项目规则**: `AGENTS.md`
**适用范围**: 项目级（仓库根）
**最后更新**: 2026-07-06

## 1. 阅读指引
- 本文件通过上方独立 import 承接共同项目规则，只追加 Claude 平台差异。
- 不在本文件复制项目事实、门禁、证据、回滚或共同项目规则映射；这些内容一律以 `AGENTS.md` 为准。
- 本仓是受管目标仓试点，不负责全局规则分发；全局规则真源在 `D:\CODE\governed-ai-coding-runtime`。

## B. Claude 平台差异
- Claude 项目规则真源是 `CLAUDE.md` + 上方 `@AGENTS.md` import；若加载可疑，先用 `/memory`、`/status` 或当前 help 取证。
- `.claude/settings.json`、`.claude/rules/`、hooks、permissions、MCP 属 deterministic enforcement，不在本文件复制配置正文。
- `CLAUDE.local.md` 只允许存放本机个人偏好，不能作为 repo truth 或规则真源。
- 本文件必须保持 thin wrapper：只保留 Claude 加载诊断、settings/hooks 边界和少量平台差异，不复制运行时目录、调度真源、run evidence 路径或共同项目规则映射正文。

## D. 维护校验
- 若共同规则主体变化，先改 `AGENTS.md`，不要把 wrapper 扩写成第二份共同正文。
- 修改本文件或控制仓 Claude 全局规则后，重新运行：
  - `python D:\CODE\governed-ai-coding-runtime\scripts\verify-target-project-rules.py --targets local-ai-dev-orchestrator`
  - `python .\scripts\verify-planning-status.py`
  - `pwsh .\scripts\governance\preflight.ps1 -DisableAutoCommit`
