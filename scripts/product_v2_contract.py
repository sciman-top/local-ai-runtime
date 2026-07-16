"""Stdlib-only verifier for the frozen ProductContract.v2 bundle."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable


PRODUCT_V2_PATHS = {
    "policy": Path("docs/specs/local-ai-runtime-0.2/normative/ProductContract.v2.json"),
    "first_run_schema": Path(
        "docs/specs/local-ai-runtime-0.2/schemas/FirstRunExperience.v1.schema.json"
    ),
    "launch_template_catalog": Path(
        "docs/specs/local-ai-runtime-0.2/catalogs/LaunchTemplateCatalog.v1.json"
    ),
    "operator_presentation_catalog": Path(
        "docs/specs/local-ai-runtime-0.2/catalogs/OperatorPresentationCatalog.v1.json"
    ),
    "fixture": Path(
        "docs/specs/local-ai-runtime-0.2/fixtures/product-v2/manifest.json"
    ),
}

EXPECTED_PRODUCT_V2_IDENTITIES = {
    "policy": {
        "byte_count": 14902,
        "sha256": "ef93061279accfd6af7a580d1eafbb3352bf8a8a4f610f7bcd86006643a9bcae",
    },
    "first_run_schema": {
        "byte_count": 5080,
        "sha256": "1f5ebdc4bc33bc5a145bdb6331e11275688e783ab895ab0bb5f9dece965ac462",
    },
    "launch_template_catalog": {
        "byte_count": 9371,
        "sha256": "dd6d0065bc00aa13f4427c650050c39604c13e4c933966c6efe812590b5d861e",
    },
    "operator_presentation_catalog": {
        "byte_count": 5701,
        "sha256": "c028d50742f1d55005310eb542875bfd00d255c3101a2cc08fcc4fc76fb2db8e",
    },
    "fixture": {
        "byte_count": 3092,
        "sha256": "4775a5c0075a3c2146c9792930de15c058cd77e913ae3c15826df4de9f345ce5",
    },
}

EXPECTED_STEP_COMMANDS = {
    "doctor_setup_readiness": "runtime doctor --setup-readiness",
    "install_qualify_staged": "runtime install/qualify --staged",
    "activate_dry_run": "runtime activate --dry-run",
    "repo_inspect_qualify": "repo inspect/qualify --repo <path>",
    "template_list_eligible": "template list --eligible --repo <repo_id>",
    "authorization_prepare_activate": (
        "authorization prepare/activate --repo <repo_id> --template <template_id>"
    ),
    "batch_submit": (
        "batch submit --repo <repo_id> --template <template_id> "
        "--params <public-json> --expected-base <oid>"
    ),
    "batch_status_watch": "batch status/watch <task_id>",
    "batch_inspect": "batch inspect <task_id>",
    "review_local_commit": "batch inspect <task_id> --review-bundle",
}

EXPECTED_TEMPLATE_IDS = [
    "docs_contract_sync_v1",
    "bounded_lint_type_repair_v1",
    "focused_test_repair_v1",
    "mechanical_repo_maintenance_v1",
]

EXPECTED_PROMOTION_FLOW = [
    "candidate_definition",
    "negative_examples",
    "disposable_dry_run",
    "repo_template_qualification",
    "explicit_operator_promotion",
    "reusable_authorization",
]

EXPECTED_METRIC_IDS = {
    "prequalified_host_to_first_dry_run_net_human_minutes",
    "first_commit_ready_pilot_net_human_minutes",
    "template_qualification_lead_time",
    "eligible_template_coverage",
    "operator_action_age",
    "policy_false_block_review_rate",
    "recovery_to_terminal_time",
    "template_maintenance_minutes_per_success",
}

EXPECTED_VIEW_IDS = {
    "runtime_status_v1",
    "repo_status_v1",
    "batch_status_v1",
    "operator_action_inbox_v1",
    "doctor_result_v1",
}

EXPECTED_REASON_CODES = {
    "configuration_error",
    "needs_auth",
    "needs_environment",
    "platform_incompatible",
    "transient_unavailable",
    "operator_review_required",
    "cleanup_incomplete",
    "qualification_stale",
}

FORBIDDEN_OUTPUT_SOURCES = {
    "raw_model_output",
    "raw_tool_output",
    "secret_derived_metadata",
}

FORBIDDEN_PARAMETER_KINDS = {
    "free_prompt",
    "free_text",
    "dynamic_command",
    "command",
    "argv",
    "environment",
    "secret",
}

FORBIDDEN_PARAMETER_IDS = {
    "prompt",
    "free_prompt",
    "command",
    "argv",
    "environment",
    "secret",
    "secret_token",
    "api_key",
    "password",
    "model",
    "provider",
    "sandbox",
    "permission_root",
}

ALLOWED_EFFECTS = {
    "read_repo_file",
    "write_allowlisted_file",
    "run_declared_gate",
    "run_declared_generator",
    "create_local_commit",
    "create_runtime_task_ref",
    "write_task_evidence",
}


class ProductV2ValidationError(RuntimeError):
    """Raised with a stable machine reason for a v2 contract failure."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def _object(value: Any, label: str, reason: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProductV2ValidationError(reason, f"{label} must be an object")
    return value


def _array(value: Any, label: str, reason: str) -> list[Any]:
    if not isinstance(value, list):
        raise ProductV2ValidationError(reason, f"{label} must be an array")
    return value


def _exact(value: Any, fields: set[str], label: str, reason: str) -> dict[str, Any]:
    result = _object(value, label, reason)
    if set(result) != fields:
        raise ProductV2ValidationError(reason, f"{label} fields mismatch")
    return result


def _load(root: Path, key: str) -> tuple[dict[str, Any], bytes]:
    path = root / PRODUCT_V2_PATHS[key]
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProductV2ValidationError(
            "product_v2_json", f"cannot read {PRODUCT_V2_PATHS[key]}"
        ) from exc
    if not isinstance(value, dict):
        raise ProductV2ValidationError(
            "product_v2_json", f"{PRODUCT_V2_PATHS[key]} must be a JSON object"
        )
    expected = EXPECTED_PRODUCT_V2_IDENTITIES[key]
    if len(raw) != expected["byte_count"] or hashlib.sha256(raw).hexdigest() != expected["sha256"]:
        raise ProductV2ValidationError(
            f"product_v2_{key}_identity",
            f"{PRODUCT_V2_PATHS[key]} identity mismatch",
        )
    return value, raw


def _validate_first_run_schema(schema: dict[str, Any]) -> None:
    if (
        schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
        or schema.get("title") != "FirstRunExperiencePolicy.v1"
        or schema.get("type") != "object"
        or schema.get("additionalProperties") is not False
    ):
        raise ProductV2ValidationError("first_run_schema", "schema envelope mismatch")
    required = schema.get("required")
    properties = schema.get("properties")
    if not isinstance(required, list) or not isinstance(properties, dict) or set(required) != set(properties):
        raise ProductV2ValidationError("first_run_schema", "schema root closure mismatch")
    journey = _object(properties.get("journey"), "journey schema", "first_run_schema")
    if journey.get("minItems") != 10 or journey.get("maxItems") != 10:
        raise ProductV2ValidationError("first_run_schema", "journey cardinality is not closed")
    definitions = _object(schema.get("$defs"), "$defs", "first_run_schema")
    step = _object(definitions.get("journey_step"), "journey_step", "first_run_schema")
    if step.get("additionalProperties") is not False:
        raise ProductV2ValidationError("first_run_schema", "journey step is not closed")


def _validate_first_run(value: Any) -> None:
    first_run = _exact(
        value,
        {
            "policy_id",
            "policy_version",
            "baseline_id",
            "journey",
            "output_contract",
            "mutation_contract",
            "exit_codes",
            "terminal_outcome",
        },
        "first-run policy",
        "first_run_schema",
    )
    if (
        first_run["policy_id"] != "first_run_cli_to_reviewable_commit"
        or first_run["policy_version"] != "FirstRunExperiencePolicy.v1"
        or first_run["baseline_id"] != "local-ai-runtime-0.2-v3.24"
    ):
        raise ProductV2ValidationError("first_run_schema", "first-run identity mismatch")
    steps = _array(first_run["journey"], "first-run journey", "first_run_journey")
    if len(steps) != 10:
        raise ProductV2ValidationError("first_run_journey", "first-run journey must have ten steps")
    ids: list[str] = []
    for index, raw_step in enumerate(steps, start=1):
        step = _exact(
            raw_step,
            {
                "step_id",
                "order",
                "command",
                "kind",
                "authority",
                "input_fields",
                "human_output_fields",
                "json_output_fields",
                "success_exit_code",
                "failure_exit_codes",
                "evidence_locator",
                "rollback",
                "next_step_ids",
            },
            "first-run step",
            "first_run_journey",
        )
        step_id = step["step_id"]
        if step_id not in EXPECTED_STEP_COMMANDS or step["command"] != EXPECTED_STEP_COMMANDS[step_id]:
            raise ProductV2ValidationError("first_run_journey", "step command mismatch")
        if step["order"] != index or step["success_exit_code"] != 0 or step["failure_exit_codes"] != [2, 3]:
            raise ProductV2ValidationError("first_run_journey", "step ordering or exit codes mismatch")
        public_outputs = set(
            _array(step["human_output_fields"], "human fields", "first_run_output")
        ) | set(_array(step["json_output_fields"], "JSON fields", "first_run_output"))
        if public_outputs & FORBIDDEN_OUTPUT_SOURCES:
            raise ProductV2ValidationError("first_run_output", "raw or secret output is exposed")
        if step["kind"] == "read_only" and step["authority"] != "none":
            raise ProductV2ValidationError("first_run_mutation", "read-only step requires authority")
        if step["kind"] == "mutation":
            required_preview = {
                "effect_summary",
                "authority",
                "expected_generation",
                "rollback_entrypoint",
                "challenge_required",
            }
            if not required_preview.issubset(set(step["json_output_fields"])):
                raise ProductV2ValidationError("first_run_mutation", "mutation preview is incomplete")
        ids.append(step_id)
    if ids != list(EXPECTED_STEP_COMMANDS):
        raise ProductV2ValidationError("first_run_journey", "step identity order mismatch")
    for index, step in enumerate(steps):
        expected_next = [] if index == len(steps) - 1 else [steps[index + 1]["step_id"]]
        if step["next_step_ids"] != expected_next:
            raise ProductV2ValidationError("first_run_journey", "journey next edge mismatch")
    output = _object(first_run["output_contract"], "output contract", "first_run_output")
    if (
        output.get("machine_format") != "stable_json"
        or output.get("machine_unknown_field_policy") != "fail_closed"
        or output.get("human_renderer") != "OperatorPresentationCatalog.v1"
        or set(output.get("forbidden_sources", [])) != FORBIDDEN_OUTPUT_SOURCES
    ):
        raise ProductV2ValidationError("first_run_output", "first-run output boundary mismatch")
    mutation = _object(first_run["mutation_contract"], "mutation contract", "first_run_mutation")
    if (
        mutation.get("preview_required") is not True
        or mutation.get("read_only_approval_policy") != "never"
        or mutation.get("required_preview_fields")
        != [
            "effect_summary",
            "authority",
            "expected_generation",
            "rollback_entrypoint",
            "challenge_required",
        ]
    ):
        raise ProductV2ValidationError("first_run_mutation", "mutation boundary mismatch")
    if first_run["exit_codes"] != {
        "success": 0,
        "policy_or_input_error": 2,
        "temporary_unavailable": 3,
    }:
        raise ProductV2ValidationError("first_run_output", "exit code contract mismatch")
    terminal = _object(first_run["terminal_outcome"], "terminal outcome", "first_run_journey")
    if (
        terminal.get("result") != "reviewable_local_commit"
        or terminal.get("delivery") != ["deterministic_local_commit", "runtime_owned_task_ref"]
        or terminal.get("forbidden_delivery") != ["merge", "push", "pull_request", "deployment"]
    ):
        raise ProductV2ValidationError("first_run_journey", "terminal outcome mismatch")


def _validate_launch_catalog(value: Any) -> None:
    catalog = _exact(
        value,
        {
            "catalog_id",
            "catalog_version",
            "baseline_id",
            "catalog_status",
            "template_count",
            "promotion_flow",
            "native_spec_authority",
            "templates",
        },
        "launch catalog",
        "launch_template_catalog",
    )
    if (
        catalog["catalog_version"] != "LaunchTemplateCatalog.v1"
        or catalog["baseline_id"] != "local-ai-runtime-0.2-v3.24"
        or catalog["catalog_status"] != "candidate_not_promoted"
        or catalog["template_count"] != 4
    ):
        raise ProductV2ValidationError("launch_template_catalog", "catalog identity mismatch")
    if catalog["promotion_flow"] != EXPECTED_PROMOTION_FLOW or catalog["native_spec_authority"] != "candidate_definition_only":
        raise ProductV2ValidationError("launch_template_promotion", "promotion flow mismatch")
    templates = _array(catalog["templates"], "launch templates", "launch_template_catalog")
    if [template.get("template_id") for template in templates if isinstance(template, dict)] != EXPECTED_TEMPLATE_IDS:
        raise ProductV2ValidationError("launch_template_catalog", "template set or order mismatch")
    for raw_template in templates:
        template = _exact(
            raw_template,
            {
                "template_id",
                "template_version",
                "purpose",
                "work_class",
                "risk_class",
                "host_scope",
                "parameter_definitions",
                "path_envelope",
                "effect_envelope",
                "required_gates",
                "forbidden_gates",
                "forbidden_effects",
                "expected_outputs",
                "stop_reasons",
                "recovery_class",
                "evaluation",
                "rollback",
            },
            "launch template",
            "launch_template_catalog",
        )
        if template["template_version"] != 1 or template["work_class"] != "batch" or template["risk_class"] != "low" or template["host_scope"] != "host_local":
            raise ProductV2ValidationError("launch_template_catalog", "template boundary mismatch")
        parameters = _array(
            template["parameter_definitions"], "template parameters", "launch_template_parameter"
        )
        parameter_ids: list[str] = []
        for raw_parameter in parameters:
            parameter = _object(raw_parameter, "template parameter", "launch_template_parameter")
            parameter_id = parameter.get("parameter_id")
            kind = parameter.get("kind")
            if (
                not isinstance(parameter_id, str)
                or parameter_id in FORBIDDEN_PARAMETER_IDS
                or kind in FORBIDDEN_PARAMETER_KINDS
                or kind
                not in {
                    "boolean",
                    "integer",
                    "enum",
                    "public_id",
                    "public_id_array",
                    "approved_relative_path_id",
                    "approved_relative_path_id_array",
                }
                or not isinstance(parameter.get("required"), bool)
            ):
                raise ProductV2ValidationError("launch_template_parameter", "parameter is not closed")
            if kind == "integer" and (
                type(parameter.get("minimum")) is not int
                or type(parameter.get("maximum")) is not int
                or parameter["minimum"] > parameter["maximum"]
            ):
                raise ProductV2ValidationError("launch_template_parameter", "integer bounds invalid")
            if kind != "integer" and type(parameter.get("max_items")) is not int:
                raise ProductV2ValidationError("launch_template_parameter", "parameter bound missing")
            parameter_ids.append(parameter_id)
        if len(parameter_ids) != len(set(parameter_ids)):
            raise ProductV2ValidationError("launch_template_parameter", "duplicate parameter")
        path_envelope = _object(template["path_envelope"], "path envelope", "launch_template_path")
        if set(path_envelope) != {"read_classes", "write_classes", "max_primary_files"} or type(path_envelope["max_primary_files"]) is not int or path_envelope["max_primary_files"] < 1:
            raise ProductV2ValidationError("launch_template_path", "path envelope mismatch")
        effects = _array(template["effect_envelope"], "effect envelope", "launch_template_effect")
        if not effects or not set(effects).issubset(ALLOWED_EFFECTS):
            raise ProductV2ValidationError("launch_template_effect", "effect expansion detected")
        for field in ("required_gates", "forbidden_gates", "forbidden_effects", "expected_outputs", "stop_reasons"):
            values = _array(template[field], field, "launch_template_catalog")
            if not values or len(values) != len(set(values)) or not all(isinstance(item, str) for item in values):
                raise ProductV2ValidationError("launch_template_catalog", f"{field} is not closed")
        evaluation = _exact(
            template["evaluation"],
            {"denominator", "unknown_handling", "success"},
            "template evaluation",
            "launch_template_evaluation",
        )
        expected_denominator = f"all_admitted_{template['template_id']}_tasks"
        if evaluation["denominator"] != expected_denominator or evaluation["unknown_handling"] != "retain_as_unknown":
            raise ProductV2ValidationError("launch_template_evaluation", "evaluation denominator mismatch")


def _validate_operator_presentation(value: Any) -> None:
    catalog = _exact(
        value,
        {
            "catalog_id",
            "catalog_version",
            "baseline_id",
            "render_policy",
            "status_views",
            "reason_messages",
            "operator_action_contract",
        },
        "operator presentation catalog",
        "operator_presentation_catalog",
    )
    if catalog["catalog_version"] != "OperatorPresentationCatalog.v1" or catalog["baseline_id"] != "local-ai-runtime-0.2-v3.24":
        raise ProductV2ValidationError("operator_presentation_catalog", "catalog identity mismatch")
    render = _object(catalog["render_policy"], "render policy", "operator_presentation_source")
    if (
        render.get("human_renderer") != "catalog_template_only"
        or render.get("human_source") != "public_machine_state_reason_code_and_public_locator"
        or render.get("machine_format") != "stable_json"
        or render.get("machine_unknown_field_policy") != "fail_closed"
        or set(render.get("forbidden_sources", [])) != FORBIDDEN_OUTPUT_SOURCES
        or render.get("secret_field_policy") != "never_render_never_persist"
    ):
        raise ProductV2ValidationError("operator_presentation_source", "render source mismatch")
    views = _array(catalog["status_views"], "status views", "operator_presentation_catalog")
    if {view.get("view_id") for view in views if isinstance(view, dict)} != EXPECTED_VIEW_IDS:
        raise ProductV2ValidationError("operator_presentation_catalog", "status view set mismatch")
    for raw_view in views:
        view = _exact(
            raw_view,
            {"view_id", "command", "public_fields", "human_template", "empty_template", "forbidden_fields"},
            "status view",
            "operator_presentation_catalog",
        )
        public_fields = set(_array(view["public_fields"], "public fields", "operator_presentation_source"))
        forbidden_fields = set(_array(view["forbidden_fields"], "forbidden fields", "operator_presentation_source"))
        if public_fields & forbidden_fields or public_fields & FORBIDDEN_OUTPUT_SOURCES or not forbidden_fields:
            raise ProductV2ValidationError("operator_presentation_source", "view exposes forbidden source")
        if not isinstance(view["human_template"], str) or not isinstance(view["empty_template"], str):
            raise ProductV2ValidationError("operator_presentation_catalog", "human template missing")
    reasons = _array(catalog["reason_messages"], "reason messages", "operator_presentation_catalog")
    if {reason.get("reason_code") for reason in reasons if isinstance(reason, dict)} != EXPECTED_REASON_CODES:
        raise ProductV2ValidationError("operator_presentation_catalog", "reason code set mismatch")
    action = _object(catalog["operator_action_contract"], "operator action contract", "operator_action_contract")
    if (
        action.get("durability") != "sqlite_authority_with_public_evidence_locator"
        or action.get("resolution") != "explicit_catalog_action_only"
        or action.get("global_clear_forbidden") is not True
    ):
        raise ProductV2ValidationError("operator_action_contract", "operator action boundary mismatch")


def _validate_metrics(value: Any) -> None:
    metrics_policy = _exact(
        value,
        {"target_status", "p4_freeze_requirement", "metrics"},
        "product metrics",
        "product_metric",
    )
    if (
        metrics_policy["target_status"] != "unmeasured_no_target_claim"
        or metrics_policy["p4_freeze_requirement"]
        != "denominator_collection_and_unknown_policy_fixed_before_p4"
    ):
        raise ProductV2ValidationError("product_metric", "metric status mismatch")
    metrics = _array(metrics_policy["metrics"], "metrics", "product_metric")
    if {metric.get("metric_id") for metric in metrics if isinstance(metric, dict)} != EXPECTED_METRIC_IDS:
        raise ProductV2ValidationError("product_metric", "metric set mismatch")
    for raw_metric in metrics:
        metric = _exact(
            raw_metric,
            {"metric_id", "denominator", "collection_point", "unknown_handling", "target"},
            "metric",
            "product_metric",
        )
        if (
            not isinstance(metric["denominator"], str)
            or not metric["denominator"]
            or not isinstance(metric["collection_point"], str)
            or not metric["collection_point"]
            or "unknown" not in metric["unknown_handling"]
            or metric["target"] is not None
        ):
            raise ProductV2ValidationError("product_metric", "metric denominator or target mismatch")


def _validate_product_policy(value: Any, identities: dict[str, dict[str, Any]]) -> dict[str, Any]:
    envelope = _exact(value, {"domain", "schema_version", "payload"}, "ProductContract.v2", "product_v2_policy")
    if envelope["domain"] != "local-ai-runtime/ProductContract/v2" or envelope["schema_version"] != 2:
        raise ProductV2ValidationError("product_v2_policy", "policy envelope mismatch")
    payload = _exact(
        envelope["payload"],
        {
            "artifact_id",
            "artifact_version",
            "baseline_id",
            "predecessor_binding",
            "bundle_bindings",
            "product",
            "object_contracts",
            "work_routing_policy",
            "submission_policy",
            "promotion_policy",
            "first_run_experience",
            "launch_template_catalog",
            "operator_presentation",
            "product_metrics",
        },
        "ProductContract.v2 payload",
        "product_v2_policy",
    )
    if (
        payload["artifact_id"] != "P0A-PRODUCT"
        or payload["artifact_version"] != "ProductContract.v2"
        or payload["baseline_id"] != "local-ai-runtime-0.2-v3.24"
    ):
        raise ProductV2ValidationError("product_v2_policy", "artifact binding mismatch")
    predecessor = _object(payload["predecessor_binding"], "predecessor binding", "product_v2_policy")
    if predecessor != {
        "artifact_version": "ProductContract.v1",
        "path": "docs/specs/local-ai-runtime-0.2/normative/ProductContract.v1.json",
        "byte_count": 5003,
        "sha256": "b239cee308681ac5972e494ad4ff76958623fbd558a47e03b95e0be4159fb1ef",
        "disposition": "immutable_compatible_predecessor_not_sufficient_for_v324",
    }:
        raise ProductV2ValidationError("product_v2_policy", "predecessor binding mismatch")
    bindings = _object(payload["bundle_bindings"], "bundle bindings", "product_v2_bundle_binding")
    expected_binding_keys = {
        "first_run_schema": "first_run_schema",
        "launch_template_catalog": "launch_template_catalog",
        "operator_presentation_catalog": "operator_presentation_catalog",
        "fixture_manifest": "fixture",
    }
    if set(bindings) != set(expected_binding_keys):
        raise ProductV2ValidationError("product_v2_bundle_binding", "binding set mismatch")
    for binding_key, identity_key in expected_binding_keys.items():
        expected = identities[identity_key]
        expected_value = {
            "path": PRODUCT_V2_PATHS[identity_key].as_posix(),
            "byte_count": expected["byte_count"],
            "sha256": expected["sha256"],
        }
        if bindings[binding_key] != expected_value:
            raise ProductV2ValidationError("product_v2_bundle_binding", f"{binding_key} mismatch")
    objects = _object(payload["object_contracts"], "object contracts", "product_object_contract")
    if set(objects) != {"WorkDefinition_v2", "TaskFamily_v2", "TaskTemplate_v2", "BatchSubmission_v2"}:
        raise ProductV2ValidationError("product_object_contract", "object contract set mismatch")
    batch = _object(objects["BatchSubmission_v2"], "BatchSubmission_v2", "batch_submission_boundary")
    if (
        batch.get("exact_fields") != ["repo_id", "template_id", "parameters", "expected_base_commit"]
        or batch.get("additional_properties") is not False
        or batch.get("free_prompt_allowed") is not False
        or batch.get("canonical_domain") != "local-ai-runtime/BatchSubmission/v2"
    ):
        raise ProductV2ValidationError("batch_submission_boundary", "BatchSubmission.v2 expanded")
    template = _object(objects["TaskTemplate_v2"], "TaskTemplate_v2", "product_object_contract")
    if template.get("additional_properties") is not False or "free_prompt" not in template.get("forbidden_parameter_influence", []):
        raise ProductV2ValidationError("product_object_contract", "TaskTemplate.v2 is not closed")
    routing = _object(payload["work_routing_policy"], "routing policy", "product_routing")
    if (
        routing.get("output_work_classes") != ["native_direct", "native_spec", "native_program", "batch"]
        or routing.get("native_human_controlled") is not True
        or routing.get("native_spec_output") != "candidate_definition_only"
        or routing.get("runtime_model_router_service") != "absent"
    ):
        raise ProductV2ValidationError("product_routing", "Native/Batch boundary mismatch")
    promotion = _object(payload["promotion_policy"], "promotion policy", "launch_template_promotion")
    if (
        promotion.get("flow") != EXPECTED_PROMOTION_FLOW
        or promotion.get("native_spec_maximum_authority") != "candidate_definition_only"
        or promotion.get("automatic_promotion") is not False
        or promotion.get("candidate_execution_allowed") is not False
    ):
        raise ProductV2ValidationError("launch_template_promotion", "promotion policy mismatch")
    _validate_first_run(payload["first_run_experience"])
    launch_binding = _object(payload["launch_template_catalog"], "launch binding", "launch_template_catalog")
    if (
        launch_binding.get("required_template_ids") != EXPECTED_TEMPLATE_IDS
        or launch_binding.get("template_count") != 4
        or launch_binding.get("additional_templates_allowed") is not False
    ):
        raise ProductV2ValidationError("launch_template_catalog", "launch binding mismatch")
    presentation = _object(payload["operator_presentation"], "operator presentation", "operator_presentation_source")
    if (
        presentation.get("human_output_source") != "catalog_rendered_public_machine_state"
        or presentation.get("raw_output_interpolation") is not False
        or presentation.get("operator_action_inbox") != "durable_local_status_v1"
    ):
        raise ProductV2ValidationError("operator_presentation_source", "presentation binding mismatch")
    _validate_metrics(payload["product_metrics"])
    return payload


def _mutation_registry() -> dict[str, tuple[str, Callable[[dict[str, Any]], None]]]:
    return {
        "add_free_prompt_parameter": (
            "launch_template_parameter",
            lambda value: value["templates"][0]["parameter_definitions"].append(
                {"parameter_id": "notes", "required": False, "kind": "free_prompt", "max_items": 1}
            ),
        ),
        "add_dynamic_command_parameter": (
            "launch_template_parameter",
            lambda value: value["templates"][0]["parameter_definitions"].append(
                {"parameter_id": "command", "required": False, "kind": "dynamic_command", "max_items": 1}
            ),
        ),
        "add_dependency_install_effect": (
            "launch_template_effect",
            lambda value: value["templates"][0]["effect_envelope"].append("dependency_install"),
        ),
        "add_push_effect": (
            "launch_template_effect",
            lambda value: value["templates"][0]["effect_envelope"].append("push"),
        ),
        "add_secret_parameter": (
            "launch_template_parameter",
            lambda value: value["templates"][0]["parameter_definitions"].append(
                {"parameter_id": "secret_token", "required": False, "kind": "public_id", "max_items": 1}
            ),
        ),
        "remove_operator_promotion": (
            "launch_template_promotion",
            lambda value: value["promotion_flow"].remove("explicit_operator_promotion"),
        ),
        "allow_raw_model_output": (
            "operator_presentation_source",
            lambda value: value["render_policy"].__setitem__("human_source", "raw_model_output"),
        ),
        "remove_raw_tool_forbidden_source": (
            "first_run_output",
            lambda value: value["output_contract"]["forbidden_sources"].remove("raw_tool_output"),
        ),
        "require_read_only_approval": (
            "first_run_mutation",
            lambda value: value["mutation_contract"].__setitem__("read_only_approval_policy", "required"),
        ),
        "drop_unknown_from_denominator": (
            "product_metric",
            lambda value: value["payload"]["product_metrics"]["metrics"][0].__setitem__("unknown_handling", "drop"),
        ),
        "set_unmeasured_target": (
            "product_metric",
            lambda value: value["payload"]["product_metrics"]["metrics"][0].__setitem__("target", 5),
        ),
        "add_batch_submission_field": (
            "batch_submission_boundary",
            lambda value: value["payload"]["object_contracts"]["BatchSubmission_v2"]["exact_fields"].append("prompt"),
        ),
    }


def _verify_fixture(
    fixture: dict[str, Any],
    policy: dict[str, Any],
    launch_catalog: dict[str, Any],
    operator_catalog: dict[str, Any],
    identities: dict[str, dict[str, Any]],
) -> tuple[int, int]:
    fixture = _exact(
        fixture,
        {
            "fixture_id",
            "schema_version",
            "baseline_id",
            "policy_path",
            "legacy_policy_path",
            "first_run_schema_path",
            "launch_template_catalog_path",
            "operator_presentation_catalog_path",
            "positive_cases",
            "negative_mutations",
        },
        "product-v2 fixture",
        "product_v2_fixture",
    )
    if (
        fixture["fixture_id"] != "ProductContract.v2.contract-fixtures"
        or fixture["schema_version"] != 2
        or fixture["baseline_id"] != "local-ai-runtime-0.2-v3.24"
        or fixture["policy_path"] != PRODUCT_V2_PATHS["policy"].as_posix()
        or fixture["first_run_schema_path"] != PRODUCT_V2_PATHS["first_run_schema"].as_posix()
        or fixture["launch_template_catalog_path"]
        != PRODUCT_V2_PATHS["launch_template_catalog"].as_posix()
        or fixture["operator_presentation_catalog_path"]
        != PRODUCT_V2_PATHS["operator_presentation_catalog"].as_posix()
    ):
        raise ProductV2ValidationError("product_v2_fixture", "fixture identity mismatch")
    positives = _array(fixture["positive_cases"], "positive cases", "product_v2_fixture")
    expected_positive_ids = {
        "first_run_complete",
        "four_launch_templates_closed",
        "catalog_rendered_human_output",
        "closed_submission_and_promotion",
        "metrics_keep_unknown",
    }
    if {case.get("case_id") for case in positives if isinstance(case, dict)} != expected_positive_ids or any(case.get("expected_result") != "valid" for case in positives):
        raise ProductV2ValidationError("product_v2_fixture", "positive case set mismatch")
    negative_cases = _array(fixture["negative_mutations"], "negative mutations", "product_v2_fixture")
    registry = _mutation_registry()
    if {case.get("mutation") for case in negative_cases if isinstance(case, dict)} != set(registry):
        raise ProductV2ValidationError("product_v2_fixture", "negative mutation set mismatch")
    targets: dict[str, tuple[dict[str, Any], Callable[[Any], None]]] = {
        "launch_catalog": (launch_catalog, _validate_launch_catalog),
        "operator_presentation": (operator_catalog, _validate_operator_presentation),
        "first_run": (policy["payload"]["first_run_experience"], _validate_first_run),
        "product_policy": (
            policy,
            lambda candidate: _validate_product_policy(candidate, identities),
        ),
    }
    for raw_case in negative_cases:
        case = _exact(
            raw_case,
            {"case_id", "target", "mutation", "expected_reason"},
            "negative mutation",
            "product_v2_fixture",
        )
        mutation_entry = registry.get(case["mutation"])
        target_entry = targets.get(case["target"])
        if mutation_entry is None or target_entry is None:
            raise ProductV2ValidationError("product_v2_fixture", "unknown mutation or target")
        registry_reason, mutation = mutation_entry
        if case["expected_reason"] != registry_reason:
            raise ProductV2ValidationError("product_v2_fixture", "mutation reason mismatch")
        candidate = copy.deepcopy(target_entry[0])
        try:
            mutation(candidate)
            target_entry[1](candidate)
        except ProductV2ValidationError as exc:
            if exc.reason != case["expected_reason"]:
                raise ProductV2ValidationError(
                    "product_v2_fixture_reason",
                    f"{case['case_id']}: expected {case['expected_reason']}, got {exc.reason}",
                ) from exc
        else:
            raise ProductV2ValidationError(
                "product_v2_negative_accepted", str(case["case_id"])
            )
    return len(positives), len(negative_cases)


def verify_product_v2_bundle(repo_root: Path) -> dict[str, Any]:
    """Verify every v2 bundle member, cross-binding and negative fixture."""

    root = repo_root.resolve()
    policy, policy_raw = _load(root, "policy")
    first_run_schema, _ = _load(root, "first_run_schema")
    launch_catalog, _ = _load(root, "launch_template_catalog")
    operator_catalog, _ = _load(root, "operator_presentation_catalog")
    fixture, _ = _load(root, "fixture")
    _validate_first_run_schema(first_run_schema)
    payload = _validate_product_policy(policy, EXPECTED_PRODUCT_V2_IDENTITIES)
    _validate_launch_catalog(launch_catalog)
    _validate_operator_presentation(operator_catalog)
    positive_count, negative_count = _verify_fixture(
        fixture,
        policy,
        launch_catalog,
        operator_catalog,
        EXPECTED_PRODUCT_V2_IDENTITIES,
    )
    return {
        "artifact_version": payload["artifact_version"],
        "artifact_byte_count": len(policy_raw),
        "artifact_sha256": hashlib.sha256(policy_raw).hexdigest(),
        "first_run_step_count": len(payload["first_run_experience"]["journey"]),
        "launch_template_count": len(launch_catalog["templates"]),
        "operator_view_count": len(operator_catalog["status_views"]),
        "operator_reason_count": len(operator_catalog["reason_messages"]),
        "product_metric_count": len(payload["product_metrics"]["metrics"]),
        "positive_fixture_count": positive_count,
        "negative_fixture_count": negative_count,
        "bundle_identities": copy.deepcopy(EXPECTED_PRODUCT_V2_IDENTITIES),
    }
