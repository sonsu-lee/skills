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
VALID_SKILL_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
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
REQUIRED_RULE_IDS = {
    *(f"ORCH-{number:03d}" for number in range(1, 9)),
    *(f"RESOLVE-{number:03d}" for number in range(1, 8)),
    *(f"HANDOFF-{number:03d}" for number in range(1, 6)),
}
REQUIRED_HANDOFF_FIELDS = {
    "objective",
    "scope",
    "completed_phase",
    "decisions",
    "artifacts",
    "skill_resolution",
    "authorization",
    "verification",
    "blockers",
    "next_action",
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
    verification = record.get("verification", {})
    passed = set(verification.get("passed", []))
    not_run = set(verification.get("not_run", []))
    if passed & not_run:
        findings.add("HANDOFF-004")
    authorization = record.get("authorization", {})
    next_action = record.get("next_action")
    if isinstance(next_action, str):
        normalized = next_action.lower()
        for capability, state in authorization.items():
            if capability in normalized and state not in {"granted", "consumed"}:
                findings.add("HANDOFF-002")
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
        actual = evaluate_authorization(case)
        status = "pass" if actual == case.get("expected") else "fail"
        if status == "fail":
            findings.append(f"authorization:{case.get('id')}:expectation_mismatch")
        case_results.append({"id": case["id"], "kind": "authorization", "status": status})

    for case in cases.get("handoff_cases", []):
        actual = validate_handoff(case.get("record", {}))
        status = "pass" if actual == case.get("expected_rules") else "fail"
        if status == "fail":
            findings.append(f"handoff:{case.get('id')}:expectation_mismatch")
        case_results.append({"id": case["id"], "kind": "handoff", "status": status})

    actual_activation, activation_findings = validate_activation(root, activation)
    findings.extend(activation_findings)
    source_paths = (
        cases_path,
        root / "skills/develop-change/references/orchestration-contract.schema.json",
        root / "skills/develop-change/references/orchestration-contract.md",
        root / "skills/develop-change/references/skill-resolution-contract.md",
        root / "skills/develop-change/references/handoff-contract.md",
        root / "skills/develop-change/scripts/validate_orchestration.py",
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
