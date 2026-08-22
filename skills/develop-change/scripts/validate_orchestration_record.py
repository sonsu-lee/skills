#!/usr/bin/env python3
"""Validate cross-field semantics for a develop-change orchestration record."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any


VALIDATOR_ID = "develop-change-orchestration-record-validator"
VALIDATOR_REVISION = 5
SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = SKILL_ROOT / "references" / "orchestration-contract.schema.json"
FOUNDATION_SCHEMA_PATH = SKILL_ROOT / "references" / "foundation-contract.schema.json"
HANDOFF_SNAPSHOT_FIELDS = (
    "objective",
    "scope",
    "decisions",
    "effect_binding",
    "profile",
    "foundation_binding",
    "skill_resolution",
    "authorization",
    "verification",
)
ROUTE_SEQUENCE = (
    "understand",
    "shape",
    "decide",
    "design",
    "diagnose",
    "change",
    "verify",
    "deliver",
    "operate",
    "evolve",
)
ROUTE_POSITION = {route: index for index, route in enumerate(ROUTE_SEQUENCE)}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def record_digest_payload(value: Any) -> Any:
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


def authorization_record_digest(record: dict[str, Any]) -> str:
    return hashlib.sha256(
        b"phase1-foundation-authorization-record-v1\n"
        + canonical_bytes(record_digest_payload(record))
    ).hexdigest()


def current_scope_fingerprint(scope: dict[str, Any]) -> str:
    payload = {
        "include": scope.get("include"),
        "exclude": scope.get("exclude"),
    }
    return hashlib.sha256(b"develop-change-scope-v1\n" + canonical_bytes(payload)).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def string_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}


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


def resolve_schema_ref(
    ref: str,
    root: dict[str, Any],
    registry: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    base, separator, fragment = ref.partition("#")
    target_root = registry.get(base) if base else root
    if target_root is None:
        raise ValueError(f"unknown schema reference: {ref}")
    target: Any = target_root
    if separator and fragment:
        if not fragment.startswith("/"):
            raise ValueError(f"unsupported schema fragment: {ref}")
        for token in fragment[1:].split("/"):
            target = target[decode_pointer_token(token)]
    if not isinstance(target, dict):
        raise ValueError(f"schema reference is not an object: {ref}")
    return target, target_root


def validate_schema_node(
    value: Any,
    node: dict[str, Any],
    root: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    path: str,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def add(message: str, finding_path: str = path) -> None:
        findings.append(
            {"rule_id": "ORCH-SCHEMA", "path": finding_path or "/", "message": message}
        )

    if "$ref" in node:
        target, target_root = resolve_schema_ref(node["$ref"], root, registry)
        return validate_schema_node(value, target, target_root, registry, path)

    for constraint in node.get("allOf", []):
        findings.extend(validate_schema_node(value, constraint, root, registry, path))

    if "if" in node:
        condition = validate_schema_node(value, node["if"], root, registry, path)
        branch = node.get("then") if not condition else node.get("else")
        if branch is not None:
            findings.extend(validate_schema_node(value, branch, root, registry, path))

    if "oneOf" in node:
        matches = sum(
            not validate_schema_node(value, branch, root, registry, path)
            for branch in node["oneOf"]
        )
        if matches != 1:
            add("value must match exactly one schema branch")
        return findings

    if "const" in node and value != node["const"]:
        add(f"expected constant {node['const']!r}")
    if "enum" in node and value not in node["enum"]:
        add("value is outside the closed enum")

    expected = node.get("type")
    if expected is not None:
        types = expected if isinstance(expected, list) else [expected]
        if not any(matches_type(value, item) for item in types):
            add(f"expected type {types}")
            return findings

    if isinstance(value, str):
        if len(value) < node.get("minLength", 0):
            add("string is shorter than minLength")
        if "pattern" in node and not re.fullmatch(node["pattern"], value):
            add("string does not match pattern")
    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in node and value < node["minimum"]:
            add("integer is below minimum")
        if "maximum" in node and value > node["maximum"]:
            add("integer is above maximum")

    if isinstance(value, dict):
        required = set(node.get("required", []))
        for key in sorted(required - set(value)):
            add("required field is missing", f"{path}/{key}")
        properties = node.get("properties", {})
        if node.get("additionalProperties") is False:
            for key in sorted(set(value) - set(properties)):
                add("unknown field", f"{path}/{key}")
        for key, child in properties.items():
            if key in value:
                findings.extend(
                    validate_schema_node(
                        value[key], child, root, registry, f"{path}/{key}"
                    )
                )

    if isinstance(value, list):
        if len(value) < node.get("minItems", 0):
            add("array is shorter than minItems")
        if "maxItems" in node and len(value) > node["maxItems"]:
            add("array is longer than maxItems")
        if node.get("uniqueItems"):
            encoded = [
                json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                for item in value
            ]
            if len(encoded) != len(set(encoded)):
                add("array items must be unique")
        if "items" in node:
            for index, item in enumerate(value):
                findings.extend(
                    validate_schema_node(
                        item, node["items"], root, registry, f"{path}/{index}"
                    )
                )
        if "contains" in node and not any(
            not validate_schema_node(item, node["contains"], root, registry, path)
            for item in value
        ):
            add("array does not contain a required item")
    return findings


def validate_schema(record: dict[str, Any]) -> list[dict[str, str]]:
    schema = load_json(SCHEMA_PATH)
    foundation_schema = load_json(FOUNDATION_SCHEMA_PATH)
    registry = {
        schema["$id"]: schema,
        foundation_schema["$id"]: foundation_schema,
    }
    return validate_schema_node(record, schema, schema, registry, "")


def validate_record(record: dict[str, Any]) -> list[dict[str, str]]:
    """Return stable rule/path findings not expressible solely by field schemas."""
    findings: list[dict[str, str]] = []

    def add(rule_id: str, path: str, message: str) -> None:
        findings.append({"rule_id": rule_id, "path": path, "message": message})

    primary_route = record.get("primary_route")
    route_plan = record.get("route_plan")
    if not isinstance(route_plan, list) or primary_route not in route_plan:
        add("ORCH-002", "/route_plan", "primary_route must be present in route_plan")
    elif any(route not in ROUTE_POSITION for route in route_plan) or any(
        ROUTE_POSITION[earlier] >= ROUTE_POSITION[later]
        for earlier, later in zip(route_plan, route_plan[1:])
    ):
        add("ORCH-002", "/route_plan", "route_plan must follow canonical route order")

    handoff = record.get("handoff") if isinstance(record.get("handoff"), dict) else {}
    completed_phase = handoff.get("completed_phase")
    completed_phase_valid = (
        isinstance(route_plan, list)
        and primary_route in route_plan
        and (
            (completed_phase is None and route_plan.index(primary_route) == 0)
            or (
                completed_phase in route_plan
                and route_plan.index(completed_phase) <= route_plan.index(primary_route)
            )
        )
    )
    if not completed_phase_valid:
        add(
            "HANDOFF-001",
            "/handoff/completed_phase",
            "completed_phase must be null before the first route or a planned route not later than primary_route",
        )

    gate = record.get("gate") if isinstance(record.get("gate"), dict) else {}
    gate_result = gate.get("result")
    assumptions = gate.get("assumptions")
    assumptions_valid = (
        isinstance(assumptions, list)
        and bool(assumptions)
        and all(
            isinstance(item, dict)
            and isinstance(item.get("summary"), str)
            and bool(item["summary"])
            and isinstance(item.get("basis_refs"), list)
            and bool(item["basis_refs"])
            and all(isinstance(ref, str) and ref for ref in item["basis_refs"])
            and isinstance(item.get("validation"), str)
            and bool(item["validation"])
            for item in assumptions
        )
    )
    if gate_result == "conditional" and not assumptions_valid:
        add(
            "FND-GATE-002",
            "/gate/assumptions",
            "conditional gate requires supported, verifiable assumptions",
        )
    if gate_result != "conditional" and assumptions:
        add(
            "FND-GATE-002",
            "/gate/assumptions",
            "assumptions are only valid for a conditional gate",
        )
    unfinished_plan = completed_phase_valid and (
        completed_phase is None
        or route_plan.index(completed_phase) < len(route_plan) - 1
    )
    if (gate_result == "blocked" or unfinished_plan) and not (
        isinstance(handoff.get("next_action"), str) and handoff["next_action"]
    ):
        add(
            "HANDOFF-001",
            "/handoff/next_action",
            "blocked or unfinished handoff requires a non-empty next_action",
        )

    profile = record.get("profile") if isinstance(record.get("profile"), dict) else {}
    if profile.get("confidence") == "provisional":
        if primary_route == "change" and gate_result != "blocked":
            add(
                "FND-PROFILE-004",
                "/gate/result",
                "provisional profile cannot cross the change side-effect checkpoint",
            )
        elif gate_result == "pass":
            add(
                "FND-PROFILE-001",
                "/gate/result",
                "provisional profile cannot have a pass gate",
            )

    resolution = (
        record.get("skill_resolution")
        if isinstance(record.get("skill_resolution"), dict)
        else {}
    )
    if resolution.get("status") == "blocked" and gate_result != "blocked":
        add(
            "ORCH-002",
            "/gate/result",
            "blocked skill resolution requires a blocked gate",
        )

    decisions = resolution.get("decisions")
    if isinstance(decisions, list):
        skill_ids = [
            item.get("skill_id")
            for item in decisions
            if isinstance(item, dict) and isinstance(item.get("skill_id"), str)
        ]
        duplicate_ids = sorted(
            {skill_id for skill_id in skill_ids if skill_ids.count(skill_id) > 1}
        )
        if duplicate_ids:
            add(
                "RESOLVE-004",
                "/skill_resolution/decisions",
                f"skill_id must be unique: {','.join(str(item) for item in duplicate_ids)}",
            )
        active_by_responsibility: dict[Any, list[dict[str, Any]]] = {}
        active_skill_ids: set[str] = set()
        for item in decisions:
            if not isinstance(item, dict) or item.get("decision") not in {
                "selected",
                "composed",
            }:
                continue
            if isinstance(item.get("skill_id"), str):
                active_skill_ids.add(item["skill_id"])
            active_by_responsibility.setdefault(item.get("responsibility"), []).append(item)
            if primary_route not in string_set(item.get("applies_to_routes")):
                add(
                    "RESOLVE-003",
                    "/skill_resolution/decisions",
                    f"active skill must apply to primary_route: {item.get('skill_id')}",
                )
        for responsibility, active in active_by_responsibility.items():
            if len(active) > 1 and any(item.get("decision") != "composed" for item in active):
                add(
                    "RESOLVE-005",
                    "/skill_resolution/decisions",
                    f"multiple active skills for {responsibility!r} must be composed",
                )
        planned_capabilities = resolution.get("planned_capabilities")
        planned_ids = {
            item.get("capability_id")
            for item in planned_capabilities
            if isinstance(item, dict) and isinstance(item.get("capability_id"), str)
        } if isinstance(planned_capabilities, list) else set()
        selected_planned_ids = sorted(active_skill_ids & planned_ids)
        if selected_planned_ids:
            add(
                "RESOLVE-007",
                "/skill_resolution/decisions",
                "planned capability cannot be selected as a skill: "
                + ",".join(selected_planned_ids),
            )
        rejected_user_named = any(
            isinstance(item, dict)
            and item.get("source") == "user_named"
            and item.get("decision") == "rejected"
            for item in decisions
        )
        fallback = resolution.get("fallback")
        if (
            rejected_user_named
            and not active_skill_ids
            and resolution.get("status") != "blocked"
            and not (isinstance(fallback, str) and fallback)
        ):
            add(
                "RESOLVE-005",
                "/skill_resolution/fallback",
                "rejected user-named skill requires an active replacement, fallback, or blocked resolution",
            )

    scope = record.get("scope") if isinstance(record.get("scope"), dict) else {}
    included = string_set(scope.get("include"))
    excluded = string_set(scope.get("exclude"))
    if included & excluded:
        add("ORCH-001", "/scope", "scope include and exclude must be disjoint")

    verification = (
        record.get("verification")
        if isinstance(record.get("verification"), dict)
        else {}
    )
    passed = string_set(verification.get("passed"))
    failed = string_set(verification.get("failed"))
    not_run = string_set(verification.get("not_run"))
    if (passed & failed) or (passed & not_run) or (failed & not_run):
        add(
            "HANDOFF-004",
            "/verification",
            "verification result sets must be mutually exclusive",
        )

    authorization = record.get("authorization")
    if isinstance(authorization, list):
        binding_keys: list[tuple[Any, Any, Any, Any]] = []
        for item in authorization:
            if not isinstance(item, dict):
                continue
            binding_key = (
                item.get("capability"),
                item.get("target_fingerprint"),
                item.get("scope_fingerprint"),
                item.get("basis_fingerprint"),
            )
            if all(isinstance(value, str) for value in binding_key):
                binding_keys.append(binding_key)
        if len(binding_keys) != len(set(binding_keys)):
            add(
                "FND-AUTH-001",
                "/authorization",
                "authorization binding must have one current lineage leaf",
            )
        effect_binding = (
            record.get("effect_binding")
            if isinstance(record.get("effect_binding"), dict)
            else {}
        )
        foundation_binding = (
            record.get("foundation_binding")
            if isinstance(record.get("foundation_binding"), dict)
            else {}
        )
        authorization_record = foundation_binding.get("authorization_record")
        authorization_evaluation = foundation_binding.get(
            "authorization_evaluation"
        )
        expected_scope_fingerprint = current_scope_fingerprint(scope)

        def matches_current_local_change(item: Any) -> bool:
            if not (
                isinstance(item, dict)
                and isinstance(authorization_record, dict)
                and isinstance(authorization_evaluation, dict)
            ):
                return False
            authorization_ref = item.get("authorization_ref")
            expected_digest = authorization_record_digest(authorization_record)
            record_matches_effect = (
                authorization_record.get("logical_task_id")
                == effect_binding.get("logical_task_id")
                and authorization_record.get("capability") == "local_change"
                and authorization_record.get("target_fingerprint")
                == effect_binding.get("target_fingerprint")
                and authorization_record.get("scope_fingerprint")
                == expected_scope_fingerprint
                and authorization_record.get("basis_fingerprint")
                == effect_binding.get("basis_fingerprint")
                and authorization_record.get("status") == "granted"
                and authorization_record.get("runtime_eligible") is True
            )
            summary_matches_record = (
                isinstance(authorization_ref, dict)
                and authorization_ref.get("id")
                == authorization_record.get("authorization_id")
                and authorization_ref.get("revision")
                == authorization_record.get("revision")
                and authorization_ref.get("digest") == expected_digest
                and item.get("capability") == authorization_record.get("capability")
                and item.get("target_fingerprint")
                == authorization_record.get("target_fingerprint")
                and item.get("scope_fingerprint")
                == authorization_record.get("scope_fingerprint")
                and item.get("basis_fingerprint")
                == authorization_record.get("basis_fingerprint")
                and item.get("status") == authorization_record.get("status")
                and item.get("runtime_eligible")
                == authorization_record.get("runtime_eligible")
            )
            evaluation_matches_record = (
                authorization_evaluation.get("required_capability")
                == authorization_record.get("capability")
                and authorization_evaluation.get("target_fingerprint")
                == authorization_record.get("target_fingerprint")
                and authorization_evaluation.get("scope_fingerprint")
                == authorization_record.get("scope_fingerprint")
                and authorization_evaluation.get("basis_fingerprint")
                == authorization_record.get("basis_fingerprint")
                and authorization_evaluation.get("selected_authorization_id")
                == authorization_record.get("authorization_id")
                and authorization_evaluation.get("side_effect_intent") == "dependent"
                and authorization_evaluation.get("derived_result") == "allowed"
                and authorization_evaluation.get("next_action") == "continue"
                and authorization_evaluation.get("dependent_side_effect_count") == 1
            )
            return record_matches_effect and summary_matches_record and evaluation_matches_record

        local_change_granted = any(
            matches_current_local_change(item) for item in authorization
        )
        if (
            primary_route == "change"
            and gate_result != "blocked"
            and not local_change_granted
        ):
            add(
                "FND-AUTH-005",
                "/authorization",
                "change route requires a current runtime-eligible local_change grant or a blocked gate",
            )

    for field in HANDOFF_SNAPSHOT_FIELDS:
        if handoff.get(field) != record.get(field):
            add(
                "HANDOFF-002",
                f"/handoff/{field}",
                f"handoff {field} must equal the current top-level state",
            )
    if handoff.get("blockers") != gate.get("blockers"):
        add(
            "HANDOFF-002",
            "/handoff/blockers",
            "handoff blockers must equal the current gate blockers",
        )

    return findings


def decode_pointer_token(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def apply_mutation(record: dict[str, Any], mutation: dict[str, Any]) -> None:
    path = mutation.get("path")
    if not isinstance(path, str) or not path.startswith("/"):
        raise ValueError("mutation path must be a JSON pointer")
    tokens = [decode_pointer_token(token) for token in path[1:].split("/")]
    parent: Any = record
    for token in tokens[:-1]:
        parent = parent[int(token)] if isinstance(parent, list) else parent[token]
    key = tokens[-1]
    operation = mutation.get("op")
    if operation == "replace":
        if isinstance(parent, list):
            parent[int(key)] = mutation.get("value")
        else:
            parent[key] = mutation.get("value")
    elif operation == "append":
        target = parent[int(key)] if isinstance(parent, list) else parent[key]
        if not isinstance(target, list):
            raise ValueError("append mutation target must be an array")
        target.append(mutation.get("value"))
    elif operation == "remove":
        if isinstance(parent, list):
            del parent[int(key)]
        else:
            del parent[key]
    else:
        raise ValueError(f"unsupported mutation operation: {operation!r}")


def run_cases(path: Path) -> dict[str, Any]:
    catalog = load_json(path)
    if catalog.get("schema_version") != "develop-change-orchestration-record-evals-v1":
        raise ValueError("unexpected orchestration record catalog version")
    base_record = catalog.get("base_record")
    if not isinstance(base_record, dict):
        raise ValueError("base_record must be an object")
    cases = catalog.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a non-empty array")
    case_ids = [case.get("id") for case in cases if isinstance(case, dict)]
    if (
        len(case_ids) != len(cases)
        or any(not isinstance(case_id, str) or not case_id for case_id in case_ids)
        or len(case_ids) != len(set(case_ids))
    ):
        raise ValueError("case ids must be non-empty and unique")
    results: list[dict[str, Any]] = []
    for case in cases:
        record = copy.deepcopy(base_record)
        for mutation in case.get("mutations", []):
            apply_mutation(record, mutation)
        schema_actual = not validate_schema(record)
        schema_expected = case.get("expected_schema_valid", True)
        actual_rules = sorted({item["rule_id"] for item in validate_record(record)})
        expected_rules = sorted(case.get("expected_rules", []))
        passed = actual_rules == expected_rules and schema_actual is schema_expected
        results.append(
            {
                "id": case.get("id"),
                "status": "pass" if passed else "fail",
                "expected_schema_valid": schema_expected,
                "actual_schema_valid": schema_actual,
                "expected_rules": expected_rules,
                "actual_rules": actual_rules,
            }
        )
    passed = sum(result["status"] == "pass" for result in results)
    return {
        "validator": {"id": VALIDATOR_ID, "revision": VALIDATOR_REVISION},
        "status": "pass" if passed == len(results) else "fail",
        "case_count": len(results),
        "passed_count": passed,
        "cases": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="orchestration record JSON")
    source.add_argument("--cases", type=Path, help="semantic regression catalog JSON")
    args = parser.parse_args()

    if args.cases is not None:
        result = run_cases(args.cases)
    else:
        record = load_json(args.input)
        if not isinstance(record, dict):
            raise SystemExit("input must be a JSON object")
        schema_findings = validate_schema(record)
        semantic_findings = validate_record(record)
        result = {
            "validator": {"id": VALIDATOR_ID, "revision": VALIDATOR_REVISION},
            "status": "pass" if not schema_findings and not semantic_findings else "fail",
            "schema_findings": schema_findings,
            "semantic_findings": semantic_findings,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
