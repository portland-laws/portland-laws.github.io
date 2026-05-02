"""Fixture validation for PP&D requirement-to-process dependency graphs."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from ppd.logic.requirement_process_dependency_graph import (
    validate_requirement_process_dependency_graph,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "requirement_process_dependency_graph.json"


class RequirementProcessDependencyGraphTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_valid_graph_has_no_findings(self) -> None:
        findings = validate_requirement_process_dependency_graph(self.fixture["validGraph"])
        self.assertEqual([], findings)

    def test_invalid_graph_cases_fail_closed(self) -> None:
        valid_graph = self.fixture["validGraph"]
        for invalid_case in self.fixture["invalidCases"]:
            with self.subTest(case_id=invalid_case["caseId"]):
                mutated = _apply_mutation(valid_graph, invalid_case["mutate"])
                findings = validate_requirement_process_dependency_graph(mutated)
                reasons = "\n".join(finding.reason for finding in findings)
                self.assertIn(invalid_case["expectedFinding"], reasons)


def _apply_mutation(graph: dict[str, object], mutation: dict[str, object]) -> dict[str, object]:
    mutated = copy.deepcopy(graph)

    for replacement in mutation.get("nodes", []):
        if not isinstance(replacement, dict):
            continue
        node_id = replacement.get("id")
        nodes = mutated.get("nodes", [])
        if isinstance(nodes, list):
            _merge_or_append_by_id(nodes, node_id, replacement)

    for replacement in mutation.get("edges", []):
        if not isinstance(replacement, dict):
            continue
        edge_id = replacement.get("id")
        edges = mutated.get("edges", [])
        if isinstance(edges, list):
            _merge_or_append_by_id(edges, edge_id, replacement)

    return mutated


def _merge_or_append_by_id(items: list[object], item_id: object, replacement: dict[str, object]) -> None:
    for index, item in enumerate(items):
        if isinstance(item, dict) and item.get("id") == item_id:
            merged = copy.deepcopy(item)
            merged.update(replacement)
            items[index] = merged
            return
    items.append(copy.deepcopy(replacement))


if __name__ == "__main__":
    unittest.main()
