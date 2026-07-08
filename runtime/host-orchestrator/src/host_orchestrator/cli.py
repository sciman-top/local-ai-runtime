from __future__ import annotations

import argparse
import json
from pathlib import Path

from host_orchestrator import agentbridge
from host_orchestrator.config_runtime import RuntimeConfigError, load_runtime_config
from host_orchestrator.evidence_index import revalidate_evidence_index
from host_orchestrator.hermes_parity import run_hermes_parity
from host_orchestrator.multi_worker_simulation import run_multi_worker_simulation
from host_orchestrator.remote_non_gui_promotion import run_remote_non_gui_promotion
from host_orchestrator.paths import RuntimeLayout, discover_repo_root
from host_orchestrator.host_local import HostLocalConfig, HostLocalRunner
from host_orchestrator.runtime_v2.migration import (
    perform_cutover,
    run_cutover_drill,
    run_cutover_rollback_drill,
    run_cutover_review,
    write_migration_manifest,
)
from host_orchestrator.runtime_v2.evaluation import evaluate_regression_fixtures
from host_orchestrator.runtime_v2.runner import RuntimeV2Config, RuntimeV2Runner
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
        help="Run a task through the active repo-owned runtime entrypoint. Before cutover this remains host_local v1; after cutover it follows runtime.active_version.",
    )
    parser.add_argument(
        "--run-task-v2",
        type=Path,
        default=None,
        help="Run a v2 canonical JSON/YAML task through the experimental runtime_v2 entrypoint.",
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
    lifecycle_v2_group = parser.add_mutually_exclusive_group()
    lifecycle_v2_group.add_argument(
        "--resume-task-v2",
        default=None,
        help="Mark a v2 task attempt as ready from a specific resume point.",
    )
    lifecycle_v2_group.add_argument(
        "--retry-task-v2",
        default=None,
        help="Create a new v2 task attempt from a retry rewind point.",
    )
    lifecycle_v2_group.add_argument(
        "--run-ready-blocked-v2",
        action="store_true",
        help="Run v2 blocked tasks whose dependency_refs are now completed.",
    )
    lifecycle_v2_group.add_argument(
        "--eval-regression-fixtures-v2",
        action="store_true",
        help="Evaluate recorded runtime_v2 regression_fixture artifacts and print a JSON summary.",
    )
    lifecycle_v2_group.add_argument(
        "--migrate-control-plane-v2",
        action="store_true",
        help="Write the repo-side migration manifest for dual-track runtime_v2 storage without switching the default entrypoint.",
    )
    lifecycle_v2_group.add_argument(
        "--cutover-v2",
        action="store_true",
        help="Archive legacy v1 control-plane artifacts and switch runtime.active_version to v2.",
    )
    lifecycle_v2_group.add_argument(
        "--cutover-drill-v2",
        action="store_true",
        help="Run the runtime_v2 cutover drill without switching runtime.active_version.",
    )
    lifecycle_v2_group.add_argument(
        "--cutover-rollback-drill-v2",
        action="store_true",
        help="Run the runtime_v2 rollback restore drill without switching runtime.active_version.",
    )
    parser.add_argument(
        "--confirm-cutover-v2",
        action="store_true",
        help="Explicitly approve --cutover-v2 after review; without this flag cutover only writes the review summary.",
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
    runtime_bundle = _load_runtime_bundle_if_available(repo_root)
    runtime_v2_layout = (
        layout.with_runtime_v2_paths(
            control_plane_db_v2=runtime_bundle.runtime.control_plane_db_v2,
            artifact_root_v2=runtime_bundle.runtime.artifact_root_v2,
        )
        if runtime_bundle is not None
        else layout
    )

    if args.run_task is not None:
        task_path = args.run_task if args.run_task.is_absolute() else (repo_root / args.run_task)
        active_version = runtime_bundle.runtime.active_version if runtime_bundle is not None else "v1"
        if active_version == "v2":
            runner = RuntimeV2Runner(
                RuntimeV2Config(
                    workspace_root=repo_root,
                    layout=runtime_v2_layout,
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
                        "attempt_id": payload["attempt_id"],
                        "status": payload["status"],
                        "worker_profile": payload["worker_profile"],
                        "verification_profile": payload["verification_profile"],
                        "continuation_policy": payload["continuation_policy"],
                        "next_action": payload["next_action"],
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0
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

    if args.run_task_v2 is not None:
        task_path = args.run_task_v2 if args.run_task_v2.is_absolute() else (repo_root / args.run_task_v2)
        runner = RuntimeV2Runner(
            RuntimeV2Config(
                workspace_root=repo_root,
                layout=runtime_v2_layout,
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
                    "attempt_id": payload["attempt_id"],
                    "status": payload["status"],
                    "worker_profile": payload["worker_profile"],
                    "verification_profile": payload["verification_profile"],
                    "continuation_policy": payload["continuation_policy"],
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

    if args.migrate_control_plane_v2:
        payload = write_migration_manifest(layout=runtime_v2_layout)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if args.cutover_v2:
        drill_payload = run_cutover_drill(layout=runtime_v2_layout)
        if not drill_payload["ready"]:
            print(json.dumps(drill_payload, indent=2, ensure_ascii=False))
            return 1
        review_payload = run_cutover_review(layout=runtime_v2_layout, drill_payload=drill_payload)
        if not args.confirm_cutover_v2:
            print(json.dumps(review_payload, indent=2, ensure_ascii=False))
            return 1
        payload = perform_cutover(layout=runtime_v2_layout)
        payload["cutover_drill_summary_path"] = drill_payload["summary_path"]
        payload["cutover_review_summary_path"] = review_payload["summary_path"]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if args.cutover_drill_v2:
        payload = run_cutover_drill(layout=runtime_v2_layout)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0 if payload["ready"] else 1

    if args.cutover_rollback_drill_v2:
        payload = run_cutover_rollback_drill(layout=runtime_v2_layout)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0 if payload["rollback_ready"] else 1

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

    if args.resume_task_v2 is not None:
        if args.resume_point is None:
            parser.error("--resume-task-v2 requires --resume-point")
        runner = RuntimeV2Runner(
            RuntimeV2Config(
                workspace_root=repo_root,
                layout=runtime_v2_layout,
                worker_profile=args.worker_profile,
                run_id=args.run_id,
            ),
            worker_factory=RuntimeWorkerFactory(),
        )
        payload = runner.resume_attempt(
            attempt_id=args.resume_task_v2,
            resume_point=args.resume_point,
            reason=args.reason or "operator resumed the v2 attempt",
        )
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if args.retry_task_v2 is not None:
        if args.retry_rewind is None:
            parser.error("--retry-task-v2 requires --retry-rewind")
        runner = RuntimeV2Runner(
            RuntimeV2Config(
                workspace_root=repo_root,
                layout=runtime_v2_layout,
                worker_profile=args.worker_profile,
                run_id=args.run_id,
            ),
            worker_factory=RuntimeWorkerFactory(),
        )
        payload = runner.retry_attempt(
            attempt_id=args.retry_task_v2,
            retry_rewind=args.retry_rewind,
            reason=args.reason or "operator retried the v2 attempt",
        )
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if args.run_ready_blocked_v2:
        runner = RuntimeV2Runner(
            RuntimeV2Config(
                workspace_root=repo_root,
                layout=runtime_v2_layout,
                worker_profile=args.worker_profile,
                run_id=args.run_id,
            ),
            worker_factory=RuntimeWorkerFactory(),
        )
        result_paths = runner.run_ready_blocked_tasks()
        results = []
        for result_path in result_paths:
            payload = json.loads(result_path.read_text(encoding="utf-8"))
            results.append(
                {
                    "result_path": str(result_path),
                    "task_id": payload["task_id"],
                    "run_id": payload["run_id"],
                    "attempt_id": payload["attempt_id"],
                    "status": payload["status"],
                    "next_action": payload["next_action"],
                }
            )
        print(
            json.dumps(
                {
                    "continued_count": len(results),
                    "results": results,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    if args.eval_regression_fixtures_v2:
        payload = evaluate_regression_fixtures(layout=runtime_v2_layout)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0 if payload["ok"] else 1

    if args.print_layout:
        payload = {
            "repo_root": str(layout.repo_root),
            "ai_root": str(layout.ai_root),
            "runs_root": str(layout.runs_root),
            "runs_v2_root": str(runtime_v2_layout.runs_v2_root),
            "control_plane_root": str(layout.control_plane_root),
            "control_plane_db": str(layout.control_plane_db),
            "control_plane_v2_db": str(runtime_v2_layout.control_plane_v2_db),
            "control_plane_logs": str(layout.control_plane_logs),
            "archive_root": str(layout.archive_root),
            "wave_smokes": str(layout.wave_smokes),
        }
        if runtime_bundle is not None:
            payload["runtime_active_version"] = runtime_bundle.runtime.active_version
            payload["runtime_experimental_v2_enabled"] = runtime_bundle.runtime.experimental_v2_enabled
        print(
            json.dumps(payload, indent=2, ensure_ascii=True)
        )
        return 0

    parser.print_help()
    return 0


def _load_runtime_bundle_if_available(repo_root: Path):
    try:
        return load_runtime_config(repo_root)
    except RuntimeConfigError:
        return None
