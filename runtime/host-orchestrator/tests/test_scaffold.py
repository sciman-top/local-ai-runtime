from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]


def test_host_orchestrator_scaffold_has_expected_layout() -> None:
    expected_paths = [
        PROJECT_ROOT / "pyproject.toml",
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "scripts",
        PROJECT_ROOT / "src" / "host_orchestrator" / "__init__.py",
        PROJECT_ROOT / "src" / "host_orchestrator" / "__main__.py",
        PROJECT_ROOT / "src" / "host_orchestrator" / "cli.py",
        PROJECT_ROOT / "src" / "host_orchestrator" / "paths.py",
    ]

    missing = [
        str(path.relative_to(PROJECT_ROOT))
        for path in expected_paths
        if not path.exists()
    ]

    assert not missing, f"Missing scaffold entries: {missing}"


def test_layout_defaults_point_to_repo_private_local() -> None:
    from host_orchestrator.paths import RuntimeLayout

    layout = RuntimeLayout.from_repo_root(REPO_ROOT)

    assert layout.control_plane_db == REPO_ROOT / "private-local" / "control-plane" / "control-plane.db"
    assert layout.control_plane_logs == REPO_ROOT / "private-local" / "control-plane" / "logs"
    assert layout.wave_smokes == REPO_ROOT / "private-local" / "wave-smokes"


def test_sdk_worker_request_maps_to_codex_thread_run() -> None:
    from openai_codex import ApprovalMode, Sandbox

    from host_orchestrator.worker import WorkerRequest, build_thread_start_options, build_turn_run_options

    request = WorkerRequest(
        prompt="Diagnose the failing smoke test.",
        cwd=REPO_ROOT,
        model="gpt-5.4",
    )

    start_options = build_thread_start_options(request)
    run_options = build_turn_run_options(request)

    assert start_options == {
        "cwd": str(REPO_ROOT),
        "model": "gpt-5.4",
        "sandbox": Sandbox.workspace_write,
        "approval_mode": ApprovalMode.deny_all,
    }
    assert run_options == {
        "cwd": str(REPO_ROOT),
        "model": "gpt-5.4",
        "sandbox": Sandbox.workspace_write,
        "approval_mode": ApprovalMode.deny_all,
    }


def test_sdk_worker_executes_prompt_via_thread_run() -> None:
    from openai_codex import ApprovalMode, Sandbox

    from host_orchestrator.worker import CodexSdkWorker, WorkerRequest

    calls: dict[str, object] = {}

    class FakeThread:
        def run(self, input: str, **kwargs: object) -> object:
            calls["run"] = {"input": input, "kwargs": kwargs}
            return SimpleNamespace(final_response="WORKER_OK")

    class FakeCodex:
        def thread_start(self, **kwargs: object) -> FakeThread:
            calls["thread_start"] = kwargs
            return FakeThread()

    worker = CodexSdkWorker(FakeCodex())
    request = WorkerRequest(
        prompt="Implement the first safe slice.",
        cwd=REPO_ROOT,
        model="gpt-5.4",
    )

    result = worker.run(request)

    assert result.final_response == "WORKER_OK"
    assert calls["thread_start"] == {
        "cwd": str(REPO_ROOT),
        "model": "gpt-5.4",
        "sandbox": Sandbox.workspace_write,
        "approval_mode": ApprovalMode.deny_all,
    }
    assert calls["run"] == {
        "input": "Implement the first safe slice.",
        "kwargs": {
            "cwd": str(REPO_ROOT),
            "model": "gpt-5.4",
            "sandbox": Sandbox.workspace_write,
            "approval_mode": ApprovalMode.deny_all,
        },
    }
