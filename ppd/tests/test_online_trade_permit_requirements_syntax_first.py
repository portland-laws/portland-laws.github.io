"""Syntax-first sentinel for online trade permit requirement extraction.

This test intentionally checks only ppd/extraction/online_trade_permit_requirements.py.
It compiles the target source before importing it so malformed Python fails before
broader online trade permit validation can run.
"""

from __future__ import annotations

import importlib.util
import py_compile
import unittest
from pathlib import Path


TARGET_MODULE_NAME = "ppd.extraction.online_trade_permit_requirements"
TARGET_MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "extraction"
    / "online_trade_permit_requirements.py"
)


class OnlineTradePermitRequirementsSyntaxFirstTest(unittest.TestCase):
    def test_online_trade_permit_requirements_imports_after_py_compile(self) -> None:
        if not TARGET_MODULE_PATH.exists():
            self.skipTest(f"{TARGET_MODULE_NAME} is not present yet")

        try:
            py_compile.compile(str(TARGET_MODULE_PATH), doraise=True)
        except py_compile.PyCompileError as exc:
            self.fail(f"{TARGET_MODULE_NAME} contains malformed Python: {exc.msg}")

        spec = importlib.util.spec_from_file_location(
            TARGET_MODULE_NAME,
            TARGET_MODULE_PATH,
        )
        self.assertIsNotNone(spec, f"could not create import spec for {TARGET_MODULE_NAME}")
        self.assertIsNotNone(spec.loader, f"missing loader for {TARGET_MODULE_NAME}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertEqual(module.__name__, TARGET_MODULE_NAME)


if __name__ == "__main__":
    unittest.main()
