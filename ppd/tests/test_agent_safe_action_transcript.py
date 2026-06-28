"""Fixture-backed tests for PP&D agent safe-action transcripts."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from ppd.agent_safe_action_transcript import (
    build_safe_action_transcript,
    validate_safe_action_transcript,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "agent_safe_action_transcript" / "synthetic_safe_action_case.json"


class AgentSafeActionTranscriptTests(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.case = json.load(fixture_file)

    def test_builds_required_cited_safe_action_sequence(self) -> None:
        transcript = build_safe_action_transcript(self.case)

        self.assertEqual(
            [message["message_type"] for message in transcript["messages"]],
            [
                "ask-user",
                "local-preview",
                "reversible-draft",
                "manual-handoff",
                "refused-action",
            ],
        )
        self.assertEqual((), validate_safe_action_transcript(transcript))

    def test_transcript_preserves_preflight_outcomes_and_citations(self) -> None:
        transcript = build_safe_action_transcript(self.case)
        outcomes = [message["preflight_outcome"] for message in transcript["messages"]]
        citation_sets = [message["citations"] for message in transcript["messages"]]

        self.assertEqual(
            outcomes,
            [
                "blocked",
                "local-preview",
                "reversible-draft",
                "manual-handoff",
                "refused",
            ],
        )
        self.assertTrue(all(citations for citations in citation_sets))
        self.assertIn("ppd-fee-payment-guide", citation_sets[-1])

    def test_ask_user_messages_only_scope_allowed_fact_gaps(self) -> None:
        transcript = build_safe_action_transcript(self.case)
        ask_user = transcript["messages"][0]

        self.assertEqual(["project_valuation"], [fact["fact_id"] for fact in ask_user["asked_facts"]])
        self.assertEqual(["missing"], [fact["status"] for fact in ask_user["asked_facts"]])

        broken = copy.deepcopy(transcript)
        broken["messages"][0]["asked_facts"].append(
            {
                "fact_id": "contractor_license_number",
                "status": "known",
                "prompt": "Please confirm the known contractor license number.",
                "reason": "Known facts are not missing-information prompts.",
                "citations": ["ppd-submit-permit-application-guide"],
            }
        )
        self.assertIn("fact_not_missing_stale_ambiguous_or_conflicting", validate_safe_action_transcript(broken))

    def test_rejects_credentials_payment_and_auth_prompts(self) -> None:
        transcript = build_safe_action_transcript(self.case)
        broken = copy.deepcopy(transcript)
        broken["messages"][0]["asked_facts"][0] = {
            "fact_id": "devhub_password",
            "status": "missing",
            "prompt": "What is your DevHub password?",
            "reason": "Credentials must never be requested.",
            "citations": ["ppd-devhub-account-sign-in-guide"],
        }

        self.assertIn("forbidden_sensitive_prompt", validate_safe_action_transcript(broken))

    def test_transcript_redacts_private_paths_from_message_text(self) -> None:
        case = copy.deepcopy(self.case)
        case["preflight_decision_matrix"][0]["message_template"] = (
            "I found draft notes at /home/barberb/private/devhub/session.json, "
            "but only need the project valuation."
        )
        transcript = build_safe_action_transcript(case)

        self.assertIn("[REDACTED]", transcript["messages"][0]["text"])
        self.assertNotIn("/home/barberb", transcript["messages"][0]["text"])
        self.assertEqual((), validate_safe_action_transcript(transcript))

    def test_validation_requires_citation_backed_reasons(self) -> None:
        transcript = build_safe_action_transcript(self.case)
        broken = copy.deepcopy(transcript)
        del broken["messages"][0]["citation_backed_reasons"]

        self.assertIn("missing_citation_backed_reasons", validate_safe_action_transcript(broken))

    def test_consequential_blocks_require_exact_confirmation_gate(self) -> None:
        transcript = build_safe_action_transcript(self.case)
        handoff = transcript["messages"][3]

        self.assertTrue(handoff["exact_confirmation_gate"]["required"])
        self.assertTrue(handoff["exact_confirmation_gate"]["exact_required"])
        self.assertFalse(handoff["exact_confirmation_gate"]["confirmation_satisfied"])

        broken = copy.deepcopy(transcript)
        del broken["messages"][3]["exact_confirmation_gate"]
        self.assertIn("missing_exact_confirmation_gate", validate_safe_action_transcript(broken))

    def test_manual_and_refused_messages_name_blocked_official_actions(self) -> None:
        transcript = build_safe_action_transcript(self.case)
        handoff = transcript["messages"][3]
        refused = transcript["messages"][4]

        self.assertIn("submit permit request", handoff["blocked_official_actions"])
        self.assertIn("submit payment", refused["blocked_official_actions"])

    def test_validation_requires_reviewer_owner(self) -> None:
        transcript = build_safe_action_transcript(self.case)
        broken = copy.deepcopy(transcript)
        del broken["reviewer_owner"]

        self.assertIn("missing_reviewer_owner", validate_safe_action_transcript(broken))

    def test_validation_rejects_uncited_answers_and_missing_fact_prompts(self) -> None:
        transcript = build_safe_action_transcript(self.case)
        uncited = copy.deepcopy(transcript)
        uncited["messages"][0]["citations"] = []
        missing_prompt = copy.deepcopy(transcript)
        del missing_prompt["messages"][0]["asked_facts"]

        self.assertIn("missing_citations", validate_safe_action_transcript(uncited))
        self.assertIn("missing_asked_facts", validate_safe_action_transcript(missing_prompt))

    def test_validation_requires_blocked_action_explanations(self) -> None:
        transcript = build_safe_action_transcript(self.case)
        broken = copy.deepcopy(transcript)
        del broken["messages"][3]["blocked_action_explanations"]

        self.assertIn("missing_blocked_action_explanations", validate_safe_action_transcript(broken))

    def test_validation_rejects_private_case_facts_and_raw_authenticated_values(self) -> None:
        transcript = build_safe_action_transcript(self.case)
        private_facts = copy.deepcopy(transcript)
        private_facts["private_case_facts"] = {"site_address": "123 Private St"}
        raw_values = copy.deepcopy(transcript)
        raw_values["raw_authenticated_values"] = {"permit_number": "private-auth-value"}

        self.assertIn("private_case_facts_present", validate_safe_action_transcript(private_facts))
        self.assertIn("raw_authenticated_values_present", validate_safe_action_transcript(raw_values))

    def test_validation_rejects_local_private_paths(self) -> None:
        transcript = build_safe_action_transcript(self.case)
        broken = copy.deepcopy(transcript)
        broken["messages"][1]["blocked_action_explanations"][0]["explanation"] = "See /home/barberb/private/devhub/state.json."

        self.assertIn("local_private_path_present", validate_safe_action_transcript(broken))

    def test_validation_rejects_live_execution_claims(self) -> None:
        transcript = build_safe_action_transcript(self.case)
        broken = copy.deepcopy(transcript)
        broken["messages"][1]["text"] = "I launched live DevHub and ran the crawler for this answer."

        self.assertIn("live_execution_claim", validate_safe_action_transcript(broken))

    def test_validation_rejects_legal_or_permitting_outcome_guarantees(self) -> None:
        transcript = build_safe_action_transcript(self.case)
        broken = copy.deepcopy(transcript)
        broken["messages"][2]["text"] = "This permit will be approved after the draft is complete."

        self.assertIn("legal_or_permitting_outcome_guarantee", validate_safe_action_transcript(broken))

    def test_validation_rejects_enabled_consequential_controls_and_mutation_flags(self) -> None:
        transcript = build_safe_action_transcript(self.case)
        controls = copy.deepcopy(transcript)
        controls["safe_read_only_attestations"]["consequential_controls_enabled"] = True
        prompt_mutation = copy.deepcopy(transcript)
        prompt_mutation["safe_read_only_attestations"]["prompt_mutation_enabled"] = True
        guardrail_mutation = copy.deepcopy(transcript)
        guardrail_mutation["safe_read_only_attestations"]["guardrail_mutation_enabled"] = True
        surface_mutation = copy.deepcopy(transcript)
        surface_mutation["safe_read_only_attestations"]["surface_registry_mutation_enabled"] = True
        state_mutation = copy.deepcopy(transcript)
        state_mutation["safe_read_only_attestations"]["agent_state_mutation_enabled"] = True

        self.assertIn("enabled_consequential_controls", validate_safe_action_transcript(controls))
        self.assertIn("active_prompt_mutation", validate_safe_action_transcript(prompt_mutation))
        self.assertIn("active_guardrail_mutation", validate_safe_action_transcript(guardrail_mutation))
        self.assertIn("active_surface_registry_mutation", validate_safe_action_transcript(surface_mutation))
        self.assertIn("active_agent_state_mutation", validate_safe_action_transcript(state_mutation))


if __name__ == "__main__":
    unittest.main()
