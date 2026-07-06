from __future__ import annotations

import json
from pathlib import Path
import shutil
import sqlite3

import pytest

from host_orchestrator.canonical_task import write_task
from host_orchestrator.host_local import HostLocalConfig, HostLocalRunner
from host_orchestrator.paths import RuntimeLayout


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]


def _copy_runtime_config(repo_root: Path) -> None:
    source_root = REPO_ROOT / ".ai" / "config"
    destination_root = repo_root / ".ai" / "config"
    destination_root.mkdir(parents=True, exist_ok=True)
    for filename in ["orchestrator.yaml", "workers.yaml", "policies.yaml"]:
        shutil.copy2(source_root / filename, destination_root / filename)


def _canonical_task_payload(task_id: str) -> dict[str, object]:
    return {
        "task_id": task_id,
        "title": "Validate host-local canonical runtime",
        "description": "Exercise the canonical task contract through the host-local runner.",
        "target_repo": "local-ai-dev-orchestrator",
        "base_branch": "main",
        "branch_name": "codex/host-local-test",
        "worktree_path": ".",
        "allowed_paths": ["runtime/host-orchestrator/**", "docs/**"],
        "forbidden_paths": [".env", ".env.*", ".git/config"],
        "write_access": True,
        "risk_level": "medium",
        "merge_policy": "manual_merge_only",
        "execution_lane": "host_local",
        "requires_network": False,
        "requires_gui": False,
        "depends_on": [],
        "artifacts_out": [
            f".ai/runs/<run_id>/{task_id}/result.json",
        ],
        "handoff_policy": "handoff_on_risk",
        "verification_commands": {
            "build": None,
            "test": "python -c \"print('TEST_OK')\"",
            "lint": None,
            "typecheck": None,
            "contract": "python -c \"print('CONTRACT_OK')\"",
            "hotspot": None,
        },
    }


def test_host_local_runner_marks_failed_task_and_releases_worker_after_exception(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    _copy_runtime_config(repo_root)

    task_id = "TASK-CRASH-001"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    write_task(task_path, _canonical_task_payload(task_id))

    class FailingWorker:
        def run(self, request) -> object:
            raise RuntimeError("synthetic worker failure")

    layout = RuntimeLayout.from_repo_root(repo_root)
    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=layout,
            run_id="host-local-failure",
            worker_id="worker-crash-test",
        ),
        FailingWorker(),
    )

    with pytest.raises(RuntimeError, match="synthetic worker failure"):
        runner.run_task(task_path)

    with sqlite3.connect(layout.control_plane_db) as connection:
        runtime_task = connection.execute(
            "SELECT state, execution_lane, worker_profile, result_path FROM runtime_tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        worker = connection.execute(
            "SELECT status FROM workers WHERE worker_id = ?",
            ("worker-crash-test",),
        ).fetchone()
        event_rows = connection.execute(
            "SELECT event_type, payload_json FROM events ORDER BY created_at"
        ).fetchall()
        lease_count = connection.execute("SELECT COUNT(*) FROM leases").fetchone()[0]

    assert runtime_task == ("failed", "host_local", "local_maint", None)
    assert worker == ("idle",)
    assert [event_type for (event_type, _) in event_rows] == ["task_started", "task_failed"]
    failed_payload = json.loads(event_rows[1][1])
    assert failed_payload["error_type"] == "RuntimeError"
    assert failed_payload["error_message"] == "synthetic worker failure"
    assert failed_payload["worker_id"] == "worker-crash-test"
    assert lease_count == 0
    assert not (repo_root / ".ai" / "runs" / "host-local-failure" / task_id / "result.json").exists()
