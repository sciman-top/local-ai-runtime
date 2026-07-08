from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any

from host_orchestrator import db
from host_orchestrator.canonical_task import write_task
from host_orchestrator.host_local import HostLocalConfig, HostLocalRunner, PLANNER_HANDOFF_NEXT_ACTION
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.worker import WorkerRequest, WorkerResult


TERMINAL_RUNTIME_STATES = {"completed", "needs_review", "waiting_handoff"}
REMOTE_NON_GUI_PROMOTION_TASK_IDS = {
    "default_remote_request": "TASK-20260707-remote-non-gui-default-request",
    "explicit_remote_profile": "TASK-20260707-remote-non-gui-profile-promotion",
}


@dataclass(frozen=True)
class RemoteNonGuiPromotionOutcome:
    task_id: str
    scenario: str
    final_state: str
    worker_profile: str
    route_reason: str
    next_action: str
    status_reason: str
    result_json_path: str
    dispatch_state_path: str
    handoff_receipt_ref: str
    handoff_reason_codes: list[str]
    worker_execution_attempted: bool


@dataclass(frozen=True)
class RemoteNonGuiPromotionSummary:
    run_id: str
    run_root: Path
    summary_path: Path
    control_plane_db: Path
    scenario_count: int
    task_run_count: int
    terminal_task_count: int
    route_decision_count: int
    active_lease_count: int
    worker_statuses: dict[str, str]
    worker_lanes: dict[str, str]
    state_counts: dict[str, int]
    task_outcomes: list[RemoteNonGuiPromotionOutcome]
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
            "active_lease_count": self.active_lease_count,
            "worker_statuses": dict(self.worker_statuses),
            "worker_lanes": dict(self.worker_lanes),
            "state_counts": dict(self.state_counts),
            "task_outcomes": [asdict(outcome) for outcome in self.task_outcomes],
            "ok": self.ok,
            "issues": list(self.issues),
        }


class FailIfCalledWorker:
    def __init__(self) -> None:
        self.call_count = 0

    def run(self, request: WorkerRequest) -> WorkerResult:
        self.call_count += 1
        raise AssertionError("remote_non_gui promotion tasks must hand off before worker execution")


def build_remote_non_gui_promotion_run_id() -> str:
    return "remote-non-gui-promotion-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def build_remote_non_gui_promotion_layout(repo_root: Path, run_root: Path) -> RuntimeLayout:
    ai_root = repo_root / ".ai"
    control_plane_root = run_root / "control-plane"
    return RuntimeLayout(
        repo_root=repo_root,
        ai_root=ai_root,
        runs_root=ai_root / "runs",
        runs_v2_root=ai_root / "runs-v2",
        control_plane_root=control_plane_root,
        control_plane_db=control_plane_root / "control-plane.db",
        control_plane_v2_db=control_plane_root / "control-plane-v2.db",
        control_plane_logs=control_plane_root / "logs",
        archive_root=run_root / "archive",
        wave_smokes=repo_root / "private-local" / "wave-smokes",
    )


def run_remote_non_gui_promotion(
    repo_root: Path,
    *,
    run_id: str | None = None,
) -> RemoteNonGuiPromotionSummary:
    repo_root = repo_root.resolve()
    actual_run_id = run_id or build_remote_non_gui_promotion_run_id()
    run_root = repo_root / "private-local" / "remote-non-gui-promotions" / actual_run_id
    if run_root.exists():
        raise FileExistsError(f"remote_non_gui promotion run already exists: {run_root}")
    run_root.mkdir(parents=True, exist_ok=False)

    layout = build_remote_non_gui_promotion_layout(repo_root, run_root)
    task_root = run_root / "tasks"
    task_root.mkdir(parents=True, exist_ok=True)

    default_request_path = task_root / f"{REMOTE_NON_GUI_PROMOTION_TASK_IDS['default_remote_request']}.json"
    promoted_profile_path = task_root / f"{REMOTE_NON_GUI_PROMOTION_TASK_IDS['explicit_remote_profile']}.json"

    write_task(
        default_request_path,
        _build_task_payload(
            task_id=REMOTE_NON_GUI_PROMOTION_TASK_IDS["default_remote_request"],
            execution_lane="remote_non_gui",
            requires_network=False,
            worker_profile=None,
        ),
    )
    write_task(
        promoted_profile_path,
        _build_task_payload(
            task_id=REMOTE_NON_GUI_PROMOTION_TASK_IDS["explicit_remote_profile"],
            execution_lane="remote_non_gui",
            requires_network=True,
            worker_profile="remote_non_gui_probe",
        ),
    )

    task_run_count = 0
    worker = FailIfCalledWorker()

    _run_handoff_task(
        task_path=default_request_path,
        layout=layout,
        repo_root=repo_root,
        worker=worker,
        worker_id=f"{actual_run_id}-worker-default-remote-request",
        run_id=f"{actual_run_id}-default-remote-request",
    )
    task_run_count += 1

    _run_handoff_task(
        task_path=promoted_profile_path,
        layout=layout,
        repo_root=repo_root,
        worker=worker,
        worker_id=f"{actual_run_id}-worker-remote-promotion",
        run_id=f"{actual_run_id}-remote-promotion",
    )
    task_run_count += 1

    summary_path = run_root / "remote-non-gui-promotion-summary.json"
    summary = collect_remote_non_gui_promotion_summary(
        layout=layout,
        run_id=actual_run_id,
        run_root=run_root,
        summary_path=summary_path,
        task_run_count=task_run_count,
        worker_call_count=worker.call_count,
        scenario_task_ids=list(REMOTE_NON_GUI_PROMOTION_TASK_IDS.values()),
    )
    summary_path.write_text(
        json.dumps(summary.to_dict(), indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    if not summary.ok:
        raise RuntimeError("remote_non_gui promotion suite found issues: " + "; ".join(summary.issues))
    return summary


def collect_remote_non_gui_promotion_summary(
    *,
    layout: RuntimeLayout,
    run_id: str,
    run_root: Path,
    summary_path: Path,
    task_run_count: int,
    worker_call_count: int,
    scenario_task_ids: list[str],
) -> RemoteNonGuiPromotionSummary:
    with sqlite3.connect(layout.control_plane_db) as connection:
        runtime_rows = connection.execute(
            f"""
            SELECT task_id, state, worker_profile, next_action, state_reason, result_path, dispatch_state_path
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
        worker_rows = connection.execute(
            "SELECT worker_id, lane, status FROM workers ORDER BY worker_id"
        ).fetchall()
        active_lease_count = connection.execute("SELECT COUNT(*) FROM leases").fetchone()[0]

    worker_statuses = {worker_id: status for worker_id, _, status in worker_rows}
    worker_lanes = {worker_id: lane for worker_id, lane, _ in worker_rows}
    terminal_task_count = sum(1 for _, state, *_ in runtime_rows if state in TERMINAL_RUNTIME_STATES)
    state_counts: dict[str, int] = {}
    outcomes: list[RemoteNonGuiPromotionOutcome] = []
    issues: list[str] = []

    expected_scenarios = {
        REMOTE_NON_GUI_PROMOTION_TASK_IDS["default_remote_request"]: (
            "default_remote_request",
            "local_maint",
            "repo default worker_profile=local_maint selected from orchestrator.yaml",
            "execution_lane=remote_non_gui",
        ),
        REMOTE_NON_GUI_PROMOTION_TASK_IDS["explicit_remote_profile"]: (
            "explicit_remote_profile",
            "remote_non_gui_probe",
            "repo-owned worker_profile=remote_non_gui_probe selected from canonical task",
            "host_runtime=host_local selected_lane=remote_non_gui runner_not_wired worker_profile=remote_non_gui_probe",
        ),
    }

    for task_id, state, worker_profile, next_action, state_reason, result_path, dispatch_state_path in runtime_rows:
        state_counts[state] = state_counts.get(state, 0) + 1
        result_json_path = layout.repo_root / str(result_path or "")
        dispatch_json_path = layout.repo_root / str(dispatch_state_path or "")
        if not result_json_path.exists():
            issues.append(f"Missing result.json for remote_non_gui promotion task {task_id}: {result_json_path}")
            continue
        if not dispatch_json_path.exists():
            issues.append(
                f"Missing dispatch_state.json for remote_non_gui promotion task {task_id}: {dispatch_json_path}"
            )
            continue

        result_payload = json.loads(result_json_path.read_text(encoding="utf-8"))
        dispatch_payload = json.loads(dispatch_json_path.read_text(encoding="utf-8"))
        route_reason = str(result_payload.get("route_reason") or "")
        handoff_receipt_ref = str(result_payload.get("handoff_receipt_ref") or "")
        handoff_reason_codes: list[str] = []
        worker_execution_attempted = True
        if route_reason != str(dispatch_payload.get("route_reason") or ""):
            issues.append(f"route_reason drifted between result and dispatch for {task_id}")
        if not handoff_receipt_ref:
            issues.append(f"Missing handoff_receipt_ref for remote_non_gui promotion task {task_id}")
        elif handoff_receipt_ref != str(dispatch_payload.get("handoff_receipt_ref") or ""):
            issues.append(f"handoff_receipt_ref drifted between result and dispatch for {task_id}")
        else:
            handoff_receipt_path = layout.repo_root / handoff_receipt_ref
            if not handoff_receipt_path.exists():
                issues.append(
                    f"Missing handoff_receipt.json for remote_non_gui promotion task {task_id}: {handoff_receipt_path}"
                )
            else:
                handoff_receipt_payload = json.loads(handoff_receipt_path.read_text(encoding="utf-8"))
                raw_reason_codes = handoff_receipt_payload.get("reason_codes")
                if isinstance(raw_reason_codes, list):
                    handoff_reason_codes = [str(item) for item in raw_reason_codes]
                worker_execution_attempted = bool(
                    handoff_receipt_payload.get("worker_execution_attempted")
                )
                if handoff_receipt_payload.get("status") != "waiting_handoff":
                    issues.append(
                        f"Expected {task_id} handoff receipt status waiting_handoff, "
                        f"found {handoff_receipt_payload.get('status')}."
                    )
                if worker_execution_attempted:
                    issues.append(f"Expected {task_id} handoff receipt to prove worker was not attempted.")

        scenario_name, expected_worker_profile, expected_route_reason, expected_status_fragment = expected_scenarios[task_id]
        if state != "waiting_handoff":
            issues.append(f"Expected {task_id} final state waiting_handoff, found {state}.")
        if str(worker_profile) != expected_worker_profile:
            issues.append(f"Expected {task_id} worker_profile {expected_worker_profile}, found {worker_profile}.")
        if route_reason != expected_route_reason:
            issues.append(f"Expected {task_id} route_reason {expected_route_reason}, found {route_reason}.")
        if PLANNER_HANDOFF_NEXT_ACTION != str(next_action or ""):
            issues.append(f"Expected {task_id} next_action {PLANNER_HANDOFF_NEXT_ACTION}, found {next_action}.")
        if expected_status_fragment not in str(state_reason or ""):
            issues.append(
                f"Expected {task_id} status_reason to contain {expected_status_fragment}, found {state_reason}."
            )

        outcomes.append(
            RemoteNonGuiPromotionOutcome(
                task_id=task_id,
                scenario=scenario_name,
                final_state=state,
                worker_profile=str(worker_profile),
                route_reason=route_reason,
                next_action=str(next_action or ""),
                status_reason=str(state_reason or ""),
                result_json_path=str(result_json_path.relative_to(layout.repo_root)).replace("\\", "/"),
                dispatch_state_path=str(dispatch_json_path.relative_to(layout.repo_root)).replace("\\", "/"),
                handoff_receipt_ref=handoff_receipt_ref,
                handoff_reason_codes=handoff_reason_codes,
                worker_execution_attempted=worker_execution_attempted,
            )
        )

    if len(runtime_rows) != len(scenario_task_ids):
        issues.append(f"Expected {len(scenario_task_ids)} final runtime task rows, found {len(runtime_rows)}.")
    if task_run_count != len(scenario_task_ids):
        issues.append(f"Expected {len(scenario_task_ids)} task runs, found {task_run_count}.")
    if route_decision_count != len(scenario_task_ids):
        issues.append(f"Expected {len(scenario_task_ids)} route decisions, found {route_decision_count}.")
    if terminal_task_count != len(scenario_task_ids):
        issues.append(f"Expected {len(scenario_task_ids)} terminal tasks, found {terminal_task_count}.")
    if active_lease_count != 0:
        issues.append(f"Expected all leases released after promotion suite, found {active_lease_count}.")
    if worker_call_count != 0:
        issues.append(f"Expected zero worker invocations, found {worker_call_count}.")
    if not worker_statuses:
        issues.append("Expected worker status rows to be materialized.")
    elif set(worker_statuses.values()) != {"idle"}:
        issues.append(f"Expected all worker statuses to be idle, found {worker_statuses}.")
    if len(worker_statuses) != len(scenario_task_ids):
        issues.append(f"Expected {len(scenario_task_ids)} worker ids, found {len(worker_statuses)}.")
    if state_counts != {"waiting_handoff": len(scenario_task_ids)}:
        issues.append(f"Unexpected final state counts: {state_counts}.")

    promoted_outcome = next(
        (item for item in outcomes if item.task_id == REMOTE_NON_GUI_PROMOTION_TASK_IDS["explicit_remote_profile"]),
        None,
    )
    if promoted_outcome is None:
        issues.append("Missing explicit remote_non_gui promotion outcome.")
    elif "requires_network=true" in promoted_outcome.status_reason:
        issues.append("Explicit remote_non_gui promotion should not hand off because of requires_network=true.")

    if set(worker_lanes.values()) != {"host_local", "remote_non_gui"}:
        issues.append(f"Expected worker lanes host_local + remote_non_gui, found {worker_lanes}.")

    return RemoteNonGuiPromotionSummary(
        run_id=run_id,
        run_root=run_root,
        summary_path=summary_path,
        control_plane_db=layout.control_plane_db,
        scenario_count=len(scenario_task_ids),
        task_run_count=task_run_count,
        terminal_task_count=terminal_task_count,
        route_decision_count=route_decision_count,
        active_lease_count=active_lease_count,
        worker_statuses=worker_statuses,
        worker_lanes=worker_lanes,
        state_counts=state_counts,
        task_outcomes=outcomes,
        ok=not issues,
        issues=issues,
    )


def _build_task_payload(
    *,
    task_id: str,
    execution_lane: str,
    requires_network: bool,
    worker_profile: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "task_id": task_id,
        "title": f"remote_non_gui promotion task {task_id}",
        "description": "Deterministic remote_non_gui promotion fixture.",
        "target_repo": "local-ai-dev-orchestrator",
        "base_branch": "main",
        "branch_name": "codex/remote-non-gui-promotion",
        "worktree_path": ".",
        "allowed_paths": ["runtime/host-orchestrator/**"],
        "forbidden_paths": [".env", ".env.*", ".git/config"],
        "write_access": False,
        "risk_level": "low",
        "merge_policy": "manual_merge_only",
        "execution_lane": execution_lane,
        "requires_network": requires_network,
        "requires_gui": False,
        "depends_on": [],
        "artifacts_out": [f".ai/runs/<run_id>/{task_id}/result.json"],
        "handoff_policy": "handoff_on_risk",
        "verification_commands": {
            "build": None,
            "test": 'python -c "print(\'REMOTE_PROMOTION_TEST_OK\')"',
            "lint": None,
            "typecheck": None,
            "contract": 'python -c "print(\'REMOTE_PROMOTION_CONTRACT_OK\')"',
            "hotspot": None,
        },
    }
    if worker_profile is not None:
        payload["worker_profile"] = worker_profile
    return payload


def _run_handoff_task(
    *,
    task_path: Path,
    layout: RuntimeLayout,
    repo_root: Path,
    worker: FailIfCalledWorker,
    worker_id: str,
    run_id: str,
) -> Path:
    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=layout,
            worker_id=worker_id,
            run_id=run_id,
        ),
        worker,
    )
    return runner.run_task(task_path)
