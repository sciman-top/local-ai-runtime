from __future__ import annotations

import json
from pathlib import Path
import sqlite3

import pytest

from host_orchestrator.host_local import HostLocalConfig, HostLocalRunner
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.worker import WorkerRequest, WorkerResult

from support import canonical_task_payload, copy_runtime_config


PLANNER_NEXT_ACTION = "planner handoff required before worker execution"
REVIEW_NEXT_ACTION = "heterogeneous review required before downstream use"


def _write_markdown_task(path: Path, front_matter: str, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{front_matter}\n---\n\n{body}", encoding="utf-8", newline="\n")
    return path


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


def test_host_local_runner_hands_off_planner_tasks_without_calling_worker(
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

    class FailIfCalledWorker:
        def __init__(self) -> None:
            self.call_count = 0

        def run(self, request: WorkerRequest) -> WorkerResult:
            self.call_count += 1
            raise AssertionError("planner-gated tasks must not reach the primary worker")

    worker = FailIfCalledWorker()
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
    projection_path = agentbridge_root / "results" / f"{task_id}.md"

    assert worker.call_count == 0
    assert result_payload["status"] == "waiting_handoff"
    assert result_payload["termination_reason"] == "planner_handoff_required"
    assert result_payload["handoff_required"] is True
    assert result_payload["next_action"] == PLANNER_NEXT_ACTION
    assert "risk_level=critical" in result_payload["status_reason"]
    assert verification_payload["status"] == "waiting_handoff"
    assert verification_payload["commands_run"] == []
    assert cost_payload["source"] == "planner_handoff_no_worker_usage"
    assert dispatch_payload["status"] == "waiting_handoff"
    assert dispatch_payload["next_action"] == PLANNER_NEXT_ACTION
    assert "risk_level=critical" in dispatch_payload["status_reason"]
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
    assert [event_type for (event_type, _) in events] == ["task_started", "task_waiting_handoff"]
    waiting_payload = json.loads(events[1][1])
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

    class FailIfCalledWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            raise AssertionError("manual_only markdown task must hand off before worker execution")

    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            agentbridge_root=repo_root / "AgentBridge",
            run_id="markdown-planner-gate",
        ),
        FailIfCalledWorker(),
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert result_payload["status"] == "waiting_handoff"
    assert result_payload["handoff_required"] is True
    assert result_payload["next_action"] == PLANNER_NEXT_ACTION


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
    projection_text = (agentbridge_root / "results" / f"{task_id}.md").read_text(encoding="utf-8")

    assert worker.call_count == 1
    assert result_payload["status"] == "needs_review"
    assert result_payload["termination_reason"] == "review_required_before_downstream"
    assert result_payload["handoff_required"] is True
    assert result_payload["next_action"] == REVIEW_NEXT_ACTION
    assert verification_payload["status"] == "pass"
    assert "status: needs_review" in projection_text
    assert "human_review_required: true" in projection_text
    assert "handoff_required: true" in projection_text
    assert f"next_action: {REVIEW_NEXT_ACTION}" in projection_text

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
