from __future__ import annotations

import copy
import unittest
from pathlib import Path

from ppd.logic.requirement_regeneration_acknowledgement_packet import (
    build_requirement_regeneration_acknowledgement_packet,
)
from ppd.logic.requirement_regeneration_queue import build_regeneration_queue_from_files, load_json


QUEUE_FIXTURES = Path(__file__).parent / "fixtures" / "requirement_regeneration_queue"
ACK_FIXTURES = Path(__file__).parent / "fixtures" / "requirement_regeneration_acknowledgement"


class RequirementRegenerationAcknowledgementPacketTest(unittest.TestCase):
    def _queue_plan(self) -> dict[str, object]:
        return build_regeneration_queue_from_files(
            QUEUE_FIXTURES / "public_recrawl_execution_rehearsal_plan.json",
            QUEUE_FIXTURES / "source_freshness_drift_digest.json",
            QUEUE_FIXTURES / "source_dependency_index.json",
        )

    def _reviewer_decisions(self) -> dict[str, object]:
        return load_json(ACK_FIXTURES / "reviewer_decisions.json")

    def test_records_reviewer_acknowledgement_decisions_for_queue_sources(self) -> None:
        packet = build_requirement_regeneration_acknowledgement_packet(
            self._queue_plan(),
            self._reviewer_decisions(),
        )

        self.assertEqual(packet["packet_type"], "ppd.requirement_regeneration_reviewer_acknowledgement.v1")
        self.assertEqual(packet["mode"], "fixture_first")
        self.assertFalse(packet["live_crawl_required"])
        self.assertTrue(packet["acknowledgement_complete"])
        self.assertFalse(packet["downstream_activation_blocked"])
        self.assertEqual(
            packet["next_allowed_step"],
            "validate_acknowledgement_packet_before_any_process_or_guardrail_activation",
        )

        acknowledgements = {item["source_id"]: item for item in packet["source_acknowledgements"]}
        self.assertEqual(sorted(acknowledgements), ["ppd-devhub-application-guide", "ppd-spp-file-naming-standards"])

        devhub = acknowledgements["ppd-devhub-application-guide"]
        self.assertEqual(devhub["reviewer_decision"], "accepted_for_regeneration")
        self.assertEqual(devhub["human_review_owners"], ("devhub-workflow-review", "requirements-counsel"))
        self.assertEqual(devhub["missing_human_review_owner_acknowledgements"], ())
        self.assertEqual(devhub["missing_required_synthetic_fixtures"], ())
        self.assertIn("changed_devhub_action_guidance", devhub["citation_refresh_scope"])
        self.assertTrue(devhub["inherited_queue_activation_block"])
        self.assertFalse(devhub["blocked_downstream_activation_until_acknowledgement_complete"])

        file_rules = acknowledgements["ppd-spp-file-naming-standards"]
        self.assertEqual(file_rules["affected_guardrail_bundle_ids"], ("guardrail-submit-plans-online",))
        self.assertEqual(
            file_rules["required_synthetic_fixtures"],
            (
                "ppd/tests/fixtures/requirement_regeneration_queue/ppd-spp-file-naming-standards.changed_file_rule.json",
                "ppd/tests/fixtures/requirement_regeneration_queue/ppd-spp-file-naming-standards.changed_required_document.json",
                "ppd/tests/fixtures/requirement_regeneration_queue/spp_file_naming_guardrail_fixture.json",
            ),
        )

    def test_blocks_downstream_activation_when_required_fixture_acknowledgement_is_missing(self) -> None:
        decisions = copy.deepcopy(self._reviewer_decisions())
        decisions["reviewer_decisions"][1]["acknowledged_required_synthetic_fixtures"] = [
            "ppd/tests/fixtures/requirement_regeneration_queue/ppd-spp-file-naming-standards.changed_file_rule.json"
        ]

        packet = build_requirement_regeneration_acknowledgement_packet(self._queue_plan(), decisions)
        acknowledgements = {item["source_id"]: item for item in packet["source_acknowledgements"]}

        self.assertFalse(packet["acknowledgement_complete"])
        self.assertTrue(packet["downstream_activation_blocked"])
        self.assertEqual(
            packet["activation_block_reason"],
            "reviewer_acknowledgement_required_before_guardrail_or_process_activation",
        )
        self.assertTrue(
            acknowledgements["ppd-spp-file-naming-standards"]["blocked_downstream_activation_until_acknowledgement_complete"]
        )
        self.assertIn(
            "ppd/tests/fixtures/requirement_regeneration_queue/spp_file_naming_guardrail_fixture.json",
            acknowledgements["ppd-spp-file-naming-standards"]["missing_required_synthetic_fixtures"],
        )


if __name__ == "__main__":
    unittest.main()
