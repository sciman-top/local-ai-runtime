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
DEFAULT_FORBIDDEN_PATHS = [
    ".env",
    ".env.*",
    ".git/config",
    ".ssh/**",
    "secrets/**",
]
DEFAULT_VERIFICATION_COMMANDS = {
    "build": None,
    "test": None,
    "lint": None,
    "typecheck": None,
    "contract": None,
    "hotspot": None,
}
APPROVAL_LEVEL_TO_RISK = {
    "safe": "low",
    "review": "medium",
    "manual_only": "high",
}
REQUIRED_MARKDOWN_TASK_KEYS = {
    "id",
    "created_at",
    "requested_by",
    "source_runtime",
    "source_model",
    "source_provider",
    "goal",
    "constraints",
    "runner",
    "requires_gui",
    "approval_level",
    "artifacts_out",
}
OPTIONAL_MARKDOWN_TASK_KEYS = {
    "title",
}
UNSAFE_MARKDOWN_OVERRIDE_KEYS = {
    "target_repo",
    "base_branch",
    "branch_name",
    "worktree_path",
    "allowed_paths",
    "forbidden_paths",
    "write_access",
    "risk_level",
    "merge_policy",
    "execution_lane",
    "requires_network",
    "depends_on",
    "handoff_policy",
    "verification_commands",
}
SUPPORTED_MARKDOWN_TASK_KEYS = REQUIRED_MARKDOWN_TASK_KEYS | OPTIONAL_MARKDOWN_TASK_KEYS


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
    _validate_markdown_task_front_matter(front_matter, source=str(path))

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
    goal = _require_string(front_matter, "goal", source=str(task.path))
    front_matter_title = _optional_front_matter_string(front_matter, "title", source=str(task.path))
    title = front_matter_title
    if title is None:
        title = _extract_summary_title(task.raw_text) or goal or task.task_id

    approval_level = _require_string(front_matter, "approval_level", source=str(task.path))

    return {
        "task_id": task.task_id,
        "title": title,
        "description": task.raw_text.strip(),
        "target_repo": repo_root.name,
        "base_branch": "main",
        "branch_name": f"compat/{task.task_id}",
        "worktree_path": ".",
        "allowed_paths": ["**"],
        "forbidden_paths": list(DEFAULT_FORBIDDEN_PATHS),
        "write_access": True,
        "risk_level": APPROVAL_LEVEL_TO_RISK[approval_level],
        "merge_policy": "manual_merge_only",
        "execution_lane": "host_local",
        "requires_network": False,
        "requires_gui": _require_bool(front_matter, "requires_gui", source=str(task.path)),
        "depends_on": [],
        "artifacts_out": _require_string_list(front_matter, "artifacts_out", source=str(task.path)),
        "handoff_policy": "handoff_on_risk",
        "verification_commands": dict(DEFAULT_VERIFICATION_COMMANDS),
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
    handoff_required: bool,
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
            f"handoff_required: {'true' if handoff_required else 'false'}",
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


def _optional_front_matter_string(
    front_matter: dict[str, Any],
    key: str,
    *,
    source: str,
) -> str | None:
    if key not in front_matter:
        return None

    value = front_matter[key]
    if not isinstance(value, str):
        raise CompatibilityAdapterError(f"{source}:{key} must be a string")
    return value.strip()


def _validate_markdown_task_front_matter(front_matter: dict[str, Any], *, source: str) -> None:
    missing = sorted(REQUIRED_MARKDOWN_TASK_KEYS - front_matter.keys())
    if missing:
        raise CompatibilityAdapterError(
            "Missing required markdown task fields: " + ", ".join(missing)
        )

    unsafe_keys = sorted(UNSAFE_MARKDOWN_OVERRIDE_KEYS & front_matter.keys())
    if unsafe_keys:
        raise CompatibilityAdapterError(
            "Unsupported markdown execution override(s): " + ", ".join(unsafe_keys)
        )

    unknown_keys = sorted(front_matter.keys() - SUPPORTED_MARKDOWN_TASK_KEYS - UNSAFE_MARKDOWN_OVERRIDE_KEYS)
    if unknown_keys:
        raise CompatibilityAdapterError(
            "Unsupported markdown task field(s): " + ", ".join(unknown_keys)
        )

    for key in [
        "requested_by",
        "source_runtime",
        "source_model",
        "source_provider",
        "goal",
        "runner",
        "approval_level",
    ]:
        _require_string(front_matter, key, source=source)

    _require_timestamp_candidate(front_matter, "created_at", source=source)
    _require_string_list(front_matter, "constraints", source=source)
    _require_string_list(front_matter, "artifacts_out", source=source)
    _require_bool(front_matter, "requires_gui", source=source)

    runner = _require_string(front_matter, "runner", source=source)
    if runner != "codex":
        raise CompatibilityAdapterError(f"{source}:runner must be 'codex'")

    approval_level = _require_string(front_matter, "approval_level", source=source)
    if approval_level not in APPROVAL_LEVEL_TO_RISK:
        raise CompatibilityAdapterError(
            f"{source}:approval_level must be one of {', '.join(sorted(APPROVAL_LEVEL_TO_RISK))}"
        )

    if "title" in front_matter:
        _optional_front_matter_string(front_matter, "title", source=source)


def _require_string(payload: dict[str, Any], key: str, *, source: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CompatibilityAdapterError(f"{source}:{key} must be a non-empty string")
    return value.strip()


def _require_string_list(payload: dict[str, Any], key: str, *, source: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise CompatibilityAdapterError(f"{source}:{key} must be a list of non-empty strings")
    return [item.strip() for item in value]


def _require_bool(payload: dict[str, Any], key: str, *, source: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise CompatibilityAdapterError(f"{source}:{key} must be a boolean")
    return value


def _require_timestamp_candidate(payload: dict[str, Any], key: str, *, source: str) -> str:
    value = payload.get(key)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise CompatibilityAdapterError(f"{source}:{key} must be a timestamp string")
