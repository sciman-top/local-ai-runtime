from __future__ import annotations

import argparse
import json
from pathlib import Path

from host_orchestrator.paths import RuntimeLayout, discover_repo_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="host-orchestrator",
        description="Wave 1 host-local orchestrator scaffold.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Optional repository root override.",
    )
    parser.add_argument(
        "--print-layout",
        action="store_true",
        help="Print the default runtime layout as JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve() if args.repo_root else discover_repo_root()
    layout = RuntimeLayout.from_repo_root(repo_root)

    if args.print_layout:
        print(
            json.dumps(
                {
                    "repo_root": str(layout.repo_root),
                    "control_plane_root": str(layout.control_plane_root),
                    "control_plane_db": str(layout.control_plane_db),
                    "control_plane_logs": str(layout.control_plane_logs),
                    "wave_smokes": str(layout.wave_smokes),
                },
                indent=2,
                ensure_ascii=True,
            )
        )
        return 0

    parser.print_help()
    return 0
