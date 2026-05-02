"""Fixture-only guardrail checks for the FCC wireless application workflow."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from urllib.parse import urlparse


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "guardrails" / "fcc_wireless_application_workflow.json"
FORBIDDEN_KEYS = {
    "authorization",
    "authState",
    "body",
    "captcha",
    "cookie",
    "credentials",
    "mfa",
    "password",
    "rawBody",
    "rawHtml",
    "screenshot",
    "session",
    "storageState",
    "token",
    "trace",
    "uploadPayload",
}
PUBLIC_HOSTS = {"www.portland.gov", "devhub.portlandoregon.gov"}


class FccWirelessGuardrailFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture = json.load(fixture_file)

    def test_fixture_is_redacted_public_and_source_backed(self) -> None:
        self.assertTrue(self.fixture["fixtureOnly"])
        self.assertTrue(self.fixture["userCase"]["redacted"])
        self.assert_forbidden_keys_absent(self.fixture)

        source_ids = {source["sourceId"] for source in self.fixture["provenance"]}
        self.assertGreaterEqual(len(source_ids), 3)
        for source in self.fixture["provenance"]:
            parsed = urlparse(source["url"])
            self.assertEqual(parsed.scheme, "https")
            self.assertIn(parsed.netloc, PUBLIC_HOSTS)
            self.assertTrue(source["capturedAt"].endswith("Z"))

        for fact in self.fixture["processModel"]["requiredFacts"]:
            self.assertIn(fact["sourceId"], source_ids)
        for group in self.fixture["processModel"]["documentGroups"]:
            for document in group["documents"]:
                self.assertIn(document["sourceId"], source_ids)
        for gate in self.fixture["processModel"]["actionGates"]:
            self.assertIn(gate["sourceId"], source_ids)

    def test_missing_facts_are_compiled_from_required_unknown_facts(self) -> None:
        known_facts = self.fixture["userCase"]["knownFacts"]
        required_facts = self.fixture["processModel"]["requiredFacts"]
        expected_missing = sorted(
            fact["id"]
            for fact in required_facts
            if fact["required"] and known_facts.get(fact["id"]) is not True
        )

        compiled_missing = sorted(self.fixture["compiledGuardrails"]["missingFacts"])
        self.assertEqual(
            compiled_missing,
            expected_missing,
            "compiler fixture should request only required FCC wireless facts not already known",
        )
        self.assertEqual(
            compiled_missing,
            sorted(
                [
                    "fact_facility_class",
                    "fact_owner_authorization_status",
                    "fact_proposed_antenna_height",
                    "fact_rf_compliance_prepared",
                ]
            ),
        )

    def test_required_document_groups_are_compiled_from_missing_fixture_files(self) -> None:
        inventory = self.fixture["userCase"]["documentInventory"]
        expected_groups = []
        for group in self.fixture["processModel"]["documentGroups"]:
            missing_documents = [
                document["id"]
                for document in group["documents"]
                if document["required"] and not inventory[document["id"]]["present"]
            ]
            if missing_documents:
                expected_groups.append({"groupId": group["id"], "missingDocumentIds": missing_documents})

        self.assertEqual(self.fixture["compiledGuardrails"]["missingDocumentGroups"], expected_groups)
        missing_group_ids = {group["groupId"] for group in expected_groups}
        self.assertEqual(
            missing_group_ids,
            {
                "group_application_packet",
                "group_wireless_plans",
                "group_technical_reports",
                "group_authorization",
            },
        )

    def test_payment_stop_point_requires_exact_confirmation(self) -> None:
        gate = self.gate_by_action("pay_intake_fees")
        self.assertEqual(gate["classification"], "financial")
        self.assertTrue(gate["stopPoint"])
        self.assertTrue(gate["requiresExactConfirmation"])
        self.assertFalse(self.fixture["userCase"]["confirmations"]["pay_intake_fees"])
        self.assertIn("gate_pay_intake_fees", self.compiled_stop_gate_ids())

    def test_correction_upload_stop_points_require_exact_confirmation(self) -> None:
        for action in ("upload_official_corrections", "certify_corrections"):
            gate = self.gate_by_action(action)
            self.assertEqual(gate["classification"], "consequential")
            self.assertEqual(gate["stage"], "corrections")
            self.assertTrue(gate["stopPoint"])
            self.assertTrue(gate["requiresExactConfirmation"])
            self.assertFalse(self.fixture["userCase"]["confirmations"][action])
            self.assertIn(gate["id"], self.compiled_stop_gate_ids())

    def test_inspection_and_finalization_stop_points_require_exact_confirmation(self) -> None:
        expected = {
            "schedule_inspection": "inspection",
            "request_finalization": "finalization",
        }
        for action, stage in expected.items():
            gate = self.gate_by_action(action)
            self.assertEqual(gate["classification"], "consequential")
            self.assertEqual(gate["stage"], stage)
            self.assertTrue(gate["stopPoint"])
            self.assertTrue(gate["requiresExactConfirmation"])
            self.assertFalse(self.fixture["userCase"]["confirmations"][action])
            self.assertIn(gate["id"], self.compiled_stop_gate_ids())

    def test_compiled_preview_actions_do_not_include_live_or_irreversible_actions(self) -> None:
        self.assertEqual(
            set(self.fixture["compiledGuardrails"]["allowedWithoutConfirmation"]),
            {"read_public_guidance", "preview_missing_information", "save_reversible_draft"},
        )
        stopped_actions = {stop["action"] for stop in self.fixture["compiledGuardrails"]["stopPoints"]}
        self.assertIn("pay_intake_fees", stopped_actions)
        self.assertIn("upload_official_corrections", stopped_actions)
        self.assertIn("certify_corrections", stopped_actions)
        self.assertIn("schedule_inspection", stopped_actions)
        self.assertIn("request_finalization", stopped_actions)

    def gate_by_action(self, action: str) -> dict[str, object]:
        matches = [gate for gate in self.fixture["processModel"]["actionGates"] if gate["action"] == action]
        self.assertEqual(len(matches), 1)
        return matches[0]

    def compiled_stop_gate_ids(self) -> set[str]:
        return {stop["gateId"] for stop in self.fixture["compiledGuardrails"]["stopPoints"]}

    def assert_forbidden_keys_absent(self, value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                self.assertNotIn(key, FORBIDDEN_KEYS)
                self.assert_forbidden_keys_absent(child)
        elif isinstance(value, list):
            for child in value:
                self.assert_forbidden_keys_absent(child)


if __name__ == "__main__":
    unittest.main()
