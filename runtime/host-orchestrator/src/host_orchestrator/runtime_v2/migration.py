from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

import yaml

from host_orchestrator.config_runtime import load_runtime_config
from host_orchestrator.paths import RuntimeLayout


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


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
