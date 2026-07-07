from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any

from host_orchestrator import db
from host_orchestrator.canonical_task import write_task
from host_orchestrator.host_local import HostLocalConfig, HostLocalRunner
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.task_lifecycle import retry_task
from host_orchestrator.wave1_smoke import extract_task_id
from host_orchestrator.worker import WorkerRequest, WorkerResult


TERMINAL_RUNTIME_STATES = {"completed", "needs_review", "waiting_handoff"}
SIMULATION_TASK_IDS = {
    "explicit_wave1": "TASK-20260707-simulation-explicit-wave1",
    "review": "TASK-20260707-simulation-review",
    "quota": "TASK-20260707-simulation-quota",
    "retry": "TASK-20260707-simulation-retry",
}


@dataclass(frozen=True)
class MultiWorkerSimulationTaskOutcome:
    task_id: str
    scenario: str
    final_state: str
    attempt: int
    worker_profile: str
    route_reason: str
    next_action: str
    status_reason: str
    result_json_path: str
    dispatch_state_path: str


@dataclass(frozen=True)
class MultiWorkerSimulationSummary:
    run_id: str
    run_root: Path
    summary_path: Path
    control_plane_db: Path
    scenario_count: int
    task_run_count: int
    terminal_task_count: int
    route_decision_count: int
    retry_event_count: int
    active_lease_count: int
    worker_statuses: dict[str, str]
    state_counts: dict[str, int]
    retried_task_ids: list[str]
    task_outcomes: list[MultiWorkerSimulationTaskOutcome]
    ok: bool
    issues: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "run_root": str(self.run_root),
            "summary_path": str(self.summary_path),
            "control_plane_db": str(self.control_plane_db),
            "scenario_count": self.scenario_count,
            "task_run_count": self.task_run_count,
            "terminal_task_count": self.terminal_task_count,
            "route_decision_count": self.route_decision_count,
            "retry_event_count": self.retry_event_count,
            "active_lease_count": self.active_lease_count,
            "worker_statuses": dict(self.worker_statuses),
            "state_counts": dict(self.state_counts),
            "retried_task_ids": list(self.retried_task_ids),
            "task_outcomes": [asdict(outcome) for outcome in self.task_outcomes],
            "ok": self.ok,
            "issues": list(self.issues),
        }


class ScriptedSimulationWorker:
    def __init__(self, responses_by_task_id: dict[str, str]) -> None:
        self._responses_by_task_id = responses_by_task_id

    def run(self, request: WorkerRequest) -> WorkerResult:
        task_id = extract_task_id(request.prompt)
        try:
            final_response = self._responses_by_task_id[task_id]
        except KeyError as exc:
            raise KeyError(f"Simulation response not found for task {task_id}") from exc
        return WorkerResult(
            final_response=final_response,
            raw_result={"mode": "scripted-multi-worker-simulation", "task_id": task_id},
            stdout_text=final_response,
            stderr_text="",
        )


def build_multi_worker_simulation_run_id() -> str:
    return "multi-worker-sim-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def build_multi_worker_simulation_layout(repo_root: Path, run_root: Path) -> RuntimeLayout:
    ai_root = repo_root / ".ai"
    control_plane_root = run_root / "control-plane"
    return RuntimeLayout(
        repo_root=repo_root,
        ai_root=ai_root,
        runs_root=ai_root / "runs",
        control_plane_root=control_plane_root,
        control_plane_db=control_plane_root / "control-plane.db",
        control_plane_logs=control_plane_root / "logs",
        wave_smokes=repo_root / "private-local" / "wave-smokes",
    )


def run_multi_worker_simulation(
    repo_root: Path,
    *,
    run_id: str | None = None,
) -> MultiWorkerSimulationSummary:
    repo_root = repo_root.resolve()
    actual_run_id = run_id or build_multi_worker_simulation_run_id()
    run_root = repo_root / "private-local" / "multi-worker-simulations" / actual_run_id
    if run_root.exists():
        raise FileExistsError(f"Multi-worker simulation run already exists: {run_root}")
    run_root.mkdir(parents=True, exist_ok=False)

    layout = build_multi_worker_simulation_layout(repo_root, run_root)
    task_root = run_root / "tasks"
    task_root.mkdir(parents=True, exist_ok=True)

    explicit_path = task_root / f"{SIMULATION_TASK_IDS['explicit_wave1']}.json"
    review_path = task_root / f"{SIMULATION_TASK_IDS['review']}.json"
    quota_path = task_root / f"{SIMULATION_TASK_IDS['quota']}.json"
    retry_path = task_root / f"{SIMULATION_TASK_IDS['retry']}.json"

    write_task(
        explicit_path,
        _build_task_payload(
            task_id=SIMULATION_TASK_IDS["explicit_wave1"],
            risk_level="low",
            write_access=False,
            worker_profile="wave1_smoke",
        ),
    )
    write_task(
        review_path,
        _build_task_payload(
            task_id=SIMULATION_TASK_IDS["review"],
            risk_level="medium",
            write_access=True,
        ),
    )
    write_task(
        quota_path,
        _build_task_payload(
            task_id=SIMULATION_TASK_IDS["quota"],
            risk_level="low",
            write_access=False,
        ),
    )
    write_task(
        retry_path,
        _build_task_payload(
            task_id=SIMULATION_TASK_IDS["retry"],
            risk_level="low",
            write_access=False,
            test_command='python -c "import sys; sys.exit(1)"',
        ),
    )

    task_run_count = 0
    _run_scripted_task(
        task_path=explicit_path,
        task_id=SIMULATION_TASK_IDS["explicit_wave1"],
        layout=layout,
        repo_root=repo_root,
        worker_id=f"{actual_run_id}-worker-wave1",
        run_id=f"{actual_run_id}-wave1",
        response_text="SIMULATION_EXPLICIT_WAVE1_OK",
        worker_profile=None,
        attempt=1,
    )
    task_run_count += 1

    _run_scripted_task(
        task_path=review_path,
        task_id=SIMULATION_TASK_IDS["review"],
        layout=layout,
        repo_root=repo_root,
        worker_id=f"{actual_run_id}-worker-review",
        run_id=f"{actual_run_id}-review",
        response_text="SIMULATION_REVIEW_OK",
        worker_profile=None,
        attempt=1,
    )
    task_run_count += 1

    occupied_task_id = f"{actual_run_id}-occupied-local-maint"
    _seed_quota_occupant(layout=layout, task_id=occupied_task_id)
    _run_scripted_task(
        task_path=quota_path,
        task_id=SIMULATION_TASK_IDS["quota"],
        layout=layout,
        repo_root=repo_root,
        worker_id=f"{actual_run_id}-worker-quota",
        run_id=f"{actual_run_id}-quota",
        response_text="SIMULATION_QUOTA_SHOULD_NOT_RUN",
        worker_profile=None,
        attempt=1,
    )
    db.release_task_leases(layout.control_plane_db, task_id=occupied_task_id)
    task_run_count += 1

    _run_scripted_task(
        task_path=retry_path,
        task_id=SIMULATION_TASK_IDS["retry"],
        layout=layout,
        repo_root=repo_root,
        worker_id=f"{actual_run_id}-worker-retry-a1",
        run_id=f"{actual_run_id}-retry-a1",
        response_text="SIMULATION_RETRY_FAIL_FIRST",
        worker_profile=None,
        attempt=1,
    )
    task_run_count += 1

    retry_task(
        layout,
        task_id=SIMULATION_TASK_IDS["retry"],
        retried_at="2026-07-07T10:20:00Z",
        retry_rewind="worker_execution",
        reason="simulation retry after verification repair",
    )
    write_task(
        retry_path,
        _build_task_payload(
            task_id=SIMULATION_TASK_IDS["retry"],
            risk_level="low",
            write_access=False,
            test_command='python -c "print(\'SIMULATION_TEST_OK\')"',
        ),
    )
    _run_scripted_task(
        task_path=retry_path,
        task_id=SIMULATION_TASK_IDS["retry"],
        layout=layout,
        repo_root=repo_root,
        worker_id=f"{actual_run_id}-worker-retry-a2",
        run_id=f"{actual_run_id}-retry-a2",
        response_text="SIMULATION_RETRY_OK",
        worker_profile=None,
        attempt=2,
    )
    task_run_count += 1

    summary_path = run_root / "multi-worker-simulation-summary.json"
    summary = collect_multi_worker_simulation_summary(
        layout=layout,
        run_id=actual_run_id,
        run_root=run_root,
        summary_path=summary_path,
        task_run_count=task_run_count,
        scenario_task_ids=list(SIMULATION_TASK_IDS.values()),
    )
    summary_path.write_text(
        json.dumps(summary.to_dict(), indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    if not summary.ok:
        raise RuntimeError("Multi-worker simulation found issues: " + "; ".join(summary.issues))
    return summary


def collect_multi_worker_simulation_summary(
    *,
    layout: RuntimeLayout,
    run_id: str,
    run_root: Path,
    summary_path: Path,
    task_run_count: int,
    scenario_task_ids: list[str],
) -> MultiWorkerSimulationSummary:
    with sqlite3.connect(layout.control_plane_db) as connection:
        runtime_rows = connection.execute(
            f"""
            SELECT task_id, state, attempt, worker_profile, next_action, state_reason, result_path, dispatch_state_path
            FROM runtime_tasks
            WHERE task_id IN ({", ".join("?" for _ in scenario_task_ids)})
            ORDER BY task_id
            """,
            tuple(scenario_task_ids),
        ).fetchall()
        route_decision_count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM route_decisions
            WHERE task_id IN ({", ".join("?" for _ in scenario_task_ids)})
            """,
            tuple(scenario_task_ids),
        ).fetchone()[0]
        retry_event_count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM events
            WHERE event_type = 'task_retry_requested'
              AND task_id IN ({", ".join("?" for _ in scenario_task_ids)})
            """,
            tuple(scenario_task_ids),
        ).fetchone()[0]
        retried_task_rows = connection.execute(
            f"""
            SELECT DISTINCT task_id
            FROM events
            WHERE event_type = 'task_retry_requested'
              AND task_id IN ({", ".join("?" for _ in scenario_task_ids)})
            ORDER BY task_id
            """,
            tuple(scenario_task_ids),
        ).fetchall()
        worker_rows = connection.execute(
            "SELECT worker_id, status FROM workers ORDER BY worker_id"
        ).fetchall()
        active_lease_count = connection.execute(
            "SELECT COUNT(*) FROM leases"
        ).fetchone()[0]

    worker_statuses = {worker_id: status for worker_id, status in worker_rows}
    terminal_task_count = sum(1 for _, state, *_ in runtime_rows if state in TERMINAL_RUNTIME_STATES)
    state_counts: dict[str, int] = {}
    outcomes: list[MultiWorkerSimulationTaskOutcome] = []
    issues: list[str] = []

    expected_scenarios = {
        SIMULATION_TASK_IDS["explicit_wave1"]: ("explicit_wave1", "completed", 1),
        SIMULATION_TASK_IDS["review"]: ("review", "needs_review", 1),
        SIMULATION_TASK_IDS["quota"]: ("quota", "waiting_handoff", 1),
        SIMULATION_TASK_IDS["retry"]: ("retry", "completed", 2),
    }

    for task_id, state, attempt, worker_profile, next_action, state_reason, result_path, dispatch_state_path in runtime_rows:
        state_counts[state] = state_counts.get(state, 0) + 1
        result_json_path = layout.repo_root / str(result_path or "")
        dispatch_json_path = layout.repo_root / str(dispatch_state_path or "")
        if not result_json_path.exists():
            issues.append(f"Missing result.json for simulation task {task_id}: {result_json_path}")
            continue
        if not dispatch_json_path.exists():
            issues.append(f"Missing dispatch_state.json for simulation task {task_id}: {dispatch_json_path}")
            continue

        result_payload = json.loads(result_json_path.read_text(encoding="utf-8"))
        dispatch_payload = json.loads(dispatch_json_path.read_text(encoding="utf-8"))
        route_reason = str(result_payload.get("route_reason") or "")
        if route_reason != str(dispatch_payload.get("route_reason") or ""):
            issues.append(f"route_reason drifted between result and dispatch for {task_id}")

        scenario_name, expected_state, expected_attempt = expected_scenarios[task_id]
        if state != expected_state:
            issues.append(f"Expected {task_id} final state {expected_state}, found {state}.")
        if int(attempt) != expected_attempt:
            issues.append(f"Expected {task_id} attempt {expected_attempt}, found {attempt}.")

        outcomes.append(
            MultiWorkerSimulationTaskOutcome(
                task_id=task_id,
                scenario=scenario_name,
                final_state=state,
                attempt=int(attempt),
                worker_profile=str(worker_profile),
                route_reason=route_reason,
                next_action=str(next_action or ""),
                status_reason=str(state_reason or ""),
                result_json_path=str(result_json_path.relative_to(layout.repo_root)).replace("\\", "/"),
                dispatch_state_path=str(dispatch_json_path.relative_to(layout.repo_root)).replace("\\", "/"),
            )
        )

    if len(runtime_rows) != len(scenario_task_ids):
        issues.append(f"Expected {len(scenario_task_ids)} final runtime task rows, found {len(runtime_rows)}.")
    if task_run_count != 5:
        issues.append(f"Expected 5 task runs, found {task_run_count}.")
    if route_decision_count != 5:
        issues.append(f"Expected 5 route decisions, found {route_decision_count}.")
    if retry_event_count != 1:
        issues.append(f"Expected 1 retry event, found {retry_event_count}.")
    if terminal_task_count != len(scenario_task_ids):
        issues.append(
            f"Expected {len(scenario_task_ids)} terminal tasks, found {terminal_task_count}."
        )
    if active_lease_count != 0:
        issues.append(f"Expected all leases released after simulation, found {active_lease_count}.")
    if not worker_statuses:
        issues.append("Expected worker status rows to be materialized.")
    elif set(worker_statuses.values()) != {"idle"}:
        issues.append(f"Expected all worker statuses to be idle, found {worker_statuses}.")
    if len(worker_statuses) != task_run_count:
        issues.append(f"Expected {task_run_count} worker ids, found {len(worker_statuses)}.")
    if state_counts != {"completed": 2, "needs_review": 1, "waiting_handoff": 1}:
        issues.append(f"Unexpected final state counts: {state_counts}.")
    if [task_id for (task_id,) in retried_task_rows] != [SIMULATION_TASK_IDS["retry"]]:
        issues.append(f"Unexpected retried task ids: {[task_id for (task_id,) in retried_task_rows]}.")

    explicit_outcome = next((item for item in outcomes if item.task_id == SIMULATION_TASK_IDS["explicit_wave1"]), None)
    if explicit_outcome is None:
        issues.append("Missing explicit wave1 simulation outcome.")
    elif explicit_outcome.route_reason != "repo-owned worker_profile=wave1_smoke selected from canonical task":
        issues.append("Explicit worker_profile route reason drifted from canonical task selection.")

    quota_outcome = next((item for item in outcomes if item.task_id == SIMULATION_TASK_IDS["quota"]), None)
    if quota_outcome is None:
        issues.append("Missing quota simulation outcome.")
    elif "lease_quota_exhausted" not in quota_outcome.status_reason:
        issues.append("Quota simulation did not materialize lease_quota_exhausted in status_reason.")

    default_route_reason = "repo default worker_profile=local_maint selected from orchestrator.yaml"
    for task_id in (
        SIMULATION_TASK_IDS["review"],
        SIMULATION_TASK_IDS["quota"],
        SIMULATION_TASK_IDS["retry"],
    ):
        default_route_outcome = next((item for item in outcomes if item.task_id == task_id), None)
        if default_route_outcome is None:
            issues.append(f"Missing default-route simulation outcome for {task_id}.")
            continue
        if default_route_outcome.worker_profile != "local_maint":
            issues.append(
                f"Expected default worker_profile local_maint for {task_id}, found {default_route_outcome.worker_profile}."
            )
        if default_route_outcome.route_reason != default_route_reason:
            issues.append(
                f"Default worker_profile route reason drifted for {task_id}: {default_route_outcome.route_reason}"
            )

    return MultiWorkerSimulationSummary(
        run_id=run_id,
        run_root=run_root,
        summary_path=summary_path,
        control_plane_db=layout.control_plane_db,
        scenario_count=len(scenario_task_ids),
        task_run_count=task_run_count,
        terminal_task_count=terminal_task_count,
        route_decision_count=route_decision_count,
        retry_event_count=retry_event_count,
        active_lease_count=active_lease_count,
        worker_statuses=worker_statuses,
        state_counts=state_counts,
        retried_task_ids=[task_id for (task_id,) in retried_task_rows],
        task_outcomes=outcomes,
        ok=not issues,
        issues=issues,
    )


def _build_task_payload(
    *,
    task_id: str,
    risk_level: str,
    write_access: bool,
    worker_profile: str | None = None,
    test_command: str = 'python -c "print(\'SIMULATION_TEST_OK\')"',
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "task_id": task_id,
        "title": f"Simulation task {task_id}",
        "description": "Deterministic multi-worker simulation fixture.",
        "target_repo": "local-ai-dev-orchestrator",
        "base_branch": "main",
        "branch_name": "codex/multi-worker-simulation",
        "worktree_path": ".",
        "allowed_paths": ["runtime/host-orchestrator/**"],
        "forbidden_paths": [".env", ".env.*", ".git/config"],
        "write_access": write_access,
        "risk_level": risk_level,
        "merge_policy": "manual_merge_only",
        "execution_lane": "host_local",
        "requires_network": False,
        "requires_gui": False,
        "depends_on": [],
        "artifacts_out": [f".ai/runs/<run_id>/{task_id}/result.json"],
        "handoff_policy": "handoff_on_risk",
        "verification_commands": {
            "build": None,
            "test": test_command,
            "lint": None,
            "typecheck": None,
            "contract": 'python -c "print(\'SIMULATION_CONTRACT_OK\')"',
            "hotspot": None,
        },
    }
    if worker_profile is not None:
        payload["worker_profile"] = worker_profile
    return payload


def _run_scripted_task(
    *,
    task_path: Path,
    task_id: str,
    layout: RuntimeLayout,
    repo_root: Path,
    worker_id: str,
    run_id: str,
    response_text: str,
    worker_profile: str | None,
    attempt: int,
) -> Path:
    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=layout,
            worker_id=worker_id,
            worker_profile=worker_profile,
            run_id=run_id,
            attempt=attempt,
        ),
        ScriptedSimulationWorker({task_id: response_text}),
    )
    return runner.run_task(task_path)


def _seed_quota_occupant(
    *,
    layout: RuntimeLayout,
    task_id: str,
) -> None:
    created_at = "2026-07-07T10:05:00Z"
    db.upsert_runtime_task(
        layout.control_plane_db,
        task_id=task_id,
        run_id="simulation-quota-occupant",
        attempt=1,
        state="running",
        state_reason="simulation occupied local_maint slot",
        execution_lane="host_local",
        worker_profile="local_maint",
        next_action="wait_for_worker_result",
        cleanup_status="inline_only",
        cleanup_owner="inline_execution",
        created_at=created_at,
        updated_at=created_at,
        dispatch_state_path=".ai/runs/simulation-quota-occupant/dispatch_state.json",
    )
    db.acquire_lease(
        layout.control_plane_db,
        task_id=task_id,
        worker_id="simulation-occupied-worker",
        acquired_at=created_at,
        expires_at="2026-07-07T10:35:00Z",
    )
