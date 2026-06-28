from __future__ import annotations

import copy
import unittest
from pathlib import Path

from ppd.agent_readiness.post_recompile_release_decision_packet_v7 import build_post_recompile_release_decision_packet_v7_from_fixture
from ppd.validation.post_recompile_release_decision_packet_v7 import (
    ReleaseDecisionPacketV7Issue,
    reject_packet,
    validate_packet,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "post_recompile_release_decision_packet_v7"
REPLAY_FIXTURE = FIXTURE_DIR / "post_recompile_agent_readiness_replay_v7_fixture.json"


class PostRecompileReleaseDecisionPacketV7ValidationTest(unittest.TestCase):
    def _packet(self) -> dict[str, object]:
        return build_post_recompile_release_decision_packet_v7_from_fixture(REPLAY_FIXTURE)

    def test_valid_packet_passes(self) -> None:
        packet = self._packet()

        self.assertEqual([], validate_packet(packet))
        reject_packet(packet)

    def test_rejects_each_missing_required_section(self) -> None:
        expected_codes = {
            "source_fixture_refs": "missing_source_fixture_refs",
            "go_no_go_rows": "missing_go_no_go_rows",
            "unresolved_hold_inventory": "missing_unresolved_hold_inventory",
            "citation_continuity_summaries": "missing_citation_continuity_summaries",
            "agent_compatibility_notes": "missing_agent_compatibility_notes",
            "inactive_guardrail_promotion_eligibility_placeholders": "missing_inactive_guardrail_promotion_eligibility_placeholders",
            "rollback_owner_placeholders": "missing_rollback_owner_placeholders",
            "monitoring_handoff_reminders": "missing_monitoring_handoff_reminders",
            "reviewer_signoff_placeholders": "missing_reviewer_signoff_placeholders",
            "offline_validation_commands": "missing_offline_validation_commands",
            "validation_commands": "missing_validation_commands",
        }
        for section, code in expected_codes.items():
            with self.subTest(section=section):
                packet = self._packet()
                packet[section] = []

                issues = validate_packet(packet)

                self.assertIssue(issues, code, f"$.{section}")

    def test_rejects_missing_readiness_replay_references(self) -> None:
        packet = self._packet()
        packet["source_fixture_refs"] = [{"fixture_role": "other", "path": "fixture.json", "replay": "other"}]
        packet["consumes_only"] = {"post_recompile_agent_readiness_replay_v7_fixtures": False, "replay": "other"}

        issues = validate_packet(packet)

        self.assertIssue(issues, "missing_readiness_replay_reference", "$.source_fixture_refs")
        self.assertIssue(issues, "invalid_replay_consumption_attestation", "$.consumes_only.post_recompile_agent_readiness_replay_v7_fixtures")
        self.assertIssue(issues, "invalid_replay_consumption_attestation", "$.consumes_only.replay")

    def test_rejects_invalid_go_no_go_rows(self) -> None:
        packet = self._packet()
        rows = copy.deepcopy(packet["go_no_go_rows"])
        self.assertIsInstance(rows, list)
        rows[0]["activation_allowed"] = True
        rows[0]["manual_reviewer_decision_required"] = False
        rows[0]["recommendation"] = "GO"
        rows[0]["basis"] = ""
        packet["go_no_go_rows"] = rows

        issues = validate_packet(packet)

        self.assertIssue(issues, "activation_not_allowed", "$.go_no_go_rows[0].activation_allowed")
        self.assertIssue(issues, "missing_manual_reviewer_decision", "$.go_no_go_rows[0].manual_reviewer_decision_required")
        self.assertIssue(issues, "invalid_go_no_go_recommendation", "$.go_no_go_rows[0].recommendation")
        self.assertIssue(issues, "missing_go_no_go_row_field", "$.go_no_go_rows[0].basis")

    def test_rejects_invalid_inventory_summary_note_and_placeholder_statuses(self) -> None:
        packet = self._packet()
        packet["unresolved_hold_inventory"][0]["promotion_blocked"] = False
        packet["citation_continuity_summaries"][0]["requires_manual_review"] = False
        packet["agent_compatibility_notes"][0]["requires_manual_review"] = False
        packet["inactive_guardrail_promotion_eligibility_placeholders"][0]["activation_allowed"] = True
        packet["rollback_owner_placeholders"][0]["active_state_changed"] = True
        packet["monitoring_handoff_reminders"][0]["handoff_required"] = False
        packet["reviewer_signoff_placeholders"][0]["signoff_required"] = False

        issues = validate_packet(packet)

        self.assertIssue(issues, "invalid_placeholder_status", "$.unresolved_hold_inventory[0].promotion_blocked")
        self.assertIssue(issues, "invalid_placeholder_status", "$.citation_continuity_summaries[0].requires_manual_review")
        self.assertIssue(issues, "invalid_placeholder_status", "$.agent_compatibility_notes[0].requires_manual_review")
        self.assertIssue(issues, "invalid_placeholder_status", "$.inactive_guardrail_promotion_eligibility_placeholders[0].activation_allowed")
        self.assertIssue(issues, "invalid_placeholder_status", "$.rollback_owner_placeholders[0].active_state_changed")
        self.assertIssue(issues, "invalid_placeholder_status", "$.monitoring_handoff_reminders[0].handoff_required")
        self.assertIssue(issues, "invalid_placeholder_status", "$.reviewer_signoff_placeholders[0].signoff_required")

    def test_rejects_missing_or_mutated_validation_commands(self) -> None:
        packet = self._packet()
        packet["validation_commands"] = [["python3", "-m", "unittest"]]
        packet["offline_validation_commands"] = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

        issues = validate_packet(packet)

        self.assertIssue(issues, "invalid_validation_commands", "$.validation_commands")
        self.assertIssue(issues, "invalid_offline_validation_commands", "$.offline_validation_commands")

    def test_rejects_active_activation_live_crawl_official_guarantee_and_mutation_claims(self) -> None:
        examples = {
            "active_activation_claim": "The release is active after reviewer approval.",
            "live_crawl_execution_claim": "The packet ran live crawl against PP&D.",
            "private_session_auth_artifact": "A session token was retained.",
            "official_action_completion_claim": "The application was submitted to the city.",
            "legal_or_permitting_guarantee": "Permit approval guaranteed.",
            "active_mutation_claim": "The packet changed active state.",
        }
        for code, text in examples.items():
            with self.subTest(code=code):
                packet = self._packet()
                packet["reviewer_note"] = text

                issues = validate_packet(packet)

                self.assertTrue(any(issue.code == code for issue in issues), f"missing {code}; got {issues!r}")

    def test_rejects_private_session_auth_raw_downloaded_trace_and_payment_artifacts(self) -> None:
        forbidden_examples = {
            "auth_state": {"stored": True},
            "cookies": {"session": "abc"},
            "trace_path": "tmp/trace.zip",
            "har_path": "tmp/devhub.har",
            "raw_crawl_output": "tmp/raw-crawl/devhub.html",
            "downloaded_document_path": "tmp/downloaded/application.pdf",
            "payment_details": {"card_token": "tok_test"},
        }
        for key, value in forbidden_examples.items():
            with self.subTest(key=key):
                packet = self._packet()
                packet[key] = value

                issues = validate_packet(packet)

                self.assertTrue(any(issue.code == "private_session_auth_artifact" for issue in issues), f"expected artifact rejection for {key}; got {issues!r}")

    def test_rejects_active_mutation_flags(self) -> None:
        packet = self._packet()
        packet["activation_executed"] = True
        packet["runtime"] = {"active_mutation_flag": True, "apply_live": True}

        issues = validate_packet(packet)

        self.assertIssue(issues, "required_flag_not_false", "$.activation_executed")
        self.assertIssue(issues, "active_mutation_flag", "$.runtime.active_mutation_flag")
        self.assertIssue(issues, "active_mutation_flag", "$.runtime.apply_live")

    def test_reject_helper_raises_with_issue_details(self) -> None:
        packet = self._packet()
        packet["go_no_go_rows"] = []

        with self.assertRaisesRegex(ValueError, "go_no_go_rows"):
            reject_packet(packet)

    def assertIssue(self, issues: list[ReleaseDecisionPacketV7Issue], code: str, path: str) -> None:
        self.assertTrue(
            any(issue.code == code and issue.path == path for issue in issues),
            f"missing issue {code} at {path}; got {issues!r}",
        )


if __name__ == "__main__":
    unittest.main()
