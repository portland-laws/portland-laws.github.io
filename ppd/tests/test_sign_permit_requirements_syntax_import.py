"""Syntax-first import sentinel for sign permit requirement extraction."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


class SignPermitRequirementsSyntaxImportTest(unittest.TestCase):
    def test_sign_permit_requirements_imports_as_single_target_module(self) -> None:
        module_path = Path(__file__).resolve().parent.parent / "extraction" / "sign_permit_requirements.py"
        self.assertTrue(module_path.exists(), f"missing target module: {module_path}")

        loaded_ppd_sign_modules_before = {
            name for name in sys.modules if name.startswith("ppd.extraction.sign_permit")
        }

        spec = importlib.util.spec_from_file_location(
            "_ppd_sign_permit_requirements_syntax_probe",
            module_path,
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        loaded_ppd_sign_modules_after = {
            name for name in sys.modules if name.startswith("ppd.extraction.sign_permit")
        }
        self.assertEqual(loaded_ppd_sign_modules_before, loaded_ppd_sign_modules_after)
        self.assertEqual(module.MODULE_PURPOSE, "syntax_first_import_sentinel")
        self.assertEqual(module.validator_status(), "syntax_first_import_ready")


if __name__ == "__main__":
    unittest.main()
