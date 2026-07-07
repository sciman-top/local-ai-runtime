from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path


@dataclass(frozen=True)
class RuntimeLayout:
    repo_root: Path
    ai_root: Path
    runs_root: Path
    runs_v2_root: Path
    control_plane_root: Path
    control_plane_db: Path
    control_plane_v2_db: Path
    control_plane_logs: Path
    archive_root: Path
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
            runs_v2_root=ai_root / "runs-v2",
            control_plane_root=control_plane_root,
            control_plane_db=control_plane_root / "control-plane.db",
            control_plane_v2_db=control_plane_root / "control-plane-v2.db",
            control_plane_logs=control_plane_root / "logs",
            archive_root=ai_root / "archive",
            wave_smokes=private_local / "wave-smokes",
        )

    def with_runtime_v2_paths(
        self,
        *,
        control_plane_db_v2: str | Path,
        artifact_root_v2: str | Path,
    ) -> "RuntimeLayout":
        return replace(
            self,
            control_plane_v2_db=_resolve_repo_path(self.repo_root, control_plane_db_v2),
            runs_v2_root=_resolve_repo_path(self.repo_root, artifact_root_v2),
        )


def discover_repo_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__)).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists() or (candidate / "AGENTS.md").exists():
            return candidate
    raise RuntimeError("Unable to discover repository root from current path.")


def _resolve_repo_path(repo_root: Path, value: str | Path) -> Path:
    candidate = value if isinstance(value, Path) else Path(value)
    if candidate.is_absolute():
        return candidate
    return (repo_root / candidate).resolve(strict=False)
