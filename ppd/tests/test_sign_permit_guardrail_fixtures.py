"""Fixture-only guardrail tests for the PP&D sign permit workflow."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "guardrails" / "sign_permit_workflow_guardrails.json"
_ALLOWED_HOSTS = {"www.portland.gov", "devhub.portlandoregon.gov", "www.portlandoregon.gov", "www.portlandmaps.com"}
_PRIVATE_MARKERS = (
    "password",
    "credential",
    "auth_state",
    "storage_state",
    "cookie",
    "token",
    "trace.zip",
    "screenshot",
    "ppd/data/private",
    "ppd/data/raw",
    "downloaded_documents",
)


class SignPermitGuardrailFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture = json.load(fixture_file)
        self.guardrails = {guardrail["id"]: guardrail for guardrail in self.fixture["compiledGuardrails"]}

    def test_fixture_is_public_redacted_and_source_backed(self) -> None:
        self.assertEqual(self.fixture["sourceMode"], "fixture_only")
        self.assertEqual(self.fixture["redactionStatus"], "redacted_public_fixture")
        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in _PRIVATE_MARKERS:
            self.assertNotIn(marker, serialized)

        source_ids = {source["id"] for source in self.fixture["authoritySources"]}
        self.assertGreaterEqual(len(source_ids), 2)
        for source in self.fixture["authoritySources"]:
            parsed = urlparse(source["canonicalUrl"])
            self.assertEqual(parsed.scheme, "https")
            self.assertIn(parsed.netloc, _ALLOWED_HOSTS)
            self.assertRegex(source["contentHash"], r"^sha256:[0-9a-f]{64}$")
            self.assertTrue(source["retrievedAt"].endswith("Z"))

        for guardrail in self.fixture["compiledGuardrails"]:
            self.assertTrue(set(guardrail["sourceIds"]).issubset(source_ids))
            self.assertTrue(guardrail["agentInstruction"].strip())

    def test_missing_fact_guardrail_reports_only_unknown_required_facts(self) -> None:
        known_fact_keys = set(self.fixture["knownUserCase"]["facts"].keys())
        required_by_predicate = {fact["id"]: fact["predicate"] for fact in self.fixture["requiredFacts"]}
        guardrail = self.guardrails["guard-missing-facts-before-submit"]

        self.assertEqual(guardrail["kind"], "missing_fact")
        self.assertEqual(guardrail["statusForKnownCase"], "blocked")
        self.assertEqual(
            guardrail["missingItemsForKnownCase"],
            ["fact-property-owner", "fact-sign-dimensions", "fact-installation-method"],
        )
        self.assertNotIn("fact-project-address", guardrail["missingItemsForKnownCase"])
        self.assertNotIn("fact-sign-type", guardrail["missingItemsForKnownCase"])

        for missing_fact_id in guardrail["missingItemsForKnownCase"]:
            self.assertIn(missing_fact_id, required_by_predicate)
            normalized_name = re.sub(r"^has_", "", required_by_predicate[missing_fact_id])
            self.assertNotIn(normalized_name, known_fact_keys)

    def test_required_document_group_guardrail_blocks_incomplete_sign_package(self) -> None:
        known_document_groups = set(self.fixture["knownUserCase"]["documents"].keys())
        guardrail = self.guardrails["guard-required-document-groups-before-upload"]

        self.assertEqual(guardrail["kind"], "required_document_group")
        self.assertEqual(guardrail["stage"], "document_preparation")
        self.assertEqual(guardrail["statusForKnownCase"], "blocked")
        self.assertIn("sign_elevation_or_drawings", guardrail["missingItemsForKnownCase"])
        self.assertIn(
            "structural_calculations_or_engineer_statement_or_owner_authorization",
            guardrail["missingItemsForKnownCase"],
        )
        self.assertTrue({"application_form", "site_plan"}.issubset(known_document_groups))

        document_group_ids = {group["id"] for group in self.fixture["requiredDocumentGroups"]}
        self.assertEqual(
            document_group_ids,
            {"doc-group-application", "doc-group-plans", "doc-group-supporting"},
        )

    def test_payment_stop_point_is_financial_and_requires_exact_confirmation(self) -> None:
        guardrail = self.guardrails["guard-payment-stop-point"]

        self.assertEqual(guardrail["kind"], "action_gate")
        self.assertEqual(guardrail["stage"], "fee_payment")
        self.assertEqual(guardrail["classification"], "financial")
        self.assertEqual(guardrail["statusForKnownCase"], "stop_required")
        self.assertIn("pay_fees", guardrail["prohibitedActions"])
        self.assertIn("enter_payment_details", guardrail["prohibitedActions"])
        self.assertIn("Exact session-specific user confirmation", guardrail["requiredConfirmation"])

    def test_correction_upload_stop_point_blocks_official_upload_and_certification(self) -> None:
        guardrail = self.guardrails["guard-correction-upload-stop-point"]

        self.assertEqual(guardrail["kind"], "action_gate")
        self.assertEqual(guardrail["stage"], "corrections")
        self.assertEqual(guardrail["classification"], "potentially_consequential")
        self.assertEqual(guardrail["statusForKnownCase"], "stop_required")
        self.assertEqual(
            set(guardrail["prohibitedActions"]),
            {"official_correction_upload", "certify_correction_response", "submit_correction_response"},
        )
        self.assertIn("preview is allowed", guardrail["agentInstruction"])

    def test_inspection_and_finalization_stop_points_are_consequential(self) -> None:
        inspection_guardrail = self.guardrails["guard-inspection-stop-point"]
        finalization_guardrail = self.guardrails["guard-finalization-stop-point"]

        self.assertEqual(inspection_guardrail["stage"], "inspections")
        self.assertEqual(inspection_guardrail["classification"], "potentially_consequential")
        self.assertEqual(inspection_guardrail["statusForKnownCase"], "stop_required")
        self.assertEqual(
            set(inspection_guardrail["prohibitedActions"]),
            {"schedule_inspection", "reschedule_inspection", "cancel_inspection"},
        )

        self.assertEqual(finalization_guardrail["stage"], "finalization")
        self.assertEqual(finalization_guardrail["classification"], "potentially_consequential")
        self.assertEqual(finalization_guardrail["statusForKnownCase"], "stop_required")
        self.assertTrue(
            {"submit_application", "certify_application", "accept_issuance_terms", "finalize_permit_request"}.issubset(
                set(finalization_guardrail["prohibitedActions"])
            )
        )
        self.assertIn("do not finalize", finalization_guardrail["agentInstruction"])

    def test_forbidden_automation_covers_irreversible_sign_workflow_actions(self) -> None:
        forbidden = set(self.fixture["forbiddenAutomation"])
        self.assertTrue(
            {
                "captcha",
                "mfa",
                "account_creation",
                "payment",
                "submission",
                "certification",
                "official_upload",
                "inspection_scheduling",
                "finalization",
            }.issubset(forbidden)
        )


if __name__ == "__main__":
    unittest.main()
