from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import sqlite3
import subprocess

import pytest
import yaml

from host_orchestrator.adaptive_orchestration import (
    AdaptiveOrchestrationError,
    evaluate_orchestration_payload,
    inspect_worktree,
    read_active_leases,
    validate_orchestration_decision_payload,
)
from host_orchestrator.agent_work_assets import load_mapping_file
from host_orchestrator.cli import main as cli_main
from host_orchestrator.config_runtime import load_runtime_config
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.runtime_v2.orchestration import run_orchestration_manifest_v2
from host_orchestrator.runtime_v2.evaluation import evaluate_orchestration_experiments
from host_orchestrator.runtime_v2.runner import RuntimeV2Config, RuntimeV2Runner
from host_orchestrator.worker import WorkerRequest, WorkerResult

from support import REPO_ROOT, copy_runtime_config


def _manifest_with_tasks(*tasks: dict[str, object], profile: str = "observe_default"):
    payload = load_mapping_file(REPO_ROOT / "templates" / "agent-work-manifest.example.yaml")
    payload["run_id"] = "adaptive-test-run"
    payload["repo_root"] = str(REPO_ROOT)
    payload["tasks"] = list(tasks)
    payload["orchestration_constraints"]["profile"] = profile
    payload["orchestration_constraints"]["mode_preference"] = "auto"
    return payload


def _task(
    task_id: str,
    *,
    write_access: bool = False,
    read_set: list[str] | None = None,
    write_set: list[str] | None = None,
    depends_on: list[str] | None = None,
    intent: str = "research",
    kind: str = "explore",
    risk_level: str = "low",
    worker_profile: str | None = None,
) -> dict[str, object]:
    template = load_mapping_file(
        REPO_ROOT / "templates" / "agent-work-manifest.example.yaml"
    )["tasks"][0]
    task = deepcopy(template)
    task.update(
        {
            "task_id": task_id,
            "title": task_id,
            "kind": kind,
            "intent": intent,
            "goal": f"execute {task_id}",
            "branch_name": f"codex/{task_id.lower()}",
            "worktree_path": f".worktrees/{task_id.lower()}",
            "read_set": read_set or [],
            "write_set": write_set or [],
            "allowed_paths": write_set or [],
            "write_access": write_access,
            "risk_level": risk_level,
            "depends_on": depends_on or [],
            "done_when": [f"{task_id} complete"],
        }
    )
    if worker_profile is None:
        task.pop("worker_profile", None)
    else:
        task["worker_profile"] = worker_profile
    return task


class _StaticWorker:
    def __init__(self, requests: list[WorkerRequest] | None = None) -> None:
        self.requests = requests if requests is not None else []

    def run(self, request: WorkerRequest) -> WorkerResult:
        self.requests.append(request)
        return WorkerResult(final_response="ADAPTIVE_OK", raw_result={"kind": "fake"})


def _init_git_repo(repo_root: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Adaptive Test"], cwd=repo_root, check=True)
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True)
    subprocess.run(
        ["git", "commit", "-m", "seed adaptive test repo"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


def _verified_worktree(task, repo_root: Path) -> dict[str, object]:
    return {
        "required": bool(task["write_access"]),
        "verified": True,
        "reason_code": "worktree_verified",
        "resolved_path": str(repo_root / str(task["worktree_path"])),
        "branch": str(task["branch_name"]),
    }


def test_single_task_defaults_to_single_agent_observe() -> None:
    runtime_config = load_runtime_config(REPO_ROOT)
    decision = evaluate_orchestration_payload(
        _manifest_with_tasks(_task("T01")),
        repo_root=REPO_ROOT,
        runtime_config=runtime_config,
        evaluated_at="2026-07-10T00:00:00Z",
    )

    assert decision["decision_status"] == "observed"
    assert decision["selected_mode"] == "single_agent"
    assert decision["reason_codes"] == ["single_agent_default", "single_task"]
    assert decision["runtime_boundaries"] == {
        "default_entrypoint_changed": False,
        "active_queue_changed": False,
        "live_accepted": False,
    }


def test_independent_read_only_tasks_select_parallel_wave_and_efficient_model() -> None:
    decision = evaluate_orchestration_payload(
        _manifest_with_tasks(
            _task("T01", read_set=["docs/a/**"]),
            _task("T02", read_set=["runtime/b/**"]),
        ),
        repo_root=REPO_ROOT,
        runtime_config=load_runtime_config(REPO_ROOT),
        evaluated_at="2026-07-10T00:00:00Z",
    )

    assert decision["selected_mode"] == "multi_agent"
    assert decision["waves"] == [
        {
            "wave_id": "wave-001",
            "task_ids": ["T01", "T02"],
            "parallel": True,
            "execution_kind": "parallel_read_only",
        }
    ]
    assert decision["budgets"]["delegated_task_count"] == 2
    assert {route["model_policy"]["model"] for route in decision["task_routes"]} == {
        "gpt-5.6-terra"
    }
    assert all("exploration" in route["capabilities"] for route in decision["task_routes"])


def test_dependency_chain_stays_serial_even_when_multi_agent_is_preferred() -> None:
    manifest = _manifest_with_tasks(
        _task("T01"),
        _task("T02", depends_on=["T01"]),
    )
    manifest["orchestration_constraints"]["mode_preference"] = "multi_agent"

    decision = evaluate_orchestration_payload(
        manifest,
        repo_root=REPO_ROOT,
        runtime_config=load_runtime_config(REPO_ROOT),
        evaluated_at="2026-07-10T00:00:00Z",
    )

    assert decision["selected_mode"] == "single_agent"
    assert [wave["task_ids"] for wave in decision["waves"]] == [["T01"], ["T02"]]
    assert "multi_agent_preference_downgraded" in decision["reason_codes"]


def test_write_write_and_write_read_conflicts_serialize_verified_writers() -> None:
    manifest = _manifest_with_tasks(
        _task(
            "T01",
            write_access=True,
            write_set=["runtime/shared.py"],
            read_set=["docs/**"],
            kind="implement",
            intent="feature",
        ),
        _task(
            "T02",
            write_access=True,
            write_set=["runtime/shared.py"],
            read_set=["runtime/**"],
            kind="implement",
            intent="bugfix",
        ),
        profile="guarded_isolated_writers",
    )

    decision = evaluate_orchestration_payload(
        manifest,
        repo_root=REPO_ROOT,
        runtime_config=load_runtime_config(REPO_ROOT),
        worktree_inspector=_verified_worktree,
        evaluated_at="2026-07-10T00:00:00Z",
    )

    assert decision["selected_mode"] == "single_agent"
    assert [wave["task_ids"] for wave in decision["waves"]] == [["T01"], ["T02"]]
    reasons = set(decision["conflicts"][0]["reason_codes"])
    assert {"write_write_conflict", "write_read_conflict"} <= reasons


def test_policy_surface_writers_are_serialized_even_with_disjoint_write_sets() -> None:
    decision = evaluate_orchestration_payload(
        _manifest_with_tasks(
            _task(
                "T01",
                write_access=True,
                write_set=["docs/specs/a.md"],
                kind="implement",
                intent="docs",
            ),
            _task(
                "T02",
                write_access=True,
                write_set=["docs/architecture/b.md"],
                kind="implement",
                intent="docs",
            ),
            profile="guarded_isolated_writers",
        ),
        repo_root=REPO_ROOT,
        runtime_config=load_runtime_config(REPO_ROOT),
        worktree_inspector=_verified_worktree,
        evaluated_at="2026-07-10T00:00:00Z",
    )

    assert decision["selected_mode"] == "single_agent"
    assert "policy_surface_competition" in decision["conflicts"][0]["reason_codes"]


def test_unverified_writer_cannot_enter_parallel_wave() -> None:
    decision = evaluate_orchestration_payload(
        _manifest_with_tasks(
            _task("T01", write_access=True, write_set=["runtime/a.py"], kind="implement"),
            _task("T02", write_access=True, write_set=["runtime/b.py"], kind="implement"),
            profile="guarded_isolated_writers",
        ),
        repo_root=REPO_ROOT,
        runtime_config=load_runtime_config(REPO_ROOT),
        evaluated_at="2026-07-10T00:00:00Z",
    )

    assert decision["selected_mode"] == "single_agent"
    assert "writer_isolation_unverified" in decision["reason_codes"]
    assert decision["decision_status"] == "blocked"
    assert "writer_isolation_unverified" in decision["blocking_reason_codes"]


def test_guarded_total_worker_budget_blocks_unbounded_serial_fallback() -> None:
    manifest = _manifest_with_tasks(
        *[_task(f"T{index:02d}") for index in range(1, 8)],
        profile="guarded_read_only",
    )

    decision = evaluate_orchestration_payload(
        manifest,
        repo_root=REPO_ROOT,
        runtime_config=load_runtime_config(REPO_ROOT),
        evaluated_at="2026-07-10T00:00:00Z",
    )

    assert decision["decision_status"] == "blocked"
    assert decision["budgets"]["planned_worker_count"] == 7
    assert "total_subagent_budget_exceeded" in decision["blocking_reason_codes"]


def test_high_risk_explorer_keeps_read_only_worker_profile() -> None:
    decision = evaluate_orchestration_payload(
        _manifest_with_tasks(_task("T01", risk_level="high")),
        repo_root=REPO_ROOT,
        runtime_config=load_runtime_config(REPO_ROOT),
        evaluated_at="2026-07-10T00:00:00Z",
    )

    route = decision["task_routes"][0]
    assert route["worker_profile"] == "adaptive_read"
    assert route["model_policy"] == {
        "route": "strong_read",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "high",
    }


def test_standalone_nested_repo_cannot_impersonate_linked_worktree(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub\n", encoding="utf-8")
    _init_git_repo(repo_root)
    nested = repo_root / ".worktrees" / "t01"
    nested.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=nested, check=True, capture_output=True, text=True)
    subprocess.run(["git", "checkout", "-b", "codex/t01"], cwd=nested, check=True, capture_output=True, text=True)

    status = inspect_worktree(
        _task("T01", write_access=True, write_set=["runtime/a.py"], kind="implement"),
        repo_root,
    )

    assert status["verified"] is False
    assert status["reason_code"] in {
        "worktree_missing_or_not_git",
        "worktree_not_linked_to_repo",
    }


def test_repo_linked_worktree_is_verified(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub\n", encoding="utf-8")
    (repo_root / ".gitignore").write_text(".worktrees/\n", encoding="utf-8")
    _init_git_repo(repo_root)
    worktree_path = repo_root / ".worktrees" / "t01"
    subprocess.run(
        ["git", "worktree", "add", "-b", "codex/t01", str(worktree_path)],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    status = inspect_worktree(
        _task("T01", write_access=True, write_set=["runtime/a.py"], kind="implement"),
        repo_root,
    )

    assert status["verified"] is True
    assert status["reason_code"] == "worktree_verified"


def test_active_lease_read_failure_is_fail_closed(tmp_path: Path) -> None:
    db_path = tmp_path / "control-plane-v2.db"
    db_path.write_bytes(b"not-a-sqlite-database")

    with pytest.raises(AdaptiveOrchestrationError, match="lease_state_unavailable"):
        read_active_leases(db_path=db_path, worker_profiles=["adaptive_read"])


def test_missing_capability_and_unknown_worker_fail_closed_with_stable_reasons() -> None:
    runtime_config = load_runtime_config(REPO_ROOT)
    adaptive = replace(
        runtime_config.policies.adaptive_orchestration,
        available_capabilities=(),
    )
    runtime_config = replace(
        runtime_config,
        policies=replace(runtime_config.policies, adaptive_orchestration=adaptive),
    )
    decision = evaluate_orchestration_payload(
        _manifest_with_tasks(
            _task("T01", intent="bugfix", worker_profile="missing-profile")
        ),
        repo_root=REPO_ROOT,
        runtime_config=runtime_config,
        evaluated_at="2026-07-10T00:00:00Z",
    )

    assert decision["decision_status"] == "blocked"
    assert decision["blocking_reason_codes"] == [
        "capability_unavailable",
        "unknown_worker_profile",
    ]


def test_observe_cli_writes_decision_without_creating_control_plane_db(
    tmp_path: Path,
    capsys,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    copy_runtime_config(repo_root)
    manifest = _manifest_with_tasks(_task("T01"))
    manifest["repo_root"] = str(repo_root)
    manifest_path = repo_root / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(manifest, allow_unicode=False, sort_keys=False),
        encoding="utf-8",
    )

    exit_code = cli_main(
        [
            "--repo-root",
            str(repo_root),
            "--evaluate-orchestration-manifest",
            str(manifest_path),
        ]
    )
    summary = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert summary["worker_execution_attempted"] is False
    assert summary["default_entrypoint_changed"] is False
    assert Path(summary["decision_path"]).exists()
    assert not (repo_root / ".ai" / "state" / "control-plane-v2.db").exists()


def test_guarded_runtime_v2_runs_parallel_read_only_wave_and_attaches_evidence(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub\n", encoding="utf-8")
    copy_runtime_config(repo_root)
    _init_git_repo(repo_root)
    manifest = _manifest_with_tasks(
        _task("T01", read_set=["docs/a/**"]),
        _task("T02", read_set=["runtime/b/**"]),
        profile="guarded_read_only",
    )
    manifest["repo_root"] = str(repo_root)
    manifest["run_id"] = "guarded-parallel-read"
    manifest_path = repo_root / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(manifest, allow_unicode=False, sort_keys=False),
        encoding="utf-8",
    )

    worker_requests: list[WorkerRequest] = []

    def build_runner(config: RuntimeV2Config, route):
        del route
        return RuntimeV2Runner(config, worker=_StaticWorker(worker_requests))

    summary_path, summary = run_orchestration_manifest_v2(
        manifest_path,
        repo_root=repo_root,
        layout=RuntimeLayout.from_repo_root(repo_root),
        runner_builder=build_runner,
    )

    assert summary_path.exists()
    assert summary["status"] == "completed"
    assert summary["selected_mode"] == "multi_agent"
    assert summary["parallel_wave_count"] == 1
    assert summary["worker_execution_attempted"] is True
    assert summary["status_counts"] == {"completed": 2}
    assert summary["default_entrypoint_changed"] is False
    for result in summary["results"]:
        result_path = repo_root / result["result_path"]
        result_payload = json.loads(result_path.read_text(encoding="utf-8"))
        fixture_payload = json.loads(
            (result_path.parent / "regression_fixture.json").read_text(encoding="utf-8")
        )
        closeout_payload = json.loads(
            (result_path.parent / "closeout_bundle.json").read_text(encoding="utf-8")
        )
        assert result_payload["decision_id"] == summary["decision_id"]
        assert result_payload["orchestration_decision_ref"] == summary[
            "orchestration_decision_ref"
        ]
        assert result_payload["model_policy"]["model"] == "gpt-5.6-terra"
        assert fixture_payload["artifact_refs"]["orchestration_decision"] == summary[
            "orchestration_decision_ref"
        ]
        assert fixture_payload["orchestration_metrics"]["evidence_complete"] is True
        assert fixture_payload["orchestration_metrics"]["subagent_count"] == 1
        assert closeout_payload["policy_version"] == "adaptive_orchestration.v1"
        evidence_index_path = result_path.parent / "evidence_index.json"
        evidence_index = json.loads(evidence_index_path.read_text(encoding="utf-8"))
        assert evidence_index["decision_id"] == summary["decision_id"]
        assert any(
            artifact["kind"] == "orchestration_decision"
            for artifact in evidence_index["artifacts"]
        )

    assert {request.reasoning_effort for request in worker_requests} == {"medium"}

    db_path = repo_root / ".ai" / "state" / "control-plane-v2.db"
    with sqlite3.connect(db_path) as connection:
        decision_artifact_count = connection.execute(
            "SELECT COUNT(*) FROM artifacts WHERE kind = 'orchestration_decision'"
        ).fetchone()[0]
        evidence_index_count = connection.execute(
            "SELECT COUNT(*) FROM artifacts WHERE kind = 'evidence_index'"
        ).fetchone()[0]
    assert decision_artifact_count == 2
    assert evidence_index_count == 2


def test_guarded_runtime_error_summary_keeps_decision_context(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    copy_runtime_config(repo_root)
    _init_git_repo(repo_root)
    manifest = _manifest_with_tasks(_task("T01"), profile="guarded_read_only")
    manifest["repo_root"] = str(repo_root)
    manifest["run_id"] = "guarded-error-context"
    manifest_path = repo_root / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(manifest, allow_unicode=False, sort_keys=False),
        encoding="utf-8",
    )

    def failing_builder(config: RuntimeV2Config, route):
        del config, route
        raise RuntimeError("runner construction failed")

    _, summary = run_orchestration_manifest_v2(
        manifest_path,
        repo_root=repo_root,
        layout=RuntimeLayout.from_repo_root(repo_root),
        runner_builder=failing_builder,
    )

    result = summary["results"][0]
    assert result["status"] == "error"
    assert summary["worker_execution_attempted"] is False
    assert result["worker_execution_attempted"] is False
    assert result["decision_id"] == summary["decision_id"]
    assert result["orchestration_decision_ref"] == summary["orchestration_decision_ref"]
    assert result["worker_profile"] == "adaptive_read"


def test_guarded_runtime_rejects_observe_profile_before_worker_or_db(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    copy_runtime_config(repo_root)
    manifest = _manifest_with_tasks(_task("T01"), profile="observe_default")
    manifest["repo_root"] = str(repo_root)
    manifest_path = repo_root / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(manifest, allow_unicode=False, sort_keys=False),
        encoding="utf-8",
    )
    runner_calls: list[str] = []

    def unexpected_runner(config: RuntimeV2Config, route):
        runner_calls.append(str(route["task_id"]))
        raise AssertionError("observe profile must not construct a worker")

    with pytest.raises(AdaptiveOrchestrationError, match="effect=guarded"):
        run_orchestration_manifest_v2(
            manifest_path,
            repo_root=repo_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            runner_builder=unexpected_runner,
        )

    assert runner_calls == []
    assert not (repo_root / ".ai" / "state" / "control-plane-v2.db").exists()


def test_orchestration_decision_example_is_valid() -> None:
    payload = json.loads(
        (REPO_ROOT / "templates" / "orchestration-decision.example.json").read_text(
            encoding="utf-8"
        )
    )

    validate_orchestration_decision_payload(payload)


def test_orchestration_eval_requires_repeated_pareto_improvement_and_never_promotes() -> None:
    fixtures: list[dict[str, object]] = []
    for variant, tokens, batch_ms, subagent_count in (
        ("baseline", 100, 200, 0),
        ("candidate", 80, 150, 2),
    ):
        for repeat_index in (1, 2, 3):
            fixtures.append(
                {
                    "task_id": "T01",
                    "verification_profile": "read_only",
                    "model_policy": {
                        "model": "gpt-5.6-terra",
                        "reasoning_effort": "medium",
                    },
                    "evaluation_context": {
                        "experiment_id": "read-parallel",
                        "variant": variant,
                        "repeat_index": repeat_index,
                        "baseline_run_id": "baseline-run" if variant == "candidate" else None,
                    },
                    "orchestration_metrics": {
                        "task_success": True,
                        "gate_pass": True,
                        "evidence_complete": True,
                        "total_tokens": tokens,
                        "wall_time_ms": batch_ms,
                        "batch_wall_time_ms": batch_ms,
                        "human_handoff_count": 0,
                        "subagent_count": subagent_count,
                        "conflict_count": 0,
                        "retry_count": 0,
                        "rework_count": 0,
                    },
                }
            )

    evaluation = evaluate_orchestration_experiments(fixtures)

    assert evaluation["promotion_status"] == "eligible_for_manual_review"
    assert evaluation["automatic_promotion_performed"] is False
    comparison = evaluation["experiments"][0]
    assert comparison["contract_match"] is True
    assert comparison["primary_non_regression"] is True
    assert comparison["secondary_pareto_improvement"] is True
    assert comparison["candidate"]["average_subagent_count"] == 2.0
    assert comparison["candidate"]["average_conflict_count"] == 0.0


def test_orchestration_eval_reports_insufficient_evidence_before_three_repeats() -> None:
    fixture = {
        "task_id": "T01",
        "verification_profile": "read_only",
        "model_policy": {"model": "gpt-5.6-terra", "reasoning_effort": "medium"},
        "evaluation_context": {
            "experiment_id": "insufficient",
            "variant": "candidate",
            "repeat_index": 1,
            "baseline_run_id": "missing-baseline",
        },
        "orchestration_metrics": {
            "task_success": True,
            "gate_pass": True,
            "evidence_complete": True,
        },
    }

    evaluation = evaluate_orchestration_experiments([fixture])

    assert evaluation["promotion_status"] == "insufficient_evidence"
    assert evaluation["automatic_promotion_performed"] is False
