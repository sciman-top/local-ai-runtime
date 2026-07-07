from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any, Callable


ENV_SENSITIVE_BRINGUP_GATES = {"independent_key", "independent_base_url"}
KNOWN_GOOD_FILENAME_RE = re.compile(r"known-good-\d{8}-\d{6}(?:-\d{3})?\.json")
BOUNDARY_FILENAME_RE = re.compile(r"verify-hermes-boundary-\d{8}-\d{6}(?:-\d{3})?\.json")
HERMES_BASELINE_REQUIRED_SNIPPETS = [
    "历史基线",
    "compatibility lane",
    "historical operator evidence",
    "不是当前通用编排器主线的 authoritative truth",
]
CERTIFIED_BASELINE_REQUIRED_SNIPPETS = [
    "certified historical baseline",
    "compatibility projection",
]

GateRunner = Callable[[str, Path, Path | None], dict[str, Any]]


@dataclass(frozen=True)
class HermesParitySummary:
    run_id: str
    run_root: Path
    summary_path: Path
    snapshot_root: Path
    baseline_doc_path: str
    implementation_status_path: str
    known_good_snapshot_path: str
    boundary_snapshot_path: str
    known_good_anchor_mentions: dict[str, str]
    boundary_anchor_mentions: dict[str, str]
    contract_ok: bool
    known_good_snapshot_ok: bool
    bringup_gate_ready: bool
    bringup_failed_gates: list[str]
    env_sensitive_failed_gates: list[str]
    non_env_failed_gates: list[str]
    anchor_alignment_ok: bool
    current_truth_boundary_ok: bool
    historical_snapshot_mapping_ok: bool
    container_lifecycle_ok: bool
    claim_boundary: str
    next_gap: str
    ok: bool
    issues: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "run_root": str(self.run_root),
            "summary_path": str(self.summary_path),
            "snapshot_root": str(self.snapshot_root),
            "baseline_doc_path": self.baseline_doc_path,
            "implementation_status_path": self.implementation_status_path,
            "known_good_snapshot_path": self.known_good_snapshot_path,
            "boundary_snapshot_path": self.boundary_snapshot_path,
            "known_good_anchor_mentions": dict(self.known_good_anchor_mentions),
            "boundary_anchor_mentions": dict(self.boundary_anchor_mentions),
            "contract_ok": self.contract_ok,
            "known_good_snapshot_ok": self.known_good_snapshot_ok,
            "bringup_gate_ready": self.bringup_gate_ready,
            "bringup_failed_gates": list(self.bringup_failed_gates),
            "env_sensitive_failed_gates": list(self.env_sensitive_failed_gates),
            "non_env_failed_gates": list(self.non_env_failed_gates),
            "anchor_alignment_ok": self.anchor_alignment_ok,
            "current_truth_boundary_ok": self.current_truth_boundary_ok,
            "historical_snapshot_mapping_ok": self.historical_snapshot_mapping_ok,
            "container_lifecycle_ok": self.container_lifecycle_ok,
            "claim_boundary": self.claim_boundary,
            "next_gap": self.next_gap,
            "ok": self.ok,
            "issues": list(self.issues),
        }


def build_hermes_parity_run_id() -> str:
    return "hermes-parity-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def run_hermes_parity(
    repo_root: Path,
    *,
    run_id: str | None = None,
    gate_runner: GateRunner | None = None,
) -> HermesParitySummary:
    repo_root = repo_root.resolve()
    actual_run_id = run_id or build_hermes_parity_run_id()
    run_root = repo_root / "private-local" / "hermes-parity" / actual_run_id
    if run_root.exists():
        raise FileExistsError(f"Hermes parity run already exists: {run_root}")
    run_root.mkdir(parents=True, exist_ok=False)

    summary_path = run_root / "hermes-parity-summary.json"
    summary = collect_hermes_parity_summary(
        repo_root=repo_root,
        run_id=actual_run_id,
        run_root=run_root,
        summary_path=summary_path,
        gate_runner=gate_runner or _run_snapshot_gate,
    )
    summary_path.write_text(
        json.dumps(summary.to_dict(), indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    if not summary.ok:
        raise RuntimeError("Hermes parity suite found issues: " + "; ".join(summary.issues))
    return summary


def collect_hermes_parity_summary(
    *,
    repo_root: Path,
    run_id: str,
    run_root: Path,
    summary_path: Path,
    gate_runner: GateRunner,
) -> HermesParitySummary:
    issues: list[str] = []

    planning_status_path = repo_root / "docs" / "architecture" / "planning-status.json"
    handoff_summary_path = repo_root / "docs" / "platforms" / "hermes" / "当前交接摘要.md"
    handoff_checklist_path = repo_root / "docs" / "platforms" / "hermes" / "接手检查单.md"
    snapshot_root = repo_root / "snapshots" / "agentbridge-20260628"
    implementation_status_path = snapshot_root / "docs" / "implementation-status.md"

    planning_payload = _load_json(planning_status_path)
    baseline_ref = str(planning_payload.get("certified_baseline", {}).get("evidence_ref") or "").strip()
    claim_boundary = str(planning_payload.get("certified_baseline", {}).get("claim_boundary") or "").strip()
    current_truth_boundary_ok = True
    expected_baseline_ref = "docs/platforms/hermes/README.md"
    if baseline_ref != expected_baseline_ref:
        current_truth_boundary_ok = False
        issues.append(
            f"Expected certified_baseline.evidence_ref {expected_baseline_ref}, found {baseline_ref or '<missing>'}."
        )
    baseline_doc_path = repo_root / baseline_ref if baseline_ref else repo_root / expected_baseline_ref
    if not baseline_doc_path.exists():
        current_truth_boundary_ok = False
        issues.append(f"Missing baseline doc: {baseline_doc_path}")

    if not baseline_ref:
        current_truth_boundary_ok = False
    if not claim_boundary:
        current_truth_boundary_ok = False
        issues.append("planning-status certified_baseline.claim_boundary is empty.")
    else:
        missing_claim_boundary = [
            snippet for snippet in CERTIFIED_BASELINE_REQUIRED_SNIPPETS if snippet not in claim_boundary
        ]
        if missing_claim_boundary:
            current_truth_boundary_ok = False
            issues.append(
                "planning-status certified_baseline.claim_boundary is missing: "
                + ", ".join(missing_claim_boundary)
            )

    baseline_text = baseline_doc_path.read_text(encoding="utf-8") if baseline_doc_path.exists() else ""
    missing_baseline_snippets = [
        snippet for snippet in HERMES_BASELINE_REQUIRED_SNIPPETS if snippet not in baseline_text
    ]
    if missing_baseline_snippets:
        current_truth_boundary_ok = False
        issues.append(
            f"{baseline_doc_path.relative_to(repo_root)} is missing baseline snippets: "
            + ", ".join(missing_baseline_snippets)
        )

    implementation_status_text = implementation_status_path.read_text(encoding="utf-8")
    handoff_summary_text = handoff_summary_path.read_text(encoding="utf-8")
    handoff_checklist_text = handoff_checklist_path.read_text(encoding="utf-8")

    known_good_anchor_mentions = {
        "implementation_status": _extract_anchor_after_marker(
            text=implementation_status_text,
            marker="the latest verified known-good snapshot is:",
            pattern=KNOWN_GOOD_FILENAME_RE,
            label=str(implementation_status_path.relative_to(repo_root)),
        ),
        "handoff_summary": _extract_anchor_filename(
            text=handoff_summary_text,
            pattern=KNOWN_GOOD_FILENAME_RE,
            label=str(handoff_summary_path.relative_to(repo_root)),
        ),
        "handoff_checklist": _extract_anchor_filename(
            text=handoff_checklist_text,
            pattern=KNOWN_GOOD_FILENAME_RE,
            label=str(handoff_checklist_path.relative_to(repo_root)),
        ),
    }
    boundary_anchor_mentions = {
        "implementation_status": _extract_anchor_after_marker(
            text=implementation_status_text,
            marker="the latest verified boundary evidence is:",
            pattern=BOUNDARY_FILENAME_RE,
            label=str(implementation_status_path.relative_to(repo_root)),
        ),
        "handoff_summary": _extract_anchor_filename(
            text=handoff_summary_text,
            pattern=BOUNDARY_FILENAME_RE,
            label=str(handoff_summary_path.relative_to(repo_root)),
        ),
        "handoff_checklist": _extract_anchor_filename(
            text=handoff_checklist_text,
            pattern=BOUNDARY_FILENAME_RE,
            label=str(handoff_checklist_path.relative_to(repo_root)),
        ),
    }

    anchor_alignment_ok = True
    known_good_filenames = set(known_good_anchor_mentions.values())
    if len(known_good_filenames) != 1:
        anchor_alignment_ok = False
        issues.append(
            f"Known-good anchor drift detected: {known_good_anchor_mentions}"
        )
    boundary_filenames = set(boundary_anchor_mentions.values())
    if len(boundary_filenames) != 1:
        anchor_alignment_ok = False
        issues.append(
            f"Boundary anchor drift detected: {boundary_anchor_mentions}"
        )

    known_good_snapshot_path = snapshot_root / "docs" / known_good_anchor_mentions["implementation_status"]
    boundary_snapshot_path = snapshot_root / "docs" / boundary_anchor_mentions["implementation_status"]
    if not known_good_snapshot_path.exists():
        anchor_alignment_ok = False
        issues.append(f"Missing known-good snapshot anchor: {known_good_snapshot_path}")
    if not boundary_snapshot_path.exists():
        anchor_alignment_ok = False
        issues.append(f"Missing boundary snapshot anchor: {boundary_snapshot_path}")

    contract_result = gate_runner("contract", snapshot_root, None)
    known_good_result = gate_runner("known_good", snapshot_root, known_good_snapshot_path)
    bringup_result = gate_runner("bringup", snapshot_root, None)

    contract_ok = bool(contract_result.get("ok") is True)
    known_good_snapshot_ok = bool(known_good_result.get("ok") is True)
    bringup_gate_ready = bool(bringup_result.get("ready") is True)
    bringup_failed_gates = [
        str(item.get("gate"))
        for item in bringup_result.get("gates", [])
        if item.get("passed") is False
    ]
    env_sensitive_failed_gates = [
        gate for gate in bringup_failed_gates if gate in ENV_SENSITIVE_BRINGUP_GATES
    ]
    non_env_failed_gates = [
        gate for gate in bringup_failed_gates if gate not in ENV_SENSITIVE_BRINGUP_GATES
    ]

    if not contract_ok:
        issues.append(f"Snapshot AgentBridge contract gate is not green: {contract_result}")
    if not known_good_snapshot_ok:
        issues.append(f"Known-good snapshot validation is not green: {known_good_result}")
    if non_env_failed_gates:
        issues.append(
            "Hermes bring-up gates failed outside the env-sensitive boundary: "
            + ", ".join(non_env_failed_gates)
        )

    runtime_profile_path = snapshot_root / "docs" / "hermes-runtime.json"
    image_resolution_path = snapshot_root / "docs" / "hermes-image-resolution.json"
    runtime_profile = _load_json(runtime_profile_path)
    image_resolution = _load_json(image_resolution_path)
    known_good_payload = _load_json(known_good_snapshot_path)
    boundary_payload = _load_json(boundary_snapshot_path)

    historical_snapshot_mapping_ok = anchor_alignment_ok and contract_ok and known_good_snapshot_ok
    if str(known_good_payload.get("hermes_image_digest") or "") != str(image_resolution.get("repo_digest") or ""):
        historical_snapshot_mapping_ok = False
        issues.append(
            "known-good snapshot hermes_image_digest does not match hermes-image-resolution repo_digest."
        )
    if str(known_good_payload.get("hermes_image_resolution_status") or "") != "resolved":
        historical_snapshot_mapping_ok = False
        issues.append("known-good snapshot hermes_image_resolution_status is not resolved.")
    if str(known_good_payload.get("hermes_bootstrap_model") or "") != str(runtime_profile.get("bootstrap_model") or ""):
        historical_snapshot_mapping_ok = False
        issues.append("known-good snapshot hermes_bootstrap_model does not match hermes-runtime bootstrap_model.")
    if str(known_good_payload.get("hermes_runtime_image") or "") != str(runtime_profile.get("runtime_image") or ""):
        historical_snapshot_mapping_ok = False
        issues.append("known-good snapshot hermes_runtime_image does not match hermes-runtime runtime_image.")
    if str(known_good_payload.get("hermes_runtime_user") or "") != str(runtime_profile.get("runtime_user") or ""):
        historical_snapshot_mapping_ok = False
        issues.append("known-good snapshot hermes_runtime_user does not match hermes-runtime runtime_user.")

    container_lifecycle_ok = not non_env_failed_gates
    if str(boundary_payload.get("bootstrap_model") or "") != str(runtime_profile.get("bootstrap_model") or ""):
        container_lifecycle_ok = False
        issues.append("Boundary snapshot bootstrap_model does not match hermes-runtime bootstrap_model.")
    if str(boundary_payload.get("runtime_user") or "") != str(runtime_profile.get("runtime_user") or ""):
        container_lifecycle_ok = False
        issues.append("Boundary snapshot runtime_user does not match hermes-runtime runtime_user.")
    if str(boundary_payload.get("requested_container_user_override") or "") != str(
        runtime_profile.get("container_start_user") or ""
    ):
        container_lifecycle_ok = False
        issues.append(
            "Boundary snapshot requested_container_user_override does not match hermes-runtime container_start_user."
        )
    if int(boundary_payload.get("service_uid") or -1) != int(known_good_payload.get("hermes_service_uid") or -2):
        container_lifecycle_ok = False
        issues.append("Boundary snapshot service_uid does not match known-good hermes_service_uid.")
    if int(boundary_payload.get("service_gid") or -1) != int(known_good_payload.get("hermes_service_gid") or -2):
        container_lifecycle_ok = False
        issues.append("Boundary snapshot service_gid does not match known-good hermes_service_gid.")
    if boundary_payload.get("service_uidgid_present") is not True:
        container_lifecycle_ok = False
        issues.append("Boundary snapshot does not confirm service_uidgid_present=true.")
    if boundary_payload.get("requested_read_only_rootfs") is not True:
        container_lifecycle_ok = False
        issues.append("Boundary snapshot does not confirm requested_read_only_rootfs=true.")
    if boundary_payload.get("observed_read_only_rootfs") is not True:
        container_lifecycle_ok = False
        issues.append("Boundary snapshot does not confirm observed_read_only_rootfs=true.")
    if boundary_payload.get("rootfs_write_blocked") is not True:
        container_lifecycle_ok = False
        issues.append("Boundary snapshot does not confirm rootfs_write_blocked=true.")
    tmpfs_targets = set(boundary_payload.get("tmpfs_targets") or [])
    if not {"/run", "/tmp"}.issubset(tmpfs_targets):
        container_lifecycle_ok = False
        issues.append(f"Boundary snapshot tmpfs_targets is missing /run or /tmp: {sorted(tmpfs_targets)}.")
    if boundary_payload.get("cap_drop_all_present") is not False:
        container_lifecycle_ok = False
        issues.append("Boundary snapshot unexpectedly reports cap_drop_all_present=true.")

    if not current_truth_boundary_ok:
        issues.append("Current repo truth does not keep the Hermes baseline boundary aligned.")

    claim_boundary_text = (
        "repo-side Hermes parity + historical snapshot mapping proof only; "
        "not remote runner, not platform compatibility green, and not live accepted."
    )
    next_gap = "P6-T03 vm_gui conditional promotion evidence"
    ok = current_truth_boundary_ok and historical_snapshot_mapping_ok and container_lifecycle_ok

    return HermesParitySummary(
        run_id=run_id,
        run_root=run_root,
        summary_path=summary_path,
        snapshot_root=snapshot_root,
        baseline_doc_path=str(baseline_doc_path.relative_to(repo_root)).replace("\\", "/"),
        implementation_status_path=str(implementation_status_path.relative_to(repo_root)).replace("\\", "/"),
        known_good_snapshot_path=str(known_good_snapshot_path.relative_to(repo_root)).replace("\\", "/"),
        boundary_snapshot_path=str(boundary_snapshot_path.relative_to(repo_root)).replace("\\", "/"),
        known_good_anchor_mentions=known_good_anchor_mentions,
        boundary_anchor_mentions=boundary_anchor_mentions,
        contract_ok=contract_ok,
        known_good_snapshot_ok=known_good_snapshot_ok,
        bringup_gate_ready=bringup_gate_ready,
        bringup_failed_gates=bringup_failed_gates,
        env_sensitive_failed_gates=env_sensitive_failed_gates,
        non_env_failed_gates=non_env_failed_gates,
        anchor_alignment_ok=anchor_alignment_ok,
        current_truth_boundary_ok=current_truth_boundary_ok,
        historical_snapshot_mapping_ok=historical_snapshot_mapping_ok,
        container_lifecycle_ok=container_lifecycle_ok,
        claim_boundary=claim_boundary_text,
        next_gap=next_gap,
        ok=ok,
        issues=issues,
    )


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_anchor_filename(*, text: str, pattern: re.Pattern[str], label: str) -> str:
    match = pattern.search(text)
    if match is None:
        raise ValueError(f"Missing anchor filename in {label}")
    return match.group(0)


def _extract_anchor_after_marker(*, text: str, marker: str, pattern: re.Pattern[str], label: str) -> str:
    marker_index = text.find(marker)
    if marker_index == -1:
        raise ValueError(f"Missing marker '{marker}' in {label}")
    return _extract_anchor_filename(text=text[marker_index:], pattern=pattern, label=label)


def _run_snapshot_gate(name: str, snapshot_root: Path, known_good_path: Path | None) -> dict[str, Any]:
    script_name = {
        "contract": "test-agentbridge-contract.ps1",
        "known_good": "test-known-good-snapshot.ps1",
        "bringup": "test-hermes-bringup-gates.ps1",
    }[name]
    script_path = snapshot_root / "scripts" / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Missing snapshot gate script: {script_path}")

    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if powershell is None:
        raise FileNotFoundError("PowerShell is required to run Hermes parity gates.")

    command_parts = [
        "$r = &",
        _ps_quote(str(script_path)),
        "-Root",
        _ps_quote(str(snapshot_root)),
    ]
    if name == "known_good":
        if known_good_path is None:
            raise ValueError("known_good gate requires a snapshot path.")
        command_parts.extend(
            [
                "-SnapshotPath",
                _ps_quote(str(known_good_path)),
            ]
        )
    command_parts.extend([";", "$r | ConvertTo-Json -Depth 10"])
    completed = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            " ".join(command_parts),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=snapshot_root,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Snapshot gate {name} failed (exit={completed.returncode}): {completed.stderr.strip() or completed.stdout.strip()}"
        )
    return json.loads(completed.stdout)


def _ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"
