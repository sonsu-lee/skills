from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_skill_catalog.py"
SPEC = importlib.util.spec_from_file_location("validate_skill_catalog", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog)


class JsonManifestValidationTest(unittest.TestCase):
    def test_rejects_yaml_only_json_syntax(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / "plugin.json"
            manifest.write_text('{"name": "skills"}\n# YAML-only comment\n')
            errors: list[str] = []
            original_root = catalog.ROOT
            try:
                catalog.ROOT = root
                self.assertEqual(catalog.load_json(manifest, errors), {})
            finally:
                catalog.ROOT = original_root

            self.assertEqual(len(errors), 1)
            self.assertIn("JSON을 읽을 수 없습니다", errors[0])


class SemVerValidationTest(unittest.TestCase):
    def test_accepts_complete_semver_syntax(self) -> None:
        valid_versions = (
            "0.2.0",
            "0.2.0-rc.1",
            "0.2.0+build.7",
            "1.0.0-beta+exp.sha.5114f85",
        )
        for version in valid_versions:
            with self.subTest(version=version):
                self.assertIsNotNone(catalog.VERSION_PATTERN.fullmatch(version))

    def test_rejects_invalid_semver_syntax(self) -> None:
        invalid_versions = (
            "01.0.0",
            "1.0",
            "v1.0.0",
            "1.0.0-01",
            "1.0.0-alpha..1",
            "1.0.0+",
        )
        for version in invalid_versions:
            with self.subTest(version=version):
                self.assertIsNone(catalog.VERSION_PATTERN.fullmatch(version))


if __name__ == "__main__":
    unittest.main()
