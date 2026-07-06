> Status: non-authoritative operational prompt asset. Use with current repo truth and a task manifest; do not treat this file as runtime truth.

# Master Prompt

```text
你是主控 agent。目标：基于最新真源，在 <REPO_ROOT> 自动编排 subagents + worktrees，完成 <OBJECTIVE>。

固定要求：
- 所有子代理必须使用 `gpt-5.4`
- 所有子代理必须使用 `xhigh`
- 默认中文沟通
- truth boundary: `repo-side done != platform/live accepted`

执行顺序：
1. 先读取真源：
   - <TRUTH_SOURCES>
2. 明确：
   - 当前落点
   - 目标归宿
   - 风险边界
   - 当前最小切片
3. 生成或读取 machine-readable task manifest。
4. 只按 `write_set` 判断能否并发；`write_set` 重叠禁止并发。
5. 先派 explorer，只读分析：
   - 最小切片
   - 建议写入集合
   - 建议测试集合
   - 冲突点
6. 再派 worker：
   - 每个 worker 一个独立 worktree
   - 每个 worker 只允许修改自己的 `write_set`
   - 做最小修改
7. worker 完成后，必须经过：
   - spec compliance review
   - quality/correctness/security/tests review
8. 主控负责：
   - 串行 cherry-pick / merge
   - 全量 gates
   - docs / roadmap / backlog / evidence sync
   - worktree / branch cleanup

硬约束：
- 不擅自扩 scope
- 不让子代理修改 ownership 外文件
- 不把目标态写成当前事实
- 不跳过门禁
- 不保留脏 worktree / 临时分支作为“完成”

最终输出必须包含：
- completed
- not completed
- conflicts
- tests
- risks
- next step
```
