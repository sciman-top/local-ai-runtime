from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATUS_PATH = ROOT / "docs" / "architecture" / "planning-status.json"
SUPPLEMENTAL_SYNC_FILES = [
    ROOT / "ai_dev_orchestrator_impl_pack" / "00_README_FIRST.md",
    ROOT / "ai_dev_orchestrator_impl_pack" / "04_REPOSITORY_LAYOUT.md",
    ROOT / "ai_dev_orchestrator_impl_pack" / "13_BOOTSTRAP_CHECKLIST.md",
    ROOT / "ai_dev_orchestrator_impl_pack" / "14_HANDOFF_MESSAGE_TO_CODEX.md",
]
SUPPLEMENTAL_FORBIDDEN_TOKENS = [
    "创建项目目录骨架",
    "生成最小可运行的 Python Orchestrator",
    "project-root/",
    "  orchestrator/",
    "`orchestrator/`：Python 主体代码",
    "创建目录结构",
    "仅创建目录",
]
SUPPLEMENTAL_REQUIRED_TOKENS = [
    "runtime/host-orchestrator",
    ".ai/state/control-plane.db",
    ".ai/runs/<run_id>/<task_id>/",
]
REQUIRED_DOC_SNIPPETS = {
    "README.md": [
        "Governance Overlay",
        "phase1_prereq_probe_first",
    ],
    "docs/README.md": [
        "Governance Overlay",
        "phase1_prereq_probe_first",
    ],
    "docs/product/orchestrator-prd.md": [
        "selector + change-evidence + preflight + reference governance",
    ],
    "docs/architecture/orchestrator-target-architecture.md": [
        "Governance Overlay",
        "docs/change-evidence/README.md",
    ],
    "docs/specs/result-contract.md": [
        "docs/change-evidence/README.md",
    ],
    "docs/roadmap/orchestrator-roadmap.md": [
        "Governance Overlay",
        "GOV-T01",
        "phase1_prereq_probe_first",
    ],
    "docs/plans/orchestrator-implementation-plan.md": [
        "Governance Overlay",
        "GOV-T01",
        "phase1_prereq_probe_first",
    ],
    "docs/backlog/orchestrator-task-list.md": [
        "GOV-T01",
        "PHASE-1-VERTICAL-SLICE",
        "phase1_prereq_probe_first",
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
    }


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
