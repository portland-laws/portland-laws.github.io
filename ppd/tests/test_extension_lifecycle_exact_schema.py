"""Exact-schema and mutation tests for extension lifecycle fixture recovery.

This test intentionally loads only the two accepted lifecycle fixtures. The
extension evidence map carries source-inventory category references; committed
evidence ids are validated from the process skeleton only.
"""

from __future__ import annotations

from copy import deepcopy
import json
import unittest
from pathlib import Path
from typing import Any, Callable


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "lifecycle"
SKELETON_PATH = FIXTURE_DIR / "extension_lifecycle_process_skeleton.json"
EVIDENCE_MAP_PATH = FIXTURE_DIR / "extension_lifecycle_evidence_map.json"

SKELETON_KEYS = {
    "schemaVersion",
    "fixtureType",
    "fixtureOnly",
    "processId",
    "lifecycleAction",
    "evidenceMapFixture",
    "sourceInventoryFixture",
    "sourceInventoryCategoryId",
    "sourceInventoryEvidenceIds",
    "authoritySources",
    "requiredFacts",
    "requiredDocuments",
    "userDecisions",
    "actionGates",
    "noLiveAutomationNotes",
    "excludedArtifacts",
}

AUTHORITY_SOURCE_KEYS = {
    "evidenceId",
    "categoryId",
    "title",
    "sourceUrl",
    "canonicalUrl",
    "authorityLabel",
    "recrawlCadence",
    "capturedAt",
}
FACT_KEYS = {"id", "label", "requiredFor", "evidenceIds"}
DOCUMENT_KEYS = {"id", "label", "requiredFor", "evidenceIds", "notes"}
DECISION_KEYS = {"id", "prompt", "requiredBefore", "evidenceIds"}
ACTION_GATE_BASE_KEYS = {
    "id",
    "classification",
    "action",
    "allowedInFixture",
    "requiresExactUserConfirmation",
    "evidenceIds",
}
ACTION_GATE_STOP_KEYS = ACTION_GATE_BASE_KEYS | {"stopBeforeAction"}
NO_LIVE_KEYS = {
    "liveCrawling",
    "devhubLogin",
    "officialExtensionAction",
    "paymentAction",
    "submissionAction",
    "uploadAction",
    "certificationAction",
    "captchaOrMfaAutomation",
    "notes",
}
EVIDENCE_MAP_KEYS = {
    "schemaVersion",
    "fixtureType",
    "sourceInventoryFixture",
    "generatedFrom",
    "categories",
}
EVIDENCE_CATEGORY_KEYS = {
    "categoryId",
    "lifecycleAction",
    "description",
    "sourceInventoryEvidenceIds",
    "requiredCitationFields",
    "excludedArtifacts",
    "automationBoundary",
}
AUTOMATION_BOUNDARY_KEYS = {
    "liveCrawling",
    "devhubLogin",
    "officialExtensionAction",
    "paymentAction",
    "submissionAction",
    "uploadAction",
}
EXPECTED_EVIDENCE_ID = "ppd_lifecycle_extension_reactivation_public_guidance"
EXPECTED_CATEGORY_ID = "permit_extension_guidance"


class ExtensionLifecycleExactSchemaTest(unittest.TestCase):
    def load_json(self, path: Path) -> dict[str, Any]:
        self.assertTrue(path.is_file(), f"missing fixture: {path}")
        with path.open(encoding="utf-8") as fixture_file:
            data = json.load(fixture_file)
        self.assertIsInstance(data, dict)
        return data

    def validate_extension_lifecycle_fixtures(
        self,
        skeleton: dict[str, Any],
        evidence_map: dict[str, Any],
    ) -> None:
        self.assertEqual(set(skeleton), SKELETON_KEYS)
        self.assertEqual(skeleton["schemaVersion"], 1)
        self.assertEqual(skeleton["fixtureType"], "ppd_lifecycle_extension_process_skeleton")
        self.assertIs(skeleton["fixtureOnly"], True)
        self.assertEqual(skeleton["lifecycleAction"], "extension")
        self.assertEqual(skeleton["sourceInventoryCategoryId"], EXPECTED_CATEGORY_ID)
        self.assertEqual(skeleton["sourceInventoryEvidenceIds"], [EXPECTED_EVIDENCE_ID])

        self.assertEqual(set(evidence_map), EVIDENCE_MAP_KEYS)
        self.assertEqual(evidence_map["schemaVersion"], 1)
        self.assertEqual(evidence_map["fixtureType"], "ppd_lifecycle_extension_evidence_map")
        self.assertNotIn("evidenceIds", evidence_map)
        self.assertEqual(len(evidence_map["categories"]), 1)

        category = evidence_map["categories"][0]
        self.assertEqual(set(category), EVIDENCE_CATEGORY_KEYS)
        self.assertEqual(category["categoryId"], EXPECTED_CATEGORY_ID)
        self.assertEqual(category["lifecycleAction"], "extension")
        self.assertEqual(category["sourceInventoryEvidenceIds"], [EXPECTED_CATEGORY_ID])
        self.assertNotIn(EXPECTED_EVIDENCE_ID, category["sourceInventoryEvidenceIds"])
        self.assertEqual(set(category["automationBoundary"]), AUTOMATION_BOUNDARY_KEYS)
        self.assertTrue(all(value is False for value in category["automationBoundary"].values()))

        authority_evidence_ids = set()
        for source in skeleton["authoritySources"]:
            self.assertEqual(set(source), AUTHORITY_SOURCE_KEYS)
            self.assertEqual(source["categoryId"], EXPECTED_CATEGORY_ID)
            self.assertTrue(source["sourceUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertEqual(source["sourceUrl"], source["canonicalUrl"])
            self.assertTrue(source["capturedAt"].endswith("Z"))
            authority_evidence_ids.add(source["evidenceId"])

        committed_evidence_ids = set(skeleton["sourceInventoryEvidenceIds"]) | authority_evidence_ids
        self.assertEqual(committed_evidence_ids, {EXPECTED_EVIDENCE_ID})

        for fact in skeleton["requiredFacts"]:
            self.assertEqual(set(fact), FACT_KEYS)
            self.assertEqual(fact["evidenceIds"], [EXPECTED_EVIDENCE_ID])
        self.assertGreaterEqual(len(skeleton["requiredFacts"]), 4)

        for document in skeleton["requiredDocuments"]:
            self.assertEqual(set(document), DOCUMENT_KEYS)
            self.assertEqual(document["evidenceIds"], [EXPECTED_EVIDENCE_ID])
            self.assertIn("does not download, upload, or submit", document["notes"])

        for decision in skeleton["userDecisions"]:
            self.assertEqual(set(decision), DECISION_KEYS)
            self.assertEqual(decision["evidenceIds"], [EXPECTED_EVIDENCE_ID])
        self.assertIn("confirm_official_extension_action", {item["id"] for item in skeleton["userDecisions"]})

        for gate in skeleton["actionGates"]:
            expected_keys = ACTION_GATE_STOP_KEYS if gate.get("stopBeforeAction") is True else ACTION_GATE_BASE_KEYS
            self.assertEqual(set(gate), expected_keys)
            self.assertEqual(gate["evidenceIds"], [EXPECTED_EVIDENCE_ID])
            if gate["classification"] in {"potentially_consequential", "financial"}:
                self.assertIs(gate["allowedInFixture"], False)
                self.assertIs(gate["requiresExactUserConfirmation"], True)
                self.assertIs(gate["stopBeforeAction"], True)

        no_live = skeleton["noLiveAutomationNotes"]
        self.assertEqual(set(no_live), NO_LIVE_KEYS)
        for key in NO_LIVE_KEYS - {"notes"}:
            self.assertIs(no_live[key], False)
        self.assertIn("does not authorize live crawling", no_live["notes"])

        excluded = set(skeleton["excludedArtifacts"])
        self.assertIn("python_modules", excluded)
        self.assertIn("typescript_modules", excluded)
        self.assertIn("official_action_automation", excluded)

    def test_extension_lifecycle_fixtures_have_exact_schema(self) -> None:
        skeleton = self.load_json(SKELETON_PATH)
        evidence_map = self.load_json(EVIDENCE_MAP_PATH)
        self.validate_extension_lifecycle_fixtures(skeleton, evidence_map)

    def test_extension_lifecycle_validator_rejects_single_missing_skeleton_fields(self) -> None:
        skeleton = self.load_json(SKELETON_PATH)
        evidence_map = self.load_json(EVIDENCE_MAP_PATH)

        mutations: dict[str, Callable[[dict[str, Any]], None]] = {
            "required fact citation evidence": lambda data: data["requiredFacts"][0].pop("evidenceIds"),
            "required document note": lambda data: data["requiredDocuments"][0].pop("notes"),
            "user decision citation evidence": lambda data: data["userDecisions"][0].pop("evidenceIds"),
            "authority source evidence id": lambda data: data["authoritySources"][0].pop("evidenceId"),
            "action gate citation evidence": lambda data: data["actionGates"][0].pop("evidenceIds"),
            "no-live-automation note": lambda data: data["noLiveAutomationNotes"].pop("notes"),
        }

        for name, mutate in mutations.items():
            with self.subTest(name=name):
                mutated = deepcopy(skeleton)
                mutate(mutated)
                with self.assertRaises(AssertionError):
                    self.validate_extension_lifecycle_fixtures(mutated, evidence_map)


if __name__ == "__main__":
    unittest.main()
