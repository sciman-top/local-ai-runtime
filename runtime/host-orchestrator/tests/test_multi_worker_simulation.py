from __future__ import annotations

import json
from pathlib import Path

import pytest

from host_orchestrator.cli import main as cli_main
from support import copy_runtime_config


def _seed_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    copy_runtime_config(repo_root)
    return repo_root


def test_multi_worker_simulation_suite_writes_summary_and_covers_retry_route_and_quota(
    tmp_path: Path,
) -> None:
    try:
        from host_orchestrator.multi_worker_simulation import run_multi_worker_simulation
    except ModuleNotFoundError as exc:
        pytest.fail(f"multi_worker_simulation module missing: {exc}")

    repo_root = _seed_repo(tmp_path)
    summary = run_multi_worker_simulation(
        repo_root,
        run_id="multi-worker-sim-test",
    )

    assert summary.ok is True
    assert summary.scenario_count == 4
    assert summary.task_run_count == 5
    assert summary.terminal_task_count == 4
    assert summary.route_decision_count == 5
    assert summary.retry_event_count == 1
    assert summary.active_lease_count == 0
    assert len(summary.worker_statuses) == 5
    assert set(summary.worker_statuses.values()) == {"idle"}
    assert summary.state_counts == {
        "completed": 2,
        "needs_review": 1,
        "waiting_handoff": 1,
    }
    assert summary.retried_task_ids == ["TASK-20260707-simulation-retry"]
    assert summary.summary_path.exists()

    outcomes = {outcome.task_id: outcome for outcome in summary.task_outcomes}
    assert outcomes["TASK-20260707-simulation-explicit-wave1"].worker_profile == "wave1_smoke"
    assert outcomes["TASK-20260707-simulation-explicit-wave1"].final_state == "completed"
    assert (
        outcomes["TASK-20260707-simulation-explicit-wave1"].route_reason
        == "repo-owned worker_profile=wave1_smoke selected from canonical task"
    )
    assert outcomes["TASK-20260707-simulation-review"].worker_profile == "local_maint"
    assert outcomes["TASK-20260707-simulation-review"].final_state == "needs_review"
    assert (
        outcomes["TASK-20260707-simulation-review"].route_reason
        == "repo default worker_profile=local_maint selected from orchestrator.yaml"
    )
    assert outcomes["TASK-20260707-simulation-quota"].worker_profile == "local_maint"
    assert outcomes["TASK-20260707-simulation-quota"].final_state == "waiting_handoff"
    assert (
        outcomes["TASK-20260707-simulation-quota"].route_reason
        == "repo default worker_profile=local_maint selected from orchestrator.yaml"
    )
    assert "lease_quota_exhausted" in outcomes["TASK-20260707-simulation-quota"].status_reason
    assert outcomes["TASK-20260707-simulation-retry"].worker_profile == "local_maint"
    assert outcomes["TASK-20260707-simulation-retry"].final_state == "completed"
    assert outcomes["TASK-20260707-simulation-retry"].attempt == 2
    assert (
        outcomes["TASK-20260707-simulation-retry"].route_reason
        == "repo default worker_profile=local_maint selected from orchestrator.yaml"
    )

    summary_payload = json.loads(summary.summary_path.read_text(encoding="utf-8"))
    assert summary_payload["retry_event_count"] == 1
    assert summary_payload["route_decision_count"] == 5


def test_cli_runs_multi_worker_simulation_and_prints_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root = _seed_repo(tmp_path)

    exit_code = cli_main(
        [
            "--repo-root",
            str(repo_root),
            "--run-multi-worker-simulation",
            "--multi-worker-simulation-run-id",
            "multi-worker-cli-test",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["scenario_count"] == 4
    assert payload["retry_event_count"] == 1
