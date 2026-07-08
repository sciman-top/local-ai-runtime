# Review Contract

## 目的

定义 heterogeneous review 的正式输出协议。

## 当前事实边界

- 当前 repo-side review gate 发生在 worker + verification 之后；命中时正式结果停在 `needs_review`
- 当前 live `Claude Code + GLM-5.2` reviewer 已可在配置 `review_worker_profile = claude_glm_review` 的 host_local review path 上 materialize bounded blocking receipt；它基于 runtime status、verification gates、changed files、bounded patch summary 与 primary worker output summary 运行，并仍把正式结果停在 `needs_review`
- `review_result.json` 当前可能是 live heterogeneous reviewer receipt，也可能是在 sidecar 缺 summary / 失败 / 返回无效 payload 时的 repo-side blocking fallback receipt；fallback receipt 只表达 repo-side gate 为什么阻断
- `host-orchestrator --record-review-disposition <task_id> --review-disposition approve|revise|reject` 当前只对 `needs_review` 任务生效；它记录 repo-side disposition，不创建真实 operator approval evidence，也不声明 live accepted
- 低风险写任务当前默认自动推进，不因 `write_access = true` 单独触发 blocking review
- medium/high/critical 风险、`touches_policy_surface = true`、以及 `user_forced_review = true` 当前都会阻断下游 flow
- 当前 live review sidecar 在 isolated temp cwd 中以 `--bare --no-session-persistence` 运行；diff context 只来自当前 git-backed host_local write-boundary guard，不等于 approval / merge、真实 remote/vm runner、或 `live accepted`

## 必填字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `task_id` | string | 关联任务 |
| `reviewer_kind` | enum | `claude_glm / codex_review / gpt54_direct_review` |
| `review_mode` | enum | `advisory / blocking` |
| `model` | string | 实际模型名，或 repo-owned policy receipt identifier |
| `risk` | enum | `low / medium / high / critical` |
| `findings` | array | 结构化问题列表 |
| `blocking_reasons` | string[] | 阻断原因 |
| `missing_tests` | string[] | 缺失测试 |
| `recommended_action` | enum | `approve / revise / reject` |
| `source_evidence_refs` | string[] | 审查依据引用 |

## Blocking 规则

当以下任一条件满足时，review 输出必须允许阻断执行链：

- `review_required = true`
- `touches_policy_surface = true`
- `user_forced_review = true`
- `risk_level in {high, critical}`

补充说明：

- `risk_level = medium` 当前在 repo-side gate 上同样会停在 `needs_review`
- `write_access = true` 当前只在风险或 policy surface 已经触发 review 时写入阻断原因，不是单独触发 blocking 的充分条件
- `review_disposition = revise` 当前通过 `attempt + retry_rewind=worker_execution` 进入 rework；`review_disposition = approve` 只关闭 repo-side review hold，仍保留 live acceptance 边界
- 跨仓任务仍属于 future review routing 候选条件，当前不应写成“已 live materialize”

## 示例

```json
{
  "task_id": "TASK-20260706-vertical-slice",
  "reviewer_kind": "codex_review",
  "review_mode": "blocking",
  "model": "repo_policy_gate",
  "risk": "medium",
  "findings": [
    {
      "severity": "medium",
      "category": "review_gate",
      "title": "Repo-side blocking review required before downstream use",
      "detail": "The repo-side review gate derived blocking reasons before downstream use and wrote a machine-readable receipt. This does not imply that a live heterogeneous reviewer already ran.",
      "suggested_fix": "Produce a downstream review decision or explicit operator disposition before downstream use."
    }
  ],
  "blocking_reasons": [
    "risk_level=medium",
    "write_access=true"
  ],
  "missing_tests": [],
  "recommended_action": "revise",
  "source_evidence_refs": [
    ".ai/runs/<run_id>/<task_id>/result.json",
    ".ai/runs/<run_id>/<task_id>/dispatch_state.json",
    ".ai/runs/<run_id>/<task_id>/verification_summary.json"
  ]
}
```
