from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from ppd.logic.requirement_regeneration_promotion_decision_packet import (
    RequirementRegenerationPromotionDecisionPacketError,
    build_requirement_regeneration_promotion_decision_packet,
    finding_codes,
    validate_requirement_regeneration_promotion_decision_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "requirement_regeneration_promotion_decision_packet"


class RequirementRegenerationPromotionDecisionPacketTest(unittest.TestCase):
    def load_fixture(self) -> dict:
        with (FIXTURE_DIR / "packet_input.json").open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertIsInstance(data, dict)
        return data

    def test_builds_metadata_only_promote_and_defer_decision_packet(self) -> None:
        fixture = self.load_fixture()
        original = copy.deepcopy(fixture)

        packet = build_requirement_regeneration_promotion_decision_packet(fixture)

        self.assertEqual(fixture, original)
        self.assertEqual(packet["packet_type"], "requirement_regeneration_promotion_decision_packet")
        self.assertEqual(packet["packet_mode"], "fixture_first_metadata_only")
        self.assertTrue(packet["blocked_downstream_activation"])
        self.assertFalse(packet["activation_allowed"])
        self.assertFalse(packet["active_requirement_mutated"])
        self.assertFalse(packet["active_process_model_mutated"])
        self.assertFalse(packet["active_guardrail_bundle_mutated"])
        self.assertTrue(packet["does_not_mutate_active_requirements"])
        self.assertTrue(packet["does_not_mutate_active_process_models"])
        self.assertTrue(packet["does_not_mutate_active_guardrail_bundles"])

        artifact_ids = packet["metadata_only_artifact_ids"]
        self.assertEqual(len(artifact_ids), 5)
        self.assertTrue(all(artifact["metadata_only"] is True for artifact in artifact_ids))
        self.assertTrue(all(artifact["payload_persisted"] is False for artifact in artifact_ids))
        self.assertTrue(all(artifact["activation_allowed"] is False for artifact in artifact_ids))

        prerequisite_components = {link["component"] for link in packet["prerequisite_links"]}
        self.assertEqual(
            prerequisite_components,
            {
                "reviewer_acknowledgement_packet",
                "regenerated_requirement_candidate",
                "process_model_impact_candidate",
                "guardrail_recompilation_rehearsal",
                "regenerated_agent_regression_matrix",
            },
        )
        self.assertTrue(all(row["cited"] is True for row in packet["change_citation_audit"]))

        decisions = {decision["decision_id"]: decision for decision in packet["reviewer_selected_decisions"]}
        promote = decisions["decision.promote.file-naming-citation-refresh"]
        defer = decisions["decision.defer.upload-activation"]
        self.assertEqual(promote["reviewer_selected_decision"], "promote")
        self.assertEqual(promote["final_decision"], "promote_candidate_metadata_only")
        self.assertTrue(promote["blocked_downstream_activation"])
        self.assertFalse(promote["activation_allowed"])
        self.assertEqual(defer["reviewer_selected_decision"], "defer")
        self.assertEqual(defer["final_decision"], "defer")
        self.assertIn("consequential_upload_activation_requires_attended_exact_confirmation", defer["blocked_reasons"])

        self.assertGreaterEqual(len(packet["citation_refresh_scope"]), 3)
        self.assertEqual(packet["rollback_notes"][0]["active_guardrail_bundle_id"], "guardrail.bundle.building-permit-plan-review.active")
        self.assertEqual(validate_requirement_regeneration_promotion_decision_packet(packet), [])

    def test_validation_rejects_active_content_and_unblocked_activation(self) -> None:
        packet = build_requirement_regeneration_promotion_decision_packet(self.load_fixture())
        packet["blocked_downstream_activation"] = False
        packet["active_guardrail_bundle"] = {"guardrail_bundle_id": "replacement"}

        codes = finding_codes(validate_requirement_regeneration_promotion_decision_packet(packet))

        self.assertIn("activation_not_blocked", codes)
        self.assertIn("active_content_present", codes)

    def test_regression_matrix_issue_defers_requested_promote(self) -> None:
        fixture = self.load_fixture()
        fixture["regenerated_agent_regression_matrix"]["cases"][0]["expected"] = {
            "outcome": "allowed autonomous upload",
            "source_evidence_ids": ["ev.file-standards.current.001"],
        }

        packet = build_requirement_regeneration_promotion_decision_packet(fixture)
        decisions = {decision["decision_id"]: decision for decision in packet["reviewer_selected_decisions"]}

        self.assertEqual(packet["input_validation_summary"]["regression_matrix_issue_count"], 1)
        self.assertEqual(decisions["decision.promote.file-naming-citation-refresh"]["final_decision"], "defer")
        self.assertIn("regression_matrix_validation_failed", decisions["decision.promote.file-naming-citation-refresh"]["blocked_reasons"])

    def test_validation_rejects_missing_prerequisite_links(self) -> None:
        packet = build_requirement_regeneration_promotion_decision_packet(self.load_fixture())
        packet["prerequisite_links"] = []

        codes = finding_codes(validate_requirement_regeneration_promotion_decision_packet(packet))

        self.assertIn("missing_prerequisite_links", codes)

    def test_validation_rejects_uncited_requirement_or_process_changes(self) -> None:
        packet = build_requirement_regeneration_promotion_decision_packet(self.load_fixture())
        packet["change_citation_audit"][0]["citation_ids"] = []
        packet["change_citation_audit"][0]["cited"] = False

        codes = finding_codes(validate_requirement_regeneration_promotion_decision_packet(packet))

        self.assertIn("uncited_requirement_or_process_change", codes)

    def test_builder_rejects_private_case_facts(self) -> None:
        fixture = self.load_fixture()
        fixture["regenerated_agent_regression_matrix"]["cases"][0]["private_case_fact_value"] = "homeowner phone number"

        with self.assertRaisesRegex(RequirementRegenerationPromotionDecisionPacketError, "private_case_or_session_fact"):
            build_requirement_regeneration_promotion_decision_packet(fixture)

    def test_builder_rejects_raw_document_or_crawl_references(self) -> None:
        fixture = self.load_fixture()
        fixture["regenerated_requirement_candidate"]["raw_document_ref"] = "ppd/tests/fixtures/raw-download.html"

        with self.assertRaisesRegex(RequirementRegenerationPromotionDecisionPacketError, "raw_document_or_crawl_reference"):
            build_requirement_regeneration_promotion_decision_packet(fixture)

    def test_builder_rejects_stale_source_accepted_without_reviewer_acknowledgement(self) -> None:
        fixture = self.load_fixture()
        fixture["reviewer_acknowledgement_packet"]["source_acknowledgements"][0]["freshness_status"] = "stale"

        with self.assertRaisesRegex(RequirementRegenerationPromotionDecisionPacketError, "stale_source_accepted_without_acknowledgement"):
            build_requirement_regeneration_promotion_decision_packet(fixture)

    def test_builder_accepts_stale_source_when_reviewer_acknowledges_it(self) -> None:
        fixture = self.load_fixture()
        acknowledgement = fixture["reviewer_acknowledgement_packet"]["source_acknowledgements"][0]
        acknowledgement["freshness_status"] = "stale"
        acknowledgement["stale_source_reviewer_acknowledgement"] = True

        packet = build_requirement_regeneration_promotion_decision_packet(fixture)

        self.assertEqual(validate_requirement_regeneration_promotion_decision_packet(packet), [])

    def test_builder_rejects_production_ready_labels(self) -> None:
        fixture = self.load_fixture()
        fixture["regenerated_requirement_candidate"]["candidate_status"] = "production_ready"

        with self.assertRaisesRegex(RequirementRegenerationPromotionDecisionPacketError, "production_ready_label"):
            build_requirement_regeneration_promotion_decision_packet(fixture)

    def test_builder_rejects_downstream_activation_flags(self) -> None:
        fixture = self.load_fixture()
        fixture["process_model_impact_candidate"]["promotion"]["promote_to_active"] = True

        with self.assertRaisesRegex(RequirementRegenerationPromotionDecisionPacketError, "downstream_activation_flag"):
            build_requirement_regeneration_promotion_decision_packet(fixture)

    def test_builder_rejects_active_artifact_mutation(self) -> None:
        fixture = self.load_fixture()
        fixture["process_model_impact_candidate"]["active_process_model_mutated"] = True

        with self.assertRaisesRegex(RequirementRegenerationPromotionDecisionPacketError, "active_artifact_mutation"):
            build_requirement_regeneration_promotion_decision_packet(fixture)


if __name__ == "__main__":
    unittest.main()
