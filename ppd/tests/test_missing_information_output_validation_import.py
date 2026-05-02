"""Syntax-first import guard for the missing-information output validator.

This test deliberately loads only ppd/contracts/missing_information_output_validation.py
from its file path. It avoids importing ppd.contracts or any broad detector-output
validation helpers so invalid Python in the target module fails before wider test
discovery resumes that work.
"""

from __future__ import annotations

import importlib.util
import py_compile
import unittest
from pathlib import Path


class MissingInformationOutputValidationImportTest(unittest.TestCase):
    def test_contract_module_imports_without_syntax_error(self) -> None:
        module_path = (
            Path(__file__).resolve().parents[1]
            / "contracts"
            / "missing_information_output_validation.py"
        )
        self.assertTrue(
            module_path.exists(),
            "missing_information_output_validation.py must exist before broad output validation resumes",
        )

        py_compile.compile(str(module_path), doraise=True)
        spec = importlib.util.spec_from_file_location(
            "ppd_missing_information_output_validation_syntax_guard",
            module_path,
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.MODULE_STATUS, "syntax_first_import_ready")


if __name__ == "__main__":
    unittest.main()
