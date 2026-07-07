from __future__ import annotations

import argparse
import json
from pathlib import Path

from host_orchestrator import agentbridge
from host_orchestrator.evidence_index import revalidate_evidence_index
from host_orchestrator.hermes_parity import run_hermes_parity
from host_orchestrator.multi_worker_simulation import run_multi_worker_simulation
from host_orchestrator.remote_non_gui_promotion import run_remote_non_gui_promotion
from host_orchestrator.paths import RuntimeLayout, discover_repo_root
from host_orchestrator.host_local import HostLocalConfig, HostLocalRunner
from host_orchestrator.task_lifecycle import (
    RESUME_POINTS,
    cancel_task,
    normalize_timestamp,
    reconcile_stale_tasks,
    resume_task,
    retry_task,
)
from host_orchestrator.worker_factory import RuntimeWorkerFactory
from host_orchestrator.vm_gui_promotion import run_vm_gui_promotion
from host_orchestrator.wave1_smoke import run_wave1_smokes


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
    parser.add_argument(
        "--run-task",
        type=Path,
        default=None,
        help="Run a canonical JSON/YAML task or AgentBridge markdown task through the repo-owned host_local entrypoint.",
    )
    parser.add_argument(
        "--agentbridge-root",
        type=Path,
        default=None,
        help="Optional AgentBridge compatibility projection root override for --run-task.",
    )
    parser.add_argument(
        "--worker-profile",
        default=None,
        help="Optional worker profile override for --run-task.",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Optional run id override for --run-task.",
    )
    parser.add_argument(
        "--run-wave1-smokes",
        action="store_true",
        help="Run the deterministic Wave 1 repo-side smoke suite and print its JSON summary.",
    )
    parser.add_argument(
        "--wave1-smoke-run-id",
        default=None,
        help="Optional run id override for the Wave 1 smoke suite.",
    )
    parser.add_argument(
        "--run-multi-worker-simulation",
        action="store_true",
        help="Run the deterministic multi-worker simulation suite and print its JSON summary.",
    )
    parser.add_argument(
        "--multi-worker-simulation-run-id",
        default=None,
        help="Optional run id override for the multi-worker simulation suite.",
    )
    parser.add_argument(
        "--run-remote-non-gui-promotion",
        action="store_true",
        help="Run the deterministic remote_non_gui promotion suite and print its JSON summary.",
    )
    parser.add_argument(
        "--remote-non-gui-promotion-run-id",
        default=None,
        help="Optional run id override for the remote_non_gui promotion suite.",
    )
    parser.add_argument(
        "--run-vm-gui-promotion",
        action="store_true",
        help="Run the deterministic vm_gui conditional promotion suite and print its JSON summary.",
    )
    parser.add_argument(
        "--vm-gui-promotion-run-id",
        default=None,
        help="Optional run id override for the vm_gui promotion suite.",
    )
    parser.add_argument(
        "--run-hermes-parity",
        action="store_true",
        help="Run the repo-owned Hermes parity and historical snapshot mapping suite and print its JSON summary.",
    )
    parser.add_argument(
        "--hermes-parity-run-id",
        default=None,
        help="Optional run id override for the Hermes parity suite.",
    )
    parser.add_argument(
        "--revalidate-evidence-index",
        type=Path,
        default=None,
        help="Recompute sha256/byte_count for an existing evidence_index.json and exit non-zero on mismatch.",
    )
    lifecycle_group = parser.add_mutually_exclusive_group()
    lifecycle_group.add_argument(
        "--reconcile-stale-tasks",
        action="store_true",
        help="Mark stale runtime tasks whose dispatch_state stale_after has expired.",
    )
    lifecycle_group.add_argument(
        "--cancel-task",
        default=None,
        help="Mark a runtime task as cancelled.",
    )
    lifecycle_group.add_argument(
        "--resume-task",
        default=None,
        help="Mark a runtime task as resumed from a specific resume point.",
    )
    lifecycle_group.add_argument(
        "--retry-task",
        default=None,
        help="Increment attempt and mark a runtime task as resumed from a retry rewind point.",
    )
    parser.add_argument(
        "--at",
        default=None,
        help="Optional ISO8601 timestamp override for lifecycle operations.",
    )
    parser.add_argument(
        "--reason",
        default="",
        help="Optional operator reason for lifecycle operations.",
    )
    parser.add_argument(
        "--resume-point",
        choices=sorted(RESUME_POINTS),
        default=None,
        help="Resume point for --resume-task.",
    )
    parser.add_argument(
        "--retry-rewind",
        choices=sorted(RESUME_POINTS),
        default=None,
        help="Retry rewind boundary for --retry-task.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve() if args.repo_root else discover_repo_root()
    layout = RuntimeLayout.from_repo_root(repo_root)

    if args.run_task is not None:
        task_path = args.run_task if args.run_task.is_absolute() else (repo_root / args.run_task)
        agentbridge_root = (
            args.agentbridge_root.resolve()
            if args.agentbridge_root is not None
            else repo_root / "AgentBridge"
        )
        runner = HostLocalRunner(
            HostLocalConfig(
                workspace_root=repo_root,
                layout=layout,
                agentbridge_root=agentbridge_root,
                worker_profile=args.worker_profile,
                run_id=args.run_id,
            ),
            worker_factory=RuntimeWorkerFactory(),
        )
        result_path = runner.run_task(task_path.resolve(strict=False))
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        print(
            json.dumps(
                {
                    "result_path": str(result_path),
                    "task_id": payload["task_id"],
                    "run_id": payload["run_id"],
                    "status": payload["status"],
                    "worker_profile": payload["worker_profile"],
                    "worker_kind": payload["worker_kind"],
                    "handoff_required": payload["handoff_required"],
                    "next_action": payload["next_action"],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    if args.run_wave1_smokes:
        summary = run_wave1_smokes(
            repo_root,
            run_id=args.wave1_smoke_run_id,
        )
        print(json.dumps(summary.to_dict(), indent=2, ensure_ascii=True))
        return 0

    if args.run_multi_worker_simulation:
        summary = run_multi_worker_simulation(
            repo_root,
            run_id=args.multi_worker_simulation_run_id,
        )
        print(json.dumps(summary.to_dict(), indent=2, ensure_ascii=True))
        return 0

    if args.run_remote_non_gui_promotion:
        summary = run_remote_non_gui_promotion(
            repo_root,
            run_id=args.remote_non_gui_promotion_run_id,
        )
        print(json.dumps(summary.to_dict(), indent=2, ensure_ascii=True))
        return 0

    if args.run_vm_gui_promotion:
        summary = run_vm_gui_promotion(
            repo_root,
            run_id=args.vm_gui_promotion_run_id,
        )
        print(json.dumps(summary.to_dict(), indent=2, ensure_ascii=True))
        return 0

    if args.run_hermes_parity:
        summary = run_hermes_parity(
            repo_root,
            run_id=args.hermes_parity_run_id,
        )
        print(json.dumps(summary.to_dict(), indent=2, ensure_ascii=True))
        return 0

    if args.revalidate_evidence_index is not None:
        evidence_index_path = args.revalidate_evidence_index
        if not evidence_index_path.is_absolute():
            evidence_index_path = repo_root / evidence_index_path
        result = revalidate_evidence_index(
            repo_root=repo_root,
            evidence_index_path=evidence_index_path.resolve(strict=False),
        )
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return 0 if result.ok else 1

    changed_at = normalize_timestamp(args.at or agentbridge.utc_now_iso())

    if args.reconcile_stale_tasks:
        stale_task_ids = reconcile_stale_tasks(layout, as_of=changed_at)
        print(
            json.dumps(
                {
                    "as_of": changed_at,
                    "stale_task_ids": stale_task_ids,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    if args.cancel_task is not None:
        payload = cancel_task(
            layout,
            task_id=args.cancel_task,
            cancelled_at=changed_at,
            reason=args.reason or "operator requested stop",
        )
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if args.resume_task is not None:
        if args.resume_point is None:
            parser.error("--resume-task requires --resume-point")
        payload = resume_task(
            layout,
            task_id=args.resume_task,
            resumed_at=changed_at,
            resume_point=args.resume_point,
            reason=args.reason or "operator resumed the task",
        )
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if args.retry_task is not None:
        if args.retry_rewind is None:
            parser.error("--retry-task requires --retry-rewind")
        payload = retry_task(
            layout,
            task_id=args.retry_task,
            retried_at=changed_at,
            retry_rewind=args.retry_rewind,
            reason=args.reason or "operator requested a retry",
        )
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if args.print_layout:
        print(
            json.dumps(
                {
                    "repo_root": str(layout.repo_root),
                    "ai_root": str(layout.ai_root),
                    "runs_root": str(layout.runs_root),
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
