from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

RUNNER_ACCEPTANCE_SCHEMA_VERSION = "non_host_local_runner_acceptance.v1"


class RunnerAcceptanceError(ValueError):
    """Raised when a non-host-local runner acceptance payload is invalid."""


def validate_runner_acceptance_file(
    *,
    acceptance_path: Path,
    acceptance_ref: str,
    worker_profile: str | None = None,
    lane: str | None = None,
    runner_kind: str | None = None,
) -> None:
    context = f"runner_acceptance_ref:{acceptance_ref}"
    try:
        payload = json.loads(acceptance_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RunnerAcceptanceError(f"{context} must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise RunnerAcceptanceError(f"{context} must contain a JSON object")
    validate_runner_acceptance_payload(
        payload,
        context=context,
        worker_profile=worker_profile,
        lane=lane,
        runner_kind=runner_kind,
    )


def validate_runner_acceptance_payload(
    payload: Mapping[str, Any],
    *,
    context: str = "runner_acceptance",
    worker_profile: str | None = None,
    lane: str | None = None,
    runner_kind: str | None = None,
) -> None:
    schema_version = _require_string(payload, "schema_version", context)
    if schema_version != RUNNER_ACCEPTANCE_SCHEMA_VERSION:
        raise RunnerAcceptanceError(
            f"{context}:schema_version must be {RUNNER_ACCEPTANCE_SCHEMA_VERSION}"
        )
    acceptance_status = _require_string(payload, "acceptance_status", context)
    if acceptance_status != "accepted":
        raise RunnerAcceptanceError(f"{context}:acceptance_status must be accepted")

    if worker_profile is None:
        _require_string(payload, "worker_profile", context)
    else:
        _require_match(payload, key="worker_profile", expected=worker_profile, context=context)
    if lane is None:
        _require_string(payload, "lane", context)
    else:
        _require_match(payload, key="lane", expected=lane, context=context)
    if runner_kind is None:
        _require_string(payload, "runner_kind", context)
    else:
        _require_match(payload, key="runner_kind", expected=runner_kind, context=context)

    _require_string(payload, "accepted_by", context)
    _require_string(payload, "accepted_at", context)
    _require_string(payload, "acceptance_scope", context)
    evidence_refs = _require_string_list(payload, "evidence_refs", context)
    if not evidence_refs:
        raise RunnerAcceptanceError(f"{context}:evidence_refs must contain at least one item")


def _require_match(
    payload: Mapping[str, Any],
    *,
    key: str,
    expected: str,
    context: str,
) -> None:
    actual = _require_string(payload, key, context)
    if actual != expected:
        raise RunnerAcceptanceError(f"{context}:{key} must be {expected}")


def _require_string(payload: Mapping[str, Any], key: str, context: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RunnerAcceptanceError(f"{context}:{key} must be a non-empty string")
    return value.strip()


def _require_string_list(payload: Mapping[str, Any], key: str, context: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise RunnerAcceptanceError(f"{context}:{key} must be a list of strings")
    values: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise RunnerAcceptanceError(
                f"{context}:{key}[{index}] must be a non-empty string"
            )
        values.append(item.strip())
    return values
