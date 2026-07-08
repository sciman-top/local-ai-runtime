from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import subprocess

import pytest
import yaml

from host_orchestrator.cli import main as cli_main
from host_orchestrator.config_runtime import load_runtime_config
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.runtime_v2 import admission, storage
from host_orchestrator.runtime_v2.contracts import RuntimeV2TaskError, load_task, write_task
from host_orchestrator.runtime_v2.migration import (
    perform_cutover,
    run_cutover_drill,
    run_cutover_rollback_drill,
    run_cutover_review,
    write_migration_manifest,
)
from host_orchestrator.runtime_v2.runner import RuntimeV2Config, RuntimeV2Runner
from host_orchestrator.worker import WorkerRequest, WorkerResult

from support import REPO_ROOT, copy_runtime_config, runtime_v2_task_payload


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


def _runtime_v2_db(layout: RuntimeLayout) -> Path:
    return layout.with_runtime_v2_paths(
        control_plane_db_v2=".ai/state/control-plane-v2.db",
        artifact_root_v2=".ai/runs-v2",
    ).control_plane_v2_db


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


def _init_git_repo(repo_root: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Runtime V2 Test"], cwd=repo_root, check=True)
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-m", "seed runtime v2 test repo"], cwd=repo_root, check=True, capture_output=True, text=True)


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


def test_repo_runtime_v2_experimental_lane_is_enabled_without_default_cutover() -> None:
    bundle = load_runtime_config(REPO_ROOT)

    assert bundle.runtime.active_version == "v1"
    assert bundle.runtime.experimental_v2_enabled is True


def test_runtime_v2_live_coding_probe_fixture_is_safe_and_loadable() -> None:
    task_path = (
        REPO_ROOT
        / "runtime"
        / "host-orchestrator"
        / "fixtures"
        / "runtime-v2"
        / "tasks"
        / "T-20260708-000001-live-coding-probe.yaml"
    )

    task = load_task(task_path)

    assert task.task_id == "T-20260708-000001-LIVE-CODING-PROBE"
    assert task.worker_profile == "local_maint"
    assert task.verification_profile == "fast"
    assert task.continuation_policy == "auto"
    assert task.risk_level == "low"
    assert task.write_access is True
    assert task.requires_network is False
    assert task.requires_gui is False
    assert task.allowed_paths == (
        "runtime/host-orchestrator/fixtures/runtime-v2/live-coding-probe-output.md",
    )


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
        task_columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(tasks)").fetchall()
        }
        columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(task_attempts)").fetchall()
        }

    assert "task_path" in task_columns
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


def test_runtime_v2_dependency_block_writes_regression_fixture(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_id = "TASK-RUNTIME-V2-DEPENDENCY-FIXTURE"
    task_path = _write_v2_task(
        repo_root,
        task_id,
        updates={"dependency_refs": ["TASK-UPSTREAM"]},
    )
    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-dependency-fixture"),
        worker=_StaticWorker("must not run"),
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    fixture_payload = json.loads((result_path.parent / "regression_fixture.json").read_text(encoding="utf-8"))
    with sqlite3.connect(_runtime_v2_db(layout)) as connection:
        artifact_row = connection.execute(
            "SELECT path FROM artifacts WHERE attempt_id = ? AND kind = 'regression_fixture'",
            (result_payload["attempt_id"],),
        ).fetchone()

    assert result_payload["status"] == "blocked"
    assert result_payload["regression_fixture_ref"].endswith("/regression_fixture.json")
    assert fixture_payload["schema_version"] == "runtime_v2_regression_fixture.v1"
    assert fixture_payload["status"] == "blocked"
    assert fixture_payload["next_action"] == "complete_dependencies_then_retry"
    assert fixture_payload["dependency_refs"] == ["TASK-UPSTREAM"]
    assert fixture_payload["gate_status"] == "blocked"
    assert fixture_payload["artifact_refs"]["result"].endswith("/result.json")
    assert artifact_row == (result_payload["regression_fixture_ref"],)


def test_runtime_v2_pre_worker_policy_guard_blocks_network_requirement(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_id = "TASK-RUNTIME-V2-NETWORK-GUARD"
    task_path = _write_v2_task(
        repo_root,
        task_id,
        updates={"requires_network": True},
    )

    class UnexpectedWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            raise AssertionError("policy-guarded task must not execute a worker")

    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-network-guard"),
        worker=UnexpectedWorker(),
    )

    result_path = runner.run_task(task_path)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    gate_report = json.loads((result_path.parent / "gate_report.json").read_text(encoding="utf-8"))
    attempt = storage.load_attempt(
        layout.with_runtime_v2_paths(
            control_plane_db_v2=".ai/state/control-plane-v2.db",
            artifact_root_v2=".ai/runs-v2",
        ).control_plane_v2_db,
        attempt_id=payload["attempt_id"],
    )

    assert payload["status"] == "blocked"
    assert payload["next_action"] == "resolve_policy_guard_then_retry"
    assert payload["status_reason"] == "pre_worker_policy_guard blocked task execution"
    assert payload["policy_guard_reasons"] == [
        {
            "category": "network",
            "detail": "requires_network=true but worker_profile.network_profile=off",
        }
    ]
    assert gate_report["policy_guard"]["status"] == "blocked"
    assert gate_report["policy_guard"]["blocking_reasons"] == payload["policy_guard_reasons"]
    assert attempt.state == "blocked"


def test_runtime_v2_pre_worker_policy_guard_blocks_non_host_local_profile(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_id = "TASK-RUNTIME-V2-LANE-GUARD"
    task_path = _write_v2_task(
        repo_root,
        task_id,
        updates={"worker_profile": "remote_non_gui_probe"},
    )

    class UnexpectedWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            raise AssertionError("non-host-local runtime_v2 task must not execute a worker")

    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-lane-guard"),
        worker=UnexpectedWorker(),
    )

    result_path = runner.run_task(task_path)
    payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert payload["status"] == "blocked"
    assert payload["next_action"] == "resolve_policy_guard_then_retry"
    assert payload["policy_guard_reasons"] == [
        {
            "category": "worker_lane",
            "detail": "worker_profile.lane=remote_non_gui is not wired for runtime_v2 primary execution",
        }
    ]


def test_runtime_v2_pre_worker_policy_guard_blocks_sensitive_write_scope(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_id = "TASK-RUNTIME-V2-SENSITIVE-GUARD"
    task_path = _write_v2_task(
        repo_root,
        task_id,
        updates={
            "write_access": True,
            "allowed_paths": [".env"],
            "forbidden_paths": [],
        },
    )

    class UnexpectedWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            raise AssertionError("sensitive-scope runtime_v2 task must not execute a worker")

    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-sensitive-guard"),
        worker=UnexpectedWorker(),
    )

    result_path = runner.run_task(task_path)
    payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert payload["status"] == "blocked"
    assert payload["next_action"] == "resolve_policy_guard_then_retry"
    assert payload["policy_guard_reasons"] == [
        {
            "category": "sensitive_path",
            "detail": "write-scoped allowed_paths overlap sensitive_paths: .env",
        }
    ]


def test_runtime_v2_pre_worker_policy_guard_blocks_gui_requirement(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_id = "TASK-RUNTIME-V2-GUI-GUARD"
    task_path = _write_v2_task(
        repo_root,
        task_id,
        updates={"requires_gui": True},
    )

    class UnexpectedWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            raise AssertionError("GUI runtime_v2 task must not execute before vm_gui runner wiring")

    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-gui-guard"),
        worker=UnexpectedWorker(),
    )

    result_path = runner.run_task(task_path)
    payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert payload["status"] == "blocked"
    assert payload["next_action"] == "resolve_policy_guard_then_retry"
    assert payload["policy_guard_reasons"] == [
        {
            "category": "gui",
            "detail": "requires_gui=true but runtime_v2 has no vm_gui primary runner wiring",
        }
    ]


def test_runtime_v2_policy_guard_block_writes_regression_fixture(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_id = "TASK-RUNTIME-V2-GUARD-FIXTURE"
    task_path = _write_v2_task(
        repo_root,
        task_id,
        updates={"requires_network": True},
    )
    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-guard-fixture"),
        worker=_StaticWorker("must not run"),
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    fixture_payload = json.loads((result_path.parent / "regression_fixture.json").read_text(encoding="utf-8"))

    assert result_payload["status"] == "blocked"
    assert result_payload["regression_fixture_ref"].endswith("/regression_fixture.json")
    assert fixture_payload["schema_version"] == "runtime_v2_regression_fixture.v1"
    assert fixture_payload["status"] == "blocked"
    assert fixture_payload["next_action"] == "resolve_policy_guard_then_retry"
    assert fixture_payload["review_required"] is False
    assert fixture_payload["policy_guard_reasons"] == result_payload["policy_guard_reasons"]
    assert fixture_payload["artifact_refs"]["result"].endswith("/result.json")


def test_runtime_v2_admission_pause_writes_regression_fixture(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    db_path = _runtime_v2_db(layout)
    storage.initialize_control_plane_v2(db_path)
    admission.acquire_slot(
        db_path,
        worker_profile="local_maint",
        max_slots=1,
        attempt_id="external-active-attempt",
        worker_id="external-worker",
        acquired_at="2026-07-08T00:00:00Z",
    )
    task_id = "TASK-RUNTIME-V2-ADMISSION-FIXTURE"
    task_path = _write_v2_task(repo_root, task_id)
    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-admission-fixture"),
        worker=_StaticWorker("must not run"),
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    fixture_payload = json.loads((result_path.parent / "regression_fixture.json").read_text(encoding="utf-8"))
    with sqlite3.connect(db_path) as connection:
        artifact_row = connection.execute(
            "SELECT path FROM artifacts WHERE attempt_id = ? AND kind = 'regression_fixture'",
            (result_payload["attempt_id"],),
        ).fetchone()

    assert result_payload["status"] == "paused"
    assert result_payload["next_action"] == "wait_for_available_worker_slot"
    assert result_payload["regression_fixture_ref"].endswith("/regression_fixture.json")
    assert fixture_payload["status"] == "paused"
    assert fixture_payload["next_action"] == "wait_for_available_worker_slot"
    assert fixture_payload["execution_profile"] == "admission_wait"
    assert fixture_payload["gate_status"] == "paused"
    assert artifact_row == (result_payload["regression_fixture_ref"],)


def test_runtime_v2_runner_auto_continues_blocked_task_after_dependencies_complete(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    upstream_path = _write_v2_task(repo_root, "TASK-RUNTIME-V2-UPSTREAM")
    downstream_path = _write_v2_task(
        repo_root,
        "TASK-RUNTIME-V2-DOWNSTREAM",
        updates={"dependency_refs": ["TASK-RUNTIME-V2-UPSTREAM"]},
    )
    manual_blocked_path = _write_v2_task(repo_root, "TASK-RUNTIME-V2-MANUAL-BLOCK")
    worker = _StaticWorker()
    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-auto-continue"),
        worker=worker,
    )

    blocked_result_path = runner.run_task(downstream_path)
    blocked_payload = json.loads(blocked_result_path.read_text(encoding="utf-8"))
    assert blocked_payload["status"] == "blocked"

    upstream_result_path = runner.run_task(upstream_path)
    upstream_payload = json.loads(upstream_result_path.read_text(encoding="utf-8"))
    assert upstream_payload["status"] == "completed"

    db_path = layout.with_runtime_v2_paths(
        control_plane_db_v2=".ai/state/control-plane-v2.db",
        artifact_root_v2=".ai/runs-v2",
    ).control_plane_v2_db
    storage.upsert_task(
        db_path,
        task_id="TASK-RUNTIME-V2-MANUAL-BLOCK",
        task_path=".ai/not-a-runnable-task.yaml",
        title="Manual block",
        risk_level="low",
        worker_profile="local_maint",
        verification_profile="fast",
        continuation_policy="auto",
        write_access=True,
        requires_network=False,
        requires_gui=False,
        status="blocked",
        status_reason="manual review hold",
        created_at="2026-07-08T00:00:00Z",
        updated_at="2026-07-08T00:00:00Z",
    )

    continued_paths = runner.run_ready_blocked_tasks()

    assert len(continued_paths) == 1
    continued_payload = json.loads(continued_paths[0].read_text(encoding="utf-8"))
    assert continued_payload["task_id"] == "TASK-RUNTIME-V2-DOWNSTREAM"
    assert continued_payload["attempt_number"] == 2
    assert continued_payload["status"] == "completed"
    assert len(worker.requests) == 2
    assert manual_blocked_path.exists()


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


def test_runtime_v2_completed_attempt_writes_regression_fixture(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_id = "TASK-RUNTIME-V2-REGRESSION-FIXTURE"
    task_path = _write_v2_task(repo_root, task_id)
    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-regression-fixture"),
        worker=_StaticWorker("fixture worker output"),
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    fixture_path = result_path.parent / "regression_fixture.json"
    fixture_payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    db_path = layout.with_runtime_v2_paths(
        control_plane_db_v2=".ai/state/control-plane-v2.db",
        artifact_root_v2=".ai/runs-v2",
    ).control_plane_v2_db
    with sqlite3.connect(db_path) as connection:
        artifact_row = connection.execute(
            "SELECT path FROM artifacts WHERE attempt_id = ? AND kind = 'regression_fixture'",
            (result_payload["attempt_id"],),
        ).fetchone()

    assert result_payload["regression_fixture_ref"] == (
        f".ai/runs-v2/{result_payload['run_id']}/{task_id}/{result_payload['attempt_id']}/regression_fixture.json"
    )
    assert fixture_payload["schema_version"] == "runtime_v2_regression_fixture.v1"
    assert fixture_payload["task_id"] == task_id
    assert fixture_payload["attempt_id"] == result_payload["attempt_id"]
    assert fixture_payload["status"] == "completed"
    assert fixture_payload["next_action"] == "none"
    assert fixture_payload["artifact_refs"]["result"] == result_payload["regression_fixture_ref"].replace(
        "regression_fixture.json",
        "result.json",
    )
    assert fixture_payload["artifact_refs"]["gate_report"].endswith("/gate_report.json")
    assert fixture_payload["artifact_refs"]["trace_manifest"].endswith("/trace_manifest.json")
    assert fixture_payload["review_required"] is False
    assert fixture_payload["policy_guard_reasons"] == []
    assert artifact_row == (result_payload["regression_fixture_ref"],)


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
    assert review_payload["blocking_reasons"] == [
        {
            "category": "risk_level",
            "detail": "risk_level=medium is listed in continuation_policy.review_on_risk_levels",
        }
    ]
    assert review_payload["gate_failed"] is False
    assert review_payload["policy_surface_touched"] is False


def test_runtime_v2_review_receipt_records_policy_surface_reason(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    _init_git_repo(repo_root)
    task_id = "TASK-RUNTIME-V2-POLICY-REVIEW"
    task_path = _write_v2_task(
        repo_root,
        task_id,
        updates={
            "allowed_paths": ["AGENTS.md", "runtime/host-orchestrator/**"],
            "write_access": True,
        },
    )

    class PolicySurfaceWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            (request.cwd / "AGENTS.md").write_text("updated policy surface\n", encoding="utf-8")
            return WorkerResult(final_response="POLICY_SURFACE_UPDATED", raw_result={"kind": "fake"})

    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout),
        worker=PolicySurfaceWorker(),
    )

    result_path = runner.run_task(task_path)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    review_payload = json.loads((result_path.parent / "sidecars" / "review_result.json").read_text(encoding="utf-8"))

    assert payload["status"] == "reviewing"
    assert payload["next_action"] == "review_task_artifacts"
    assert review_payload["blocking_reasons"] == [
        {
            "category": "policy_surface",
            "detail": "changed paths match policy_surface_globs",
        }
    ]
    assert "AGENTS.md" in review_payload["changed_paths"]
    assert review_payload["gate_failed"] is False
    assert review_payload["policy_surface_touched"] is True


def test_runtime_v2_review_sidecar_materializes_bounded_receipt(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_id = "TASK-RUNTIME-V2-SIDECAR-REVIEW"
    task_path = _write_v2_task(
        repo_root,
        task_id,
        updates={
            "risk_level": "medium",
            "continuation_policy": "guarded",
        },
    )
    review_requests: list[WorkerRequest] = []

    class FakeReviewWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            review_requests.append(request)
            assert "Return a blocking runtime_v2 review receipt" in request.prompt
            assert "Runtime V2 sidecar target summary" in request.prompt
            assert "Runtime V2 primary worker changed scheduling policy receipts." in request.prompt
            return WorkerResult(
                final_response=json.dumps(
                    {
                        "reviewer_kind": "claude_glm",
                        "review_mode": "blocking",
                        "findings": [
                            {
                                "severity": "medium",
                                "category": "heterogeneous_review",
                                "title": "Review sidecar wants inspection",
                                "detail": "The sidecar recorded a bounded second opinion for the v2 review-gated task.",
                                "suggested_fix": "Inspect the sidecar receipt before downstream use.",
                            }
                        ],
                        "blocking_reasons": ["heterogeneous_second_opinion_required"],
                        "missing_tests": [],
                        "recommended_action": "revise",
                        "summary": "Bounded runtime_v2 sidecar review materialized.",
                    }
                ),
                raw_result={"kind": "review"},
            )

    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-sidecar-review"),
        worker=_StaticWorker("Runtime V2 primary worker changed scheduling policy receipts."),
        review_worker=FakeReviewWorker(),
    )

    result_path = runner.run_task(task_path)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    review_payload = json.loads((result_path.parent / "sidecars" / "review_result.json").read_text(encoding="utf-8"))

    assert payload["status"] == "paused"
    assert len(review_requests) == 1
    assert review_payload["sidecar_status"] == "materialized"
    assert review_payload["reviewer_kind"] == "claude_glm"
    assert review_payload["model"] == "glm-5.2"
    assert review_payload["findings"][0]["category"] == "heterogeneous_review"
    assert review_payload["sidecar_blocking_reasons"] == ["heterogeneous_second_opinion_required"]
    assert review_payload["blocking_reasons"][0]["category"] == "risk_level"


def test_runtime_v2_review_sidecar_reviewer_kind_follows_profile(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    workers_path = repo_root / ".ai" / "config" / "workers.yaml"
    workers_payload = yaml.safe_load(workers_path.read_text(encoding="utf-8"))
    workers_payload["workers"]["claude_glm_review"]["worker_kind"] = "codex_sdk"
    workers_payload["workers"]["claude_glm_review"]["model"] = "gpt-5.4"
    workers_path.write_text(
        yaml.safe_dump(workers_payload, allow_unicode=False, sort_keys=False),
        encoding="utf-8",
    )
    task_id = "TASK-RUNTIME-V2-SIDECAR-PROFILE"
    task_path = _write_v2_task(
        repo_root,
        task_id,
        updates={
            "risk_level": "medium",
            "continuation_policy": "guarded",
        },
    )

    class CodexReviewWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            assert "Use reviewer_kind codex_review" in request.prompt
            return WorkerResult(
                final_response=json.dumps(
                    {
                        "review_mode": "blocking",
                        "findings": [],
                        "blocking_reasons": ["codex_review_required"],
                        "missing_tests": [],
                        "recommended_action": "revise",
                        "summary": "Codex review receipt materialized.",
                    }
                ),
                raw_result={"kind": "review"},
            )

    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-sidecar-profile"),
        worker=_StaticWorker("Runtime V2 primary worker changed guarded task."),
        review_worker=CodexReviewWorker(),
    )

    result_path = runner.run_task(task_path)
    review_payload = json.loads((result_path.parent / "sidecars" / "review_result.json").read_text(encoding="utf-8"))

    assert review_payload["sidecar_status"] == "materialized"
    assert review_payload["reviewer_kind"] == "codex_review"
    assert review_payload["model"] == "gpt-5.4"
    assert review_payload["sidecar_blocking_reasons"] == ["codex_review_required"]


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


def test_runtime_v2_worker_failure_writes_regression_fixture(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_id = "TASK-RUNTIME-V2-WORKER-FAIL-FIXTURE"
    task_path = _write_v2_task(repo_root, task_id)
    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-worker-fail-fixture"),
        worker=_FailingWorker(),
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    fixture_payload = json.loads((result_path.parent / "regression_fixture.json").read_text(encoding="utf-8"))
    with sqlite3.connect(_runtime_v2_db(layout)) as connection:
        artifact_row = connection.execute(
            "SELECT path FROM artifacts WHERE attempt_id = ? AND kind = 'regression_fixture'",
            (result_payload["attempt_id"],),
        ).fetchone()

    assert result_payload["status"] == "retryable"
    assert result_payload["next_action"] == "retry_from_worker_execution"
    assert result_payload["regression_fixture_ref"].endswith("/regression_fixture.json")
    assert fixture_payload["status"] == "retryable"
    assert fixture_payload["gate_status"] == "retryable"
    assert fixture_payload["artifact_refs"]["result"].endswith("/result.json")
    assert artifact_row == (result_payload["regression_fixture_ref"],)


def test_runtime_v2_retry_attempt_writes_queued_regression_fixture(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_id = "TASK-RUNTIME-V2-RETRY-FIXTURE"
    task_path = _write_v2_task(repo_root, task_id)
    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-retry-fixture"),
        worker=_FailingWorker(),
    )
    failed_result_path = runner.run_task(task_path)
    failed_payload = json.loads(failed_result_path.read_text(encoding="utf-8"))

    retry_payload = runner.retry_attempt(
        attempt_id=failed_payload["attempt_id"],
        retry_rewind="worker_execution",
        reason="retry fixture coverage",
    )
    retry_fixture_path = (
        repo_root
        / ".ai"
        / "runs-v2"
        / failed_payload["run_id"]
        / task_id
        / retry_payload["new_attempt_id"]
        / "regression_fixture.json"
    )
    fixture_payload = json.loads(retry_fixture_path.read_text(encoding="utf-8"))
    with sqlite3.connect(_runtime_v2_db(layout)) as connection:
        artifact_row = connection.execute(
            "SELECT path FROM artifacts WHERE attempt_id = ? AND kind = 'regression_fixture'",
            (retry_payload["new_attempt_id"],),
        ).fetchone()

    assert retry_payload["state"] == "queued"
    assert retry_payload["regression_fixture_ref"].endswith("/regression_fixture.json")
    assert fixture_payload["status"] == "queued"
    assert fixture_payload["next_action"] == "rerun_attempt"
    assert fixture_payload["retry_rewind"] == "worker_execution"
    assert fixture_payload["source_attempt_id"] == failed_payload["attempt_id"]
    assert fixture_payload["artifact_refs"]["result"] is None
    assert artifact_row == (retry_payload["regression_fixture_ref"],)


def test_runtime_v2_regression_fixture_eval_summary_and_cli(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    completed_task_path = _write_v2_task(repo_root, "TASK-RUNTIME-V2-EVAL-COMPLETE")
    blocked_task_path = _write_v2_task(
        repo_root,
        "TASK-RUNTIME-V2-EVAL-BLOCKED",
        updates={"dependency_refs": ["TASK-UPSTREAM"]},
    )
    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-eval"),
        worker=_StaticWorker("eval fixture worker output"),
    )
    runner.run_task(completed_task_path)
    runner.run_task(blocked_task_path)

    from host_orchestrator.runtime_v2.evaluation import evaluate_regression_fixtures

    summary = evaluate_regression_fixtures(
        layout=layout.with_runtime_v2_paths(
            control_plane_db_v2=".ai/state/control-plane-v2.db",
            artifact_root_v2=".ai/runs-v2",
        )
    )
    summary_path = Path(summary["summary_path"])
    summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["schema_version"] == "runtime_v2_regression_eval.v1"
    assert summary["ok"] is True
    assert summary["fixture_count"] == 2
    assert summary["invalid_fixture_count"] == 0
    assert summary["missing_fixture_count"] == 0
    assert summary["status_counts"] == {"blocked": 1, "completed": 1}
    assert summary_payload["fixture_count"] == 2

    assert cli_main(["--repo-root", str(repo_root), "--eval-regression-fixtures-v2"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    assert cli_payload["schema_version"] == "runtime_v2_regression_eval.v1"
    assert cli_payload["ok"] is True
    assert cli_payload["fixture_count"] == 2
    assert cli_payload["summary_path"].endswith("regression-fixture-summary.json")


def test_runtime_v2_cutover_drill_blocks_without_completed_attempt_and_eval_summary(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)

    summary = run_cutover_drill(
        layout=layout.with_runtime_v2_paths(
            control_plane_db_v2=".ai/state/control-plane-v2.db",
            artifact_root_v2=".ai/runs-v2",
        )
    )
    summary_payload = json.loads(Path(summary["summary_path"]).read_text(encoding="utf-8"))
    orchestrator_payload = yaml.safe_load(
        (repo_root / ".ai" / "config" / "orchestrator.yaml").read_text(encoding="utf-8")
    )

    assert summary["schema_version"] == "runtime_v2_cutover_drill.v1"
    assert summary["status"] == "blocked"
    assert summary["ready"] is False
    assert summary["cutover_performed"] is False
    assert "completed_v2_attempt" in summary["blocking_reasons"]
    assert "regression_fixture_eval" in summary["blocking_reasons"]
    assert summary_payload["status"] == "blocked"
    assert orchestrator_payload["runtime"]["active_version"] == "v1"


def test_runtime_v2_cutover_drill_ready_after_completed_attempt_and_eval_summary(tmp_path: Path) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_path = _write_v2_task(repo_root, "TASK-RUNTIME-V2-CUTOVER-DRILL")
    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-cutover-drill"),
        worker=_StaticWorker("cutover drill worker output"),
    )
    runner.run_task(task_path)

    summary = run_cutover_drill(
        layout=layout.with_runtime_v2_paths(
            control_plane_db_v2=".ai/state/control-plane-v2.db",
            artifact_root_v2=".ai/runs-v2",
        )
    )

    assert summary["status"] == "ready"
    assert summary["ready"] is True
    assert summary["cutover_performed"] is False
    assert summary["blocking_reasons"] == []
    check_statuses = {check["name"]: check["status"] for check in summary["checks"]}
    assert check_statuses["runtime_v2_enabled"] == "pass"
    assert check_statuses["default_entrypoint_still_v1"] == "pass"
    assert check_statuses["completed_v2_attempt"] == "pass"
    assert check_statuses["regression_fixture_eval"] == "pass"


def test_runtime_v2_cli_cutover_fails_closed_until_drill_ready(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root, _ = _seed_repo(tmp_path)

    exit_code = cli_main(["--repo-root", str(repo_root), "--cutover-v2"])
    payload = json.loads(capsys.readouterr().out)
    orchestrator_payload = yaml.safe_load(
        (repo_root / ".ai" / "config" / "orchestrator.yaml").read_text(encoding="utf-8")
    )

    assert exit_code == 1
    assert payload["schema_version"] == "runtime_v2_cutover_drill.v1"
    assert payload["status"] == "blocked"
    assert payload["cutover_performed"] is False
    assert orchestrator_payload["runtime"]["active_version"] == "v1"


def test_runtime_v2_cutover_review_requires_manual_confirmation_after_drill_ready(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_path = _write_v2_task(repo_root, "TASK-RUNTIME-V2-CUTOVER-REVIEW")
    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-cutover-review"),
        worker=_StaticWorker("cutover review worker output"),
    )
    runner.run_task(task_path)

    review = run_cutover_review(
        layout=layout.with_runtime_v2_paths(
            control_plane_db_v2=".ai/state/control-plane-v2.db",
            artifact_root_v2=".ai/runs-v2",
        )
    )
    review_payload = json.loads(Path(review["summary_path"]).read_text(encoding="utf-8"))

    assert review["schema_version"] == "runtime_v2_cutover_review.v1"
    assert review["status"] == "manual_approval_required"
    assert review["manual_approval_required"] is True
    assert review["cutover_performed"] is False
    assert review["drill_ready"] is True
    assert review_payload["rollback_plan"]["restore_active_version"] == "v1"
    assert ".ai/config/orchestrator.yaml" in review["prospective_changes"]

    exit_code = cli_main(["--repo-root", str(repo_root), "--cutover-v2"])
    payload = json.loads(capsys.readouterr().out)
    orchestrator_payload = yaml.safe_load(
        (repo_root / ".ai" / "config" / "orchestrator.yaml").read_text(encoding="utf-8")
    )

    assert exit_code == 1
    assert payload["schema_version"] == "runtime_v2_cutover_review.v1"
    assert payload["status"] == "manual_approval_required"
    assert payload["cutover_performed"] is False
    assert orchestrator_payload["runtime"]["active_version"] == "v1"


def test_runtime_v2_cli_cutover_requires_explicit_confirmation_when_review_ready(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_path = _write_v2_task(repo_root, "TASK-RUNTIME-V2-CONFIRMED-CUTOVER")
    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-confirmed-cutover"),
        worker=_StaticWorker("confirmed cutover worker output"),
    )
    runner.run_task(task_path)
    legacy_db = layout.control_plane_db
    legacy_db.parent.mkdir(parents=True, exist_ok=True)
    legacy_db.write_text("legacy-db-stub\n", encoding="utf-8")

    exit_code = cli_main(
        [
            "--repo-root",
            str(repo_root),
            "--cutover-v2",
            "--confirm-cutover-v2",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    orchestrator_payload = yaml.safe_load(
        (repo_root / ".ai" / "config" / "orchestrator.yaml").read_text(encoding="utf-8")
    )

    assert exit_code == 0
    assert payload["active_version"] == "v2"
    assert payload["cutover_review_summary_path"].endswith("cutover-review-summary.json")
    assert payload["archived_db"] is not None
    assert orchestrator_payload["runtime"]["active_version"] == "v2"


def test_runtime_v2_cutover_rollback_drill_validates_restore_path_without_cutover(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root, layout = _seed_repo(tmp_path)
    task_path = _write_v2_task(repo_root, "TASK-RUNTIME-V2-ROLLBACK-DRILL")
    runner = RuntimeV2Runner(
        RuntimeV2Config(workspace_root=repo_root, layout=layout, run_id="runtime-v2-rollback-drill"),
        worker=_StaticWorker("rollback drill worker output"),
    )
    runner.run_task(task_path)

    summary = run_cutover_rollback_drill(
        layout=layout.with_runtime_v2_paths(
            control_plane_db_v2=".ai/state/control-plane-v2.db",
            artifact_root_v2=".ai/runs-v2",
        )
    )
    summary_payload = json.loads(Path(summary["summary_path"]).read_text(encoding="utf-8"))
    check_statuses = {check["name"]: check["status"] for check in summary["checks"]}

    assert summary["schema_version"] == "runtime_v2_cutover_rollback_drill.v1"
    assert summary["status"] == "ready"
    assert summary["rollback_ready"] is True
    assert summary["restore_performed"] is False
    assert summary["cutover_performed"] is False
    assert summary["active_version"] == "v1"
    assert summary["review_summary_path"].endswith("cutover-review-summary.json")
    assert summary_payload["rollback_plan"]["restore_active_version"] == "v1"
    assert check_statuses["review_manual_approval_required"] == "pass"
    assert check_statuses["restore_config_target"] == "pass"
    assert check_statuses["archive_root_available"] == "pass"
    assert check_statuses["default_entrypoint_currently_v1"] == "pass"

    exit_code = cli_main(["--repo-root", str(repo_root), "--cutover-rollback-drill-v2"])
    payload = json.loads(capsys.readouterr().out)
    orchestrator_payload = yaml.safe_load(
        (repo_root / ".ai" / "config" / "orchestrator.yaml").read_text(encoding="utf-8")
    )

    assert exit_code == 0
    assert payload["schema_version"] == "runtime_v2_cutover_rollback_drill.v1"
    assert payload["rollback_ready"] is True
    assert payload["restore_performed"] is False
    assert orchestrator_payload["runtime"]["active_version"] == "v1"


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

    upstream_task_id = "TASK-RUNTIME-V2-CLI-UPSTREAM"
    downstream_task_id = "TASK-RUNTIME-V2-CLI-DOWNSTREAM"
    upstream_task_path = _write_v2_task(repo_root, upstream_task_id)
    downstream_task_path = _write_v2_task(
        repo_root,
        downstream_task_id,
        updates={"dependency_refs": [upstream_task_id]},
    )
    assert cli_main(["--repo-root", str(repo_root), "--run-task-v2", str(downstream_task_path)]) == 0
    blocked_payload = json.loads(capsys.readouterr().out)
    assert blocked_payload["status"] == "blocked"
    assert cli_main(["--repo-root", str(repo_root), "--run-task-v2", str(upstream_task_path)]) == 0
    upstream_payload = json.loads(capsys.readouterr().out)
    assert upstream_payload["status"] == "completed"
    assert cli_main(["--repo-root", str(repo_root), "--run-ready-blocked-v2"]) == 0
    continued_payload = json.loads(capsys.readouterr().out)
    assert continued_payload["continued_count"] == 1
    assert continued_payload["results"][0]["task_id"] == downstream_task_id
    assert continued_payload["results"][0]["status"] == "completed"

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
