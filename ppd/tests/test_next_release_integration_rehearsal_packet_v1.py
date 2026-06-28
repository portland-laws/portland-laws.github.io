from __future__ import annotations

import copy
import unittest
from pathlib import Path

from ppd.next_release_integration_rehearsal_packet_v1 import (
    NextReleaseIntegrationRehearsalPacketV1Error,
    assert_next_release_integration_rehearsal_packet_v1,
    load_next_release_integration_rehearsal_packet_v1,
    validate_next_release_integration_rehearsal_packet_v1,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "next_release_integration_rehearsal_packet_v1" / "valid_packet.json"


class NextReleaseIntegrationRehearsalPacketV1Test(unittest.TestCase):
    def packet(self) -> dict:
        return load_next_release_integration_rehearsal_packet_v1(FIXTURE_PATH)

    def issue_text(self, packet: dict) -> str:
        return "\n".join(validate_next_release_integration_rehearsal_packet_v1(packet))

    def test_accepts_valid_fixture(self) -> None:
        packet = self.packet()

        self.assertEqual(validate_next_release_integration_rehearsal_packet_v1(packet), [])
        assert_next_release_integration_rehearsal_packet_v1(packet)

    def test_rejects_missing_source_and_delta_references(self) -> None:
        packet = self.packet()
        for key in (
            "source_freshness_references",
            "requirement_delta_references",
            "process_delta_references",
            "guardrail_delta_references",
            "gap_analysis_delta_references",
        ):
            candidate = copy.deepcopy(packet)
            candidate[key] = []

            self.assertIn("missing", self.issue_text(candidate), key)

    def test_rejects_missing_release_ready_held_and_rejected_scenarios(self) -> None:
        packet = self.packet()
        packet["release_scenarios"] = [
            row for row in packet["release_scenarios"] if row["scenario"] != "release-held"
        ]

        issues = self.issue_text(packet)

        self.assertIn("missing release scenario coverage", issues)
        self.assertIn("release-held", issues)

    def test_rejects_missing_rollback_reviewer_dependency_and_validation_sections(self) -> None:
        packet = self.packet()
        packet["rollback_notes"] = []
        packet["reviewer_dispositions"] = []
        packet["dependency_ordering"] = []
        packet["validation_commands"] = []

        issues = self.issue_text(packet)

        self.assertIn("missing rollback notes", issues)
        self.assertIn("missing reviewer dispositions", issues)
        self.assertIn("missing dependency ordering", issues)
        self.assertIn("missing validation commands", issues)

    def test_rejects_private_session_browser_raw_and_downloaded_artifacts(self) -> None:
        packet = self.packet()
        packet["session_artifact"] = "state/session/storage_state.json"
        packet["reviewer_dispositions"][0]["notes"] = "Downloaded document is available at captures/raw/body.html"

        issues = self.issue_text(packet)

        self.assertIn("private/session/browser/raw/downloaded artifact field", issues)
        self.assertIn("private/session/browser/raw/downloaded artifact reference", issues)

    def test_rejects_live_devhub_guarantees_official_completion_and_promotion_claims(self) -> None:
        packet = self.packet()
        packet["release_scenarios"][0]["recommendation"] = "Live crawl completed and opened DevHub."
        packet["release_scenarios"][1]["recommendation"] = "Permit will be approved after this packet."
        packet["release_scenarios"][2]["recommendation"] = "Application submitted and release promoted."

        issues = self.issue_text(packet)

        self.assertIn("live crawl or DevHub claim", issues)
        self.assertIn("legal or permitting guarantee", issues)
        self.assertIn("official-action completion claim", issues)
        self.assertIn("release promotion claim", issues)

    def test_rejects_active_mutation_flags(self) -> None:
        packet = self.packet()
        packet["active_guardrail_mutation"] = True
        packet["mutation_enabled"] = True

        issues = self.issue_text(packet)

        self.assertIn("active mutation flag must not be true: active_guardrail_mutation", issues)
        self.assertIn("active mutation flag must not be true: mutation_enabled", issues)

    def test_assert_raises_on_invalid_packet(self) -> None:
        packet = self.packet()
        packet["validation_commands"] = []

        with self.assertRaises(NextReleaseIntegrationRehearsalPacketV1Error):
            assert_next_release_integration_rehearsal_packet_v1(packet)


if __name__ == "__main__":
    unittest.main()
