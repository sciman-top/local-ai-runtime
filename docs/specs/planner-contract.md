# Planner Contract

## 目的

定义 live planner sidecar 的正式输出协议。

## 当前事实边界

- 当前 planner sidecar 只在 codex-backed `host_local` profile 上 live materialize
- planner-gated task 当前会先运行 planner sidecar、写出 `planner_result.json`，然后仍停在 `waiting_handoff`
- 当前这条 planner receipt 边界并不等于 live `Direct GPT-5.4 API` planner 已接线
- capability / quota / lane 不满足的 pre-worker handoff 仍保持 fail-closed，不伪装成 planner 已执行

## 必填字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `task_id` | string | 关联任务 |
| `planner_kind` | enum | `codex_sdk / gpt54_direct / repo_policy_gate` |
| `planner_mode` | enum | `advisory / blocking` |
| `planner_profile` | string | 实际 planner 走的 repo-owned worker profile |
| `model` | string | 实际模型名，或 repo-owned policy identifier |
| `risk` | enum | `low / medium / high / critical` |
| `disposition` | enum | `proceed / handoff` |
| `reason_summary` | string | 结构化原因摘要 |
| `blocking_reasons` | string[] | 阻断原因；`disposition=handoff` 时至少应有语义性内容 |
| `plan_outline` | string[] | 下一步计划摘要 |
| `source_evidence_refs` | string[] | planner 依据的正式证据引用 |

## 当前运行边界

- `disposition=proceed` 当前只表示 planner 允许后续 worker 继续，不代表 runtime 已自动继续执行 worker
- `disposition=handoff` 当前表示 planner 明确要求 operator follow-up，runtime 继续停在 `waiting_handoff`
- 当前 `planner_result.json` 是 repo-owned planner receipt，不等于 live accepted

## 示例

```json
{
  "task_id": "TASK-20260707-planner-sidecar",
  "planner_kind": "codex_sdk",
  "planner_mode": "blocking",
  "planner_profile": "local_maint",
  "model": "gpt-5.4",
  "risk": "high",
  "disposition": "proceed",
  "reason_summary": "Planner sidecar recorded a proceed disposition and kept the run at the worker boundary.",
  "blocking_reasons": [],
  "plan_outline": [
    "Review the planner receipt.",
    "Continue the worker step only after operator approval."
  ],
  "source_evidence_refs": [
    ".ai/runs/<run_id>/<task_id>/result.json",
    ".ai/runs/<run_id>/<task_id>/dispatch_state.json",
    ".ai/runs/<run_id>/<task_id>/verification_summary.json",
    ".ai/runs/<run_id>/<task_id>/cost_summary.json"
  ]
}
```
