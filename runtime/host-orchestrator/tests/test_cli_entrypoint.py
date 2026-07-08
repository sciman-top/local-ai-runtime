from __future__ import annotations

import tomllib
from pathlib import Path


def test_pyproject_declares_host_orchestrator_console_script() -> None:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    assert payload["project"]["scripts"]["host-orchestrator"] == (
        "host_orchestrator.cli:main"
    )
