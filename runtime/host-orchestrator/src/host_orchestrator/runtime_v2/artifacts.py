from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from host_orchestrator.evidence_index import render_relative_path
from host_orchestrator.paths import RuntimeLayout


@dataclass(frozen=True)
class V2Artifacts:
    run_id: str
    task_id: str
    attempt_id: str
    attempt_root: Path
    sidecars_root: Path
    stdout_log: Path
    stderr_log: Path
    attempt_json: Path
    result_json: Path
    gate_report: Path
    trace_manifest: Path
    closeout_bundle: Path
    planner_result: Path
    review_result: Path


def build_artifacts(
    *,
    layout: RuntimeLayout,
    run_id: str,
    task_id: str,
    attempt_id: str,
) -> V2Artifacts:
    attempt_root = layout.runs_v2_root / run_id / task_id / attempt_id
    sidecars_root = attempt_root / "sidecars"
    return V2Artifacts(
        run_id=run_id,
        task_id=task_id,
        attempt_id=attempt_id,
        attempt_root=attempt_root,
        sidecars_root=sidecars_root,
        stdout_log=attempt_root / "stdout.log",
        stderr_log=attempt_root / "stderr.log",
        attempt_json=attempt_root / "attempt.json",
        result_json=attempt_root / "result.json",
        gate_report=attempt_root / "gate_report.json",
        trace_manifest=attempt_root / "trace_manifest.json",
        closeout_bundle=attempt_root / "closeout_bundle.json",
        planner_result=sidecars_root / "planner_result.json",
        review_result=sidecars_root / "review_result.json",
    )


def ensure_artifact_dirs(artifacts: V2Artifacts) -> None:
    artifacts.attempt_root.mkdir(parents=True, exist_ok=True)
    artifacts.sidecars_root.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def repo_relative(layout: RuntimeLayout, path: Path) -> str:
    return render_relative_path(layout.repo_root, path)
