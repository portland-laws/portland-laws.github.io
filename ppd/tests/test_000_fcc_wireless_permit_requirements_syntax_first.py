"""Syntax-first import sentinel for FCC wireless permit requirements."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_NAME = "ppd.extraction.fcc_wireless_permit_requirements"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "extraction"
    / "fcc_wireless_permit_requirements.py"
)


class FccWirelessPermitRequirementsSyntaxFirstTest(unittest.TestCase):
    def test_imports_only_target_module(self) -> None:
        spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)

        imported_before = set(sys.modules)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        imported_after = set(sys.modules)

        self.assertEqual("syntax_first_import_ready", module.validator_status())
        self.assertNotIn("ppd.extraction.fcc_wireless_requirement_validation", imported_after - imported_before)
        self.assertNotIn("ppd.extraction.fcc_wireless_permit_requirement_validation", imported_after - imported_before)


if __name__ == "__main__":
    unittest.main()
