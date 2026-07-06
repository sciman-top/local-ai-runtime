from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from host_orchestrator import agentbridge, db
from host_orchestrator.canonical_result import build_run_id, write_result_bundle
from host_orchestrator.canonical_task import CanonicalTask, load_task
from host_orchestrator.config_runtime import RuntimeConfigBundle, WorkerProfile, load_runtime_config
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.worker import WorkerLike, WorkerRequest, WorkerUsage


@dataclass(frozen=True)
class HostLocalConfig:
    workspace_root: Path
    layout: RuntimeLayout
    agentbridge_root: Path | None = None
    worker_id: str = "host-local-default"
    worker_profile: str | None = None
    run_id: str | None = None
    attempt: int = 1
    route_reason: str = "Phase 1 single worker default host_local lane"


class HostLocalRunner:
    def __init__(self, config: HostLocalConfig, worker: WorkerLike) -> None:
        self._config = config
        self._worker = worker
        self._runtime_config = load_runtime_config(config.layout.repo_root)

    def run_task(self, task_path: Path) -> Path:
        task = load_task(task_path)
        worker_profile = self._runtime_config.worker_profile(self._config.worker_profile)
        run_id = self._config.run_id or build_run_id(
            prefix=self._runtime_config.orchestrator.run_id_prefix
        )
        started_at = agentbridge.utc_now_iso()

        db.initialize_control_plane(self._config.layout.control_plane_db)
        db.upsert_worker(
            self._config.layout.control_plane_db,
            worker_id=self._config.worker_id,
            lane=worker_profile.lane,
            status="busy",
            heartbeat_at=started_at,
        )
        db.record_route_decision(
            self._config.layout.control_plane_db,
            task_id=task.task_id,
            selected_lane=worker_profile.lane,
            reason=self._config.route_reason,
            created_at=started_at,
        )
        db.upsert_runtime_task(
            self._config.layout.control_plane_db,
            task_id=task.task_id,
            state="running",
            execution_lane=worker_profile.lane,
            worker_profile=worker_profile.name,
            created_at=started_at,
            updated_at=started_at,
        )
        db.append_event(
            self._config.layout.control_plane_db,
            task_id=task.task_id,
            event_type="task_started",
            payload={
                "lane": worker_profile.lane,
                "worker_id": self._config.worker_id,
                "worker_profile": worker_profile.name,
                "run_id": run_id,
                "attempt": self._config.attempt,
            },
            created_at=started_at,
        )

        request = WorkerRequest(
            prompt=task.render_worker_prompt(),
            cwd=self._config.workspace_root,
            model=worker_profile.model,
            sandbox=worker_profile.sandbox(),
            approval_mode=worker_profile.approval_mode(),
        )
        worker_result = self._worker.run(request)
        finished_at = agentbridge.utc_now_iso()

        result_bundle = write_result_bundle(
            layout=self._config.layout,
            task=task,
            run_id=run_id,
            attempt=self._config.attempt,
            worker_profile=worker_profile,
            worker_result=worker_result,
            started_at=started_at,
            finished_at=finished_at,
            projection_writer=(
                lambda artifacts: self._write_compatibility_projection(
                    task=task,
                    worker_profile=worker_profile,
                    worker_result=worker_result,
                    artifacts=artifacts,
                )
            ),
        )

        relative_result_path = str(
            result_bundle.artifacts.result_json.relative_to(self._config.layout.repo_root)
        ).replace("\\", "/")
        projection_path = result_bundle.result_payload.get("compatibility_projection_ref")
        evidence_index_path = str(
            result_bundle.artifacts.evidence_index.relative_to(self._config.layout.repo_root)
        ).replace("\\", "/")
        db.upsert_runtime_task(
            self._config.layout.control_plane_db,
            task_id=task.task_id,
            state="completed",
            execution_lane=worker_profile.lane,
            worker_profile=worker_profile.name,
            created_at=started_at,
            updated_at=finished_at,
            result_path=relative_result_path,
        )
        db.upsert_worker(
            self._config.layout.control_plane_db,
            worker_id=self._config.worker_id,
            lane=worker_profile.lane,
            status="idle",
            heartbeat_at=finished_at,
        )
        db.append_event(
            self._config.layout.control_plane_db,
            task_id=task.task_id,
            event_type="task_completed",
            payload={
                "result_path": relative_result_path,
                "compatibility_projection_ref": projection_path,
                "evidence_index_ref": evidence_index_path,
                "usage": self._usage_payload(worker_result.usage),
            },
            created_at=finished_at,
        )
        return result_bundle.artifacts.result_json

    def _write_compatibility_projection(
        self,
        *,
        task: CanonicalTask,
        worker_profile: WorkerProfile,
        worker_result: object,
        artifacts: object,
    ) -> Path | None:
        if self._config.agentbridge_root is None:
            return None
        if not self._runtime_config.orchestrator.projection_required:
            return None
        if worker_profile.projection_mode != "compatibility_dual_write":
            return None

        if not isinstance(worker_result, object) or not hasattr(artifacts, "worker_output"):
            return None

        compatibility_root = self._config.agentbridge_root
        compatibility_root.mkdir(parents=True, exist_ok=True)
        (compatibility_root / "results").mkdir(parents=True, exist_ok=True)
        (compatibility_root / "artifacts").mkdir(parents=True, exist_ok=True)

        artifact = agentbridge.write_text_artifact(
            compatibility_root,
            task.task_id,
            getattr(worker_result, "final_response", None) or "",
        )
        observations = [
            "- Markdown result remains a compatibility projection from canonical runtime output.",
            "- The formal runtime truth lives under `.ai/runs/<run_id>/<task_id>/result.json`.",
            *self._build_usage_observations(getattr(worker_result, "usage", None)),
        ]
        return agentbridge.write_result_projection(
            agentbridge_root=compatibility_root,
            task_id=task.task_id,
            status="succeeded",
            model=worker_profile.model,
            provider=worker_profile.provider,
            worker_id=self._config.worker_id,
            lane=worker_profile.lane,
            sandbox_mode=worker_profile.sandbox_profile,
            network_mode=worker_profile.network_profile,
            final_response=getattr(worker_result, "final_response", None),
            artifact=artifact,
            failures=[],
            observations=observations,
            human_review_required=False,
            next_action="none",
        )

    @staticmethod
    def _build_usage_observations(usage: WorkerUsage | None) -> list[str]:
        if usage is None:
            return ["- Structured token usage was not available from the worker runtime."]

        return [
            "- Structured token usage captured from the worker runtime.",
            (
                f"- usage source={usage.source}; total={usage.total.total_tokens}; "
                f"input={usage.total.input_tokens}; output={usage.total.output_tokens}; "
                f"cached_input={usage.total.cached_input_tokens}; "
                f"reasoning_output={usage.total.reasoning_output_tokens}."
            ),
            (
                f"- usage last_turn total={usage.last.total_tokens}; input={usage.last.input_tokens}; "
                f"output={usage.last.output_tokens}."
            ),
        ]

    @staticmethod
    def _usage_payload(usage: WorkerUsage | None) -> dict[str, Any] | None:
        if usage is None:
            return None

        return {
            "source": usage.source,
            "last": {
                "cached_input_tokens": usage.last.cached_input_tokens,
                "input_tokens": usage.last.input_tokens,
                "output_tokens": usage.last.output_tokens,
                "reasoning_output_tokens": usage.last.reasoning_output_tokens,
                "total_tokens": usage.last.total_tokens,
            },
            "total": {
                "cached_input_tokens": usage.total.cached_input_tokens,
                "input_tokens": usage.total.input_tokens,
                "output_tokens": usage.total.output_tokens,
                "reasoning_output_tokens": usage.total.reasoning_output_tokens,
                "total_tokens": usage.total.total_tokens,
            },
            "model_context_window": usage.model_context_window,
        }
