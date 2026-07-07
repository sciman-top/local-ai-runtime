from __future__ import annotations

import json
from pathlib import Path

from host_orchestrator.claude_code_worker import (
    ClaudeCodeStructuredWorker,
    ClaudeCommandResult,
    build_claude_print_argv,
)
from host_orchestrator.worker import WorkerRequest


def test_build_claude_print_argv_shapes_noninteractive_structured_call(tmp_path: Path) -> None:
    request = WorkerRequest(
        prompt="Review the runtime artifacts.",
        cwd=tmp_path,
        model="glm-5.2",
    )
    schema = {
        "type": "object",
        "properties": {"ok": {"type": "boolean"}},
        "required": ["ok"],
    }

    argv = build_claude_print_argv(request, schema)

    assert argv == [
        "claude",
        "--bare",
        "--no-session-persistence",
        "-p",
        "Review the runtime artifacts.",
        "--output-format",
        "json",
        "--effort",
        "low",
        "--permission-mode",
        "dontAsk",
        "--tools",
        "",
        "--model",
        "glm-5.2",
        "--json-schema",
        json.dumps(schema, ensure_ascii=False),
    ]


def test_claude_structured_worker_reads_structured_output_and_usage(tmp_path: Path) -> None:
    request = WorkerRequest(
        prompt="Review the runtime artifacts.",
        cwd=tmp_path,
        model="glm-5.2",
    )
    schema = {
        "type": "object",
        "properties": {"ok": {"type": "boolean"}},
        "required": ["ok"],
    }

    class FakeExecutor:
        def run(self, argv: list[str], cwd: Path) -> ClaudeCommandResult:
            assert cwd == tmp_path
            return ClaudeCommandResult(
                argv=argv,
                returncode=0,
                stdout=json.dumps(
                    {
                        "structured_output": {"ok": True},
                        "modelUsage": {
                            "glm-5.2": {
                                "inputTokens": 321,
                                "outputTokens": 45,
                                "cacheReadInputTokens": 7,
                                "cacheCreationInputTokens": 0,
                                "contextWindow": 200000,
                            }
                        },
                    }
                ),
                stderr="",
            )

    worker = ClaudeCodeStructuredWorker(
        json_schema=schema,
        executor=FakeExecutor(),
    )

    result = worker.run(request)

    assert result.final_response == "{\"ok\": true}"
    assert result.usage is not None
    assert result.usage.source == "claude_cli_structured"
    assert result.usage.total.input_tokens == 321
    assert result.usage.total.output_tokens == 45
    assert result.usage.total.cached_input_tokens == 7
    assert result.usage.model_context_window == 200000


def test_claude_structured_worker_accepts_direct_schema_shaped_json(tmp_path: Path) -> None:
    request = WorkerRequest(
        prompt="Review the runtime artifacts.",
        cwd=tmp_path,
        model="glm-5.2",
    )
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {"ok": {"type": "boolean"}},
        "required": ["ok"],
    }

    class FakeExecutor:
        def run(self, argv: list[str], cwd: Path) -> ClaudeCommandResult:
            assert cwd == tmp_path
            return ClaudeCommandResult(
                argv=argv,
                returncode=0,
                stdout="{\"ok\": true}",
                stderr="",
            )

    worker = ClaudeCodeStructuredWorker(
        json_schema=schema,
        executor=FakeExecutor(),
    )

    result = worker.run(request)

    assert result.final_response == "{\"ok\": true}"
