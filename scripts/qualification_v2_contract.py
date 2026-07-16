"""Stdlib-only verifier for QualificationContractSet.v2 exact toolchain rules."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Callable


QUALIFICATION_V2_PATHS = {
    "policy": Path(
        "docs/specs/local-ai-runtime-0.2/normative/QualificationContractSet.v2.json"
    ),
    "toolchain_schema": Path(
        "docs/specs/local-ai-runtime-0.2/schemas/RuntimeToolchainManifest.v1.schema.json"
    ),
    "execution_profile": Path(
        "docs/specs/local-ai-runtime-0.2/catalogs/VerificationExecutionProfile.v1.json"
    ),
    "fixture": Path(
        "docs/specs/local-ai-runtime-0.2/fixtures/toolchain-v2/manifest.json"
    ),
}

ACTIVE_TOOLCHAIN_SURFACE_PATHS = (
    Path("AGENTS.md"),
    Path("README.md"),
    Path("docs/README.md"),
    Path("docs/architecture/orchestrator-target-architecture.md"),
    Path("docs/architecture/planning-status.json"),
    Path("docs/architecture/next-work-selection-policy.json"),
    Path("docs/backlog/orchestrator-task-list.md"),
    Path("docs/plans/local-ai-runtime-0.2-work-items.json"),
    Path("docs/plans/orchestrator-implementation-plan.md"),
    Path("docs/product/orchestrator-prd.md"),
    Path("docs/roadmap/orchestrator-roadmap.md"),
    Path("docs/specs/acceptance-and-gates.md"),
    Path("docs/specs/local-ai-runtime-0.2-baseline-candidate.md"),
    Path("docs/specs/local-ai-runtime-0.2-normative-package.json"),
)

EXPECTED_QUALIFICATION_V2_IDENTITIES = {
    "policy": {
        "byte_count": 7936,
        "sha256": "4c873185b2eb293c23099d616fb1e754ce073e89491200dcc4e4ac0bb6fc4dac",
    },
    "toolchain_schema": {
        "byte_count": 5314,
        "sha256": "96bfcba51d76d5539c3b37559ebd9e455d32482442442dc8add3ae86100e8a90",
    },
    "execution_profile": {
        "byte_count": 3392,
        "sha256": "9744a431f0dedf1fe5c3503d83535ac4902b8e064bd4175bcf2cf56f70365d49",
    },
    "fixture": {
        "byte_count": 7143,
        "sha256": "91004d7915f331ef94579c1e0b34f34bf178eee3efefc956440f2cd51369b50f",
    },
}

PREPARATION_COMMAND = (
    "& <uv.absolute_path> sync --locked --offline --no-python-downloads "
    "--python <python.absolute_path> --project runtime/local-ai-runtime"
)

EXPECTED_GATE_ORDER = [
    "supply_chain_identity",
    "build",
    "test",
    "contract_invariant",
    "hotspot",
]

EXPECTED_COMMANDS = {
    "supply_chain_identity": [
        "& <uv.absolute_path> lock --check --offline --no-python-downloads --python <python.absolute_path> --project runtime/local-ai-runtime",
        "& <python.absolute_path> -I -s -E -m local_ai_runtime toolchain verify-environment --profile new_runtime_exact_v1 --json",
    ],
    "build": [
        "& <uv.absolute_path> build --offline --no-python-downloads --python <python.absolute_path> --build-constraint <hashed_build_constraints.absolute_path> --require-hashes --project runtime/local-ai-runtime runtime/local-ai-runtime"
    ],
    "test": [
        "& <uv.absolute_path> run --no-sync --offline --no-python-downloads --python <python.absolute_path> --project runtime/local-ai-runtime python -I -s -E -m pytest"
    ],
    "contract_invariant": [
        "& <uv.absolute_path> run --no-sync --offline --no-python-downloads --python <python.absolute_path> --project runtime/local-ai-runtime python -I -s -E -m local_ai_runtime contracts verify",
        "python scripts/verify-planning-status.py",
        "python scripts/select-next-work.py",
    ],
    "hotspot": [
        "& <uv.absolute_path> run --no-sync --offline --no-python-downloads --python <python.absolute_path> --project runtime/local-ai-runtime ruff check runtime/local-ai-runtime",
        "& <uv.absolute_path> run --no-sync --offline --no-python-downloads --python <python.absolute_path> --project runtime/local-ai-runtime pyright --project runtime/local-ai-runtime",
        "git diff --check",
    ],
}

EXPECTED_PROHIBITED_FORMS = [
    "uv sync --exact",
    "uv sync --inexact",
    "uv run --locked --offline",
    "uv build --offline --project",
    "PATH python",
    "automatic Python download",
    "unconstrained cached build backend",
    "validation command that performs sync",
    "build without --require-hashes",
    "build without --build-constraint",
]

EXPECTED_NEGATIVE_MUTATIONS = {
    "add_extraneous_distribution": "toolchain_distribution_set",
    "add_extraneous_plugin": "toolchain_plugin_set",
    "change_python_patch": "toolchain_python_identity",
    "change_python_path": "toolchain_python_identity",
    "request_python_download": "toolchain_python_download",
    "add_unconstrained_backend": "toolchain_backend_set",
    "remove_backend_hash": "toolchain_build_hash",
    "change_member_manifest": "toolchain_repeatability",
    "change_artifact_hash": "toolchain_repeatability",
    "replace_no_sync_with_locked": "toolchain_validation_command",
    "remove_require_hashes": "toolchain_build_command",
    "remove_explicit_python": "toolchain_python_command",
}

SHA256 = re.compile(r"^[0-9a-f]{64}$")
PYTHON_VERSION = re.compile(r"^3\.11\.[0-9]+$")
WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:/[^\r\n]+$")


class QualificationV2ValidationError(RuntimeError):
    """Raised with a stable reason code for an exact-toolchain failure."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def _object(value: Any, label: str, reason: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise QualificationV2ValidationError(reason, f"{label} must be an object")
    return value


def _array(value: Any, label: str, reason: str) -> list[Any]:
    if not isinstance(value, list):
        raise QualificationV2ValidationError(reason, f"{label} must be an array")
    return value


def _exact(value: Any, fields: set[str], label: str, reason: str) -> dict[str, Any]:
    result = _object(value, label, reason)
    if set(result) != fields:
        raise QualificationV2ValidationError(reason, f"{label} fields mismatch")
    return result


def _hash(value: Any, reason: str, label: str) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise QualificationV2ValidationError(reason, f"{label} must be SHA-256")
    return value


def _load(root: Path, key: str) -> tuple[dict[str, Any], bytes]:
    path = root / QUALIFICATION_V2_PATHS[key]
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise QualificationV2ValidationError(
            "qualification_v2_json", f"cannot read {QUALIFICATION_V2_PATHS[key]}"
        ) from exc
    if not isinstance(value, dict):
        raise QualificationV2ValidationError(
            "qualification_v2_json", f"{QUALIFICATION_V2_PATHS[key]} must be an object"
        )
    identity = EXPECTED_QUALIFICATION_V2_IDENTITIES[key]
    if len(raw) != identity["byte_count"] or hashlib.sha256(raw).hexdigest() != identity["sha256"]:
        raise QualificationV2ValidationError(
            f"qualification_v2_{key}_identity",
            f"{QUALIFICATION_V2_PATHS[key]} identity mismatch",
        )
    return value, raw


def _validate_schema(schema: dict[str, Any]) -> None:
    if (
        schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
        or schema.get("title") != "RuntimeToolchainManifest.v1"
        or schema.get("type") != "object"
        or schema.get("additionalProperties") is not False
    ):
        raise QualificationV2ValidationError("toolchain_schema", "schema envelope mismatch")
    required = schema.get("required")
    properties = schema.get("properties")
    if not isinstance(required, list) or not isinstance(properties, dict) or set(required) != set(properties):
        raise QualificationV2ValidationError("toolchain_schema", "root field closure mismatch")
    for field in ("python", "uv", "lock", "environment", "build", "reproducibility"):
        child = _object(properties.get(field), f"{field} schema", "toolchain_schema")
        if child.get("additionalProperties") is not False:
            raise QualificationV2ValidationError("toolchain_schema", f"{field} is not closed")
    definitions = _object(schema.get("$defs"), "$defs", "toolchain_schema")
    for field in ("distribution", "plugin", "hashed_requirement"):
        if _object(definitions.get(field), field, "toolchain_schema").get("additionalProperties") is not False:
            raise QualificationV2ValidationError("toolchain_schema", f"{field} is not closed")


def _validate_distribution(value: Any, reason: str) -> tuple[str, str, str]:
    distribution = _exact(
        value,
        {"name", "version", "metadata_sha256"},
        "distribution",
        reason,
    )
    if not isinstance(distribution["name"], str) or not isinstance(distribution["version"], str):
        raise QualificationV2ValidationError(reason, "distribution identity is invalid")
    return (
        distribution["name"],
        distribution["version"],
        _hash(distribution["metadata_sha256"], reason, "distribution metadata"),
    )


def _validate_plugin(value: Any, reason: str) -> tuple[str, str, str, str]:
    plugin = _exact(
        value,
        {"entry_point", "distribution_name", "distribution_version", "metadata_sha256"},
        "pytest plugin",
        reason,
    )
    if not all(isinstance(plugin[field], str) for field in ("entry_point", "distribution_name", "distribution_version")):
        raise QualificationV2ValidationError(reason, "plugin identity is invalid")
    return (
        plugin["entry_point"],
        plugin["distribution_name"],
        plugin["distribution_version"],
        _hash(plugin["metadata_sha256"], reason, "plugin metadata"),
    )


def _validate_toolchain_manifest(value: Any) -> dict[str, Any]:
    manifest = _exact(
        value,
        {
            "schema_version",
            "manifest_id",
            "baseline_id",
            "python",
            "uv",
            "lock",
            "environment",
            "build",
            "reproducibility",
        },
        "RuntimeToolchainManifest",
        "toolchain_manifest",
    )
    if manifest["schema_version"] != 1 or manifest["baseline_id"] != "local-ai-runtime-0.2-v3.24" or not isinstance(manifest["manifest_id"], str):
        raise QualificationV2ValidationError("toolchain_manifest", "manifest identity mismatch")
    python = _exact(
        manifest["python"],
        {"absolute_path", "version", "file_identity_sha256", "file_sha256", "automatic_downloads"},
        "Python identity",
        "toolchain_python_identity",
    )
    if (
        not isinstance(python["absolute_path"], str)
        or WINDOWS_ABSOLUTE.fullmatch(python["absolute_path"]) is None
        or not isinstance(python["version"], str)
        or PYTHON_VERSION.fullmatch(python["version"]) is None
    ):
        raise QualificationV2ValidationError("toolchain_python_identity", "Python path or patch mismatch")
    _hash(python["file_identity_sha256"], "toolchain_python_identity", "Python file identity")
    _hash(python["file_sha256"], "toolchain_python_identity", "Python file hash")
    if python["automatic_downloads"] != "deny":
        raise QualificationV2ValidationError("toolchain_python_download", "automatic Python download is not denied")
    uv = _exact(
        manifest["uv"],
        {"absolute_path", "version", "file_identity_sha256", "file_sha256"},
        "uv identity",
        "toolchain_uv_identity",
    )
    if not isinstance(uv["absolute_path"], str) or WINDOWS_ABSOLUTE.fullmatch(uv["absolute_path"]) is None or not isinstance(uv["version"], str):
        raise QualificationV2ValidationError("toolchain_uv_identity", "uv path or version mismatch")
    _hash(uv["file_identity_sha256"], "toolchain_uv_identity", "uv file identity")
    _hash(uv["file_sha256"], "toolchain_uv_identity", "uv file hash")
    lock = _exact(
        manifest["lock"],
        {"project_path", "lock_path", "lock_sha256", "offline_cache_manifest_sha256"},
        "lock binding",
        "toolchain_lock",
    )
    if lock["project_path"] != "runtime/local-ai-runtime" or lock["lock_path"] != "runtime/local-ai-runtime/uv.lock":
        raise QualificationV2ValidationError("toolchain_lock", "lock path mismatch")
    _hash(lock["lock_sha256"], "toolchain_lock", "lock hash")
    _hash(lock["offline_cache_manifest_sha256"], "toolchain_lock", "cache manifest hash")
    environment = _exact(
        manifest["environment"],
        {"environment_root", "distribution_identities", "pytest_plugin_identities", "extraneous_policy"},
        "environment",
        "toolchain_environment",
    )
    if not isinstance(environment["environment_root"], str) or WINDOWS_ABSOLUTE.fullmatch(environment["environment_root"]) is None or environment["extraneous_policy"] != "exact_set_no_additions_no_missing":
        raise QualificationV2ValidationError("toolchain_environment", "environment binding mismatch")
    distributions = [
        _validate_distribution(item, "toolchain_distribution_set")
        for item in _array(environment["distribution_identities"], "distributions", "toolchain_distribution_set")
    ]
    plugins = [
        _validate_plugin(item, "toolchain_plugin_set")
        for item in _array(environment["pytest_plugin_identities"], "plugins", "toolchain_plugin_set")
    ]
    if not distributions or len(distributions) != len(set(distributions)) or len(plugins) != len(set(plugins)):
        raise QualificationV2ValidationError("toolchain_distribution_set", "duplicate or empty identity set")
    build = _exact(
        manifest["build"],
        {"frontend", "backend", "constraint_path", "constraint_sha256", "require_hashes", "backend_requirements"},
        "build identity",
        "toolchain_build_hash",
    )
    _validate_distribution(build["frontend"], "toolchain_build_hash")
    backend = _validate_distribution(build["backend"], "toolchain_build_hash")
    if not isinstance(build["constraint_path"], str) or WINDOWS_ABSOLUTE.fullmatch(build["constraint_path"]) is None or build["require_hashes"] is not True:
        raise QualificationV2ValidationError("toolchain_build_hash", "build constraints are incomplete")
    _hash(build["constraint_sha256"], "toolchain_build_hash", "build constraint")
    requirements: list[tuple[str, str, str]] = []
    for item in _array(build["backend_requirements"], "backend requirements", "toolchain_build_hash"):
        requirement = _exact(
            item,
            {"name", "version", "artifact_sha256"},
            "backend requirement",
            "toolchain_build_hash",
        )
        if not isinstance(requirement["name"], str) or not isinstance(requirement["version"], str):
            raise QualificationV2ValidationError("toolchain_build_hash", "backend identity invalid")
        requirements.append(
            (
                requirement["name"],
                requirement["version"],
                _hash(requirement["artifact_sha256"], "toolchain_build_hash", "backend artifact"),
            )
        )
    if not requirements or len(requirements) != len(set(requirements)) or backend[:2] not in {(item[0], item[1]) for item in requirements}:
        raise QualificationV2ValidationError("toolchain_build_hash", "backend requirement set mismatch")
    reproducibility = _exact(
        manifest["reproducibility"],
        {"source_date_epoch", "clean_root_count", "comparison_fields", "normalization_policy"},
        "reproducibility",
        "toolchain_repeatability",
    )
    if (
        type(reproducibility["source_date_epoch"]) is not int
        or reproducibility["source_date_epoch"] < 1
        or reproducibility["clean_root_count"] != 2
        or reproducibility["comparison_fields"]
        != ["normalized_member_manifest_sha256", "artifact_sha256"]
        or reproducibility["normalization_policy"]
        != "wheel_member_path_mode_size_content_hash_no_root_path_or_mtime"
    ):
        raise QualificationV2ValidationError("toolchain_repeatability", "reproducibility contract mismatch")
    return manifest


def _validate_profile(value: Any) -> dict[str, Any]:
    profile = _exact(
        value,
        {
            "catalog_version",
            "baseline_id",
            "profile_id",
            "profile_status",
            "environment_preparation",
            "environment_preparation_is_gate",
            "environment_preparation_semantics",
            "fixed_gate_order",
            "commands",
            "child_identity_readback",
            "build_contract",
            "reproducibility_contract",
            "prohibited_active_forms",
        },
        "VerificationExecutionProfile",
        "toolchain_profile",
    )
    if (
        profile["catalog_version"] != "VerificationExecutionProfile.v1"
        or profile["baseline_id"] != "local-ai-runtime-0.2-v3.24"
        or profile["profile_id"] != "new_runtime_exact_v1"
        or profile["profile_status"] != "normative_preimplementation_contract"
    ):
        raise QualificationV2ValidationError("toolchain_profile", "profile identity mismatch")
    if (
        profile["environment_preparation"] != [PREPARATION_COMMAND]
        or profile["environment_preparation_is_gate"] is not False
        or profile["environment_preparation_semantics"]
        != "uv_sync_default_exact_and_inexact_forbidden"
    ):
        raise QualificationV2ValidationError("toolchain_preparation_command", "preparation boundary mismatch")
    if profile["fixed_gate_order"] != EXPECTED_GATE_ORDER:
        raise QualificationV2ValidationError("toolchain_gate_order", "gate order mismatch")
    commands = _object(profile["commands"], "commands", "toolchain_validation_command")
    if set(commands) != set(EXPECTED_COMMANDS):
        raise QualificationV2ValidationError("toolchain_validation_command", "gate command set mismatch")
    for gate, expected in EXPECTED_COMMANDS.items():
        actual = _array(commands[gate], gate, "toolchain_validation_command")
        if actual != expected:
            if gate == "build" and any("--require-hashes" not in command or "--build-constraint" not in command for command in actual):
                raise QualificationV2ValidationError("toolchain_build_command", "build hashes missing")
            if any("<uv.absolute_path>" in command and "--python <python.absolute_path>" not in command for command in actual):
                raise QualificationV2ValidationError("toolchain_python_command", "explicit Python missing")
            raise QualificationV2ValidationError("toolchain_validation_command", f"{gate} command mismatch")
    for gate in ("test", "contract_invariant", "hotspot"):
        for command in commands[gate]:
            if "<uv.absolute_path> run" in command and "--no-sync" not in command:
                raise QualificationV2ValidationError("toolchain_validation_command", "validation may synchronize")
    build_command = commands["build"][0]
    if "--require-hashes" not in build_command or "--build-constraint" not in build_command:
        raise QualificationV2ValidationError("toolchain_build_command", "build hashes missing")
    for gate_commands in commands.values():
        for command in gate_commands:
            if "<uv.absolute_path>" in command and "--python <python.absolute_path>" not in command:
                raise QualificationV2ValidationError("toolchain_python_command", "explicit Python missing")
            if "<uv.absolute_path>" in command and "--no-python-downloads" not in command:
                raise QualificationV2ValidationError("toolchain_python_command", "download denial missing")
    if profile["prohibited_active_forms"] != EXPECTED_PROHIBITED_FORMS:
        raise QualificationV2ValidationError("toolchain_prohibited_forms", "prohibited form set mismatch")
    build_contract = _object(profile["build_contract"], "build contract", "toolchain_build_command")
    if not all(
        build_contract.get(field) is True
        for field in (
            "offline",
            "no_python_downloads",
            "explicit_python",
            "build_constraint_required",
            "require_hashes",
        )
    ) or build_contract.get("cached_backend_selection") != "exact_manifest_set_only":
        raise QualificationV2ValidationError("toolchain_build_command", "build contract mismatch")
    repeat = _object(profile["reproducibility_contract"], "reproducibility contract", "toolchain_repeatability")
    if repeat.get("clean_root_count") != 2 or repeat.get("compare") != ["normalized_member_manifest_sha256", "artifact_sha256"] or repeat.get("root_path_and_mtime_in_hash") is not False:
        raise QualificationV2ValidationError("toolchain_repeatability", "profile repeatability mismatch")
    return profile


def _validate_environment_observation(observation: Any, manifest: dict[str, Any]) -> None:
    value = _exact(
        observation,
        {
            "python_absolute_path",
            "python_version",
            "python_file_identity_sha256",
            "python_file_sha256",
            "automatic_download_requested",
            "distribution_identities",
            "pytest_plugin_identities",
            "build_backend_identities",
        },
        "environment observation",
        "toolchain_environment_observation",
    )
    python = manifest["python"]
    if (
        value["python_absolute_path"] != python["absolute_path"]
        or value["python_version"] != python["version"]
        or value["python_file_identity_sha256"] != python["file_identity_sha256"]
        or value["python_file_sha256"] != python["file_sha256"]
    ):
        raise QualificationV2ValidationError("toolchain_python_identity", "Python observation mismatch")
    if value["automatic_download_requested"] is not False:
        raise QualificationV2ValidationError("toolchain_python_download", "Python download requested")
    expected_distributions = {
        _validate_distribution(item, "toolchain_distribution_set")
        for item in manifest["environment"]["distribution_identities"]
    }
    actual_distributions = {
        _validate_distribution(item, "toolchain_distribution_set")
        for item in _array(value["distribution_identities"], "observed distributions", "toolchain_distribution_set")
    }
    if actual_distributions != expected_distributions:
        raise QualificationV2ValidationError("toolchain_distribution_set", "distribution set mismatch")
    expected_plugins = {
        _validate_plugin(item, "toolchain_plugin_set")
        for item in manifest["environment"]["pytest_plugin_identities"]
    }
    actual_plugins = {
        _validate_plugin(item, "toolchain_plugin_set")
        for item in _array(value["pytest_plugin_identities"], "observed plugins", "toolchain_plugin_set")
    }
    if actual_plugins != expected_plugins:
        raise QualificationV2ValidationError("toolchain_plugin_set", "pytest plugin set mismatch")
    expected_backends = {
        (item["name"], item["version"], item["artifact_sha256"])
        for item in manifest["build"]["backend_requirements"]
    }
    actual_backends: set[tuple[str, str, str]] = set()
    for raw in _array(value["build_backend_identities"], "observed backends", "toolchain_backend_set"):
        backend = _exact(raw, {"name", "version", "artifact_sha256"}, "observed backend", "toolchain_backend_set")
        actual_backends.add((backend["name"], backend["version"], _hash(backend["artifact_sha256"], "toolchain_backend_set", "backend hash")))
    if actual_backends != expected_backends:
        raise QualificationV2ValidationError("toolchain_backend_set", "backend set mismatch")


def _validate_repeat_build(value: Any, manifest: dict[str, Any]) -> None:
    repeat = _exact(
        value,
        {"source_date_epoch", "roots"},
        "repeat build",
        "toolchain_repeatability",
    )
    if repeat["source_date_epoch"] != manifest["reproducibility"]["source_date_epoch"]:
        raise QualificationV2ValidationError("toolchain_repeatability", "SOURCE_DATE_EPOCH mismatch")
    roots = _array(repeat["roots"], "clean roots", "toolchain_repeatability")
    if len(roots) != 2:
        raise QualificationV2ValidationError("toolchain_repeatability", "exactly two clean roots required")
    identities: list[tuple[str, str]] = []
    root_ids: list[str] = []
    for raw in roots:
        root = _exact(
            raw,
            {"root_id", "normalized_member_manifest_sha256", "artifact_sha256"},
            "clean root result",
            "toolchain_repeatability",
        )
        root_ids.append(root["root_id"])
        identities.append(
            (
                _hash(root["normalized_member_manifest_sha256"], "toolchain_repeatability", "member manifest"),
                _hash(root["artifact_sha256"], "toolchain_repeatability", "artifact"),
            )
        )
    if len(set(root_ids)) != 2 or identities[0] != identities[1]:
        raise QualificationV2ValidationError("toolchain_repeatability", "clean-root build mismatch")


def _validate_policy(value: Any) -> dict[str, Any]:
    envelope = _exact(value, {"domain", "schema_version", "payload"}, "QualificationContractSet.v2", "qualification_v2_policy")
    if envelope["domain"] != "local-ai-runtime/QualificationContractSet/v2" or envelope["schema_version"] != 2:
        raise QualificationV2ValidationError("qualification_v2_policy", "policy envelope mismatch")
    payload = _exact(
        envelope["payload"],
        {
            "artifact_id",
            "artifact_version",
            "baseline_id",
            "predecessor_binding",
            "bundle_bindings",
            "qualification_scope",
            "inherited_v1_contracts",
            "runtime_toolchain_manifest",
            "environment_preparation",
            "verification_profile",
            "environment_identity_readback",
            "build_supply_chain",
            "reproducibility",
            "active_surface_rejection",
            "fixture_requirements",
        },
        "QualificationContractSet.v2 payload",
        "qualification_v2_policy",
    )
    if payload["artifact_id"] != "P0A-QUALIFICATION" or payload["artifact_version"] != "QualificationContractSet.v2" or payload["baseline_id"] != "local-ai-runtime-0.2-v3.24":
        raise QualificationV2ValidationError("qualification_v2_policy", "artifact binding mismatch")
    predecessor = payload["predecessor_binding"]
    if predecessor != {
        "artifact_version": "QualificationContractSet.v1",
        "path": "docs/specs/local-ai-runtime-0.2/normative/QualificationContractSet.v1.json",
        "byte_count": 7336,
        "sha256": "089a60664188fdc86c0de56496c493339246c5b423ddc3271450fb01e4fd6a80",
        "disposition": "immutable_compatible_predecessor_extended_by_exact_toolchain_v2",
    }:
        raise QualificationV2ValidationError("qualification_v2_policy", "predecessor binding mismatch")
    expected_bindings = {
        "runtime_toolchain_manifest_schema": "toolchain_schema",
        "verification_execution_profile": "execution_profile",
        "fixture_manifest": "fixture",
    }
    bindings = _object(payload["bundle_bindings"], "bundle bindings", "qualification_v2_binding")
    if set(bindings) != set(expected_bindings):
        raise QualificationV2ValidationError("qualification_v2_binding", "binding set mismatch")
    for binding, identity_key in expected_bindings.items():
        identity = EXPECTED_QUALIFICATION_V2_IDENTITIES[identity_key]
        if bindings[binding] != {
            "path": QUALIFICATION_V2_PATHS[identity_key].as_posix(),
            "byte_count": identity["byte_count"],
            "sha256": identity["sha256"],
        }:
            raise QualificationV2ValidationError("qualification_v2_binding", f"{binding} mismatch")
    scope = _object(payload["qualification_scope"], "qualification scope", "qualification_v2_scope")
    if (
        scope.get("mode") != "preimplementation_contract_only"
        or scope.get("live_environment_preparation_performed") is not False
        or scope.get("network_allowed") is not False
        or scope.get("python_or_dependency_download_allowed") is not False
        or scope.get("runtime_package_required") is not False
    ):
        raise QualificationV2ValidationError("qualification_v2_scope", "preimplementation boundary mismatch")
    preparation = _object(payload["environment_preparation"], "environment preparation", "toolchain_preparation_command")
    if (
        preparation.get("command") != PREPARATION_COMMAND
        or preparation.get("classification")
        != "explicit_preparation_not_validation_gate"
        or preparation.get("hidden_sync_in_validation") != "deny"
        or preparation.get("exactness_semantics")
        != "uv_sync_default_exact_and_inexact_forbidden"
        or preparation.get("frozen_candidate_command_correction")
        != {
            "source": "uv sync --exact",
            "replacement": "uv sync",
            "classification": "non_semantic_cli_spelling_correction",
            "reason": "uv_sync_is_exact_by_default_and_does_not_accept_an_exact_option",
            "authority": "QualificationContractSet.v2_and_VerificationExecutionProfile.v1",
        }
    ):
        raise QualificationV2ValidationError("toolchain_preparation_command", "preparation policy mismatch")
    profile = _object(payload["verification_profile"], "profile binding", "toolchain_profile")
    if profile.get("profile_id") != "new_runtime_exact_v1" or profile.get("fixed_gate_order") != EXPECTED_GATE_ORDER or profile.get("validation_environment_mode") != "no_sync" or profile.get("no_python_downloads") is not True or profile.get("explicit_python_on_uv_commands") is not True:
        raise QualificationV2ValidationError("toolchain_profile", "profile policy mismatch")
    build = _object(payload["build_supply_chain"], "build supply chain", "toolchain_build_command")
    if build.get("command_requires") != ["--offline", "--no-python-downloads", "--python", "--build-constraint", "--require-hashes", "--project"] or build.get("cached_backend_policy") != "only_exact_manifest_set_may_be_selected":
        raise QualificationV2ValidationError("toolchain_build_command", "build supply-chain policy mismatch")
    repeat = _object(payload["reproducibility"], "reproducibility", "toolchain_repeatability")
    if repeat.get("clean_root_count") != 2 or repeat.get("required_equalities") != ["normalized_member_manifest_sha256", "artifact_sha256"] or set(repeat.get("excluded_fields", [])) != {"absolute_root_path", "filesystem_mtime", "build_start_time", "random_temp_path"}:
        raise QualificationV2ValidationError("toolchain_repeatability", "reproducibility policy mismatch")
    rejection = _object(payload["active_surface_rejection"], "active surface rejection", "toolchain_prohibited_forms")
    if (
        rejection.get("prohibited_forms") != EXPECTED_PROHIBITED_FORMS
        or rejection.get("historical_and_negative_fixture_exception") is not True
        or rejection.get("frozen_candidate_cli_spelling_exception")
        != "only_the_frozen_v3_24_source_excerpt_bound_by_environment_preparation.frozen_candidate_command_correction"
    ):
        raise QualificationV2ValidationError("toolchain_prohibited_forms", "prohibited form policy mismatch")
    fixtures = _object(payload["fixture_requirements"], "fixture requirements", "qualification_v2_fixture")
    if set(fixtures.get("negative", [])) != {
        "extraneous_distribution",
        "extraneous_pytest_plugin",
        "wrong_python_patch",
        "wrong_python_executable",
        "python_download_request",
        "multi_backend_cache",
        "missing_backend_hash",
        "repeat_member_mismatch",
        "repeat_artifact_mismatch",
        "hidden_sync_in_validation",
        "build_without_require_hashes",
        "path_python_fallback",
    } or fixtures.get("all_negative_must_fail") is not True:
        raise QualificationV2ValidationError("qualification_v2_fixture", "negative fixture policy mismatch")
    return payload


def _mutation_registry() -> dict[str, Callable[[dict[str, Any]], None]]:
    return {
        "add_extraneous_distribution": lambda value: value["distribution_identities"].append(
            {"name": "extra", "version": "1.0.0", "metadata_sha256": "0" * 64}
        ),
        "add_extraneous_plugin": lambda value: value["pytest_plugin_identities"].append(
            {"entry_point": "extra", "distribution_name": "extra", "distribution_version": "1.0.0", "metadata_sha256": "0" * 64}
        ),
        "change_python_patch": lambda value: value.__setitem__("python_version", "3.11.8"),
        "change_python_path": lambda value: value.__setitem__("python_absolute_path", "C:/Other/python.exe"),
        "request_python_download": lambda value: value.__setitem__("automatic_download_requested", True),
        "add_unconstrained_backend": lambda value: value["build_backend_identities"].append(
            {"name": "setuptools", "version": "75.0.0", "artifact_sha256": "0" * 64}
        ),
        "remove_backend_hash": lambda value: value["build"]["backend_requirements"][0].pop("artifact_sha256"),
        "change_member_manifest": lambda value: value["roots"][1].__setitem__("normalized_member_manifest_sha256", "0" * 64),
        "change_artifact_hash": lambda value: value["roots"][1].__setitem__("artifact_sha256", "0" * 64),
        "replace_no_sync_with_locked": lambda value: value["commands"]["test"].__setitem__(0, value["commands"]["test"][0].replace("--no-sync", "--locked")),
        "remove_require_hashes": lambda value: value["commands"]["build"].__setitem__(0, value["commands"]["build"][0].replace(" --require-hashes", "")),
        "remove_explicit_python": lambda value: value["commands"]["build"].__setitem__(0, value["commands"]["build"][0].replace(" --python <python.absolute_path>", "")),
    }


def _verify_fixture(
    fixture: dict[str, Any],
    manifest: dict[str, Any],
    profile: dict[str, Any],
) -> int:
    fixture = _exact(
        fixture,
        {
            "fixture_id",
            "schema_version",
            "baseline_id",
            "policy_path",
            "legacy_policy_path",
            "toolchain_schema_path",
            "execution_profile_path",
            "runtime_toolchain_manifest_positive",
            "environment_observation_positive",
            "repeat_build_positive",
            "negative_mutations",
        },
        "toolchain-v2 fixture",
        "qualification_v2_fixture",
    )
    if (
        fixture["fixture_id"] != "QualificationContractSet.v2.toolchain-fixtures"
        or fixture["schema_version"] != 2
        or fixture["baseline_id"] != "local-ai-runtime-0.2-v3.24"
        or fixture["policy_path"] != QUALIFICATION_V2_PATHS["policy"].as_posix()
        or fixture["toolchain_schema_path"] != QUALIFICATION_V2_PATHS["toolchain_schema"].as_posix()
        or fixture["execution_profile_path"] != QUALIFICATION_V2_PATHS["execution_profile"].as_posix()
    ):
        raise QualificationV2ValidationError("qualification_v2_fixture", "fixture identity mismatch")
    _validate_environment_observation(fixture["environment_observation_positive"], manifest)
    _validate_repeat_build(fixture["repeat_build_positive"], manifest)
    negatives = _array(fixture["negative_mutations"], "negative mutations", "qualification_v2_fixture")
    registry = _mutation_registry()
    if {case.get("mutation") for case in negatives if isinstance(case, dict)} != set(registry):
        raise QualificationV2ValidationError("qualification_v2_fixture", "negative mutation set mismatch")
    target_registry: dict[str, tuple[dict[str, Any], Callable[[dict[str, Any]], None]]] = {
        "environment": (
            fixture["environment_observation_positive"],
            lambda value: _validate_environment_observation(value, manifest),
        ),
        "manifest": (fixture["runtime_toolchain_manifest_positive"], _validate_toolchain_manifest),
        "repeat_build": (
            fixture["repeat_build_positive"],
            lambda value: _validate_repeat_build(value, manifest),
        ),
        "profile": (profile, _validate_profile),
    }
    for raw_case in negatives:
        case = _exact(
            raw_case,
            {"case_id", "target", "mutation", "expected_reason"},
            "negative mutation",
            "qualification_v2_fixture",
        )
        if case["expected_reason"] != EXPECTED_NEGATIVE_MUTATIONS.get(case["mutation"]):
            raise QualificationV2ValidationError("qualification_v2_fixture", "negative reason mismatch")
        target = target_registry.get(case["target"])
        mutation = registry.get(case["mutation"])
        if target is None or mutation is None:
            raise QualificationV2ValidationError("qualification_v2_fixture", "unknown mutation target")
        candidate = copy.deepcopy(target[0])
        try:
            mutation(candidate)
            target[1](candidate)
        except QualificationV2ValidationError as exc:
            if exc.reason != case["expected_reason"]:
                raise QualificationV2ValidationError(
                    "qualification_v2_fixture_reason",
                    f"{case['case_id']}: expected {case['expected_reason']}, got {exc.reason}",
                ) from exc
        else:
            raise QualificationV2ValidationError(
                "qualification_v2_negative_accepted", str(case["case_id"])
            )
    return len(negatives)


def _verify_active_toolchain_surfaces(root: Path) -> int:
    """Reject unsupported sync command forms outside the frozen source exception."""

    for relative_path in ACTIVE_TOOLCHAIN_SURFACE_PATHS:
        path = root / relative_path
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise QualificationV2ValidationError(
                "toolchain_active_surface_read",
                f"cannot read active toolchain surface {relative_path.as_posix()}",
            ) from exc
        for prohibited in ("uv sync --exact", "uv sync --inexact"):
            if prohibited in text:
                raise QualificationV2ValidationError(
                    "toolchain_prohibited_active_surface",
                    f"{relative_path.as_posix()} contains {prohibited}",
                )
    return len(ACTIVE_TOOLCHAIN_SURFACE_PATHS)


def verify_qualification_v2_bundle(repo_root: Path) -> dict[str, Any]:
    """Verify the v2 policy, schema, profile and all offline fixtures."""

    root = repo_root.resolve()
    policy, policy_raw = _load(root, "policy")
    schema, _ = _load(root, "toolchain_schema")
    profile, _ = _load(root, "execution_profile")
    fixture, _ = _load(root, "fixture")
    _validate_schema(schema)
    payload = _validate_policy(policy)
    checked_profile = _validate_profile(profile)
    manifest = _validate_toolchain_manifest(fixture.get("runtime_toolchain_manifest_positive"))
    negative_count = _verify_fixture(fixture, manifest, checked_profile)
    active_surface_count = _verify_active_toolchain_surfaces(root)
    return {
        "artifact_version": payload["artifact_version"],
        "artifact_byte_count": len(policy_raw),
        "artifact_sha256": hashlib.sha256(policy_raw).hexdigest(),
        "profile_id": checked_profile["profile_id"],
        "fixed_gate_order": copy.deepcopy(checked_profile["fixed_gate_order"]),
        "preparation_command_count": len(checked_profile["environment_preparation"]),
        "validation_command_count": sum(len(commands) for commands in checked_profile["commands"].values()),
        "distribution_count": len(manifest["environment"]["distribution_identities"]),
        "pytest_plugin_count": len(manifest["environment"]["pytest_plugin_identities"]),
        "backend_requirement_count": len(manifest["build"]["backend_requirements"]),
        "negative_fixture_count": negative_count,
        "active_surface_count": active_surface_count,
        "bundle_identities": copy.deepcopy(EXPECTED_QUALIFICATION_V2_IDENTITIES),
    }
