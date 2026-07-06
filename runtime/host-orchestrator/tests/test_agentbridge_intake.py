from __future__ import annotations

import json
from pathlib import Path

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


def test_markdown_task_to_canonical_payload_preserves_explicit_canonical_fields(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    task_id = "T-20260706-100001-lossless-intake"
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
                "goal: >",
                "  Preserve every canonical intake field from markdown front matter.",
                "constraints:",
                "  - Stay inside the worktree.",
                "runner: codex",
                "approval_level: manual_only",
                "target_repo: external-repo-alias",
                "base_branch: release/2026-07",
                "branch_name: codex/d-t01-explicit",
                "worktree_path: .worktrees/d-t01-explicit",
                "allowed_paths:",
                "  - runtime/host-orchestrator/**",
                "  - docs/specs/**",
                "forbidden_paths:",
                "  - docs/backlog/**",
                "  - .env",
                "write_access: false",
                "risk_level: critical",
                "merge_policy: draft_pr_only",
                "execution_lane: host_local",
                "requires_network: true",
                "requires_gui: true",
                "depends_on:",
                "  - D-T00",
                "artifacts_out:",
                "  - .ai/runs/<run_id>/T-20260706-100001-lossless-intake/result.json",
                "handoff_policy: handoff_always",
                "verification_commands:",
                "  build: uv run --project ./runtime/host-orchestrator python -m pytest",
                "  test: uv run --project ./runtime/host-orchestrator python -m pytest -k intake",
                "  lint: null",
                "  typecheck: null",
                "  contract: python ./scripts/verify-planning-status.py",
                "  hotspot: null",
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
    assert canonical_task.target_repo == "external-repo-alias"
    assert canonical_task.base_branch == "release/2026-07"
    assert canonical_task.branch_name == "codex/d-t01-explicit"
    assert canonical_task.worktree_path == ".worktrees/d-t01-explicit"
    assert canonical_task.allowed_paths == (
        "runtime/host-orchestrator/**",
        "docs/specs/**",
    )
    assert canonical_task.forbidden_paths == ("docs/backlog/**", ".env")
    assert canonical_task.write_access is False
    assert canonical_task.risk_level == "critical"
    assert canonical_task.merge_policy == "draft_pr_only"
    assert canonical_task.execution_lane == "host_local"
    assert canonical_task.requires_network is True
    assert canonical_task.requires_gui is True
    assert canonical_task.depends_on == ("D-T00",)
    assert canonical_task.artifacts_out == (
        ".ai/runs/<run_id>/T-20260706-100001-lossless-intake/result.json",
    )
    assert canonical_task.handoff_policy == "handoff_always"
    assert (
        canonical_task.verification_commands.test
        == "uv run --project ./runtime/host-orchestrator python -m pytest -k intake"
    )
    assert canonical_task.verification_commands.contract == "python ./scripts/verify-planning-status.py"
    assert canonical_task.description.startswith("---\nid: T-20260706-100001-lossless-intake")


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
                "verification_commands:",
                "  build: null",
                "  test: python -c \"print('TEST_OK')\"",
                "  lint: null",
                "  typecheck: null",
                "  contract: python -c \"print('CONTRACT_OK')\"",
                "  hotspot: null",
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

    runner = HostLocalRunner(
        HostLocalConfig(
            workspace_root=repo_root,
            layout=RuntimeLayout.from_repo_root(repo_root),
            run_id="markdown-intake-test",
        ),
        FakeWorker(),
    )

    result_path = runner.run_task(task_path)
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    verification_payload = json.loads(
        (result_path.parent / "verification_summary.json").read_text(encoding="utf-8")
    )

    assert result_path == (
        repo_root / ".ai" / "runs" / "markdown-intake-test" / task_id / "result.json"
    )
    assert result_payload["task_id"] == task_id
    assert result_payload["lane"] == "host_local"
    assert verification_payload["status"] == "pass"
    assert not (task_path.with_suffix(".json")).exists()
