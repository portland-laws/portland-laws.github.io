"""Validate checkbox-130 supersession decision fixtures for checkbox-108.

The fixture is intentionally deterministic and task-board scoped. It proves that
missing evidence keeps checkbox-108 parked, while complete accepted-work evidence
only recommends a task-board supersession update.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "checkbox_131"
    / "checkbox_130_supersede_decision.json"
)

PRIVATE_OR_LIVE_MARKERS = (
    "ppd/data/private",
    "ppd\\data\\private",
    "ppd/data/raw",
    "ppd\\data\\raw",
    "devhub/session",
    "devhub\\session",
    "storage_state",
    "auth_state",
    "trace.zip",
    "traces/",
    "screenshots/",
    "downloads/",
    "public/corpus/portland-or/current",
    "src/lib/logic",
    "ipfs_datasets_py/.daemon",
)

FORBIDDEN_ARTIFACT_KINDS = {
    "crawler_code",
    "crawl_contract",
    "public_corpus_fixture",
    "raw_crawl_output",
    "network_automation",
    "schema_rewrite",
    "typescript_logic_ledger",
    "private_devhub_session",
}


class Checkbox131SupersessionDecisionTest(unittest.TestCase):
    maxDiff = None

    def load_fixture(self) -> dict[str, Any]:
        with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
            fixture = json.load(fixture_file)
        self.assertIsInstance(fixture, dict)
        return fixture

    def test_fixture_has_unique_cases_and_no_private_or_live_artifact_paths(self) -> None:
        fixture = self.load_fixture()
        cases = fixture.get("cases")
        self.assertIsInstance(cases, list)
        self.assertEqual(2, len(cases))

        case_ids = [case.get("caseId") for case in cases]
        self.assertEqual(len(case_ids), len(set(case_ids)))

        serialized = json.dumps(fixture, sort_keys=True)
        lowered = serialized.lower()
        for marker in PRIVATE_OR_LIVE_MARKERS:
            self.assertNotIn(marker.lower(), lowered)

        self.assertEqual("checkbox-131", fixture.get("taskId"))
        self.assertEqual("checkbox-130", fixture.get("decisionFixtureFor"))
        self.assertEqual("checkbox-108", fixture.get("parkedTaskId"))

    def test_missing_evidence_keeps_checkbox_108_parked(self) -> None:
        fixture = self.load_fixture()
        missing_case = self.case_by_id(fixture, "missing_evidence_keeps_checkbox_108_parked")

        self.assertEqual("checkbox-108", missing_case.get("parkedTaskId"))
        self.assertEqual("park", missing_case.get("decision"))
        self.assertEqual("missing_supersession_evidence", missing_case.get("reason"))
        self.assertEqual(False, missing_case.get("taskBoardUpdateAllowed"))
        self.assertEqual([], missing_case.get("taskBoardOnlyRecommendations"))

        missing_evidence = missing_case.get("missingEvidence")
        self.assertIsInstance(missing_evidence, list)
        self.assertGreaterEqual(len(missing_evidence), 1)
        self.assertIn("accepted_validation_evidence_for_checkbox_130", missing_evidence)

        present_evidence = missing_case.get("presentEvidence")
        self.assertIsInstance(present_evidence, list)
        self.assertNotIn("accepted_validation_evidence_for_checkbox_130", present_evidence)

    def test_complete_evidence_produces_task_board_only_supersession_recommendation(self) -> None:
        fixture = self.load_fixture()
        complete_case = self.case_by_id(
            fixture,
            "complete_evidence_recommends_task_board_only_supersession",
        )

        self.assertEqual("checkbox-108", complete_case.get("parkedTaskId"))
        self.assertEqual("recommend_supersession", complete_case.get("decision"))
        self.assertEqual("task-board-only", complete_case.get("recommendationScope"))
        self.assertEqual(True, complete_case.get("taskBoardUpdateAllowed"))
        self.assertEqual([], complete_case.get("missingEvidence"))

        required_evidence = set(complete_case.get("requiredEvidence", []))
        present_evidence = set(complete_case.get("presentEvidence", []))
        self.assertTrue(required_evidence)
        self.assertTrue(required_evidence.issubset(present_evidence))

        recommendations = complete_case.get("taskBoardOnlyRecommendations")
        self.assertIsInstance(recommendations, list)
        self.assertEqual(1, len(recommendations))
        recommendation = recommendations[0]
        self.assertEqual("mark_superseded", recommendation.get("operation"))
        self.assertEqual("checkbox-108", recommendation.get("targetTaskId"))
        self.assertEqual("checkbox-130", recommendation.get("supersededByTaskId"))
        self.assertEqual("ppd/daemon/task-board.md", recommendation.get("allowedPath"))

        artifact_kinds = set(complete_case.get("artifactKinds", []))
        self.assertFalse(FORBIDDEN_ARTIFACT_KINDS.intersection(artifact_kinds))
        self.assertEqual(["task_board_markdown"], complete_case.get("artifactKinds"))

    @staticmethod
    def case_by_id(fixture: dict[str, Any], case_id: str) -> dict[str, Any]:
        cases = fixture.get("cases", [])
        for case in cases:
            if case.get("caseId") == case_id:
                return case
        raise AssertionError(f"fixture case not found: {case_id}")


if __name__ == "__main__":
    unittest.main()
