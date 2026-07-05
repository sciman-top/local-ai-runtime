# 启动实现清单

## 本地环境
- [ ] Python 3.12+
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
1. 创建目录结构
2. 写配置模型
3. 写 task schema 校验
4. 写 worktree manager
5. 写 codex adapter
6. 写 runner / logger
7. 写 verification
8. 写 report generation
9. 写 tests
10. 做一次 dry-run

## 第一轮 dry-run 示例
- 仅创建目录
- 不真正调用 Codex
- 只验证：
  - 任务解析
  - 路径检查
  - worktree 命令拼接
  - 工件目录生成
