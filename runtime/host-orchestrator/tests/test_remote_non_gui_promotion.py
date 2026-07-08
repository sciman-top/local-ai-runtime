from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from host_orchestrator.cli import main as cli_main
from host_orchestrator.config_runtime import RuntimeConfigError, load_runtime_config
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


def _runner_acceptance_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "non_host_local_runner_acceptance.v1",
        "acceptance_status": "accepted",
        "worker_profile": "remote_non_gui_probe",
        "lane": "remote_non_gui",
        "runner_kind": "codex_exec",
        "accepted_by": "pytest",
        "accepted_at": "2026-07-08T00:00:00Z",
        "acceptance_scope": "fake injected runner coverage only",
        "evidence_refs": [
            "docs/change-evidence/20260708-non-host-local-runner-acceptance-schema.md"
        ],
    }
    payload.update(overrides)
    return payload


def _write_remote_non_gui_acceptance_ref(
    repo_root: Path,
    payload: dict[str, object] | None = None,
) -> str:
    acceptance_ref = "docs/change-evidence/test-remote-non-gui-runner-acceptance.json"
    acceptance_path = repo_root / acceptance_ref
    acceptance_path.parent.mkdir(parents=True, exist_ok=True)
    acceptance_path.write_text(
        json.dumps(payload or _runner_acceptance_payload(), indent=2),
        encoding="utf-8",
    )
    return acceptance_ref


def _mark_remote_non_gui_runner_wired(repo_root: Path) -> None:
    acceptance_ref = _write_remote_non_gui_acceptance_ref(repo_root)
    workers_path = repo_root / ".ai" / "config" / "workers.yaml"
    payload = yaml.safe_load(workers_path.read_text(encoding="utf-8"))
    payload["workers"]["remote_non_gui_probe"]["runner_wired"] = True
    payload["workers"]["remote_non_gui_probe"]["runner_acceptance_ref"] = acceptance_ref
    workers_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def test_non_host_local_runner_wired_requires_acceptance_ref(tmp_path: Path) -> None:
    repo_root = _seed_repo(tmp_path)
    workers_path = repo_root / ".ai" / "config" / "workers.yaml"
    payload = yaml.safe_load(workers_path.read_text(encoding="utf-8"))
    payload["workers"]["remote_non_gui_probe"]["runner_wired"] = True
    workers_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match="runner_acceptance_ref"):
        load_runtime_config(repo_root)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"acceptance_status": "pending"}, "acceptance_status"),
        ({"worker_profile": "other_profile"}, "worker_profile"),
        ({"lane": "vm_gui"}, "lane"),
        ({"runner_kind": "scripted"}, "runner_kind"),
        ({"evidence_refs": []}, "evidence_refs"),
    ],
)
def test_non_host_local_runner_wired_requires_valid_acceptance_payload(
    tmp_path: Path,
    overrides: dict[str, object],
    message: str,
) -> None:
    repo_root = _seed_repo(tmp_path)
    acceptance_ref = _write_remote_non_gui_acceptance_ref(
        repo_root,
        _runner_acceptance_payload(**overrides),
    )
    workers_path = repo_root / ".ai" / "config" / "workers.yaml"
    payload = yaml.safe_load(workers_path.read_text(encoding="utf-8"))
    payload["workers"]["remote_non_gui_probe"]["runner_wired"] = True
    payload["workers"]["remote_non_gui_probe"]["runner_acceptance_ref"] = acceptance_ref
    workers_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=message):
        load_runtime_config(repo_root)


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
    payload["allowed_paths"] = ["README.md"]
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
    handoff_receipt_path = repo_root / result_payload["handoff_receipt_ref"]
    handoff_receipt_payload = json.loads(handoff_receipt_path.read_text(encoding="utf-8"))

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
    assert dispatch_payload["handoff_receipt_ref"] == result_payload["handoff_receipt_ref"]
    assert handoff_receipt_payload["receipt_kind"] == "pre_worker_handoff"
    assert handoff_receipt_payload["status"] == "waiting_handoff"
    assert handoff_receipt_payload["worker_execution_attempted"] is False
    assert handoff_receipt_payload["requested_lane_runner_wired"] is False
    assert handoff_receipt_payload["selected_profile_runner_wired"] is False
    assert handoff_receipt_payload["requested_execution_lane"] == "remote_non_gui"
    assert handoff_receipt_payload["selected_lane"] == "remote_non_gui"
    assert handoff_receipt_payload["worker_profile"] == "remote_non_gui_probe"
    assert "selected_lane_runner_not_wired" in handoff_receipt_payload["reason_codes"]
    assert result_payload["handoff_receipt_ref"] in {
        entry["relative_path"]
        for entry in json.loads((result_path.parent / "evidence_index.json").read_text(encoding="utf-8"))[
            "entries"
        ]
    }


def test_host_local_runner_executes_explicit_remote_non_gui_profile_when_runner_is_wired(
    tmp_path: Path,
) -> None:
    from host_orchestrator.canonical_task import write_task

    repo_root = _seed_repo(tmp_path)
    _mark_remote_non_gui_runner_wired(repo_root)
    task_id = "TASK-20260708-wired-remote-non-gui-profile"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = canonical_task_payload(task_id)
    payload["risk_level"] = "low"
    payload["write_access"] = False
    payload["allowed_paths"] = ["README.md"]
    payload["execution_lane"] = "remote_non_gui"
    payload["requires_network"] = True
    payload["worker_profile"] = "remote_non_gui_probe"
    write_task(task_path, payload)

    class RecordingRemoteWorker:
        def __init__(self) -> None:
            self.requests: list[WorkerRequest] = []

        def run(self, request: WorkerRequest) -> WorkerResult:
            self.requests.append(request)
            return WorkerResult(
                final_response="remote runner fixture completed",
                raw_result={"kind": "remote_non_gui_fixture"},
                stdout_text="remote stdout",
                stderr_text="",
            )

    worker = RecordingRemoteWorker()
    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            run_id="wired-remote-non-gui-profile-test",
        ),
        worker,
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    dispatch_payload = json.loads((result_path.parent / "dispatch_state.json").read_text(encoding="utf-8"))

    assert len(worker.requests) == 1
    assert worker.requests[0].model == "gpt-5.4"
    assert result_payload["status"] == "succeeded"
    assert result_payload["worker_profile"] == "remote_non_gui_probe"
    assert result_payload["lane"] == "remote_non_gui"
    assert result_payload["handoff_required"] is False
    assert result_payload["handoff_receipt_ref"] is None
    assert result_payload["status_reason"] == "task completed within graded autonomy boundary"
    assert dispatch_payload["status"] == "completed"
    assert dispatch_payload["execution_lane"] == "remote_non_gui"
    assert dispatch_payload["worker_profile"] == "remote_non_gui_probe"


def test_wired_remote_non_gui_worker_failure_stays_failed_and_does_not_write_success_result(
    tmp_path: Path,
) -> None:
    from host_orchestrator.canonical_task import write_task

    repo_root = _seed_repo(tmp_path)
    _mark_remote_non_gui_runner_wired(repo_root)
    task_id = "TASK-20260708-wired-remote-non-gui-failure"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = canonical_task_payload(task_id)
    payload["risk_level"] = "low"
    payload["write_access"] = False
    payload["execution_lane"] = "remote_non_gui"
    payload["requires_network"] = True
    payload["worker_profile"] = "remote_non_gui_probe"
    write_task(task_path, payload)

    class FailingRemoteWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            raise RuntimeError("remote runner fixture failed")

    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            run_id="wired-remote-non-gui-failure-test",
        ),
        FailingRemoteWorker(),
    )

    with pytest.raises(RuntimeError, match="remote runner fixture failed"):
        runner.run_task(task_path)

    task_run_root = (
        repo_root
        / ".ai"
        / "runs"
        / "wired-remote-non-gui-failure-test"
        / task_id
    )
    dispatch_payload = json.loads((task_run_root / "dispatch_state.json").read_text(encoding="utf-8"))

    assert dispatch_payload["status"] == "failed"
    assert dispatch_payload["execution_lane"] == "remote_non_gui"
    assert dispatch_payload["worker_profile"] == "remote_non_gui_probe"
    assert dispatch_payload["status_reason"] == "remote runner fixture failed"
    assert not (task_run_root / "result.json").exists()


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
    assert promoted_outcome.handoff_receipt_ref.endswith("/handoff_receipt.json")
    assert "selected_lane_runner_not_wired" in promoted_outcome.handoff_reason_codes
    assert promoted_outcome.worker_execution_attempted is False

    summary_payload = json.loads(summary.summary_path.read_text(encoding="utf-8"))
    assert summary_payload["route_decision_count"] == 2
    assert summary_payload["state_counts"] == {"waiting_handoff": 2}
    summary_outcomes = {item["task_id"]: item for item in summary_payload["task_outcomes"]}
    assert summary_outcomes["TASK-20260707-remote-non-gui-profile-promotion"][
        "handoff_reason_codes"
    ] == promoted_outcome.handoff_reason_codes


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


def test_cli_validates_runner_acceptance_ref_against_worker_profile(
    tmp_path: Path,
    capsys,
) -> None:
    repo_root = _seed_repo(tmp_path)
    acceptance_ref = _write_remote_non_gui_acceptance_ref(repo_root)

    exit_code = cli_main(
        [
            "--repo-root",
            str(repo_root),
            "--worker-profile",
            "remote_non_gui_probe",
            "--validate-runner-acceptance",
            acceptance_ref,
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["status"] == "pass"
    assert payload["acceptance_ref"] == acceptance_ref
    assert payload["worker_profile"] == "remote_non_gui_probe"
    assert payload["lane"] == "remote_non_gui"
    assert payload["runner_kind"] == "codex_exec"
    assert payload["runner_wired"] is False
    assert payload["validation_only"] is True
    assert payload["runner_executed"] is False


def test_cli_runner_acceptance_validation_fails_on_profile_mismatch(
    tmp_path: Path,
    capsys,
) -> None:
    repo_root = _seed_repo(tmp_path)
    acceptance_ref = _write_remote_non_gui_acceptance_ref(repo_root)

    exit_code = cli_main(
        [
            "--repo-root",
            str(repo_root),
            "--worker-profile",
            "vm_gui_probe",
            "--validate-runner-acceptance",
            acceptance_ref,
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 1
    assert payload["status"] == "fail"
    assert payload["acceptance_ref"] == acceptance_ref
    assert payload["worker_profile"] == "vm_gui_probe"
    assert "worker_profile" in payload["error"]
    assert payload["validation_only"] is True
    assert payload["runner_executed"] is False
