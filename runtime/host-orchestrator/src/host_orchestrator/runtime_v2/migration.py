from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3

import yaml

from host_orchestrator.config_runtime import load_runtime_config
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.runtime_v2.evaluation import evaluate_regression_fixtures


def write_migration_manifest(*, layout: RuntimeLayout) -> dict[str, object]:
    layout = _resolve_runtime_v2_layout(layout)
    layout.archive_root.mkdir(parents=True, exist_ok=True)
    legacy_db_exists = layout.control_plane_db.exists()
    legacy_runs_exists = layout.runs_root.exists()
    payload = {
        "generated_at": _utc_now_iso(),
        "legacy_db": str(layout.control_plane_db),
        "legacy_db_exists": legacy_db_exists,
        "legacy_runs_root": str(layout.runs_root),
        "legacy_runs_exists": legacy_runs_exists,
        "v2_db": str(layout.control_plane_v2_db),
        "v2_runs_root": str(layout.runs_v2_root),
        "status": "legacy_archived",
    }
    manifest_path = layout.archive_root / "control-plane-v2-migration-manifest.json"
    manifest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def run_cutover_drill(*, layout: RuntimeLayout) -> dict[str, object]:
    layout = _resolve_runtime_v2_layout(layout)
    runtime_config = load_runtime_config(layout.repo_root)
    eval_summary = evaluate_regression_fixtures(layout=layout)
    completed_attempt_count = _completed_v2_attempt_count(layout.control_plane_v2_db)
    checks = [
        _check(
            name="runtime_v2_enabled",
            passed=runtime_config.runtime.experimental_v2_enabled,
            detail="runtime.experimental_v2_enabled must be true",
        ),
        _check(
            name="default_entrypoint_still_v1",
            passed=runtime_config.runtime.active_version == "v1",
            detail="cutover drill expects runtime.active_version to remain v1 before switch",
            value=runtime_config.runtime.active_version,
        ),
        _check(
            name="completed_v2_attempt",
            passed=completed_attempt_count > 0,
            detail="at least one runtime_v2 attempt must reach completed",
            count=completed_attempt_count,
        ),
        _check(
            name="regression_fixture_eval",
            passed=bool(eval_summary.get("ok")),
            detail="--eval-regression-fixtures-v2 summary must be ok",
            summary_path=str(eval_summary.get("summary_path") or ""),
            fixture_count=int(eval_summary.get("fixture_count") or 0),
        ),
    ]
    blocking_reasons = [
        str(check["name"])
        for check in checks
        if check["status"] != "pass"
    ]
    ready = not blocking_reasons
    summary_path = layout.runs_v2_root / "_cutover" / "cutover-drill-summary.json"
    payload = {
        "schema_version": "runtime_v2_cutover_drill.v1",
        "status": "ready" if ready else "blocked",
        "ready": ready,
        "cutover_performed": False,
        "active_version": runtime_config.runtime.active_version,
        "checks": checks,
        "blocking_reasons": blocking_reasons,
        "summary_path": str(summary_path),
        "regression_eval_summary_path": str(eval_summary.get("summary_path") or ""),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return payload


def run_cutover_review(
    *,
    layout: RuntimeLayout,
    drill_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    layout = _resolve_runtime_v2_layout(layout)
    if drill_payload is None:
        drill_payload = run_cutover_drill(layout=layout)
    drill_ready = bool(drill_payload.get("ready"))
    summary_path = layout.runs_v2_root / "_cutover" / "cutover-review-summary.json"
    rollback_plan = {
        "restore_active_version": "v1",
        "restore_config_path": ".ai/config/orchestrator.yaml",
        "restore_legacy_db": "copy archived .ai/archive/control-plane-v1-*.db back to .ai/state/control-plane.db",
        "restore_legacy_runs": "copy archived .ai/archive/runs-v1-* back to .ai/runs",
        "git_recovery": "git restore .ai/config/orchestrator.yaml and remove cutover archives created by the aborted switch",
    }
    payload = {
        "schema_version": "runtime_v2_cutover_review.v1",
        "status": "manual_approval_required" if drill_ready else "blocked",
        "manual_approval_required": drill_ready,
        "cutover_performed": False,
        "drill_ready": drill_ready,
        "blocking_reasons": list(drill_payload.get("blocking_reasons") or []),
        "drill_summary_path": str(drill_payload.get("summary_path") or ""),
        "summary_path": str(summary_path),
        "prospective_changes": [
            ".ai/config/orchestrator.yaml",
            ".ai/archive/control-plane-v1-*.db",
            ".ai/archive/runs-v1-*",
            "host-orchestrator --run-task default route",
        ],
        "rollback_plan": rollback_plan,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return payload


def run_cutover_rollback_drill(*, layout: RuntimeLayout) -> dict[str, object]:
    layout = _resolve_runtime_v2_layout(layout)
    runtime_config = load_runtime_config(layout.repo_root)
    review_payload = run_cutover_review(layout=layout)
    rollback_plan = review_payload.get("rollback_plan")
    if not isinstance(rollback_plan, dict):
        rollback_plan = {}
    archive_root_error = ""
    try:
        layout.archive_root.mkdir(parents=True, exist_ok=True)
        archive_root_available = True
    except OSError as exc:
        archive_root_available = False
        archive_root_error = str(exc)
    archive_restore_acceptance = _write_archive_restore_acceptance(
        layout=layout,
        rollback_plan=rollback_plan,
        archive_root_available=archive_root_available,
        archive_root_error=archive_root_error,
    )
    checks = [
        _check(
            name="review_manual_approval_required",
            passed=review_payload.get("status") == "manual_approval_required",
            detail="cutover rollback drill requires a ready review summary that still blocks on manual approval",
            review_status=str(review_payload.get("status") or ""),
        ),
        _check(
            name="restore_config_target",
            passed=rollback_plan.get("restore_active_version") == "v1"
            and rollback_plan.get("restore_config_path") == ".ai/config/orchestrator.yaml",
            detail="rollback plan must restore runtime.active_version=v1 through the repo-owned orchestrator config",
        ),
        _check(
            name="archive_root_available",
            passed=archive_root_available,
            detail="archive root must be available before a confirmed cutover can be considered recoverable",
            archive_root=str(layout.archive_root),
            error=archive_root_error,
        ),
        _check(
            name="archive_restore_acceptance",
            passed=archive_restore_acceptance.get("accepted") is True,
            detail="rollback drill requires a separate archive restore acceptance summary before confirmed cutover",
            summary_path=str(archive_restore_acceptance.get("summary_path") or ""),
            blocking_reasons=list(archive_restore_acceptance.get("blocking_reasons") or []),
        ),
        _check(
            name="default_entrypoint_currently_v1",
            passed=runtime_config.runtime.active_version == "v1",
            detail="rollback drill is only non-destructive while the default entrypoint remains v1",
            value=runtime_config.runtime.active_version,
        ),
    ]
    blocking_reasons = [
        str(check["name"])
        for check in checks
        if check["status"] != "pass"
    ]
    rollback_ready = not blocking_reasons
    summary_path = layout.runs_v2_root / "_cutover" / "cutover-rollback-drill-summary.json"
    payload = {
        "schema_version": "runtime_v2_cutover_rollback_drill.v1",
        "status": "ready" if rollback_ready else "blocked",
        "rollback_ready": rollback_ready,
        "restore_performed": False,
        "cutover_performed": False,
        "active_version": runtime_config.runtime.active_version,
        "checks": checks,
        "blocking_reasons": blocking_reasons,
        "review_summary_path": str(review_payload.get("summary_path") or ""),
        "archive_restore_acceptance_path": str(archive_restore_acceptance.get("summary_path") or ""),
        "summary_path": str(summary_path),
        "rollback_plan": rollback_plan,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return payload


def _write_archive_restore_acceptance(
    *,
    layout: RuntimeLayout,
    rollback_plan: dict[str, object],
    archive_root_available: bool,
    archive_root_error: str,
) -> dict[str, object]:
    legacy_db_source_exists = layout.control_plane_db.is_file()
    legacy_runs_source_exists = layout.runs_root.is_dir()
    checks = [
        _check(
            name="archive_root_available",
            passed=archive_root_available,
            detail="archive root must be available for v1 restore artifacts",
            archive_root=str(layout.archive_root),
            error=archive_root_error,
        ),
        _check(
            name="legacy_db_source_exists",
            passed=legacy_db_source_exists,
            detail="v1 control-plane DB source must exist before confirmed cutover",
            source_path=str(layout.control_plane_db),
        ),
        _check(
            name="legacy_runs_source_exists",
            passed=legacy_runs_source_exists,
            detail="v1 runs root source must exist before confirmed cutover",
            source_path=str(layout.runs_root),
        ),
        _check(
            name="restore_plan_targets",
            passed=rollback_plan.get("restore_active_version") == "v1"
            and rollback_plan.get("restore_config_path") == ".ai/config/orchestrator.yaml",
            detail="restore acceptance requires the rollback plan to target the repo-owned v1 config path",
        ),
    ]
    blocking_reasons = [
        str(check["name"])
        for check in checks
        if check["status"] != "pass"
    ]
    accepted = not blocking_reasons
    summary_path = layout.runs_v2_root / "_cutover" / "archive-restore-acceptance.json"
    payload = {
        "schema_version": "runtime_v2_archive_restore_acceptance.v1",
        "status": "accepted" if accepted else "blocked",
        "accepted": accepted,
        "restore_performed": False,
        "cutover_performed": False,
        "archive_root": str(layout.archive_root),
        "legacy_db_source": str(layout.control_plane_db),
        "legacy_db_source_exists": legacy_db_source_exists,
        "legacy_runs_source": str(layout.runs_root),
        "legacy_runs_source_exists": legacy_runs_source_exists,
        "restore_config_path": str(rollback_plan.get("restore_config_path") or ""),
        "checks": checks,
        "blocking_reasons": blocking_reasons,
        "summary_path": str(summary_path),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return payload


def validate_cutover_operator_approval(
    *,
    layout: RuntimeLayout,
    approval_ref: Path | None,
    review_payload: dict[str, object],
    rollback_payload: dict[str, object],
) -> dict[str, object]:
    layout = _resolve_runtime_v2_layout(layout)
    summary_path = layout.runs_v2_root / "_cutover" / "cutover-operator-approval-summary.json"
    approval_path = _resolve_optional_repo_path(layout.repo_root, approval_ref)
    approval_payload: dict[str, object] = {}
    approval_error = ""
    approval_byte_count = 0
    approval_sha256 = ""
    if approval_path is not None and approval_path.exists():
        try:
            approval_bytes = approval_path.read_bytes()
            approval_byte_count = len(approval_bytes)
            approval_sha256 = hashlib.sha256(approval_bytes).hexdigest()
            loaded_payload = json.loads(approval_bytes.decode("utf-8"))
            if isinstance(loaded_payload, dict):
                approval_payload = loaded_payload
            else:
                approval_error = "approval file must contain a JSON object"
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            approval_error = str(exc)
    elif approval_path is not None:
        approval_error = "approval file does not exist"

    acknowledged_risks = approval_payload.get("acknowledged_risks")
    if not isinstance(acknowledged_risks, list):
        acknowledged_risks = []
    required_risks = {"default_entrypoint_switch", "rollback_restore_required"}
    acknowledged_risk_set = {str(item) for item in acknowledged_risks}
    checks = [
        _check(
            name="approval_ref",
            passed=approval_path is not None,
            detail="confirmed cutover requires --cutover-approval-ref",
            approval_ref=str(approval_path) if approval_path is not None else "",
        ),
        _check(
            name="approval_file",
            passed=approval_path is not None and approval_path.exists() and not approval_error,
            detail="operator approval evidence must be a readable JSON object",
            error=approval_error,
        ),
        _check(
            name="approval_schema",
            passed=approval_payload.get("schema_version") == "runtime_v2_cutover_operator_approval.v1",
            detail="operator approval evidence must use schema runtime_v2_cutover_operator_approval.v1",
        ),
        _check(
            name="approval_flag",
            passed=approval_payload.get("approved") is True,
            detail="operator approval evidence must set approved=true",
        ),
        _check(
            name="approval_identity",
            passed=bool(str(approval_payload.get("approved_by") or "").strip())
            and bool(str(approval_payload.get("approved_at") or "").strip()),
            detail="operator approval evidence must include approved_by and approved_at",
        ),
        _check(
            name="review_summary_ref",
            passed=_same_repo_path_text(
                approval_payload.get("review_summary_path"),
                review_payload.get("summary_path"),
                repo_root=layout.repo_root,
            ),
            detail="operator approval evidence must reference the current cutover review summary",
        ),
        _check(
            name="rollback_drill_summary_ref",
            passed=_same_repo_path_text(
                approval_payload.get("rollback_drill_summary_path"),
                rollback_payload.get("summary_path"),
                repo_root=layout.repo_root,
            ),
            detail="operator approval evidence must reference the current rollback drill summary",
        ),
        _check(
            name="rollback_drill_ready",
            passed=rollback_payload.get("rollback_ready") is True,
            detail="confirmed cutover requires rollback drill to be ready",
        ),
        _check(
            name="acknowledged_risks",
            passed=required_risks <= acknowledged_risk_set,
            detail="operator approval evidence must acknowledge default switch and rollback restore risks",
            required=sorted(required_risks),
        ),
    ]
    blocking_reasons = [
        str(check["name"])
        for check in checks
        if check["status"] != "pass"
    ]
    approved = not blocking_reasons
    approval_audit_path = _write_operator_approval_audit(
        layout=layout,
        approval_path=approval_path,
        approval_payload=approval_payload,
        approval_sha256=approval_sha256,
        approval_byte_count=approval_byte_count,
    )
    payload = {
        "schema_version": "runtime_v2_cutover_operator_approval.v1",
        "status": "approved" if approved else "approval_required",
        "approved": approved,
        "cutover_performed": False,
        "approval_ref": str(approval_path) if approval_path is not None else "",
        "approval_sha256": approval_sha256,
        "approval_byte_count": approval_byte_count,
        "approval_audit_path": str(approval_audit_path) if approval_audit_path is not None else "",
        "approved_by": str(approval_payload.get("approved_by") or ""),
        "approved_at": str(approval_payload.get("approved_at") or ""),
        "checks": checks,
        "blocking_reasons": blocking_reasons,
        "review_summary_path": str(review_payload.get("summary_path") or ""),
        "rollback_drill_summary_path": str(rollback_payload.get("summary_path") or ""),
        "summary_path": str(summary_path),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return payload


def _write_operator_approval_audit(
    *,
    layout: RuntimeLayout,
    approval_path: Path | None,
    approval_payload: dict[str, object],
    approval_sha256: str,
    approval_byte_count: int,
) -> Path | None:
    if approval_path is None or not approval_payload:
        return None
    audit_path = layout.runs_v2_root / "_cutover" / "operator-approval-audit.json"
    acknowledged_risks = approval_payload.get("acknowledged_risks")
    if not isinstance(acknowledged_risks, list):
        acknowledged_risks = []
    audit_payload = {
        "schema_version": "runtime_v2_cutover_operator_approval_audit.v1",
        "captured_at": _utc_now_iso(),
        "source_path": str(approval_path),
        "source_sha256": approval_sha256,
        "source_byte_count": approval_byte_count,
        "approved": approval_payload.get("approved") is True,
        "approved_by": str(approval_payload.get("approved_by") or ""),
        "approved_at": str(approval_payload.get("approved_at") or ""),
        "review_summary_path": str(approval_payload.get("review_summary_path") or ""),
        "rollback_drill_summary_path": str(approval_payload.get("rollback_drill_summary_path") or ""),
        "acknowledged_risks": [str(item) for item in acknowledged_risks],
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit_payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return audit_path


def write_cutover_operator_approval_template(
    *,
    layout: RuntimeLayout,
    output_path: Path | None = None,
) -> dict[str, object]:
    layout = _resolve_runtime_v2_layout(layout)
    drill_payload = run_cutover_drill(layout=layout)
    if drill_payload["ready"]:
        review_payload = run_cutover_review(layout=layout, drill_payload=drill_payload)
        rollback_payload = run_cutover_rollback_drill(layout=layout)
    else:
        review_payload = {}
        rollback_payload = {}
    rollback_ready = rollback_payload.get("rollback_ready") is True
    template_ready = bool(drill_payload["ready"]) and rollback_ready
    summary_path = layout.runs_v2_root / "_cutover" / "cutover-approval-template-summary.json"
    template_path = (
        _resolve_optional_repo_path(layout.repo_root, output_path)
        if output_path is not None
        else layout.runs_v2_root / "_cutover" / "operator-approval.template.json"
    )
    blocking_reasons = []
    if not drill_payload["ready"]:
        blocking_reasons.extend(str(item) for item in drill_payload.get("blocking_reasons") or [])
    if drill_payload["ready"] and not rollback_ready:
        blocking_reasons.extend(str(item) for item in rollback_payload.get("blocking_reasons") or [])

    template_payload = {
        "schema_version": "runtime_v2_cutover_operator_approval.v1",
        "approved": False,
        "approved_by": "",
        "approved_at": "",
        "review_summary_path": str(review_payload.get("summary_path") or ""),
        "rollback_drill_summary_path": str(rollback_payload.get("summary_path") or ""),
        "acknowledged_risks": [
            "default_entrypoint_switch",
            "rollback_restore_required",
        ],
        "operator_instructions": [
            "Review the referenced cutover review and rollback drill summaries.",
            "Set approved=true only after manual acceptance.",
            "Fill approved_by and approved_at before passing this file to --cutover-approval-ref.",
        ],
    }
    if template_ready:
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.write_text(json.dumps(template_payload, indent=2, ensure_ascii=True), encoding="utf-8")

    payload = {
        "schema_version": "runtime_v2_cutover_operator_approval_template.v1",
        "status": "template_written" if template_ready else "blocked",
        "template_written": template_ready,
        "cutover_performed": False,
        "template_path": str(template_path) if template_ready else "",
        "drill_summary_path": str(drill_payload.get("summary_path") or ""),
        "review_summary_path": str(review_payload.get("summary_path") or ""),
        "rollback_drill_summary_path": str(rollback_payload.get("summary_path") or ""),
        "blocking_reasons": blocking_reasons,
        "summary_path": str(summary_path),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return payload


def perform_cutover(*, layout: RuntimeLayout) -> dict[str, object]:
    layout = _resolve_runtime_v2_layout(layout)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    layout.archive_root.mkdir(parents=True, exist_ok=True)
    archived_db = None
    archived_runs = None
    if layout.control_plane_db.exists():
        archived_db = layout.archive_root / f"control-plane-v1-{timestamp}.db"
        shutil.copy2(layout.control_plane_db, archived_db)
    if layout.runs_root.exists():
        archived_runs = layout.archive_root / f"runs-v1-{timestamp}"
        if archived_runs.exists():
            shutil.rmtree(archived_runs)
        shutil.copytree(layout.runs_root, archived_runs)

    orchestrator_path = layout.repo_root / ".ai" / "config" / "orchestrator.yaml"
    payload = yaml.safe_load(orchestrator_path.read_text(encoding="utf-8"))
    runtime_payload = dict(payload.get("runtime") or {})
    runtime_payload["active_version"] = "v2"
    payload["runtime"] = runtime_payload
    orchestrator_path.write_text(
        yaml.safe_dump(payload, allow_unicode=False, sort_keys=False),
        encoding="utf-8",
    )

    return {
        "archived_db": str(archived_db) if archived_db is not None else None,
        "archived_runs": str(archived_runs) if archived_runs is not None else None,
        "active_version": "v2",
        "cutover_at": _utc_now_iso(),
    }


def _resolve_runtime_v2_layout(layout: RuntimeLayout) -> RuntimeLayout:
    runtime_config = load_runtime_config(layout.repo_root)
    return layout.with_runtime_v2_paths(
        control_plane_db_v2=runtime_config.runtime.control_plane_db_v2,
        artifact_root_v2=runtime_config.runtime.artifact_root_v2,
    )


def _completed_v2_attempt_count(db_path: Path) -> int:
    if not db_path.exists():
        return 0
    with sqlite3.connect(db_path) as connection:
        try:
            row = connection.execute(
                "SELECT COUNT(*) FROM task_attempts WHERE state = 'completed'"
            ).fetchone()
        except sqlite3.OperationalError:
            return 0
    return int(row[0] if row is not None else 0)


def _check(*, name: str, passed: bool, detail: str, **extra: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": name,
        "status": "pass" if passed else "fail",
        "detail": detail,
    }
    payload.update(extra)
    return payload


def _resolve_optional_repo_path(repo_root: Path, value: Path | None) -> Path | None:
    if value is None:
        return None
    return value if value.is_absolute() else repo_root / value


def _same_repo_path_text(value: object, expected: object, *, repo_root: Path) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if not isinstance(expected, str) or not expected.strip():
        return False
    left = Path(value)
    right = Path(expected)
    if not left.is_absolute():
        left = repo_root / left
    if not right.is_absolute():
        right = repo_root / right
    return left.resolve(strict=False) == right.resolve(strict=False)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
