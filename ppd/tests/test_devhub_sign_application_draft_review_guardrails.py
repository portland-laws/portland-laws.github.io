"""Guardrail tests for mocked DevHub sign application draft review.

These tests use a deterministic fixture only. They do not open DevHub, attach to
a browser, authenticate, upload files, certify statements, submit requests, pay
fees, cancel permits, or schedule inspections.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub"
    / "sign_application_draft_review_guardrails.json"
)

BLOCKED_ACTION_IDS = {
    "official_upload_sign_documents",
    "certify_sign_application",
    "submit_sign_application",
    "pay_sign_application_fees",
    "cancel_sign_application",
    "schedule_sign_inspection",
}

CONSEQUENTIAL_OR_FINANCIAL = {"consequential", "financial"}
PRIVATE_ARTIFACT_FRAGMENTS = (
    "credential",
    "password",
    "secret",
    "auth_state",
    "storage_state",
    "trace.zip",
    "screenshot",
    "raw_response_body",
    "downloaded_document",
    "mfa_code",
    "captcha_solution",
)


def load_fixture() -> dict:
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def exact_confirmation_allows(fixture: dict, action_id: str, session_id: str, text: str) -> bool:
    blocked_actions = {
        action["action_id"]: action for action in fixture["blocked_actions"]
    }
    action = blocked_actions[action_id]
    expected_phrase = action["required_confirmation_phrase"]
    active_session_id = fixture["session"]["session_id"]
    return (
        session_id == active_session_id
        and text == expected_phrase
        and f" {action_id} " in f" {text} "
        and text.endswith(active_session_id)
    )


class DevHubSignApplicationDraftReviewGuardrailTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = load_fixture()

    def test_review_can_produce_preview_without_official_action(self) -> None:
        draft_review = self.fixture["draft_review"]
        preview = draft_review["preview"]

        self.assertTrue(draft_review["read_only_preview_allowed"])
        self.assertFalse(draft_review["official_action_performed"])
        self.assertEqual(preview["preview_id"], "preview-sign-draft-review-redacted")
        self.assertIn("produce_preview", preview["review_only_actions"])
        self.assertGreaterEqual(len(preview["planned_changes"]), 1)

        for change in preview["planned_changes"]:
            self.assertEqual(change["classification"], "draft_edit")
            self.assertTrue(change["before_redacted"].startswith("[redacted-"))
            self.assertTrue(change["after_redacted"].startswith("[redacted-"))
            selector = change["selector_basis"]
            self.assertTrue(selector["role"])
            self.assertTrue(selector["accessible_name"])
            self.assertTrue(selector["label_text"])
            self.assertTrue(selector["nearby_heading"])

    def test_official_actions_are_blocked_without_exact_session_confirmation(self) -> None:
        session_id = self.fixture["session"]["session_id"]
        action_ids = {action["action_id"] for action in self.fixture["blocked_actions"]}
        self.assertEqual(action_ids, BLOCKED_ACTION_IDS)

        for action in self.fixture["blocked_actions"]:
            with self.subTest(action=action["action_id"]):
                self.assertIn(action["classification"], CONSEQUENTIAL_OR_FINANCIAL)
                self.assertFalse(action["allowed_without_exact_confirmation"])
                self.assertIn(action["action_id"], action["required_confirmation_phrase"])
                self.assertIn(session_id, action["required_confirmation_phrase"])
                self.assertFalse(
                    exact_confirmation_allows(
                        self.fixture,
                        action["action_id"],
                        session_id,
                        "",
                    )
                )
                self.assertFalse(
                    exact_confirmation_allows(
                        self.fixture,
                        action["action_id"],
                        "devhub-session-redacted-old",
                        action["required_confirmation_phrase"],
                    )
                )

    def test_only_exact_confirmation_for_active_session_allows_matching_action(self) -> None:
        for example in self.fixture["confirmation_examples"]:
            with self.subTest(example=example["example_id"]):
                allowed = exact_confirmation_allows(
                    self.fixture,
                    example["action_id"],
                    example["session_id"],
                    example["confirmation_text"],
                )
                self.assertEqual(allowed, example["expected_allowed"])

    def test_confirmation_policy_is_session_specific_and_preview_first(self) -> None:
        policy = self.fixture["confirmation_policy"]
        self.assertTrue(policy["requires_active_session_match"])
        self.assertTrue(policy["requires_exact_action_match"])
        self.assertTrue(policy["requires_exact_phrase_match"])
        self.assertTrue(policy["requires_preview_before_execution"])
        self.assertEqual(
            policy["confirmation_template"],
            "I confirm {action_id} for DevHub session {session_id}",
        )

    def test_audit_expectations_cover_preview_and_blocked_actions(self) -> None:
        audit = self.fixture["audit_expectations"]
        self.assertTrue(audit["record_preview_event"])
        self.assertTrue(audit["record_blocked_action_event"])
        self.assertTrue(audit["record_selector_basis"])
        self.assertTrue(audit["record_source_requirement"])
        self.assertTrue(audit["record_user_confirmation_state"])
        self.assertTrue(audit["record_before_after_redacted_state"])

        requirements = self.fixture["source_requirements"]
        self.assertEqual(len(requirements), 1)
        self.assertEqual(requirements[0]["requirement_type"], "action_gate")
        self.assertTrue(requirements[0]["source_url"].startswith("https://www.portland.gov/ppd"))

    def test_fixture_contains_no_private_devhub_artifacts(self) -> None:
        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for fragment in PRIVATE_ARTIFACT_FRAGMENTS:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, serialized)


if __name__ == "__main__":
    unittest.main()
