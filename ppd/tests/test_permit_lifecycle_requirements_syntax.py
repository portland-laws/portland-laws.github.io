"""Syntax-first import sentinel for permit lifecycle requirement extraction.

This test intentionally imports only the target extractor module. If the module is
not implemented yet, the test skips. If the module exists but contains malformed
Python, importlib surfaces SyntaxError before broader lifecycle validation can run.
"""

from __future__ import annotations

import importlib
import unittest


TARGET_MODULE = "ppd.extraction.permit_lifecycle_requirements"


class PermitLifecycleRequirementsSyntaxTest(unittest.TestCase):
    def test_target_module_imports_when_present(self) -> None:
        try:
            module = importlib.import_module(TARGET_MODULE)
        except ModuleNotFoundError as exc:
            if exc.name == TARGET_MODULE:
                self.skipTest(f"{TARGET_MODULE} is not present yet")
            raise

        self.assertEqual(module.__name__, TARGET_MODULE)


if __name__ == "__main__":
    unittest.main()
