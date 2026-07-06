from __future__ import annotations

from pathlib import Path

from host_orchestrator.canonical_task import CanonicalTask, VerificationCommands
from host_orchestrator.verification import run_verification


def _task_with_commands(*, test: str | None, contract: str | None) -> CanonicalTask:
    return CanonicalTask(
        path=Path("task.json"),
        task_id="TASK-VERIFY-001",
        title="Verification smoke",
        description="exercise verification runner",
        target_repo="local-ai-dev-orchestrator",
        base_branch="main",
        branch_name="codex/verify",
        worktree_path=".",
        allowed_paths=("runtime/host-orchestrator/**",),
        forbidden_paths=(".env",),
        write_access=True,
        risk_level="medium",
        merge_policy="manual_merge_only",
        execution_lane="host_local",
        requires_network=False,
        requires_gui=False,
        depends_on=(),
        artifacts_out=(),
        handoff_policy="handoff_on_risk",
        verification_commands=VerificationCommands(
            build=None,
            test=test,
            lint=None,
            typecheck=None,
            contract=contract,
            hotspot=None,
        ),
    )


def test_run_verification_executes_test_and_contract_only(tmp_path: Path) -> None:
    summary = run_verification(
        task=_task_with_commands(
            test="python -c \"print('TEST_OK')\"",
            contract="python -c \"print('CONTRACT_OK')\"",
        ),
        workspace_root=tmp_path,
    )

    assert summary["status"] == "pass"
    outcomes = summary["commands_run"]
    assert [outcome["gate"] for outcome in outcomes] == [
        "build",
        "lint",
        "typecheck",
        "test",
        "contract",
        "hotspot",
    ]
    assert outcomes[0]["status"] == "gate_na"
    assert outcomes[3]["status"] == "pass"
    assert "TEST_OK" in outcomes[3]["stdout"]
    assert outcomes[4]["status"] == "pass"
    assert "CONTRACT_OK" in outcomes[4]["stdout"]


def test_run_verification_reports_no_commands_configured(tmp_path: Path) -> None:
    summary = run_verification(
        task=_task_with_commands(test=None, contract=None),
        workspace_root=tmp_path,
    )

    assert summary["status"] == "no_commands_configured"
    test_outcome = next(outcome for outcome in summary["commands_run"] if outcome["gate"] == "test")
    contract_outcome = next(
        outcome for outcome in summary["commands_run"] if outcome["gate"] == "contract"
    )
    assert test_outcome["status"] == "not_configured"
    assert contract_outcome["status"] == "not_configured"


def test_run_verification_reports_failure_when_gate_command_fails(tmp_path: Path) -> None:
    summary = run_verification(
        task=_task_with_commands(
            test="python -c \"import sys; print('BROKEN'); sys.exit(3)\"",
            contract="python -c \"print('CONTRACT_OK')\"",
        ),
        workspace_root=tmp_path,
    )

    assert summary["status"] == "failed"
    test_outcome = next(outcome for outcome in summary["commands_run"] if outcome["gate"] == "test")
    assert test_outcome["status"] == "fail"
    assert test_outcome["exit_code"] == 3
    assert "BROKEN" in test_outcome["stdout"]
