"""Syntax-first import guard for the solar permit requirements module."""

from __future__ import annotations

import importlib
import py_compile
import sys
import unittest
from pathlib import Path


TARGET_MODULE = "ppd.extraction.solar_permit_requirements"
TARGET_PATH = Path(__file__).resolve().parents[1] / "extraction" / "solar_permit_requirements.py"


class SolarPermitRequirementsSyntaxFirstImportTest(unittest.TestCase):
    def test_target_file_compiles_before_broad_validation(self) -> None:
        py_compile.compile(str(TARGET_PATH), doraise=True)

    def test_imports_solar_permit_requirements_module_only(self) -> None:
        before_import = set(sys.modules)

        module = importlib.import_module(TARGET_MODULE)

        imported_extraction_modules = sorted(
            name
            for name in set(sys.modules) - before_import
            if name.startswith("ppd.extraction.") and name != TARGET_MODULE
        )
        self.assertEqual(TARGET_MODULE, module.__name__)
        self.assertEqual([], imported_extraction_modules)
        self.assertEqual("syntax_first_import_ready", module.validator_status())


if __name__ == "__main__":
    unittest.main()
