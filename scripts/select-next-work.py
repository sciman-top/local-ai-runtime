from __future__ import annotations

import argparse
from datetime import date
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATUS_PATH = ROOT / "docs" / "architecture" / "planning-status.json"
DEFAULT_POLICY_PATH = ROOT / "docs" / "architecture" / "next-work-selection-policy.json"
DEFAULT_PREFLIGHT_PATH = ROOT / "scripts" / "governance" / "preflight.ps1"
DEFAULT_VERIFIER_PATH = ROOT / "scripts" / "verify-planning-status.py"


def main() -> int:
    parser = argparse.ArgumentParser(description="Select the next local orchestrator work item.")
    parser.add_argument("--repo-root", default=str(ROOT))
    parser.add_argument("--status-path", default=str(DEFAULT_STATUS_PATH))
    parser.add_argument("--policy-path", default=str(DEFAULT_POLICY_PATH))
    parser.add_argument("--preflight-path", default=str(DEFAULT_PREFLIGHT_PATH))
    parser.add_argument("--verifier-path", default=str(DEFAULT_VERIFIER_PATH))
    args = parser.parse_args()

    try:
        result = select_next_work(
            repo_root=Path(args.repo_root),
            status_path=Path(args.status_path),
            policy_path=Path(args.policy_path),
            preflight_path=Path(args.preflight_path),
            verifier_path=Path(args.verifier_path),
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def select_next_work(
    *,
    repo_root: Path,
    status_path: Path,
    policy_path: Path,
    preflight_path: Path,
    verifier_path: Path,
) -> dict[str, object]:
    root = repo_root.resolve(strict=False)
    try:
        policy = _load_policy(policy_path)
        reasons = {item["next_action"]: item["why"] for item in policy["selection_order"]}
    except ValueError as exc:
        return _build_result(
            action="refresh_governance_evidence_first",
            reason="Governance Overlay policy is missing or unreadable, so repo-level evidence and entrypoints must be refreshed first.",
            policy_path=policy_path,
            governance_issues=[str(exc)],
            verifier_status=None,
            preflight_status=None,
            live_posture=None,
        )

    governance_issues = _inspect_governance_entrypoints(root=root, policy=policy)
    if governance_issues:
        return _build_result(
            action="refresh_governance_evidence_first",
            reason=reasons["refresh_governance_evidence_first"],
            policy_path=policy_path,
            governance_issues=governance_issues,
            verifier_status=None,
            preflight_status=None,
            live_posture=None,
        )

    review_expires_at = str(policy.get("review_expires_at") or "").strip()
    if review_expires_at and _is_expired(review_expires_at):
        return _build_result(
            action="refresh_governance_evidence_first",
            reason="Governance selector policy review has expired, so repo-level evidence must be refreshed before promoting product work.",
            policy_path=policy_path,
            governance_issues=[],
            verifier_status=None,
            preflight_status=None,
            live_posture=None,
        )

    verifier_status = _run_verifier(
        repo_root=root,
        status_path=status_path,
        verifier_path=verifier_path,
    )
    if verifier_status["exit_code"] != 0:
        return _build_result(
            action="repair_gate_first",
            reason=reasons["repair_gate_first"],
            policy_path=policy_path,
            governance_issues=[],
            verifier_status=verifier_status,
            preflight_status=None,
            live_posture=None,
        )

    preflight_status = _run_preflight(repo_root=root, preflight_path=preflight_path)
    if preflight_status["exit_code"] != 0:
        return _build_result(
            action="repair_gate_first",
            reason=reasons["repair_gate_first"],
            policy_path=policy_path,
            governance_issues=[],
            verifier_status=verifier_status,
            preflight_status=preflight_status,
            live_posture=None,
        )

    payload = _load_json(status_path)
    live_posture = payload.get("current_live_posture", {})
    gateway_status = str(live_posture.get("gpt54_gateway_probe_status") or "").strip()
    exec_status = str(live_posture.get("codex_exec_probe_status") or "").strip()
    if gateway_status != "ready" or exec_status != "ready":
        return _build_result(
            action="phase1_prereq_probe_first",
            reason=reasons["phase1_prereq_probe_first"],
            policy_path=policy_path,
            governance_issues=[],
            verifier_status=verifier_status,
            preflight_status=preflight_status,
            live_posture=live_posture,
        )

    return _build_result(
        action="promote_phase1_execution",
        reason=reasons["promote_phase1_execution"],
        policy_path=policy_path,
        governance_issues=[],
        verifier_status=verifier_status,
        preflight_status=preflight_status,
        live_posture=live_posture,
    )


def _build_result(
    *,
    action: str,
    reason: str,
    policy_path: Path,
    governance_issues: list[str],
    verifier_status: dict[str, object] | None,
    preflight_status: dict[str, object] | None,
    live_posture: dict[str, object] | None,
) -> dict[str, object]:
    return {
        "status": "pass",
        "policy_path": str(policy_path.resolve(strict=False)).replace("\\", "/"),
        "next_action": action,
        "why": reason,
        "governance_issues": governance_issues,
        "verifier_status": verifier_status,
        "preflight_status": preflight_status,
        "current_live_posture": live_posture,
    }


def _inspect_governance_entrypoints(*, root: Path, policy: dict[str, object]) -> list[str]:
    missing: list[str] = []
    for relative_path in policy.get("required_entrypoints", []):
        path = root / relative_path
        if not path.exists():
            missing.append(f"missing entrypoint: {relative_path}")

    for item in policy.get("required_doc_refs", []):
        path = root / item["path"]
        if not path.exists():
            missing.append(f"missing doc ref: {item['path']}")
            continue
        text = path.read_text(encoding="utf-8")
        if item["contains"] not in text:
            missing.append(f"missing required text: {item['path']}:{item['contains']}")

    return missing


def _run_verifier(*, repo_root: Path, status_path: Path, verifier_path: Path) -> dict[str, object]:
    command = [
        sys.executable,
        str(verifier_path),
        "--repo-root",
        str(repo_root),
        "--status-path",
        str(status_path),
    ]
    result = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    payload = None
    if result.returncode == 0 and result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = None
    return {
        "command": " ".join(command),
        "exit_code": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "payload": payload,
    }


def _run_preflight(*, repo_root: Path, preflight_path: Path) -> dict[str, object]:
    command = [
        "pwsh",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(preflight_path),
        "-DisableAutoCommit",
        "-Json",
    ]
    result = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    payload = None
    stdout = result.stdout.strip()
    if result.returncode == 0 and stdout:
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            payload = None
    return {
        "command": " ".join(command),
        "exit_code": result.returncode,
        "stdout": stdout,
        "stderr": result.stderr.strip(),
        "payload": payload,
    }


def _load_policy(path: Path) -> dict[str, object]:
    payload = _load_json(path)
    required_fields = [
        "policy_id",
        "reviewed_on",
        "review_expires_at",
        "allowed_next_actions",
        "selection_order",
        "required_entrypoints",
        "required_doc_refs",
        "rollback_ref",
    ]
    missing_fields = [field for field in required_fields if field not in payload]
    if missing_fields:
        raise ValueError(
            "next-work selection policy is missing fields: " + ", ".join(missing_fields)
        )
    review_expires_at = payload.get("review_expires_at")
    if not isinstance(review_expires_at, str) or not review_expires_at.strip():
        raise ValueError("next-work selection policy review_expires_at must be a non-empty string")
    try:
        date.fromisoformat(review_expires_at)
    except ValueError as exc:
        raise ValueError("next-work selection policy review_expires_at must be a valid ISO date") from exc
    return payload


def _is_expired(review_expires_at: str) -> bool:
    return date.fromisoformat(review_expires_at) < date.today()


def _load_json(path: Path) -> dict[str, object]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"JSON file is not readable: {path} ({exc})") from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON file is invalid: {path} ({exc.msg})") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON file must be an object: {path}")
    return payload


if __name__ == "__main__":
    raise SystemExit(main())
