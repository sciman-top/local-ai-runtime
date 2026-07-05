# Review Contract

## 目的

定义 heterogeneous review 的正式输出协议。

## 必填字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `task_id` | string | 关联任务 |
| `reviewer_kind` | enum | `claude_glm / codex_review / gpt54_direct_review` |
| `review_mode` | enum | `advisory / blocking` |
| `model` | string | 实际模型名 |
| `risk` | enum | `low / medium / high / critical` |
| `findings` | array | 结构化问题列表 |
| `blocking_reasons` | string[] | 阻断原因 |
| `missing_tests` | string[] | 缺失测试 |
| `recommended_action` | enum | `approve / revise / reject` |
| `source_evidence_refs` | string[] | 审查依据引用 |

## Blocking 规则

当以下任一条件满足时，review 输出必须允许阻断执行链：

- `review_required = true`
- `risk_level in {high, critical}`
- 修改命中 policy surface
- 跨仓任务

## 示例

```json
{
  "task_id": "TASK-20260706-vertical-slice",
  "reviewer_kind": "claude_glm",
  "review_mode": "blocking",
  "model": "glm-5.2",
  "risk": "medium",
  "findings": [
    {
      "severity": "medium",
      "category": "tests",
      "title": "Missing dual-write regression",
      "detail": "The phase 1 runner writes JSON but does not prove the markdown projection still exists.",
      "suggested_fix": "Add a parity assertion for the markdown projection."
    }
  ],
  "blocking_reasons": [
    "review_required"
  ],
  "missing_tests": [
    "projection parity regression"
  ],
  "recommended_action": "revise",
  "source_evidence_refs": [
    ".ai/runs/<run_id>/<task_id>/result.json"
  ]
}
```
