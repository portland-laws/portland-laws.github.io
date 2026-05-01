import copy
import json
import unittest
from pathlib import Path
from typing import Any

from ppd.logic import GuardrailCompilerError, compile_requirement_fixture


REQUIREMENT_FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "requirement_extraction"
    / "ppd_public_guidance_requirement_fixture.json"
)

GUARDRAIL_FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "guardrail_compiler"
    / "single_pdf_guardrail_cases.json"
)


class GuardrailCompilerTests(unittest.TestCase):
    def load_requirement_fixture(self):
        return json.loads(REQUIREMENT_FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_compiles_fixture_requirements_to_guardrails(self):
        compiled = compile_requirement_fixture(self.load_requirement_fixture())

        self.assertEqual(compiled.fixture_id, "ppd_public_guidance_requirement_fixture_v1")
        self.assertEqual(len(compiled.guardrails), 7)
        self.assertFalse(compiled.validate())

        requirement_ids = {guardrail.requirement_id for guardrail in compiled.guardrails}
        self.assertIn("req-stop-before-submission-obligation", requirement_ids)
        self.assertIn("req-fee-payment-action-gate", requirement_ids)

    def test_preserves_source_support_map(self):
        compiled = compile_requirement_fixture(self.load_requirement_fixture())

        for guardrail in compiled.guardrails:
            self.assertIn(guardrail.requirement_id, compiled.support_map)
            evidence = compiled.support_map[guardrail.requirement_id]
            self.assertGreaterEqual(len(evidence), 1)
            self.assertTrue(evidence[0].source_url.startswith("https://www.portland.gov/"))
            self.assertTrue(evidence[0].anchor_id)

    def test_compiles_confirmation_gates_as_prohibitions(self):
        compiled = compile_requirement_fixture(self.load_requirement_fixture())
        by_id = {guardrail.requirement_id: guardrail for guardrail in compiled.guardrails}

        submission = by_id["req-stop-before-submission-obligation"]
        payment = by_id["req-fee-payment-action-gate"]

        self.assertIsNotNone(submission.deontic_rule)
        self.assertIsNotNone(payment.deontic_rule)
        self.assertEqual(submission.deontic_rule.modality, "obligated")
        self.assertEqual(payment.deontic_rule.modality, "prohibited_without_confirmation")
        self.assertEqual(payment.temporal_rule.relation, "before")
        self.assertEqual(payment.temporal_rule.trigger, "pay_fee")

    def test_rejects_missing_evidence(self):
        fixture = self.load_requirement_fixture()
        fixture["expected_requirements"][0]["evidence"] = []

        with self.assertRaises(GuardrailCompilerError):
            compile_requirement_fixture(fixture)


class GuardrailCompilerFixtureCoverageTests(unittest.TestCase):
    def load_fixture(self) -> dict[str, Any]:
        return json.loads(GUARDRAIL_FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fixture_compiles_document_fact_and_confirmation_guardrails(self):
        fixture = self.load_fixture()
        compiled = compile_requirement_fixture(fixture)
        by_id = {guardrail.requirement_id: guardrail for guardrail in compiled.guardrails}

        self.assertEqual(compiled.fixture_id, "single_pdf_guardrail_cases_v1")
        self.assertFalse(compiled.validate())
        self.assertIn("req-application-pdf-present", by_id)
        self.assertIn("req-drawing-plan-single-searchable-pdf", by_id)
        self.assertIn("req-property-address-known", by_id)
        self.assertIn("req-property-id-known", by_id)
        self.assertIn("req-submit-explicit-confirmation", by_id)
        self.assertEqual(by_id["req-submit-explicit-confirmation"].deontic_rule.modality, "prohibited_without_confirmation")

    def test_fixture_reports_document_completeness_pdf_rules_missing_facts_and_confirmation_gates(self):
        fixture = self.load_fixture()
        compile_requirement_fixture(fixture)

        statuses = _evaluate_guardrail_checks(fixture, fixture["user_case"])

        self.assertEqual(statuses["check-application-pdf-present"], "missing")
        self.assertEqual(statuses["check-drawing-plan-pdf-rule"], "pass")
        self.assertEqual(statuses["check-property-address-known"], "pass")
        self.assertEqual(statuses["check-property-id-known"], "missing")
        self.assertEqual(statuses["check-submit-confirmation"], "blocked")

        expected = {
            check["check_id"]: check["expected_status"]
            for check in fixture["expected_guardrail_checks"]
        }
        self.assertEqual(statuses, expected)

    def test_completed_case_satisfies_document_and_user_fact_guardrails_but_keeps_confirmation_explicit(self):
        fixture = self.load_fixture()
        completed_case = copy.deepcopy(fixture["user_case"])
        completed_case["known_facts"]["property_id"] = "R123456"
        completed_case["uploaded_documents"].append(
            {
                "document_id": "doc-application-form",
                "document_type": "application_form",
                "file_name": "building-permit-application.pdf",
                "mime_type": "application/pdf",
                "searchable_text": True,
            }
        )

        without_confirmation = _evaluate_guardrail_checks(fixture, completed_case)
        self.assertEqual(without_confirmation["check-application-pdf-present"], "pass")
        self.assertEqual(without_confirmation["check-property-id-known"], "pass")
        self.assertEqual(without_confirmation["check-submit-confirmation"], "blocked")

        completed_case["explicit_confirmations"]["submit_application"] = True
        with_confirmation = _evaluate_guardrail_checks(fixture, completed_case)
        self.assertEqual(with_confirmation["check-submit-confirmation"], "confirmed")

    def test_pdf_file_rule_rejects_non_pdf_or_non_searchable_plan_documents(self):
        fixture = self.load_fixture()
        bad_case = copy.deepcopy(fixture["user_case"])
        bad_case["uploaded_documents"] = [
            {
                "document_id": "doc-drawing-plan-image",
                "document_type": "drawing_plan",
                "file_name": "drawing-plan.png",
                "mime_type": "image/png",
                "searchable_text": False,
            }
        ]

        statuses = _evaluate_guardrail_checks(fixture, bad_case)
        self.assertEqual(statuses["check-drawing-plan-pdf-rule"], "fail")


def _evaluate_guardrail_checks(fixture: dict[str, Any], user_case: dict[str, Any]) -> dict[str, str]:
    known_facts = user_case.get("known_facts", {})
    uploaded_documents = user_case.get("uploaded_documents", [])
    explicit_confirmations = user_case.get("explicit_confirmations", {})
    statuses: dict[str, str] = {}

    for check in fixture.get("expected_guardrail_checks", []):
        kind = check["kind"]
        if kind == "document_completeness":
            statuses[check["check_id"]] = _document_completeness_status(check, uploaded_documents)
        elif kind == "pdf_file_rule":
            statuses[check["check_id"]] = _pdf_file_rule_status(check, uploaded_documents)
        elif kind == "missing_user_fact":
            fact_key = check["fact_key"]
            statuses[check["check_id"]] = "pass" if known_facts.get(fact_key) else "missing"
        elif kind == "explicit_confirmation_gate":
            action = check["action"]
            statuses[check["check_id"]] = "confirmed" if explicit_confirmations.get(action) is True else "blocked"
        else:
            raise AssertionError(f"unknown guardrail check kind: {kind}")

    return statuses


def _document_completeness_status(check: dict[str, Any], uploaded_documents: list[dict[str, Any]]) -> str:
    required_type = check["document_type"]
    return "pass" if any(document.get("document_type") == required_type for document in uploaded_documents) else "missing"


def _pdf_file_rule_status(check: dict[str, Any], uploaded_documents: list[dict[str, Any]]) -> str:
    document_type = check["document_type"]
    matching_documents = [
        document
        for document in uploaded_documents
        if document.get("document_type") == document_type
    ]
    if not matching_documents:
        return "missing"
    if check.get("require_single_file") and len(matching_documents) != 1:
        return "fail"

    for document in matching_documents:
        file_name = str(document.get("file_name", "")).lower()
        mime_type = document.get("mime_type")
        if mime_type != "application/pdf" or not file_name.endswith(".pdf"):
            return "fail"
        if check.get("require_searchable_text") and document.get("searchable_text") is not True:
            return "fail"
    return "pass"


if __name__ == "__main__":
    unittest.main()
