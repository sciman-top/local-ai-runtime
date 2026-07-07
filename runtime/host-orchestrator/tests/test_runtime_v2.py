from __future__ import annotations

import json
from pathlib import Path
import sqlite3

import pytest
import yaml

from host_orchestrator.cli import main as cli_main
from host_orchestrator.config_runtime import load_runtime_config
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.runtime_v2 import storage
from host_orchestrator.runtime_v2.contracts import RuntimeV2TaskError, load_task, write_task
from host_orchestrator.runtime_v2.migration import perform_cutover, write_migration_manifest
from host_orchestrator.runtime_v2.runner import RuntimeV2Config, RuntimeV2Runner
from host_orchestrator.worker import WorkerRequest, WorkerResult

from support import copy_runtime_config, runtime_v2_task_payload


def _seed_repo(tmp_path: Path, *, active_version: str = "v1") -> tuple[Path, RuntimeLayout]:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    copy_runtime_config(repo_root)

    orchestrator_path = repo_root / ".ai" / "config" / "orchestrator.yaml"
    orchestrator_payload = yaml.safe_load(orchestrator_path.read_text(encoding="utf-8"))
    orchestrator_payload["runtime"]["active_version"] = active_version
    orchestrator_payload["runtime"]["experimental_v2_enabled"] = True
    orchestrator_path.write_text(
        yaml.safe_dump(orchestrator_payload, allow_unicode=False, sort_keys=False),
        encoding="utf-8",
    )

    policies_path = repo_root / ".ai" / "config" / "policies.yaml"
    policies_payload = yaml.safe_load(policies_path.read_text(encoding="utf-8"))
    policies_payload["verification_profiles"]["fast"]["test"] = (
        "python -c \"print('V2_FAST_TEST_OK')\""
    )
    policies_payload["verification_profiles"]["fast"]["contract"] = (
        "python -c \"print('V2_FAST_CONTRACT_OK')\""
    )
    policies_payload["verification_profiles"]["full"]["test"] = (
        "python -c \"print('V2_FULL_TEST_OK')\""
    )
    policies_payload["verification_profiles"]["full"]["contract"] = (
        "python -c \"print('V2_FULL_CONTRACT_OK')\""
    )
    policies_payload["verification_profiles"]["full"]["hotspot"] = None
    policies_path.write_text(
        yaml.safe_dump(policies_payload, allow_unicode=False, sort_keys=False),
        encoding="utf-8",
    )

    return repo_root, RuntimeLayout.from_repo_root(repo_root)


def _write_v2_task(
    repo_root: Path,
    task_id: str,
    *,
    updates: dict[str, object] | None = None,
) -> Path:
    task_path = repo_root / "tasks" / f"{task_id}.yaml"
    payload = runtime_v2_task_payload(task_id)
    if updates:
        payload.update(updates)
    write_task(task_path, payload)
    return task_path


class _StaticWorker:
    def __init__(self, final_response: str = "RUNTIME_V2_OK") -> None:
        self.final_response = final_response
        self.requests: list[WorkerRequest] = []

    def run(self, request: WorkerRequest) -> WorkerResult:
        self.requests.append(request)
        return WorkerResult(
            final_response=self.final_response,
            raw_result={"kind": "fake"},
        )


class _FailingWorker:
    def run(self, request: WorkerRequest) -> WorkerResult:
        raise RuntimeError("simulated worker failure")


def test_runtime_config_loads_runtime_v2_sections(tmp_path: Path) -> None:
    repo_root, _ = _seed_repo(tmp_path)

    bundle = load_runtime_config(repo_root)

    assert bundle.runtime.active_version == "v1"
    assert bundle.runtime.experimental_v2_enabled is True
    assert bundle.runtime.control_plane_db_v2 == ".ai/state/control-plane-v2.db"
    assert bundle.runtime.artifact_root_v2 == ".ai/runs-v2"
    assert set(bundle.policies.verification_profiles) >= {"fast", "full"}
    assert set(bundle.policies.continuation_policies) >= {"auto", "guarded"}
    assert "default" in bundle.policies.retry_policies


def test_runtime_v2_task_rejects_legacy_authored_fields(tmp_path: Path) -> None:
    task_path = tmp_path / "task.yaml"
    payload = runtime_v2_task_payload("TASK-RUNTIME-V2-LEGACY")
    payload["depends_on"] = ["TASK-UPSTREAM"]
    write_task(task_path, payload)

    with pytest.raises(RuntimeV2TaskError, match="legacy/derived fields"):
        load_task(task_path)


def test_initialize_control_plane_v2_creates_expected_tables_and_columns(tmp_path: Path) -> None:
    db_path = tmp_path / "control-plane-v2.db"

    storage.initialize_control_plane_v2(db_path)

    assert storage.list_tables(db_path) >= {
        "artifacts",
        "events",
        "leases",
        "task_attempts",
        "task_dependencies",
        "tasks",
    }
    with sqlite3.connect(db_path) as connection:
        columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(task_attempts)").fetchall()
        }

    assert {"resume_point", "retry_rewind"} <= columns


def test_runtime_v2_runner_blocks_on_unresolved_dependencies(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_id = "TASK-RUNTIME-V2-BLOCKED"
    task_path = _write_v2_task(
        repo_root,
        task_id,
        updates={"dependency_refs": ["TASK-UPSTREAM"]},
    )

    class UnexpectedWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            raise AssertionError("blocked task must not execute a worker")

    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-blocked"),
        worker=UnexpectedWorker(),
    )

    result_path = runner.run_task(task_path)
    payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert payload["status"] == "blocked"
    assert payload["next_action"] == "complete_dependencies_then_retry"
    attempt = storage.load_attempt(layout.with_runtime_v2_paths(
        control_plane_db_v2=".ai/state/control-plane-v2.db",
        artifact_root_v2=".ai/runs-v2",
    ).control_plane_v2_db, attempt_id=payload["attempt_id"])
    assert attempt.state == "blocked"


def test_runtime_v2_runner_completes_low_risk_auto_task(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_id = "TASK-RUNTIME-V2-COMPLETE"
    task_path = _write_v2_task(repo_root, task_id)
    worker = _StaticWorker()
    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout),
        worker=worker,
    )

    result_path = runner.run_task(task_path)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    gate_report = json.loads((result_path.parent / "gate_report.json").read_text(encoding="utf-8"))

    assert payload["status"] == "completed"
    assert payload["next_action"] == "none"
    assert payload["verification_profile"] == "fast"
    assert len(worker.requests) == 1
    assert gate_report["status"] == "pass"
    assert [entry["gate"] for entry in gate_report["commands_run"]] == [
        "build",
        "lint",
        "typecheck",
        "test",
        "contract",
        "hotspot",
    ]


def test_runtime_v2_runner_pauses_medium_risk_guarded_task(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_id = "TASK-RUNTIME-V2-GUARDED"
    task_path = _write_v2_task(
        repo_root,
        task_id,
        updates={
            "risk_level": "medium",
            "continuation_policy": "guarded",
        },
    )
    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout),
        worker=_StaticWorker(),
    )

    result_path = runner.run_task(task_path)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    review_payload = json.loads((result_path.parent / "sidecars" / "review_result.json").read_text(encoding="utf-8"))

    assert payload["status"] == "paused"
    assert payload["next_action"] == "review_task_artifacts"
    assert payload["review_result_ref"] == (
        f".ai/runs-v2/{payload['run_id']}/{task_id}/{payload['attempt_id']}/sidecars/review_result.json"
    )
    assert review_payload["review_mode"] == "blocking"


def test_runtime_v2_runner_marks_gate_failure_retryable(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    policies_path = repo_root / ".ai" / "config" / "policies.yaml"
    policies_payload = yaml.safe_load(policies_path.read_text(encoding="utf-8"))
    policies_payload["verification_profiles"]["fast"]["test"] = (
        "python -c \"import sys; sys.exit(2)\""
    )
    policies_path.write_text(
        yaml.safe_dump(policies_payload, allow_unicode=False, sort_keys=False),
        encoding="utf-8",
    )

    task_id = "TASK-RUNTIME-V2-GATE-FAIL"
    task_path = _write_v2_task(repo_root, task_id)
    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout),
        worker=_StaticWorker(),
    )

    result_path = runner.run_task(task_path)
    payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert payload["status"] == "retryable"
    assert payload["next_action"] == "retry_from_verification"


def test_runtime_v2_runner_marks_worker_failure_retryable(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_id = "TASK-RUNTIME-V2-WORKER-FAIL"
    task_path = _write_v2_task(repo_root, task_id)
    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout),
        worker=_FailingWorker(),
    )

    result_path = runner.run_task(task_path)
    payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert payload["status"] == "retryable"
    assert payload["next_action"] == "retry_from_worker_execution"


def test_runtime_v2_cli_run_resume_retry_and_cutover(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_id = "TASK-RUNTIME-V2-CLI"
    task_path = _write_v2_task(repo_root, task_id)

    class FakeRuntimeWorkerFactory:
        def build(self, worker_profile: object) -> object:
            return _StaticWorker("CLI_RUNTIME_V2_OK")

    monkeypatch.setattr("host_orchestrator.cli.RuntimeWorkerFactory", FakeRuntimeWorkerFactory)

    exit_code = cli_main(
        [
            "--repo-root",
            str(repo_root),
            "--run-task-v2",
            str(task_path),
        ]
    )
    run_payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert run_payload["task_id"] == task_id
    assert run_payload["status"] == "completed"

    attempt_id = run_payload["attempt_id"]
    exit_code = cli_main(
        [
            "--repo-root",
            str(repo_root),
            "--resume-task-v2",
            attempt_id,
            "--resume-point",
            "verification",
        ]
    )
    resume_payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert resume_payload == {
        "attempt_id": attempt_id,
        "state": "ready",
        "resume_point": "verification",
    }

    exit_code = cli_main(
        [
            "--repo-root",
            str(repo_root),
            "--retry-task-v2",
            attempt_id,
            "--retry-rewind",
            "worker_execution",
        ]
    )
    retry_payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert retry_payload["source_attempt_id"] == attempt_id
    assert retry_payload["state"] == "queued"

    migration_manifest = write_migration_manifest(layout=layout)
    assert migration_manifest["status"] == "legacy_archived"

    legacy_db = layout.control_plane_db
    legacy_db.parent.mkdir(parents=True, exist_ok=True)
    legacy_db.write_text("legacy-db-stub\n", encoding="utf-8")
    legacy_runs_root = layout.runs_root / "legacy-run" / "TASK-LEGACY"
    legacy_runs_root.mkdir(parents=True, exist_ok=True)
    (legacy_runs_root / "result.json").write_text("{\"status\": \"completed\"}\n", encoding="utf-8")

    cutover_payload = perform_cutover(layout=layout)
    assert cutover_payload["active_version"] == "v2"
    assert cutover_payload["archived_db"] is not None
    assert cutover_payload["archived_runs"] is not None

    orchestrator_payload = yaml.safe_load(
        (repo_root / ".ai" / "config" / "orchestrator.yaml").read_text(encoding="utf-8")
    )
    assert orchestrator_payload["runtime"]["active_version"] == "v2"

    routed_task_id = "TASK-RUNTIME-V2-DEFAULT-ROUTE"
    routed_task_path = _write_v2_task(repo_root, routed_task_id)
    exit_code = cli_main(
        [
            "--repo-root",
            str(repo_root),
            "--run-task",
            str(routed_task_path),
        ]
    )
    routed_payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert routed_payload["task_id"] == routed_task_id
    assert "attempt_id" in routed_payload
    assert routed_payload["status"] == "completed"
