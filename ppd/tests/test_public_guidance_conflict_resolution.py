"""Validate fixture-only public guidance conflict resolution behavior."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "conflict_resolution"
    / "public_guidance_conflict_single_pdf_process.json"
)


class PublicGuidanceConflictResolutionFixtureTest(unittest.TestCase):
    def test_conflicting_guidance_preserves_provenance_and_blocks_drafting(self) -> None:
        fixture = _load_fixture()

        self.assertEqual(fixture["schemaVersion"], 1)
        self.assertEqual(fixture["scenarioType"], "public_guidance_conflict_resolution")
        self.assertEqual(fixture["conflictStatus"], "unresolved")
        self.assertEqual(fixture["reviewStatus"], "review_needed")
        self.assertIs(fixture["humanResolutionRequired"], True)

        requirement_key = fixture["requirementKey"]
        sources = fixture["conflictingSources"]
        self.assertEqual(len(sources), 2)

        extracted_actions: set[str] = set()
        source_ids: set[str] = set()
        for source in sources:
            source_id = _required_text(source, "sourceId")
            self.assertNotIn(source_id, source_ids)
            source_ids.add(source_id)

            url = _required_text(source, "url")
            parsed = urlparse(url)
            self.assertEqual(parsed.scheme, "https")
            self.assertEqual(parsed.netloc, "www.portland.gov")
            self.assertTrue(parsed.path.startswith("/ppd/"))

            citation = _required_mapping(source, "citation")
            self.assertTrue(_required_text(citation, "anchor").startswith("#"))
            self.assertTrue(_required_text(citation, "quotedRequirement"))

            extracted_requirement = _required_mapping(source, "extractedRequirement")
            self.assertEqual(extracted_requirement["requirementKey"], requirement_key)
            self.assertEqual(
                extracted_requirement["requirementObject"],
                fixture["requirementObject"],
            )
            extracted_actions.add(_required_text(extracted_requirement, "normalizedAction"))

            provenance_chain = source.get("provenanceChain")
            self.assertIsInstance(provenance_chain, list)
            self.assertGreaterEqual(len(provenance_chain), 3)
            self.assertEqual(
                [entry["kind"] for entry in provenance_chain],
                ["source_index_record", "normalized_document", "extracted_requirement"],
            )
            self.assertEqual(
                provenance_chain[-1]["id"],
                extracted_requirement["requirementId"],
            )

        self.assertEqual(len(extracted_actions), 2)

        draft_gate = _required_mapping(fixture, "draftAutomationGate")
        self.assertIs(draft_gate["usableForDraftAutomation"], False)
        self.assertEqual(draft_gate["blockedUntil"], "human_resolution_required")
        self.assertEqual(draft_gate["blockedRequirementKey"], requirement_key)
        self.assertIn("rely_on_either_conflicting_source", draft_gate["prohibitedActions"])

        source_usability = draft_gate.get("sourceUsability")
        self.assertIsInstance(source_usability, list)
        self.assertEqual({entry["sourceId"] for entry in source_usability}, source_ids)
        for source_decision in source_usability:
            self.assertIs(source_decision["mayUseForDraftAutomation"], False)
            self.assertEqual(source_decision["reason"], "unresolved_conflict")

        expected = _required_mapping(fixture, "expectedResolutionBehavior")
        self.assertIs(expected["preserveAllProvenanceChains"], True)
        self.assertIs(expected["markRequirementReviewNeeded"], True)
        self.assertIs(expected["requireHumanResolutionBeforeDraftAutomation"], True)


def _load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise AssertionError("conflict-resolution fixture must be a JSON object")
    return data


def _required_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise AssertionError(f"{key} must be an object")
    return value


def _required_text(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AssertionError(f"{key} must be a non-empty string")
    return value


if __name__ == "__main__":
    unittest.main()
