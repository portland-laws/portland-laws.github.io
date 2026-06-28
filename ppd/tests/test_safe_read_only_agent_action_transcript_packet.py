from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from ppd.safe_read_only_agent_action_transcript_packet import (
    build_safe_read_only_agent_action_transcript_packet,
    validate_safe_read_only_agent_action_transcript_packet,
)


FIXTURE = Path(__file__).parent / "fixtures" / "safe_read_only_agent_action_transcript_packet" / "input_packets.json"


class SafeReadOnlyAgentActionTranscriptPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inputs = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_builds_fixture_first_transcript_packet(self) -> None:
        packet = build_safe_read_only_agent_action_transcript_packet(self.inputs)

        self.assertEqual("ppd.safe_read_only_agent_action_transcript_packet.v1", packet["packet_type"])
        self.assertTrue(packet["fixture_first"])
        self.assertTrue(packet["offline_only"])
        self.assertTrue(packet["read_only_only"])
        self.assertEqual((), validate_safe_read_only_agent_action_transcript_packet(packet).errors)

    def test_consumes_all_required_source_packets(self) -> None:
        packet = build_safe_read_only_agent_action_transcript_packet(self.inputs)

        self.assertEqual(
            {
                "release_acceptance_review_packet",
                "agent_release_consumer_handoff_packet",
                "devhub_read_only_pilot_reconciliation_packet",
            },
            set(packet["consumed_source_packets"]),
        )
        self.assertTrue(all(row["consumed"] for row in packet["consumed_source_packets"].values()))

    def test_emits_scenarios_answers_prompts_and_blocked_explanations(self) -> None:
        packet = build_safe_read_only_agent_action_transcript_packet(self.inputs)

        self.assertGreaterEqual(len(packet["user_question_scenarios"]), 3)
        self.assertTrue(packet["source_grounded_read_only_answers"])
        self.assertTrue(packet["missing_fact_prompts"])
        self.assertTrue(packet["blocked_consequential_action_explanations"])
        self.assertTrue(all(row["citations"] for row in packet["source_grounded_read_only_answers"]))

    def test_attestations_block_live_llm_devhub_prompt_mutation_and_consequential_controls(self) -> None:
        packet = build_safe_read_only_agent_action_transcript_packet(self.inputs)
        attestations = packet["no_live_llm_no_devhub_no_prompt_mutation_attestations"]

        self.assertTrue(attestations["no_live_llm"])
        self.assertTrue(attestations["no_devhub_launch"])
        self.assertTrue(attestations["no_prompt_mutation"])
        self.assertFalse(attestations["llm_execution_enabled"])
        self.assertFalse(attestations["devhub_execution_enabled"])
        self.assertFalse(attestations["prompt_mutation_enabled"])
        self.assertFalse(attestations["consequential_controls_enabled"])

    def test_validation_rejects_uncited_answers_missing_prompts_and_enabled_execution(self) -> None:
        packet = build_safe_read_only_agent_action_transcript_packet(self.inputs)

        uncited = copy.deepcopy(packet)
        uncited["source_grounded_read_only_answers"][0]["citations"] = []
        self.assertIn("missing_source_grounded_read_only_answers_citations", validate_safe_read_only_agent_action_transcript_packet(uncited).errors)

        missing_prompt = copy.deepcopy(packet)
        missing_prompt["missing_fact_prompts"] = []
        self.assertIn("missing_missing_fact_prompts", validate_safe_read_only_agent_action_transcript_packet(missing_prompt).errors)

        live_llm = copy.deepcopy(packet)
        live_llm["no_live_llm_no_devhub_no_prompt_mutation_attestations"]["llm_execution_enabled"] = True
        self.assertIn("llm_execution_enabled_must_be_false", validate_safe_read_only_agent_action_transcript_packet(live_llm).errors)

    def test_validation_rejects_private_artifacts_and_live_claims(self) -> None:
        packet = build_safe_read_only_agent_action_transcript_packet(self.inputs)
        broken = copy.deepcopy(packet)
        broken["source_grounded_read_only_answers"][0]["answer"] = "I opened DevHub and saved auth_state.json."

        errors = validate_safe_read_only_agent_action_transcript_packet(broken).errors
        self.assertIn("private_or_session_artifact", errors)
        self.assertIn("live_execution_claim", errors)


if __name__ == "__main__":
    unittest.main()
