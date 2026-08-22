#!/usr/bin/env python3
"""Validate develop-change orchestration, resolution, and activation contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from validate_orchestration_record import run_cases as run_record_cases

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment setup failure
    raise SystemExit("PyYAML이 필요합니다: python3 -m pip install pyyaml") from exc


ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = ROOT / "skills" / "develop-change"
CASES_PATH = SKILL_ROOT / "evals" / "orchestration-cases.json"
SCHEMA_PATH = SKILL_ROOT / "references" / "orchestration-contract.schema.json"
CONTRACT_PATHS = (
    SKILL_ROOT / "references" / "orchestration-contract.md",
    SKILL_ROOT / "references" / "skill-resolution-contract.md",
    SKILL_ROOT / "references" / "handoff-contract.md",
)
VALID_SKILL_ID = re.compile(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*(?::[a-z0-9]+(?:-[a-z0-9]+)*)?$"
)
SECRET_PATTERN = re.compile(
    r"(?:api[_-]?key|token|secret)=[A-Za-z0-9_-]{12,}", re.IGNORECASE
)
SOURCE_PRIORITY = {"installed": 1, "repository": 2, "user_named": 3}
PLANNED_CAPABILITIES = {
    "typescript-javascript-practices",
    "frontend-framework-practices",
    "database-orm-practices",
    "testing-quality-practices",
    "security-operations-practices",
}
ROUTES = {
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
}
CAPABILITIES = {
    "local_change",
    "working_artifact_write",
    "temporary_work_state",
    "workspace_cleanup",
    "durable_document_write",
    "durable_document_content",
    "branch_create",
    "branch_switch",
    "stage",
    "commit",
    "push",
    "pr_create",
    "merge",
    "rebase",
    "history_rewrite",
    "destructive_local",
    "external_write",
    "scope_expansion",
}
AUTHORIZATION_STATES = {
    "not_applicable",
    "not_granted",
    "granted",
    "denied",
    "withdrawn",
    "stale",
}
REQUIRED_RULE_IDS = {
    *(f"ORCH-{number:03d}" for number in range(1, 9)),
    *(f"RESOLVE-{number:03d}" for number in range(1, 8)),
    *(f"HANDOFF-{number:03d}" for number in range(1, 6)),
}
REQUIRED_HANDOFF_FIELDS = {
    "objective",
    "scope",
    "completed_phase",
    "primary_route",
    "route_plan",
    "decisions",
    "artifacts",
    "effect_binding",
    "profile",
    "foundation_binding",
    "skill_resolution",
    "authorization",
    "verification",
    "blockers",
    "next_action",
    "next_action_kind",
}
REQUIRED_AUTHORIZATION_FIELDS = {
    "capability",
    "authorization_ref",
    "target_fingerprint",
    "scope_fingerprint",
    "basis_fingerprint",
    "status",
    "runtime_eligible",
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_rejection(candidate: dict[str, Any]) -> str | None:
    if not candidate.get("relevant"):
        return "irrelevant"
    if not candidate.get("available"):
        return "unavailable"
    if not candidate.get("compatible"):
        return "incompatible"
    if candidate.get("project_rule_conflict"):
        return "project_rule_conflict"
    return None


def resolve_candidates(case: dict[str, Any], planned: set[str]) -> dict[str, Any]:
    rejected: list[dict[str, str]] = []
    eligible: dict[str, list[dict[str, Any]]] = {}
    seen_ids: set[str] = set()

    planned_capability = case.get("planned_capability")
    if planned_capability is not None and planned_capability not in planned:
        raise ValueError(f"unknown planned capability: {planned_capability}")

    for candidate in case.get("candidates", []):
        skill_id = candidate.get("skill_id")
        if not isinstance(skill_id, str) or not VALID_SKILL_ID.fullmatch(skill_id):
            raise ValueError(f"invalid skill id: {skill_id!r}")
        if skill_id in seen_ids:
            raise ValueError(f"duplicate skill id: {skill_id}")
        if skill_id in planned:
            raise ValueError(f"planned capability used as skill id: {skill_id}")
        seen_ids.add(skill_id)
        source = candidate.get("source")
        if source not in SOURCE_PRIORITY:
            raise ValueError(f"invalid source for {skill_id}: {source!r}")
        specificity = candidate.get("specificity")
        if not isinstance(specificity, int) or not 0 <= specificity <= 5:
            raise ValueError(f"invalid specificity for {skill_id}")
        responsibility = candidate.get("responsibility")
        if not isinstance(responsibility, str) or not responsibility:
            raise ValueError(f"missing responsibility for {skill_id}")
        rejection = _candidate_rejection(candidate)
        if rejection:
            rejected.append({"skill_id": skill_id, "reason": rejection})
            continue
        eligible.setdefault(responsibility, []).append(candidate)

    selected: list[str] = []
    for responsibility in sorted(eligible):
        candidates = eligible[responsibility]
        candidates.sort(
            key=lambda item: (
                -SOURCE_PRIORITY[item["source"]],
                -item["specificity"],
                item["skill_id"],
            )
        )
        top = candidates[0]
        tied = [
            candidate
            for candidate in candidates
            if SOURCE_PRIORITY[candidate["source"]]
            == SOURCE_PRIORITY[top["source"]]
            and candidate["specificity"] == top["specificity"]
        ]
        guidance_keys = {candidate.get("guidance_key") for candidate in tied}
        if len(tied) > 1 and len(guidance_keys) > 1:
            ids = ",".join(sorted(candidate["skill_id"] for candidate in tied))
            return {
                "status": "blocked",
                "selected": [],
                "rejected": sorted(rejected, key=lambda item: item["skill_id"]),
                "fallback": None,
                "blocker": f"unresolved_material_conflict:{responsibility}:{ids}",
            }
        selected.append(top["skill_id"])
        for candidate in candidates[1:]:
            rejected.append(
                {"skill_id": candidate["skill_id"], "reason": "superseded"}
            )

    return {
        "status": "pass",
        "selected": sorted(selected),
        "rejected": sorted(rejected, key=lambda item: item["skill_id"]),
        "fallback": (
            None if selected else "official_documentation_and_base_capability"
        ),
        "blocker": None,
    }


def evaluate_authorization(case: dict[str, Any]) -> dict[str, str | None]:
    requested = set(case.get("requested_effects", []))
    authorization = case.get("authorization", {})
    unknown_effects = requested - CAPABILITIES
    unknown_authorizations = set(authorization) - CAPABILITIES
    if unknown_effects or unknown_authorizations:
        unknown = sorted(unknown_effects | unknown_authorizations)
        raise ValueError(f"unknown capability: {','.join(unknown)}")
    invalid_states = {
        state for state in authorization.values() if state not in AUTHORIZATION_STATES
    }
    if invalid_states:
        raise ValueError(f"unknown authorization state: {sorted(invalid_states)!r}")
    if case.get("scope_changed") and requested:
        return {"gate": "blocked", "blocker": "scope_expansion"}
    missing = sorted(
        effect for effect in requested if authorization.get(effect) != "granted"
    )
    if missing:
        return {
            "gate": "blocked",
            "blocker": f"missing_authorization:{','.join(missing)}",
        }
    return {"gate": "pass", "blocker": None}


def validate_gate(gate: dict[str, Any]) -> bool:
    result = gate.get("result")
    blockers = gate.get("blockers")
    if result not in {"pass", "conditional", "blocked"}:
        return False
    if not isinstance(blockers, list) or any(
        not isinstance(blocker, str) or not blocker for blocker in blockers
    ):
        return False
    if result in {"pass", "conditional"}:
        return not blockers
    return bool(blockers)


def validate_profile(profile: dict[str, Any]) -> bool:
    if set(profile) != {"level", "confidence"}:
        return False
    level = profile.get("level")
    confidence = profile.get("confidence")
    if level not in {"direct", "bounded", "architectural"}:
        return False
    if confidence not in {"confirmed", "provisional"}:
        return False
    return level != "direct" or confidence == "confirmed"


def validate_skill_resolution(record: dict[str, Any]) -> bool:
    if set(record) != {"status", "decisions", "planned_capabilities", "fallback"}:
        return False
    status = record.get("status")
    decisions = record.get("decisions")
    planned = record.get("planned_capabilities")
    fallback = record.get("fallback")
    if status not in {"pass", "blocked"}:
        return False
    if not isinstance(decisions, list) or not isinstance(planned, list):
        return False
    if fallback is not None and not isinstance(fallback, str):
        return False
    for decision in decisions:
        if not isinstance(decision, dict):
            return False
        disposition = decision.get("decision")
        if disposition not in {"selected", "composed", "rejected", "blocked"}:
            return False
        if disposition in {"selected", "composed"} and decision.get("compatible") is not True:
            return False
        provenance = decision.get("provenance")
        if disposition in {"selected", "composed"} and not (
            isinstance(provenance, dict)
            and isinstance(provenance.get("locator"), str)
            and provenance["locator"]
            and isinstance(provenance.get("version"), str)
            and provenance["version"]
            and isinstance(provenance.get("content_digest"), str)
            and re.fullmatch(r"[0-9a-f]{64}", provenance["content_digest"])
        ):
            return False
    if any(decision.get("decision") == "blocked" for decision in decisions):
        return status == "blocked"
    return True


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _walk_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_strings(nested)


def validate_handoff(record: dict[str, Any]) -> list[str]:
    findings: set[str] = set()
    if set(record) != REQUIRED_HANDOFF_FIELDS:
        findings.add("HANDOFF-001")

    objective = record.get("objective")
    if not isinstance(objective, dict) or set(objective) != {"summary", "finish_line"}:
        findings.add("HANDOFF-001")
    scope = record.get("scope")
    if (
        not isinstance(scope, dict)
        or set(scope) != {"include", "exclude"}
        or not isinstance(scope.get("include"), list)
        or not isinstance(scope.get("exclude"), list)
    ):
        findings.add("HANDOFF-001")
    if record.get("completed_phase") not in ROUTES:
        findings.add("HANDOFF-001")
    primary_route = record.get("primary_route")
    route_plan = record.get("route_plan")
    if (
        primary_route not in ROUTES
        or not isinstance(route_plan, list)
        or not route_plan
        or primary_route not in route_plan
        or any(route not in ROUTES for route in route_plan)
    ):
        findings.add("HANDOFF-001")
    completed_phase = record.get("completed_phase")
    if isinstance(route_plan, list) and completed_phase in route_plan:
        completed_index = route_plan.index(completed_phase)
        expected_route = (
            completed_phase
            if completed_index == len(route_plan) - 1
            else route_plan[completed_index + 1]
        )
        if primary_route != expected_route:
            findings.add("HANDOFF-001")
    if not isinstance(record.get("decisions"), list):
        findings.add("HANDOFF-001")
    if not isinstance(record.get("artifacts"), list):
        findings.add("HANDOFF-001")
    effect_binding = record.get("effect_binding")
    if (
        not isinstance(effect_binding, dict)
        or set(effect_binding)
        != {
            "logical_task_id",
            "capability",
            "target_fingerprint",
            "basis_fingerprint",
        }
        or not isinstance(effect_binding.get("logical_task_id"), str)
        or not effect_binding.get("logical_task_id")
        or effect_binding.get("capability") not in CAPABILITIES | {None}
        or any(
            not isinstance(effect_binding.get(field), str)
            or re.fullmatch(r"[0-9a-f]{64}", effect_binding[field]) is None
            for field in ("target_fingerprint", "basis_fingerprint")
        )
    ):
        findings.add("HANDOFF-001")
    profile = record.get("profile")
    if (
        not isinstance(profile, dict)
        or set(profile) != {"level", "confidence"}
        or profile.get("level") not in {"direct", "bounded", "architectural"}
        or profile.get("confidence") not in {"confirmed", "provisional"}
    ):
        findings.add("HANDOFF-001")
    foundation_binding = record.get("foundation_binding")
    if not isinstance(foundation_binding, dict) or set(foundation_binding) != {
        "fixture_only",
        "routing_ref",
        "routing_record",
        "gate_ref",
        "frontier_ref",
        "gate_record",
        "frontier_record",
        "authorization_records",
        "authorization_evaluations",
    }:
        findings.add("HANDOFF-001")
    else:
        if not isinstance(foundation_binding["fixture_only"], bool):
            findings.add("HANDOFF-001")
        for field in ("routing_ref", "gate_ref", "frontier_ref"):
            identity_ref = foundation_binding[field]
            if not isinstance(identity_ref, dict) or set(identity_ref) != {
                "id",
                "revision",
                "digest",
            }:
                findings.add("HANDOFF-001")
        for field in ("routing_record", "gate_record", "frontier_record"):
            if not isinstance(foundation_binding[field], dict):
                findings.add("HANDOFF-001")
        for field in ("authorization_records", "authorization_evaluations"):
            if not isinstance(foundation_binding[field], list) or not all(
                isinstance(item, dict) for item in foundation_binding[field]
            ):
                findings.add("HANDOFF-001")

    skill_resolution = record.get("skill_resolution")
    if not isinstance(skill_resolution, dict) or not validate_skill_resolution(
        skill_resolution
    ):
        findings.add("HANDOFF-001")

    verification = record.get("verification", {})
    if not isinstance(verification, dict) or set(verification) != {
        "passed",
        "failed",
        "not_run",
    }:
        findings.add("HANDOFF-001")
        verification = {}
    passed = set(verification.get("passed", []))
    failed = set(verification.get("failed", []))
    not_run = set(verification.get("not_run", []))
    if (passed & failed) or (passed & not_run) or (failed & not_run):
        findings.add("HANDOFF-004")

    authorization = record.get("authorization", [])
    authorization_by_capability: dict[str, dict[str, Any]] = {}
    if not isinstance(authorization, list):
        findings.add("HANDOFF-001")
        authorization = []
    for item in authorization:
        if not isinstance(item, dict) or set(item) != REQUIRED_AUTHORIZATION_FIELDS:
            findings.add("HANDOFF-001")
            continue
        capability = item.get("capability")
        state = item.get("status")
        runtime_eligible = item.get("runtime_eligible")
        if capability not in CAPABILITIES or state not in AUTHORIZATION_STATES:
            findings.add("HANDOFF-002")
            continue
        if capability in authorization_by_capability:
            findings.add("HANDOFF-002")
        if runtime_eligible is not (state == "granted"):
            findings.add("HANDOFF-002")
        authorization_by_capability[capability] = item

    next_action = record.get("next_action")
    if isinstance(next_action, str):
        normalized = next_action.lower()
        for capability in CAPABILITIES:
            if capability not in normalized:
                continue
            current = authorization_by_capability.get(capability)
            if not current or not current["runtime_eligible"]:
                findings.add("HANDOFF-002")
    elif next_action is not None:
        findings.add("HANDOFF-001")
    next_action_kind = record.get("next_action_kind")
    if next_action_kind not in {"continue", "clarify", "reauthorize", "report", None}:
        findings.add("HANDOFF-001")
    completed_phase = record.get("completed_phase")
    unfinished_plan = (
        isinstance(route_plan, list)
        and completed_phase in route_plan
        and route_plan.index(completed_phase) < len(route_plan) - 1
    )
    if unfinished_plan and next_action_kind != "continue":
        findings.add("HANDOFF-001")
    gate_record = (
        foundation_binding.get("gate_record")
        if isinstance(foundation_binding, dict)
        else None
    )
    if isinstance(gate_record, dict) and gate_record.get("result") == "blocked":
        gate_action = gate_record.get("next_action")
        expected_kind = (
            gate_action
            if gate_action in {"continue", "clarify", "reauthorize"}
            else "report"
        )
        if next_action_kind != expected_kind:
            findings.add("HANDOFF-001")
    elif (
        not unfinished_plan
        and isinstance(gate_record, dict)
        and gate_record.get("work_remaining") is False
        and (next_action is not None or next_action_kind is not None)
    ):
        findings.add("HANDOFF-001")

    if not isinstance(record.get("blockers"), list):
        findings.add("HANDOFF-001")
    if any(SECRET_PATTERN.search(value) for value in _walk_strings(record)):
        findings.add("HANDOFF-005")
    return sorted(findings)


def validate_contract_sources(root: Path, findings: list[str]) -> None:
    observed_ids: set[str] = set()
    for relative in (
        "skills/develop-change/references/orchestration-contract.md",
        "skills/develop-change/references/skill-resolution-contract.md",
        "skills/develop-change/references/handoff-contract.md",
    ):
        path = root / relative
        if not path.is_file():
            findings.append(f"missing_contract:{relative}")
            continue
        observed_ids.update(re.findall(r"(?:ORCH|RESOLVE|HANDOFF)-\d{3}", path.read_text(encoding="utf-8")))
    for rule_id in sorted(REQUIRED_RULE_IDS - observed_ids):
        findings.append(f"missing_rule_id:{rule_id}")

    schema_path = root / "skills/develop-change/references/orchestration-contract.schema.json"
    try:
        schema = load_json(schema_path)
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(f"invalid_schema:{exc}")
        return
    if schema.get("$id") != "urn:sonsu:skills:develop-change:orchestration:v1":
        findings.append("invalid_schema_id")
    contract_version = (
        schema.get("properties", {}).get("contract_version", {}).get("const")
    )
    if contract_version != "develop-change-orchestration-v1":
        findings.append("invalid_contract_version")
    planned_status = (
        schema.get("$defs", {})
        .get("plannedCapability", {})
        .get("properties", {})
        .get("status", {})
        .get("const")
    )
    if planned_status != "planned":
        findings.append("invalid_planned_capability_status")
    required = set(schema.get("required", []))
    expected_required = {
        "objective",
        "scope",
        "decisions",
        "effect_binding",
        "primary_route",
        "route_plan",
        "profile",
        "gate",
        "foundation_binding",
        "skill_resolution",
        "authorization",
        "verification",
        "handoff",
    }
    if not expected_required.issubset(required):
        findings.append("orchestration_schema_required_fields_missing")
    handoff_required = set(
        schema.get("$defs", {}).get("handoff", {}).get("required", [])
    )
    if handoff_required != REQUIRED_HANDOFF_FIELDS:
        findings.append("handoff_schema_required_fields_mismatch")
    skill_required = set(
        schema.get("$defs", {}).get("skillDecision", {}).get("required", [])
    )
    if not {
        "responsibility",
        "applies_to_routes",
        "effect_boundary",
    }.issubset(skill_required):
        findings.append("skill_decision_scope_missing")
    authorization_statuses = set(
        schema.get("$defs", {})
        .get("authorizationSummary", {})
        .get("properties", {})
        .get("status", {})
        .get("enum", [])
    )
    if authorization_statuses != AUTHORIZATION_STATES:
        findings.append("authorization_status_mismatch")
    profile_constraints = schema.get("properties", {}).get("profile", {}).get("allOf", [])
    if not any(
        constraint.get("if", {}).get("properties", {}).get("level", {}).get("const")
        == "direct"
        and constraint.get("then", {})
        .get("properties", {})
        .get("confidence", {})
        .get("const")
        == "confirmed"
        for constraint in profile_constraints
    ):
        findings.append("direct_profile_must_be_confirmed")
    resolution_constraints = (
        schema.get("$defs", {}).get("skillResolution", {}).get("allOf", [])
    )
    if not any(
        constraint.get("then", {})
        .get("properties", {})
        .get("status", {})
        .get("const")
        == "blocked"
        for constraint in resolution_constraints
    ):
        findings.append("blocked_decision_status_constraint_missing")
    decision_constraints = (
        schema.get("$defs", {}).get("skillDecision", {}).get("allOf", [])
    )
    if not any(
        set(
            constraint.get("if", {})
            .get("properties", {})
            .get("decision", {})
            .get("enum", [])
        )
        == {"selected", "composed"}
        and constraint.get("then", {})
        .get("properties", {})
        .get("compatible", {})
        .get("const")
        is True
        for constraint in decision_constraints
    ):
        findings.append("selected_skill_compatibility_constraint_missing")


def validate_activation(root: Path, requested: str) -> tuple[str, list[str]]:
    skill_file = root / "skills/develop-change/SKILL.md"
    actual = "active" if skill_file.is_file() else "inactive"
    expected = actual if requested == "auto" else requested
    findings: list[str] = []
    if actual != expected:
        findings.append(f"activation_state:{actual}:expected:{expected}")
        return actual, findings
    if actual == "inactive":
        return actual, findings

    metadata_path = root / "skills/develop-change/agents/openai.yaml"
    if not metadata_path.is_file():
        findings.append("active_metadata_missing")
    else:
        try:
            metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            findings.append(f"active_metadata_invalid:{exc}")
        else:
            allow_implicit = (
                metadata.get("policy", {}).get("allow_implicit_invocation")
                if isinstance(metadata, dict)
                else None
            )
            if allow_implicit is not False:
                findings.append("active_policy_must_be_explicit_only")

    catalog_source = (root / "scripts/validate_skill_catalog.py").read_text(
        encoding="utf-8"
    )
    if '"develop-change": False' not in catalog_source:
        findings.append("catalog_policy_missing")
    internal_match = re.search(r"INTERNAL_SKILL_DIRS\s*=\s*\{([^}]*)\}", catalog_source)
    if internal_match and "develop-change" in internal_match.group(1):
        findings.append("active_skill_still_internal")
    readme = (root / "README.md").read_text(encoding="utf-8")
    if not re.search(r"^\| `develop-change` \|", readme, re.MULTILINE):
        findings.append("active_readme_row_missing")
    return actual, findings


def run_validation(root: Path, activation: str) -> dict[str, Any]:
    findings: list[str] = []
    validate_contract_sources(root, findings)
    cases_path = root / "skills/develop-change/evals/orchestration-cases.json"
    record_cases_path = (
        root / "skills/develop-change/evals/orchestration-record-cases.json"
    )
    cases = load_json(cases_path)
    planned = set(cases.get("planned_capabilities", []))
    if planned != PLANNED_CAPABILITIES:
        findings.append("planned_capability_catalog_mismatch")

    case_results: list[dict[str, str]] = []
    for case in cases.get("resolution_cases", []):
        try:
            actual = resolve_candidates(case, planned)
        except (KeyError, TypeError, ValueError) as exc:
            findings.append(f"resolution:{case.get('id')}:{exc}")
            case_results.append({"id": str(case.get("id")), "kind": "resolution", "status": "fail"})
            continue
        status = "pass" if actual == case.get("expected") else "fail"
        if status == "fail":
            findings.append(f"resolution:{case.get('id')}:expectation_mismatch")
        case_results.append({"id": case["id"], "kind": "resolution", "status": status})

    for case in cases.get("authorization_cases", []):
        try:
            actual = evaluate_authorization(case)
        except (TypeError, ValueError) as exc:
            findings.append(f"authorization:{case.get('id')}:{exc}")
            case_results.append(
                {
                    "id": str(case.get("id")),
                    "kind": "authorization",
                    "status": "fail",
                }
            )
            continue
        status = "pass" if actual == case.get("expected") else "fail"
        if status == "fail":
            findings.append(f"authorization:{case.get('id')}:expectation_mismatch")
        case_results.append({"id": case["id"], "kind": "authorization", "status": status})

    for case in cases.get("gate_cases", []):
        actual = validate_gate(case.get("gate", {}))
        status = "pass" if actual is case.get("expected_valid") else "fail"
        if status == "fail":
            findings.append(f"gate:{case.get('id')}:expectation_mismatch")
        case_results.append({"id": case["id"], "kind": "gate", "status": status})

    for case in cases.get("profile_cases", []):
        actual = validate_profile(case.get("profile", {}))
        status = "pass" if actual is case.get("expected_valid") else "fail"
        if status == "fail":
            findings.append(f"profile:{case.get('id')}:expectation_mismatch")
        case_results.append({"id": case["id"], "kind": "profile", "status": status})

    for case in cases.get("skill_resolution_cases", []):
        actual = validate_skill_resolution(case.get("record", {}))
        status = "pass" if actual is case.get("expected_valid") else "fail"
        if status == "fail":
            findings.append(
                f"skill_resolution:{case.get('id')}:expectation_mismatch"
            )
        case_results.append(
            {"id": case["id"], "kind": "skill_resolution", "status": status}
        )

    for case in cases.get("handoff_cases", []):
        actual = validate_handoff(case.get("record", {}))
        status = "pass" if actual == case.get("expected_rules") else "fail"
        if status == "fail":
            findings.append(f"handoff:{case.get('id')}:expectation_mismatch")
        case_results.append({"id": case["id"], "kind": "handoff", "status": status})

    record_report = run_record_cases(record_cases_path)
    for result in record_report["cases"]:
        if result["status"] == "fail":
            findings.append(
                f"orchestration_record:{result['id']}:expectation_mismatch"
            )
        case_results.append(
            {
                "id": result["id"],
                "kind": "orchestration_record",
                "status": result["status"],
            }
        )

    actual_activation, activation_findings = validate_activation(root, activation)
    findings.extend(activation_findings)
    source_paths = (
        cases_path,
        record_cases_path,
        root / "skills/develop-change/references/orchestration-contract.schema.json",
        root / "skills/develop-change/references/orchestration-contract.md",
        root / "skills/develop-change/references/skill-resolution-contract.md",
        root / "skills/develop-change/references/handoff-contract.md",
        root / "skills/develop-change/scripts/validate_orchestration.py",
        root / "skills/develop-change/scripts/validate_orchestration_record.py",
    )
    source_digests = {
        path.relative_to(root).as_posix(): sha256_bytes(path.read_bytes())
        for path in source_paths
    }
    status = "pass" if not findings else "fail"
    return {
        "schema_version": "develop-change-orchestration-report-v1",
        "status": status,
        "activation": actual_activation,
        "case_count": len(case_results),
        "passed_case_count": sum(
            result["status"] == "pass" for result in case_results
        ),
        "findings": sorted(findings),
        "case_results": case_results,
        "source_digests": source_digests,
    }


def serialized_report(report: dict[str, Any]) -> bytes:
    return (
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--activation", choices=("auto", "inactive", "active"), default="auto"
    )
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--output", type=Path)
    output_group.add_argument("--check-output", type=Path)
    args = parser.parse_args()

    report = run_validation(ROOT, args.activation)
    payload = serialized_report(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(payload)
    elif args.check_output:
        try:
            existing = args.check_output.read_bytes()
        except OSError as exc:
            print(f"FAIL: report를 읽을 수 없습니다: {exc}")
            return 1
        if existing != payload:
            print("FAIL: 저장된 report가 현재 입력에서 재현되지 않습니다.")
            return 1
    else:
        print(payload.decode("utf-8"), end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
