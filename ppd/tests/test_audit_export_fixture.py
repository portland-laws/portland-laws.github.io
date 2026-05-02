"""Validate fixture-only PP&D audit exports for downstream human review."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "audit_export" / "human_review_audit_export.json"
REDACTED_TOKENS = {
    "[REDACTED_EMPTY]",
    "[REDACTED_DRAFT_VALUE]",
    "[REDACTED_USER_FACT]",
}
PRIVATE_ARTIFACT_MARKERS = (
    "auth_state",
    "storage_state",
    "cookie",
    "credential",
    "password",
    "playwright-report",
    "trace.zip",
    "traces.zip",
    "screenshot.png",
    "screenshot.jpg",
    "localstorage",
    "ppd/data/private",
    "ppd/data/raw",
)
REFUSED_OFFICIAL_ACTIONS = {
    "submit_application",
    "pay_fees",
    "certify_statement",
    "cancel_request",
}


class AuditExportFixtureTest(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
            self.fixture: dict[str, Any] = json.load(fixture_file)

    def test_fixture_is_exported_for_human_review_only(self) -> None:
        self.assertEqual(1, self.fixture.get("schema_version"))
        self.assertTrue(self.fixture.get("fixture_only"))
        self.assertEqual("downstream_human_review", self.fixture.get("review_purpose"))
        review_packet = self.fixture.get("human_review_packet", {})
        self.assertEqual("needs_human_review", review_packet.get("review_status"))
        self.assertFalse(review_packet.get("contains_browser_artifacts"))
        self.assertFalse(review_packet.get("contains_official_action_execution"))
        self.assertFalse(review_packet.get("contains_unredacted_user_values"))

    def test_source_evidence_is_public_and_referenced(self) -> None:
        evidence = self.fixture.get("source_evidence", [])
        self.assertGreaterEqual(len(evidence), 2)
        evidence_ids = {item.get("evidence_id") for item in evidence}
        for item in evidence:
            self.assertTrue(item.get("public_source"), item)
            self.assertTrue(str(item.get("source_url", "")).startswith("https://www.portland.gov/ppd"), item)
            self.assertTrue(str(item.get("captured_at", "")).endswith("Z"), item)
            self.assertGreater(len(item.get("supports", [])), 0, item)
        for section_name in (
            "user_question_decisions",
            "redacted_draft_previews",
            "guardrail_outcomes",
            "refused_official_actions",
        ):
            for record in self.fixture.get(section_name, []):
                referenced_ids = set(record.get("source_evidence_ids", []))
                self.assertGreater(len(referenced_ids), 0, record)
                self.assertTrue(referenced_ids.issubset(evidence_ids), record)

    def test_user_question_decisions_are_source_linked(self) -> None:
        decisions = self.fixture.get("user_question_decisions", [])
        self.assertGreaterEqual(len(decisions), 2)
        allowed_decisions = {"ask_user", "defer_to_human_review"}
        for decision in decisions:
            self.assertIn(decision.get("decision"), allowed_decisions)
            self.assertTrue(decision.get("linked_requirement_id"), decision)
            self.assertIn(decision.get("asked_value_preview"), REDACTED_TOKENS)

    def test_draft_previews_are_redacted_and_not_executed(self) -> None:
        previews = self.fixture.get("redacted_draft_previews", [])
        self.assertGreaterEqual(len(previews), 2)
        for preview in previews:
            self.assertEqual("reversible_draft_edit", preview.get("action_classification"))
            self.assertIn(preview.get("before_value"), REDACTED_TOKENS)
            self.assertIn(preview.get("after_value"), REDACTED_TOKENS)
            self.assertFalse(preview.get("requires_exact_user_confirmation"))
            self.assertFalse(preview.get("executed"))
            selector_basis = preview.get("selector_basis", {})
            self.assertTrue(selector_basis.get("role"), preview)
            self.assertTrue(selector_basis.get("accessible_name"), preview)
            self.assertTrue(selector_basis.get("nearby_heading"), preview)

    def test_guardrails_record_blocked_and_preview_only_outcomes(self) -> None:
        outcomes = self.fixture.get("guardrail_outcomes", [])
        self.assertGreaterEqual(len(outcomes), 3)
        outcome_by_id = {outcome.get("guardrail_id"): outcome for outcome in outcomes}
        self.assertEqual("blocked", outcome_by_id["gate-stop-before-submit"].get("outcome"))
        self.assertEqual("blocked", outcome_by_id["gate-stop-before-payment"].get("outcome"))
        self.assertEqual(
            "allowed_as_preview_only",
            outcome_by_id["gate-redacted-preview-only"].get("outcome"),
        )
        self.assertTrue(outcome_by_id["gate-stop-before-submit"].get("human_review_required"))
        self.assertTrue(outcome_by_id["gate-stop-before-payment"].get("human_review_required"))

    def test_official_actions_are_refused_and_not_executed(self) -> None:
        refused = self.fixture.get("refused_official_actions", [])
        refused_actions = {action.get("official_action") for action in refused}
        self.assertEqual(REFUSED_OFFICIAL_ACTIONS, refused_actions)
        for action in refused:
            self.assertIn(action.get("classification"), {"potentially_consequential", "financial"})
            self.assertTrue(action.get("refusal_reason"), action)
            self.assertFalse(action.get("executed"), action)

    def test_fixture_contains_no_private_artifact_markers(self) -> None:
        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in PRIVATE_ARTIFACT_MARKERS:
            self.assertNotIn(marker, serialized)


if __name__ == "__main__":
    unittest.main()
