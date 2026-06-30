from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import sqlite3

from host_orchestrator.host_local import HostLocalConfig, HostLocalRunner
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.worker import WorkerRequest, WorkerResult


TASK_ID_PATTERN = re.compile(r"(?m)^id:\s*(?P<value>[^\n]+?)\s*$")
EXPECTED_CATEGORIES = {"code_refactor", "docs_sync", "script_contract"}


@dataclass(frozen=True)
class Wave1SmokeSample:
    task_id: str
    category: str
    description: str
    task_path: Path
    response_path: Path


@dataclass(frozen=True)
class Wave1SmokeTaskOutcome:
    task_id: str
    category: str
    result_path: str
    artifact_path: str


@dataclass(frozen=True)
class Wave1SmokeSummary:
    run_id: str
    run_root: Path
    summary_path: Path
    agentbridge_root: Path
    control_plane_db: Path
    sample_count: int
    completed_task_count: int
    route_decision_count: int
    event_count: int
    worker_status: str | None
    task_outcomes: list[Wave1SmokeTaskOutcome]
    ok: bool
    issues: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "run_root": str(self.run_root),
            "summary_path": str(self.summary_path),
            "agentbridge_root": str(self.agentbridge_root),
            "control_plane_db": str(self.control_plane_db),
            "sample_count": self.sample_count,
            "completed_task_count": self.completed_task_count,
            "route_decision_count": self.route_decision_count,
            "event_count": self.event_count,
            "worker_status": self.worker_status,
            "task_outcomes": [asdict(outcome) for outcome in self.task_outcomes],
            "ok": self.ok,
            "issues": list(self.issues),
        }


class ScriptedWave1SmokeWorker:
    def __init__(self, responses_by_task_id: dict[str, str]) -> None:
        self._responses_by_task_id = responses_by_task_id

    def run(self, request: WorkerRequest) -> WorkerResult:
        task_id = extract_task_id(request.prompt)
        if task_id not in self._responses_by_task_id:
            raise KeyError(f"Wave 1 smoke response not found for task: {task_id}")
        return WorkerResult(
            final_response=self._responses_by_task_id[task_id],
            raw_result={"mode": "scripted-wave1-smoke", "task_id": task_id},
        )


def default_wave1_smoke_fixtures_root(repo_root: Path) -> Path:
    return repo_root / "runtime" / "host-orchestrator" / "fixtures" / "wave1-smokes"


def default_agentbridge_snapshot_root(repo_root: Path) -> Path:
    return repo_root / "snapshots" / "agentbridge-20260628"


def build_wave1_smoke_run_id() -> str:
    return "wave1-smoke-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def extract_task_id(raw_text: str) -> str:
    task_id_match = TASK_ID_PATTERN.search(raw_text)
    if not task_id_match:
        raise ValueError("Wave 1 smoke task content is missing an id field.")
    return task_id_match.group("value").strip()


def load_wave1_smoke_samples(fixtures_root: Path) -> list[Wave1SmokeSample]:
    manifest_path = fixtures_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    samples: list[Wave1SmokeSample] = []
    for entry in manifest["samples"]:
        task_path = fixtures_root / entry["task_path"]
        response_path = fixtures_root / entry["response_path"]
        if not task_path.exists():
            raise FileNotFoundError(f"Missing Wave 1 smoke task fixture: {task_path}")
        if not response_path.exists():
            raise FileNotFoundError(f"Missing Wave 1 smoke response fixture: {response_path}")

        task_id = extract_task_id(task_path.read_text(encoding="utf-8"))
        if task_id != entry["task_id"]:
            raise ValueError(
                "Wave 1 smoke manifest task_id does not match task fixture: "
                f"{entry['task_id']} != {task_id}"
            )

        samples.append(
            Wave1SmokeSample(
                task_id=task_id,
                category=entry["category"],
                description=entry["description"],
                task_path=task_path,
                response_path=response_path,
            )
        )

    return samples


def build_wave1_smoke_layout(repo_root: Path, run_root: Path) -> RuntimeLayout:
    control_plane_root = run_root / "control-plane"
    return RuntimeLayout(
        repo_root=repo_root,
        control_plane_root=control_plane_root,
        control_plane_db=control_plane_root / "control-plane.db",
        control_plane_logs=control_plane_root / "logs",
        wave_smokes=repo_root / "private-local" / "wave-smokes",
    )


def initialize_agentbridge_smoke_root(agentbridge_root: Path, snapshot_root: Path) -> None:
    (agentbridge_root / "tasks").mkdir(parents=True, exist_ok=True)
    (agentbridge_root / "results").mkdir(parents=True, exist_ok=True)
    (agentbridge_root / "artifacts").mkdir(parents=True, exist_ok=True)

    template_pairs = [
        (snapshot_root / "tasks" / "_TEMPLATE.md", agentbridge_root / "tasks" / "_TEMPLATE.md"),
        (snapshot_root / "results" / "_TEMPLATE.md", agentbridge_root / "results" / "_TEMPLATE.md"),
    ]
    for source, destination in template_pairs:
        if not source.exists():
            raise FileNotFoundError(f"Missing AgentBridge contract template: {source}")
        shutil.copy2(source, destination)


def collect_wave1_smoke_summary(
    *,
    run_id: str,
    run_root: Path,
    summary_path: Path,
    agentbridge_root: Path,
    layout: RuntimeLayout,
    worker_id: str,
    samples: list[Wave1SmokeSample],
    outcomes: list[Wave1SmokeTaskOutcome],
) -> Wave1SmokeSummary:
    with sqlite3.connect(layout.control_plane_db) as connection:
        completed_task_count = connection.execute(
            "SELECT COUNT(*) FROM runtime_tasks WHERE state = 'completed'"
        ).fetchone()[0]
        route_decision_count = connection.execute(
            "SELECT COUNT(*) FROM route_decisions"
        ).fetchone()[0]
        event_count = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        worker_row = connection.execute(
            "SELECT status FROM workers WHERE worker_id = ?",
            (worker_id,),
        ).fetchone()

    worker_status = worker_row[0] if worker_row else None
    sample_map = {sample.task_id: sample for sample in samples}
    issues: list[str] = []

    if {sample.category for sample in samples} != EXPECTED_CATEGORIES:
        issues.append(
            "Wave 1 smoke categories drifted from the expected three-sample set."
        )

    if len(samples) != 3:
        issues.append(f"Expected 3 Wave 1 smoke samples, found {len(samples)}.")

    if completed_task_count != len(samples):
        issues.append(
            f"Expected {len(samples)} completed runtime tasks, found {completed_task_count}."
        )

    if route_decision_count != len(samples):
        issues.append(
            f"Expected {len(samples)} route decisions, found {route_decision_count}."
        )

    expected_event_count = len(samples) * 2
    if event_count != expected_event_count:
        issues.append(
            f"Expected {expected_event_count} lifecycle events, found {event_count}."
        )

    if worker_status != "idle":
        issues.append(f"Expected worker status 'idle', found {worker_status!r}.")

    if len(outcomes) != len(samples):
        issues.append(
            f"Expected {len(samples)} task outcomes, found {len(outcomes)}."
        )

    for outcome in outcomes:
        result_path = agentbridge_root / outcome.result_path
        artifact_path = agentbridge_root / outcome.artifact_path
        if not result_path.exists():
            issues.append(f"Missing Wave 1 smoke result: {result_path}")
            continue
        if not artifact_path.exists():
            issues.append(f"Missing Wave 1 smoke artifact: {artifact_path}")
            continue

        result_text = result_path.read_text(encoding="utf-8")
        if f"task_id: {outcome.task_id}" not in result_text:
            issues.append(f"Result file is missing task id {outcome.task_id}: {result_path}")
        if "provider: wave1-scripted-fake-worker" not in result_text:
            issues.append(f"Result file lost the scripted provider marker: {result_path}")

        expected_artifact = sample_map[outcome.task_id].response_path.read_text(encoding="utf-8")
        actual_artifact = artifact_path.read_text(encoding="utf-8")
        if expected_artifact != actual_artifact:
            issues.append(f"Artifact content drifted for task {outcome.task_id}.")

    return Wave1SmokeSummary(
        run_id=run_id,
        run_root=run_root,
        summary_path=summary_path,
        agentbridge_root=agentbridge_root,
        control_plane_db=layout.control_plane_db,
        sample_count=len(samples),
        completed_task_count=completed_task_count,
        route_decision_count=route_decision_count,
        event_count=event_count,
        worker_status=worker_status,
        task_outcomes=outcomes,
        ok=not issues,
        issues=issues,
    )


def run_wave1_smokes(
    repo_root: Path,
    *,
    run_id: str | None = None,
    fixtures_root: Path | None = None,
    snapshot_root: Path | None = None,
) -> Wave1SmokeSummary:
    repo_root = repo_root.resolve()
    fixtures_root = (fixtures_root or default_wave1_smoke_fixtures_root(repo_root)).resolve()
    snapshot_root = (snapshot_root or default_agentbridge_snapshot_root(repo_root)).resolve()
    samples = load_wave1_smoke_samples(fixtures_root)

    actual_run_id = run_id or build_wave1_smoke_run_id()
    run_root = repo_root / "private-local" / "wave-smokes" / actual_run_id
    if run_root.exists():
        raise FileExistsError(f"Wave 1 smoke run already exists: {run_root}")

    agentbridge_root = run_root / "agentbridge"
    initialize_agentbridge_smoke_root(agentbridge_root, snapshot_root)
    for sample in samples:
        shutil.copy2(sample.task_path, agentbridge_root / "tasks" / sample.task_path.name)

    layout = build_wave1_smoke_layout(repo_root, run_root)
    responses_by_task_id = {
        sample.task_id: sample.response_path.read_text(encoding="utf-8")
        for sample in samples
    }
    worker_id = f"{actual_run_id}-worker"
    runner = HostLocalRunner(
        HostLocalConfig(
            agentbridge_root=agentbridge_root,
            workspace_root=repo_root,
            layout=layout,
            worker_id=worker_id,
            worker_profile="wave1_smoke",
            provider="wave1-scripted-fake-worker",
        ),
        ScriptedWave1SmokeWorker(responses_by_task_id),
    )

    outcomes: list[Wave1SmokeTaskOutcome] = []
    for sample in samples:
        task_path = agentbridge_root / "tasks" / sample.task_path.name
        result_path = runner.run_task(task_path)
        outcomes.append(
            Wave1SmokeTaskOutcome(
                task_id=sample.task_id,
                category=sample.category,
                result_path=str(result_path.relative_to(agentbridge_root)).replace("\\", "/"),
                artifact_path=f"artifacts/{sample.task_id}-worker-output.txt",
            )
        )

    summary_path = run_root / "wave1-smoke-summary.json"
    summary = collect_wave1_smoke_summary(
        run_id=actual_run_id,
        run_root=run_root,
        summary_path=summary_path,
        agentbridge_root=agentbridge_root,
        layout=layout,
        worker_id=worker_id,
        samples=samples,
        outcomes=outcomes,
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary.to_dict(), indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    if not summary.ok:
        raise RuntimeError(
            "Wave 1 smoke suite found issues: " + "; ".join(summary.issues)
        )

    return summary
