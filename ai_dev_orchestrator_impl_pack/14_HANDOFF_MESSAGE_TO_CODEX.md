请阅读当前实现包内的全部文档，并严格按下列顺序开始工作：

> Status: non-authoritative operational prompt asset. Use only as a handoff helper, not as runtime truth.

1. 先输出一份 `implementation_plan.md`，按 Phase 1 MVP 列出模块、依赖和顺序；
2. 再说明如何在现有 `runtime/host-orchestrator` 骨架上扩展，而不是新建平行顶层包；
3. 再实现：
   - 配置加载
   - canonical 任务契约解析
   - worktree 管理
   - codex adapter
   - `.ai/state` 与 `.ai/runs` 工件落盘
   - 验证命令执行
4. 完成后提供：
   - 当前功能完成情况
   - 未完成项
   - 如何 dry-run
   - 下一步建议

强约束：
- 默认不自动 merge
- 默认不触碰敏感路径
- 默认不引入多余依赖
- 不要实现超出 MVP 的复杂 UI
- 不要脱离现有 `runtime/host-orchestrator` 骨架另起平行实现
- 需要测试
- 需要错误处理
- 需要清晰模块边界
