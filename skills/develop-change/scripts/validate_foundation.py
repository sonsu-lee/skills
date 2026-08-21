#!/usr/bin/env python3
"""Validate Phase 1 contract-foundation schema, fixtures, and isolated leaf packaging."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime_projection import (
    ProjectionError,
    query_effective_skill_catalog,
    query_installed_plugin_inventory,
    snapshot_codex_executable_identity,
    snapshot_effective_skill_catalog,
    snapshot_installed_plugin_inventory,
    snapshot_projection,
)

SCHEMA_VERSION = "phase1-foundation-draft-v1"
VALIDATOR_ID = "phase1-contract-foundation-validator"
VALIDATOR_REVISION = 4
ISOLATED_MARKETPLACE = "phase1-leaf-only-marketplace"
ISOLATED_PLUGIN = "phase1-leaf-only-fixture"
CONTRACT_ARTIFACTS = (
    "authorization-contract.md",
    "foundation-contract.schema.json",
    "gate-contract.md",
    "routing-contract.md",
)

ROUTES = {
    "understand", "shape", "decide", "design", "diagnose", "change",
    "verify", "deliver", "operate", "evolve",
}
AXES = {
    "domain_rule", "public_contract", "trust_boundary", "runtime_dependency",
    "multi_system_owner", "data_transition", "operational_blast_radius",
}
DIRECT_CONDITIONS = {
    "exact_outcome", "no_unresolved_architectural_axis",
    "single_local_effect_boundary", "mechanical_existing_semantics",
    "simple_local_revert", "narrow_immediate_validation",
    "no_rollout_migration_or_operations",
}
PER_TASK_CAPABILITIES = {
    "local_change", "working_artifact_write", "temporary_work_state",
    "workspace_cleanup", "durable_document_write", "durable_document_content",
    "branch_create", "branch_switch", "stage", "commit", "push", "pr_create", "merge", "rebase",
    "history_rewrite", "destructive_local", "external_write", "scope_expansion",
}
HISTORICAL_STATES = {"stale", "superseded"}
SAFE_DEFAULT_IDS = {
    "within_authorized_scope", "observable_result_unchanged",
    "persistent_semantics_unchanged", "no_external_or_destructive_effect",
    "simple_local_revert", "supported_by_project_evidence",
    "detectable_by_current_validation",
}


@dataclass(frozen=True)
class Finding:
    rule_id: str
    location: str
    message: str


class LeafProbeInvariantError(ValueError):
    """A completed isolated observation disproved a required leaf invariant."""

    def __init__(self, rule_id: str, message: str) -> None:
        super().__init__(message)
        self.rule_id = rule_id


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def emit_report(payload: dict[str, Any], output: str | None) -> None:
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output is None:
        print(serialized, end="")
        return
    destination = Path(output)
    if not destination.parent.is_dir():
        raise ValueError("report output parent directory does not exist")
    destination.write_text(serialized, encoding="utf-8")


def run_json_command(command: list[str], *, cwd: Path) -> tuple[int, dict[str, Any]]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "FND-DEVELOP-SKILL-001: validator did not emit JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError("FND-DEVELOP-SKILL-001: validator JSON must be an object")
    return completed.returncode, payload


def validate_develop_skill(repo: Path) -> dict[str, Any]:
    """Exercise strict metadata, scaffolding, regressions, and catalog validation."""
    skill_root = repo / "skills/develop-skill"
    validator = skill_root / "scripts/validate_skill.py"
    scaffold = skill_root / "scripts/scaffold_skill.py"
    case_catalog = json.loads((skill_root / "evals/cases.json").read_text())
    regressions = case_catalog.get("validator_regressions")
    if not isinstance(regressions, list) or not regressions:
        raise ValueError(
            "FND-DEVELOP-SKILL-001: validator_regressions must be a non-empty array"
        )

    results: list[dict[str, Any]] = []

    strict_exit, strict_payload = run_json_command(
        [
            sys.executable,
            str(validator),
            str(skill_root),
            "--require-explicit-invocation-policy",
            "--json",
        ],
        cwd=repo,
    )
    results.append(
        {
            "id": "develop-skill-strict-self",
            "passed": strict_exit == 0 and strict_payload.get("valid") is True,
        }
    )

    catalog_results: list[dict[str, Any]] = []
    for skill_file in sorted((repo / "skills").glob("*/SKILL.md")):
        exit_code, payload = run_json_command(
            [sys.executable, str(validator), str(skill_file.parent), "--json"],
            cwd=repo,
        )
        catalog_results.append(
            {
                "skill_id": skill_file.parent.name,
                "passed": exit_code == 0 and payload.get("valid") is True,
            }
        )

    with tempfile.TemporaryDirectory(prefix="phase1-develop-skill-") as temporary:
        temporary_root = Path(temporary)
        scaffolded = subprocess.run(
            [
                sys.executable,
                str(scaffold),
                "audit-skill",
                "--path",
                str(temporary_root),
                "--description",
                "반복 감사 작업을 한 가지 검증 가능한 흐름으로 수행해야 할 때 사용한다.",
                "--title",
                "감사 스킬",
                "--short-description",
                "감사 스킬의 반복 작업을 정확하고 안전하게 수행하도록 안내",
                "--default-prompt",
                "$audit-skill을 사용해 대표 작업을 수행하고 결과를 검증해줘.",
                "--allow-implicit-invocation",
                "false",
            ],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
        )
        scaffolded_skill = temporary_root / "audit-skill" / "SKILL.md"
        if scaffolded.returncode == 0 and scaffolded_skill.is_file():
            scaffolded_skill.write_text(
                scaffolded_skill.read_text(encoding="utf-8").replace(
                    "TODO: 품질 기준, 핵심 워크플로와 확인 가능한 완료 조건을 작성한다.",
                    "대표 입력을 확인하고 감사 작업을 수행한 뒤 결과와 근거를 검증한다.",
                ),
                encoding="utf-8",
            )
        scaffold_exit, scaffold_payload = run_json_command(
            [
                sys.executable,
                str(validator),
                str(temporary_root / "audit-skill"),
                "--require-explicit-invocation-policy",
                "--json",
            ],
            cwd=repo,
        )
        results.append(
            {
                "id": "scaffold-to-strict-validator",
                "passed": (
                    scaffolded.returncode == 0
                    and scaffold_exit == 0
                    and scaffold_payload.get("valid") is True
                ),
            }
        )

        regression_results: list[dict[str, Any]] = []
        fixture_root = temporary_root / "regression" / "audit-skill"
        (fixture_root / "agents").mkdir(parents=True)
        (fixture_root / "SKILL.md").write_text(
            "---\n"
            "name: audit-skill\n"
            "description: 반복 감사 작업을 한 가지 검증 가능한 흐름으로 수행해야 할 때 사용한다.\n"
            "---\n\n"
            "# 감사 스킬\n\n대표 작업을 수행하고 결과를 검증한다.\n",
            encoding="utf-8",
        )
        for case in regressions:
            if not isinstance(case, dict):
                raise ValueError(
                    "FND-DEVELOP-SKILL-001: validator regression case must be an object"
                )
            (fixture_root / "agents/openai.yaml").write_text(
                str(case.get("openai_yaml", "")), encoding="utf-8"
            )
            exit_code, payload = run_json_command(
                [
                    sys.executable,
                    str(validator),
                    str(fixture_root),
                    "--require-explicit-invocation-policy",
                    "--json",
                ],
                cwd=repo,
            )
            errors = [
                finding.get("message")
                for finding in payload.get("errors", [])
                if isinstance(finding, dict)
            ]
            expected_error = case.get("expected_error")
            passed = (
                exit_code == case.get("expected_exit")
                and (
                    expected_error is None
                    or expected_error in errors
                )
            )
            regression_results.append({"id": case.get("id"), "passed": passed})

    results.extend(regression_results)
    passed = all(result["passed"] for result in results) and all(
        result["passed"] for result in catalog_results
    )
    return {
        "status": "pass" if passed else "fail",
        "passed_count": sum(result["passed"] for result in results),
        "case_count": len(results),
        "results": results,
        "catalog_validation": {
            "passed_count": sum(result["passed"] for result in catalog_results),
            "skill_count": len(catalog_results),
            "results": catalog_results,
        },
    }


RECORD_DIGEST_DOMAINS = {
    "routing": b"phase1-foundation-routing-record-v1\n",
    "gate": b"phase1-foundation-gate-record-v1\n",
    "authorization": b"phase1-foundation-authorization-record-v1\n",
    "frontier_unit": b"phase1-foundation-frontier-unit-record-v1\n",
}


def record_digest_payload(value: Any) -> Any:
    """Remove only nested identity-reference digests to avoid reference cycles."""
    if isinstance(value, list):
        return [record_digest_payload(item) for item in value]
    if isinstance(value, dict):
        identity_ref = set(value) == {"id", "revision", "digest"}
        return {
            key: record_digest_payload(item)
            for key, item in value.items()
            if not (identity_ref and key == "digest")
        }
    return value


def canonical_record_digest(kind: str, record: dict[str, Any]) -> str:
    return hashlib.sha256(
        RECORD_DIGEST_DOMAINS[kind] + canonical_bytes(record_digest_payload(record))
    ).hexdigest()


def identity_ref_matches(
    reference: object,
    target: dict[str, Any] | None,
    *,
    kind: str,
    id_field: str,
) -> bool:
    return bool(
        isinstance(reference, dict)
        and isinstance(target, dict)
        and reference.get("id") == target.get(id_field)
        and reference.get("revision") == target.get("revision")
        and reference.get("digest") == canonical_record_digest(kind, target)
    )


def clarification_view_digest(view: dict[str, Any]) -> str:
    payload = {key: value for key, value in view.items() if key != "view_digest"}
    return hashlib.sha256(
        b"phase1-clarification-view-v1\n" + canonical_bytes(payload)
    ).hexdigest()


def bind_fixture_identity_digests(instance: dict[str, Any]) -> None:
    """Materialize canonical refs after a fixture's semantic mutations."""
    routing = instance.get("routing", {})
    gate = instance.get("gate", {})
    authorizations = instance.get("authorizations", [])
    authorization_by_id = {
        record.get("authorization_id"): record for record in authorizations
    }
    units = instance.get("frontier", {}).get("units", [])
    unit_by_identity = {
        (unit.get("unit_id"), unit.get("revision")): unit for unit in units
    }

    gate_ref = routing.get("gate_ref")
    if isinstance(gate_ref, dict):
        gate_ref["digest"] = canonical_record_digest("gate", gate)
    routing_ref = gate.get("routing_ref")
    if isinstance(routing_ref, dict):
        routing_ref["digest"] = canonical_record_digest("routing", routing)
    authorization_ref = routing.get("authorization_ref")
    if isinstance(authorization_ref, dict):
        target = authorization_by_id.get(authorization_ref.get("id"))
        if target is not None:
            authorization_ref["digest"] = canonical_record_digest(
                "authorization", target
            )
    for record in authorizations:
        reference = record.get("predecessor_authorization_ref")
        if isinstance(reference, dict):
            target = authorization_by_id.get(reference.get("id"))
            if target is not None:
                reference["digest"] = canonical_record_digest(
                    "authorization", target
                )
    for unit in units:
        for field in ("predecessor_unit_ref", "successor_unit_ref"):
            reference = unit.get(field)
            if isinstance(reference, dict):
                target = unit_by_identity.get(
                    (reference.get("id"), reference.get("revision"))
                )
                if target is not None:
                    reference["digest"] = canonical_record_digest(
                        "frontier_unit", target
                    )

    frontier = instance.get("frontier", {})
    view_records = list(frontier.get("clarification_view_history", []))
    current_view = frontier.get("clarification_view")
    if isinstance(current_view, dict):
        view_records.append(current_view)
    view_by_identity = {
        (view.get("round_id"), view.get("revision")): view
        for view in view_records
    }
    unresolved = list(view_records)
    while unresolved:
        progressed = False
        for view in list(unresolved):
            reference = view.get("predecessor_view_ref")
            if reference is None:
                view["view_digest"] = clarification_view_digest(view)
            elif isinstance(reference, dict):
                predecessor = view_by_identity.get(
                    (reference.get("id"), reference.get("revision"))
                )
                if predecessor is None or predecessor in unresolved:
                    continue
                reference["digest"] = predecessor.get("view_digest")
                view["view_digest"] = clarification_view_digest(view)
            else:
                continue
            unresolved.remove(view)
            progressed = True
        if not progressed:
            break


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add(findings: list[Finding], rule: str, location: str, message: str) -> None:
    item = Finding(rule, location, message)
    if item not in findings:
        findings.append(item)


def decode_pointer(pointer: str) -> list[str]:
    if not pointer.startswith("/"):
        raise ValueError(f"invalid JSON pointer: {pointer}")
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]


def apply_mutations(base: dict[str, Any], mutations: list[dict[str, Any]]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for mutation in mutations:
        parts = decode_pointer(mutation["path"])
        parent: Any = result
        for part in parts[:-1]:
            parent = parent[int(part)] if isinstance(parent, list) else parent[part]
        key = parts[-1]
        op = mutation["op"]
        if op in {"add", "replace"}:
            if isinstance(parent, list):
                if op == "add" and key == "-":
                    parent.append(copy.deepcopy(mutation["value"]))
                else:
                    parent[int(key)] = copy.deepcopy(mutation["value"])
            else:
                parent[key] = copy.deepcopy(mutation["value"])
        elif op == "remove":
            if isinstance(parent, list):
                del parent[int(key)]
            else:
                del parent[key]
        else:
            raise ValueError(f"unsupported mutation op: {op}")
    return result


def schema_rule(path: str) -> str:
    if path.startswith("/routing/profile") or "architectural_axes" in path or "direct_conditions" in path:
        return "FND-PROFILE-002"
    if path.startswith("/routing"):
        return "FND-ROUTE-001"
    if path.startswith("/gate"):
        return "FND-GATE-001"
    if path.startswith("/frontier"):
        return "FND-FRONTIER-001"
    if path.startswith("/authorization") or path.startswith("/authorizations"):
        return "FND-AUTH-001"
    if path == "/runtime_activation":
        return "FND-RUNTIME-001"
    return "FND-SCHEMA-001"


def resolve_ref(root: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"external schema ref is not allowed: {ref}")
    value: Any = root
    for part in ref[2:].split("/"):
        value = value[part.replace("~1", "/").replace("~0", "~")]
    return value


def matches_type(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, False)


def validate_schema_node(
    value: Any, node: dict[str, Any], root: dict[str, Any], path: str, findings: list[Finding]
) -> None:
    if "$ref" in node:
        validate_schema_node(value, resolve_ref(root, node["$ref"]), root, path, findings)
        return
    if "oneOf" in node:
        trials: list[list[Finding]] = []
        for branch in node["oneOf"]:
            branch_findings: list[Finding] = []
            validate_schema_node(value, branch, root, path, branch_findings)
            trials.append(branch_findings)
        if sum(not trial for trial in trials) != 1:
            add(findings, schema_rule(path), path, "value must match exactly one schema branch")
        return
    if "const" in node and value != node["const"]:
        add(findings, schema_rule(path), path, f"expected constant {node['const']!r}")
    if "enum" in node and value not in node["enum"]:
        add(findings, schema_rule(path), path, "value is outside the closed enum")
    expected = node.get("type")
    if expected:
        types = expected if isinstance(expected, list) else [expected]
        if not any(matches_type(value, item) for item in types):
            add(findings, schema_rule(path), path, f"expected type {types}")
            return
    if isinstance(value, str) and "pattern" in node and not re.fullmatch(node["pattern"], value):
        add(findings, schema_rule(path), path, "string does not match pattern")
    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in node and value < node["minimum"]:
            add(findings, schema_rule(path), path, "integer is below minimum")
        if "maximum" in node and value > node["maximum"]:
            add(findings, schema_rule(path), path, "integer is above maximum")
    if isinstance(value, dict):
        required = set(node.get("required", []))
        for key in sorted(required - set(value)):
            add(findings, schema_rule(f"{path}/{key}"), f"{path}/{key}", "required field is missing")
        properties = node.get("properties", {})
        if node.get("additionalProperties") is False:
            for key in sorted(set(value) - set(properties)):
                add(findings, schema_rule(f"{path}/{key}"), f"{path}/{key}", "unknown field")
        for key, child in properties.items():
            if key in value:
                validate_schema_node(value[key], child, root, f"{path}/{key}", findings)
    if isinstance(value, list):
        if len(value) < node.get("minItems", 0):
            add(findings, schema_rule(path), path, "array is shorter than minItems")
        if "maxItems" in node and len(value) > node["maxItems"]:
            add(findings, schema_rule(path), path, "array is longer than maxItems")
        if node.get("uniqueItems"):
            encoded = [canonical_bytes(item) for item in value]
            if len(encoded) != len(set(encoded)):
                add(findings, schema_rule(path), path, "array items must be unique")
        if "items" in node:
            for index, child in enumerate(value):
                validate_schema_node(child, node["items"], root, f"{path}/{index}", findings)


def validate_routing(data: dict[str, Any], findings: list[Finding]) -> None:
    routing = data.get("routing", {})
    if routing.get("primary_route") not in routing.get("route_plan", []):
        add(findings, "FND-ROUTE-002", "/routing/route_plan", "primary route is absent")
    axes = {item.get("id"): item.get("state") for item in routing.get("architectural_axes", [])}
    direct = {item.get("id"): item.get("state") for item in routing.get("direct_conditions", [])}
    if set(axes) != AXES or set(direct) != DIRECT_CONDITIONS:
        add(findings, "FND-PROFILE-002", "/routing", "profile inputs are not exact closed sets")
        return
    unresolved = sorted(key for key, state in axes.items() if state == "unresolved")
    checkpoint = routing.get("profile_checkpoint")
    material_checkpoint = checkpoint != "read_only_discovery"
    if any(state == "true" for state in axes.values()) or (unresolved and material_checkpoint):
        expected_profile = "architectural"
    elif unresolved:
        expected_profile = "bounded"
    elif all(state == "true" for state in direct.values()):
        expected_profile = "direct"
    else:
        expected_profile = "bounded"
    expected = (
        expected_profile,
        "provisional" if unresolved else "confirmed",
        unresolved,
    )
    actual = (
        routing.get("profile"), routing.get("profile_status"),
        sorted(routing.get("unresolved_architectural_axes", [])),
    )
    if actual != expected:
        add(findings, "FND-PROFILE-001", "/routing/profile", "derived profile does not match inputs")
        add(findings, "FND-PROFILE-002", "/routing/profile_status", "status/unresolved set mismatch")
    assessment = routing.get("runtime_dependency_assessment", {})
    assessment_values = [
        assessment.get("production_artifact_unchanged"),
        assessment.get("runtime_unchanged"),
        assessment.get("ci_contract_unchanged"),
        assessment.get("deployment_license_security_unchanged"),
        assessment.get("simple_removal_and_existing_validation"),
    ]
    change_kind = assessment.get("change_kind")
    if change_kind == "none":
        expected_runtime_axis = "false"
        assessment_valid = set(assessment_values) == {"not_applicable"}
    elif change_kind == "production_or_runtime":
        expected_runtime_axis = "true"
        assessment_valid = set(assessment_values) == {"not_applicable"}
    else:
        assessment_valid = change_kind == "dev_test_only" and "not_applicable" not in assessment_values
        if "false" in assessment_values:
            expected_runtime_axis = "true"
        elif "unresolved" in assessment_values:
            expected_runtime_axis = "unresolved"
        else:
            expected_runtime_axis = "false"
    if not assessment_valid or axes.get("runtime_dependency") != expected_runtime_axis:
        add(findings, "FND-PROFILE-003", "/routing/runtime_dependency_assessment", "runtime dependency assessment does not derive the axis")
    runtime_axis = next(
        (item for item in routing.get("architectural_axes", []) if item.get("id") == "runtime_dependency"),
        {},
    )
    if sorted(runtime_axis.get("evidence_refs", [])) != sorted(assessment.get("evidence_refs", [])):
        add(findings, "FND-PROFILE-003", "/routing/runtime_dependency_assessment/evidence_refs", "runtime dependency assessment and axis evidence differ")
    transition = routing.get("transition", {})
    reason = transition.get("reason")
    predecessor_fields = (
        transition.get("predecessor_routing_ref"),
        transition.get("from_route"),
        transition.get("from_profile"),
        transition.get("applied_before_side_effect"),
    )
    transition_valid = True
    if reason == "initial":
        transition_valid = all(value is None for value in predecessor_fields)
    else:
        transition_valid = all(value is not None for value in predecessor_fields) and transition.get("applied_before_side_effect") is True
        old_profile = transition.get("from_profile")
        new_profile = routing.get("profile")
        if reason == "route_progress" and old_profile != new_profile:
            transition_valid = False
        if old_profile != new_profile and reason not in {"new_evidence", "scope_changed", "hard_floor_detected", "hard_floor_resolved"}:
            transition_valid = False
        rank = {"direct": 0, "bounded": 1, "architectural": 2}
        if old_profile in rank and new_profile in rank:
            if rank[new_profile] < rank[old_profile] and reason != "hard_floor_resolved":
                transition_valid = False
            if rank[new_profile] < rank[old_profile] and (
                routing.get("profile_status") != "confirmed" or unresolved
            ):
                transition_valid = False
            if rank[new_profile] > rank[old_profile] and reason == "hard_floor_resolved":
                transition_valid = False
    if not transition_valid:
        add(findings, "FND-PROFILE-004", "/routing/transition", "profile transition is not closed or timely")


def validate_gate(data: dict[str, Any], findings: list[Finding]) -> None:
    gate = data.get("gate", {})
    result, blocker, action = gate.get("result"), gate.get("blocker"), gate.get("next_action")
    valid = True
    if result in {"pass", "conditional"}:
        valid = blocker == "none" and action in {"continue", None}
    elif result == "blocked":
        mapping = {
            "missing_decision": {"clarify"},
            "missing_authorization": {"reauthorize"},
            "scope_expansion": {"reauthorize"},
            "external_dependency": {None},
        }
        if blocker == "missing_evidence":
            valid = action in {"continue", "clarify"}
        else:
            valid = action in mapping.get(blocker, set())
    if gate.get("blocking_defer"):
        valid = result == "blocked" and blocker != "none" and action is None
    if not valid:
        add(findings, "FND-GATE-001", "/gate", "gate/blocker/next-action cross-product is invalid")
    owner = gate.get("missing_evidence_owner")
    if blocker == "missing_evidence":
        expected_action = "continue" if owner == "local" else "clarify" if owner == "user" else None
        if action != expected_action:
            add(findings, "FND-GATE-002", "/gate/missing_evidence_owner", "missing-evidence owner does not derive the next action")
    elif owner != "none":
        add(findings, "FND-GATE-002", "/gate/missing_evidence_owner", "non-evidence blocker must have owner none")
    if gate.get("blocking_defer"):
        expected_progress = "partial_block" if gate.get("work_remaining") else "terminal_blocked"
    elif result in {"pass", "conditional"} or (blocker == "missing_evidence" and action == "continue"):
        expected_progress = "continue"
    elif action in {"clarify", "reauthorize"}:
        expected_progress = "partial_block" if gate.get("work_remaining") else "await_input"
    elif result == "blocked" and action is None:
        expected_progress = "partial_block" if gate.get("work_remaining") else "terminal_blocked"
    else:
        expected_progress = "terminal_blocked"
    if gate.get("progress") != expected_progress:
        add(findings, "FND-GATE-002", "/gate/progress", "progress does not follow the gate state")
    assumption = gate.get("assumption_effect")
    if assumption == "non_material" and result != "conditional":
        add(findings, "FND-GATE-002", "/gate/assumption_effect", "non-material assumption must be conditional")
    if assumption == "changes_result" and (result, blocker, action) != ("blocked", "missing_decision", "clarify"):
        add(findings, "FND-GATE-002", "/gate/assumption_effect", "material assumption must return to decision clarification")


def validate_frontier(data: dict[str, Any], findings: list[Finding]) -> None:
    frontier = data.get("frontier", {})
    units = frontier.get("units", [])
    unit_index = {(unit.get("unit_id"), unit.get("revision")): unit for unit in units}
    if len(unit_index) != len(units):
        add(findings, "FND-FRONTIER-005", "/frontier/units", "unit ID/revision pairs must be unique")
    current = [u for u in units if u.get("state") not in HISTORICAL_STATES]
    if sorted(frontier.get("visible_unit_ids", [])) != sorted(u.get("unit_id") for u in current):
        add(findings, "FND-FRONTIER-001", "/frontier/visible_unit_ids", "visible IDs are not current exact set")
    known_unit_ids = {unit.get("unit_id") for unit in units}
    dependency_graph: dict[Any, set[Any]] = {}
    for index, unit in enumerate(units):
        path = f"/frontier/units/{index}"
        unit_id = unit.get("unit_id")
        dependencies = set(unit.get("dependency_ids", []))
        if unit_id in dependencies or not dependencies <= known_unit_ids:
            add(findings, "FND-FRONTIER-001", f"{path}/dependency_ids", "unit dependencies must be existing non-self frontier unit IDs")
        if unit.get("state") not in HISTORICAL_STATES:
            dependency_graph.setdefault(unit_id, set()).update(dependencies)
            if unit.get("basis_fingerprint") != frontier.get("basis_fingerprint"):
                add(findings, "FND-FRONTIER-001", f"{path}/basis_fingerprint", "current unit basis must equal the current frontier basis")
    dependency_color: dict[Any, int] = {}

    def dependency_cycle(unit_id: Any) -> bool:
        color = dependency_color.get(unit_id, 0)
        if color == 1:
            return True
        if color == 2:
            return False
        dependency_color[unit_id] = 1
        if any(dependency_cycle(dependency_id) for dependency_id in dependency_graph.get(unit_id, set())):
            return True
        dependency_color[unit_id] = 2
        return False

    if any(dependency_cycle(unit_id) for unit_id in dependency_graph):
        add(findings, "FND-FRONTIER-001", "/frontier/units", "current unit dependency graph must be acyclic")
    pending_clarifications: list[dict[str, Any]] = []
    pending_authorizations: list[tuple[Any, Any]] = []
    authorization_records = {item.get("authorization_id"): item for item in data.get("authorizations", [])}
    current_auth_ids = current_authorization_ids(data.get("authorizations", []))
    authorization_evaluations: dict[Any, list[dict[str, Any]]] = {}
    for evaluation in data.get("authorization_evaluations", []):
        authorization_evaluations.setdefault(
            evaluation.get("selected_authorization_id"), []
        ).append(evaluation)
    for index, unit in enumerate(units):
        path = f"/frontier/units/{index}"
        predecessor_ref = unit.get("predecessor_unit_ref")
        successor_ref = unit.get("successor_unit_ref")
        if predecessor_ref is None:
            if unit.get("revision") != 1:
                add(findings, "FND-FRONTIER-005", path, "a root unit must begin at revision one")
        else:
            predecessor = (
                unit_index.get(
                    (predecessor_ref.get("id"), predecessor_ref.get("revision"))
                )
                if isinstance(predecessor_ref, dict)
                else None
            )
            predecessor_valid = bool(
                predecessor
                and predecessor.get("unit_id") == unit.get("unit_id")
                and predecessor.get("gap_kind") == unit.get("gap_kind")
                and predecessor.get("revision") == unit.get("revision", 0) - 1
                and identity_ref_matches(
                    predecessor_ref,
                    predecessor,
                    kind="frontier_unit",
                    id_field="unit_id",
                )
                and identity_ref_matches(
                    predecessor.get("successor_unit_ref"),
                    unit,
                    kind="frontier_unit",
                    id_field="unit_id",
                )
            )
            if not predecessor_valid:
                add(findings, "FND-FRONTIER-005", path, "unit predecessor is not an exact adjacent reciprocal record")
        if successor_ref is not None:
            successor = (
                unit_index.get(
                    (successor_ref.get("id"), successor_ref.get("revision"))
                )
                if isinstance(successor_ref, dict)
                else None
            )
            successor_valid = bool(
                successor
                and successor.get("unit_id") == unit.get("unit_id")
                and successor.get("revision") == unit.get("revision", 0) + 1
                and identity_ref_matches(
                    successor_ref,
                    successor,
                    kind="frontier_unit",
                    id_field="unit_id",
                )
                and identity_ref_matches(
                    successor.get("predecessor_unit_ref"),
                    unit,
                    kind="frontier_unit",
                    id_field="unit_id",
                )
            )
            if not successor_valid:
                add(findings, "FND-FRONTIER-005", path, "unit successor is not an exact adjacent reciprocal record")
        if unit.get("state") not in HISTORICAL_STATES and successor_ref is not None:
            add(findings, "FND-FRONTIER-005", path, "a current unit must be the successor-free lineage leaf")
    for index, unit in enumerate(units):
        path = f"/frontier/units/{index}"
        state = unit.get("state")
        relevance = unit.get("checkpoint_relevance")
        disposition = unit.get("runtime_disposition")
        kind = unit.get("gap_kind")
        authorization_id = unit.get("authorization_id")
        auth = authorization_records.get(authorization_id)
        if (kind == "authorization") != (authorization_id is not None):
            add(findings, "FND-FRONTIER-001", f"{path}/authorization_id", "authorization reference presence does not match gap kind")
        if kind == "authorization" and auth is None:
            add(findings, "FND-FRONTIER-006", f"{path}/authorization_id", "authorization unit references no exact authorization record")
        if (
            kind == "authorization"
            and auth is not None
            and bool(auth.get("future_only")) != (relevance == "future_only")
        ):
            add(findings, "FND-FRONTIER-006", path, "authorization future-only state and unit relevance differ")
        if state in HISTORICAL_STATES:
            successor_ref = unit.get("successor_unit_ref")
            successor = unit_index.get((successor_ref.get("id"), successor_ref.get("revision"))) if isinstance(successor_ref, dict) else None
            predecessor_ref = successor.get("predecessor_unit_ref") if successor else None
            transition_closed = bool(
                successor
                and successor.get("unit_id") == unit.get("unit_id")
                and successor.get("revision") == unit.get("revision", 0) + 1
                and identity_ref_matches(
                    successor_ref,
                    successor,
                    kind="frontier_unit",
                    id_field="unit_id",
                )
                and identity_ref_matches(
                    predecessor_ref,
                    unit,
                    kind="frontier_unit",
                    id_field="unit_id",
                )
            )
            if disposition is not None or not transition_closed:
                add(findings, "FND-FRONTIER-005", path, "historical revision needs null runtime and successor")
            expected_historical_state = (
                "superseded" if auth and auth.get("status") == "withdrawn"
                else "stale" if auth and auth.get("status") == "stale"
                else None
            )
            if kind == "authorization" and state != expected_historical_state:
                add(findings, "FND-FRONTIER-006", path, "historical authorization unit does not match its authorization record")
            continue
        if not isinstance(disposition, dict):
            add(findings, "FND-FRONTIER-001", f"{path}/runtime_disposition", "current unit must have a runtime disposition")
            continue
        if kind == "authorization" and authorization_id not in current_auth_ids:
            add(findings, "FND-FRONTIER-006", f"{path}/authorization_id", "current authorization unit must reference a current lineage leaf")
        matching_evaluations = authorization_evaluations.get(authorization_id, [])
        exact_evaluation = (
            matching_evaluations[0]
            if kind == "authorization" and len(matching_evaluations) == 1
            else None
        )
        if kind == "authorization" and len(matching_evaluations) != 1:
            add(findings, "FND-FRONTIER-006", path, "current authorization unit needs exactly one bound evaluation")
        authorization_blocker = (
            "scope_expansion"
            if exact_evaluation
            and exact_evaluation.get("derived_result") == "blocked_scope_expansion"
            else "missing_authorization"
        )
        action = disposition.get("resolution_action")
        defer_effect = disposition.get("defer_effect")
        allowed_pairs = {
            "discoverable_fact": {("investigate", "pending"), ("investigate", "resolved_by_evidence")},
            "user_supplied_evidence": {("request_input", "pending"), ("request_input", "resolved_by_evidence")},
            "incidental_preference": {("defer", "deferred"), ("assume", "assumed")},
            "material_decision": {("request_input", "pending"), ("request_input", "answered")},
            "authorization": {("request_input", "pending"), ("request_input", "resolved_by_evidence")},
            "external_blocker": {("report_blocker", "pending"), ("report_blocker", "resolved_by_evidence")},
        }
        if action == "defer" and state == "deferred":
            pair_valid = True
        else:
            pair_valid = (action, state) in allowed_pairs.get(kind, set())
        if not pair_valid:
            add(findings, "FND-FRONTIER-001", path, "gap kind, action, and state are incompatible")
        binding = unit.get("value_binding")
        expected_binding_kind = (
            {"receipt"} if state == "resolved_by_evidence" and kind == "authorization"
            else {"evidence"} if state == "resolved_by_evidence"
            else {"assumption"} if state == "assumed"
            else {"normalized_value"} if state == "answered"
            else None
        )
        if expected_binding_kind is None:
            if binding is not None:
                add(findings, "FND-FRONTIER-001", f"{path}/value_binding", "unresolved or deferred state must be value-free")
        elif not isinstance(binding, dict) or binding.get("kind") not in expected_binding_kind:
            add(findings, "FND-FRONTIER-001", f"{path}/value_binding", "state has the wrong value binding kind")
        if kind == "authorization" and state == "resolved_by_evidence":
            expected_receipt_binding = (
                {
                    "kind": "receipt",
                    "authorization_id": authorization_id,
                    "receipt_revision": auth.get("receipt_revision"),
                    "receipt_fingerprint": auth.get("receipt_fingerprint"),
                }
                if auth is not None
                else None
            )
            if binding != expected_receipt_binding:
                add(findings, "FND-FRONTIER-001", f"{path}/value_binding", "resolved authorization must bind the exact current receipt tuple")
        if action == "defer":
            if defer_effect not in {"nonblocking", "blocks_dependent_scope"} or unit.get("value_binding") is not None:
                add(findings, "FND-FRONTIER-002", path, "defer must be value-free with an exact effect")
            if defer_effect == "nonblocking" and relevance != "future_only":
                add(findings, "FND-FRONTIER-002", path, "nonblocking defer is limited to a future-only checkpoint")
            if defer_effect == "blocks_dependent_scope" and relevance != "current":
                add(findings, "FND-FRONTIER-002", path, "blocking defer must apply to the current checkpoint")
        elif defer_effect != "none":
            add(findings, "FND-FRONTIER-002", path, "non-defer action must have defer_effect none")
        future_tuple = (
            action == "defer"
            and state == "deferred"
            and defer_effect == "nonblocking"
            and disposition.get("gate_result") == "pass"
            and disposition.get("blocker") == "none"
            and disposition.get("next_action") == "continue"
        )
        if (relevance == "future_only") != future_tuple:
            add(findings, "FND-FRONTIER-002", path, "checkpoint relevance does not match the exact future-only tuple")
        if defer_effect == "blocks_dependent_scope":
            if unit.get("gap_kind") not in {"discoverable_fact", "user_supplied_evidence", "material_decision", "authorization", "external_blocker"}:
                add(findings, "FND-FRONTIER-002", path, "gap kind cannot block on defer")
            if disposition.get("gate_result") != "blocked" or disposition.get("blocker") == "none" or disposition.get("next_action") is not None:
                add(findings, "FND-FRONTIER-002", path, "blocking defer must preserve blocker and null action")
            blocker_by_kind = {
                "discoverable_fact": {"missing_evidence"},
                "user_supplied_evidence": {"missing_evidence"},
                "material_decision": {"missing_decision"},
                "authorization": {"missing_authorization", "scope_expansion"},
                "external_blocker": {"external_dependency"},
            }
            if disposition.get("blocker") not in blocker_by_kind.get(kind, set()):
                add(findings, "FND-FRONTIER-002", path, "blocking defer has the wrong blocker for its gap kind")
        if unit.get("gap_kind") == "incidental_preference" and action == "assume":
            conditions = {c.get("id"): c.get("state") for c in unit.get("safe_default_conditions", [])}
            if set(conditions) != SAFE_DEFAULT_IDS or not all(v == "true" for v in conditions.values()):
                add(findings, "FND-FRONTIER-003", path, "preference assumption lacks all safe-default proofs")
        interaction = disposition.get("interaction_kind")
        requirement = disposition.get("interaction_requirement")
        gate_tuple = (disposition.get("gate_result"), disposition.get("blocker"), disposition.get("next_action"))
        progress = disposition.get("progress")
        if state in {"resolved_by_evidence", "answered"}:
            expected_disposition = (("pass", "none", "continue"), "none", "none", {"continue"})
        elif state == "assumed":
            expected_disposition = (("conditional", "none", "continue"), "none", "none", {"continue"})
        elif action == "investigate" and state == "pending":
            expected_disposition = (("conditional", "none", "continue"), "none", "none", {"continue"})
        elif action == "request_input" and state == "pending":
            if kind == "authorization":
                expected_disposition = (("blocked", authorization_blocker, "reauthorize"), "authorization", "required", {"await_input", "partial_block"})
            elif kind == "material_decision":
                expected_disposition = (("blocked", "missing_decision", "clarify"), "clarification", "required", {"await_input", "partial_block"})
            else:
                expected_disposition = (("blocked", "missing_evidence", "clarify"), "clarification", "required", {"await_input", "partial_block"})
        elif action == "report_blocker" and state == "pending":
            expected_disposition = (("blocked", "external_dependency", None), "none", "none", {"partial_block", "terminal_blocked"})
        elif action == "assume":
            expected_disposition = (("conditional", "none", "continue"), "none", "none", {"continue"})
        elif action == "defer" and defer_effect == "nonblocking":
            expected_disposition = (("pass", "none", "continue"), "none", "none", {"continue"})
        elif action == "defer" and defer_effect == "blocks_dependent_scope":
            expected_disposition = (("blocked", disposition.get("blocker"), None), "none", "none", {"partial_block", "terminal_blocked"})
        else:
            expected_disposition = None
        if expected_disposition:
            expected_gate, expected_interaction, expected_requirement, expected_progress = expected_disposition
            if (gate_tuple, interaction, requirement) != (expected_gate, expected_interaction, expected_requirement) or progress not in expected_progress:
                add(findings, "FND-FRONTIER-001", f"{path}/runtime_disposition", "runtime disposition does not match the state")
        if interaction == "clarification" and state == "pending":
            pending_clarifications.append(unit)
        if interaction == "authorization" and state == "pending":
            pending_authorizations.append((frontier.get("logical_task_id"), disposition.get("interaction_owner")))
        if kind == "authorization" and auth is not None:
            status = auth.get("status")
            if status in {"denied", "withdrawn"}:
                expected_auth_options = {
                    ("deferred", "defer", "blocks_dependent_scope", "blocked", "missing_authorization", None)
                }
            elif status == "stale" and auth.get("future_only"):
                expected_auth_options = {
                    ("deferred", "defer", "nonblocking", "pass", "none", "continue")
                }
            elif (
                status == "granted"
                and exact_evaluation
                and exact_evaluation.get("derived_result") == "allowed"
            ):
                expected_auth_options = {
                    ("resolved_by_evidence", "request_input", "none", "pass", "none", "continue")
                }
            elif status in {"stale", "not_granted", "granted"}:
                expected_auth_options = {
                    ("pending", "request_input", "none", "blocked", authorization_blocker, "reauthorize"),
                    ("deferred", "defer", "blocks_dependent_scope", "blocked", authorization_blocker, None),
                }
            else:
                expected_auth_options = set()
            actual_auth = (state, action, defer_effect, *gate_tuple)
            expected_auth_progress = (
                {"continue"}
                if actual_auth[3] == "pass"
                else {"await_input", "partial_block"}
                if actual_auth[1] == "request_input"
                else {"partial_block", "terminal_blocked"}
            )
            if actual_auth not in expected_auth_options or progress not in expected_auth_progress:
                add(findings, "FND-FRONTIER-006", path, "authorization state does not derive the frontier disposition")
    if len(pending_authorizations) != len(set(pending_authorizations)):
        add(findings, "FND-FRONTIER-004", "/frontier", "more than one pending authorization interaction per owner")
    if pending_clarifications and pending_authorizations:
        add(findings, "FND-FRONTIER-004", "/frontier", "clarification and authorization interactions cannot both be pending")
    pending_clarification_ids = {
        unit.get("unit_id") for unit in pending_clarifications
    }
    for unit_id in pending_clarification_ids:
        visited: set[Any] = set()
        stack = list(dependency_graph.get(unit_id, set()))
        while stack:
            dependency_id = stack.pop()
            if dependency_id in visited:
                continue
            visited.add(dependency_id)
            stack.extend(dependency_graph.get(dependency_id, set()))
        if (visited & pending_clarification_ids) - {unit_id}:
            add(findings, "FND-FRONTIER-004", "/frontier/clarification_view", "one clarification view cannot batch transitively dependent units")
            break
    for authorization_id, auth in authorization_records.items():
        related = [unit for unit in units if unit.get("authorization_id") == authorization_id]
        current_related = [
            unit for unit in related if unit.get("state") not in HISTORICAL_STATES
        ]
        if len(current_related) > 1:
            add(findings, "FND-FRONTIER-006", "/frontier/units", "one authorization evaluation cannot bind multiple current frontier units")
        routed_authorization_id = data.get("routing", {}).get(
            "authorization_ref", {}
        ).get("id")
        invalid_current_required = bool(
            authorization_id in current_auth_ids
            and (
                auth.get("status") in {"denied", "withdrawn", "stale"}
                or (
                    auth.get("status") == "not_granted"
                    and authorization_id == routed_authorization_id
                )
            )
        )
        if invalid_current_required:
            if len(current_related) != 1:
                add(findings, "FND-FRONTIER-006", "/frontier/units", "invalid authorization must have exactly one current successor unit")
            if len(authorization_evaluations.get(authorization_id, [])) != 1:
                add(findings, "FND-FRONTIER-006", "/authorization_evaluations", "invalid current authorization must have exactly one evaluation")
        if auth.get("status") in {"withdrawn", "stale"}:
            expected_history = "superseded" if auth.get("status") == "withdrawn" else "stale"
            historical_related = [unit for unit in related if unit.get("state") == expected_history]
            if len(historical_related) != 1:
                add(findings, "FND-FRONTIER-006", "/frontier/units", "withdrawn or stale authorization must retain one exact historical unit")
    for index, evaluation in enumerate(data.get("authorization_evaluations", [])):
        selected_id = evaluation.get("selected_authorization_id")
        selected = authorization_records.get(selected_id)
        current_related = [
            unit
            for unit in units
            if unit.get("authorization_id") == selected_id
            and unit.get("gap_kind") == "authorization"
            and unit.get("state") not in HISTORICAL_STATES
        ]
        selected_is_current = bool(
            selected is not None and selected_id in current_auth_ids
        )
        if not selected_is_current:
            add(
                findings,
                "FND-FRONTIER-006",
                f"/authorization_evaluations/{index}/selected_authorization_id",
                "authorization evaluation must select an existing current lineage leaf",
            )
        elif evaluation.get("derived_result") != "allowed":
            if len(current_related) != 1:
                add(
                    findings,
                    "FND-FRONTIER-006",
                    f"/authorization_evaluations/{index}",
                    "blocked authorization evaluation must surface as one exact current authorization unit",
                )
        elif len(current_related) == 1 and current_related[0].get("state") != "resolved_by_evidence":
            add(
                findings,
                "FND-FRONTIER-006",
                f"/authorization_evaluations/{index}",
                "surfaced allowed authorization evaluation must be resolved by its exact receipt",
            )
    validate_clarification_views(frontier, pending_clarifications, findings)


def clarification_view_shape_valid(view: dict[str, Any]) -> bool:
    view_units = view.get("units", [])
    view_unit_ids = [item.get("unit_id") for item in view_units]
    valid = (
        len(view_unit_ids) == len(set(view_unit_ids))
        and sorted(view.get("visible_unit_ids", [])) == sorted(view_unit_ids)
    )
    decision_options: dict[str, set[str]] = {}
    for item in view_units:
        if item.get("kind") == "decision":
            option_ids = [option.get("option_id") for option in item.get("options", [])]
            if len(option_ids) != len(set(option_ids)):
                valid = False
            recommended = item.get("recommended_option_id")
            if recommended is not None and recommended not in option_ids:
                valid = False
            decision_options[item.get("unit_id")] = set(option_ids)
    shorthand = view.get("accepted_shorthand", [])
    shorthand_ids = [item.get("shorthand_id") for item in shorthand]
    if len(shorthand_ids) != len(set(shorthand_ids)) or any(
        item.get("option_id")
        not in decision_options.get(item.get("unit_id"), set())
        for item in shorthand
    ):
        valid = False
    return valid and view.get("view_digest") == clarification_view_digest(view)


def stable_view_payload(view: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in view.items()
        if key
        not in {
            "revision",
            "predecessor_view_ref",
            "transition_cause",
            "view_digest",
            "view_state",
        }
    }


def validate_clarification_views(
    frontier: dict[str, Any],
    pending_clarifications: list[dict[str, Any]],
    findings: list[Finding],
) -> None:
    history = frontier.get("clarification_view_history", [])
    current_view = frontier.get("clarification_view")
    views = list(history)
    if isinstance(current_view, dict):
        views.append(current_view)
    if not views:
        if pending_clarifications:
            add(findings, "FND-FRONTIER-004", "/frontier/clarification_view", "pending clarification units have no fresh view")
        return
    if not isinstance(current_view, dict):
        add(findings, "FND-FRONTIER-004", "/frontier/clarification_view", "view history has no current lineage leaf")
        return

    view_index = {
        (view.get("round_id"), view.get("revision")): view for view in views
    }
    known_unit_ids = {
        unit.get("unit_id") for unit in frontier.get("units", [])
    }
    unit_kinds_by_id: dict[Any, set[Any]] = {}
    for unit in frontier.get("units", []):
        unit_kinds_by_id.setdefault(unit.get("unit_id"), set()).add(
            unit.get("gap_kind")
        )
    lifecycle_valid = len(view_index) == len(views)
    predecessor_counts: dict[tuple[Any, Any], int] = {}
    roots = 0
    for view in views:
        if not clarification_view_shape_valid(view):
            lifecycle_valid = False
        if not set(view.get("visible_unit_ids", [])) <= known_unit_ids:
            lifecycle_valid = False
        for item in view.get("units", []):
            expected_gap_kind = (
                "material_decision"
                if item.get("kind") == "decision"
                else "user_supplied_evidence"
            )
            if unit_kinds_by_id.get(item.get("unit_id")) != {
                expected_gap_kind
            }:
                lifecycle_valid = False
        reference = view.get("predecessor_view_ref")
        state = view.get("view_state")
        cause = view.get("transition_cause")
        if reference is None:
            roots += 1
            if view.get("revision") != 1 or state != "pending" or cause != "initial_presentation":
                lifecycle_valid = False
            continue
        if not isinstance(reference, dict):
            lifecycle_valid = False
            continue
        key = (reference.get("id"), reference.get("revision"))
        predecessor = view_index.get(key)
        predecessor_counts[key] = predecessor_counts.get(key, 0) + 1
        if not predecessor or reference.get("digest") != predecessor.get("view_digest"):
            lifecycle_valid = False
            continue
        same_round_successor = bool(
            view.get("round_id") == predecessor.get("round_id")
            and view.get("revision") == predecessor.get("revision", 0) + 1
        )
        new_round_successor = bool(
            view.get("round_id") != predecessor.get("round_id")
            and view.get("revision") == 1
            and cause == "new_interaction"
        )
        if not (same_round_successor or new_round_successor):
            lifecycle_valid = False
        transition = (predecessor.get("view_state"), state, cause)
        if transition in {
            ("pending", "consumed", "response_consumed"),
            ("pending", "expired", "basis_expired"),
        }:
            if stable_view_payload(view) != stable_view_payload(predecessor):
                lifecycle_valid = False
        elif transition == ("consumed", "pending", "partial_response_remaining"):
            previous_ids = set(predecessor.get("visible_unit_ids", []))
            current_ids = set(view.get("visible_unit_ids", []))
            removed_ids = previous_ids - current_ids
            previous_units = {
                item.get("unit_id"): item for item in predecessor.get("units", [])
            }
            current_units = {
                item.get("unit_id"): item for item in view.get("units", [])
            }
            previous_shorthand = {
                canonical_bytes(item)
                for item in predecessor.get("accepted_shorthand", [])
                if item.get("unit_id") in current_ids
            }
            current_shorthand = {
                canonical_bytes(item) for item in view.get("accepted_shorthand", [])
            }
            if (
                not same_round_successor
                or not current_ids
                or not current_ids < previous_ids
                or view.get("basis_fingerprint") != predecessor.get("basis_fingerprint")
                or view.get("interaction_owner") != predecessor.get("interaction_owner")
                or view.get("renderer_version") != predecessor.get("renderer_version")
                or any(
                    current_units.get(unit_id) != previous_units.get(unit_id)
                    for unit_id in current_ids
                )
                or current_shorthand != previous_shorthand
            ):
                lifecycle_valid = False
            current_frontier_units: dict[Any, list[dict[str, Any]]] = {}
            for unit in frontier.get("units", []):
                if unit.get("state") not in HISTORICAL_STATES:
                    current_frontier_units.setdefault(unit.get("unit_id"), []).append(unit)
            for unit_id in removed_ids:
                rendered = previous_units.get(unit_id, {})
                candidates = current_frontier_units.get(unit_id, [])
                expected = (
                    ("material_decision", {"answered", "deferred"})
                    if rendered.get("kind") == "decision"
                    else (
                        "user_supplied_evidence",
                        {"resolved_by_evidence", "deferred"},
                    )
                )
                if (
                    len(candidates) != 1
                    or candidates[0].get("gap_kind") != expected[0]
                    or candidates[0].get("state") not in expected[1]
                ):
                    lifecycle_valid = False
        elif transition == ("expired", "pending", "basis_refreshed"):
            if not same_round_successor:
                lifecycle_valid = False
        elif not (
            new_round_successor
            and predecessor.get("view_state") in {"consumed", "expired"}
            and state == "pending"
        ):
            lifecycle_valid = False

    current_key = (current_view.get("round_id"), current_view.get("revision"))
    historical_keys = {
        (view.get("round_id"), view.get("revision")) for view in history
    }
    lifecycle_valid = bool(
        lifecycle_valid
        and roots == 1
        and all(predecessor_counts.get(key) == 1 for key in historical_keys)
        and current_key not in predecessor_counts
    )
    if not lifecycle_valid:
        add(findings, "FND-FRONTIER-004", "/frontier/clarification_view", "clarification view lifecycle, predecessor, or digest is invalid")

    if pending_clarifications:
        expected_ids = sorted(unit.get("unit_id") for unit in pending_clarifications)
        owners = {
            unit["runtime_disposition"].get("interaction_owner")
            for unit in pending_clarifications
        }
        source_by_id = {
            unit.get("unit_id"): unit for unit in pending_clarifications
        }
        pending_valid = current_view.get("view_state") == "pending"
        if pending_valid:
            for item in current_view.get("units", []):
                source = source_by_id.get(item.get("unit_id"), {})
                expected_kind = (
                    "decision"
                    if source.get("gap_kind") == "material_decision"
                    else "evidence_request"
                )
                if item.get("kind") != expected_kind:
                    pending_valid = False
            pending_valid = bool(
                pending_valid
                and current_view.get("basis_fingerprint")
                == frontier.get("basis_fingerprint")
                and sorted(current_view.get("visible_unit_ids", [])) == expected_ids
                and len(owners) == 1
                and current_view.get("interaction_owner") in owners
                and clarification_view_shape_valid(current_view)
            )
        if not pending_valid:
            add(findings, "FND-FRONTIER-004", "/frontier/clarification_view", "pending clarification view is not the exact heterogeneous unit set")
    elif current_view.get("view_state") == "pending":
        add(findings, "FND-FRONTIER-004", "/frontier/clarification_view", "pending view has no pending clarification units")


def current_authorization_ids(auth_items: list[dict[str, Any]]) -> set[Any]:
    predecessor_ids = {
        record["predecessor_authorization_ref"].get("id")
        for record in auth_items
        if isinstance(record.get("predecessor_authorization_ref"), dict)
    }
    return {record.get("authorization_id") for record in auth_items} - predecessor_ids


def validate_authorization(data: dict[str, Any], findings: list[Finding]) -> None:
    auth_items = data.get("authorizations", [])
    records = {item.get("authorization_id"): item for item in auth_items}
    if len(records) != len(auth_items):
        add(findings, "FND-AUTH-001", "/authorizations", "authorization IDs must be unique")
    predecessor_counts: dict[Any, int] = {}
    for record in auth_items:
        predecessor_ref = record.get("predecessor_authorization_ref")
        if isinstance(predecessor_ref, dict):
            predecessor_id = predecessor_ref.get("id")
            predecessor_counts[predecessor_id] = predecessor_counts.get(predecessor_id, 0) + 1
    if any(count != 1 for count in predecessor_counts.values()):
        add(findings, "FND-AUTH-004", "/authorizations", "authorization lineage branches")
    current_ids = current_authorization_ids(auth_items)
    roots_by_binding: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    current_by_binding: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    grant_receipts_by_binding: dict[tuple[Any, ...], list[Any]] = {}
    for record in auth_items:
        binding = (
            record.get("logical_task_id"),
            record.get("capability"),
            record.get("target_fingerprint"),
            record.get("scope_fingerprint"),
            record.get("basis_fingerprint"),
        )
        if record.get("predecessor_authorization_ref") is None:
            roots_by_binding.setdefault(binding, []).append(record)
        if record.get("authorization_id") in current_ids:
            current_by_binding.setdefault(binding, []).append(record)
        if record.get("status") == "granted":
            grant_receipts_by_binding.setdefault(binding, []).append(
                record.get("receipt_fingerprint")
            )
    if any(len(items) > 1 for items in roots_by_binding.values()) or any(
        len(items) > 1 for items in current_by_binding.values()
    ):
        add(findings, "FND-AUTH-004", "/authorizations", "one authorization binding must have one connected root and current leaf")
    if any(
        len(receipts) != len(set(receipts))
        for receipts in grant_receipts_by_binding.values()
    ):
        add(findings, "FND-AUTH-004", "/authorizations", "grant receipt fingerprints cannot replay within one authorization binding")
    evaluations = data.get("authorization_evaluations", [])
    evaluation_ids = [item.get("evaluation_id") for item in evaluations]
    selected_ids = [item.get("selected_authorization_id") for item in evaluations]
    if len(evaluation_ids) != len(set(evaluation_ids)):
        add(findings, "FND-AUTH-005", "/authorization_evaluations", "authorization evaluation IDs must be unique")
    if len(selected_ids) != len(set(selected_ids)):
        add(findings, "FND-AUTH-005", "/authorization_evaluations", "one current authorization leaf can be evaluated only once per envelope")
    for index, record in enumerate(data.get("authorizations", [])):
        path = f"/authorizations/{index}"
        if record.get("capability") not in PER_TASK_CAPABILITIES:
            add(findings, "FND-AUTH-001", f"{path}/capability", "capability is outside per-task enum")
        status = record.get("status")
        request_revision = record.get("request_revision")
        authorization_revision = record.get("authorization_revision")
        receipt_revision = record.get("receipt_revision")
        receipt_fingerprint = record.get("receipt_fingerprint")
        grant_tuple = (request_revision, authorization_revision, receipt_revision, receipt_fingerprint)
        status_shape_valid = False
        if status == "not_applicable":
            status_shape_valid = all(value is None for value in grant_tuple) and not record.get("future_only")
        elif status == "not_granted":
            status_shape_valid = all(value is None for value in grant_tuple[1:]) and not record.get("future_only")
        elif status == "denied":
            status_shape_valid = request_revision is not None and all(value is None for value in grant_tuple[1:]) and not record.get("future_only")
        elif status == "granted":
            status_shape_valid = all(value is not None for value in grant_tuple) and not record.get("future_only")
        elif status in {"withdrawn", "stale"}:
            status_shape_valid = all(value is not None for value in grant_tuple) and (status == "stale" or not record.get("future_only"))
        expected_runtime = status == "granted"
        if not status_shape_valid or bool(record.get("runtime_eligible")) != expected_runtime:
            add(findings, "FND-AUTH-002", path, "authorization status fields or current eligibility are invalid")
        predecessor_ref = record.get("predecessor_authorization_ref")
        if isinstance(predecessor_ref, dict):
            predecessor = records.get(predecessor_ref.get("id"))
            allowed_transitions = {
                "not_granted": {"granted", "denied"},
                "granted": {"withdrawn", "stale"},
                "denied": {"not_granted"},
                "withdrawn": {"granted"},
                "stale": {"granted", "stale"},
            }
            transition_valid = bool(
                predecessor
                and identity_ref_matches(
                    predecessor_ref,
                    predecessor,
                    kind="authorization",
                    id_field="authorization_id",
                )
                and record.get("revision") == predecessor.get("revision", 0) + 1
                and status in allowed_transitions.get(predecessor.get("status"), set())
            )
            if transition_valid:
                transition_valid = bool(
                    record.get("logical_task_id") == predecessor.get("logical_task_id")
                    and record.get("capability") == predecessor.get("capability")
                )
            if transition_valid and predecessor.get("status") == "granted":
                transition_valid = all(
                    record.get(key) == predecessor.get(key)
                    for key in (
                        "target_fingerprint", "scope_fingerprint", "basis_fingerprint",
                        "request_revision", "authorization_revision", "receipt_revision", "receipt_fingerprint",
                    )
                )
            if transition_valid and predecessor.get("status") == "denied":
                transition_valid = bool(
                    record.get("request_revision") is not None
                    and record.get("request_revision") > (predecessor.get("request_revision") or 0)
                )
            if (
                transition_valid
                and predecessor.get("status") == "stale"
                and status == "stale"
            ):
                transition_valid = bool(
                    predecessor.get("future_only") is True
                    and record.get("future_only") is False
                    and all(
                        record.get(key) == predecessor.get(key)
                        for key in (
                            "target_fingerprint",
                            "scope_fingerprint",
                            "basis_fingerprint",
                            "request_revision",
                            "authorization_revision",
                            "receipt_revision",
                            "receipt_fingerprint",
                        )
                    )
                )
            if (
                transition_valid
                and predecessor.get("status") in {"withdrawn", "stale"}
                and status == "granted"
            ):
                ancestor_receipt_fingerprints: set[Any] = set()
                ancestor = predecessor
                visited_ancestor_ids: set[Any] = set()
                while ancestor is not None:
                    ancestor_id = ancestor.get("authorization_id")
                    if ancestor_id in visited_ancestor_ids:
                        break
                    visited_ancestor_ids.add(ancestor_id)
                    ancestor_receipt = ancestor.get("receipt_fingerprint")
                    if ancestor_receipt is not None:
                        ancestor_receipt_fingerprints.add(ancestor_receipt)
                    ancestor_ref = ancestor.get("predecessor_authorization_ref")
                    ancestor = (
                        records.get(ancestor_ref.get("id"))
                        if isinstance(ancestor_ref, dict)
                        else None
                    )
                transition_valid = bool(
                    all(
                        record.get(key) is not None
                        and record.get(key) > (predecessor.get(key) or 0)
                        for key in ("request_revision", "authorization_revision", "receipt_revision")
                    )
                    and record.get("receipt_fingerprint")
                    not in ancestor_receipt_fingerprints
                )
            if not transition_valid:
                add(findings, "FND-AUTH-004", path, "authorization successor transition is invalid")
    for index, evaluation in enumerate(evaluations):
        selected = records.get(evaluation.get("selected_authorization_id"))
        selected_is_current = bool(selected and selected.get("authorization_id") in current_ids)
        allowed = bool(
            selected
            and selected_is_current
            and selected.get("status") == "granted"
            and selected.get("runtime_eligible")
            and selected.get("capability") == evaluation.get("required_capability")
            and all(selected.get(key) == evaluation.get(key) for key in ("target_fingerprint", "scope_fingerprint", "basis_fingerprint"))
        )
        scope_mismatch = bool(
            selected
            and selected_is_current
            and selected.get("status") == "granted"
            and selected.get("runtime_eligible")
            and selected.get("capability") == evaluation.get("required_capability")
            and selected.get("basis_fingerprint") == evaluation.get("basis_fingerprint")
            and any(selected.get(key) != evaluation.get(key) for key in ("target_fingerprint", "scope_fingerprint"))
        )
        expected = "allowed" if allowed else "blocked_scope_expansion" if scope_mismatch else "blocked_missing_authorization"
        expected_action = "continue" if allowed else "reauthorize"
        expected_count = 1 if allowed and evaluation.get("side_effect_intent") == "dependent" else 0
        binding_mismatch = bool(selected and any(selected.get(key) != evaluation.get(key) for key in ("target_fingerprint", "scope_fingerprint", "basis_fingerprint")))
        if evaluation.get("basis_fingerprint") != data.get("routing", {}).get("basis_fingerprint"):
            add(findings, "FND-AUTH-003", f"/authorization_evaluations/{index}/basis_fingerprint", "authorization evaluation basis must equal the current routing basis")
        if selected is None:
            add(findings, "FND-AUTH-005", f"/authorization_evaluations/{index}", "authorization evaluation selects no exact record")
        if selected and not selected_is_current:
            add(findings, "FND-AUTH-003", f"/authorization_evaluations/{index}", "historical authorization cannot be selected")
        if binding_mismatch and (evaluation.get("derived_result") == "allowed" or evaluation.get("dependent_side_effect_count", 0) != 0):
            add(findings, "FND-AUTH-003", f"/authorization_evaluations/{index}", "authorization binding does not match the requested operation")
        if evaluation.get("derived_result") != expected or evaluation.get("next_action") != expected_action or evaluation.get("dependent_side_effect_count") != expected_count:
            add(findings, "FND-AUTH-005", f"/authorization_evaluations/{index}", "authorization evaluation is not exact-bound")


def validate_gate_frontier_aggregate(data: dict[str, Any], findings: list[Finding]) -> None:
    gate = data.get("gate", {})
    current_units = [
        unit
        for unit in data.get("frontier", {}).get("units", [])
        if unit.get("state") not in HISTORICAL_STATES
        and unit.get("checkpoint_relevance") == "current"
        and isinstance(unit.get("runtime_disposition"), dict)
    ]
    dispositions = [unit["runtime_disposition"] for unit in current_units]
    blocker_rank = {
        "missing_evidence": 1,
        "missing_decision": 2,
        "missing_authorization": 3,
        "scope_expansion": 4,
        "external_dependency": 5,
    }
    blocked = [item for item in dispositions if item.get("gate_result") == "blocked"]
    if blocked:
        selected = max(blocked, key=lambda item: blocker_rank.get(item.get("blocker"), 0))
        same_blocker = [item for item in blocked if item.get("blocker") == selected.get("blocker")]
        if len({item.get("next_action") for item in same_blocker}) != 1:
            add(findings, "FND-GATE-002", "/frontier/units", "same-priority blockers disagree on next action")
        expected_result = "blocked"
        expected_blocker = selected.get("blocker")
        expected_action = selected.get("next_action")
        expected_blocking_defer = any(
            item.get("resolution_action") == "defer"
            and item.get("defer_effect") == "blocks_dependent_scope"
            and item.get("blocker") == expected_blocker
            for item in same_blocker
        )
        if gate.get("work_remaining"):
            expected_progress = "partial_block"
        elif expected_action in {"clarify", "reauthorize"}:
            expected_progress = "await_input"
        else:
            expected_progress = "terminal_blocked"
    elif data.get("routing", {}).get("profile_status") == "provisional" or any(
        item.get("gate_result") == "conditional" for item in dispositions
    ):
        expected_result, expected_blocker, expected_action = "conditional", "none", "continue"
        expected_progress, expected_blocking_defer = "continue", False
    else:
        expected_result, expected_blocker = "pass", "none"
        expected_action = "continue" if gate.get("work_remaining") else None
        expected_progress, expected_blocking_defer = "continue", False
    expected_owner = "none"
    if expected_blocker == "missing_evidence" and expected_action in {"continue", "clarify"}:
        expected_owner = "local" if expected_action == "continue" else "user"
    expected_assumption = (
        "non_material"
        if expected_result == "conditional" and any(unit.get("state") == "assumed" for unit in current_units)
        else "none"
    )
    actual = (
        gate.get("result"), gate.get("blocker"), gate.get("next_action"),
        gate.get("progress"), gate.get("blocking_defer"),
        gate.get("missing_evidence_owner"), gate.get("assumption_effect"),
    )
    expected = (
        expected_result, expected_blocker, expected_action,
        expected_progress, expected_blocking_defer,
        expected_owner, expected_assumption,
    )
    if actual != expected:
        add(findings, "FND-GATE-002", "/gate", "top-level gate is not the exact current-frontier aggregate")


def validate_instance(instance: dict[str, Any], schema: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    validate_schema_node(instance, schema, schema, "", findings)
    if (instance.get("record_kind") == "foundation_contract_fixture") != bool(instance.get("fixture_only")):
        add(findings, "FND-SCHEMA-001", "/record_kind", "record kind and fixture-only marker disagree")
    if any(bool(record.get("fixture_only")) != bool(instance.get("fixture_only")) for record in instance.get("authorizations", [])):
        add(findings, "FND-SCHEMA-001", "/authorizations", "authorization fixture marker disagrees with the envelope")
    routing = instance.get("routing", {})
    gate = instance.get("gate", {})
    frontier = instance.get("frontier", {})
    auth_records = instance.get("authorizations", [])
    gate_ref = routing.get("gate_ref", {})
    if not identity_ref_matches(
        gate_ref, gate, kind="gate", id_field="gate_id"
    ):
        add(findings, "FND-GATE-001", "/routing/gate_ref", "routing does not reference the exact gate identity")
    routing_ref = gate.get("routing_ref", {})
    if not identity_ref_matches(
        routing_ref, routing, kind="routing", id_field="routing_id"
    ):
        add(findings, "FND-ROUTE-001", "/gate/routing_ref", "gate does not reference the exact routing identity")
    authorization_ref = routing.get("authorization_ref", {})
    current_auth_ids = current_authorization_ids(auth_records)
    if not any(
        identity_ref_matches(
            authorization_ref,
            record,
            kind="authorization",
            id_field="authorization_id",
        )
        and record.get("authorization_id") in current_auth_ids
        for record in auth_records
    ):
        add(findings, "FND-AUTH-001", "/routing/authorization_ref", "routing does not reference an exact current authorization identity")
    logical_task_id = routing.get("logical_task_id")
    if frontier.get("logical_task_id") != logical_task_id or any(record.get("logical_task_id") != logical_task_id for record in auth_records):
        add(findings, "FND-ROUTE-001", "/routing/logical_task_id", "foundation records disagree on the logical task")
    if frontier.get("basis_fingerprint") != routing.get("basis_fingerprint"):
        add(findings, "FND-ROUTE-001", "/frontier/basis_fingerprint", "routing and current frontier bases must match")
    validate_routing(instance, findings)
    validate_gate(instance, findings)
    validate_frontier(instance, findings)
    validate_authorization(instance, findings)
    validate_gate_frontier_aggregate(instance, findings)
    if instance.get("routing", {}).get("profile_status") == "provisional":
        if instance.get("gate", {}).get("result") == "pass":
            add(findings, "FND-GATE-002", "/gate/result", "provisional profile cannot globally pass")
        if any(item.get("dependent_side_effect_count", 0) != 0 for item in instance.get("authorization_evaluations", [])):
            add(findings, "FND-PROFILE-004", "/authorization_evaluations", "provisional hard floor cannot cross a dependent side-effect checkpoint")
    return sorted(findings, key=lambda item: (item.rule_id, item.location, item.message))


def validate_foundation_cases(root: Path) -> dict[str, Any]:
    schema = json.loads((root / "references/foundation-contract.schema.json").read_text())
    catalog = json.loads((root / "evals/foundation-cases.json").read_text())
    if catalog.get("canonical_identity_binding") != "phase1-foundation-record-digest-v1":
        raise ValueError("fixture catalog identity binding mismatch")
    results = []
    for case in catalog["cases"]:
        instance = apply_mutations(catalog["base_fixture"], case["mutations"])
        bind_fixture_identity_digests(instance)
        instance = apply_mutations(instance, case.get("post_bind_mutations", []))
        findings = validate_instance(instance, schema)
        observed = sorted({finding.rule_id for finding in findings})
        expected = sorted(case["expected_rule_ids"])
        passed = (not findings) if case["expected"] == "pass" else all(rule in observed for rule in expected)
        results.append({"case_id": case["case_id"], "passed": passed, "expected_rule_ids": expected, "observed_rule_ids": observed})
    return {"catalog": "foundation-cases.json", "case_count": len(results), "passed_count": sum(r["passed"] for r in results), "results": results}


def validate_contract_documents(root: Path) -> dict[str, Any]:
    required = {
        "routing-contract.md": ("공통 routing 계약", "FND-ROUTE-001"),
        "gate-contract.md": ("공통 gate와 decision frontier 계약", "FND-GATE-001"),
        "authorization-contract.md": ("공통 authorization 계약", "FND-AUTH-001"),
    }
    results = []
    for name, tokens in required.items():
        path = root / "references" / name
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        expected = (
            *tokens,
            "현재 runtime에서는 사용하지 않는다.",
            "foundation-contract.schema.json",
        )
        missing = [token for token in expected if token not in text]
        results.append({"path": f"references/{name}", "passed": not missing, "missing_tokens": missing})
    return {"document_count": len(results), "passed_count": sum(r["passed"] for r in results), "results": results}


def has_symlink(root: Path) -> bool:
    return any(path.is_symlink() for path in root.rglob("*"))


def lexical_absolute(path: Path) -> Path:
    """Make a path absolute without collapsing symlink-sensitive ``..``."""
    return path if path.is_absolute() else Path.cwd() / path


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def resolve_with_provenance(
    raw_path: Path,
    *,
    forbidden_root: Path | None = None,
) -> Path:
    """Resolve every symlink hop while retaining forbidden-root provenance."""
    absolute = lexical_absolute(raw_path)
    current = Path(absolute.anchor)
    pending = list(absolute.parts[1:])
    seen_states: set[tuple[str, tuple[str, ...]]] = set()
    symlink_hops = 0
    while pending:
        state = (str(current), tuple(pending))
        if state in seen_states:
            raise ValueError(
                "FND-PROJECTION-001: symlink resolution cycle was observed"
            )
        seen_states.add(state)
        component = pending.pop(0)
        if component in {"", "."}:
            continue
        if component == "..":
            current = current.parent
            if forbidden_root is not None and path_is_within(
                current, forbidden_root
            ):
                raise ValueError(
                    "FND-PROJECTION-001: locator provenance crosses candidate repo"
                )
            continue
        current = current / component
        if forbidden_root is not None and path_is_within(current, forbidden_root):
            raise ValueError(
                "FND-PROJECTION-001: locator provenance crosses candidate repo"
            )
        try:
            info = current.lstat()
        except OSError as exc:
            raise ValueError(
                "FND-PROJECTION-001: locator provenance cannot be resolved"
            ) from exc
        if not stat.S_ISLNK(info.st_mode):
            continue
        symlink_hops += 1
        if symlink_hops > 64:
            raise ValueError(
                "FND-PROJECTION-001: symlink resolution exceeded the closed limit"
            )
        try:
            target_text = os.readlink(current)
        except OSError as exc:
            raise ValueError(
                "FND-PROJECTION-001: symlink target cannot be observed"
            ) from exc
        target = Path(target_text)
        if target.is_absolute():
            current = Path(target.anchor)
            target_parts = list(target.parts[1:])
        else:
            current = current.parent
            target_parts = list(target.parts)
        pending = target_parts + pending
    return current


def regular_file_inodes(root: Path) -> set[tuple[int, int]]:
    """Return regular-file inodes reachable through directory/file symlinks."""
    resolved_root = resolve_with_provenance(root)
    directory_queue = [resolved_root]
    visited_directory_inodes: set[tuple[int, int]] = set()
    inodes: set[tuple[int, int]] = set()
    while directory_queue:
        directory = directory_queue.pop()
        try:
            directory_info = directory.stat()
            directory_inode = (directory_info.st_dev, directory_info.st_ino)
            if directory_inode in visited_directory_inodes:
                continue
            visited_directory_inodes.add(directory_inode)
            with os.scandir(directory) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    if entry.is_symlink():
                        resolved = resolve_with_provenance(path)
                        if resolved.is_dir():
                            directory_queue.append(resolved)
                        elif resolved.is_file():
                            info = resolved.stat()
                            inodes.add((info.st_dev, info.st_ino))
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        directory_queue.append(path)
                    elif entry.is_file(follow_symlinks=False):
                        info = entry.stat(follow_symlinks=False)
                        inodes.add((info.st_dev, info.st_ino))
        except OSError as exc:
            raise ValueError(
                "FND-PROJECTION-001: reachable inode closure cannot be observed"
            ) from exc
    return inodes


def validate_source_root_descendants(
    source_root: Path,
    *,
    candidate_root: Path,
    candidate_inodes: set[tuple[int, int]],
) -> dict[str, int]:
    """Reject candidate aliases reachable anywhere below an effective skill root."""
    descendant_symlink_count = 0
    regular_descendant_count = 0
    directory_queue = [source_root]
    visited_directory_inodes: set[tuple[int, int]] = set()
    while directory_queue:
        directory = directory_queue.pop()
        try:
            directory_info = directory.stat()
            directory_inode = (directory_info.st_dev, directory_info.st_ino)
            if directory_inode in visited_directory_inodes:
                continue
            visited_directory_inodes.add(directory_inode)
            with os.scandir(directory) as entries:
                for entry in entries:
                    descendant = Path(entry.path)
                    if entry.is_symlink():
                        descendant_symlink_count += 1
                        resolved = resolve_with_provenance(
                            descendant, forbidden_root=candidate_root
                        )
                        if resolved.is_file():
                            info = resolved.stat()
                            if (info.st_dev, info.st_ino) in candidate_inodes:
                                raise ValueError(
                                    "FND-PROJECTION-001: active effective descendant "
                                    "symlink shares a candidate file inode"
                                )
                        elif resolved.is_dir():
                            directory_queue.append(resolved)
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        directory_queue.append(descendant)
                    elif entry.is_file(follow_symlinks=False):
                        regular_descendant_count += 1
                        info = entry.stat(follow_symlinks=False)
                        if (info.st_dev, info.st_ino) in candidate_inodes:
                            raise ValueError(
                                "FND-PROJECTION-001: active effective descendant "
                                "shares a candidate file inode"
                            )
        except OSError as exc:
            raise ValueError(
                "FND-PROJECTION-001: active effective descendants cannot be resolved"
            ) from exc
    return {
        "descendant_symlink_count": descendant_symlink_count,
        "regular_descendant_count": regular_descendant_count,
    }


def validate_effective_catalog_isolation(
    records: list[dict[str, str]], repo: Path
) -> dict[str, object]:
    """Reject any effective skill whose resolved source aliases the candidate."""
    candidate_root = repo.resolve()
    candidate_inodes = regular_file_inodes(candidate_root)
    source_roots: set[Path] = set()
    for record in records:
        raw_locator = record.get("source_locator")
        declared_raw_locator = record.get("declared_source_locator")
        if not isinstance(raw_locator, str) or not isinstance(
            declared_raw_locator, str
        ):
            raise ValueError(
                "FND-PROJECTION-001: effective catalog source locators are missing"
            )
        locator = Path(raw_locator)
        declared_locator = Path(declared_raw_locator)
        if not locator.is_absolute() or not declared_locator.is_absolute():
            raise ValueError(
                "FND-PROJECTION-001: active effective source locator is not absolute"
            )
        resolved = resolve_with_provenance(
            declared_locator, forbidden_root=candidate_root
        )
        recorded_resolved = resolve_with_provenance(
            locator, forbidden_root=candidate_root
        )
        if recorded_resolved != resolved:
            raise ValueError(
                "FND-PROJECTION-001: declared/resolved source locator binding mismatches"
            )
        if not resolved.is_file():
            raise ValueError(
                "FND-PROJECTION-001: active effective source locator is not a file"
            )
        try:
            resolved.relative_to(candidate_root)
        except ValueError:
            pass
        else:
            raise ValueError(
                "FND-PROJECTION-001: active effective source resolves into candidate repo"
            )
        source_roots.add(resolved.parent)
        metadata = resolved.parent / "agents" / "openai.yaml"
        declared_metadata = record.get("metadata_source_locator", "")
        declared_raw_metadata = record.get(
            "declared_metadata_source_locator", ""
        )
        if metadata.exists() or metadata.is_symlink():
            if (
                not isinstance(declared_raw_metadata, str)
                or not declared_raw_metadata
                or not Path(declared_raw_metadata).is_absolute()
            ):
                raise ValueError(
                    "FND-PROJECTION-001: effective declared metadata locator is missing"
                )
            resolved_metadata = resolve_with_provenance(
                Path(declared_raw_metadata), forbidden_root=candidate_root
            )
            sibling_metadata = resolve_with_provenance(
                metadata, forbidden_root=candidate_root
            )
            if not resolved_metadata.is_file():
                raise ValueError(
                    "FND-PROJECTION-001: effective metadata locator is not a file"
                )
            if (
                not isinstance(declared_metadata, str)
                or not declared_metadata
                or not Path(declared_metadata).is_absolute()
                or resolve_with_provenance(
                    Path(declared_metadata), forbidden_root=candidate_root
                )
                != resolved_metadata
                or sibling_metadata != resolved_metadata
            ):
                raise ValueError(
                    "FND-PROJECTION-001: effective metadata locator binding mismatches sibling"
                )
            try:
                resolved_metadata.relative_to(candidate_root)
            except ValueError:
                pass
            else:
                raise ValueError(
                    "FND-PROJECTION-001: effective metadata resolves into candidate repo"
                )
            source_roots.add(resolved_metadata.parent)
        elif declared_metadata or declared_raw_metadata:
            raise ValueError(
                "FND-PROJECTION-001: absent effective metadata has a source locator"
            )
    descendant_symlink_count = 0
    regular_descendant_count = 0
    for source_root in source_roots:
        descendant_projection = validate_source_root_descendants(
            source_root,
            candidate_root=candidate_root,
            candidate_inodes=candidate_inodes,
        )
        descendant_symlink_count += descendant_projection["descendant_symlink_count"]
        regular_descendant_count += descendant_projection["regular_descendant_count"]
    return {
        "verified": True,
        "catalog_record_count": len(records),
        "resolved_source_root_count": len(source_roots),
        "descendant_symlink_count": descendant_symlink_count,
        "regular_descendant_count": regular_descendant_count,
        "candidate_alias_count": 0,
    }


def validate_active_catalog_isolation_cases(
    repo: Path, catalog: dict[str, Any]
) -> dict[str, object]:
    """Exercise candidate source and sibling-metadata aliases."""
    results: list[dict[str, object]] = []
    candidate = (repo / "skills/research/SKILL.md").resolve()
    for case in catalog["active_catalog_isolation_cases"]:
        with tempfile.TemporaryDirectory(prefix="phase1-catalog-alias-") as raw:
            temp = Path(raw)
            mode = case["locator_mode"]
            validation_repo = repo
            if mode == "direct":
                locator = candidate
            elif mode == "symlink":
                root = temp / "symlink-skill"
                root.mkdir()
                locator = root / "SKILL.md"
                locator.symlink_to(candidate)
            elif mode == "hardlink":
                root = temp / "hardlink-skill"
                root.mkdir()
                locator = root / "SKILL.md"
                os.link(candidate, locator)
            elif mode == "fallback":
                fallback = temp / "fallback-skills"
                fallback.symlink_to(repo / "skills", target_is_directory=True)
                locator = fallback / "research" / "SKILL.md"
            elif mode == "metadata_symlink":
                root = temp / "metadata-symlink-skill"
                agents = root / "agents"
                agents.mkdir(parents=True)
                locator = root / "SKILL.md"
                shutil.copy2(candidate, locator)
                metadata = agents / "openai.yaml"
                metadata.symlink_to(
                    repo / "skills/research/agents/openai.yaml"
                )
            elif mode == "nested_reference_symlink":
                root = temp / "nested-reference-symlink-skill"
                references = root / "references"
                references.mkdir(parents=True)
                locator = root / "SKILL.md"
                shutil.copy2(candidate, locator)
                (references / "routing-contract.md").symlink_to(
                    repo
                    / "skills/develop-change/references/routing-contract.md"
                )
            elif mode == "nested_script_symlink":
                root = temp / "nested-script-symlink-skill"
                scripts = root / "scripts"
                scripts.mkdir(parents=True)
                locator = root / "SKILL.md"
                shutil.copy2(candidate, locator)
                (scripts / "runtime_projection.py").symlink_to(
                    repo / "skills/develop-change/scripts/runtime_projection.py"
                )
            elif mode == "nested_asset_hardlink":
                root = temp / "nested-asset-hardlink-skill"
                assets = root / "assets"
                assets.mkdir(parents=True)
                locator = root / "SKILL.md"
                shutil.copy2(candidate, locator)
                os.link(
                    repo / "skills/develop-change/evals/README.md",
                    assets / "fixture-readme.md",
                )
            elif mode == "nested_directory_symlink_chain":
                root = temp / "nested-directory-symlink-chain-skill"
                root.mkdir()
                locator = root / "SKILL.md"
                shutil.copy2(candidate, locator)
                shared = temp / "shared-symlink-target"
                shared.mkdir()
                (shared / "routing-contract.md").symlink_to(
                    repo
                    / "skills/develop-change/references/routing-contract.md"
                )
                (root / "references").symlink_to(
                    shared, target_is_directory=True
                )
            elif mode == "nested_directory_hardlink_chain":
                root = temp / "nested-directory-hardlink-chain-skill"
                root.mkdir()
                locator = root / "SKILL.md"
                shutil.copy2(candidate, locator)
                shared = temp / "shared-hardlink-target"
                shared.mkdir()
                os.link(
                    repo / "skills/develop-change/evals/README.md",
                    shared / "fixture-readme.md",
                )
                (root / "assets").symlink_to(
                    shared, target_is_directory=True
                )
            elif mode == "candidate_intermediate_source_symlink":
                validation_repo = temp / "candidate"
                validation_repo.mkdir()
                external = temp / "external-source"
                external.mkdir()
                shutil.copy2(candidate, external / "SKILL.md")
                (validation_repo / "bridge").symlink_to(
                    external, target_is_directory=True
                )
                locator = validation_repo / "bridge" / "SKILL.md"
            elif mode == "candidate_intermediate_metadata_symlink":
                validation_repo = temp / "candidate"
                validation_repo.mkdir()
                external = temp / "external-metadata-source"
                agents = external / "agents"
                agents.mkdir(parents=True)
                locator = external / "SKILL.md"
                shutil.copy2(candidate, locator)
                final_metadata = temp / "final-openai.yaml"
                final_metadata.write_text("policy: {}\n", encoding="utf-8")
                bridge = validation_repo / "metadata-bridge"
                bridge.symlink_to(final_metadata)
                (agents / "openai.yaml").symlink_to(bridge)
            elif mode == "candidate_intermediate_descendant_symlink":
                validation_repo = temp / "candidate"
                validation_repo.mkdir()
                root = temp / "intermediate-descendant-skill"
                root.mkdir()
                locator = root / "SKILL.md"
                shutil.copy2(candidate, locator)
                shared = temp / "intermediate-shared"
                shared.mkdir()
                (shared / "reference.md").write_text("external\n", encoding="utf-8")
                bridge = validation_repo / "descendant-bridge"
                bridge.symlink_to(shared, target_is_directory=True)
                (root / "references").symlink_to(
                    bridge, target_is_directory=True
                )
            elif mode == "candidate_linked_subtree_hardlink":
                validation_repo = temp / "candidate"
                validation_repo.mkdir()
                shared = temp / "candidate-linked-shared"
                shared.mkdir()
                shared_file = shared / "shared.md"
                shared_file.write_text("shared\n", encoding="utf-8")
                (validation_repo / "linked").symlink_to(
                    shared, target_is_directory=True
                )
                root = temp / "linked-subtree-hardlink-skill"
                assets = root / "assets"
                assets.mkdir(parents=True)
                locator = root / "SKILL.md"
                shutil.copy2(candidate, locator)
                os.link(shared_file, assets / "shared.md")
            elif mode == "descendant_symlink_cycle":
                root = temp / "descendant-cycle-skill"
                root.mkdir()
                locator = root / "SKILL.md"
                shutil.copy2(candidate, locator)
                (root / "cycle-a").symlink_to(root / "cycle-b")
                (root / "cycle-b").symlink_to(root / "cycle-a")
            elif mode == "symlink_dotdot_candidate_chain":
                validation_repo = temp / "candidate"
                candidate_subdir = validation_repo / "subdir"
                candidate_subdir.mkdir(parents=True)
                (validation_repo / "payload").write_text(
                    "candidate\n", encoding="utf-8"
                )
                helper = temp / "helper"
                helper.mkdir()
                (helper / "payload").write_text("safe\n", encoding="utf-8")
                (helper / "bridge").symlink_to(
                    candidate_subdir, target_is_directory=True
                )
                root = temp / "dotdot-chain-skill"
                root.mkdir()
                locator = root / "SKILL.md"
                shutil.copy2(candidate, locator)
                (root / "reference").symlink_to(
                    "../helper/bridge/../payload"
                )
            else:
                raise ValueError(
                    "FND-PROJECTION-001: unknown catalog isolation fixture mode"
                )
            observed_rule_ids: list[str] = []
            try:
                declared_locator = lexical_absolute(locator)
                resolved_locator = resolve_with_provenance(declared_locator)
                metadata_locator = (
                    resolved_locator.parent / "agents" / "openai.yaml"
                )
                metadata_present = (
                    metadata_locator.exists() or metadata_locator.is_symlink()
                )
                validate_effective_catalog_isolation(
                    [
                        {
                            "declared_source_locator": str(declared_locator),
                            "source_locator": str(resolved_locator),
                            "declared_metadata_source_locator": (
                                str(lexical_absolute(metadata_locator))
                                if metadata_present
                                else ""
                            ),
                            "metadata_source_locator": (
                                str(resolve_with_provenance(metadata_locator))
                                if metadata_present
                                else ""
                            ),
                        }
                    ],
                    validation_repo,
                )
            except ValueError as exc:
                match = re.match(r"(FND-[A-Z]+-[0-9]{3})", str(exc))
                if match is not None:
                    observed_rule_ids.append(match.group(1))
            expected = sorted(case["expected_rule_ids"])
            results.append(
                {
                    "case_id": case["case_id"],
                    "expected_rule_ids": expected,
                    "observed_rule_ids": sorted(observed_rule_ids),
                    "passed": expected == sorted(observed_rule_ids),
                }
            )
    return {
        "case_count": len(results),
        "passed_count": sum(bool(item["passed"]) for item in results),
        "results": results,
    }


def validate_leaf_catalog(repo: Path, catalog: dict[str, Any]) -> dict[str, Any]:
    if catalog.get("schema_version") != "phase1-leaf-only-install-cases-v1":
        raise ValueError("FND-INSTALL-001: leaf fixture catalog schema mismatch")
    expected_probe = {
        "required_for_pass": True,
        "installed_inventory": {
            "command": "plugin list --json",
            "coverage": "installed_plugins_only",
            "selector_catalog_coverage": "not_observed",
        },
        "effective_catalog": {
            "command": "debug prompt-input",
            "coverage": "model_visible_skills_instructions",
            "projection": (
                "exact_skill_id_description_declared_resolved_locator_metadata_policy"
            ),
            "candidate_alias_guard": (
                "declared_resolved_skill_metadata_descendant_graph_plus_inode_closure"
            ),
            "internal_selector_state_coverage": "not_observed",
            "expected_leaf_implicit_invocation_policy": "explicit_true",
        },
        "codex_executable_identity": {
            "fields": ["version", "path_digest", "executable_digest"],
        },
    }
    if catalog.get("discovery_probe") != expected_probe:
        raise ValueError("FND-INSTALL-005: leaf fixture discovery probe contract mismatch")
    expected_isolation_cases = [
        {
            "case_id": f"active-catalog-invalid-candidate-{mode}",
            "locator_mode": mode,
            "expected": "reject",
            "expected_rule_ids": ["FND-PROJECTION-001"],
        }
        for mode in (
            "direct",
            "symlink",
            "hardlink",
            "fallback",
            "metadata_symlink",
            "nested_reference_symlink",
            "nested_script_symlink",
            "nested_asset_hardlink",
            "nested_directory_symlink_chain",
            "nested_directory_hardlink_chain",
            "candidate_intermediate_source_symlink",
            "candidate_intermediate_metadata_symlink",
            "candidate_intermediate_descendant_symlink",
            "candidate_linked_subtree_hardlink",
            "descendant_symlink_cycle",
            "symlink_dotdot_candidate_chain",
        )
    ]
    if catalog.get("active_catalog_isolation_cases") != expected_isolation_cases:
        raise ValueError(
            "FND-PROJECTION-001: active catalog isolation fixtures are incomplete"
        )
    case_keys = {
        "case_id",
        "expected",
        "expected_rule_ids",
        "copy_mode",
        "manifest_additions",
        "add_develop_change_skill",
        "contract_mutation",
        "catalog_mutation",
        "simulate_projection_drift",
    }
    expected_case_projection = [
        (
            "leaf-only-valid-isolated-copy",
            "pass",
            (),
            "copy",
            {},
            False,
            "none",
            "none",
            False,
        ),
        (
            "leaf-only-invalid-symlink",
            "reject",
            ("FND-INSTALL-002",),
            "symlink",
            {},
            False,
            "none",
            "none",
            False,
        ),
        (
            "leaf-only-invalid-hardlink",
            "reject",
            ("FND-INSTALL-002",),
            "hardlink",
            {},
            False,
            "none",
            "none",
            False,
        ),
        (
            "leaf-only-invalid-contract-missing",
            "reject",
            ("FND-INSTALL-001",),
            "copy",
            {},
            False,
            "missing",
            "none",
            False,
        ),
        (
            "leaf-only-invalid-contract-drift",
            "reject",
            ("FND-INSTALL-001",),
            "copy",
            {},
            False,
            "drift",
            "none",
            False,
        ),
        (
            "leaf-only-invalid-schema-drift",
            "reject",
            ("FND-INSTALL-001",),
            "copy",
            {},
            False,
            "schema_drift",
            "none",
            False,
        ),
        (
            "leaf-only-invalid-fallback-root",
            "reject",
            ("FND-INSTALL-002",),
            "copy",
            {"fallback_skill_roots": ["../active-skills"]},
            False,
            "none",
            "none",
            False,
        ),
        (
            "leaf-only-invalid-develop-change-discovered",
            "reject",
            ("FND-INSTALL-003",),
            "copy",
            {},
            True,
            "none",
            "none",
            False,
        ),
        (
            "leaf-only-invalid-active-projection-drift",
            "reject",
            ("FND-INSTALL-004",),
            "copy",
            {},
            False,
            "none",
            "none",
            True,
        ),
        (
            "leaf-only-invalid-description-only-drift",
            "reject",
            ("FND-INSTALL-004",),
            "copy",
            {},
            False,
            "none",
            "description_drift",
            False,
        ),
        (
            "leaf-only-invalid-policy-only-drift",
            "reject",
            ("FND-INSTALL-004",),
            "copy",
            {},
            False,
            "none",
            "policy_drift",
            False,
        ),
    ]
    cases = catalog.get("cases")
    if not isinstance(cases, list) or any(
        not isinstance(case, dict) or set(case) != case_keys for case in cases
    ):
        raise ValueError("FND-INSTALL-001: leaf fixture case schema is not closed")
    actual_case_projection = [
        (
            case["case_id"],
            case["expected"],
            tuple(case["expected_rule_ids"]),
            case["copy_mode"],
            case["manifest_additions"],
            case["add_develop_change_skill"],
            case["contract_mutation"],
            case["catalog_mutation"],
            case["simulate_projection_drift"],
        )
        for case in cases
    ]
    if actual_case_projection != expected_case_projection:
        raise ValueError("FND-INSTALL-001: leaf fixture case set is incomplete")
    bundle = catalog.get("contract_bundle")
    if not isinstance(bundle, dict):
        raise ValueError("FND-INSTALL-001: leaf contract bundle is missing")
    schema = bundle.get("schema")
    documents = bundle.get("documents")
    expected_document_paths = [
        "authorization-contract.md",
        "gate-contract.md",
        "routing-contract.md",
    ]
    if (
        not isinstance(schema, dict)
        or schema.get("path") != "foundation-contract.schema.json"
        or not isinstance(documents, list)
        or [item.get("path") for item in documents if isinstance(item, dict)]
        != expected_document_paths
        or len(documents) != len(expected_document_paths)
    ):
        raise ValueError("FND-INSTALL-001: leaf contract bundle is not the exact schema+3MD set")
    descriptors = [schema, *documents]
    source_root = repo / "skills/develop-change/references"
    for descriptor in descriptors:
        digest = descriptor.get("sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("FND-INSTALL-001: leaf contract bundle digest is invalid")
        source = source_root / str(descriptor["path"])
        if not source.is_file() or source.is_symlink() or sha256_file(source) != digest:
            raise ValueError("FND-INSTALL-001: leaf contract source differs from catalog digest")
    manifest = catalog.get("plugin_manifest")
    if manifest != {
        "name": ISOLATED_PLUGIN,
        "version": "0.0.0-fixture",
        "skills": "./skills/",
    }:
        raise ValueError("FND-INSTALL-001: leaf fixture plugin manifest mismatch")
    return {
        "schema": dict(schema),
        "documents": [dict(item) for item in documents],
        "bundle_digest": hashlib.sha256(
            b"phase1-leaf-contract-bundle-v1\n" + canonical_bytes(bundle)
        ).hexdigest(),
    }


def _isolated_cli_context(
    temp: Path,
    *,
    active_codex_root: Path,
) -> tuple[dict[str, str], list[str], str, Path]:
    names = (
        "codex-home",
        "sqlite-home",
        "xdg-config",
        "xdg-data",
        "xdg-cache",
        "xdg-state",
        "tmp",
        "work",
    )
    for name in names:
        path = temp / name
        path.mkdir()
        os.chmod(path, 0o700)
    environment = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin:/usr/sbin:/sbin"),
        "CODEX_HOME": str(temp / "codex-home"),
        "CODEX_SQLITE_HOME": str(temp / "sqlite-home"),
        "XDG_CONFIG_HOME": str(temp / "xdg-config"),
        "XDG_DATA_HOME": str(temp / "xdg-data"),
        "XDG_CACHE_HOME": str(temp / "xdg-cache"),
        "XDG_STATE_HOME": str(temp / "xdg-state"),
        "TMPDIR": str(temp / "tmp"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "NO_COLOR": "1",
    }
    prefix: list[str] = []
    isolation_kind = "disposable_codex_and_xdg_roots"
    sandbox = shutil.which("sandbox-exec")
    if sandbox:
        profile = temp / "codex-plugin-probe.sb"
        denied = [active_codex_root, Path.home() / ".agents"]
        clauses = "\n".join(
            f"(deny file-read* file-write* (subpath {json.dumps(str(path))}))"
            for path in denied
        )
        profile.write_text(
            "(version 1)\n(allow default)\n(deny network*)\n" + clauses + "\n",
            encoding="utf-8",
        )
        prefix = [sandbox, "-f", str(profile)]
        isolation_kind = "sandboxed_disposable_codex_and_xdg_roots"
    return environment, prefix, isolation_kind, temp / "work"


def _active_inventory_guard(active_codex_root: Path) -> tuple[list[str], str]:
    """Prevent a nominal plugin-list read from writing active Codex metadata."""
    sandbox = shutil.which("sandbox-exec")
    if not sandbox:
        return [], "unfenced_active_inventory_read"
    denied = [active_codex_root, Path.home() / ".agents"]
    clauses = " ".join(
        f"(deny file-write* (subpath {json.dumps(str(path))}))" for path in denied
    )
    profile = f"(version 1) (allow default) (deny network*) {clauses}"
    return [sandbox, "-p", profile], "sandboxed_read_only_active_inventory"


def _active_effective_catalog_guard(
    active_codex_root: Path,
) -> tuple[list[str], str]:
    """Allow only the CLI's installation-ID open and documented temp writes."""
    sandbox = shutil.which("sandbox-exec")
    if not sandbox:
        return [], "unfenced_active_effective_catalog_read"
    root = active_codex_root.resolve()
    root_filter = (
        f"(deny file-write* (require-all (subpath {json.dumps(str(root))}) "
        f"(require-not (subpath {json.dumps(str(root / 'tmp'))})) "
        f"(require-not (subpath {json.dumps(str(root / '.tmp'))})) "
        f"(require-not (literal {json.dumps(str(root / 'installation_id'))}))))"
    )
    agents_filter = (
        f"(deny file-write* (subpath "
        f"{json.dumps(str((Path.home() / '.agents').resolve()))}))"
    )
    profile = f"(version 1) (allow default) {root_filter} {agents_filter}"
    return [sandbox, "-p", profile], "sandboxed_minimal_active_effective_catalog"


def _active_catalog_observer_state(active_codex_root: Path) -> dict[str, object]:
    """Content-free state of the only non-temp writable active observer file."""
    installation_id = active_codex_root / "installation_id"
    if not installation_id.exists():
        return {"state": "absent", "digest": hashlib.sha256(b"absent").hexdigest()}
    if not installation_id.is_file() or installation_id.is_symlink():
        raise ValueError(
            "FND-PROJECTION-003: active installation identity is not a regular file"
        )
    info = installation_id.stat()
    return {
        "state": "present",
        "digest": sha256_file(installation_id),
        "size": info.st_size,
        "mode": stat.S_IMODE(info.st_mode),
        "device": info.st_dev,
        "inode": info.st_ino,
        "mtime_ns": info.st_mtime_ns,
        "ctime_ns": info.st_ctime_ns,
    }


def _run_codex_json(
    command: list[str],
    *,
    environment: dict[str, str],
    command_prefix: list[str],
    cwd: Path,
) -> dict[str, Any]:
    completed = subprocess.run(
        [*command_prefix, *command],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
        cwd=cwd,
        timeout=30,
    )
    payload = json.loads(completed.stdout)
    if not isinstance(payload, dict):
        raise ValueError("Codex CLI returned a non-object JSON result")
    return payload


def detect_isolated_plugin_cli(
    codex_executable: str,
    *,
    active_codex_root: Path,
) -> dict[str, object]:
    resolved = shutil.which(codex_executable)
    if resolved is None:
        return {"supported": False, "reason_code": "codex_executable_unavailable"}
    try:
        with tempfile.TemporaryDirectory(prefix="phase1-foundation-cli-") as raw:
            temp = Path(raw)
            os.chmod(temp, 0o700)
            environment, prefix, isolation_kind, work = _isolated_cli_context(
                temp, active_codex_root=active_codex_root
            )
            completed = subprocess.run(
                [*prefix, resolved, "plugin", "--help"],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
                cwd=work,
                timeout=30,
            )
            help_text = completed.stdout
            supported = all(token in help_text for token in ("marketplace", "add", "list"))
            return {
                "supported": supported,
                "reason_code": "supported" if supported else "required_subcommands_absent",
                "isolation_kind": isolation_kind,
                "resolved_executable": resolved,
            }
    except (OSError, subprocess.SubprocessError):
        return {"supported": False, "reason_code": "plugin_help_probe_failed"}


def _build_leaf_marketplace(
    repo: Path,
    temp: Path,
    case: dict[str, Any],
    catalog: dict[str, Any],
) -> tuple[Path, Path, Path]:
    marketplace = temp / "source-marketplace"
    plugin = marketplace / "plugins" / ISOLATED_PLUGIN
    skills = plugin / "skills"
    contracts = skills / "develop-change" / "references"
    contracts.mkdir(parents=True)
    leaf_source = repo / "skills/research"
    leaf_target = skills / "research"
    if case["copy_mode"] == "symlink":
        leaf_target.symlink_to(leaf_source, target_is_directory=True)
    elif case["copy_mode"] == "hardlink":
        shutil.copytree(leaf_source, leaf_target, copy_function=os.link)
    else:
        shutil.copytree(leaf_source, leaf_target)
    source_contracts = repo / "skills/develop-change/references"
    for name in CONTRACT_ARTIFACTS:
        shutil.copy2(source_contracts / name, contracts / name)
    mutation = case.get("contract_mutation")
    if mutation == "missing":
        (contracts / "gate-contract.md").unlink()
    elif mutation == "drift":
        (contracts / "gate-contract.md").write_text("fixture drift\n", encoding="utf-8")
    elif mutation == "schema_drift":
        (contracts / "foundation-contract.schema.json").write_text(
            '{"fixture":"drift"}\n', encoding="utf-8"
        )
    manifest = {**catalog["plugin_manifest"], **case["manifest_additions"]}
    manifest_dir = plugin / ".codex-plugin"
    manifest_dir.mkdir()
    (manifest_dir / "plugin.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    if case["add_develop_change_skill"]:
        (skills / "develop-change" / "SKILL.md").write_text(
            "---\nname: develop-change\ndescription: fixture\n---\n", encoding="utf-8"
        )
    marketplace_index = marketplace / ".agents" / "plugins"
    marketplace_index.mkdir(parents=True)
    marketplace_payload = {
        "name": ISOLATED_MARKETPLACE,
        "plugins": [
            {
                "name": ISOLATED_PLUGIN,
                "source": {"source": "local", "path": f"./plugins/{ISOLATED_PLUGIN}"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Engineering",
            }
        ],
    }
    (marketplace_index / "marketplace.json").write_text(
        json.dumps(marketplace_payload, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return marketplace, plugin, leaf_source


def _validate_contract_bundle_at(
    contracts: Path,
    bundle: dict[str, Any],
    rules: set[str],
) -> None:
    descriptors = [bundle["schema"], *bundle["documents"]]
    for descriptor in descriptors:
        path = contracts / descriptor["path"]
        if (
            not path.is_file()
            or path.is_symlink()
            or sha256_file(path) != descriptor["sha256"]
        ):
            rules.add("FND-INSTALL-001")


def run_leaf_case(
    repo: Path,
    case: dict[str, Any],
    catalog: dict[str, Any],
    cli_support: dict[str, object],
    *,
    active_codex_root: Path,
) -> dict[str, object]:
    rules: set[str] = set()
    probe_status = "structural_only"
    effective_catalog_digest: str | None = None
    effective_skill_count: int | None = None
    effective_policy_observation_status: str | None = None
    isolation_kind = cli_support.get("isolation_kind", "unavailable")
    with tempfile.TemporaryDirectory(prefix="phase1-foundation-") as raw:
        temp = Path(raw)
        os.chmod(temp, 0o700)
        environment, prefix, isolation_kind, work = _isolated_cli_context(
            temp, active_codex_root=active_codex_root
        )
        marketplace, plugin, leaf_source = _build_leaf_marketplace(
            repo, temp, case, catalog
        )
        skills = plugin / "skills"
        contracts = skills / "develop-change" / "references"
        leaf_target = skills / "research"
        linked_to_source = False
        if leaf_target.exists() and not leaf_target.is_symlink():
            for candidate in leaf_target.rglob("*"):
                if candidate.is_file():
                    source_candidate = leaf_source / candidate.relative_to(leaf_target)
                    if (
                        source_candidate.is_file()
                        and candidate.stat().st_dev == source_candidate.stat().st_dev
                        and candidate.stat().st_ino == source_candidate.stat().st_ino
                    ):
                        linked_to_source = True
                        break
        if (
            has_symlink(plugin)
            or linked_to_source
            or case["manifest_additions"].get("fallback_skill_roots")
        ):
            rules.add("FND-INSTALL-002")
        if sorted(path.parent.name for path in skills.glob("*/SKILL.md")) != ["research"]:
            rules.add("FND-INSTALL-003")
        _validate_contract_bundle_at(contracts, catalog["contract_bundle"], rules)
        if case["simulate_projection_drift"]:
            rules.add("FND-INSTALL-004")
        if not cli_support.get("supported"):
            rules.add("FND-INSTALL-005")
        else:
            codex_executable = str(cli_support["resolved_executable"])
            try:
                _run_codex_json(
                    [codex_executable, "plugin", "marketplace", "add", str(marketplace), "--json"],
                    environment=environment,
                    command_prefix=prefix,
                    cwd=work,
                )
                _run_codex_json(
                    [
                        codex_executable,
                        "plugin",
                        "add",
                        f"{ISOLATED_PLUGIN}@{ISOLATED_MARKETPLACE}",
                        "--json",
                    ],
                    environment=environment,
                    command_prefix=prefix,
                    cwd=work,
                )
                records = query_installed_plugin_inventory(
                    codex_executable,
                    environment=environment,
                    command_prefix=prefix,
                    cwd=work,
                )
                expected_id = f"{ISOLATED_PLUGIN}@{ISOLATED_MARKETPLACE}"
                matches = [item for item in records if item["plugin_id"] == expected_id]
                if (
                    len(matches) != 1
                    or not matches[0]["installed"]
                    or not matches[0]["enabled"]
                ):
                    raise LeafProbeInvariantError(
                        "FND-INSTALL-003",
                        "isolated plugin record was not discovered",
                    )
                installed = (
                    Path(environment["CODEX_HOME"])
                    / "plugins"
                    / "cache"
                    / ISOLATED_MARKETPLACE
                    / ISOLATED_PLUGIN
                    / str(catalog["plugin_manifest"]["version"])
                )
                if not installed.is_dir() or installed.is_symlink():
                    raise LeafProbeInvariantError(
                        "FND-INSTALL-001",
                        "isolated installed plugin root was not materialized",
                    )
                installed_manifest = json.loads(
                    (installed / ".codex-plugin/plugin.json").read_text()
                )
                if installed_manifest != {
                    **catalog["plugin_manifest"],
                    **case["manifest_additions"],
                }:
                    rules.add("FND-INSTALL-001")
                installed_skills = installed / "skills"
                if sorted(
                    path.parent.name for path in installed_skills.glob("*/SKILL.md")
                ) != ["research"]:
                    rules.add("FND-INSTALL-003")
                _validate_contract_bundle_at(
                    installed_skills / "develop-change" / "references",
                    catalog["contract_bundle"],
                    rules,
                )
                effective_records = query_effective_skill_catalog(
                    codex_executable,
                    environment=environment,
                    command_prefix=prefix,
                    cwd=work,
                    locator_root=Path(environment["CODEX_HOME"]),
                )
                effective = snapshot_effective_skill_catalog(effective_records)
                expected_skill_id = f"{ISOLATED_PLUGIN}:research"
                expected_locator = (
                    Path("plugins")
                    / "cache"
                    / ISOLATED_MARKETPLACE
                    / ISOLATED_PLUGIN
                    / str(catalog["plugin_manifest"]["version"])
                    / "skills"
                    / "research"
                    / "SKILL.md"
                ).as_posix()
                expected_skills = [
                    item
                    for item in effective_records
                    if item["skill_id"] == expected_skill_id
                    and item["declared_source_scope"] == "bound_root_relative"
                    and item["source_scope"] == "bound_root_relative"
                    and item["source_locator"] == expected_locator
                ]
                forbidden_develop = [
                    item
                    for item in effective_records
                    if item["skill_id"] == "develop-change"
                    or item["skill_id"].endswith(":develop-change")
                ]
                active_fallback = [
                    item
                    for item in effective_records
                    if item["declared_source_scope"] != "bound_root_relative"
                    or item["source_scope"] != "bound_root_relative"
                    or (
                        item["declared_metadata_source_scope"]
                        not in {"absent", "bound_root_relative"}
                    )
                    or item["metadata_source_scope"] == "absolute"
                ]
                if len(expected_skills) != 1:
                    raise LeafProbeInvariantError(
                        "FND-INSTALL-003",
                        "isolated effective catalog omitted the exact research leaf",
                    )
                if forbidden_develop:
                    raise LeafProbeInvariantError(
                        "FND-INSTALL-003",
                        "isolated effective catalog exposed develop-change",
                    )
                if active_fallback:
                    raise LeafProbeInvariantError(
                        "FND-INSTALL-002",
                        "isolated effective catalog exposed a source fallback",
                    )
                if effective["policy_observation_status"] != "complete":
                    raise ProjectionError(
                        "FND-PROJECTION-003: isolated policy observation is incomplete"
                    )
                if (
                    expected_skills[0]["implicit_invocation_policy"]
                    != catalog["discovery_probe"]["effective_catalog"][
                        "expected_leaf_implicit_invocation_policy"
                    ]
                ):
                    raise LeafProbeInvariantError(
                        "FND-INSTALL-004",
                        "isolated research invocation policy differs from source",
                    )
                catalog_mutation = case.get("catalog_mutation", "none")
                if catalog_mutation == "description_drift":
                    skill_file = installed_skills / "research" / "SKILL.md"
                    skill_text = skill_file.read_text(encoding="utf-8")
                    if "description: " not in skill_text:
                        raise LeafProbeInvariantError(
                            "FND-INSTALL-001",
                            "fixture description cannot be mutated",
                        )
                    skill_file.write_text(
                        skill_text.replace(
                            "description: ", "description: fixture-drift ", 1
                        ),
                        encoding="utf-8",
                    )
                elif catalog_mutation == "policy_drift":
                    metadata_file = installed_skills / "research" / "agents" / "openai.yaml"
                    metadata_file.write_text(
                        metadata_file.read_text(encoding="utf-8")
                        + "\npolicy:\n  allow_implicit_invocation: false\n",
                        encoding="utf-8",
                    )
                elif catalog_mutation != "none":
                    raise LeafProbeInvariantError(
                        "FND-INSTALL-001",
                        "unknown effective catalog fixture mutation",
                    )
                after_effective_records = query_effective_skill_catalog(
                    codex_executable,
                    environment=environment,
                    command_prefix=prefix,
                    cwd=work,
                    locator_root=Path(environment["CODEX_HOME"]),
                )
                after_effective = snapshot_effective_skill_catalog(
                    after_effective_records
                )
                catalog_equal = effective == after_effective
                if catalog_mutation == "none" and not catalog_equal:
                    raise LeafProbeInvariantError(
                        "FND-INSTALL-004",
                        "isolated effective skill catalog drifted",
                    )
                if catalog_mutation != "none":
                    if catalog_equal:
                        raise LeafProbeInvariantError(
                            "FND-INSTALL-004",
                            "effective catalog mutation was not detected",
                        )
                    rules.add("FND-INSTALL-004")
                effective_catalog_digest = str(effective["catalog_digest"])
                effective_skill_count = int(effective["skill_count"])
                effective_policy_observation_status = str(
                    effective["policy_observation_status"]
                )
                probe_status = "verified_plugin_and_effective_catalog"
            except LeafProbeInvariantError as exc:
                rules.add(exc.rule_id)
                probe_status = "cli_probe_invariant_rejected"
            except (
                OSError,
                ValueError,
                ProjectionError,
                json.JSONDecodeError,
                subprocess.SubprocessError,
            ):
                rules.add("FND-INSTALL-005")
                probe_status = "cli_probe_rejected"
    return {
        "observed_rule_ids": sorted(rules),
        "probe_status": probe_status,
        "isolation_kind": isolation_kind,
        "effective_catalog_digest": effective_catalog_digest,
        "effective_skill_count": effective_skill_count,
        "effective_policy_observation_status": effective_policy_observation_status,
    }


def validate_leaf_cases(
    repo: Path,
    codex_executable: str,
    *,
    active_codex_root: Path,
    codex_executable_identity: dict[str, object],
) -> dict[str, Any]:
    catalog_path = repo / "skills/develop-change/evals/leaf-only-install-cases.json"
    catalog = json.loads(catalog_path.read_text())
    bundle = validate_leaf_catalog(repo, catalog)
    active_catalog_isolation = validate_active_catalog_isolation_cases(repo, catalog)
    cli_support = detect_isolated_plugin_cli(
        codex_executable, active_codex_root=active_codex_root
    )
    if cli_support.get("supported"):
        isolated_identity = snapshot_codex_executable_identity(
            str(cli_support["resolved_executable"])
        )
        if isolated_identity != codex_executable_identity:
            cli_support = {
                **cli_support,
                "supported": False,
                "reason_code": "codex_executable_identity_changed",
            }
    results = []
    structural_suite_passed = True
    positive_probe_passed = True
    for case in catalog["cases"]:
        outcome = run_leaf_case(
            repo,
            case,
            catalog,
            cli_support,
            active_codex_root=active_codex_root,
        )
        observed = list(outcome["observed_rule_ids"])
        structural_observed = [rule for rule in observed if rule != "FND-INSTALL-005"]
        expected = sorted(case["expected_rule_ids"])
        if case["expected"] == "pass":
            structural_passed = not structural_observed
            probe_passed = outcome["probe_status"] == "verified_plugin_and_effective_catalog"
        elif case["expected"] == "reject":
            structural_passed = bool(expected) and all(
                rule in structural_observed for rule in expected
            )
            probe_passed = True
        else:
            structural_passed = False
            probe_passed = False
        passed = structural_passed and probe_passed
        structural_suite_passed &= structural_passed
        positive_probe_passed &= probe_passed
        results.append(
            {
                "case_id": case["case_id"],
                "passed": passed,
                "structural_expectation_passed": structural_passed,
                "expected_rule_ids": expected,
                "observed_rule_ids": observed,
                "probe_status": outcome["probe_status"],
                "isolation_kind": outcome["isolation_kind"],
                "effective_catalog_digest": outcome["effective_catalog_digest"],
                "effective_skill_count": outcome["effective_skill_count"],
                "effective_policy_observation_status": outcome[
                    "effective_policy_observation_status"
                ],
            }
        )
    if not structural_suite_passed:
        evidence_status = "fail"
    elif (
        active_catalog_isolation["passed_count"]
        != active_catalog_isolation["case_count"]
    ):
        evidence_status = "fail"
    elif not positive_probe_passed:
        evidence_status = "conditional"
    else:
        evidence_status = "pass"
    return {
        "catalog": "leaf-only-install-cases.json",
        "contract_bundle": bundle,
        "active_catalog_isolation": active_catalog_isolation,
        "discovery_coverage": "installed_plugins_only",
        "installed_inventory_selector_catalog_coverage": "not_observed",
        "effective_catalog_coverage": "model_visible_skills_instructions",
        "effective_catalog_projection": (
            "exact_skill_id_description_declared_resolved_locator_metadata_policy"
        ),
        "internal_selector_state_coverage": "not_observed",
        "cli_probe": {
            "supported": bool(cli_support.get("supported")),
            "reason_code": cli_support.get("reason_code"),
            "isolation_kind": cli_support.get("isolation_kind", "unavailable"),
        },
        "evidence_status": evidence_status,
        "case_count": len(results),
        "passed_count": sum(r["passed"] for r in results),
        "structural_passed_count": sum(
            r["structural_expectation_passed"] for r in results
        ),
        "results": results,
    }


def projection_from_args(
    args: argparse.Namespace,
    inventory: dict[str, object],
    effective_catalog: dict[str, object],
    executable_identity: dict[str, object],
) -> dict[str, Any]:
    return snapshot_projection(
        active_plugin_roots=args.active_plugin_root,
        active_configs=args.active_config,
        active_hooks=args.active_hook,
        active_telemetry=args.active_telemetry,
        active_rollout=args.active_rollout,
        installed_plugin_inventory=inventory,
        effective_skill_catalog=effective_catalog,
        codex_executable_identity=executable_identity,
    )


def validate_projection_bindings(
    args: argparse.Namespace,
    repo: Path,
    inventory_records: list[dict[str, object]],
) -> dict[str, Any]:
    groups = {
        "active_plugin_root": args.active_plugin_root,
        "active_config": args.active_config,
        "active_hook": args.active_hook,
        "active_telemetry": args.active_telemetry,
        "active_rollout": args.active_rollout,
    }
    if any(len(paths) != 1 for paths in groups.values()):
        raise ValueError("FND-PROJECTION-001: v1 requires exactly one explicit path per component")
    config = Path(args.active_config[0]).expanduser().absolute()
    if config.name != "config.toml" or not config.is_file() or config.is_symlink():
        raise ValueError("FND-PROJECTION-001: active config must be the regular config.toml")
    codex_root = config.parent
    expected_codex_root = (Path.home() / ".codex").absolute()
    if codex_root != expected_codex_root:
        raise ValueError("FND-PROJECTION-001: active config must be exact ~/.codex/config.toml")
    expected_aux = {
        "active_hook": codex_root / "hooks.json",
        "active_telemetry": codex_root / "telemetry",
        "active_rollout": codex_root / "rollout",
    }
    for kind, expected in expected_aux.items():
        actual = Path(groups[kind][0]).expanduser().absolute()
        if actual != expected:
            raise ValueError(f"FND-PROJECTION-001: {kind} is not bound to the active config root")
        if actual.is_symlink() or (actual.exists() and not actual.is_file() and kind == "active_hook"):
            raise ValueError(f"FND-PROJECTION-001: {kind} is not a regular exact binding")
        if actual.is_symlink() or (actual.exists() and not actual.is_dir() and kind != "active_hook"):
            raise ValueError(f"FND-PROJECTION-001: {kind} is not a directory or explicit absent binding")
    matches = [
        item for item in inventory_records if item.get("plugin_id") == args.plugin_id
    ]
    if len(matches) != 1 or not matches[0]["installed"] or not matches[0]["enabled"]:
        raise ValueError("FND-PROJECTION-001: exact enabled plugin record was not observed")
    plugin = matches[0]
    expected_plugin = (
        codex_root
        / "plugins"
        / "cache"
        / str(plugin["marketplace_name"])
        / str(plugin["name"])
        / str(plugin["version"])
    )
    raw_plugin = Path(args.active_plugin_root[0]).expanduser().absolute()
    actual_plugin = raw_plugin.resolve()
    expected_plugin = expected_plugin.resolve()
    if actual_plugin != expected_plugin or not actual_plugin.is_dir() or raw_plugin.is_symlink():
        raise ValueError("FND-PROJECTION-001: active plugin root does not match trusted plugin inventory")
    try:
        actual_plugin.relative_to(repo)
    except ValueError:
        pass
    else:
        raise ValueError("FND-PROJECTION-001: active plugin root cannot be the candidate worktree")
    if has_symlink(actual_plugin):
        raise ValueError("FND-PROJECTION-001: active plugin projection contains a symlink")
    if regular_file_inodes(actual_plugin) & regular_file_inodes(repo):
        raise ValueError("FND-PROJECTION-001: active plugin and candidate share regular-file inodes")
    manifest = json.loads((actual_plugin / ".codex-plugin/plugin.json").read_text())
    if manifest.get("name") != plugin["name"] or manifest.get("version") != plugin["version"]:
        raise ValueError("FND-PROJECTION-001: installed plugin manifest mismatches trusted inventory")
    return {
        "verified": True,
        "plugin_id": args.plugin_id,
        "plugin_version": plugin["version"],
        "hook_binding": "exact_codex_home_hooks_json",
        "inventory_coverage": "installed_plugins_only",
        "selector_catalog_coverage": "not_observed",
        "component_path_binding_digest": hashlib.sha256(
            b"phase1-projection-binding-v1\n" + canonical_bytes(
                {kind: hashlib.sha256(str(Path(paths[0]).expanduser().absolute()).encode()).hexdigest() for kind, paths in groups.items()}
            )
        ).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[3]))
    parser.add_argument("--active-plugin-root", action="append", required=True)
    parser.add_argument("--active-config", action="append", required=True)
    parser.add_argument("--active-hook", action="append", required=True)
    parser.add_argument("--active-telemetry", action="append", required=True)
    parser.add_argument("--active-rollout", action="append", required=True)
    parser.add_argument("--plugin-id", default="skills@sonsu-skills")
    parser.add_argument("--codex-executable", default="codex")
    parser.add_argument("--output", help="write the deterministic JSON report to this path")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    root = repo / "skills/develop-change"
    active_codex_root = (Path.home() / ".codex").absolute()
    active_environment = dict(os.environ)
    active_environment["CODEX_HOME"] = str(active_codex_root)
    active_inventory_prefix, active_inventory_observer = _active_inventory_guard(
        active_codex_root
    )
    active_catalog_prefix, active_catalog_observer = _active_effective_catalog_guard(
        active_codex_root
    )
    try:
        before_executable = snapshot_codex_executable_identity(args.codex_executable)
        before_observer_state = _active_catalog_observer_state(active_codex_root)
        before_records = query_installed_plugin_inventory(
            args.codex_executable,
            environment=active_environment,
            command_prefix=active_inventory_prefix,
            cwd=repo,
        )
        before_inventory = snapshot_installed_plugin_inventory(before_records)
        before_catalog_records = query_effective_skill_catalog(
            args.codex_executable,
            environment=active_environment,
            command_prefix=active_catalog_prefix,
            cwd=repo,
        )
        before_catalog = snapshot_effective_skill_catalog(before_catalog_records)
        before_catalog_isolation = validate_effective_catalog_isolation(
            before_catalog_records, repo
        )
        before_binding = validate_projection_bindings(args, repo, before_records)
        before = projection_from_args(
            args, before_inventory, before_catalog, before_executable
        )
        documents = validate_contract_documents(root)
        foundation = validate_foundation_cases(root)
        develop_skill = validate_develop_skill(repo)
        leaf = validate_leaf_cases(
            repo,
            args.codex_executable,
            active_codex_root=active_codex_root,
            codex_executable_identity=before_executable,
        )
        after_records = query_installed_plugin_inventory(
            args.codex_executable,
            environment=active_environment,
            command_prefix=active_inventory_prefix,
            cwd=repo,
        )
        after_inventory = snapshot_installed_plugin_inventory(after_records)
        after_catalog_records = query_effective_skill_catalog(
            args.codex_executable,
            environment=active_environment,
            command_prefix=active_catalog_prefix,
            cwd=repo,
        )
        after_catalog = snapshot_effective_skill_catalog(after_catalog_records)
        after_catalog_isolation = validate_effective_catalog_isolation(
            after_catalog_records, repo
        )
        after_executable = snapshot_codex_executable_identity(args.codex_executable)
        after_observer_state = _active_catalog_observer_state(active_codex_root)
        after_binding = validate_projection_bindings(args, repo, after_records)
        after = projection_from_args(
            args, after_inventory, after_catalog, after_executable
        )
    except (
        OSError,
        ValueError,
        ProjectionError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as exc:
        error = str(exc)
        rule_match = re.match(r"(FND-[A-Z]+-[0-9]{3})", error)
        emit_report(
            {
                "schema_version": "phase1-foundation-validation-report-v1",
                "validator": {
                    "id": VALIDATOR_ID,
                    "revision": VALIDATOR_REVISION,
                },
                "status": "fail",
                "error_rule_id": (
                    rule_match.group(1)
                    if rule_match is not None
                    else "FND-VALIDATOR-UNEXPECTED"
                ),
            },
            args.output,
        )
        return 1
    projection_equal = before["projection_digest"] == after["projection_digest"]
    inventory_equal = (
        before_inventory["inventory_digest"] == after_inventory["inventory_digest"]
        and before_inventory["plugin_count"] == after_inventory["plugin_count"]
    )
    catalog_equal = (
        before_catalog["catalog_digest"] == after_catalog["catalog_digest"]
        and before_catalog["skill_count"] == after_catalog["skill_count"]
    )
    catalog_policy_complete = (
        before_catalog["policy_observation_status"] == "complete"
        and after_catalog["policy_observation_status"] == "complete"
    )
    executable_equal = before_executable == after_executable
    observer_state_equal = before_observer_state == after_observer_state
    catalog_isolation_equal = before_catalog_isolation == after_catalog_isolation
    hard_passed = (
        foundation["passed_count"] == foundation["case_count"]
        and develop_skill["status"] == "pass"
        and documents["passed_count"] == documents["document_count"]
        and leaf["evidence_status"] != "fail"
        and projection_equal
        and inventory_equal
        and catalog_equal
        and executable_equal
        and observer_state_equal
        and catalog_isolation_equal
        and before_binding == after_binding
    )
    status = (
        "fail"
        if not hard_passed
        else "conditional"
        if (
            leaf["evidence_status"] == "conditional"
            or active_inventory_observer == "unfenced_active_inventory_read"
            or active_catalog_observer == "unfenced_active_effective_catalog_read"
            or not catalog_policy_complete
        )
        else "pass"
    )
    result = {
        "schema_version": "phase1-foundation-validation-report-v1",
        "validator": {"id": VALIDATOR_ID, "revision": VALIDATOR_REVISION},
        "status": status,
        "documents": documents,
        "foundation": foundation,
        "develop_skill": develop_skill,
        "leaf_only_install": leaf,
        "runtime_projection": {
            "schema_version": before["schema_version"],
            "before_digest": before["projection_digest"],
            "after_digest": after["projection_digest"],
            "equal": projection_equal,
            "components": before["components"],
            "binding": before_binding,
            "installed_plugin_inventory": {
                "coverage": "installed_plugins_only",
                "selector_catalog_coverage": "not_observed",
                "observer_kind": active_inventory_observer,
                "before_digest": before_inventory["inventory_digest"],
                "after_digest": after_inventory["inventory_digest"],
                "before_count": before_inventory["plugin_count"],
                "after_count": after_inventory["plugin_count"],
                "equal": inventory_equal,
            },
            "effective_skill_catalog": {
                "coverage": "model_visible_skills_instructions",
                "internal_selector_state_coverage": "not_observed",
                "projection": (
                    "exact_skill_id_description_declared_resolved_locator_"
                    "metadata_policy_digest"
                ),
                "policy_observation_status": before_catalog[
                    "policy_observation_status"
                ],
                "observer_kind": active_catalog_observer,
                "before_digest": before_catalog["catalog_digest"],
                "after_digest": after_catalog["catalog_digest"],
                "before_count": before_catalog["skill_count"],
                "after_count": after_catalog["skill_count"],
                "equal": catalog_equal,
                "writable_non_temp_observer_state_equal": observer_state_equal,
                "candidate_source_isolation": before_catalog_isolation,
                "candidate_source_isolation_equal": catalog_isolation_equal,
            },
            "codex_executable_identity": {
                "version": before_executable["version"],
                "path_digest": before_executable["path_digest"],
                "executable_digest": before_executable["executable_digest"],
                "after_equal": executable_equal,
            },
        },
    }
    emit_report(result, args.output)
    return 0 if status == "pass" else 2 if status == "conditional" else 1


if __name__ == "__main__":
    raise SystemExit(main())
