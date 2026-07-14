from __future__ import annotations

import copy
import json
from pathlib import Path
import runpy
import subprocess
import sys
from typing import Callable

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
VERIFIER_PATH = REPO_ROOT / "scripts" / "verify-local-ai-runtime-baseline.py"
GIT_ROOT = REPO_ROOT / "docs" / "specs" / "local-ai-runtime-0.2"
POLICY_PATH = GIT_ROOT / "normative" / "DeterministicGitContractSet.v1.json"
OBJECT_SET_SCHEMA_PATH = GIT_ROOT / "schemas" / "ObjectSetManifest.v1.schema.json"
CONFIG_CATALOG_PATH = GIT_ROOT / "catalogs" / "GitConfigPolicy.v1.json"
FIXTURE_PATH = GIT_ROOT / "fixtures" / "git" / "manifest.json"


def _run_component(repo_root: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VERIFIER_PATH),
            "--repo-root",
            str(repo_root),
            "--component",
            "deterministic-git",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _copy_bundle(tmp_path: Path) -> None:
    for source in (
        POLICY_PATH,
        OBJECT_SET_SCHEMA_PATH,
        CONFIG_CATALOG_PATH,
        FIXTURE_PATH,
    ):
        target = tmp_path / source.relative_to(REPO_ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


def test_deterministic_git_component_closes_declared_contracts() -> None:
    completed = _run_component()

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload == {
        "status": "pass",
        "component": "deterministic-git",
        "artifact_version": "DeterministicGitContractSet.v1",
        "artifact_byte_count": 7438,
        "artifact_sha256": (
            "c6ff21651cd525f1319fe0620f280e96db825086c2e8e98149340f4e08b11e26"
        ),
        "object_set_schema_sha256": (
            "7fd65d96d603dbad8940979c53ff2035ce0f27ae3e508b7f2da3621c0ef414a3"
        ),
        "config_catalog_sha256": (
            "a4598b05fe8432f3522f53bd7853d8acbdc8fc7859c4cd9b3cf54bd8cf4d9c65"
        ),
        "fixture_sha256": (
            "75a09c60ddeb38ce05a0aa5214790729a828822ab434a4dce8e9007a4a9ec1d3"
        ),
        "blob_oid": "ce013625030ba8dba906f756967f9e9ca394464a",
        "tree_oid": "853694aae8816094a0d875fee7ea26278dbf5d0f",
        "commit_oid": "df2a0ef979213e41593cfa9e40a913f5493ec95f",
        "plan_sha256": (
            "c58e841c2416c3751a467fdfa77b8c07d1f59d737237a0a471ad32039c2b1317"
        ),
        "set_sha256": (
            "f249104f6e33913da606191263f22f61da6b17867cbc5f9535dd8553e74dfc96"
        ),
        "fixture_counts": {
            "config": 9,
            "environment": 5,
            "claim": 4,
            "commit": 10,
            "object": 8,
            "create_worktree": 5,
            "finalize": 9,
            "task_ref": 10,
            "action_order": 5,
            "cleanup": 5,
        },
    }


@pytest.mark.parametrize(
    ("target_name", "mutation", "expected_reason"),
    [
        (
            "policy",
            lambda value: value["payload"]["cleanup"].__setitem__(
                "reset_hard_allowed", True
            ),
            "deterministic_git_policy_identity",
        ),
        (
            "object_set_schema",
            lambda value: value.__setitem__("additionalProperties", True),
            "deterministic_git_schema_drift",
        ),
        (
            "config_catalog",
            lambda value: value.__setitem__("default_action", "allow"),
            "git_config_catalog_drift",
        ),
        (
            "fixture",
            lambda value: value.__setitem__("task_ref_cases", None),
            "deterministic_git_fixture_drift",
        ),
    ],
)
def test_deterministic_git_component_fails_closed_on_bundle_drift(
    tmp_path: Path,
    target_name: str,
    mutation: Callable[[dict[str, object]], None],
    expected_reason: str,
) -> None:
    _copy_bundle(tmp_path)
    targets = {
        "policy": POLICY_PATH,
        "object_set_schema": OBJECT_SET_SCHEMA_PATH,
        "config_catalog": CONFIG_CATALOG_PATH,
        "fixture": FIXTURE_PATH,
    }
    target = tmp_path / targets[target_name].relative_to(REPO_ROOT)
    value = json.loads(target.read_text(encoding="utf-8"))
    mutation(value)
    target.write_text(
        json.dumps(value, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    namespace = runpy.run_path(str(VERIFIER_PATH))
    with pytest.raises(namespace["ValidationFailure"]) as captured:
        namespace["verify_deterministic_git_component"](tmp_path)
    assert captured.value.reason == expected_reason


def test_controller_object_framing_matches_pinned_git_without_writing() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    for entry in fixture["object_payloads"]:
        completed = subprocess.run(
            ["git", "hash-object", "-t", entry["object_type"], "--stdin"],
            cwd=REPO_ROOT,
            input=bytes.fromhex(entry["payload_hex"]),
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr.decode(errors="replace")
        assert completed.stdout.decode().strip() == entry["expected_oid"]


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    [
        (
            lambda value: value.__setitem__(
                "expected_git_object_plan_sha256", "0" * 64
            ),
            "git_plan_hash",
        ),
        (
            lambda value: value["object_set_manifest_positive"].__setitem__(
                "set_sha256", "0" * 64
            ),
            "object_set_hash",
        ),
        (
            lambda value: value["object_payloads"][2].__setitem__(
                "payload_hex", value["object_payloads"][2]["payload_hex"] + "0a"
            ),
            "git_object_fixture",
        ),
    ],
)
def test_git_object_bundle_rejects_plan_set_or_commit_drift(
    mutation: Callable[[dict[str, object]], None], expected_reason: str
) -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    mutation(fixture)
    namespace = runpy.run_path(str(VERIFIER_PATH))

    with pytest.raises(namespace["ValidationFailure"]) as captured:
        namespace["_validate_git_object_bundle"](fixture)
    assert captured.value.reason == expected_reason


def test_config_audit_never_reads_name_only_or_denied_values() -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    catalog_value = json.loads(CONFIG_CATALOG_PATH.read_text(encoding="utf-8"))
    catalog = namespace["_verify_git_config_catalog"](catalog_value)
    cases = {case["case_id"]: case for case in fixture["config_cases"]}

    assert namespace["_evaluate_git_config_case"](
        cases["remote_name_only"], catalog
    ) == "allow_name_only"
    assert namespace["_evaluate_git_config_case"](
        cases["remote_value_read"], catalog
    ) == "value_read_forbidden"
    assert namespace["_evaluate_git_config_case"](
        cases["include_value_read"], catalog
    ) == "value_read_forbidden"


def test_task_ref_response_loss_confirms_only_same_intent_and_oid() -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    cases = {case["case_id"]: case for case in fixture["task_ref_cases"]}

    assert namespace["_evaluate_task_ref"](
        cases["response_loss_same_intent"]
    ) == "confirm_historical_success"
    assert namespace["_evaluate_task_ref"](
        cases["response_loss_wrong_oid"]
    ) == "ref_collision_reject"


def test_publication_order_and_cleanup_are_closed() -> None:
    namespace = runpy.run_path(str(VERIFIER_PATH))
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    action_cases = {case["case_id"]: case for case in fixture["action_order_cases"]}
    cleanup_cases = {case["case_id"]: case for case in fixture["cleanup_cases"]}

    assert namespace["_evaluate_git_action_order"](
        action_cases["complete_order"]
    ) == "action_order_accepted"
    assert namespace["_evaluate_git_action_order"](
        action_cases["task_ref_before_head"]
    ) == "action_order_reject"
    assert namespace["_evaluate_git_cleanup"](
        cleanup_cases["reset_hard"]
    ) == "reset_hard_forbidden"
