from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "docs" / "architecture" / "planning-status.json"
SUPPLEMENTAL_SYNC_FILES = [
    ROOT / "ai_dev_orchestrator_impl_pack" / "00_README_FIRST.md",
    ROOT / "ai_dev_orchestrator_impl_pack" / "04_REPOSITORY_LAYOUT.md",
    ROOT / "ai_dev_orchestrator_impl_pack" / "13_BOOTSTRAP_CHECKLIST.md",
    ROOT / "ai_dev_orchestrator_impl_pack" / "14_HANDOFF_MESSAGE_TO_CODEX.md",
]
SUPPLEMENTAL_FORBIDDEN_TOKENS = [
    "创建项目目录骨架",
    "生成最小可运行的 Python Orchestrator",
]


def main() -> int:
    try:
        result = verify()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def verify() -> dict[str, object]:
    payload = _load_json(STATUS_PATH)
    required_fields = [
        "current_active_queue",
        "current_decision_gate",
        "certified_baseline",
        "authoritative_docs",
        "required_consistency_tokens",
        "unexpected_tokens",
        "rollback_ref",
    ]
    missing_fields = [field for field in required_fields if field not in payload]

    authoritative_docs = [ROOT / Path(item) for item in payload.get("authoritative_docs", [])]
    missing_files = [str(path.relative_to(ROOT)) for path in authoritative_docs if not path.exists()]

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
                unexpected_tokens.append(f"{path.relative_to(ROOT)}:{token}")

    supplemental_violations: list[str] = []
    for path in SUPPLEMENTAL_SYNC_FILES:
        if not path.exists():
            supplemental_violations.append(f"missing supplemental sync file: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        for token in SUPPLEMENTAL_FORBIDDEN_TOKENS:
            if token in text:
                supplemental_violations.append(f"{path.relative_to(ROOT)}:{token}")

    baseline_ref = payload.get("certified_baseline", {}).get("evidence_ref")
    baseline_missing = []
    if baseline_ref:
        baseline_path = ROOT / Path(baseline_ref)
        if not baseline_path.exists():
            baseline_missing.append(baseline_ref)

    failures: list[str] = []
    if missing_fields:
        failures.append("missing fields: " + ", ".join(missing_fields))
    if missing_files:
        failures.append("missing files: " + ", ".join(missing_files))
    if baseline_missing:
        failures.append("missing certified baseline files: " + ", ".join(baseline_missing))
    if missing_tokens:
        failures.append("missing required tokens: " + ", ".join(missing_tokens))
    if unexpected_tokens:
        failures.append("unexpected authoritative tokens: " + ", ".join(unexpected_tokens))
    if supplemental_violations:
        failures.append("supplemental sync violations: " + ", ".join(supplemental_violations))

    if failures:
        raise ValueError("planning status verification failed: " + "; ".join(failures))

    return {
        "status": "pass",
        "status_path": str(STATUS_PATH.relative_to(ROOT)).replace("\\", "/"),
        "authoritative_doc_count": len(authoritative_docs),
        "supplemental_sync_files": [str(path.relative_to(ROOT)).replace("\\", "/") for path in SUPPLEMENTAL_SYNC_FILES],
    }


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
