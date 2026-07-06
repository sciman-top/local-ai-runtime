from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeLayout:
    repo_root: Path
    ai_root: Path
    runs_root: Path
    control_plane_root: Path
    control_plane_db: Path
    control_plane_logs: Path
    wave_smokes: Path

    @classmethod
    def from_repo_root(cls, repo_root: Path) -> "RuntimeLayout":
        ai_root = repo_root / ".ai"
        private_local = repo_root / "private-local"
        control_plane_root = ai_root / "state"
        return cls(
            repo_root=repo_root,
            ai_root=ai_root,
            runs_root=ai_root / "runs",
            control_plane_root=control_plane_root,
            control_plane_db=control_plane_root / "control-plane.db",
            control_plane_logs=control_plane_root / "logs",
            wave_smokes=private_local / "wave-smokes",
        )


def discover_repo_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__)).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists() or (candidate / "AGENTS.md").exists():
            return candidate
    raise RuntimeError("Unable to discover repository root from current path.")
