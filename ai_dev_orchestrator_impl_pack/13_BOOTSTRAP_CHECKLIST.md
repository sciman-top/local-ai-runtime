# 启动实现清单

## 本地环境
- [ ] Python 3.11+
- [ ] Git
- [ ] PowerShell 7
- [ ] Codex CLI
- [ ] 第三方 GPT-5.4 API 网关配置完成
- [ ] Claude Code + GLM-5.2 可本地运行（仅用于后续 Phase 2）

## 先行验证
- [ ] `codex --help` 可运行
- [ ] `codex exec` 可运行最小命令
- [ ] `git worktree list` 可运行
- [ ] 仓库可创建测试分支
- [ ] Python 可写 `.ai/runs/`

## 建议第一轮实现顺序
1. 先阅读 `docs/README.md` 与 `docs/architecture/planning-status.json`
2. 识别 `runtime/host-orchestrator` 现有可复用模块
3. 把默认 layout 迁到 `.ai/state` 与 `.ai/runs`
4. 落地 canonical task intake
5. 落地 `result.json` 与 markdown projection 双写
6. 接通 codex worker / exec fallback 的真实垂直切片
7. 补测试与 repo-side acceptance 脚本
8. 做一次 dry-run，再决定是否推进 live probe

## 第一轮 dry-run 示例
- 不新建平行顶层包
- 默认不真正调用 live Codex SDK
- 只验证：
  - authoritative docs 与 `planning-status.json` 已对齐
  - 任务解析
  - 路径检查
  - worktree 命令拼接
  - `.ai/state` / `.ai/runs` 工件目录生成
  - markdown projection 与 `result.json` 双写

## repo-side gate

- `python .\scripts\verify-planning-status.py`
- `uv run --project .\runtime\host-orchestrator python -m pytest`

以上 gate 只证明 repo-side truth 与实现骨架一致；不等于 live SDK 已验收。
