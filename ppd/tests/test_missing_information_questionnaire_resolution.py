import json
import unittest
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "missing_information" / "questionnaire_resolution.json"
REDACTED_PLACEHOLDER = "[REDACTED]"
REFUSED_ACTIONS = {
    "upload_document",
    "submit_application",
    "certify_statement",
    "pay_fee",
    "cancel_request",
    "schedule_inspection",
    "complete_mfa",
    "solve_captcha",
    "create_account",
    "recover_password",
}


class MissingInformationQuestionnaireResolutionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_questionnaire_covers_only_unresolved_user_facts(self):
        unresolved_fact_ids = {
            fact["factId"]
            for fact in self.fixture["unresolvedUserFacts"]
            if fact["status"] == "unresolved"
        }
        question_fact_ids = {
            question["factId"]
            for question in self.fixture["questionnaire"]["questions"]
        }

        self.assertEqual(unresolved_fact_ids, question_fact_ids)
        self.assertEqual(
            "minimal_missing_only",
            self.fixture["questionnaire"]["mode"],
        )

    def test_questionnaire_preserves_source_evidence(self):
        evidence_by_id = {
            evidence["evidenceId"]: evidence
            for evidence in self.fixture["sourceEvidence"]
        }
        self.assertTrue(evidence_by_id)

        for question in self.fixture["questionnaire"]["questions"]:
            self.assertTrue(question["evidenceIds"])
            for evidence_id in question["evidenceIds"]:
                evidence = evidence_by_id[evidence_id]
                self.assertTrue(evidence["url"].startswith("https://www.portland.gov/ppd/"))
                self.assertEqual("public_source_only", evidence["redaction"])
                self.assertTrue(evidence["capturedAt"].endswith("Z"))

    def test_private_answers_are_redacted_placeholders_only(self):
        self.assertEqual(
            REDACTED_PLACEHOLDER,
            self.fixture["redactionPolicy"]["placeholder"],
        )
        for fact in self.fixture["unresolvedUserFacts"]:
            self.assertEqual(REDACTED_PLACEHOLDER, fact["privateValue"])
        for question in self.fixture["questionnaire"]["questions"]:
            self.assertEqual(REDACTED_PLACEHOLDER, question["answer"])
            self.assertEqual("unresolved_redacted_placeholder", question["answerState"])

    def test_action_classification_guardrails_stop_consequential_work(self):
        guardrails = self.fixture["actionClassificationGuardrails"]
        planned_action_ids = {action["actionId"] for action in guardrails["plannedActions"]}
        planned_descriptions = " ".join(
            action["description"].lower()
            for action in guardrails["plannedActions"]
        )

        self.assertEqual({"action-render-questionnaire"}, planned_action_ids)
        for refused_action in REFUSED_ACTIONS:
            self.assertIn(refused_action, guardrails["refusedWithoutExactConfirmation"])
            self.assertNotIn(refused_action.replace("_", " "), planned_descriptions)

        for gate in guardrails["stopGates"]:
            self.assertIn(gate["classification"], {"consequential", "financial"})
            self.assertTrue(gate["explicitConfirmationRequired"])
            self.assertFalse(gate["explicitUserConfirmation"])
            self.assertTrue(gate["evidenceIds"])


if __name__ == "__main__":
    unittest.main()
