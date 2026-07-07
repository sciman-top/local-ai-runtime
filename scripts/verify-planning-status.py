from __future__ import annotations

import argparse
from datetime import date
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATUS_PATH = ROOT / "docs" / "architecture" / "planning-status.json"
SELECTOR_POLICY_PATH = ROOT / "docs" / "architecture" / "next-work-selection-policy.json"
SUPPLEMENTAL_SYNC_FILES = [
    ROOT / "ai_dev_orchestrator_impl_pack" / "00_README_FIRST.md",
    ROOT / "ai_dev_orchestrator_impl_pack" / "04_REPOSITORY_LAYOUT.md",
    ROOT / "ai_dev_orchestrator_impl_pack" / "13_BOOTSTRAP_CHECKLIST.md",
    ROOT / "ai_dev_orchestrator_impl_pack" / "14_HANDOFF_MESSAGE_TO_CODEX.md",
    ROOT / "AGENTS.md",
]
SUPPLEMENTAL_FORBIDDEN_TOKENS = [
    "创建项目目录骨架",
    "生成最小可运行的 Python Orchestrator",
    "project-root/",
    "  orchestrator/",
    "`orchestrator/`：Python 主体代码",
    "创建目录结构",
    "仅创建目录",
    "当前产品主线仍是 **通用本地 AI Dev Orchestrator**",
]
SUPPLEMENTAL_REQUIRED_TOKENS = [
    "Hermes -> AgentBridge -> Codex",
    "Local AI Runtime",
    "本地 AI 运行时",
    "runtime/host-orchestrator",
    ".ai/state/control-plane.db",
    ".ai/runs/<run_id>/<task_id>/",
    "host_local > remote_non_gui > vm_gui",
]
REQUIRED_DOC_SNIPPETS = {
    "README.md": [
        "Local AI Runtime",
        "本地 AI 运行时",
        "local-ai-dev-orchestrator",
        "Hermes -> AgentBridge -> Codex",
        "Governance Overlay",
        "promote_phase1_execution",
        "config-and-worker-profiles.md",
        "runtime_v2/",
        ".ai/state/control-plane-v2.db",
    ],
    "docs/README.md": [
        "Local AI Runtime",
        "本地 AI 运行时",
        "local-ai-dev-orchestrator",
        "Hermes -> AgentBridge -> Codex",
        "canonical `JSON/YAML` intake",
        "compatibility projection",
        "next-work-selection-policy.json",
        "runtime-v2-kernel.md",
        ".ai/runs-v2/<run_id>/<task_id>/<attempt_id>/",
    ],
    "docs/product/orchestrator-prd.md": [
        "Local AI Runtime",
        "本地 AI 运行时",
        "Hermes -> AgentBridge -> Codex",
        "selector + change-evidence + preflight + reference governance",
        "mock green",
        "live probe ready",
        "host_local > remote_non_gui > vm_gui",
        "runtime_v2",
        "control-plane-v2.db",
    ],
    "docs/architecture/orchestrator-target-architecture.md": [
        "Local AI Runtime",
        "本地 AI 运行时",
        "AgentBridge 是跨层主契约",
        "Governance Overlay",
        "docs/change-evidence/README.md",
        "runtime/host-orchestrator` 是 `host_local` 可信运行时内核",
        "runtime_v2/",
        "默认入口保持 v1",
    ],
    "docs/specs/task-contract.md": [
        "当前主协议是 `JSON/YAML`",
        "目标态与迁移窗口",
        "execution_lane",
    ],
    "docs/specs/result-contract.md": [
        "compatibility_projection_ref",
        "`lane`",
        "迁移窗口",
        "scripted",
    ],
    "docs/specs/state-and-db.md": [
        "resource_leases",
        "worker_sessions",
        "不承载 task-level evidence 正文",
        "control-plane-v2.db",
        "task_attempts",
        ".ai/runs-v2/<run_id>/<task_id>/<attempt_id>/",
    ],
    "docs/specs/runtime-v2-kernel.md": [
        "Runtime V2 Kernel Spec",
        "runtime.active_version",
        "dependency_refs",
        "verification_profile",
        "continuation_policy",
        "--run-task-v2",
    ],
    "docs/specs/config-and-worker-profiles.md": [
        ".ai/config/orchestrator.yaml",
        "worker_profile",
        "runtime.active_version",
        "experimental_v2_enabled",
        "verification_profiles",
    ],
    "docs/specs/acceptance-and-gates.md": [
        "mock green",
        "live probe ready",
        "build -> [lint -> typecheck] -> test -> contract -> hotspot",
        "gate_report.json",
    ],
    "docs/specs/run-state-and-handoff.md": [
        "Phase 1-4",
        "run_id",
        "handoff_required",
        "attempt_id",
        "retry_rewind",
        ".ai/runs-v2/<run_id>/<task_id>/<attempt_id>/",
    ],
    "docs/roadmap/orchestrator-roadmap.md": [
        "Local AI Runtime",
        "Phase A — Truth Reset",
        "Governance Overlay",
        "promote_phase1_execution",
        "Kernel V2",
        "WP1",
    ],
    "docs/plans/orchestrator-implementation-plan.md": [
        "Local AI Runtime",
        "Phase A — Truth Reset",
        "runtime/host-orchestrator` 是 `host_local` 可信运行时内核",
        "promote_phase1_execution",
        "Kernel V2",
        "--run-task-v2",
    ],
    "docs/backlog/orchestrator-task-list.md": [
        "Local AI Runtime",
        "PHASE-1-VERTICAL-SLICE",
        "host_local > remote_non_gui > vm_gui",
        "B-T01",
        "K2-T01",
        "K2-T06",
    ],
    "docs/migrations/hermes-compatibility-demotion.md": [
        "superseded",
        "20260706-strategic-regression.md",
    ],
}
DEMOTED_FILE_MARKERS = {
    "ai_dev_orchestrator_impl_pack/03_IMPLEMENTATION_ROADMAP.md": [
        "Status: superseded by roadmap/plan/task-list/planning-status",
    ],
    "ai_dev_orchestrator_impl_pack/05_TASK_CONTRACT_SCHEMA.json": [
        "\"_status_marker\": \"stale / incompatible with current canonical contract\"",
        "\"_authoritative_replacement\": \"docs/specs/task-contract.md\"",
    ],
    "ai_dev_orchestrator_impl_pack/05_SAMPLE_TASKS.json": [
        "\"status_marker\": \"stale greenfield sample\"",
        "\"authoritative_replacement\": \"docs/specs/task-contract.md\"",
    ],
    "ai_dev_orchestrator_impl_pack/06_STATE_MACHINE.md": [
        "Status: concept-only legacy note.",
    ],
    "ai_dev_orchestrator_impl_pack/07_AGENT_ROLE_MATRIX.md": [
        "Status: role-superseded.",
        "docs/specs/config-and-worker-profiles.md",
    ],
    "ai_dev_orchestrator_impl_pack/08_AGENTS.md": [
        "Status: non-authoritative operational prompt asset.",
    ],
    "ai_dev_orchestrator_impl_pack/09_CODEX_MASTER_PROMPT.md": [
        "Status: non-authoritative operational prompt asset.",
    ],
    "ai_dev_orchestrator_impl_pack/10_GLM_REVIEW_PROMPT.md": [
        "Status: non-authoritative operational prompt asset.",
        "Phase 4 review adapter",
    ],
    "ai_dev_orchestrator_impl_pack/14_HANDOFF_MESSAGE_TO_CODEX.md": [
        "Status: non-authoritative operational prompt asset.",
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify planning status source-of-truth alignment.")
    parser.add_argument("--repo-root", default=str(ROOT))
    parser.add_argument("--status-path", default=str(DEFAULT_STATUS_PATH))
    args = parser.parse_args()

    try:
        result = verify(repo_root=Path(args.repo_root), status_path=Path(args.status_path))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def verify(*, repo_root: Path, status_path: Path) -> dict[str, object]:
    root = repo_root.resolve(strict=False)
    payload = _load_json(status_path)
    required_fields = [
        "status_id",
        "updated_on",
        "current_active_queue",
        "current_decision_gate",
        "current_live_posture",
        "certified_baseline",
        "authoritative_docs",
        "required_consistency_tokens",
        "unexpected_tokens",
        "rollback_ref",
    ]
    missing_fields = [field for field in required_fields if field not in payload]

    authoritative_docs = [root / Path(item) for item in payload.get("authoritative_docs", [])]
    missing_files = [str(path.relative_to(root)) for path in authoritative_docs if not path.exists()]

    combined_text = []
    for path in authoritative_docs:
        if path.exists():
            combined_text.append(path.read_text(encoding="utf-8"))
    aggregate = "\n".join(combined_text)

    missing_tokens = [
        token for token in payload.get("required_consistency_tokens", []) if token not in aggregate
    ]

    unexpected_tokens: list[str] = []
    for path in authoritative_docs:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for token in payload.get("unexpected_tokens", []):
            if token in text:
                unexpected_tokens.append(f"{path.relative_to(root)}:{token}")

    selector_source = str(payload.get("current_decision_gate", {}).get("selector_source") or "").strip()
    proof_ref = str(payload.get("current_decision_gate", {}).get("proof_ref") or "").strip()
    baseline_ref = str(payload.get("certified_baseline", {}).get("evidence_ref") or "").strip()

    referenced_files = {
        "selector_source": selector_source,
        "proof_ref": proof_ref,
        "certified_baseline.evidence_ref": baseline_ref,
    }
    missing_refs = [
        f"{key}:{value}"
        for key, value in referenced_files.items()
        if value and not (root / Path(value)).exists()
    ]

    live_posture = payload.get("current_live_posture", {})
    live_posture_fields = [
        "status",
        "gpt54_gateway_probe_status",
        "codex_exec_probe_status",
        "as_of",
        "summary",
    ]
    missing_live_posture_fields = [
        field for field in live_posture_fields if not str(live_posture.get(field) or "").strip()
    ]

    missing_doc_snippets: list[str] = []
    for relative_path, snippets in REQUIRED_DOC_SNIPPETS.items():
        path = root / relative_path
        if not path.exists():
            missing_doc_snippets.append(f"{relative_path}:missing file")
            continue
        text = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                missing_doc_snippets.append(f"{relative_path}:{snippet}")

    supplemental_violations: list[str] = []
    supplemental_texts: list[str] = []
    for path in SUPPLEMENTAL_SYNC_FILES:
        if not path.exists():
            supplemental_violations.append(f"missing supplemental sync file: {path.relative_to(root)}")
            continue
        text = path.read_text(encoding="utf-8")
        supplemental_texts.append(text)
        for token in SUPPLEMENTAL_FORBIDDEN_TOKENS:
            if token in text:
                supplemental_violations.append(f"{path.relative_to(root)}:{token}")
    supplemental_aggregate = "\n".join(supplemental_texts)
    missing_supplemental_tokens = [
        token for token in SUPPLEMENTAL_REQUIRED_TOKENS if token not in supplemental_aggregate
    ]

    demotion_marker_failures: list[str] = []
    for relative_path, markers in DEMOTED_FILE_MARKERS.items():
        path = root / relative_path
        if not path.exists():
            demotion_marker_failures.append(f"{relative_path}:missing file")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                demotion_marker_failures.append(f"{relative_path}:{marker}")

    readme_first_path = root / "ai_dev_orchestrator_impl_pack" / "00_README_FIRST.md"
    if readme_first_path.exists():
        readme_first_text = readme_first_path.read_text(encoding="utf-8")
        if "5. `05_TASK_CONTRACT_SCHEMA.json`" in readme_first_text:
            demotion_marker_failures.append(
                "ai_dev_orchestrator_impl_pack/00_README_FIRST.md:stale 05 still appears in primary reading order"
            )
        for required_pointer in [
            "docs/README.md",
            "docs/specs/config-and-worker-profiles.md",
            "docs/specs/acceptance-and-gates.md",
            "docs/specs/run-state-and-handoff.md",
        ]:
            if required_pointer not in readme_first_text:
                demotion_marker_failures.append(
                    f"ai_dev_orchestrator_impl_pack/00_README_FIRST.md:{required_pointer}"
                )

    policy_failures = _verify_selector_policy(root)

    failures: list[str] = []
    if missing_fields:
        failures.append("missing fields: " + ", ".join(missing_fields))
    if missing_files:
        failures.append("missing files: " + ", ".join(missing_files))
    if missing_refs:
        failures.append("missing referenced files: " + ", ".join(missing_refs))
    if missing_live_posture_fields:
        failures.append("missing current_live_posture fields: " + ", ".join(missing_live_posture_fields))
    if missing_tokens:
        failures.append("missing required tokens: " + ", ".join(missing_tokens))
    if unexpected_tokens:
        failures.append("unexpected authoritative tokens: " + ", ".join(unexpected_tokens))
    if missing_doc_snippets:
        failures.append("missing required doc snippets: " + ", ".join(missing_doc_snippets))
    if supplemental_violations:
        failures.append("supplemental sync violations: " + ", ".join(supplemental_violations))
    if missing_supplemental_tokens:
        failures.append(
            "missing supplemental required tokens: " + ", ".join(missing_supplemental_tokens)
        )
    if demotion_marker_failures:
        failures.append("demotion marker failures: " + ", ".join(demotion_marker_failures))
    if policy_failures:
        failures.append("selector policy failures: " + ", ".join(policy_failures))

    if failures:
        raise ValueError("planning status verification failed: " + "; ".join(failures))

    return {
        "status": "pass",
        "status_path": _render_relative(root=root, path=status_path),
        "authoritative_doc_count": len(authoritative_docs),
        "selector_source": selector_source,
        "proof_ref": proof_ref,
        "supplemental_sync_files": [
            str(path.relative_to(root)).replace("\\", "/") for path in SUPPLEMENTAL_SYNC_FILES
        ],
        "demoted_files_checked": sorted(DEMOTED_FILE_MARKERS.keys()),
    }


def _verify_selector_policy(root: Path) -> list[str]:
    failures: list[str] = []
    payload = _load_json(SELECTOR_POLICY_PATH)
    required_fields = [
        "policy_id",
        "reviewed_on",
        "review_expires_at",
        "allowed_next_actions",
        "selection_order",
        "required_entrypoints",
        "required_doc_refs",
        "rollback_ref",
    ]
    missing_fields = [field for field in required_fields if field not in payload]
    if missing_fields:
        failures.append("missing fields: " + ", ".join(missing_fields))
        return failures

    if not isinstance(payload.get("allowed_next_actions"), list) or not payload["allowed_next_actions"]:
        failures.append("allowed_next_actions must be a non-empty array")
    if not isinstance(payload.get("selection_order"), list) or not payload["selection_order"]:
        failures.append("selection_order must be a non-empty array")
    if not isinstance(payload.get("required_entrypoints"), list) or not payload["required_entrypoints"]:
        failures.append("required_entrypoints must be a non-empty array")
    if not isinstance(payload.get("required_doc_refs"), list) or not payload["required_doc_refs"]:
        failures.append("required_doc_refs must be a non-empty array")

    review_expires_at = payload.get("review_expires_at")
    if not isinstance(review_expires_at, str) or not review_expires_at.strip():
        failures.append("review_expires_at must be a non-empty string")
    else:
        try:
            date.fromisoformat(review_expires_at)
        except ValueError:
            failures.append("review_expires_at must be a valid ISO date")

    for entry in payload.get("selection_order", []):
        if not isinstance(entry, dict):
            failures.append("selection_order entries must be objects")
            continue
        for key in ["next_action", "why"]:
            value = entry.get(key)
            if not isinstance(value, str) or not value.strip():
                failures.append(f"selection_order entry missing {key}")

    for relative_path in payload.get("required_entrypoints", []):
        if not isinstance(relative_path, str) or not relative_path.strip():
            failures.append("required_entrypoints entries must be non-empty strings")
            continue
        if not (root / relative_path).exists():
            failures.append(f"missing required entrypoint: {relative_path}")

    for item in payload.get("required_doc_refs", []):
        if not isinstance(item, dict):
            failures.append("required_doc_refs entries must be objects")
            continue
        path = item.get("path")
        contains = item.get("contains")
        if not isinstance(path, str) or not path.strip():
            failures.append("required_doc_refs.path must be a non-empty string")
            continue
        if not isinstance(contains, str) or not contains.strip():
            failures.append(f"required_doc_refs.contains must be a non-empty string: {path}")
            continue
        document_path = root / path
        if not document_path.exists():
            failures.append(f"missing required_doc_refs path: {path}")
            continue
        text = document_path.read_text(encoding="utf-8")
        if contains not in text:
            failures.append(f"required_doc_refs token missing: {path}:{contains}")

    return failures


def _render_relative(*, root: Path, path: Path) -> str:
    try:
        return str(path.resolve(strict=False).relative_to(root.resolve(strict=False))).replace("\\", "/")
    except ValueError:
        return str(path.resolve(strict=False)).replace("\\", "/")


def _load_json(path: Path) -> dict[str, object]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"planning status file is not readable: {path} ({exc})") from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"planning status file is invalid JSON: {path} ({exc.msg})") from exc
    if not isinstance(payload, dict):
        raise ValueError("planning status file must be a JSON object")
    return payload


if __name__ == "__main__":
    raise SystemExit(main())
