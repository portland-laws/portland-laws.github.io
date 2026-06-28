from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ppd.agent_readiness.inactive_release_smoke_replay_packet_v1 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    InactiveReleaseSmokeReplayPacketV1Error,
    assert_valid_inactive_release_smoke_replay_packet_v1,
    build_packet_from_fixture,
    load_inactive_release_smoke_replay_packet_v1,
    validate_inactive_release_smoke_replay_packet_v1,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "inactive_release_smoke_replay_packet_v1"
SOURCE_FIXTURE = FIXTURE_DIR / "source_rows.json"
PACKET_FIXTURE = FIXTURE_DIR / "packet.json"


class InactiveReleaseSmokeReplayPacketV1Tests(unittest.TestCase):
    def test_builder_consumes_only_synthetic_decision_and_readiness_rows(self) -> None:
        packet = build_packet_from_fixture(SOURCE_FIXTURE)

        self.assertEqual(validate_inactive_release_smoke_replay_packet_v1(packet), [])
        self.assertEqual(packet["source_kind"], "synthetic_inactive_release_decision_rows_and_post_recompile_agent_readiness_replay_rows")
        self.assertEqual(packet["validation_commands"], EXACT_OFFLINE_VALIDATION_COMMANDS)
        self.assertEqual(packet["exact_offline_validation_commands"], EXACT_OFFLINE_VALIDATION_COMMANDS)
        self.assertEqual(
            set(scenario["scenario_kind"] for scenario in packet["smoke_scenarios"]),
            {"missing_information", "blocked_action", "reversible_draft", "exact_confirmation", "citation_placeholder"},
        )

    def test_committed_packet_lists_expected_smoke_replay_outputs(self) -> None:
        packet = load_inactive_release_smoke_replay_packet_v1(PACKET_FIXTURE)

        self.assertEqual(validate_inactive_release_smoke_replay_packet_v1(packet), [])
        self.assertEqual(packet["smoke_scenario_ids"], [scenario["smoke_scenario_id"] for scenario in packet["smoke_scenarios"]])
        for scenario in packet["smoke_scenarios"]:
            self.assertTrue(scenario["source_inactive_release_decision_row_id"])
            self.assertTrue(scenario["source_post_recompile_readiness_row_id"])
            self.assertTrue(scenario["expected_missing_information_prompts"])
            self.assertTrue(scenario["expected_blocked_action_outcomes"])
            self.assertTrue(scenario["expected_reversible_draft_outcomes"])
            self.assertTrue(scenario["expected_exact_confirmation_warnings"])
            self.assertTrue(scenario["citation_placeholder_checks"])
            self.assertTrue(scenario["rollback_notes"])
            self.assertTrue(scenario["reviewer_holds"])
            self.assertEqual(scenario["offline_validation_commands"], EXACT_OFFLINE_VALIDATION_COMMANDS)

    def test_boundaries_deny_release_promotion_live_devhub_private_artifacts_and_official_actions(self) -> None:
        packet = load_inactive_release_smoke_replay_packet_v1(PACKET_FIXTURE)

        self.assertTrue(packet["boundaries"]["fixture_first"])
        self.assertTrue(packet["boundaries"]["synthetic_rows_only"])
        self.assertTrue(packet["boundaries"]["inactive_release_only"])
        self.assertFalse(packet["boundaries"]["release_promotion_enabled"])
        self.assertFalse(packet["boundaries"]["live_crawling_enabled"])
        self.assertFalse(packet["boundaries"]["devhub_opened"])
        self.assertFalse(packet["boundaries"]["private_artifact_storage_enabled"])
        self.assertFalse(packet["boundaries"]["official_action_enabled"])

    def test_rejects_missing_required_scenario_coverage_and_lists(self) -> None:
        packet = load_inactive_release_smoke_replay_packet_v1(PACKET_FIXTURE)
        unsafe = copy.deepcopy(packet)
        unsafe["smoke_scenarios"] = unsafe["smoke_scenarios"][:1]
        unsafe["smoke_scenario_ids"] = [unsafe["smoke_scenarios"][0]["smoke_scenario_id"]]
        unsafe["smoke_scenarios"][0]["expected_missing_information_prompts"] = []

        errors = validate_inactive_release_smoke_replay_packet_v1(unsafe)
        joined = "; ".join(errors)

        self.assertIn("missing required smoke scenario kinds", joined)
        self.assertIn("expected_missing_information_prompts must be a non-empty list of text", joined)

    def test_rejects_missing_release_decision_readiness_replay_and_smoke_scenario_ids(self) -> None:
        packet = load_inactive_release_smoke_replay_packet_v1(PACKET_FIXTURE)
        unsafe = copy.deepcopy(packet)
        unsafe["smoke_scenario_ids"] = []
        unsafe["consumed_inactive_release_decision_row_ids"] = []
        unsafe["consumed_post_recompile_readiness_row_ids"] = []
        unsafe["smoke_scenarios"][0]["smoke_scenario_id"] = ""
        unsafe["smoke_scenarios"][0]["source_inactive_release_decision_row_id"] = ""
        unsafe["smoke_scenarios"][0]["source_post_recompile_readiness_row_id"] = ""

        errors = validate_inactive_release_smoke_replay_packet_v1(unsafe)
        joined = "; ".join(errors)

        self.assertIn("smoke_scenario_ids must be a non-empty list of text", joined)
        self.assertIn("smoke_scenario_id must be non-empty", joined)
        self.assertIn("source_inactive_release_decision_row_id must be non-empty", joined)
        self.assertIn("source_post_recompile_readiness_row_id must be non-empty", joined)
        self.assertIn("consumed_inactive_release_decision_row_ids must be non-empty", joined)
        self.assertIn("consumed_post_recompile_readiness_row_ids must be non-empty", joined)

    def test_rejects_missing_expected_outcomes_rollbacks_holds_citations_and_commands(self) -> None:
        packet = load_inactive_release_smoke_replay_packet_v1(PACKET_FIXTURE)
        unsafe = copy.deepcopy(packet)
        scenario = unsafe["smoke_scenarios"][0]
        scenario["expected_missing_information_prompts"] = []
        scenario["expected_blocked_action_outcomes"] = []
        scenario["expected_reversible_draft_outcomes"] = []
        scenario["expected_exact_confirmation_warnings"] = []
        scenario["citation_placeholder_checks"] = []
        scenario["citation_placeholder_ids"] = []
        scenario["rollback_notes"] = []
        scenario["reviewer_holds"] = []
        scenario["offline_validation_commands"] = []
        unsafe["validation_commands"] = []

        errors = validate_inactive_release_smoke_replay_packet_v1(unsafe)
        joined = "; ".join(errors)

        self.assertIn("expected_missing_information_prompts must be a non-empty list of text", joined)
        self.assertIn("expected_blocked_action_outcomes must be a non-empty list of text", joined)
        self.assertIn("expected_reversible_draft_outcomes must be a non-empty list of text", joined)
        self.assertIn("expected_exact_confirmation_warnings must be a non-empty list of text", joined)
        self.assertIn("citation_placeholder_checks must be a non-empty list of text", joined)
        self.assertIn("citation_placeholder_ids must be non-empty", joined)
        self.assertIn("rollback_notes must be a non-empty list of text", joined)
        self.assertIn("reviewer_holds must be a non-empty list of text", joined)
        self.assertIn("offline_validation_commands must contain only the daemon self-test command", joined)
        self.assertIn("validation_commands must contain only the daemon self-test command", joined)

    def test_rejects_wrong_validation_commands_and_consumed_row_mismatch(self) -> None:
        packet = load_inactive_release_smoke_replay_packet_v1(PACKET_FIXTURE)
        unsafe = copy.deepcopy(packet)
        unsafe["validation_commands"] = [["python3", "-m", "pytest"]]
        unsafe["smoke_scenarios"][0]["offline_validation_commands"] = [["python3", "-m", "pytest"]]
        unsafe["consumed_inactive_release_decision_row_ids"] = ["different-row"]

        errors = validate_inactive_release_smoke_replay_packet_v1(unsafe)
        joined = "; ".join(errors)

        self.assertIn("validation_commands must contain only the daemon self-test command", joined)
        self.assertIn("offline_validation_commands must contain only the daemon self-test command", joined)
        self.assertIn("consumed_inactive_release_decision_row_ids must match scenario source decision rows in order", joined)

    def test_rejects_live_private_official_release_legal_guarantee_and_active_mutation_claims(self) -> None:
        packet = load_inactive_release_smoke_replay_packet_v1(PACKET_FIXTURE)
        unsafe = copy.deepcopy(packet)
        unsafe["boundaries"]["devhub_opened"] = True
        unsafe["active_prompt_mutation"] = True
        unsafe["active_surface_registry_mutation"] = True
        unsafe["notes"] = [
            "opened DevHub",
            "live crawl completed",
            "downloaded document retained",
            "official action completed",
            "release promoted",
            "approval is guaranteed",
            "permit will be issued",
        ]
        unsafe["browser_state_path"] = "state.json"
        unsafe["raw_pdf_artifact"] = "raw.pdf"

        errors = validate_inactive_release_smoke_replay_packet_v1(unsafe)
        joined = "; ".join(errors)

        self.assertIn("boundaries must exactly keep the replay fixture-only", joined)
        self.assertIn("forbidden live/private/official/release/legal guarantee claim", joined)
        self.assertIn("forbidden private/session/browser/raw artifact field", joined)
        self.assertIn("forbidden active/live/private/official true flag", joined)
        self.assertIn("forbidden active mutation flag", joined)
        with self.assertRaises(InactiveReleaseSmokeReplayPacketV1Error):
            assert_valid_inactive_release_smoke_replay_packet_v1(unsafe)

    def test_committed_packet_matches_builder_output(self) -> None:
        built = build_packet_from_fixture(SOURCE_FIXTURE)
        committed = json.loads(PACKET_FIXTURE.read_text(encoding="utf-8"))

        self.assertEqual(committed, built)


if __name__ == "__main__":
    unittest.main()
