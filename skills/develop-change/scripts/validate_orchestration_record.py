#!/usr/bin/env python3
"""Validate cross-field semantics for a develop-change orchestration record."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


VALIDATOR_ID = "develop-change-orchestration-record-validator"
VALIDATOR_REVISION = 1
HANDOFF_SNAPSHOT_FIELDS = (
    "objective",
    "scope",
    "decisions",
    "skill_resolution",
    "authorization",
    "verification",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_record(record: dict[str, Any]) -> list[dict[str, str]]:
    """Return stable rule/path findings not expressible solely by field schemas."""
    findings: list[dict[str, str]] = []

    def add(rule_id: str, path: str, message: str) -> None:
        findings.append({"rule_id": rule_id, "path": path, "message": message})

    primary_route = record.get("primary_route")
    route_plan = record.get("route_plan")
    if not isinstance(route_plan, list) or primary_route not in route_plan:
        add("ORCH-002", "/route_plan", "primary_route must be present in route_plan")

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

    profile = record.get("profile") if isinstance(record.get("profile"), dict) else {}
    if profile.get("confidence") == "provisional" and gate_result == "pass":
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
            item.get("skill_id") for item in decisions if isinstance(item, dict)
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

    handoff = record.get("handoff") if isinstance(record.get("handoff"), dict) else {}
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
    else:
        raise ValueError(f"unsupported mutation operation: {operation!r}")


def run_cases(path: Path) -> dict[str, Any]:
    catalog = load_json(path)
    base_record = catalog.get("base_record")
    if not isinstance(base_record, dict):
        raise ValueError("base_record must be an object")
    results: list[dict[str, Any]] = []
    for case in catalog.get("cases", []):
        record = copy.deepcopy(base_record)
        for mutation in case.get("mutations", []):
            apply_mutation(record, mutation)
        actual_rules = sorted({item["rule_id"] for item in validate_record(record)})
        expected_rules = sorted(case.get("expected_rules", []))
        results.append(
            {
                "id": case.get("id"),
                "status": "pass" if actual_rules == expected_rules else "fail",
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
        findings = validate_record(record)
        result = {
            "validator": {"id": VALIDATOR_ID, "revision": VALIDATOR_REVISION},
            "status": "pass" if not findings else "fail",
            "findings": findings,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
