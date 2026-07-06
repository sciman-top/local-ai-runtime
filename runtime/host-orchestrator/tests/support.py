from __future__ import annotations

from pathlib import Path
import shutil


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]


def copy_runtime_config(repo_root: Path) -> None:
    source_root = REPO_ROOT / ".ai" / "config"
    destination_root = repo_root / ".ai" / "config"
    destination_root.mkdir(parents=True, exist_ok=True)
    for filename in ["orchestrator.yaml", "workers.yaml", "policies.yaml"]:
        shutil.copy2(source_root / filename, destination_root / filename)


def canonical_task_payload(task_id: str) -> dict[str, object]:
    return {
        "task_id": task_id,
        "title": "Validate host-local canonical runtime",
        "description": "Exercise the canonical task contract through the host-local runner.",
        "target_repo": "local-ai-dev-orchestrator",
        "base_branch": "main",
        "branch_name": "codex/host-local-test",
        "worktree_path": ".",
        "allowed_paths": ["runtime/host-orchestrator/**", "docs/**"],
        "forbidden_paths": [".env", ".env.*", ".git/config"],
        "write_access": True,
        "risk_level": "medium",
        "merge_policy": "manual_merge_only",
        "execution_lane": "host_local",
        "requires_network": False,
        "requires_gui": False,
        "depends_on": [],
        "artifacts_out": [
            f".ai/runs/<run_id>/{task_id}/result.json",
        ],
        "handoff_policy": "handoff_on_risk",
        "verification_commands": {
            "build": None,
            "test": "python -c \"print('TEST_OK')\"",
            "lint": None,
            "typecheck": None,
            "contract": "python -c \"print('CONTRACT_OK')\"",
            "hotspot": None,
        },
    }
