"""Syntax-first import guard for demolition permit requirements extraction."""

from __future__ import annotations

import importlib
import importlib.util
import py_compile
import unittest
from pathlib import Path


TARGET_MODULE = "ppd.extraction.demolition_permit_requirements"


class DemolitionPermitRequirementsSyntaxFirstTest(unittest.TestCase):
    def test_target_module_source_compiles_before_import(self) -> None:
        spec = importlib.util.find_spec(TARGET_MODULE)
        self.assertIsNotNone(spec, f"missing module spec for {TARGET_MODULE}")
        self.assertIsNotNone(spec.origin, f"missing module origin for {TARGET_MODULE}")

        module_path = Path(str(spec.origin))
        self.assertEqual(module_path.name, "demolition_permit_requirements.py")
        py_compile.compile(str(module_path), doraise=True)

    def test_target_module_imports_without_broad_validation(self) -> None:
        imported = importlib.import_module(TARGET_MODULE)

        self.assertEqual(imported.MODULE_STATUS, "syntax_first_import_ready")
        self.assertEqual(imported.module_status(), "syntax_first_import_ready")


if __name__ == "__main__":
    unittest.main()
