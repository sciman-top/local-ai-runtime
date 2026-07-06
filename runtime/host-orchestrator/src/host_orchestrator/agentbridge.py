from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
from typing import Any

import yaml

from host_orchestrator.canonical_task import write_task


FRONT_MATTER_PATTERN = re.compile(r"(?s)^---\n(.*?)\n---\n")
SUMMARY_SECTION_PATTERN = re.compile(
    r"(?ms)^# Summary\s*(?P<body>.*?)(?=^# |\Z)"
)


class CompatibilityAdapterError(ValueError):
    """Raised when a compatibility projection cannot be parsed or written."""


@dataclass(frozen=True)
class MarkdownTaskProjection:
    task_id: str
    path: Path
    front_matter: dict[str, Any]
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


def load_markdown_task(path: Path) -> MarkdownTaskProjection:
    raw_text = path.read_text(encoding="utf-8")
    front_matter_match = FRONT_MATTER_PATTERN.match(raw_text)
    if not front_matter_match:
        raise CompatibilityAdapterError(f"Missing YAML front matter: {path}")

    try:
        front_matter = yaml.safe_load(front_matter_match.group(1))
    except yaml.YAMLError as exc:
        raise CompatibilityAdapterError(f"Invalid YAML front matter: {path} ({exc})") from exc

    if not isinstance(front_matter, dict):
        raise CompatibilityAdapterError(f"Task front matter must be a mapping: {path}")

    task_id = _require_string(front_matter, "id", source=str(path))
    if path.stem != task_id:
        raise CompatibilityAdapterError(f"Task basename and front matter id differ: {path}")

    return MarkdownTaskProjection(
        task_id=task_id,
        path=path,
        front_matter=front_matter,
        raw_text=raw_text,
    )


def load_task(path: Path) -> MarkdownTaskProjection:
    return load_markdown_task(path)


def markdown_task_to_canonical_payload(
    task: MarkdownTaskProjection,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    front_matter = task.front_matter
    goal = _string_value(front_matter.get("goal"))
    title = _extract_summary_title(task.raw_text) or goal or task.task_id
    requires_gui = _bool_value(front_matter.get("requires_gui"))
    approval_level = _string_value(front_matter.get("approval_level")) or "review"
    risk_level = "medium" if approval_level == "review" else "low"
    artifacts_out = _string_list(front_matter.get("artifacts_out"))

    return {
        "task_id": task.task_id,
        "title": title,
        "description": task.raw_text.strip(),
        "target_repo": repo_root.name,
        "base_branch": "main",
        "branch_name": f"compat/{task.task_id}",
        "worktree_path": ".",
        "allowed_paths": ["**"],
        "forbidden_paths": [".env", ".env.*", ".git/config", ".ssh/**", "secrets/**"],
        "write_access": True,
        "risk_level": risk_level,
        "merge_policy": "manual_merge_only",
        "execution_lane": "host_local",
        "requires_network": False,
        "requires_gui": requires_gui,
        "depends_on": [],
        "artifacts_out": artifacts_out,
        "handoff_policy": "handoff_on_risk",
        "verification_commands": {
            "build": None,
            "test": None,
            "lint": None,
            "typecheck": None,
            "contract": None,
            "hotspot": None,
        },
    }


def project_markdown_task_to_canonical(
    markdown_task_path: Path,
    destination_path: Path,
    *,
    repo_root: Path,
) -> Path:
    projection = load_markdown_task(markdown_task_path)
    payload = markdown_task_to_canonical_payload(projection, repo_root=repo_root)
    return write_task(destination_path, payload)


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


def write_result_projection(
    *,
    agentbridge_root: Path,
    task_id: str,
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
    result_path = agentbridge_root / "results" / f"{task_id}.md"
    if result_path.exists():
        raise FileExistsError(f"Result already exists for task {task_id}: {result_path}")

    created_at = utc_now_iso()
    completed_at = utc_now_iso()
    artifact_entries = [artifact.relative_path] if artifact else []
    evidence_entries = list(artifact_entries)
    artifact_lines = (
        [f"- {artifact.relative_path} | {artifact.byte_count} | {artifact.sha256}"]
        if artifact
        else ["- none | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"]
    )
    failures_block = "[]" if not failures else "\n" + "\n".join(f"  - {failure}" for failure in failures)
    artifacts_block = "[]" if not artifact_entries else "\n" + "\n".join(
        f"  - {entry}" for entry in artifact_entries
    )
    evidence_paths_block = "[]" if not evidence_entries else "\n" + "\n".join(
        f"  - {entry}" for entry in evidence_entries
    )
    observations_section = observations or ["- No extra observations."]
    summary_lines = [
        f"- compatibility projection for canonical task `{task_id}` finished with status `{status}`.",
        f"- Worker lane: `{lane}`.",
        f"- Network profile: `{network_mode}`.",
    ]
    if final_response:
        summary_lines.append("- A worker response artifact was recorded.")

    actions_lines = [
        "1. Loaded canonical task input through the host-local orchestrator runtime.",
        "2. Wrote the formal result bundle under `.ai/runs/`.",
        "3. Emitted this AgentBridge markdown file as a compatibility projection.",
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
            (
                f"evidence_paths: {evidence_paths_block}"
                if evidence_paths_block == "[]"
                else f"evidence_paths:{evidence_paths_block}"
            ),
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
            *artifact_lines,
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


def _extract_summary_title(raw_text: str) -> str:
    match = SUMMARY_SECTION_PATTERN.search(raw_text)
    if not match:
        return ""
    lines = [line.strip() for line in match.group("body").splitlines() if line.strip()]
    return lines[0] if lines else ""


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return False


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _string_value(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _require_string(payload: dict[str, Any], key: str, *, source: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CompatibilityAdapterError(f"{source}:{key} must be a non-empty string")
    return value.strip()
