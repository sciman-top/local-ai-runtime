from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = REPO_ROOT / "runtime" / "host-orchestrator"
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from host_orchestrator.agent_work_assets import (  # noqa: E402
    load_mapping_file,
    validate_closeout_bundle_payload,
    validate_dispatch_state_payload,
    validate_manifest_payload,
    validate_review_result_payload,
)
from host_orchestrator.adaptive_orchestration import (  # noqa: E402
    validate_orchestration_decision_payload,
    validate_orchestration_execution_payload,
)
from host_orchestrator.runner_acceptance import validate_runner_acceptance_payload  # noqa: E402


def main() -> int:
    validations = [
        ("manifest", REPO_ROOT / "templates" / "agent-work-manifest.example.yaml", validate_manifest_payload),
        ("dispatch_state", REPO_ROOT / "templates" / "dispatch-state.example.json", validate_dispatch_state_payload),
        ("closeout_bundle", REPO_ROOT / "templates" / "closeout-bundle.example.json", validate_closeout_bundle_payload),
        ("review_result", REPO_ROOT / "templates" / "review-result.example.json", validate_review_result_payload),
        (
            "orchestration_decision",
            REPO_ROOT / "templates" / "orchestration-decision.example.json",
            validate_orchestration_decision_payload,
        ),
        (
            "orchestration_execution",
            REPO_ROOT / "templates" / "orchestration-execution.example.json",
            validate_orchestration_execution_payload,
        ),
        (
            "runner_acceptance",
            REPO_ROOT / "templates" / "non-host-local-runner-acceptance.example.json",
            validate_runner_acceptance_payload,
        ),
    ]

    checked: list[dict[str, str]] = []
    for kind, path, validator in validations:
        payload = load_mapping_file(path)
        validator(payload)
        checked.append({"kind": kind, "path": str(path.relative_to(REPO_ROOT))})

    print(
        json.dumps(
            {
                "status": "pass",
                "repo_root": str(REPO_ROOT),
                "checked": checked,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
