"""Validate the cancellation/refund lifecycle skeleton fixture.

The fixture is intentionally JSON-only and derives its citations from the
existing lifecycle source inventory. These tests avoid live crawl, DevHub login,
payment, cancellation, refund submission, and browser automation behavior.
"""

from __future__ import annotations

from copy import deepcopy
import json
import unittest
from pathlib import Path
from typing import Any, Callable


FIXTURE_ROOT = Path(__file__).parent / "fixtures"
LIFECYCLE_FIXTURE_PATH = FIXTURE_ROOT / "lifecycle" / "cancellation_refund_lifecycle_process_skeleton.json"
SOURCE_INVENTORY_PATH = FIXTURE_ROOT / "source_inventory" / "permit_lifecycle_source_coverage_report.json"

EXPECTED_CANCELLATION_EVIDENCE_ID = "ppd_lifecycle_cancellation_public_guidance"
EXPECTED_REFUND_EVIDENCE_ID = "ppd_lifecycle_refund_public_guidance"
EXPECTED_EVIDENCE_IDS = {
    EXPECTED_CANCELLATION_EVIDENCE_ID,
    EXPECTED_REFUND_EVIDENCE_ID,
}
EXPECTED_CATEGORY_IDS = {
    "permit_cancellation_guidance",
    "permit_refund_guidance",
}

SKELETON_KEYS = {
    "schemaVersion",
    "fixtureType",
    "fixtureOnly",
    "processId",
    "lifecycleActions",
    "sourceInventoryFixture",
    "sourceInventoryCategoryIds",
    "sourceInventoryEvidenceIds",
    "authoritySources",
    "requiredFacts",
    "requiredDocuments",
    "userDecisions",
    "feePaymentGates",
    "actionGates",
    "explicitStopGates",
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
GATE_KEYS = {
    "id",
    "classification",
    "action",
    "allowedInFixture",
    "requiresExactUserConfirmation",
    "stopBeforeAction",
    "evidenceIds",
}
FEE_GATE_KEYS = GATE_KEYS | {"financialAction"}
STOP_GATE_KEYS = {"id", "blockedAction", "reason", "evidenceIds"}
NO_LIVE_KEYS = {
    "liveCrawling",
    "devhubLogin",
    "officialCancellationAction",
    "officialRefundAction",
    "paymentAction",
    "submissionAction",
    "uploadAction",
    "certificationAction",
    "captchaOrMfaAutomation",
    "notes",
}


class CancellationRefundLifecycleSkeletonTest(unittest.TestCase):
    def load_json(self, path: Path) -> dict[str, Any]:
        self.assertTrue(path.is_file(), f"missing fixture: {path}")
        with path.open(encoding="utf-8") as fixture_file:
            data = json.load(fixture_file)
        self.assertIsInstance(data, dict)
        return data

    def inventory_evidence_by_id(self, inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
        evidence = inventory.get("evidence")
        self.assertIsInstance(evidence, list)
        by_id: dict[str, dict[str, Any]] = {}
        for item in evidence:
            self.assertIsInstance(item, dict)
            evidence_id = item.get("id")
            self.assertIsInstance(evidence_id, str)
            by_id[evidence_id] = item
        return by_id

    def assert_known_evidence_ids(self, evidence_ids: list[str], inventory_ids: set[str]) -> None:
        self.assertIsInstance(evidence_ids, list)
        self.assertTrue(evidence_ids)
        for evidence_id in evidence_ids:
            self.assertIn(evidence_id, EXPECTED_EVIDENCE_IDS)
            self.assertIn(evidence_id, inventory_ids)

    def validate_cancellation_refund_skeleton(
        self,
        skeleton: dict[str, Any],
        inventory: dict[str, Any],
    ) -> None:
        self.assertEqual(set(skeleton), SKELETON_KEYS)
        self.assertEqual(skeleton["schemaVersion"], 1)
        self.assertEqual(skeleton["fixtureType"], "ppd_lifecycle_cancellation_refund_process_skeleton")
        self.assertIs(skeleton["fixtureOnly"], True)
        self.assertEqual(skeleton["processId"], "permit_cancellation_refund_lifecycle_skeleton")
        self.assertEqual(skeleton["lifecycleActions"], ["cancellation", "refund"])
        self.assertEqual(set(skeleton["sourceInventoryCategoryIds"]), EXPECTED_CATEGORY_IDS)
        self.assertEqual(set(skeleton["sourceInventoryEvidenceIds"]), EXPECTED_EVIDENCE_IDS)

        evidence_by_id = self.inventory_evidence_by_id(inventory)
        inventory_ids = set(evidence_by_id)
        self.assertTrue(EXPECTED_EVIDENCE_IDS.issubset(inventory_ids))

        for evidence_id in EXPECTED_EVIDENCE_IDS:
            evidence = evidence_by_id[evidence_id]
            self.assertIn(evidence["categoryId"], EXPECTED_CATEGORY_IDS)
            self.assertIn("authorityLabel", evidence)
            self.assertIn("recrawlCadence", evidence)
            self.assertTrue(evidence["sourceUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertEqual(evidence["sourceUrl"], evidence["canonicalUrl"])

        authority_ids = set()
        for source in skeleton["authoritySources"]:
            self.assertEqual(set(source), AUTHORITY_SOURCE_KEYS)
            self.assertIn(source["evidenceId"], EXPECTED_EVIDENCE_IDS)
            self.assertIn(source["categoryId"], EXPECTED_CATEGORY_IDS)
            self.assertTrue(source["sourceUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertEqual(source["sourceUrl"], source["canonicalUrl"])
            self.assertTrue(source["authorityLabel"].startswith("Portland Permitting & Development"))
            self.assertTrue(source["capturedAt"].endswith("Z"))
            authority_ids.add(source["evidenceId"])
        self.assertEqual(authority_ids, EXPECTED_EVIDENCE_IDS)

        for fact in skeleton["requiredFacts"]:
            self.assertEqual(set(fact), FACT_KEYS)
            self.assert_known_evidence_ids(fact["evidenceIds"], inventory_ids)
        self.assertGreaterEqual(len(skeleton["requiredFacts"]), 5)

        for document in skeleton["requiredDocuments"]:
            self.assertEqual(set(document), DOCUMENT_KEYS)
            self.assert_known_evidence_ids(document["evidenceIds"], inventory_ids)
            self.assertIn("does not", document["notes"])
        self.assertGreaterEqual(len(skeleton["requiredDocuments"]), 2)

        decision_ids = set()
        for decision in skeleton["userDecisions"]:
            self.assertEqual(set(decision), DECISION_KEYS)
            self.assert_known_evidence_ids(decision["evidenceIds"], inventory_ids)
            decision_ids.add(decision["id"])
        self.assertIn("confirm_official_cancellation_action", decision_ids)
        self.assertIn("confirm_official_refund_action", decision_ids)

        for gate in skeleton["feePaymentGates"]:
            self.assertEqual(set(gate), FEE_GATE_KEYS)
            self.assert_known_evidence_ids(gate["evidenceIds"], inventory_ids)
            if gate["classification"] == "financial":
                self.assertIs(gate["allowedInFixture"], False)
                self.assertIs(gate["requiresExactUserConfirmation"], True)
                self.assertIs(gate["stopBeforeAction"], True)
                self.assertIs(gate["financialAction"], True)
        self.assertTrue(any(gate["classification"] == "financial" for gate in skeleton["feePaymentGates"]))

        for gate in skeleton["actionGates"]:
            self.assertEqual(set(gate), GATE_KEYS)
            self.assert_known_evidence_ids(gate["evidenceIds"], inventory_ids)
            if gate["classification"] in {"potentially_consequential", "financial"}:
                self.assertIs(gate["allowedInFixture"], False)
                self.assertIs(gate["requiresExactUserConfirmation"], True)
                self.assertIs(gate["stopBeforeAction"], True)

        stop_gate_ids = set()
        for gate in skeleton["explicitStopGates"]:
            self.assertEqual(set(gate), STOP_GATE_KEYS)
            self.assert_known_evidence_ids(gate["evidenceIds"], inventory_ids)
            stop_gate_ids.add(gate["id"])
        self.assertIn("stop_before_official_cancellation", stop_gate_ids)
        self.assertIn("stop_before_official_refund_request", stop_gate_ids)
        self.assertIn("stop_before_payment_details_or_fee_payment", stop_gate_ids)

        no_live = skeleton["noLiveAutomationNotes"]
        self.assertEqual(set(no_live), NO_LIVE_KEYS)
        for key in NO_LIVE_KEYS - {"notes"}:
            self.assertIs(no_live[key], False)
        self.assertIn("does not authorize live crawling", no_live["notes"])

        excluded = set(skeleton["excludedArtifacts"])
        self.assertIn("python_modules", excluded)
        self.assertIn("typescript_modules", excluded)
        self.assertIn("official_action_automation", excluded)
        self.assertIn("downloaded_documents", excluded)
        self.assertIn("credentials", excluded)

    def test_cancellation_refund_fixture_has_required_lifecycle_gates(self) -> None:
        skeleton = self.load_json(LIFECYCLE_FIXTURE_PATH)
        inventory = self.load_json(SOURCE_INVENTORY_PATH)
        self.validate_cancellation_refund_skeleton(skeleton, inventory)

    def test_cancellation_refund_validator_rejects_missing_gate_fields(self) -> None:
        skeleton = self.load_json(LIFECYCLE_FIXTURE_PATH)
        inventory = self.load_json(SOURCE_INVENTORY_PATH)

        mutations: dict[str, Callable[[dict[str, Any]], None]] = {
            "missing user decision evidence": lambda data: data["userDecisions"][0].pop("evidenceIds"),
            "missing fee payment gate evidence": lambda data: data["feePaymentGates"][0].pop("evidenceIds"),
            "missing financial stop flag": lambda data: data["feePaymentGates"][1].pop("stopBeforeAction"),
            "missing financial action flag": lambda data: data["feePaymentGates"][1].pop("financialAction"),
            "missing action gate citation": lambda data: data["actionGates"][0].pop("evidenceIds"),
            "missing consequential stop flag": lambda data: data["actionGates"][4].pop("stopBeforeAction"),
            "missing explicit stop gate reason": lambda data: data["explicitStopGates"][0].pop("reason"),
            "missing no-live payment flag": lambda data: data["noLiveAutomationNotes"].pop("paymentAction"),
        }

        for name, mutate in mutations.items():
            with self.subTest(name=name):
                mutated = deepcopy(skeleton)
                mutate(mutated)
                with self.assertRaises(AssertionError):
                    self.validate_cancellation_refund_skeleton(mutated, inventory)


if __name__ == "__main__":
    unittest.main()
