from __future__ import annotations

import json
from pathlib import Path

import pytest

from host_orchestrator import agentbridge
from host_orchestrator.canonical_task import REQUIRED_FIELDS, task_from_payload
from host_orchestrator.host_local import HostLocalConfig, HostLocalRunner
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.worker import WorkerRequest, WorkerResult

from support import copy_runtime_config


def _write_agentbridge_task(path: Path, front_matter: str, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{front_matter}\n---\n\n{body}", encoding="utf-8", newline="\n")
    return path


def test_markdown_task_to_canonical_payload_uses_repo_owned_defaults(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    task_id = "T-20260706-100001-safe-intake"
    task_path = _write_agentbridge_task(
        repo_root / "AgentBridge" / "tasks" / f"{task_id}.md",
        "\n".join(
            [
                f"id: {task_id}",
                "created_at: 2026-07-06T10:00:01Z",
                "requested_by: hermes",
                "source_runtime: hermes",
                "source_model: gpt-5.5",
                "source_provider: third-party-openai-compatible",
                "title: Explicit markdown intake task title.",
                "goal: >",
                "  Prove markdown intake normalizes into repo-owned canonical defaults.",
                "constraints:",
                "  - Stay inside the worktree.",
                "runner: codex",
                "approval_level: manual_only",
                "requires_gui: true",
                "artifacts_out:",
                "  - .ai/runs/<run_id>/T-20260706-100001-safe-intake/result.json",
            ]
        ),
        "\n".join(
            [
                "# Summary",
                "",
                "Explicit markdown intake task title.",
                "",
                "# Requested Actions",
                "",
                "1. Keep the canonical payload lossless.",
            ]
        ),
    )

    projection = agentbridge.load_markdown_task(task_path)
    payload = agentbridge.markdown_task_to_canonical_payload(projection, repo_root=repo_root)
    canonical_task = task_from_payload(task_path, payload)

    assert set(payload) == REQUIRED_FIELDS | {"description"}
    assert canonical_task.path == task_path
    assert canonical_task.task_id == task_id
    assert canonical_task.title == "Explicit markdown intake task title."
    assert canonical_task.target_repo == repo_root.name
    assert canonical_task.base_branch == "main"
    assert canonical_task.branch_name == f"compat/{task_id}"
    assert canonical_task.worktree_path == "."
    assert canonical_task.allowed_paths == ("**",)
    assert canonical_task.forbidden_paths == (
        ".env",
        ".env.*",
        ".git/config",
        ".ssh/**",
        "secrets/**",
    )
    assert canonical_task.write_access is True
    assert canonical_task.risk_level == "high"
    assert canonical_task.merge_policy == "manual_merge_only"
    assert canonical_task.execution_lane == "host_local"
    assert canonical_task.requires_network is False
    assert canonical_task.requires_gui is True
    assert canonical_task.depends_on == ()
    assert canonical_task.artifacts_out == (
        ".ai/runs/<run_id>/T-20260706-100001-safe-intake/result.json",
    )
    assert canonical_task.handoff_policy == "handoff_on_risk"
    assert canonical_task.verification_commands.build is None
    assert canonical_task.verification_commands.test is None
    assert canonical_task.verification_commands.contract is None
    assert canonical_task.description.startswith("---\nid: T-20260706-100001-safe-intake")


def test_markdown_task_rejects_verification_command_injection(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    task_id = "T-20260706-100003-reject-verification-injection"
    task_path = _write_agentbridge_task(
        repo_root / "AgentBridge" / "tasks" / f"{task_id}.md",
        "\n".join(
            [
                f"id: {task_id}",
                "created_at: 2026-07-06T10:00:03Z",
                "requested_by: hermes",
                "source_runtime: hermes",
                "source_model: gpt-5.5",
                "source_provider: third-party-openai-compatible",
                "goal: >",
                "  Attempt to smuggle shell commands through markdown intake.",
                "constraints:",
                "  - Stay inside the worktree.",
                "runner: codex",
                "approval_level: review",
                "requires_gui: false",
                "artifacts_out:",
                "  - artifacts/example-output.txt",
                "verification_commands:",
                "  test: python -c \"print('SHOULD_NOT_RUN')\"",
            ]
        ),
        "# Summary\n\nReject injected verification commands.\n",
    )

    with pytest.raises(
        agentbridge.CompatibilityAdapterError,
        match="Unsupported markdown execution override\\(s\\): verification_commands",
    ):
        agentbridge.load_markdown_task(task_path)


def test_markdown_task_rejects_execution_critical_overrides(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    task_id = "T-20260706-100004-reject-execution-override"
    task_path = _write_agentbridge_task(
        repo_root / "AgentBridge" / "tasks" / f"{task_id}.md",
        "\n".join(
            [
                f"id: {task_id}",
                "created_at: 2026-07-06T10:00:04Z",
                "requested_by: hermes",
                "source_runtime: hermes",
                "source_model: gpt-5.5",
                "source_provider: third-party-openai-compatible",
                "goal: >",
                "  Attempt to override execution-critical runtime behavior.",
                "constraints:",
                "  - Stay inside the worktree.",
                "runner: codex",
                "approval_level: review",
                "requires_gui: false",
                "artifacts_out:",
                "  - artifacts/example-output.txt",
                "target_repo: some-other-repo",
                "write_access: false",
                "execution_lane: remote_non_gui",
                "requires_network: true",
            ]
        ),
        "# Summary\n\nReject execution overrides.\n",
    )

    with pytest.raises(
        agentbridge.CompatibilityAdapterError,
        match="Unsupported markdown execution override\\(s\\): execution_lane, requires_network, target_repo, write_access",
    ):
        agentbridge.load_markdown_task(task_path)


def test_markdown_task_rejects_incomplete_front_matter(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    task_id = "T-20260706-100005-incomplete-markdown"
    task_path = _write_agentbridge_task(
        repo_root / "AgentBridge" / "tasks" / f"{task_id}.md",
        "\n".join(
            [
                f"id: {task_id}",
                "created_at: 2026-07-06T10:00:05Z",
                "requested_by: hermes",
                "source_runtime: hermes",
                "source_model: gpt-5.5",
                "source_provider: third-party-openai-compatible",
                "goal: >",
                "  Missing approval_level should fail closed.",
                "constraints:",
                "  - Stay inside the worktree.",
                "runner: codex",
                "requires_gui: false",
                "artifacts_out:",
                "  - artifacts/example-output.txt",
            ]
        ),
        "# Summary\n\nReject incomplete markdown.\n",
    )

    with pytest.raises(
        agentbridge.CompatibilityAdapterError,
        match="Missing required markdown task fields: approval_level",
    ):
        agentbridge.load_markdown_task(task_path)


def test_host_local_runner_accepts_agentbridge_markdown_task_without_sidecar(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "AGENTS.md").write_text("stub", encoding="utf-8")
    copy_runtime_config(repo_root)

    task_id = "T-20260706-100002-host-local-intake"
    task_path = _write_agentbridge_task(
        repo_root / "AgentBridge" / "tasks" / f"{task_id}.md",
        "\n".join(
            [
                f"id: {task_id}",
                "created_at: 2026-07-06T10:00:02Z",
                "requested_by: hermes",
                "source_runtime: hermes",
                "source_model: gpt-5.5",
                "source_provider: third-party-openai-compatible",
                "goal: >",
                "  Prove host_local accepts markdown intake directly.",
                "constraints:",
                "  - Keep the test repo local.",
                "runner: codex",
                "requires_gui: false",
                "approval_level: manual_only",
                "artifacts_out:",
                "  - .ai/runs/<run_id>/T-20260706-100002-host-local-intake/result.json",
            ]
        ),
        "\n".join(
            [
                "# Summary",
                "",
                "Markdown intake through host_local.",
                "",
                "# Requested Actions",
                "",
                "1. Route the markdown task through the canonical runtime without a sidecar file.",
            ]
        ),
    )

    class FakeWorker:
        def run(self, request: WorkerRequest) -> WorkerResult:
            assert f"task_id: {task_id}" in request.prompt
            assert "title: Markdown intake through host_local." in request.prompt
            assert "risk_level: high" in request.prompt
            return WorkerResult(
                final_response="MARKDOWN_OK",
                raw_result={"kind": "fake"},
            )

    agentbridge_root = repo_root / "AgentBridge"
    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            agentbridge_root=agentbridge_root,
            run_id="markdown-intake-test",
        ),
        FakeWorker(),
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    verification_payload = json.loads(
        (result_path.parent / "verification_summary.json").read_text(encoding="utf-8")
    )
    evidence_payload = json.loads(
        (result_path.parent / "evidence_index.json").read_text(encoding="utf-8")
    )
    projection_path = agentbridge_root / "results" / f"{task_id}.md"
    artifact_path = agentbridge_root / "artifacts" / f"{task_id}-worker-output.txt"
    indexed_paths = {entry["relative_path"] for entry in evidence_payload["entries"]}

    assert result_path == (
        repo_root / ".ai" / "runs" / "markdown-intake-test" / task_id / "result.json"
    )
    assert result_payload["task_id"] == task_id
    assert result_payload["lane"] == "host_local"
    assert result_payload["compatibility_projection_ref"] == f"AgentBridge/results/{task_id}.md"
    assert verification_payload["status"] == "no_commands_configured"
    assert projection_path.exists()
    assert artifact_path.exists()
    assert artifact_path.read_text(encoding="utf-8") == "MARKDOWN_OK"
    assert f".ai/runs/markdown-intake-test/{task_id}/result.json" in indexed_paths
    assert f"AgentBridge/results/{task_id}.md" in indexed_paths
    assert not (task_path.with_suffix(".json")).exists()
