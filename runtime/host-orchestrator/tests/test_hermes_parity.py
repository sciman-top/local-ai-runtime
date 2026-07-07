from __future__ import annotations

import json
from pathlib import Path

from host_orchestrator.cli import main as cli_main
from host_orchestrator.hermes_parity import HermesParitySummary, run_hermes_parity


KNOWN_GOOD_FILENAME = "known-good-20260628-225738-431.json"
BOUNDARY_FILENAME = "verify-hermes-boundary-20260628-225841-414.json"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_repo(repo_root: Path) -> None:
    _write_json(
        repo_root / "docs" / "architecture" / "planning-status.json",
        {
            "certified_baseline": {
                "evidence_ref": "docs/platforms/hermes/README.md",
                "claim_boundary": (
                    "Hermes/AgentBridge remains the certified historical baseline and strategic north-star "
                    "reference for Local AI Runtime, while current repo runtime truth stays on result.json "
                    "evidence and compatibility projection."
                ),
            }
        },
    )
    (repo_root / "docs" / "platforms" / "hermes" / "README.md").parent.mkdir(parents=True, exist_ok=True)
    (repo_root / "docs" / "platforms" / "hermes" / "README.md").write_text(
        "\n".join(
            [
                "# Hermes / AgentBridge 兼容线",
                "这里保存的是历史基线，不是当前通用编排器主线的 authoritative truth。",
                "- compatibility lane",
                "- historical operator evidence",
            ]
        ),
        encoding="utf-8",
    )
    (repo_root / "docs" / "platforms" / "hermes" / "当前交接摘要.md").write_text(
        "\n".join(
            [
                f"- 当前 known-good anchor: `{KNOWN_GOOD_FILENAME}`",
                f"- 当前 boundary anchor: `{BOUNDARY_FILENAME}`",
            ]
        ),
        encoding="utf-8",
    )
    (repo_root / "docs" / "platforms" / "hermes" / "接手检查单.md").write_text(
        "\n".join(
            [
                f"- 当前 known-good anchor 仍是 `{KNOWN_GOOD_FILENAME}`",
                f"- 当前 boundary anchor 仍是 `{BOUNDARY_FILENAME}`",
            ]
        ),
        encoding="utf-8",
    )

    snapshot_docs = repo_root / "snapshots" / "agentbridge-20260628" / "docs"
    snapshot_docs.mkdir(parents=True, exist_ok=True)
    (snapshot_docs / "implementation-status.md").write_text(
        "\n".join(
            [
                "## Current Status",
                f"- the latest verified known-good snapshot is: `docs/{KNOWN_GOOD_FILENAME}`",
                f"- the latest verified boundary evidence is: `docs/{BOUNDARY_FILENAME}`",
            ]
        ),
        encoding="utf-8",
    )
    _write_json(
        snapshot_docs / "hermes-runtime.json",
        {
            "bootstrap_model": "derived_non_root",
            "runtime_image": "agentbridge/hermes-nonroot:p0-2-20260628",
            "runtime_user": "10001:10001",
            "volume_uid": 10001,
            "volume_gid": 10001,
            "container_start_user": "0:0",
        },
    )
    _write_json(
        snapshot_docs / "hermes-image-resolution.json",
        {
            "repo_digest": "nousresearch/hermes-agent@sha256:9f367c7756ef087661a361536a89f438d57a122b958dc23d82d456b1433e6e9e",
            "resolution_status": "resolved",
        },
    )
    _write_json(
        snapshot_docs / KNOWN_GOOD_FILENAME,
        {
            "hermes_image_digest": "nousresearch/hermes-agent@sha256:9f367c7756ef087661a361536a89f438d57a122b958dc23d82d456b1433e6e9e",
            "hermes_image_resolution_status": "resolved",
            "hermes_bootstrap_model": "derived_non_root",
            "hermes_runtime_image": "agentbridge/hermes-nonroot:p0-2-20260628",
            "hermes_runtime_user": "10001:10001",
            "hermes_service_uid": 10001,
            "hermes_service_gid": 10001,
        },
    )
    _write_json(
        snapshot_docs / BOUNDARY_FILENAME,
        {
            "bootstrap_model": "derived_non_root",
            "runtime_user": "10001:10001",
            "requested_container_user_override": "0:0",
            "requested_read_only_rootfs": True,
            "observed_read_only_rootfs": True,
            "service_uid": 10001,
            "service_gid": 10001,
            "service_uidgid_present": True,
            "tmpfs_targets": ["/run", "/tmp"],
            "rootfs_write_blocked": True,
            "cap_drop_all_present": False,
        },
    )


def test_hermes_parity_suite_maps_snapshot_baseline_and_tolerates_env_sensitive_gate_failures(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _seed_repo(repo_root)

    def fake_gate_runner(name: str, snapshot_root: Path, known_good_path: Path | None) -> dict[str, object]:
        assert snapshot_root == repo_root / "snapshots" / "agentbridge-20260628"
        if name == "contract":
            return {"ok": True, "issues": []}
        if name == "known_good":
            assert known_good_path == snapshot_root / "docs" / KNOWN_GOOD_FILENAME
            return {"ok": True, "issues": []}
        if name == "bringup":
            return {
                "ready": False,
                "gates": [
                    {"gate": "fixed_release_tag", "passed": True},
                    {"gate": "fixed_image_digest", "passed": True},
                    {"gate": "independent_key", "passed": False},
                    {"gate": "independent_base_url", "passed": False},
                    {"gate": "service_runtime_uidgid", "passed": True},
                    {"gate": "volume_init_complete", "passed": True},
                    {"gate": "agentbridge_contract_clean", "passed": True},
                ],
            }
        raise AssertionError(f"Unexpected gate name: {name}")

    summary = run_hermes_parity(
        repo_root,
        run_id="hermes-parity-test",
        gate_runner=fake_gate_runner,
    )

    assert summary.ok is True
    assert summary.anchor_alignment_ok is True
    assert summary.current_truth_boundary_ok is True
    assert summary.historical_snapshot_mapping_ok is True
    assert summary.container_lifecycle_ok is True
    assert summary.contract_ok is True
    assert summary.known_good_snapshot_ok is True
    assert summary.bringup_gate_ready is False
    assert summary.env_sensitive_failed_gates == ["independent_key", "independent_base_url"]
    assert summary.non_env_failed_gates == []
    assert summary.known_good_snapshot_path.endswith(KNOWN_GOOD_FILENAME)
    assert summary.boundary_snapshot_path.endswith(BOUNDARY_FILENAME)
    assert summary.summary_path.exists()

    payload = json.loads(summary.summary_path.read_text(encoding="utf-8"))
    assert payload["claim_boundary"].startswith("repo-side Hermes parity")
    assert payload["next_gap"] == "P6-T03 vm_gui conditional promotion evidence"
    assert payload["env_sensitive_failed_gates"] == ["independent_key", "independent_base_url"]


def test_cli_runs_hermes_parity_and_prints_json(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    def fake_run_hermes_parity(repo_root: Path, *, run_id: str | None = None) -> HermesParitySummary:
        return HermesParitySummary(
            run_id=run_id or "cli-default",
            run_root=tmp_path / "run-root",
            summary_path=tmp_path / "run-root" / "hermes-parity-summary.json",
            snapshot_root=tmp_path / "snapshot-root",
            baseline_doc_path="docs/platforms/hermes/README.md",
            implementation_status_path="snapshots/agentbridge-20260628/docs/implementation-status.md",
            known_good_snapshot_path=f"snapshots/agentbridge-20260628/docs/{KNOWN_GOOD_FILENAME}",
            boundary_snapshot_path=f"snapshots/agentbridge-20260628/docs/{BOUNDARY_FILENAME}",
            known_good_anchor_mentions={"implementation_status": KNOWN_GOOD_FILENAME},
            boundary_anchor_mentions={"implementation_status": BOUNDARY_FILENAME},
            contract_ok=True,
            known_good_snapshot_ok=True,
            bringup_gate_ready=False,
            bringup_failed_gates=["independent_key", "independent_base_url"],
            env_sensitive_failed_gates=["independent_key", "independent_base_url"],
            non_env_failed_gates=[],
            anchor_alignment_ok=True,
            current_truth_boundary_ok=True,
            historical_snapshot_mapping_ok=True,
            container_lifecycle_ok=True,
            claim_boundary="repo-side Hermes parity + historical snapshot mapping proof only",
            next_gap="P6-T03 vm_gui conditional promotion evidence",
            ok=True,
            issues=[],
        )

    monkeypatch.setattr("host_orchestrator.cli.run_hermes_parity", fake_run_hermes_parity)

    exit_code = cli_main(
        [
            "--repo-root",
            str(tmp_path),
            "--run-hermes-parity",
            "--hermes-parity-run-id",
            "hermes-parity-cli-test",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["run_id"] == "hermes-parity-cli-test"
    assert payload["next_gap"] == "P6-T03 vm_gui conditional promotion evidence"
