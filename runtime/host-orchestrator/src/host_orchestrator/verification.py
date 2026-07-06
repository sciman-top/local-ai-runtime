from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Iterable

from host_orchestrator.canonical_task import CanonicalTask


MINIMAL_EXECUTED_GATES = {"test", "contract"}
FIXED_GATE_ORDER = ("build", "lint", "typecheck", "test", "contract", "hotspot")


@dataclass(frozen=True)
class GateOutcome:
    gate: str
    status: str
    command: str | None
    exit_code: int | None
    stdout: str
    stderr: str
    reason: str
    alternative_verification: str
    evidence_link: str
    expires_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "gate": self.gate,
            "status": self.status,
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "reason": self.reason,
            "alternative_verification": self.alternative_verification,
            "evidence_link": self.evidence_link,
            "expires_at": self.expires_at,
        }


def run_verification(
    *,
    task: CanonicalTask,
    workspace_root: Path,
) -> dict[str, object]:
    outcomes = [_evaluate_gate(gate=gate, task=task, workspace_root=workspace_root) for gate in FIXED_GATE_ORDER]
    executed = [outcome for outcome in outcomes if outcome.exit_code is not None]
    failed = [outcome for outcome in executed if outcome.status == "fail"]

    if not executed:
        status = "no_commands_configured"
    elif failed:
        status = "failed"
    else:
        status = "pass"

    return {
        "status": status,
        "commands_run": [outcome.to_dict() for outcome in outcomes],
    }


def _evaluate_gate(
    *,
    gate: str,
    task: CanonicalTask,
    workspace_root: Path,
) -> GateOutcome:
    command = getattr(task.verification_commands, gate)
    if gate not in MINIMAL_EXECUTED_GATES:
        return _gate_na_outcome(gate=gate, command=command)
    if command is None:
        return _missing_command_outcome(gate=gate)

    completed = subprocess.run(
        command,
        cwd=workspace_root,
        shell=True,
        text=True,
        capture_output=True,
        check=False,
    )
    return GateOutcome(
        gate=gate,
        status="pass" if completed.returncode == 0 else "fail",
        command=command,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        reason="",
        alternative_verification="",
        evidence_link="",
        expires_at="",
    )


def _gate_na_outcome(*, gate: str, command: str | None) -> GateOutcome:
    if gate == "build":
        return GateOutcome(
            gate=gate,
            status="gate_na",
            command=command,
            exit_code=None,
            stdout="",
            stderr="",
            reason="repo-owned build gate is not defined yet for the current Hermes -> AgentBridge -> Codex runtime mainline",
            alternative_verification="uv run --project .\\runtime\\host-orchestrator python -m pytest",
            evidence_link="docs/specs/acceptance-and-gates.md",
            expires_at="when a repo-owned build gate is introduced",
        )
    if gate == "hotspot":
        return GateOutcome(
            gate=gate,
            status="gate_na",
            command=command,
            exit_code=None,
            stdout="",
            stderr="",
            reason="repo-owned hotspot gate is not defined yet for the current Hermes -> AgentBridge -> Codex runtime mainline",
            alternative_verification="repo-side proof is currently limited to verifier + pytest + diff hygiene",
            evidence_link="docs/specs/acceptance-and-gates.md",
            expires_at="when a repo-owned hotspot gate is introduced",
        )
    return GateOutcome(
        gate=gate,
        status="gate_na",
        command=command,
        exit_code=None,
        stdout="",
        stderr="",
        reason=f"Phase C minimal verification runner does not execute the {gate} gate yet.",
        alternative_verification="Promote this gate after a repo-owned command and regression coverage exist.",
        evidence_link="docs/specs/acceptance-and-gates.md",
        expires_at="when the gate is promoted beyond the minimal verification runner",
    )


def _missing_command_outcome(*, gate: str) -> GateOutcome:
    return GateOutcome(
        gate=gate,
        status="not_configured",
        command=None,
        exit_code=None,
        stdout="",
        stderr="",
        reason=f"verification_commands.{gate} is not configured for this task.",
        alternative_verification="",
        evidence_link="",
        expires_at="",
    )
