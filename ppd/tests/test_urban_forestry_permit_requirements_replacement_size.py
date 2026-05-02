"""Size and shape guard for the Urban Forestry requirements extractor.

This test intentionally inspects only one implementation module. It is a
replacement-size guard for daemon proposals: broad generated modules should fail
before they become the accepted extractor shape.
"""

from __future__ import annotations

import ast
import importlib.util
import unittest
from pathlib import Path


MODULE_NAME = "ppd.extraction.urban_forestry_permit_requirements"
MAX_PHYSICAL_LINES = 180


class UrbanForestryPermitRequirementsReplacementSizeTest(unittest.TestCase):
    def test_extractor_stays_small_and_avoids_dataclasses(self) -> None:
        module_path = _module_path(MODULE_NAME)
        source = module_path.read_text(encoding="utf-8")
        physical_lines = source.splitlines()

        self.assertLessEqual(
            len(physical_lines),
            MAX_PHYSICAL_LINES,
            (
                f"{MODULE_NAME} must stay under {MAX_PHYSICAL_LINES} physical "
                "lines; split broad generated code into focused fixtures or "
                "smaller helpers before proposing this extractor replacement"
            ),
        )

        tree = ast.parse(source, filename=str(module_path))
        dataclass_uses = _dataclass_uses(tree)
        self.assertEqual(
            [],
            dataclass_uses,
            "Urban Forestry extractor replacements must not use dataclasses: "
            + "; ".join(dataclass_uses),
        )


def _module_path(module_name: str) -> Path:
    spec = importlib.util.find_spec(module_name)
    if spec is None or spec.origin is None:
        raise AssertionError(f"could not find module {module_name}")
    path = Path(spec.origin)
    if path.name == "__init__.py":
        raise AssertionError(f"{module_name} resolved to a package, expected one module file")
    return path


def _dataclass_uses(tree: ast.AST) -> list[str]:
    findings: list[str] = []
    imported_dataclass_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "dataclasses" or alias.name.startswith("dataclasses."):
                    findings.append(f"line {node.lineno}: imports dataclasses")
        elif isinstance(node, ast.ImportFrom) and node.module == "dataclasses":
            for alias in node.names:
                imported_name = alias.asname or alias.name
                imported_dataclass_names.add(imported_name)
            findings.append(f"line {node.lineno}: imports from dataclasses")

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for decorator in node.decorator_list:
                if _is_dataclass_reference(decorator, imported_dataclass_names):
                    findings.append(f"line {node.lineno}: decorates class {node.name} as dataclass")
        elif isinstance(node, ast.Call) and _is_dataclass_reference(node.func, imported_dataclass_names):
            findings.append(f"line {node.lineno}: calls dataclass helper")
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "dataclasses":
                findings.append(f"line {node.lineno}: references dataclasses.{node.attr}")

    return sorted(set(findings))


def _is_dataclass_reference(node: ast.AST, imported_dataclass_names: set[str]) -> bool:
    if isinstance(node, ast.Name):
        return node.id in imported_dataclass_names or node.id == "dataclass"
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return node.value.id == "dataclasses" and node.attr in {"dataclass", "field", "make_dataclass"}
    return False


if __name__ == "__main__":
    unittest.main()
