import copy
import unittest

from ppd.agent_feedback_triage import (
    FeedbackTriageError,
    build_agent_consumer_feedback_triage,
    validate_agent_consumer_feedback_triage,
)


def _input_packets():
    return {
        "release_consumer_handoff": {
            "packet_id": "release-handoff-fixture",
            "reviewer_owner": "ppd-release-owner",
            "citations": [
                {
                    "citation_id": "release-citation-1",
                    "title": "Release handoff fixture",
                    "owner": "ppd-release-owner",
                }
            ],
        },
        "safe_action_regression": {
            "packet_id": "safe-action-fixture",
            "reviewer_owner": "ppd-safe-action-owner",
            "citations": [
                {
                    "citation_id": "safe-action-citation-1",
                    "title": "Safe action fixture",
                    "owner": "ppd-safe-action-owner",
                }
            ],
        },
        "post_promotion_smoke_test_plan": {
            "packet_id": "smoke-plan-fixture",
            "reviewer_owner": "ppd-smoke-owner",
            "citations": [
                {
                    "citation_id": "smoke-citation-1",
                    "title": "Smoke plan fixture",
                    "owner": "ppd-smoke-owner",
                }
            ],
        },
    }


class AgentFeedbackTriageValidationTest(unittest.TestCase):
    def test_builder_produces_valid_fixture_first_packet(self):
        packet = build_agent_consumer_feedback_triage(_input_packets())
        self.assertEqual([], validate_agent_consumer_feedback_triage(packet))
        self.assertTrue(packet["attestations"]["fixtures_only"])
        self.assertTrue(packet["attestations"]["no_live_llm_execution"])
        self.assertTrue(packet["attestations"]["no_live_devhub_execution"])
        self.assertTrue(packet["attestations"]["no_live_crawler_execution"])
        self.assertTrue(packet["attestations"]["no_live_processor_execution"])

    def test_rejects_private_case_fact_and_local_private_path_inputs(self):
        packets = _input_packets()
        packets["release_consumer_handoff"]["private_case_facts"] = {"permit_number": "private"}
        with self.assertRaises(FeedbackTriageError):
            build_agent_consumer_feedback_triage(packets)

        packets = _input_packets()
        packets["safe_action_regression"]["auth_state_path"] = "/home/user/devhub-state.json"
        with self.assertRaises(FeedbackTriageError):
            build_agent_consumer_feedback_triage(packets)

    def test_validation_rejects_uncited_feedback_missing_owner_and_missing_rerun_trigger(self):
        packet = build_agent_consumer_feedback_triage(_input_packets())
        packet = copy.deepcopy(packet)
        category = packet["feedback_categories"][0]
        category["citations"] = []
        category["reviewer_owner"] = ""
        category["regression_rerun_triggers"] = []
        findings = validate_agent_consumer_feedback_triage(packet)
        codes = {finding["code"] for finding in findings}
        self.assertIn("uncited_feedback_item", codes)
        self.assertIn("missing_reviewer_owner", codes)
        self.assertIn("missing_regression_rerun_trigger", codes)

    def test_validation_rejects_live_execution_claims_and_outcome_guarantees(self):
        packet = build_agent_consumer_feedback_triage(_input_packets())
        packet = copy.deepcopy(packet)
        packet["feedback_categories"][0]["feedback"] = "Crawler executed and permit will be approved."
        packet["attestations"]["processor_executed"] = True
        packet["attestations"]["live_devhub_executed"] = True
        findings = validate_agent_consumer_feedback_triage(packet)
        codes = {finding["code"] for finding in findings}
        self.assertIn("live_execution_claim", codes)
        self.assertIn("outcome_guarantee", codes)

    def test_validation_rejects_enabled_controls_and_active_mutation_flags(self):
        packet = build_agent_consumer_feedback_triage(_input_packets())
        packet = copy.deepcopy(packet)
        packet["controls"] = [
            {"label": "Submit application", "enabled": True},
            {"label": "Pay fees", "status": "active"},
        ]
        packet["prompt_mutation_active"] = True
        packet["release_state_mutations_performed"] = True
        findings = validate_agent_consumer_feedback_triage(packet)
        codes = {finding["code"] for finding in findings}
        self.assertIn("enabled_consequential_control", codes)
        self.assertIn("active_mutation_flag", codes)


if __name__ == "__main__":
    unittest.main()
