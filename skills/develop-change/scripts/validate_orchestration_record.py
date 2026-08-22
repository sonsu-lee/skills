#!/usr/bin/env python3
"""Validate cross-field semantics for a develop-change orchestration record."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any


SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from validate_foundation import validate_instance as validate_foundation_instance
from runtime_projection import (
    ProjectionError,
    query_effective_skill_catalog,
    snapshot_effective_skill_catalog,
)


VALIDATOR_ID = "develop-change-orchestration-record-validator"
VALIDATOR_REVISION = 22
SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[1]
SCHEMA_PATH = SKILL_ROOT / "references" / "orchestration-contract.schema.json"
FOUNDATION_SCHEMA_PATH = SKILL_ROOT / "references" / "foundation-contract.schema.json"
HANDOFF_SNAPSHOT_FIELDS = (
    "objective",
    "scope",
    "primary_route",
    "route_plan",
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
EFFECT_CAPABILITIES_BY_ROUTE = {
    "design": {"working_artifact_write", "temporary_work_state"},
    "change": {
        "local_change",
        "durable_document_write",
        "durable_document_content",
    },
    "deliver": {
        "branch_create",
        "branch_switch",
        "stage",
        "commit",
        "push",
        "pr_create",
        "merge",
        "rebase",
        "history_rewrite",
    },
    "operate": {"external_write"},
    "evolve": {"local_change"},
}
SIDE_EFFECT_ROUTES = {"change", "deliver", "operate", "evolve"}


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


FOUNDATION_RECORD_DOMAINS = {
    "routing": b"phase1-foundation-routing-record-v1\n",
    "gate": b"phase1-foundation-gate-record-v1\n",
    "authorization": b"phase1-foundation-authorization-record-v1\n",
    "frontier": b"phase1-foundation-frontier-record-v1\n",
    "frontier_unit": b"phase1-foundation-frontier-unit-record-v1\n",
}


def foundation_record_digest(kind: str, record: dict[str, Any]) -> str:
    return hashlib.sha256(
        FOUNDATION_RECORD_DOMAINS[kind] + canonical_bytes(record_digest_payload(record))
    ).hexdigest()


def authorization_record_digest(record: dict[str, Any]) -> str:
    return foundation_record_digest("authorization", record)


def identity_ref_matches(
    reference: Any,
    record: Any,
    *,
    kind: str,
    id_field: str,
) -> bool:
    return (
        isinstance(reference, dict)
        and isinstance(record, dict)
        and reference.get("id") == record.get(id_field)
        and reference.get("revision") == record.get("revision")
        and reference.get("digest") == foundation_record_digest(kind, record)
    )


def current_scope_fingerprint(scope: dict[str, Any]) -> str:
    payload = {
        "include": scope.get("include"),
        "exclude": scope.get("exclude"),
    }
    return hashlib.sha256(b"develop-change-scope-v1\n" + canonical_bytes(payload)).hexdigest()


def objective_logical_task_id(objective: dict[str, Any]) -> str:
    digest = hashlib.sha256(
        b"develop-change-objective-v1\n" + canonical_bytes(objective)
    ).hexdigest()
    return f"task.objective.{digest}"


def has_active_skill_decision(record: dict[str, Any]) -> bool:
    resolution = record.get("skill_resolution")
    decisions = resolution.get("decisions") if isinstance(resolution, dict) else None
    return isinstance(decisions, list) and any(
        isinstance(item, dict)
        and item.get("decision") in {"selected", "composed"}
        for item in decisions
    )


def active_skill_source_matches(
    item: dict[str, Any],
    effective_skill_catalog: list[dict[str, str]] | None,
    *,
    source_root: Path = REPO_ROOT,
) -> bool:
    provenance = item.get("provenance")
    if not isinstance(provenance, dict):
        return False
    locator = provenance.get("locator")
    version = provenance.get("version")
    content_digest = provenance.get("content_digest")
    if not (
        isinstance(locator, str)
        and locator
        and isinstance(version, str)
        and version
        and isinstance(content_digest, str)
        and re.fullmatch(r"[0-9a-f]{64}", content_digest)
    ):
        return False
    declared = Path(locator)
    if declared.is_absolute():
        source_path = declared
    else:
        if any(part in {"", ".", ".."} for part in declared.parts):
            return False
        source_path = source_root / declared
    try:
        resolved = source_path.resolve(strict=True)
    except (OSError, RuntimeError):
        return False
    if not resolved.is_file() or resolved.name != "SKILL.md":
        return False
    if not declared.is_absolute():
        try:
            resolved.relative_to(source_root.resolve())
        except ValueError:
            return False
    try:
        source_bytes = resolved.read_bytes()
    except OSError:
        return False
    actual_digest = hashlib.sha256(source_bytes).hexdigest()
    if content_digest != actual_digest:
        return False
    try:
        source_text = source_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return False
    frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", source_text, re.S)
    if frontmatter is None:
        return False
    name_match = re.search(
        r"^name:\s*['\"]?([a-z0-9]+(?:-[a-z0-9]+)*)['\"]?\s*$",
        frontmatter.group(1),
        re.M,
    )
    if name_match is None:
        return False
    skill_name = name_match.group(1)
    plugin_identity: tuple[str, str] | None = None
    for parent in resolved.parents:
        manifest_path = parent / ".codex-plugin" / "plugin.json"
        if not manifest_path.is_file():
            continue
        try:
            manifest = load_json(manifest_path)
        except (OSError, UnicodeError, ValueError):
            return False
        plugin_name = manifest.get("name") if isinstance(manifest, dict) else None
        plugin_version = manifest.get("version") if isinstance(manifest, dict) else None
        if not (
            isinstance(plugin_name, str)
            and plugin_name
            and isinstance(plugin_version, str)
            and plugin_version
        ):
            return False
        plugin_identity = (plugin_name, plugin_version)
        break
    expected_skill_id = (
        f"{plugin_identity[0]}:{skill_name}" if plugin_identity else skill_name
    )
    expected_versions = {f"content-sha256:{actual_digest}"}
    if plugin_identity:
        expected_versions.add(plugin_identity[1])
    if item.get("skill_id") != expected_skill_id or version not in expected_versions:
        return False
    if not isinstance(effective_skill_catalog, list):
        return False
    catalog_matches = []
    for entry in effective_skill_catalog:
        if not isinstance(entry, dict) or entry.get("skill_id") != expected_skill_id:
            continue
        raw_locators = {
            entry.get("declared_source_locator"),
            entry.get("source_locator"),
        }
        for raw_locator in raw_locators:
            if not isinstance(raw_locator, str) or not raw_locator:
                continue
            catalog_path = Path(raw_locator)
            if not catalog_path.is_absolute():
                catalog_path = source_root / catalog_path
            try:
                if catalog_path.resolve(strict=True) == resolved:
                    catalog_matches.append(entry)
                    break
            except (OSError, RuntimeError):
                continue
    return len(catalog_matches) == 1


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


def validate_record(
    record: dict[str, Any],
    *,
    allow_fixture_authorization: bool = False,
    effective_skill_catalog: list[dict[str, str]] | None = None,
    source_root: Path = REPO_ROOT,
) -> list[dict[str, str]]:
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
    completed_phase_valid = False
    if isinstance(route_plan, list) and primary_route in route_plan:
        if completed_phase is None:
            completed_phase_valid = route_plan.index(primary_route) == 0
        elif completed_phase in route_plan:
            completed_index = route_plan.index(completed_phase)
            completed_phase_valid = (
                primary_route == completed_phase
                if completed_index == len(route_plan) - 1
                else primary_route == route_plan[completed_index + 1]
            )
    if not completed_phase_valid:
        add(
            "HANDOFF-001",
            "/handoff/completed_phase",
            "primary_route must be the first route, the route after completed_phase, or the completed terminal route",
        )

    gate = record.get("gate") if isinstance(record.get("gate"), dict) else {}
    gate_result = gate.get("result")
    foundation_binding = (
        record.get("foundation_binding")
        if isinstance(record.get("foundation_binding"), dict)
        else {}
    )
    gate_record = foundation_binding.get("gate_record")
    foundation_blocker = (
        gate_record.get("blocker") if isinstance(gate_record, dict) else None
    )
    expected_blockers = [] if foundation_blocker == "none" else [foundation_blocker]
    if gate.get("blockers") != expected_blockers:
        add(
            "FND-GATE-002",
            "/gate/blockers",
            "top-level blockers must be the exact foundation gate blocker projection",
        )
    assumption_effect = (
        gate_record.get("assumption_effect")
        if isinstance(gate_record, dict)
        else None
    )
    assumptions = gate.get("assumptions")
    frontier_record = foundation_binding.get("frontier_record")
    frontier_units = (
        frontier_record.get("units") if isinstance(frontier_record, dict) else []
    )
    assumed_units = [
        unit
        for unit in frontier_units
        if isinstance(unit, dict)
        and unit.get("state") == "assumed"
        and unit.get("checkpoint_relevance") == "current"
    ]
    visible_unit_ids = string_set(
        frontier_record.get("visible_unit_ids")
        if isinstance(frontier_record, dict)
        else []
    )
    answered_decision_units = [
        unit
        for unit in frontier_units
        if isinstance(unit, dict)
        and unit.get("unit_id") in visible_unit_ids
        and unit.get("gap_kind") == "material_decision"
        and unit.get("state") == "answered"
    ]

    def matching_decision_unit(item: Any) -> dict[str, Any] | None:
        if not isinstance(item, dict):
            return None
        matches = [
            unit
            for unit in answered_decision_units
            if identity_ref_matches(
                item.get("frontier_unit_ref"),
                unit,
                kind="frontier_unit",
                id_field="unit_id",
            )
        ]
        if len(matches) != 1:
            return None
        unit = matches[0]
        value_binding = unit.get("value_binding")
        if not (
            isinstance(value_binding, dict)
            and value_binding.get("kind") == "normalized_value"
            and item.get("decision_ref") == value_binding.get("ref")
        ):
            return None
        return unit

    decisions = record.get("decisions")
    matched_decision_units = (
        [matching_decision_unit(item) for item in decisions]
        if isinstance(decisions, list)
        else []
    )
    if not (
        isinstance(decisions, list)
        and all(unit is not None for unit in matched_decision_units)
        and len(matched_decision_units) == len(answered_decision_units)
        and {
            unit["unit_id"]
            for unit in matched_decision_units
            if unit is not None
        }
        == {unit["unit_id"] for unit in answered_decision_units}
    ):
        add(
            "ORCH-DECISION-001",
            "/decisions",
            "decisions must bind one-to-one to visible answered material-decision units",
        )

    def matching_assumption_unit(item: Any) -> dict[str, Any] | None:
        if not isinstance(item, dict):
            return None
        reference = item.get("frontier_unit_ref")
        basis_refs = item.get("basis_refs")
        if not isinstance(basis_refs, list) or not all(
            isinstance(ref, str) for ref in basis_refs
        ):
            return None
        matches = [
            unit
            for unit in assumed_units
            if identity_ref_matches(
                reference,
                unit,
                kind="frontier_unit",
                id_field="unit_id",
            )
        ]
        if len(matches) != 1:
            return None
        unit = matches[0]
        value_binding = unit.get("value_binding")
        evidence_refs = {
            condition.get("evidence_ref")
            for condition in unit.get("safe_default_conditions", [])
            if isinstance(condition, dict)
            and isinstance(condition.get("evidence_ref"), str)
        }
        if not (
            isinstance(value_binding, dict)
            and value_binding.get("kind") == "assumption"
            and item.get("assumption_ref") == value_binding.get("ref")
            and set(basis_refs) == evidence_refs
        ):
            return None
        return unit

    matched_assumption_units = (
        [matching_assumption_unit(item) for item in assumptions]
        if isinstance(assumptions, list)
        else []
    )
    assumptions_valid = (
        isinstance(assumptions, list)
        and bool(assumptions)
        and all(
            isinstance(item, dict)
            and isinstance(item.get("summary"), str)
            and bool(item["summary"])
            and isinstance(item.get("frontier_unit_ref"), dict)
            and isinstance(item.get("assumption_ref"), str)
            and bool(item["assumption_ref"])
            and isinstance(item.get("basis_refs"), list)
            and bool(item["basis_refs"])
            and all(isinstance(ref, str) and ref for ref in item["basis_refs"])
            and isinstance(item.get("validation"), str)
            and bool(item["validation"])
            for item in assumptions
        )
        and all(unit is not None for unit in matched_assumption_units)
        and len(matched_assumption_units) == len(assumed_units)
        and {unit["unit_id"] for unit in matched_assumption_units if unit is not None}
        == {unit["unit_id"] for unit in assumed_units}
    )
    if (
        gate_result == "conditional"
        and assumption_effect == "non_material"
        and not assumptions_valid
    ):
        add(
            "FND-GATE-002",
            "/gate/assumptions",
            "assumption-driven conditional gate requires supported assumptions",
        )
    if gate_result != "conditional" and assumptions:
        add(
            "FND-GATE-002",
            "/gate/assumptions",
            "assumptions are only valid for a conditional gate",
        )
    if gate_result == "conditional" and assumption_effect != "non_material" and assumptions:
        add(
            "FND-GATE-002",
            "/gate/assumptions",
            "conditional gate without assumption effect must not carry assumptions",
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
    next_action_kind = handoff.get("next_action_kind")
    if gate_result == "blocked":
        foundation_action = (
            gate_record.get("next_action") if isinstance(gate_record, dict) else None
        )
        expected_kind = (
            foundation_action
            if foundation_action in {"continue", "clarify", "reauthorize"}
            else "report"
        )
        if next_action_kind != expected_kind:
            add(
                "HANDOFF-001",
                "/handoff/next_action_kind",
                "blocked handoff action must match the foundation gate action",
            )
    elif unfinished_plan and next_action_kind != "continue":
        add(
            "HANDOFF-001",
            "/handoff/next_action_kind",
            "unfinished handoff requires a continue action kind",
        )
    elif (
        not unfinished_plan
        and isinstance(gate_record, dict)
        and gate_record.get("work_remaining") is False
        and (
            handoff.get("next_action") is not None
            or next_action_kind is not None
        )
    ):
        add(
            "HANDOFF-001",
            "/handoff/next_action",
            "terminal handoff must not carry a next action",
        )

    profile = record.get("profile") if isinstance(record.get("profile"), dict) else {}
    effect_binding = (
        record.get("effect_binding")
        if isinstance(record.get("effect_binding"), dict)
        else {}
    )
    objective = record.get("objective") if isinstance(record.get("objective"), dict) else {}
    if effect_binding.get("logical_task_id") != objective_logical_task_id(objective):
        add(
            "FND-AUTH-005",
            "/effect_binding/logical_task_id",
            "logical task identity must be derived from the current objective",
        )
    has_side_effect_intent = primary_route in SIDE_EFFECT_ROUTES or isinstance(
        effect_binding.get("capability"), str
    )
    if profile.get("confidence") == "provisional":
        if has_side_effect_intent and gate_result != "blocked":
            add(
                "FND-PROFILE-004",
                "/gate/result",
                "provisional profile cannot cross a side-effect checkpoint",
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
    resolution_routing_record = foundation_binding.get("routing_record")
    if not (
        resolution.get("logical_task_id") == effect_binding.get("logical_task_id")
        and isinstance(resolution_routing_record, dict)
        and resolution.get("logical_task_id")
        == resolution_routing_record.get("logical_task_id")
        and resolution.get("basis_fingerprint")
        == effect_binding.get("basis_fingerprint")
        and resolution.get("basis_fingerprint")
        == resolution_routing_record.get("basis_fingerprint")
        and resolution.get("routing_ref") == foundation_binding.get("routing_ref")
    ):
        add(
            "RESOLVE-004",
            "/skill_resolution",
            "skill resolution must bind the current logical task, basis, and routing identity",
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
        active_decisions: list[dict[str, Any]] = []
        active_skill_ids: set[str] = set()
        for item in decisions:
            if not isinstance(item, dict) or item.get("decision") not in {
                "selected",
                "composed",
            }:
                continue
            if isinstance(item.get("skill_id"), str):
                active_skill_ids.add(item["skill_id"])
            active_decisions.append(item)
            if not active_skill_source_matches(
                item,
                effective_skill_catalog,
                source_root=source_root,
            ):
                add(
                    "RESOLVE-004",
                    "/skill_resolution/decisions",
                    f"active skill provenance must match its current source: {item.get('skill_id')}",
                )
            required_tools = item.get("required_tools")
            if not isinstance(required_tools, list) or any(
                not isinstance(tool, str)
                or "/" in tool
                or "\\" in tool
                or shutil.which(tool) is None
                for tool in required_tools
            ):
                add(
                    "RESOLVE-004",
                    "/skill_resolution/decisions",
                    f"active skill requires unavailable tools: {item.get('skill_id')}",
                )
            if primary_route not in string_set(item.get("applies_to_routes")):
                add(
                    "RESOLVE-003",
                    "/skill_resolution/decisions",
                    f"active skill must apply to primary_route: {item.get('skill_id')}",
                )
        if len(active_decisions) > 1 and any(
            item.get("decision") != "composed" for item in active_decisions
        ):
            add(
                "RESOLVE-005",
                "/skill_resolution/decisions",
                "multiple active skills must record their application order as composed",
            )
        if len(active_decisions) == 1 and active_decisions[0].get("decision") != "selected":
            add(
                "RESOLVE-005",
                "/skill_resolution/decisions",
                "a single active skill must be selected, not composed",
            )
        if any(
            isinstance(active.get("specificity"), int)
            and any(
                other is not active
                and other.get("source") == active.get("source")
                and other.get("responsibility") == active.get("responsibility")
                and isinstance(other.get("specificity"), int)
                and other["specificity"] > active["specificity"]
                for other in active_decisions
            )
            for active in active_decisions
        ):
            add(
                "RESOLVE-005",
                "/skill_resolution/decisions",
                "a lower-specificity candidate cannot remain active beside a more specific candidate for the same source and responsibility",
            )
        rejected_compatible = [
            item
            for item in decisions
            if isinstance(item, dict)
            and item.get("decision") == "rejected"
            and item.get("compatible") is True
        ]
        if any(
            isinstance(rejected.get("specificity"), int)
            and any(
                active.get("responsibility") == rejected.get("responsibility")
                and active.get("source") == rejected.get("source")
                and isinstance(active.get("specificity"), int)
                and active["specificity"] < rejected["specificity"]
                for active in active_decisions
            )
            for rejected in rejected_compatible
        ):
            add(
                "RESOLVE-005",
                "/skill_resolution/decisions",
                "a more specific compatible candidate cannot be rejected for the same source and responsibility",
            )
        blocked_decisions = [
            item
            for item in decisions
            if isinstance(item, dict) and item.get("decision") == "blocked"
        ]
        blocked_units = [
            unit
            for unit in frontier_units
            if isinstance(unit, dict)
            and unit.get("unit_id") in visible_unit_ids
            and unit.get("gap_kind") == "material_decision"
            and unit.get("state") == "pending"
            and isinstance(unit.get("runtime_disposition"), dict)
            and unit["runtime_disposition"].get("blocker") == "missing_decision"
        ]
        matched_blocked_units = [
            next(
                (
                    unit
                    for unit in blocked_units
                    if identity_ref_matches(
                        item.get("frontier_unit_ref"),
                        unit,
                        kind="frontier_unit",
                        id_field="unit_id",
                    )
                ),
                None,
            )
            for item in blocked_decisions
        ]
        if resolution.get("status") == "blocked" and not (
            blocked_decisions
            and all(unit is not None for unit in matched_blocked_units)
            and len({
                unit["unit_id"]
                for unit in matched_blocked_units
                if unit is not None
            }) == len(blocked_decisions)
        ):
            add(
                "RESOLVE-005",
                "/skill_resolution/decisions",
                "blocked resolution must bind blocked decisions one-to-one to current material-decision units",
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
        rejected_user_responsibilities = {
            item.get("responsibility")
            for item in decisions
            if isinstance(item, dict)
            and item.get("source") == "user_named"
            and item.get("decision") == "rejected"
        }
        active_responsibilities = {
            item.get("responsibility") for item in active_decisions
        }
        unrecovered_responsibilities = (
            rejected_user_responsibilities - active_responsibilities
        )
        fallback = resolution.get("fallback")
        if (
            unrecovered_responsibilities
            and resolution.get("status") != "blocked"
            and not (isinstance(fallback, str) and fallback)
        ):
            add(
                "RESOLVE-005",
                "/skill_resolution/fallback",
                "rejected user-named responsibility requires a matching replacement, fallback, or blocker",
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
    terminal_completion_claimed = (
        isinstance(gate_record, dict)
        and gate_record.get("work_remaining") is False
    )
    terminal_route_completed = bool(
        terminal_completion_claimed
        and route_plan
        and completed_phase == route_plan[-1]
    )
    verification_items = [
        item
        for result_key in ("passed", "failed", "not_run")
        for item in (
            verification.get(result_key)
            if isinstance(verification.get(result_key), list)
            else []
        )
        if isinstance(item, str) and item.strip()
    ]
    if (
        terminal_route_completed
        and completed_phase == "verify"
        and not verification_items
    ):
        add(
            "HANDOFF-004",
            "/verification",
            "terminal verify handoff must record at least one verification result",
        )
    if (
        failed
        and gate_result != "blocked"
        and (primary_route == "deliver" or terminal_completion_claimed)
    ):
        add(
            "HANDOFF-004",
            "/gate/result",
            "deliver or terminal handoff must remain blocked while verification failures are present",
        )
    artifacts = handoff.get("artifacts")
    has_result_artifact = isinstance(artifacts, list) and any(
        isinstance(item, str) and item.strip() for item in artifacts
    )
    current_effect = (
        record.get("effect_binding")
        if isinstance(record.get("effect_binding"), dict)
        else {}
    )
    terminal_effect_claimed = completed_phase in SIDE_EFFECT_ROUTES or (
        completed_phase == primary_route == "design"
        and current_effect.get("capability")
        in EFFECT_CAPABILITIES_BY_ROUTE["design"]
    )
    if (
        terminal_route_completed
        and terminal_effect_claimed
        and not has_result_artifact
    ):
        add(
            "HANDOFF-003",
            "/handoff/artifacts",
            "terminal effect handoff must identify at least one non-empty result artifact",
        )

    routing_record = foundation_binding.get("routing_record")
    frontier_record = foundation_binding.get("frontier_record")
    if not identity_ref_matches(
        foundation_binding.get("routing_ref"),
        routing_record,
        kind="routing",
        id_field="routing_id",
    ):
        add(
            "FND-ROUTE-001",
            "/foundation_binding/routing_ref",
            "routing_ref must identify the current foundation routing record",
        )
    if not identity_ref_matches(
        foundation_binding.get("gate_ref"),
        gate_record,
        kind="gate",
        id_field="gate_id",
    ) or not (
        isinstance(gate_record, dict) and gate_record.get("result") == gate_result
    ):
        add(
            "FND-GATE-001",
            "/foundation_binding/gate_ref",
            "gate_ref must identify the current foundation gate record",
        )
    if not identity_ref_matches(
        foundation_binding.get("frontier_ref"),
        frontier_record,
        kind="frontier",
        id_field="frontier_id",
    ):
        add(
            "FND-FRONTIER-004",
            "/foundation_binding/frontier_ref",
            "frontier_ref must identify the current foundation frontier record",
        )
    if not (
        isinstance(frontier_record, dict)
        and frontier_record.get("logical_task_id")
        == effect_binding.get("logical_task_id")
        and frontier_record.get("basis_fingerprint")
        == effect_binding.get("basis_fingerprint")
    ):
        add(
            "FND-FRONTIER-001",
            "/foundation_binding/frontier_record",
            "frontier record must match the current task and basis",
        )
    if not (
        isinstance(routing_record, dict)
        and routing_record.get("logical_task_id")
        == effect_binding.get("logical_task_id")
        and routing_record.get("basis_fingerprint")
        == effect_binding.get("basis_fingerprint")
        and routing_record.get("primary_route") == primary_route
        and routing_record.get("route_plan") == route_plan
        and routing_record.get("profile") == profile.get("level")
        and routing_record.get("profile_status") == profile.get("confidence")
    ):
        add(
            "FND-ROUTE-001",
            "/foundation_binding/routing_record",
            "foundation routing record must match the current orchestration decision",
        )
    if isinstance(gate_record, dict) and isinstance(unfinished_plan, bool):
        if gate_record.get("work_remaining") is not unfinished_plan:
            add(
                "FND-GATE-002",
                "/foundation_binding/gate_record/work_remaining",
                "foundation work_remaining must equal route completion state",
            )

    fixture_only = foundation_binding.get("fixture_only")
    authorization_records = foundation_binding.get("authorization_records")
    authorization_evaluations = foundation_binding.get("authorization_evaluations")
    if (
        isinstance(fixture_only, bool)
        and isinstance(routing_record, dict)
        and isinstance(gate_record, dict)
        and isinstance(frontier_record, dict)
    ):
        foundation_envelope = {
            "schema_version": "phase1-foundation-draft-v1",
            "record_kind": (
                "foundation_contract_fixture"
                if fixture_only
                else "foundation_contract_record"
            ),
            "candidate_only": True,
            "fixture_only": fixture_only,
            "runtime_activation": False,
            "routing": routing_record,
            "gate": gate_record,
            "frontier": frontier_record,
            "authorizations": (
                authorization_records
                if isinstance(authorization_records, list)
                else []
            ),
            "authorization_evaluations": (
                authorization_evaluations
                if isinstance(authorization_evaluations, list)
                else []
            ),
        }
        for foundation_finding in validate_foundation_instance(
            foundation_envelope, load_json(FOUNDATION_SCHEMA_PATH)
        ):
            add(
                foundation_finding.rule_id,
                f"/foundation_binding{foundation_finding.location}",
                foundation_finding.message,
            )

    authorization = record.get("authorization")
    if isinstance(authorization, list):
        def summary_matches_record(item: Any, authorization_record: Any) -> bool:
            return bool(
                isinstance(item, dict)
                and isinstance(authorization_record, dict)
                and identity_ref_matches(
                    item.get("authorization_ref"),
                    authorization_record,
                    kind="authorization",
                    id_field="authorization_id",
                )
                and item.get("capability")
                == authorization_record.get("capability")
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

        lineage_records = (
            authorization_records if isinstance(authorization_records, list) else []
        )
        for index, item in enumerate(authorization):
            if not any(
                summary_matches_record(item, authorization_record)
                for authorization_record in lineage_records
            ):
                add(
                    "FND-AUTH-001",
                    f"/authorization/{index}",
                    "authorization summary must identify an exact lineage record",
                )
        for index, authorization_record in enumerate(lineage_records):
            matching_summary_count = sum(
                summary_matches_record(item, authorization_record)
                for item in authorization
            )
            if matching_summary_count != 1:
                add(
                    "FND-AUTH-001",
                    f"/foundation_binding/authorization_records/{index}",
                    "each lineage authorization record must have exactly one summary",
                )
        predecessor_identity_keys = {
            (
                predecessor.get("id"),
                predecessor.get("revision"),
                predecessor.get("digest"),
            )
            for authorization_record in lineage_records
            if isinstance(authorization_record, dict)
            and isinstance(
                predecessor := authorization_record.get(
                    "predecessor_authorization_ref"
                ),
                dict,
            )
        }
        binding_keys: list[tuple[Any, Any, Any, Any]] = []
        for item in authorization:
            if not isinstance(item, dict):
                continue
            authorization_ref = item.get("authorization_ref")
            if isinstance(authorization_ref, dict) and (
                authorization_ref.get("id"),
                authorization_ref.get("revision"),
                authorization_ref.get("digest"),
            ) in predecessor_identity_keys:
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
        expected_scope_fingerprint = current_scope_fingerprint(scope)

        def matches_current_effect(item: Any) -> bool:
            if not isinstance(item, dict) or not isinstance(
                authorization_records, list
            ) or not isinstance(authorization_evaluations, list):
                return False
            authorization_ref = item.get("authorization_ref")
            for authorization_record in authorization_records:
                if not isinstance(authorization_record, dict):
                    continue
                expected_digest = authorization_record_digest(authorization_record)
                record_matches_effect = (
                    authorization_record.get("logical_task_id")
                    == effect_binding.get("logical_task_id")
                    and authorization_record.get("capability")
                    == effect_binding.get("capability")
                    and authorization_record.get("target_fingerprint")
                    == effect_binding.get("target_fingerprint")
                    and authorization_record.get("scope_fingerprint")
                    == expected_scope_fingerprint
                    and authorization_record.get("basis_fingerprint")
                    == effect_binding.get("basis_fingerprint")
                    and authorization_record.get("status") == "granted"
                    and authorization_record.get("runtime_eligible") is True
                    and authorization_record.get("future_only") is False
                    and (
                        allow_fixture_authorization
                        or authorization_record.get("fixture_only") is False
                    )
                )
                summary_matches_record = (
                    isinstance(authorization_ref, dict)
                    and authorization_ref.get("id")
                    == authorization_record.get("authorization_id")
                    and authorization_ref.get("revision")
                    == authorization_record.get("revision")
                    and authorization_ref.get("digest") == expected_digest
                    and item.get("capability")
                    == authorization_record.get("capability")
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
                routing_matches_record = identity_ref_matches(
                    routing_record.get("authorization_ref")
                    if isinstance(routing_record, dict)
                    else None,
                    authorization_record,
                    kind="authorization",
                    id_field="authorization_id",
                )
                evaluation_matches_record = any(
                    isinstance(evaluation, dict)
                    and evaluation.get("required_capability")
                    == authorization_record.get("capability")
                    and evaluation.get("target_fingerprint")
                    == authorization_record.get("target_fingerprint")
                    and evaluation.get("scope_fingerprint")
                    == authorization_record.get("scope_fingerprint")
                    and evaluation.get("basis_fingerprint")
                    == authorization_record.get("basis_fingerprint")
                    and evaluation.get("selected_authorization_id")
                    == authorization_record.get("authorization_id")
                    and evaluation.get("side_effect_intent") == "dependent"
                    and evaluation.get("derived_result") == "allowed"
                    and evaluation.get("next_action") == "continue"
                    and evaluation.get("dependent_side_effect_count") == 1
                    for evaluation in authorization_evaluations
                )
                if (
                    record_matches_effect
                    and summary_matches_record
                    and routing_matches_record
                    and evaluation_matches_record
                ):
                    return True
            return False

        current_effect_granted = any(
            matches_current_effect(item) for item in authorization
        )
        allowed_effect_capabilities = EFFECT_CAPABILITIES_BY_ROUTE.get(primary_route)
        effect_capability = effect_binding.get("capability")
        if allowed_effect_capabilities is None and effect_capability is not None:
            add(
                "FND-AUTH-005",
                "/effect_binding/capability",
                "read-only route must not carry an effect capability",
            )
        elif (
            effect_capability is not None
            and allowed_effect_capabilities is not None
            and effect_capability not in allowed_effect_capabilities
        ):
            add(
                "FND-AUTH-005",
                "/effect_binding/capability",
                "effect route requires an explicit route-compatible capability",
            )
        elif primary_route in SIDE_EFFECT_ROUTES and not isinstance(
            effect_capability, str
        ):
            add(
                "FND-AUTH-005",
                "/effect_binding/capability",
                "side-effect route requires an explicit capability",
            )
        requires_effect_grant = primary_route in SIDE_EFFECT_ROUTES or isinstance(
            effect_capability, str
        )
        if requires_effect_grant and isinstance(authorization_evaluations, list):
            dependent_evaluations = [
                evaluation
                for evaluation in authorization_evaluations
                if isinstance(evaluation, dict)
                and evaluation.get("side_effect_intent") == "dependent"
            ]
            current_effect_evaluations = [
                evaluation
                for evaluation in dependent_evaluations
                if evaluation.get("required_capability") == effect_capability
                and evaluation.get("target_fingerprint")
                == effect_binding.get("target_fingerprint")
                and evaluation.get("scope_fingerprint")
                == expected_scope_fingerprint
                and evaluation.get("basis_fingerprint")
                == effect_binding.get("basis_fingerprint")
            ]
            dependent_shape_invalid = len(dependent_evaluations) != 1 or (
                gate_result == "blocked" and len(current_effect_evaluations) != 1
            )
            if dependent_shape_invalid:
                add(
                    "FND-AUTH-005",
                    "/foundation_binding/authorization_evaluations",
                    "side-effect route must have exactly one dependent evaluation bound to the current effect",
                )
        if not requires_effect_grant and any(
            isinstance(evaluation, dict)
            and (
                evaluation.get("side_effect_intent") != "none"
                or evaluation.get("dependent_side_effect_count") != 0
            )
            for evaluation in authorization_evaluations
        ):
            add(
                "FND-AUTH-005",
                "/foundation_binding/authorization_evaluations",
                "read-only route evaluations must have no dependent side-effect intent",
            )
        if (
            requires_effect_grant
            and gate_result != "blocked"
            and not current_effect_granted
        ):
            add(
                "FND-AUTH-005",
                "/authorization",
                "effect route requires a current exact grant or a blocked gate",
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
    effective_skill_catalog = catalog.get("effective_skill_catalog")
    if not isinstance(effective_skill_catalog, list):
        raise ValueError("effective_skill_catalog must be an array")
    cases_by_id = {case["id"]: case for case in cases}
    results: list[dict[str, Any]] = []
    for case in cases:
        record = copy.deepcopy(base_record)
        base_case_id = case.get("base_case")
        if base_case_id is not None:
            base_case = cases_by_id.get(base_case_id)
            if not isinstance(base_case, dict) or base_case.get("base_case") is not None:
                raise ValueError("base_case must identify one non-derived case")
            for mutation in base_case.get("mutations", []):
                apply_mutation(record, mutation)
        for mutation in case.get("mutations", []):
            apply_mutation(record, mutation)
        schema_actual = not validate_schema(record)
        schema_expected = case.get("expected_schema_valid", True)
        allow_fixture_authorization = case.get("allow_fixture_authorization", True)
        if not isinstance(allow_fixture_authorization, bool):
            raise ValueError("allow_fixture_authorization must be boolean")
        actual_rules = sorted(
            item["rule_id"]
            for item in validate_record(
                record,
                allow_fixture_authorization=allow_fixture_authorization,
                effective_skill_catalog=effective_skill_catalog,
            )
        )
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
    parser.add_argument("--codex-executable", default="codex")
    args = parser.parse_args()

    if args.cases is not None:
        result = run_cases(args.cases)
    else:
        record = load_json(args.input)
        if not isinstance(record, dict):
            raise SystemExit("input must be a JSON object")
        schema_findings = validate_schema(record)
        effective_catalog_snapshot = None
        if schema_findings:
            semantic_findings = []
        elif not has_active_skill_decision(record):
            semantic_findings = validate_record(
                record,
                effective_skill_catalog=[],
                source_root=Path.cwd(),
            )
        else:
            try:
                effective_catalog = query_effective_skill_catalog(
                    args.codex_executable,
                    cwd=Path.cwd(),
                )
                effective_catalog_snapshot = snapshot_effective_skill_catalog(
                    effective_catalog
                )
                semantic_findings = validate_record(
                    record,
                    effective_skill_catalog=effective_catalog,
                    source_root=Path.cwd(),
                )
            except ProjectionError as exc:
                semantic_findings = [
                    {
                        "rule_id": "RESOLVE-004",
                        "path": "/skill_resolution/effective_catalog",
                        "message": str(exc),
                    }
                ]
        result = {
            "validator": {"id": VALIDATOR_ID, "revision": VALIDATOR_REVISION},
            "status": "pass" if not schema_findings and not semantic_findings else "fail",
            "schema_findings": schema_findings,
            "semantic_findings": semantic_findings,
            "effective_catalog_snapshot": effective_catalog_snapshot,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
