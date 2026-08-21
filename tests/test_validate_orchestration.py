from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT / "skills" / "develop-change" / "scripts" / "validate_orchestration.py"
)
SPEC = importlib.util.spec_from_file_location("validate_orchestration", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
orchestration = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(orchestration)


class ResolutionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = orchestration.load_json(orchestration.CASES_PATH)

    def test_all_resolution_fixtures_match(self) -> None:
        planned = set(self.cases["planned_capabilities"])
        for case in self.cases["resolution_cases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(
                    orchestration.resolve_candidates(case, planned), case["expected"]
                )

    def test_planned_capability_cannot_impersonate_a_skill(self) -> None:
        case = {
            "candidates": [
                {
                    "skill_id": "database-orm-practices",
                    "source": "repository",
                    "responsibility": "database",
                    "specificity": 3,
                    "available": True,
                    "compatible": True,
                    "relevant": True,
                    "project_rule_conflict": False,
                    "guidance_key": "planned",
                }
            ]
        }
        with self.assertRaisesRegex(ValueError, "planned capability"):
            orchestration.resolve_candidates(
                case, orchestration.PLANNED_CAPABILITIES
            )

    def test_namespaced_plugin_skill_id_is_supported(self) -> None:
        case = next(
            case
            for case in self.cases["resolution_cases"]
            if case["id"] == "namespaced-installed-skill-is-supported"
        )
        self.assertEqual(
            orchestration.resolve_candidates(case, orchestration.PLANNED_CAPABILITIES),
            case["expected"],
        )


class AuthorizationTest(unittest.TestCase):
    def test_invocation_does_not_grant_local_change(self) -> None:
        result = orchestration.evaluate_authorization(
            {
                "requested_effects": ["local_change"],
                "authorization": {},
                "scope_changed": False,
            }
        )
        self.assertEqual(
            result,
            {
                "gate": "blocked",
                "blocker": "missing_authorization:local_change",
            },
        )

    def test_unknown_capability_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown capability"):
            orchestration.evaluate_authorization(
                {
                    "requested_effects": ["totally_unknown_capability"],
                    "authorization": {
                        "totally_unknown_capability": "granted"
                    },
                    "scope_changed": False,
                }
            )


class HandoffTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = orchestration.load_json(orchestration.CASES_PATH)

    def test_handoff_fixtures_match(self) -> None:
        for case in self.cases["handoff_cases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(
                    orchestration.validate_handoff(case["record"]),
                    case["expected_rules"],
                )


class GateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = orchestration.load_json(orchestration.CASES_PATH)

    def test_gate_fixtures_match(self) -> None:
        for case in self.cases["gate_cases"]:
            with self.subTest(case=case["id"]):
                self.assertIs(
                    orchestration.validate_gate(case["gate"]),
                    case["expected_valid"],
                )


class ProfileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = orchestration.load_json(orchestration.CASES_PATH)

    def test_profile_fixtures_match(self) -> None:
        for case in self.cases["profile_cases"]:
            with self.subTest(case=case["id"]):
                self.assertIs(
                    orchestration.validate_profile(case["profile"]),
                    case["expected_valid"],
                )


class SkillResolutionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = orchestration.load_json(orchestration.CASES_PATH)

    def test_skill_resolution_fixtures_match(self) -> None:
        for case in self.cases["skill_resolution_cases"]:
            with self.subTest(case=case["id"]):
                self.assertIs(
                    orchestration.validate_skill_resolution(case["record"]),
                    case["expected_valid"],
                )


class ActivationTest(unittest.TestCase):
    def test_auto_detects_inactive_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            actual, findings = orchestration.validate_activation(root, "auto")
        self.assertEqual(actual, "inactive")
        self.assertEqual(findings, [])


class IntegrationTest(unittest.TestCase):
    def test_repository_contracts_pass_in_current_activation_state(self) -> None:
        report = orchestration.run_validation(ROOT, "auto")
        self.assertEqual(report["status"], "pass", report["findings"])
        self.assertEqual(report["case_count"], report["passed_case_count"])


if __name__ == "__main__":
    unittest.main()
