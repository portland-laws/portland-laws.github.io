"""Syntax-first import test for Urban Forestry permit requirements.

This test deliberately imports only ppd.extraction.urban_forestry_permit_requirements.
It must stay narrower than any future Urban Forestry fixture or requirement
validation so SyntaxError failures are reported before broader checks run.
"""

import importlib
import unittest


TARGET_MODULE = "ppd.extraction.urban_forestry_permit_requirements"


class UrbanForestryPermitRequirementsSyntaxFirstImportTest(unittest.TestCase):
    def test_imports_target_module_before_broad_requirement_validation(self):
        module = importlib.import_module(TARGET_MODULE)

        self.assertEqual(module.MODULE_STATUS, "syntax_first_import_ready")
        self.assertEqual(module.module_status(), "syntax_first_import_ready")


if __name__ == "__main__":
    unittest.main()
