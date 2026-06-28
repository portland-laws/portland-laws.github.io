from __future__ import annotations

import unittest
from copy import deepcopy
from pathlib import Path

from ppd.agent_readiness.source_recrawl_preflight_queue_v8 import (
    build_source_recrawl_preflight_queue_v8_fixture,
    validate_source_recrawl_preflight_queue_v8,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "source_recrawl_preflight_queue_v8"


class SourceRecrawlPreflightQueueV8Test(unittest.TestCase):
    def test_fixture_is_valid_without_live_or_private_artifacts(self) -> None:
        packet = build_source_recrawl_preflight_queue_v8_fixture()

        result = validate_source_recrawl_preflight_queue_v8(packet)

        self.assertTrue(result.accepted, result.errors)
        self.assertEqual(FIXTURE_ROOT.name, "source_recrawl_preflight_queue_v8")

    def test_rejects_missing_required_preflight_sections(self) -> None:
        required_fields = [
            "authorization_reference",
            "source_registry_references",
            "ordered_public_source_candidates",
            "canonical_url_checks",
            "allowlist_decisions",
            "robots_policy_decision_placeholders",
            "skipped_url_reason_rows",
            "processor_handoff_eligibility_flags",
            "validation_commands",
        ]

        for field in required_fields:
            with self.subTest(field=field):
                packet = build_source_recrawl_preflight_queue_v8_fixture()
                packet[field] = []

                result = validate_source_recrawl_preflight_queue_v8(packet)

                self.assertFalse(result.accepted)
                self.assertTrue(any(field in error for error in result.errors), result.errors)

    def test_rejects_missing_skipped_url_reason_rows(self) -> None:
        packet = build_source_recrawl_preflight_queue_v8_fixture()
        packet["skipped_url_reason_rows"] = [
            {"reason_code": "outside_allowlist", "example_url": "https://example.invalid/outside"}
        ]

        result = validate_source_recrawl_preflight_queue_v8(packet)

        self.assertFalse(result.accepted)
        self.assertTrue(any("missing required reason codes" in error for error in result.errors), result.errors)

    def test_rejects_live_private_artifact_and_completion_claims(self) -> None:
        blocked_fields = [
            "live_crawl_execution_claims",
            "downloaded_or_raw_crawl_artifacts",
            "private_session_auth_artifacts",
            "official_action_completion_claims",
            "legal_or_permitting_guarantees",
        ]

        for field in blocked_fields:
            with self.subTest(field=field):
                packet = build_source_recrawl_preflight_queue_v8_fixture()
                packet[field] = ["not allowed in preflight"]

                result = validate_source_recrawl_preflight_queue_v8(packet)

                self.assertFalse(result.accepted)
                self.assertTrue(any(field in error for error in result.errors), result.errors)

    def test_rejects_active_mutation_flags(self) -> None:
        active_values = [
            ["write_enabled"],
            {"crawl_mutation": True},
            "active",
        ]

        for active_value in active_values:
            with self.subTest(active_value=active_value):
                packet = build_source_recrawl_preflight_queue_v8_fixture()
                packet["active_mutation_flags"] = active_value

                result = validate_source_recrawl_preflight_queue_v8(packet)

                self.assertFalse(result.accepted)
                self.assertTrue(any("active_mutation_flags" in error for error in result.errors), result.errors)

    def test_rejects_handoff_flags_that_skip_policy_gates(self) -> None:
        packet = build_source_recrawl_preflight_queue_v8_fixture()
        packet["processor_handoff_eligibility_flags"] = deepcopy(packet["processor_handoff_eligibility_flags"])
        packet["processor_handoff_eligibility_flags"]["allowlist_decisions_present"] = False
        packet["processor_handoff_eligibility_flags"]["eligible_for_processor_handoff"] = True

        result = validate_source_recrawl_preflight_queue_v8(packet)

        self.assertFalse(result.accepted)
        self.assertIn(
            "processor_handoff_eligibility_flags.allowlist_decisions_present must be true",
            result.errors,
        )
        self.assertIn(
            "processor_handoff_eligibility_flags.eligible_for_processor_handoff must remain false until external validation",
            result.errors,
        )

    def test_rejects_missing_daemon_self_test_validation_command(self) -> None:
        packet = build_source_recrawl_preflight_queue_v8_fixture()
        packet["validation_commands"] = [["python3", "-m", "unittest"]]

        result = validate_source_recrawl_preflight_queue_v8(packet)

        self.assertFalse(result.accepted)
        self.assertIn("validation_commands must include ppd daemon self-test", result.errors)

    def test_rejects_unordered_or_non_public_candidates(self) -> None:
        packet = build_source_recrawl_preflight_queue_v8_fixture()
        packet["ordered_public_source_candidates"] = [
            {
                "order": 2,
                "source_id": "bad-candidate",
                "url": "http://user:token@example.invalid/private",
                "source_type": "public_html",
            }
        ]

        result = validate_source_recrawl_preflight_queue_v8(packet)

        self.assertFalse(result.accepted)
        self.assertTrue(any("explicitly ordered" in error for error in result.errors), result.errors)
        self.assertTrue(any("public https url" in error for error in result.errors), result.errors)


if __name__ == "__main__":
    unittest.main()
