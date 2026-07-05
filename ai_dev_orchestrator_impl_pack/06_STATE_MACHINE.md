# 状态机设计

## 任务状态
- `queued`
- `claimed`
- `running`
- `blocked`
- `failed`
- `retrying`
- `done`
- `verified`
- `reviewed`
- `pr_prepared`
- `merge_ready`
- `merged`
- `cleaned`

## 允许的状态迁移
```text
queued -> claimed -> running
running -> done
running -> failed
failed -> retrying -> running
done -> verified
verified -> reviewed
reviewed -> pr_prepared
pr_prepared -> merge_ready
merge_ready -> merged
merged -> cleaned
```

## 最低要求
第一版至少实现：
- `queued`
- `running`
- `failed`
- `done`
- `verified`
- `pr_prepared`

## 任务记录字段
```json
{
  "task_id": "task-001",
  "worker_id": "codex-gpt54-main-01",
  "status": "running",
  "attempt": 1,
  "worktree": "../wt-task-001",
  "branch": "ai/task-001",
  "started_at": "2026-07-05T09:00:00-07:00",
  "finished_at": null,
  "lease_until": "2026-07-05T09:30:00-07:00",
  "artifacts_dir": ".ai/runs/20260705_090000/task-001/"
}
```

## 原则
- 任何异常都必须落地为状态变更或错误日志
- 不允许 silent failure
- 状态更新必须可恢复
