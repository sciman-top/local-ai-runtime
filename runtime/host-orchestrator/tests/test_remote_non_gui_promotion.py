from __future__ import annotations

import json
from pathlib import Path

from host_orchestrator.cli import main as cli_main
from host_orchestrator.host_local import HostLocalConfig, HostLocalRunner
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.worker import WorkerRequest, WorkerResult

from support import canonical_task_payload, copy_runtime_config


def _seed_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    copy_runtime_config(repo_root)
    return repo_root


def test_host_local_runner_hands_off_explicit_remote_non_gui_profile_before_worker_execution(
    tmp_path: Path,
) -> None:
    from host_orchestrator.canonical_task import write_task

    repo_root = _seed_repo(tmp_path)
    task_id = "TASK-20260707-explicit-remote-non-gui-profile"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = canonical_task_payload(task_id)
    payload["risk_level"] = "low"
    payload["write_access"] = False
    payload["execution_lane"] = "remote_non_gui"
    payload["requires_network"] = True
    payload["worker_profile"] = "remote_non_gui_probe"
    write_task(task_path, payload)

    class FailIfCalledWorker:
        def __init__(self) -> None:
            self.call_count = 0

        def run(self, request: WorkerRequest) -> WorkerResult:
            self.call_count += 1
            raise AssertionError("remote_non_gui probe profile must hand off before worker execution")

    worker = FailIfCalledWorker()
    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            run_id="explicit-remote-non-gui-profile-test",
        ),
        worker,
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    dispatch_payload = json.loads((result_path.parent / "dispatch_state.json").read_text(encoding="utf-8"))

    assert worker.call_count == 0
    assert result_payload["status"] == "waiting_handoff"
    assert result_payload["worker_profile"] == "remote_non_gui_probe"
    assert result_payload["lane"] == "remote_non_gui"
    assert result_payload["route_reason"] == "repo-owned worker_profile=remote_non_gui_probe selected from canonical task"
    assert "host_runtime=host_local" in result_payload["status_reason"]
    assert "selected_lane=remote_non_gui" in result_payload["status_reason"]
    assert "runner_not_wired" in result_payload["status_reason"]
    assert "worker_profile=remote_non_gui_probe" in result_payload["status_reason"]
    assert "requires_network=true" not in result_payload["status_reason"]
    assert dispatch_payload["worker_profile"] == "remote_non_gui_probe"
    assert dispatch_payload["execution_lane"] == "remote_non_gui"
    assert dispatch_payload["route_reason"] == result_payload["route_reason"]


def test_remote_non_gui_promotion_suite_writes_summary_and_preserves_fail_closed_boundary(
    tmp_path: Path,
) -> None:
    from host_orchestrator.remote_non_gui_promotion import run_remote_non_gui_promotion

    repo_root = _seed_repo(tmp_path)
    summary = run_remote_non_gui_promotion(
        repo_root,
        run_id="remote-non-gui-promotion-test",
    )

    assert summary.ok is True
    assert summary.scenario_count == 2
    assert summary.task_run_count == 2
    assert summary.terminal_task_count == 2
    assert summary.route_decision_count == 2
    assert summary.active_lease_count == 0
    assert summary.state_counts == {"waiting_handoff": 2}
    assert set(summary.worker_statuses.values()) == {"idle"}
    assert set(summary.worker_lanes.values()) == {"host_local", "remote_non_gui"}
    assert summary.summary_path.exists()

    outcomes = {outcome.task_id: outcome for outcome in summary.task_outcomes}
    default_outcome = outcomes["TASK-20260707-remote-non-gui-default-request"]
    assert default_outcome.worker_profile == "local_maint"
    assert default_outcome.final_state == "waiting_handoff"
    assert default_outcome.route_reason == "repo default worker_profile=local_maint selected from orchestrator.yaml"
    assert "execution_lane=remote_non_gui" in default_outcome.status_reason

    promoted_outcome = outcomes["TASK-20260707-remote-non-gui-profile-promotion"]
    assert promoted_outcome.worker_profile == "remote_non_gui_probe"
    assert promoted_outcome.final_state == "waiting_handoff"
    assert promoted_outcome.route_reason == "repo-owned worker_profile=remote_non_gui_probe selected from canonical task"
    assert "host_runtime=host_local" in promoted_outcome.status_reason
    assert "selected_lane=remote_non_gui" in promoted_outcome.status_reason
    assert "runner_not_wired" in promoted_outcome.status_reason
    assert "requires_network=true" not in promoted_outcome.status_reason

    summary_payload = json.loads(summary.summary_path.read_text(encoding="utf-8"))
    assert summary_payload["route_decision_count"] == 2
    assert summary_payload["state_counts"] == {"waiting_handoff": 2}


def test_cli_runs_remote_non_gui_promotion_and_prints_json(
    tmp_path: Path,
    capsys,
) -> None:
    repo_root = _seed_repo(tmp_path)

    exit_code = cli_main(
        [
            "--repo-root",
            str(repo_root),
            "--run-remote-non-gui-promotion",
            "--remote-non-gui-promotion-run-id",
            "remote-non-gui-cli-test",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["scenario_count"] == 2
    assert payload["state_counts"] == {"waiting_handoff": 2}
