from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
from typing import Any, Protocol

from host_orchestrator.process_guard import run_guarded_process
from host_orchestrator.worker import UsageBreakdown, WorkerRequest, WorkerResult, WorkerUsage


@dataclass(frozen=True)
class ClaudeCommandResult:
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str


class ClaudeCommandExecutor(Protocol):
    def run(self, argv: list[str], cwd: Path) -> ClaudeCommandResult: ...


class ClaudeSubprocessExecutor:
    def __init__(self, *, timeout_seconds: float | None = None) -> None:
        self._timeout_seconds = timeout_seconds

    def run(self, argv: list[str], cwd: Path) -> ClaudeCommandResult:
        completed = run_guarded_process(
            argv,
            cwd=cwd,
            timeout_seconds=self._timeout_seconds,
            encoding="utf-8",
            errors="replace",
        )
        return ClaudeCommandResult(
            argv=list(argv),
            returncode=int(completed.returncode),
            stdout=str(completed.stdout),
            stderr=str(completed.stderr),
        )


def build_claude_print_argv(
    request: WorkerRequest,
    json_schema: dict[str, Any],
) -> list[str]:
    return [
        "claude",
        "--bare",
        "--no-session-persistence",
        "-p",
        request.prompt,
        "--output-format",
        "json",
        "--effort",
        "low",
        "--permission-mode",
        "dontAsk",
        "--tools",
        "",
        "--model",
        request.model,
        "--json-schema",
        json.dumps(json_schema, ensure_ascii=False),
    ]


class ClaudeCodeStructuredWorker:
    def __init__(
        self,
        *,
        json_schema: dict[str, Any],
        executor: ClaudeCommandExecutor | None = None,
    ) -> None:
        self._json_schema = json_schema
        self._executor = executor or ClaudeSubprocessExecutor()

    def run(self, request: WorkerRequest) -> WorkerResult:
        command = build_claude_print_argv(request, self._json_schema)
        command[0] = _resolve_claude_command()
        result = self._executor.run(command, request.cwd)
        if result.returncode != 0:
            raise RuntimeError(
                "claude structured worker failed "
                f"(exit={result.returncode}): {result.stderr or result.stdout}"
            )

        payload = _parse_json_object(result.stdout, error_label="claude structured worker")
        structured_output = _extract_structured_output(payload, self._json_schema)

        return WorkerResult(
            final_response=json.dumps(structured_output, ensure_ascii=False),
            raw_result=payload,
            usage=_extract_usage(payload, request.model),
            stdout_text=result.stdout,
            stderr_text=result.stderr,
        )


def _resolve_claude_command() -> str:
    for candidate in ("claude.cmd", "claude", "claude.exe"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise RuntimeError("claude CLI is not available on PATH for the review sidecar")


def _extract_structured_output(
    payload: dict[str, Any],
    json_schema: dict[str, Any],
) -> dict[str, Any]:
    structured_output = payload.get("structured_output")
    if isinstance(structured_output, dict):
        return structured_output

    result = payload.get("result")
    if isinstance(result, str):
        parsed_result = _try_parse_json_object(result)
        if parsed_result is not None and _matches_top_level_schema(parsed_result, json_schema):
            return parsed_result

    if _matches_top_level_schema(payload, json_schema):
        return payload

    raise RuntimeError("claude structured worker did not return a schema-shaped JSON object")


def _try_parse_json_object(text: str) -> dict[str, Any] | None:
    try:
        return _parse_json_object(text, error_label="claude structured worker result")
    except RuntimeError:
        return None


def _parse_json_object(text: str, *, error_label: str) -> dict[str, Any]:
    normalized = _strip_markdown_fence(text).strip()
    if not normalized:
        raise RuntimeError(f"{error_label} returned empty output")
    try:
        payload = json.loads(normalized)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{error_label} returned non-JSON output") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{error_label} returned a non-object payload")
    return payload


def _strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def _matches_top_level_schema(
    payload: dict[str, Any],
    json_schema: dict[str, Any],
) -> bool:
    if json_schema.get("type") != "object":
        return isinstance(payload, dict)

    required = json_schema.get("required")
    if isinstance(required, list):
        required_keys = [item for item in required if isinstance(item, str)]
        if not all(key in payload for key in required_keys):
            return False

    properties = json_schema.get("properties")
    if json_schema.get("additionalProperties") is False and isinstance(properties, dict):
        allowed_keys = {key for key in properties.keys() if isinstance(key, str)}
        if not set(payload.keys()).issubset(allowed_keys):
            return False

    return True


def _extract_usage(payload: dict[str, Any], model: str) -> WorkerUsage | None:
    model_usage = payload.get("modelUsage")
    if isinstance(model_usage, dict):
        candidate = model_usage.get(model)
        if isinstance(candidate, dict):
            breakdown = _usage_from_model_usage(candidate)
            if breakdown is not None:
                return WorkerUsage(
                    source="claude_cli_structured",
                    last=breakdown,
                    total=breakdown,
                    model_context_window=_optional_int(candidate.get("contextWindow")),
                )

    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None

    input_tokens = _optional_int(usage.get("input_tokens"))
    output_tokens = _optional_int(usage.get("output_tokens"))
    cached_input_tokens = _optional_int(usage.get("cache_read_input_tokens"), default=0)
    total_tokens = None
    if input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens
    if total_tokens is None:
        return None
    breakdown = UsageBreakdown(
        cached_input_tokens=cached_input_tokens or 0,
        input_tokens=input_tokens or 0,
        output_tokens=output_tokens or 0,
        reasoning_output_tokens=0,
        total_tokens=total_tokens,
    )
    return WorkerUsage(
        source="claude_cli_structured",
        last=breakdown,
        total=breakdown,
        model_context_window=None,
    )


def _usage_from_model_usage(candidate: dict[str, Any]) -> UsageBreakdown | None:
    input_tokens = _optional_int(candidate.get("inputTokens"))
    output_tokens = _optional_int(candidate.get("outputTokens"))
    cached_input_tokens = _optional_int(candidate.get("cacheReadInputTokens"), default=0)
    cache_creation_input_tokens = _optional_int(candidate.get("cacheCreationInputTokens"), default=0)
    if input_tokens is None or output_tokens is None:
        return None
    return UsageBreakdown(
        cached_input_tokens=(cached_input_tokens or 0) + (cache_creation_input_tokens or 0),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reasoning_output_tokens=0,
        total_tokens=input_tokens + output_tokens,
    )


def _optional_int(value: Any, default: int | None = None) -> int | None:
    if value is None:
        return default
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return default
