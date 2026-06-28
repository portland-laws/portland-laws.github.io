from __future__ import annotations

import copy
import unittest
from pathlib import Path

from ppd.offline_release_candidate_bundle import (
    PACKET_TYPE,
    OfflineReleaseCandidateBundleError,
    build_offline_release_candidate_bundle,
    load_fixture,
    validate_offline_release_candidate_bundle,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "release_candidate_bundle" / "input_packets.json"


class OfflineReleaseCandidateBundleTest(unittest.TestCase):
    def _fixture(self) -> dict:
        return load_fixture(FIXTURE_PATH)

    def test_builds_metadata_only_release_candidate_bundle(self) -> None:
        fixture = self._fixture()

        bundle = build_offline_release_candidate_bundle(fixture)

        self.assertEqual(bundle["packet_type"], PACKET_TYPE)
        self.assertEqual(bundle["bundle_status"], "review_candidate_only")
        self.assertTrue(bundle["fixture_first"])
        self.assertTrue(bundle["metadata_only"])
        self.assertTrue(bundle["no_production_readiness_claim"])
        self.assertFalse(bundle["live_actions_performed"])
        self.assertFalse(bundle["private_artifacts_included"])
        self.assertEqual(
            {item["input_role"] for item in bundle["inputs_consumed"]},
            set(fixture["inputs"]),
        )
        self.assertEqual(
            {item["input_role"] for item in bundle["prerequisite_links"]},
            set(fixture["inputs"]),
        )
        self.assertTrue(bundle["reviewer_prompts"])
        self.assertEqual(validate_offline_release_candidate_bundle(bundle), [])

    def test_all_live_capabilities_are_disabled(self) -> None:
        bundle = build_offline_release_candidate_bundle(self._fixture())

        self.assertTrue(bundle["disabled_live_capabilities"])
        for capability in bundle["disabled_live_capabilities"]:
            self.assertFalse(capability["enabled"])
            self.assertFalse(capability["allowed_now"])
            self.assertTrue(capability["requires_future_attended_review"])

    def test_rollbacks_cover_every_consumed_packet(self) -> None:
        bundle = build_offline_release_candidate_bundle(self._fixture())

        consumed_packet_ids = {item["packet_id"] for item in bundle["inputs_consumed"]}
        rollback_packet_ids = {item["source_packet_id"] for item in bundle["rollback_references"]}

        self.assertTrue(consumed_packet_ids.issubset(rollback_packet_ids))
        self.assertTrue(all(item["live_cleanup_required"] is False for item in bundle["rollback_references"]))

    def test_missing_required_input_is_rejected(self) -> None:
        fixture = self._fixture()
        del fixture["inputs"]["agent_regression_matrix"]

        with self.assertRaisesRegex(OfflineReleaseCandidateBundleError, "missing required inputs"):
            build_offline_release_candidate_bundle(fixture)

    def test_rejects_enabled_live_capability(self) -> None:
        bundle = build_offline_release_candidate_bundle(self._fixture())
        bundle["disabled_live_capabilities"][0]["enabled"] = True

        errors = validate_offline_release_candidate_bundle(bundle)

        self.assertIn("disabled_live_capabilities[0].enabled must be false", errors)

    def test_rejects_missing_prerequisite_link_and_rollback_reference(self) -> None:
        bundle = build_offline_release_candidate_bundle(self._fixture())
        removed = bundle["inputs_consumed"][0]
        bundle["prerequisite_links"] = [
            item for item in bundle["prerequisite_links"] if item["input_role"] != removed["input_role"]
        ]
        bundle["rollback_references"] = [
            item for item in bundle["rollback_references"] if item["source_packet_id"] != removed["packet_id"]
        ]

        errors = validate_offline_release_candidate_bundle(bundle)

        self.assertIn(f"prerequisite_links missing {removed['input_role']}", errors)
        self.assertIn(f"rollback_references missing source packet {removed['packet_id']}", errors)

    def test_rejects_private_artifacts_live_execution_and_readiness_labels(self) -> None:
        fixture = self._fixture()
        fixture["inputs"]["public_recrawl_rehearsal_plan"]["raw_crawl_output"] = "raw-crawl/body.html"
        fixture["inputs"]["agent_regression_matrix"]["execution_boundaries"]["calls_llm"] = True

        with self.assertRaisesRegex(OfflineReleaseCandidateBundleError, "forbidden private artifact"):
            build_offline_release_candidate_bundle(fixture)

        bundle = build_offline_release_candidate_bundle(self._fixture())
        bundle["bundle_status"] = "production-ready"
        errors = validate_offline_release_candidate_bundle(bundle)

        self.assertIn("bundle_status must be review_candidate_only", errors)
        self.assertTrue(any("forbidden readiness label" in error for error in errors))

    def test_builder_does_not_mutate_input_fixture(self) -> None:
        fixture = self._fixture()
        original = copy.deepcopy(fixture)

        build_offline_release_candidate_bundle(fixture)

        self.assertEqual(fixture, original)


if __name__ == "__main__":
    unittest.main()
