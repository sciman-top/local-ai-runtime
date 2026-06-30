from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re


FRONT_MATTER_PATTERN = re.compile(r"(?s)^---\n(.*?)\n---\n")
TASK_ID_PATTERN = re.compile(r"(?m)^id:\s*(?P<value>[^\n]+?)\s*$")


@dataclass(frozen=True)
class TaskDocument:
    task_id: str
    path: Path
    raw_text: str


@dataclass(frozen=True)
class ArtifactRecord:
    relative_path: str
    byte_count: int
    sha256: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_utf8_lf(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def load_task(path: Path) -> TaskDocument:
    raw_text = path.read_text(encoding="utf-8")
    front_matter = FRONT_MATTER_PATTERN.match(raw_text)
    if not front_matter:
        raise ValueError(f"Missing YAML front matter: {path}")

    task_id_match = TASK_ID_PATTERN.search(front_matter.group(1))
    if not task_id_match:
        raise ValueError(f"Task id missing from front matter: {path}")

    task_id = task_id_match.group("value").strip()
    if path.stem != task_id:
        raise ValueError(f"Task basename and front matter id differ: {path}")

    return TaskDocument(task_id=task_id, path=path, raw_text=raw_text)


def write_text_artifact(agentbridge_root: Path, task_id: str, content: str) -> ArtifactRecord:
    artifact_name = f"{task_id}-worker-output.txt"
    relative_path = Path("artifacts") / artifact_name
    artifact_path = agentbridge_root / relative_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    write_utf8_lf(artifact_path, content)

    payload = artifact_path.read_bytes()
    return ArtifactRecord(
        relative_path=str(relative_path).replace("\\", "/"),
        byte_count=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
    )


def write_result(
    *,
    agentbridge_root: Path,
    task_id: str,
    basename: str,
    status: str,
    model: str,
    provider: str,
    worker_id: str,
    lane: str,
    sandbox_mode: str,
    network_mode: str,
    final_response: str | None,
    artifact: ArtifactRecord | None,
    failures: list[str],
    observations: list[str],
    human_review_required: bool,
    next_action: str,
) -> Path:
    result_path = agentbridge_root / "results" / f"{basename}.md"
    if result_path.exists():
        raise FileExistsError(f"Result already exists for task {task_id}: {result_path}")

    created_at = utc_now_iso()
    completed_at = utc_now_iso()
    artifact_lines = []
    artifact_entries = []
    evidence_paths = []
    if artifact:
        artifact_entries = [artifact.relative_path]
        evidence_paths = [artifact.relative_path]
        artifact_lines.append(
            f"- {artifact.relative_path} | {artifact.byte_count} | {artifact.sha256}"
        )

    failures_block = "[]" if not failures else "\n" + "\n".join(f"  - {failure}" for failure in failures)
    artifacts_block = "[]" if not artifact_entries else "\n" + "\n".join(
        f"  - {entry}" for entry in artifact_entries
    )
    evidence_paths_block = "[]" if not evidence_paths else "\n" + "\n".join(
        f"  - {entry}" for entry in evidence_paths
    )
    artifact_section = artifact_lines or ["- none | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"]
    observations_section = observations or ["- No extra observations."]
    summary_lines = [
        f"- host_local task {task_id} finished with status `{status}`.",
        f"- Worker lane: `{lane}`.",
    ]
    if final_response:
        summary_lines.append("- A worker response artifact was recorded.")

    actions_lines = [
        "1. Loaded one AgentBridge task file.",
        f"2. Executed the task through the `{provider}` worker path.",
        "3. Wrote one result file sharing the task basename.",
    ]

    front_matter = "\n".join(
        [
            "---",
            f"task_id: {task_id}",
            f"created_at: {created_at}",
            f"completed_at: {completed_at}",
            f"status: {status}",
            "runner: codex",
            "runtime: codex",
            f"model: {model}",
            f"provider: {provider}",
            f"worker_id: {worker_id}",
            f"lane: {lane}",
            f"sandbox_mode: {sandbox_mode}",
            f"network_mode: {network_mode}",
            f"artifacts:{artifacts_block}",
            f"failures: {failures_block}" if failures_block == "[]" else f"failures:{failures_block}",
            f"next_action: {next_action}",
            "memory_candidate: false",
            f"human_review_required: {'true' if human_review_required else 'false'}",
            "handoff_required: false",
            f"evidence_paths: {evidence_paths_block}" if evidence_paths_block == "[]" else f"evidence_paths:{evidence_paths_block}",
            "---",
            "",
        ]
    )

    body = "\n".join(
        [
            "# Summary",
            "",
            *summary_lines,
            "",
            "# Actions",
            "",
            *actions_lines,
            "",
            "# Artifacts",
            "",
            *artifact_section,
            "",
            "# Observations",
            "",
            *observations_section,
            "",
        ]
    )

    result_path.parent.mkdir(parents=True, exist_ok=True)
    write_utf8_lf(result_path, front_matter + body)
    return result_path
