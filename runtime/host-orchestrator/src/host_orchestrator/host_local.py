from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from host_orchestrator import agentbridge, db
from host_orchestrator.paths import RuntimeLayout
from host_orchestrator.worker import WorkerLike, WorkerRequest


@dataclass(frozen=True)
class HostLocalConfig:
    agentbridge_root: Path
    workspace_root: Path
    layout: RuntimeLayout
    worker_id: str = "host-local-default"
    worker_profile: str = "local_maint"
    lane: str = "host_local"
    model: str = "gpt-5.4"
    provider: str = "openai-codex-sdk"
    network_mode: str = "off"


class HostLocalRunner:
    def __init__(self, config: HostLocalConfig, worker: WorkerLike) -> None:
        self._config = config
        self._worker = worker

    def run_task(self, task_path: Path) -> Path:
        task = agentbridge.load_task(task_path)
        now = agentbridge.utc_now_iso()

        db.initialize_control_plane(self._config.layout.control_plane_db)
        db.upsert_worker(
            self._config.layout.control_plane_db,
            worker_id=self._config.worker_id,
            lane=self._config.lane,
            status="busy",
            heartbeat_at=now,
        )
        db.record_route_decision(
            self._config.layout.control_plane_db,
            task_id=task.task_id,
            selected_lane=self._config.lane,
            reason="Wave 1 single worker default host_local lane",
            created_at=now,
        )
        db.upsert_runtime_task(
            self._config.layout.control_plane_db,
            task_id=task.task_id,
            state="running",
            execution_lane=self._config.lane,
            worker_profile=self._config.worker_profile,
            created_at=now,
            updated_at=now,
        )
        db.append_event(
            self._config.layout.control_plane_db,
            task_id=task.task_id,
            event_type="task_started",
            payload={"lane": self._config.lane, "worker_id": self._config.worker_id},
            created_at=now,
        )

        request = WorkerRequest(
            prompt=task.raw_text,
            cwd=self._config.workspace_root,
            model=self._config.model,
        )
        worker_result = self._worker.run(request)
        artifact = agentbridge.write_text_artifact(
            self._config.agentbridge_root,
            task.task_id,
            worker_result.final_response or "",
        )
        result_path = agentbridge.write_result(
            agentbridge_root=self._config.agentbridge_root,
            task_id=task.task_id,
            basename=task.path.stem,
            status="succeeded",
            model=self._config.model,
            provider=self._config.provider,
            worker_id=self._config.worker_id,
            lane=self._config.lane,
            sandbox_mode="workspace-write",
            network_mode=self._config.network_mode,
            final_response=worker_result.final_response,
            artifact=artifact,
            failures=[],
            observations=[
                "- Result file was written by the host-local orchestrator slice.",
                "- This path still uses fake-first verification; live SDK execution remains a separate acceptance step.",
            ],
            human_review_required=False,
            next_action="none",
        )

        finished_at = agentbridge.utc_now_iso()
        relative_result_path = str(result_path.relative_to(self._config.agentbridge_root)).replace("\\", "/")
        db.upsert_runtime_task(
            self._config.layout.control_plane_db,
            task_id=task.task_id,
            state="completed",
            execution_lane=self._config.lane,
            worker_profile=self._config.worker_profile,
            created_at=now,
            updated_at=finished_at,
            result_path=relative_result_path,
        )
        db.upsert_worker(
            self._config.layout.control_plane_db,
            worker_id=self._config.worker_id,
            lane=self._config.lane,
            status="idle",
            heartbeat_at=finished_at,
        )
        db.append_event(
            self._config.layout.control_plane_db,
            task_id=task.task_id,
            event_type="task_completed",
            payload={"result_path": relative_result_path, "artifact": artifact.relative_path},
            created_at=finished_at,
        )
        return result_path
