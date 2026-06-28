from __future__ import annotations

import sys
import unittest
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ppd.stale_readiness_packet_v1 import (  # noqa: E402
    PACKET_VERSION,
    build_stale_readiness_packet_v1,
    offline_validation_commands,
    validate_stale_readiness_packet_v1,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "stale_readiness_packet_v1" / "combined_public_devhub_stale_readiness_fixture.json"


class StaleReadinessPacketV1Test(unittest.TestCase):
    def test_builds_combined_packet_with_all_recommendation_types(self) -> None:
        packet = build_stale_readiness_packet_v1(FIXTURE_PATH)

        self.assertEqual(packet["packet_version"], PACKET_VERSION)
        recommendations = {row["target_id"]: row for row in packet["readiness_recommendations"]}
        self.assertEqual(recommendations["public-synthetic-index-pass"]["recommendation"], "proceed")
        self.assertEqual(recommendations["public-devhub-faq-stale"]["recommendation"], "hold")
        self.assertEqual(recommendations["public-payment-guide-failed"]["recommendation"], "reject")

        ordering = packet["dependency_order"]
        self.assertLess(ordering.index("public-synthetic-index-pass"), ordering.index("public-devhub-faq-stale"))
        self.assertLess(ordering.index("public-devhub-faq-stale"), ordering.index("public-payment-guide-failed"))

    def test_packet_is_offline_only_and_routes_reviewers(self) -> None:
        packet = build_stale_readiness_packet_v1(FIXTURE_PATH)

        false_flags = [
            "live_crawl_performed",
            "devhub_opened",
            "auth_state_stored",
            "private_files_stored",
            "form_filling_performed",
            "upload_performed",
            "submission_performed",
            "certification_performed",
            "payment_performed",
            "inspection_scheduling_performed",
            "release_promotion_performed",
            "active_prompt_mutated",
            "active_guardrail_mutated",
            "active_process_model_mutated",
            "active_requirement_mutated",
            "active_contract_mutated",
            "active_source_mutated",
            "active_archive_mutated",
            "active_document_mutated",
            "active_devhub_surface_mutated",
            "active_crawler_mutated",
            "active_release_mutated",
            "active_daemon_state_mutated",
        ]
        for flag in false_flags:
            self.assertIs(packet[flag], False)

        routing = packet["reviewer_routing"]
        self.assertTrue(any(row["reviewer"] == "public-source-monitor-reviewer" for row in routing))
        self.assertTrue(any(row["reviewer"] == "devhub-surface-reviewer" for row in routing))
        self.assertTrue(any(row["reviewer"] == "agent-safety-reviewer" for row in routing))
        self.assertEqual(packet["exact_offline_validation_commands"], offline_validation_commands())

    def test_validation_rejects_forbidden_private_or_raw_artifacts(self) -> None:
        unsafe_fixture = {
            "fixture_id": "unsafe",
            "synthetic_public_monitoring_outcomes": [
                {
                    "source_id": "unsafe-source",
                    "outcome": "current",
                    "raw_body": "not allowed",
                }
            ],
        }

        with self.assertRaises(ValueError):
            build_stale_readiness_packet_v1(unsafe_fixture)

    def test_validator_accepts_generated_packet(self) -> None:
        packet = build_stale_readiness_packet_v1(FIXTURE_PATH)
        result = validate_stale_readiness_packet_v1(packet)
        self.assertTrue(result.ok, result.errors)


if __name__ == "__main__":
    unittest.main()
