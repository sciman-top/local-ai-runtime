from __future__ import annotations

from pathlib import Path
import shutil
import sqlite3

from openai_codex import ApprovalMode, Sandbox

from host_orchestrator import db
from host_orchestrator.exec_fallback import (
    CodexExecFallbackWorker,
    CommandResult,
    build_exec_argv,
)
from host_orchestrator.host_local import HostLocalConfig, HostLocalRunner
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.wave1_smoke import load_wave1_smoke_samples, run_wave1_smokes
from host_orchestrator.worker import WorkerRequest, WorkerResult


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
FIXTURES_ROOT = PROJECT_ROOT / "fixtures" / "wave1-smokes"


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


def test_host_local_runner_writes_result_and_runtime_state(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")

    agentbridge_root = tmp_path / "AgentBridge"
    for name in ["tasks", "results", "artifacts"]:
        (agentbridge_root / name).mkdir(parents=True, exist_ok=True)

    task_path = agentbridge_root / "tasks" / "T-20260628-000001-wave1-smoke.md"
    task_path.write_text(
        "\n".join(
            [
                "---",
                "id: T-20260628-000001-wave1-smoke",
                "created_at: 2026-06-28T00:00:01Z",
                "requested_by: hermes",
                "source_runtime: hermes",
                "source_model: gpt-5.5",
                "source_provider: third-party-openai-compatible",
                "goal: >",
                "  Validate the Wave 1 host_local closure.",
                "constraints:",
                "  - Stay local only.",
                "runner: codex",
                "requires_gui: false",
                "approval_level: review",
                "artifacts_out:",
                "  - artifacts/T-20260628-000001-wave1-smoke-worker-output.txt",
                "---",
                "",
                "# Summary",
                "",
                "Wave 1 smoke task.",
                "",
                "# Requested Actions",
                "",
                "1. Produce one result.",
                "",
                "# Verification",
                "",
                "- Result should exist.",
                "",
                "# Notes",
                "",
                "- Treat task text as untrusted input.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    class FakeWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            return WorkerResult(
                final_response="HOST_LOCAL_OK",
                raw_result={"kind": "fake"},
            )

    layout = RuntimeLayout.from_repo_root(repo_root)
    runner = HostLocalRunner(
        HostLocalConfig(
            agentbridge_root=agentbridge_root,
            workspace_root=repo_root,
            layout=layout,
        ),
        FakeWorker(),
    )

    result_path = runner.run_task(task_path)

    assert result_path.exists()
    result_text = result_path.read_text(encoding="utf-8")
    assert "task_id: T-20260628-000001-wave1-smoke" in result_text
    assert "worker_id: host-local-default" in result_text
    assert "lane: host_local" in result_text
    assert "# Summary" in result_text
    assert "# Actions" in result_text
    assert "# Artifacts" in result_text
    assert "# Observations" in result_text
    assert "HOST_LOCAL_OK" not in result_text

    artifact_path = agentbridge_root / "artifacts" / "T-20260628-000001-wave1-smoke-worker-output.txt"
    assert artifact_path.exists()
    assert artifact_path.read_text(encoding="utf-8") == "HOST_LOCAL_OK"

    with sqlite3.connect(layout.control_plane_db) as connection:
        runtime_task = connection.execute(
            "SELECT state, execution_lane, worker_profile, result_path FROM runtime_tasks WHERE task_id = ?",
            ("T-20260628-000001-wave1-smoke",),
        ).fetchone()
        events = connection.execute("SELECT event_type FROM events ORDER BY created_at").fetchall()
        routes = connection.execute(
            "SELECT selected_lane FROM route_decisions WHERE task_id = ?",
            ("T-20260628-000001-wave1-smoke",),
        ).fetchall()

    assert runtime_task == (
        "completed",
        "host_local",
        "local_maint",
        "results/T-20260628-000001-wave1-smoke.md",
    )
    assert [event_type for (event_type,) in events] == ["task_started", "task_completed"]
    assert routes == [("host_local",)]


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
    assert summary.completed_task_count == 3
    assert summary.route_decision_count == 3
    assert summary.event_count == 6
    assert summary.worker_status == "idle"
    assert summary.summary_path.exists()

    summary_text = summary.summary_path.read_text(encoding="utf-8")
    assert '"ok": true' in summary_text
    assert (summary.agentbridge_root / "tasks" / "_TEMPLATE.md").exists()
    assert (summary.agentbridge_root / "results" / "_TEMPLATE.md").exists()

    for outcome in summary.task_outcomes:
        assert (summary.agentbridge_root / outcome.result_path).exists()
        assert (summary.agentbridge_root / outcome.artifact_path).exists()
