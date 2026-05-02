"""Syntax-first repair test for ppd.contracts.source_freshness.

This test intentionally loads only the source_freshness module file. It catches
invalid Python annotation syntax before broad source freshness validation resumes.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "contracts" / "source_freshness.py"
MODULE_NAME = "_ppd_source_freshness_syntax_probe"


class SourceFreshnessSyntaxTest(unittest.TestCase):
    def test_source_freshness_imports_with_valid_annotation_syntax(self) -> None:
        self.assertTrue(MODULE_PATH.exists(), "ppd.contracts.source_freshness must exist")

        source = MODULE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(MODULE_PATH))
        annotation_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.AnnAssign)]
        for node in annotation_nodes:
            self.assertIsNotNone(node.target, "annotated assignment must have a target")
            self.assertIsNotNone(node.annotation, "annotated assignment must have an annotation")

        spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)

        module = importlib.util.module_from_spec(spec)
        previous_module = sys.modules.get(MODULE_NAME)
        sys.modules[MODULE_NAME] = module
        try:
            spec.loader.exec_module(module)
        finally:
            if previous_module is None:
                sys.modules.pop(MODULE_NAME, None)
            else:
                sys.modules[MODULE_NAME] = previous_module

        self.assertEqual(1, module.SOURCE_FRESHNESS_CONTRACT_VERSION)


if __name__ == "__main__":
    unittest.main()
