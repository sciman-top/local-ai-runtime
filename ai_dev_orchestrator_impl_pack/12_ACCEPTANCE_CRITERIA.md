# 验收标准

## MVP 验收标准
### A. 基础能力
- [ ] 能读取 `tasks.json`
- [ ] 能校验任务结构
- [ ] 能创建 branch + worktree
- [ ] 能在指定 worktree 中执行 Codex task
- [ ] 能运行 test/lint/typecheck/build
- [ ] 能把日志和工件写入 `.ai/runs/<run_id>/`

### B. 安全边界
- [ ] 默认禁止敏感路径
- [ ] 任务只能写 `allowed_paths`
- [ ] 非写权限任务不能改文件
- [ ] 失败不会 silent

### C. 可维护性
- [ ] 模块化清晰
- [ ] 有基础测试
- [ ] 有 clear error handling
- [ ] 幂等清理逻辑清楚

### D. 输出工件
- [ ] `plan.md`
- [ ] `tasks.json`
- [ ] `stdout.log`
- [ ] `stderr.log`
- [ ] `result.json`
- [ ] `verification_summary.json`
- [ ] `pr_body.md`

## Phase 2 验收
- [ ] GLM 能对计划做只读审查
- [ ] GLM 能对 diff 输出结构化 review JSON
- [ ] GPT-5.4 能综合 GLM 反馈形成最终 review report

## 明确不作为“通过”的情况
以下任一出现，视为不通过：
- 自动 merge 到 main
- 擅自修改敏感路径
- 多 worker 共享写一个 worktree
- 没有日志落盘
- 没有错误状态记录
