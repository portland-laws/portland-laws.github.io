"""Fixture-backed DevHub guardrail checks for Urban Forestry draft review.

These tests intentionally use a mocked, redacted workflow state. They do not
open DevHub, authenticate, upload files, certify statements, submit requests,
pay fees, cancel applications, or schedule inspections.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any, Mapping


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub"
    / "urban_forestry_draft_review_guardrails.json"
)

CONSEQUENTIAL_OR_FINANCIAL_ACTIONS = {
    "official_upload",
    "certification",
    "submission",
    "fee_payment",
    "cancellation",
    "inspection_scheduling",
}

PRIVATE_FIXTURE_MARKERS = {
    "auth_state",
    "browser_context_storage",
    "credential",
    "password",
    "paymentcardnumber",
    "private_devhub_session",
    "raw_crawl_output",
    "screenshot",
    "trace.zip",
    "user@example.com",
}


def load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        data = json.load(fixture_file)
    if not isinstance(data, dict):
        raise AssertionError("Urban Forestry draft-review fixture must be a JSON object")
    return data


def action_map(data: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    state = data["draft_review_state"]
    actions = state["available_outputs"]
    return {str(action["action_id"]): action for action in actions}


def confirmation_allows_action(
    action: Mapping[str, Any],
    provided_confirmation: str | None,
    current_session_nonce: str,
) -> bool:
    if action.get("allowed_without_confirmation") is True:
        return True
    expected = action.get("exact_confirmation_required")
    if not isinstance(expected, str) or not expected:
        return False
    if current_session_nonce not in expected:
        return False
    return provided_confirmation == expected


class UrbanForestryDraftReviewGuardrailTests(unittest.TestCase):
    def test_draft_review_can_produce_preview_without_confirmation(self) -> None:
        data = load_fixture()
        actions = action_map(data)

        preview = actions["preview_draft_review"]

        self.assertEqual(preview["classification"], "read_only_preview")
        self.assertEqual(preview["result"], "preview_only")
        self.assertTrue(preview["allowed_without_confirmation"])
        self.assertTrue(
            confirmation_allows_action(
                preview,
                provided_confirmation=None,
                current_session_nonce=data["draft_review_state"]["session_nonce"],
            )
        )

    def test_official_actions_are_blocked_without_exact_confirmation(self) -> None:
        data = load_fixture()
        actions = action_map(data)
        session_nonce = data["draft_review_state"]["session_nonce"]

        self.assertEqual(CONSEQUENTIAL_OR_FINANCIAL_ACTIONS, set(actions) - {"preview_draft_review"})
        for action_id in sorted(CONSEQUENTIAL_OR_FINANCIAL_ACTIONS):
            with self.subTest(action_id=action_id):
                action = actions[action_id]
                self.assertFalse(action["allowed_without_confirmation"])
                self.assertIn(action["classification"], {"potentially_consequential", "financial"})
                self.assertEqual(action["result"], "refuse_until_exact_current_session_confirmation")
                self.assertFalse(
                    confirmation_allows_action(
                        action,
                        provided_confirmation=None,
                        current_session_nonce=session_nonce,
                    )
                )
                self.assertFalse(
                    confirmation_allows_action(
                        action,
                        provided_confirmation="I confirm this action",
                        current_session_nonce=session_nonce,
                    )
                )

    def test_confirmation_must_match_current_session_nonce_and_exact_action_text(self) -> None:
        data = load_fixture()
        actions = action_map(data)

        for example in data["confirmation_examples"]:
            with self.subTest(example=example):
                action = actions[example["action_id"]]
                self.assertEqual(
                    confirmation_allows_action(
                        action,
                        provided_confirmation=example["provided_confirmation"],
                        current_session_nonce=example["current_session_nonce"],
                    ),
                    example["should_allow"],
                )

    def test_fixture_contains_no_private_devhub_artifacts(self) -> None:
        data = load_fixture()
        serial = json.dumps(data, sort_keys=True).lower().replace("_", "")

        self.assertFalse(data["source_context"]["captured_from_live_site"])
        self.assertFalse(data["source_context"]["uses_private_account_data"])
        self.assertEqual(data["draft_review_state"]["redaction_profile"], "synthetic_values_only")
        for marker in sorted(PRIVATE_FIXTURE_MARKERS):
            with self.subTest(marker=marker):
                self.assertNotIn(marker.lower().replace("_", ""), serial)

    def test_required_urban_forestry_scope_is_explicit(self) -> None:
        data = load_fixture()

        self.assertEqual(data["workflow_id"], "urban_forestry_application_draft_review")
        self.assertEqual(data["permit_type"], "urban_forestry")
        self.assertEqual(data["fixture_kind"], "mocked_devhub_guardrail")
        self.assertTrue(data["source_context"]["evidence"])


if __name__ == "__main__":
    unittest.main()
