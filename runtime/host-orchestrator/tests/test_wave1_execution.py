from __future__ import annotations

import json
from pathlib import Path
import shutil
import sqlite3

from openai_codex import ApprovalMode, Sandbox
import pytest
import yaml

from host_orchestrator.canonical_task import CanonicalTaskError, load_task as load_canonical_task, write_task
from host_orchestrator import db
from host_orchestrator.cli import main as cli_main
from host_orchestrator.config_runtime import RuntimeConfigError
from host_orchestrator.evidence_index import revalidate_evidence_index
from host_orchestrator.exec_fallback import (
    CodexExecFallbackWorker,
    CommandResult,
    build_exec_argv,
)
from host_orchestrator.host_local import HostLocalConfig, HostLocalRunner
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.wave1_smoke import load_wave1_smoke_samples, run_wave1_smokes
from host_orchestrator.worker import (
    UsageBreakdown,
    WorkerRequest,
    WorkerResult,
    WorkerUsage,
)
from host_orchestrator.worker_factory import RuntimeWorkerFactory, WorkerFactoryError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
FIXTURES_ROOT = PROJECT_ROOT / "fixtures" / "wave1-smokes"


def _copy_runtime_config(repo_root: Path) -> None:
    source_root = REPO_ROOT / ".ai" / "config"
    destination_root = repo_root / ".ai" / "config"
    destination_root.mkdir(parents=True, exist_ok=True)
    for filename in ["orchestrator.yaml", "workers.yaml", "policies.yaml"]:
        shutil.copy2(source_root / filename, destination_root / filename)


def _update_worker_profile_config(
    repo_root: Path,
    profile_name: str,
    updates: dict[str, object],
) -> None:
    workers_path = repo_root / ".ai" / "config" / "workers.yaml"
    payload = yaml.safe_load(workers_path.read_text(encoding="utf-8"))
    payload["workers"][profile_name].update(updates)
    workers_path.write_text(
        yaml.safe_dump(payload, allow_unicode=False, sort_keys=False),
        encoding="utf-8",
    )


def _canonical_task_payload(task_id: str) -> dict[str, object]:
    return {
        "task_id": task_id,
        "title": "Validate host-local canonical runtime",
        "description": "Exercise the canonical task contract through the host-local runner.",
        "target_repo": "local-ai-dev-orchestrator",
        "base_branch": "main",
        "branch_name": "codex/host-local-test",
        "worktree_path": ".",
        "allowed_paths": ["runtime/host-orchestrator/**"],
        "forbidden_paths": [".env", ".env.*", ".git/config"],
        "write_access": False,
        "risk_level": "low",
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


def _run_fake_host_local_task(
    tmp_path: Path,
    *,
    task_id: str,
    task_updates: dict[str, object] | None = None,
) -> tuple[Path, RuntimeLayout, Path, Path]:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    _copy_runtime_config(repo_root)

    agentbridge_root = repo_root / "AgentBridge"
    for name in ["tasks", "results", "artifacts"]:
        (agentbridge_root / name).mkdir(parents=True, exist_ok=True)

    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = _canonical_task_payload(task_id)
    if task_updates is not None:
        payload.update(task_updates)
    write_task(task_path, payload)

    class FakeWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            assert f"task_id: {task_id}" in request.prompt
            return WorkerResult(
                final_response="HOST_LOCAL_OK",
                raw_result={"kind": "fake"},
                usage=WorkerUsage(
                    source="sdk_structured",
                    last=UsageBreakdown(
                        cached_input_tokens=3,
                        input_tokens=120,
                        output_tokens=20,
                        reasoning_output_tokens=6,
                        total_tokens=146,
                    ),
                    total=UsageBreakdown(
                        cached_input_tokens=3,
                        input_tokens=120,
                        output_tokens=20,
                        reasoning_output_tokens=6,
                        total_tokens=146,
                    ),
                    model_context_window=272000,
                ),
            )

    layout = RuntimeLayout.from_repo_root(repo_root)
    runner = HostLocalRunner(
        HostLocalConfig(
            agentbridge_root=agentbridge_root,
            workspace_root=repo_root,
            layout=layout,
            run_id="host-local-test",
        ),
        FakeWorker(),
    )

    result_path = runner.run_task(task_path)
    return repo_root, layout, agentbridge_root, result_path


def test_exec_fallback_builds_expected_codex_exec_command(tmp_path: Path) -> None:
    request = WorkerRequest(
        prompt="Reply with exactly OK.",
        cwd=tmp_path,
        model="gpt-5.4",
        sandbox=Sandbox.workspace_write,
        approval_mode=ApprovalMode.deny_all,
    )
    output_path = tmp_path / "last-message.txt"

    argv = build_exec_argv(request, output_path)

    assert argv == [
        "codex",
        "exec",
        "--json",
        "-C",
        str(tmp_path),
        "-m",
        "gpt-5.4",
        "-s",
        "workspace-write",
        "-c",
        'approval_policy="never"',
        "--output-last-message",
        str(output_path),
        "Reply with exactly OK.",
    ]


def test_exec_fallback_worker_reads_output_last_message(tmp_path: Path) -> None:
    request = WorkerRequest(
        prompt="Reply with exactly OK.",
        cwd=tmp_path,
        model="gpt-5.4",
    )

    class FakeExecutor:
        def run(self, argv: list[str], cwd: Path) -> CommandResult:
            output_index = argv.index("--output-last-message") + 1
            Path(argv[output_index]).write_text("FALLBACK_OK", encoding="utf-8")
            return CommandResult(argv=argv, returncode=0, stdout="", stderr="")

    worker = CodexExecFallbackWorker(executor=FakeExecutor())

    result = worker.run(request)

    assert result.final_response == "FALLBACK_OK"


def test_runtime_worker_factory_reuses_codex_client_for_sdk_workers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from host_orchestrator.config_runtime import WorkerProfile

    created_clients: list[object] = []

    class FakeCodex:
        pass

    def fake_codex_constructor() -> FakeCodex:
        client = FakeCodex()
        created_clients.append(client)
        return client

    monkeypatch.setattr("host_orchestrator.worker_factory.Codex", fake_codex_constructor)

    profile = WorkerProfile(
        name="local_maint",
        worker_kind="codex_sdk",
        lane="host_local",
        model="gpt-5.4",
        provider="openai-codex-sdk",
        sandbox_profile="workspace_write",
        approval_policy="never",
        network_profile="off",
        projection_mode="compatibility_dual_write",
        max_active_leases=1,
    )

    factory = RuntimeWorkerFactory()
    worker_one = factory.build(profile)
    worker_two = factory.build(profile)

    assert worker_one.__class__.__name__ == "CodexSdkWorker"
    assert worker_two.__class__.__name__ == "CodexSdkWorker"
    assert created_clients == [worker_one._codex]
    assert worker_one._codex is worker_two._codex


def test_runtime_worker_factory_builds_exec_fallback_worker() -> None:
    from host_orchestrator.config_runtime import WorkerProfile

    profile = WorkerProfile(
        name="remote_non_gui_probe",
        worker_kind="codex_exec",
        lane="remote_non_gui",
        model="gpt-5.4",
        provider="remote-runner-placeholder",
        sandbox_profile="workspace_write",
        approval_policy="never",
        network_profile="restricted",
        projection_mode="compatibility_dual_write",
        max_active_leases=1,
    )

    worker = RuntimeWorkerFactory().build(profile)

    assert worker.__class__.__name__ == "CodexExecFallbackWorker"


def test_runtime_worker_factory_builds_claude_review_sidecar_worker() -> None:
    from host_orchestrator.config_runtime import WorkerProfile

    profile = WorkerProfile(
        name="claude_glm_review",
        worker_kind="claude_glm",
        lane="host_local",
        model="glm-5.2",
        provider="claude-code-bigmodel-glm",
        sandbox_profile="read_only",
        approval_policy="never",
        network_profile="off",
        projection_mode="compatibility_dual_write",
        max_active_leases=1,
    )

    worker = RuntimeWorkerFactory().build_review_sidecar(profile)

    assert worker.__class__.__name__ == "ClaudeCodeStructuredWorker"


def test_runtime_worker_factory_rejects_unwired_worker_kinds() -> None:
    from host_orchestrator.config_runtime import WorkerProfile

    factory = RuntimeWorkerFactory()
    unsupported_profiles = [
        WorkerProfile(
            name="wave1_smoke",
            worker_kind="scripted",
            lane="host_local",
            model="gpt-5.4",
            provider="wave1-scripted-fake-worker",
            sandbox_profile="workspace_write",
            approval_policy="never",
            network_profile="off",
            projection_mode="compatibility_dual_write",
            max_active_leases=1,
        ),
        WorkerProfile(
            name="direct_planner",
            worker_kind="gpt54_direct",
            lane="host_local",
            model="gpt-5.4",
            provider="direct-gateway-placeholder",
            sandbox_profile="workspace_write",
            approval_policy="never",
            network_profile="restricted",
            projection_mode="compatibility_dual_write",
            max_active_leases=1,
        ),
        WorkerProfile(
            name="claude_glm_review",
            worker_kind="claude_glm",
            lane="host_local",
            model="glm-5.2",
            provider="claude-code-bigmodel-glm",
            sandbox_profile="read_only",
            approval_policy="never",
            network_profile="off",
            projection_mode="compatibility_dual_write",
            max_active_leases=1,
        ),
    ]

    for profile in unsupported_profiles:
        with pytest.raises(WorkerFactoryError):
            factory.build(profile)


def test_initialize_control_plane_creates_expected_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "control-plane.db"

    db.initialize_control_plane(db_path)

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()

    assert {name for (name,) in rows} >= {
        "events",
        "leases",
        "route_decisions",
        "runtime_tasks",
        "workers",
    }


def test_canonical_task_rejects_authored_derived_fields(tmp_path: Path) -> None:
    task_path = tmp_path / "task.json"
    payload = _canonical_task_payload("TASK-20260706-derived-reject")
    payload["planner_required"] = True
    write_task(task_path, payload)

    with pytest.raises(CanonicalTaskError, match="Derived fields must not be authored"):
        load_canonical_task(task_path)


def test_host_local_runner_requires_repo_owned_config(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    task_path = repo_root / "task.json"
    write_task(task_path, _canonical_task_payload("TASK-20260706-missing-config"))

    with pytest.raises(RuntimeConfigError, match="Missing repo-owned runtime config directory"):
        HostLocalRunner(
            HostLocalConfig(
                workspace_root=repo_root,
                layout=RuntimeLayout.from_repo_root(repo_root),
            ),
            worker=type("NoopWorker", (), {"run": lambda self, request: None})(),
        )


def test_host_local_runner_writes_result_and_runtime_state(tmp_path: Path) -> None:
    task_id = "T-20260628-000001-wave1-smoke"
    repo_root, layout, agentbridge_root, result_path = _run_fake_host_local_task(
        tmp_path,
        task_id=task_id,
    )

    assert result_path == repo_root / ".ai" / "runs" / "host-local-test" / task_id / "result.json"
    assert result_path.exists()
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert result_payload["task_id"] == task_id
    assert result_payload["worker_profile"] == "local_maint"
    assert result_payload["worker_kind"] == "codex_sdk"
    assert result_payload["lane"] == "host_local"
    assert result_payload["sandbox_profile"] == "workspace_write"
    assert result_payload["network_profile"] == "off"
    assert result_payload["status"] == "succeeded"
    assert result_payload["cleanup_status"] == "inline_only"
    assert result_payload["cleanup_owner"] == "inline_execution"
    assert result_payload["dispatch_state_ref"] == f".ai/runs/host-local-test/{task_id}/dispatch_state.json"
    assert "graded autonomy boundary" in result_payload["status_reason"]
    assert result_payload["compatibility_projection_ref"] == f"AgentBridge/results/{task_id}.md"

    verification_path = result_path.parent / "verification_summary.json"
    cost_path = result_path.parent / "cost_summary.json"
    evidence_index_path = result_path.parent / "evidence_index.json"
    dispatch_state_path = result_path.parent / "dispatch_state.json"
    closeout_bundle_path = result_path.parent / "closeout_bundle.json"
    stdout_log_path = result_path.parent / "stdout.log"
    stderr_log_path = result_path.parent / "stderr.log"

    assert verification_path.exists()
    assert cost_path.exists()
    assert evidence_index_path.exists()
    assert dispatch_state_path.exists()
    assert closeout_bundle_path.exists()
    assert stdout_log_path.read_text(encoding="utf-8") == "HOST_LOCAL_OK"
    assert stderr_log_path.read_text(encoding="utf-8") == ""

    verification_payload = json.loads(verification_path.read_text(encoding="utf-8"))
    assert verification_payload["status"] == "pass"
    assert [entry["gate"] for entry in verification_payload["commands_run"]] == [
        "build",
        "lint",
        "typecheck",
        "test",
        "contract",
        "hotspot",
    ]
    assert verification_payload["commands_run"][0]["status"] == "gate_na"
    assert verification_payload["commands_run"][3]["status"] == "pass"
    assert "TEST_OK" in verification_payload["commands_run"][3]["stdout"]
    assert verification_payload["commands_run"][4]["status"] == "pass"
    assert "CONTRACT_OK" in verification_payload["commands_run"][4]["stdout"]

    cost_payload = json.loads(cost_path.read_text(encoding="utf-8"))
    assert cost_payload["mode"] == "token_only"
    assert cost_payload["source"] == "sdk_structured"
    assert cost_payload["usage"]["total"]["total_tokens"] == 146

    closeout_payload = json.loads(closeout_bundle_path.read_text(encoding="utf-8"))
    assert closeout_payload["status"] == "succeeded"
    assert closeout_payload["cleanup_status"] == "inline_only"
    assert closeout_payload["cleanup_owner"] == "inline_execution"
    assert f".ai/runs/host-local-test/{task_id}/result.json" in closeout_payload["evidence_refs"]
    assert f".ai/runs/host-local-test/{task_id}/verification_summary.json" in closeout_payload["evidence_refs"]

    dispatch_payload = json.loads(dispatch_state_path.read_text(encoding="utf-8"))
    assert dispatch_payload["status"] == "completed"
    assert dispatch_payload["cleanup_status"] == "inline_only"
    assert dispatch_payload["cleanup_owner"] == "inline_execution"
    assert dispatch_payload["last_result_ref"] == f".ai/runs/host-local-test/{task_id}/result.json"
    assert dispatch_payload["source_ref"] == f"tasks/{task_id}.json"
    assert dispatch_payload["execution_lane"] == "host_local"
    assert dispatch_payload["worker_profile"] == "local_maint"

    evidence_payload = json.loads(evidence_index_path.read_text(encoding="utf-8"))
    indexed_paths = {entry["relative_path"] for entry in evidence_payload["entries"]}
    assert f".ai/runs/host-local-test/{task_id}/result.json" in indexed_paths
    assert f".ai/runs/host-local-test/{task_id}/dispatch_state.json" in indexed_paths
    assert f".ai/runs/host-local-test/{task_id}/closeout_bundle.json" in indexed_paths
    assert f"AgentBridge/results/{task_id}.md" in indexed_paths

    assert result_payload["review_result_ref"] is None
    assert result_payload["closeout_bundle_ref"] == f".ai/runs/host-local-test/{task_id}/closeout_bundle.json"

    projection_path = agentbridge_root / "results" / f"{task_id}.md"
    artifact_path = agentbridge_root / "artifacts" / f"{task_id}-worker-output.txt"
    assert projection_path.exists()
    assert artifact_path.exists()
    assert artifact_path.read_text(encoding="utf-8") == "HOST_LOCAL_OK"
    projection_text = projection_path.read_text(encoding="utf-8")
    assert "compatibility projection for canonical task" in projection_text
    assert "provider: openai-codex-sdk" in projection_text
    assert "Structured token usage captured from the worker runtime." in projection_text

    with sqlite3.connect(layout.control_plane_db) as connection:
        runtime_task = connection.execute(
            """
            SELECT
                state,
                execution_lane,
                worker_profile,
                result_path,
                next_action,
                cleanup_status,
                cleanup_owner,
                dispatch_state_path
            FROM runtime_tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()
        events = connection.execute(
            "SELECT event_type, payload_json FROM events ORDER BY created_at"
        ).fetchall()
        routes = connection.execute(
            "SELECT selected_lane FROM route_decisions WHERE task_id = ?",
            (task_id,),
        ).fetchall()

    assert runtime_task == (
        "completed",
        "host_local",
        "local_maint",
        f".ai/runs/host-local-test/{task_id}/result.json",
        "none",
        "inline_only",
        "inline_execution",
        f".ai/runs/host-local-test/{task_id}/dispatch_state.json",
    )
    assert [event_type for (event_type, _) in events] == ["task_started", "task_completed"]
    completion_payload = json.loads(events[1][1])
    assert completion_payload["compatibility_projection_ref"] == f"AgentBridge/results/{task_id}.md"
    assert completion_payload["evidence_index_ref"] == f".ai/runs/host-local-test/{task_id}/evidence_index.json"
    assert completion_payload["usage"] == {
        "source": "sdk_structured",
        "last": {
            "cached_input_tokens": 3,
            "input_tokens": 120,
            "output_tokens": 20,
            "reasoning_output_tokens": 6,
            "total_tokens": 146,
        },
        "total": {
            "cached_input_tokens": 3,
            "input_tokens": 120,
            "output_tokens": 20,
            "reasoning_output_tokens": 6,
            "total_tokens": 146,
        },
        "model_context_window": 272000,
    }
    assert routes == [("host_local",)]


def test_host_local_runner_materializes_explicit_worker_profile_route_reason(tmp_path: Path) -> None:
    task_id = "TASK-20260707-explicit-worker-profile"
    repo_root, layout, _, result_path = _run_fake_host_local_task(
        tmp_path,
        task_id=task_id,
        task_updates={"worker_profile": "wave1_smoke"},
    )

    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    dispatch_payload = json.loads((result_path.parent / "dispatch_state.json").read_text(encoding="utf-8"))

    with sqlite3.connect(layout.control_plane_db) as connection:
        route = connection.execute(
            "SELECT selected_lane, reason FROM route_decisions WHERE task_id = ?",
            (task_id,),
        ).fetchone()

    assert result_payload["worker_profile"] == "wave1_smoke"
    assert result_payload["worker_kind"] == "scripted"
    assert result_payload["route_reason"] == "repo-owned worker_profile=wave1_smoke selected from canonical task"
    assert dispatch_payload["worker_profile"] == "wave1_smoke"
    assert dispatch_payload["route_reason"] == result_payload["route_reason"]
    assert route == ("host_local", result_payload["route_reason"])


def test_host_local_runner_hands_off_when_worker_profile_quota_is_exhausted(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    _copy_runtime_config(repo_root)
    _update_worker_profile_config(
        repo_root,
        "local_maint",
        {"max_active_leases": 1},
    )

    task_id = "TASK-20260707-quota-handoff"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    write_task(task_path, _canonical_task_payload(task_id))

    layout = RuntimeLayout.from_repo_root(repo_root)
    occupied_task_id = "TASK-20260707-occupied"
    occupied_dispatch_state = ".ai/runs/occupied-run/TASK-20260707-occupied/dispatch_state.json"
    db.upsert_runtime_task(
        layout.control_plane_db,
        task_id=occupied_task_id,
        run_id="occupied-run",
        attempt=1,
        state="running",
        state_reason="existing active lease",
        execution_lane="host_local",
        worker_profile="local_maint",
        next_action="wait_for_worker_result",
        cleanup_status="inline_only",
        cleanup_owner="inline_execution",
        created_at="2026-07-07T10:00:00Z",
        updated_at="2026-07-07T10:00:00Z",
        dispatch_state_path=occupied_dispatch_state,
    )
    db.acquire_lease(
        layout.control_plane_db,
        task_id=occupied_task_id,
        worker_id="occupied-worker",
        acquired_at="2026-07-07T10:00:00Z",
        expires_at="2026-07-07T10:30:00Z",
    )

    class FailIfCalledWorker:
        def __init__(self) -> None:
            self.call_count = 0

        def run(self, request: WorkerRequest) -> WorkerResult:
            self.call_count += 1
            raise AssertionError("quota-exhausted task must hand off before worker execution")

    worker = FailIfCalledWorker()
    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=layout,
            run_id="quota-handoff-test",
        ),
        worker,
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    dispatch_payload = json.loads((result_path.parent / "dispatch_state.json").read_text(encoding="utf-8"))

    with sqlite3.connect(layout.control_plane_db) as connection:
        route = connection.execute(
            "SELECT selected_lane, reason FROM route_decisions WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        remaining_leases = connection.execute(
            "SELECT task_id FROM leases ORDER BY task_id",
        ).fetchall()

    assert worker.call_count == 0
    assert result_payload["status"] == "waiting_handoff"
    assert "lease_quota_exhausted" in result_payload["status_reason"]
    assert "worker_profile=local_maint" in result_payload["status_reason"]
    assert result_payload["route_reason"] == "repo default worker_profile=local_maint selected from orchestrator.yaml"
    assert dispatch_payload["status"] == "waiting_handoff"
    assert dispatch_payload["route_reason"] == result_payload["route_reason"]
    assert route == ("host_local", result_payload["route_reason"])
    assert remaining_leases == [(occupied_task_id,)]


def test_evidence_index_revalidation_passes_for_host_local_result(tmp_path: Path) -> None:
    task_id = "TASK-20260706-evidence-ok"
    repo_root, _, _, result_path = _run_fake_host_local_task(tmp_path, task_id=task_id)

    validation = revalidate_evidence_index(
        repo_root=repo_root,
        evidence_index_path=result_path.parent / "evidence_index.json",
    )

    assert validation.ok is True
    assert validation.task_id == task_id
    assert validation.run_id == "host-local-test"
    assert validation.issue_count == 0
    assert validation.checked_entry_count == 9
    assert {entry.status for entry in validation.entries} == {"ok"}


def test_evidence_index_revalidation_detects_tampered_projection(tmp_path: Path) -> None:
    task_id = "TASK-20260706-evidence-tamper"
    repo_root, _, agentbridge_root, result_path = _run_fake_host_local_task(tmp_path, task_id=task_id)

    projection_path = agentbridge_root / "results" / f"{task_id}.md"
    projection_path.write_text(
        projection_path.read_text(encoding="utf-8") + "\nTAMPERED\n",
        encoding="utf-8",
    )

    validation = revalidate_evidence_index(
        repo_root=repo_root,
        evidence_index_path=result_path.parent / "evidence_index.json",
    )

    assert validation.ok is False
    projection_entry = next(
        entry for entry in validation.entries if entry.relative_path == f"AgentBridge/results/{task_id}.md"
    )
    assert projection_entry.status == "sha256_and_byte_count_mismatch"
    assert projection_entry.actual_sha256 != projection_entry.expected_sha256
    assert projection_entry.actual_byte_count != projection_entry.expected_byte_count


def test_cli_revalidates_evidence_index(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    task_id = "TASK-20260706-evidence-cli"
    repo_root, _, _, result_path = _run_fake_host_local_task(tmp_path, task_id=task_id)

    exit_code = cli_main(
        [
            "--repo-root",
            str(repo_root),
            "--revalidate-evidence-index",
            str(result_path.parent / "evidence_index.json"),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["task_id"] == task_id
    assert payload["checked_entry_count"] == 9


def test_cli_run_task_uses_repo_owned_worker_factory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    _copy_runtime_config(repo_root)

    task_id = "TASK-20260708-cli-run-task"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = _canonical_task_payload(task_id)
    payload["risk_level"] = "low"
    payload["write_access"] = False
    write_task(task_path, payload)

    class FakeRuntimeWorkerFactory:
        def build(self, worker_profile: object) -> object:
            class FakeWorker:
                def run(self, request: WorkerRequest) -> WorkerResult:
                    assert f"task_id: {task_id}" in request.prompt
                    return WorkerResult(
                        final_response="CLI_TASK_OK",
                        raw_result={"kind": "fake"},
                    )

            return FakeWorker()

    monkeypatch.setattr("host_orchestrator.cli.RuntimeWorkerFactory", FakeRuntimeWorkerFactory)

    exit_code = cli_main(
        [
            "--repo-root",
            str(repo_root),
            "--run-task",
            str(task_path),
            "--run-id",
            "cli-run-task",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload == {
        "result_path": str(repo_root / ".ai" / "runs" / "cli-run-task" / task_id / "result.json"),
        "task_id": task_id,
        "run_id": "cli-run-task",
        "status": "succeeded",
        "worker_profile": "local_maint",
        "worker_kind": "codex_sdk",
        "handoff_required": False,
        "next_action": "none",
    }


def test_host_local_runner_avoids_worker_factory_when_pre_worker_handoff_triggers(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    _copy_runtime_config(repo_root)

    task_id = "TASK-20260708-factory-not-needed"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = _canonical_task_payload(task_id)
    payload["risk_level"] = "low"
    payload["write_access"] = False
    payload["requires_network"] = True
    write_task(task_path, payload)

    class FailIfBuiltFactory:
        def __init__(self) -> None:
            self.build_count = 0

        def build(self, worker_profile: object) -> object:
            self.build_count += 1
            raise AssertionError("capability handoff should happen before worker factory use")

    factory = FailIfBuiltFactory()
    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            run_id="factory-not-needed",
        ),
        worker_factory=factory,
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert factory.build_count == 0
    assert result_payload["status"] == "waiting_handoff"


def test_host_local_runner_uses_worker_factory_for_live_planner_sidecar(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    _copy_runtime_config(repo_root)

    task_id = "TASK-20260708-factory-planner"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = _canonical_task_payload(task_id)
    payload["risk_level"] = "critical"
    payload["write_access"] = False
    write_task(task_path, payload)

    class PlannerFactory:
        def __init__(self) -> None:
            self.build_count = 0

        def build(self, worker_profile: object) -> object:
            self.build_count += 1

            class FakePlannerWorker:
                def run(self, request: WorkerRequest) -> WorkerResult:
                    return WorkerResult(
                        final_response=json.dumps(
                            {
                                "disposition": "proceed",
                                "reason_summary": "Planner sidecar recorded a proceed disposition and kept the run at the worker boundary.",
                                "blocking_reasons": [],
                                "plan_outline": [
                                    "Review the planner receipt.",
                                    "Continue the worker step only after operator approval.",
                                ],
                            }
                        ),
                        raw_result={"kind": "planner"},
                    )

            return FakePlannerWorker()

    factory = PlannerFactory()
    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            run_id="factory-planner",
        ),
        worker_factory=factory,
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert factory.build_count == 1
    assert result_payload["status"] == "waiting_handoff"
    assert result_payload["termination_reason"] == "planner_sidecar_result_recorded"
    assert result_payload["next_action"] == "planner receipt recorded; operator may continue to worker execution"
    assert result_payload["planner_result_ref"] == f".ai/runs/factory-planner/{task_id}/planner_result.json"


def test_wave1_smoke_manifest_covers_three_categories() -> None:
    samples = load_wave1_smoke_samples(FIXTURES_ROOT)

    assert [sample.category for sample in samples] == [
        "code_refactor",
        "docs_sync",
        "script_contract",
    ]
    assert len({sample.task_id for sample in samples}) == 3


def test_wave1_smoke_suite_writes_summary_and_generated_agentbridge_root(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    _copy_runtime_config(repo_root)

    snapshot_root = repo_root / "snapshots" / "agentbridge-20260628"
    (snapshot_root / "tasks").mkdir(parents=True, exist_ok=True)
    (snapshot_root / "results").mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        REPO_ROOT / "snapshots" / "agentbridge-20260628" / "tasks" / "_TEMPLATE.md",
        snapshot_root / "tasks" / "_TEMPLATE.md",
    )
    shutil.copy2(
        REPO_ROOT / "snapshots" / "agentbridge-20260628" / "results" / "_TEMPLATE.md",
        snapshot_root / "results" / "_TEMPLATE.md",
    )

    summary = run_wave1_smokes(
        repo_root,
        run_id="wave1-smoke-test",
        fixtures_root=FIXTURES_ROOT,
        snapshot_root=snapshot_root,
    )

    assert summary.ok is True
    assert summary.sample_count == 3
    assert summary.completed_task_count == 0
    assert summary.terminal_task_count == 3
    assert summary.route_decision_count == 3
    assert summary.event_count == 6
    assert summary.worker_status == "idle"
    assert summary.state_counts == {"needs_review": 3}
    assert summary.summary_path.exists()
    assert not (summary.run_root / "canonical-tasks").exists()

    summary_text = summary.summary_path.read_text(encoding="utf-8")
    assert '"ok": true' in summary_text
    assert (summary.agentbridge_root / "tasks" / "_TEMPLATE.md").exists()
    assert (summary.agentbridge_root / "results" / "_TEMPLATE.md").exists()

    for outcome in summary.task_outcomes:
        expected_projection_ref = str(
            (summary.agentbridge_root / outcome.projection_path).relative_to(repo_root)
        ).replace("\\", "/")
        assert (summary.agentbridge_root / outcome.markdown_task_path).exists()
        assert (repo_root / outcome.result_json_path).exists()
        assert (repo_root / outcome.evidence_index_path).exists()
        assert (summary.agentbridge_root / outcome.projection_path).exists()
        assert (summary.agentbridge_root / outcome.artifact_path).exists()
        result_payload = json.loads(
            (repo_root / outcome.result_json_path).read_text(encoding="utf-8")
        )
        evidence_payload = json.loads(
            (repo_root / outcome.evidence_index_path).read_text(encoding="utf-8")
        )
        indexed_paths = {entry["relative_path"] for entry in evidence_payload["entries"]}
        assert result_payload["status"] == "needs_review"
        assert result_payload["handoff_required"] is True
        assert result_payload["compatibility_projection_ref"] == expected_projection_ref
        assert expected_projection_ref in indexed_paths
