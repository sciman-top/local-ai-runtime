from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import subprocess

import pytest

from host_orchestrator.host_local import HostLocalConfig, HostLocalRunner
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.worker import WorkerRequest, WorkerResult

from support import canonical_task_payload, copy_runtime_config


PLANNER_NEXT_ACTION = "planner receipt recorded; operator may continue to worker execution"
PLANNER_HANDOFF_ACTION = "planner requested operator handoff before worker execution"
REVIEW_NEXT_ACTION = "heterogeneous review required before downstream use"


def _write_markdown_task(path: Path, front_matter: str, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{front_matter}\n---\n\n{body}", encoding="utf-8", newline="\n")
    return path


def _init_git_repo(repo_root: Path) -> None:
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Codex Test"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "codex-test@example.com"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "add", "."],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "test: seed repo"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


def test_review_patch_summary_degrades_without_git_admin_path(tmp_path: Path) -> None:
    from host_orchestrator.host_local import HostLocalRunner

    assert HostLocalRunner._bounded_patch_summary(
        workspace_root=tmp_path,
        changed_paths=[],
    ) == "git_diff_unavailable: workspace has no .git admin path"


def test_review_patch_summary_degrades_when_git_diff_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from host_orchestrator import host_local

    (tmp_path / ".git").mkdir()

    def _raise_file_not_found(*args: object, **kwargs: object) -> object:
        raise FileNotFoundError("git")

    monkeypatch.setattr(host_local.subprocess, "run", _raise_file_not_found)

    assert host_local.HostLocalRunner._bounded_patch_summary(
        workspace_root=tmp_path,
        changed_paths=["runtime/host-orchestrator/src/host_orchestrator/host_local.py"],
    ) == "git_diff_unavailable: FileNotFoundError"


def test_planner_required_is_derived_from_high_risk_or_dependencies(tmp_path: Path) -> None:
    from host_orchestrator.canonical_task import load_task, write_task

    high_risk_path = tmp_path / "high-risk.json"
    high_risk_payload = canonical_task_payload("TASK-20260707-high-risk")
    high_risk_payload["risk_level"] = "high"
    write_task(high_risk_path, high_risk_payload)

    dependency_path = tmp_path / "dependency.json"
    dependency_payload = canonical_task_payload("TASK-20260707-dependency")
    dependency_payload["depends_on"] = ["TASK-20260707-upstream"]
    write_task(dependency_path, dependency_payload)

    forced_path = tmp_path / "forced-planner.json"
    forced_payload = canonical_task_payload("TASK-20260707-forced-planner")
    forced_payload["risk_level"] = "low"
    forced_payload["user_forced_planner"] = True
    write_task(forced_path, forced_payload)

    low_risk_path = tmp_path / "low-risk.json"
    low_risk_payload = canonical_task_payload("TASK-20260707-low-risk")
    low_risk_payload["risk_level"] = "low"
    write_task(low_risk_path, low_risk_payload)

    assert load_task(high_risk_path).planner_required is True
    assert load_task(dependency_path).planner_required is True
    assert load_task(forced_path).planner_required is True
    assert load_task(low_risk_path).planner_required is False


def test_host_local_runner_materializes_live_planner_receipt_before_worker_execution(
    tmp_path: Path,
) -> None:
    from host_orchestrator.canonical_task import write_task

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    copy_runtime_config(repo_root)

    task_id = "TASK-20260707-planner-handoff"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = canonical_task_payload(task_id)
    payload["risk_level"] = "critical"
    write_task(task_path, payload)

    class FakePlannerWorker:
        def __init__(self) -> None:
            self.call_count = 0

        def run(self, request: WorkerRequest) -> WorkerResult:
            self.call_count += 1
            assert "repo-owned planner sidecar" in request.prompt
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

    worker = FakePlannerWorker()
    agentbridge_root = repo_root / "AgentBridge"
    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            agentbridge_root=agentbridge_root,
            run_id="planner-handoff-test",
        ),
        worker,
    )

    result_path = runner.run_task(task_path)
    task_root = result_path.parent
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    verification_payload = json.loads((task_root / "verification_summary.json").read_text(encoding="utf-8"))
    cost_payload = json.loads((task_root / "cost_summary.json").read_text(encoding="utf-8"))
    evidence_payload = json.loads((task_root / "evidence_index.json").read_text(encoding="utf-8"))
    dispatch_payload = json.loads((task_root / "dispatch_state.json").read_text(encoding="utf-8"))
    planner_result_payload = json.loads((task_root / "planner_result.json").read_text(encoding="utf-8"))
    projection_path = agentbridge_root / "results" / f"{task_id}.md"

    assert worker.call_count == 1
    assert result_payload["status"] == "waiting_handoff"
    assert result_payload["termination_reason"] == "planner_sidecar_result_recorded"
    assert result_payload["handoff_required"] is True
    assert result_payload["next_action"] == PLANNER_NEXT_ACTION
    assert result_payload["planner_result_ref"] == f".ai/runs/planner-handoff-test/{task_id}/planner_result.json"
    assert "risk_level=critical" in result_payload["status_reason"]
    assert verification_payload["status"] == "waiting_handoff"
    assert verification_payload["commands_run"] == []
    assert verification_payload["planner_disposition"] == "proceed"
    assert cost_payload["source"] == "worker_usage_unavailable"
    assert dispatch_payload["status"] == "waiting_handoff"
    assert dispatch_payload["next_action"] == PLANNER_NEXT_ACTION
    assert dispatch_payload["planner_result_ref"] == result_payload["planner_result_ref"]
    assert "risk_level=critical" in dispatch_payload["status_reason"]
    assert planner_result_payload["task_id"] == task_id
    assert planner_result_payload["planner_kind"] == "codex_sdk"
    assert planner_result_payload["planner_mode"] == "blocking"
    assert planner_result_payload["disposition"] == "proceed"
    assert projection_path.exists()
    projection_text = projection_path.read_text(encoding="utf-8")
    assert "status: waiting_handoff" in projection_text
    assert "handoff_required: true" in projection_text
    assert f"next_action: {PLANNER_NEXT_ACTION}" in projection_text

    indexed_paths = {entry["relative_path"] for entry in evidence_payload["entries"]}
    assert f".ai/runs/planner-handoff-test/{task_id}/result.json" in indexed_paths
    assert f".ai/runs/planner-handoff-test/{task_id}/dispatch_state.json" in indexed_paths
    assert f".ai/runs/planner-handoff-test/{task_id}/verification_summary.json" in indexed_paths
    assert f".ai/runs/planner-handoff-test/{task_id}/cost_summary.json" in indexed_paths
    assert f".ai/runs/planner-handoff-test/{task_id}/planner_result.json" in indexed_paths
    assert f".ai/runs/planner-handoff-test/{task_id}/closeout_bundle.json" in indexed_paths
    assert f".ai/runs/planner-handoff-test/{task_id}/evidence_index.json" not in indexed_paths
    assert f"AgentBridge/results/{task_id}.md" in indexed_paths

    with sqlite3.connect(repo_root / ".ai" / "state" / "control-plane.db") as connection:
        runtime_task = connection.execute(
            "SELECT state, result_path FROM runtime_tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        events = connection.execute(
            "SELECT event_type, payload_json FROM events ORDER BY created_at"
        ).fetchall()

    assert runtime_task == (
        "waiting_handoff",
        f".ai/runs/planner-handoff-test/{task_id}/result.json",
    )
    assert [event_type for (event_type, _) in events] == [
        "task_started",
        "planner_completed",
        "task_waiting_handoff",
    ]
    planner_event_payload = json.loads(events[1][1])
    assert planner_event_payload["disposition"] == "proceed"
    assert planner_event_payload["next_action"] == PLANNER_NEXT_ACTION
    waiting_payload = json.loads(events[2][1])
    assert waiting_payload["next_action"] == PLANNER_NEXT_ACTION
    assert waiting_payload["handoff_required"] is True


def test_requires_network_task_hands_off_before_worker_execution(tmp_path: Path) -> None:
    from host_orchestrator.canonical_task import write_task

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    copy_runtime_config(repo_root)

    task_id = "TASK-20260707-network-handoff"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = canonical_task_payload(task_id)
    payload["risk_level"] = "low"
    payload["write_access"] = False
    payload["requires_network"] = True
    write_task(task_path, payload)

    class FailIfCalledWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            raise AssertionError("network-gated task must hand off before worker execution")

    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            run_id="network-handoff-test",
        ),
        FailIfCalledWorker(),
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert result_payload["status"] == "waiting_handoff"
    assert "requires_network=true" in result_payload["status_reason"]


def test_non_host_local_lane_hands_off_before_worker_execution(tmp_path: Path) -> None:
    from host_orchestrator.canonical_task import write_task

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    copy_runtime_config(repo_root)

    task_id = "TASK-20260707-remote-lane-handoff"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = canonical_task_payload(task_id)
    payload["risk_level"] = "low"
    payload["write_access"] = False
    payload["execution_lane"] = "remote_non_gui"
    write_task(task_path, payload)

    class FailIfCalledWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            raise AssertionError("remote lane task must hand off before worker execution")

    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            run_id="remote-lane-handoff-test",
        ),
        FailIfCalledWorker(),
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert result_payload["status"] == "waiting_handoff"
    assert "execution_lane=remote_non_gui" in result_payload["status_reason"]


def test_markdown_manual_only_task_hits_planner_handoff_gate(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    copy_runtime_config(repo_root)

    task_id = "T-20260707-markdown-manual-only"
    task_path = _write_markdown_task(
        repo_root / "AgentBridge" / "tasks" / f"{task_id}.md",
        "\n".join(
            [
                f"id: {task_id}",
                "created_at: 2026-07-07T10:00:00Z",
                "requested_by: hermes",
                "source_runtime: hermes",
                "source_model: gpt-5.5",
                "source_provider: third-party-openai-compatible",
                "goal: >",
                "  This markdown intake should stop at planner handoff.",
                "constraints:",
                "  - Keep the task repo-local.",
                "runner: codex",
                "approval_level: manual_only",
                "requires_gui: false",
                "artifacts_out:",
                "  - .ai/runs/<run_id>/T-20260707-markdown-manual-only/result.json",
            ]
        ),
        "# Summary\n\nMarkdown planner gate regression.\n",
    )

    class FakePlannerWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            return WorkerResult(
                final_response=json.dumps(
                    {
                        "disposition": "handoff",
                        "reason_summary": "Planner sidecar requested operator handoff before worker execution.",
                        "blocking_reasons": ["manual_only_high_risk"],
                        "plan_outline": ["Require operator approval before any worker execution."],
                    }
                ),
                raw_result={"kind": "planner"},
            )

    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            agentbridge_root=repo_root / "AgentBridge",
            run_id="markdown-planner-gate",
        ),
        FakePlannerWorker(),
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert result_payload["status"] == "waiting_handoff"
    assert result_payload["handoff_required"] is True
    assert result_payload["next_action"] == PLANNER_HANDOFF_ACTION
    assert result_payload["planner_result_ref"] == f".ai/runs/markdown-planner-gate/{task_id}/planner_result.json"


def test_low_risk_non_planner_task_keeps_success_path(tmp_path: Path) -> None:
    from host_orchestrator.canonical_task import write_task

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    copy_runtime_config(repo_root)

    task_id = "TASK-20260707-low-risk-success"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = canonical_task_payload(task_id)
    payload["risk_level"] = "low"
    payload["write_access"] = False
    payload["allowed_paths"] = ["runtime/host-orchestrator/**"]
    write_task(task_path, payload)

    class FakeWorker:
        def __init__(self) -> None:
            self.call_count = 0

        def run(self, request: WorkerRequest) -> WorkerResult:
            self.call_count += 1
            assert f"task_id: {task_id}" in request.prompt
            return WorkerResult(
                final_response="LOW_RISK_OK",
                raw_result={"kind": "fake"},
            )

    worker = FakeWorker()
    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            agentbridge_root=repo_root / "AgentBridge",
            run_id="low-risk-success",
        ),
        worker,
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert worker.call_count == 1
    assert result_payload["status"] == "succeeded"
    assert result_payload["handoff_required"] is False
    assert result_payload["next_action"] == "none"


def test_review_required_is_derived_from_materialized_fields(tmp_path: Path) -> None:
    from host_orchestrator.canonical_task import load_task, write_task

    medium_risk_path = tmp_path / "medium-risk.json"
    medium_risk_payload = canonical_task_payload("TASK-20260707-medium-review")
    medium_risk_payload["risk_level"] = "medium"
    medium_risk_payload["write_access"] = False
    write_task(medium_risk_path, medium_risk_payload)

    write_access_path = tmp_path / "write-access.json"
    write_access_payload = canonical_task_payload("TASK-20260707-write-access-review")
    write_access_payload["risk_level"] = "low"
    write_access_payload["write_access"] = True
    write_task(write_access_path, write_access_payload)

    forced_review_path = tmp_path / "forced-review.json"
    forced_review_payload = canonical_task_payload("TASK-20260707-forced-review")
    forced_review_payload["risk_level"] = "low"
    forced_review_payload["write_access"] = False
    forced_review_payload["user_forced_review"] = True
    write_task(forced_review_path, forced_review_payload)

    no_review_path = tmp_path / "no-review.json"
    no_review_payload = canonical_task_payload("TASK-20260707-no-review")
    no_review_payload["risk_level"] = "low"
    no_review_payload["write_access"] = False
    write_task(no_review_path, no_review_payload)

    assert load_task(medium_risk_path).review_required is True
    assert load_task(write_access_path).review_required is False
    assert load_task(forced_review_path).review_required is True
    assert load_task(no_review_path).review_required is False


def test_force_on_overrides_reject_false_values(tmp_path: Path) -> None:
    from host_orchestrator.canonical_task import CanonicalTaskError, load_task, write_task

    forced_planner_off_path = tmp_path / "forced-planner-off.json"
    forced_planner_off_payload = canonical_task_payload("TASK-20260707-forced-planner-off")
    forced_planner_off_payload["user_forced_planner"] = False
    write_task(forced_planner_off_path, forced_planner_off_payload)

    forced_review_off_path = tmp_path / "forced-review-off.json"
    forced_review_off_payload = canonical_task_payload("TASK-20260707-forced-review-off")
    forced_review_off_payload["user_forced_review"] = False
    write_task(forced_review_off_path, forced_review_off_payload)

    with pytest.raises(CanonicalTaskError, match="user_forced_planner only allows true"):
        load_task(forced_planner_off_path)

    with pytest.raises(CanonicalTaskError, match="user_forced_review only allows true"):
        load_task(forced_review_off_path)


def test_host_local_runner_marks_review_required_tasks_as_needs_review_after_worker_execution(
    tmp_path: Path,
) -> None:
    from host_orchestrator.canonical_task import write_task

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    copy_runtime_config(repo_root)

    task_id = "TASK-20260707-review-handoff"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = canonical_task_payload(task_id)
    payload["risk_level"] = "medium"
    payload["write_access"] = True
    write_task(task_path, payload)

    class FakeWorker:
        def __init__(self) -> None:
            self.call_count = 0

        def run(self, request: WorkerRequest) -> WorkerResult:
            self.call_count += 1
            return WorkerResult(
                final_response="REVIEW_GATE_OK",
                raw_result={"kind": "fake"},
            )

    worker = FakeWorker()
    agentbridge_root = repo_root / "AgentBridge"
    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            agentbridge_root=agentbridge_root,
            run_id="review-handoff-test",
        ),
        worker,
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    verification_payload = json.loads((result_path.parent / "verification_summary.json").read_text(encoding="utf-8"))
    review_result_path = result_path.parent / "review_result.json"
    closeout_bundle_path = result_path.parent / "closeout_bundle.json"
    evidence_payload = json.loads((result_path.parent / "evidence_index.json").read_text(encoding="utf-8"))
    projection_text = (agentbridge_root / "results" / f"{task_id}.md").read_text(encoding="utf-8")

    assert worker.call_count == 1
    assert result_payload["status"] == "needs_review"
    assert result_payload["termination_reason"] == "review_required_before_downstream"
    assert result_payload["handoff_required"] is True
    assert result_payload["next_action"] == REVIEW_NEXT_ACTION
    assert result_payload["review_result_ref"] == f".ai/runs/review-handoff-test/{task_id}/review_result.json"
    assert result_payload["closeout_bundle_ref"] == f".ai/runs/review-handoff-test/{task_id}/closeout_bundle.json"
    assert verification_payload["status"] == "pass"
    assert review_result_path.exists()
    assert closeout_bundle_path.exists()
    assert "status: needs_review" in projection_text
    assert "human_review_required: true" in projection_text
    assert "handoff_required: true" in projection_text
    assert f"next_action: {REVIEW_NEXT_ACTION}" in projection_text

    review_result_payload = json.loads(review_result_path.read_text(encoding="utf-8"))
    assert review_result_payload["task_id"] == task_id
    assert review_result_payload["review_mode"] == "blocking"
    assert review_result_payload["recommended_action"] == "revise"
    assert "risk_level=medium" in review_result_payload["blocking_reasons"]
    assert "write_access=true" in review_result_payload["blocking_reasons"]

    closeout_payload = json.loads(closeout_bundle_path.read_text(encoding="utf-8"))
    assert closeout_payload["status"] == "partial"
    assert f".ai/runs/review-handoff-test/{task_id}/review_result.json" in closeout_payload["evidence_refs"]
    indexed_paths = {entry["relative_path"] for entry in evidence_payload["entries"]}
    assert f".ai/runs/review-handoff-test/{task_id}/review_result.json" in indexed_paths
    assert f".ai/runs/review-handoff-test/{task_id}/closeout_bundle.json" in indexed_paths

    with sqlite3.connect(repo_root / ".ai" / "state" / "control-plane.db") as connection:
        runtime_task = connection.execute(
            "SELECT state, result_path FROM runtime_tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        events = connection.execute(
            "SELECT event_type, payload_json FROM events ORDER BY created_at"
        ).fetchall()

    assert runtime_task == (
        "needs_review",
        f".ai/runs/review-handoff-test/{task_id}/result.json",
    )
    assert [event_type for (event_type, _) in events] == ["task_started", "task_needs_review"]
    review_payload = json.loads(events[1][1])
    assert review_payload["handoff_required"] is True
    assert review_payload["next_action"] == REVIEW_NEXT_ACTION


def test_host_local_runner_materializes_live_heterogeneous_review_receipt(
    tmp_path: Path,
) -> None:
    from host_orchestrator.canonical_task import write_task

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    copy_runtime_config(repo_root)
    changed_path = repo_root / "runtime" / "host-orchestrator" / "src" / "host_orchestrator" / "host_local.py"
    changed_path.parent.mkdir(parents=True)
    changed_path.write_text("BASELINE = 'before'\n", encoding="utf-8")

    task_id = "TASK-20260708-live-review"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = canonical_task_payload(task_id)
    payload["risk_level"] = "medium"
    payload["write_access"] = True
    payload["allowed_paths"] = ["runtime/host-orchestrator/src/host_orchestrator/host_local.py"]
    write_task(task_path, payload)
    _init_git_repo(repo_root)

    class FakePrimaryWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            changed_path.write_text("BASELINE = 'after review hardening'\n", encoding="utf-8")
            return WorkerResult(
                final_response=(
                    "Change summary: host_local.py wires a live review sidecar receipt after worker+verification; "
                    "worker_factory.py adds a claude_glm review-sidecar builder only; "
                    "test_planner_adapter.py expects a live review_result.json receipt while final status stays needs_review."
                ),
                raw_result={"kind": "primary"},
            )

    class FakeReviewWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            assert "Return a blocking review receipt for this bounded runtime slice." in request.prompt
            assert "Change summary: host_local.py wires a live review sidecar receipt" in request.prompt
            assert "Changed files: runtime/host-orchestrator/src/host_orchestrator/host_local.py" in request.prompt
            assert "Bounded patch summary:" in request.prompt
            assert "-BASELINE = 'before'" in request.prompt
            assert "+BASELINE = 'after review hardening'" in request.prompt
            return WorkerResult(
                final_response=json.dumps(
                    {
                        "reviewer_kind": "claude_glm",
                        "review_mode": "blocking",
                        "findings": [
                            {
                                "severity": "medium",
                                "category": "heterogeneous_review",
                                "title": "Live review wants a second look",
                                "detail": "The heterogeneous reviewer wants an operator to inspect the change before downstream use.",
                                "suggested_fix": "Inspect the live review receipt before proceeding.",
                            }
                        ],
                        "blocking_reasons": [
                            "risk_level=medium",
                            "write_access=true",
                            "heterogeneous_second_opinion_required",
                        ],
                        "missing_tests": [],
                        "recommended_action": "revise",
                        "summary": "Live heterogeneous reviewer recorded a blocking second opinion.",
                    }
                ),
                raw_result={"kind": "review"},
            )

    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            agentbridge_root=repo_root / "AgentBridge",
            run_id="live-review-test",
        ),
        worker=FakePrimaryWorker(),
        review_worker=FakeReviewWorker(),
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    review_result_payload = json.loads((result_path.parent / "review_result.json").read_text(encoding="utf-8"))

    assert result_payload["status"] == "needs_review"
    assert result_payload["next_action"] == REVIEW_NEXT_ACTION
    assert result_payload["review_result_ref"] == f".ai/runs/live-review-test/{task_id}/review_result.json"
    assert review_result_payload["reviewer_kind"] == "claude_glm"
    assert review_result_payload["review_mode"] == "blocking"
    assert review_result_payload["model"] == "glm-5.2"
    assert "heterogeneous_second_opinion_required" in review_result_payload["blocking_reasons"]
    assert review_result_payload["findings"][0]["category"] == "heterogeneous_review"


def test_policy_surface_tasks_also_stop_at_needs_review(tmp_path: Path) -> None:
    from host_orchestrator.canonical_task import write_task

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    copy_runtime_config(repo_root)

    task_id = "TASK-20260707-policy-review"
    task_path = repo_root / "tasks" / f"{task_id}.json"
    payload = canonical_task_payload(task_id)
    payload["risk_level"] = "low"
    payload["write_access"] = False
    payload["allowed_paths"] = ["docs/architecture/**"]
    write_task(task_path, payload)

    class FakeWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            return WorkerResult(
                final_response="POLICY_REVIEW_OK",
                raw_result={"kind": "fake"},
            )

    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            agentbridge_root=repo_root / "AgentBridge",
            run_id="policy-review-test",
        ),
        FakeWorker(),
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert result_payload["status"] == "needs_review"
    assert result_payload["handoff_required"] is True
    assert result_payload["next_action"] == REVIEW_NEXT_ACTION
    assert "touches_policy_surface=true" in result_payload["status_reason"]
