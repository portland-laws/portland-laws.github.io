import copy
import unittest
from pathlib import Path

from ppd.readiness.reconciliation import REQUIRED_DISABLED_CAPABILITIES, load_packet, validate_packet


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "readiness" / "reconciliation_packet.json"


class ReadinessReconciliationPacketTest(unittest.TestCase):
    def setUp(self) -> None:
        self.packet = load_packet(FIXTURE_PATH)

    def assert_has_error(self, packet: dict, expected: str) -> None:
        errors = validate_packet(packet)
        self.assertTrue(any(expected in error for error in errors), errors)

    def test_reconciliation_packet_is_fixture_first_and_release_blocking(self) -> None:
        errors = validate_packet(self.packet)

        self.assertEqual([], errors)
        self.assertEqual("fixture_first", self.packet["mode"])
        self.assertTrue(self.packet["release_blockers"])
        self.assertTrue(all(blocker["status"] == "blocking" for blocker in self.packet["release_blockers"]))

    def test_reconciliation_packet_keeps_live_capabilities_disabled(self) -> None:
        disabled = set(self.packet["disabled_capabilities"])

        self.assertTrue(REQUIRED_DISABLED_CAPABILITIES.issubset(disabled))
        self.assertIs(self.packet["forbidden_live_evidence_present"], False)

    def test_rejects_missing_prerequisite_packet_link(self) -> None:
        packet = copy.deepcopy(self.packet)
        del packet["linked_artifacts"]["stale_guardrail_audit"]

        self.assert_has_error(packet, "missing linked artifacts: stale_guardrail_audit")

    def test_rejects_prerequisite_link_without_packet_version(self) -> None:
        packet = copy.deepcopy(self.packet)
        del packet["linked_artifacts"]["agent_response_regression_matrix"]["packet_version"]

        self.assert_has_error(packet, "linked_artifacts.agent_response_regression_matrix.packet_version is required")

    def test_rejects_uncited_release_blocker_claim(self) -> None:
        packet = copy.deepcopy(self.packet)
        del packet["release_blockers"][0]["source_evidence_ids"]

        self.assert_has_error(packet, "release_blockers[0].source_evidence_ids must be a non-empty list")

    def test_rejects_release_blocker_unknown_citation(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet["release_blockers"][0]["source_evidence_ids"] = ["missing-evidence"]

        self.assert_has_error(packet, "release_blockers[0] cites unknown evidence ids: missing-evidence")

    def test_rejects_private_or_session_artifacts(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet["devhub_session_artifact"] = "ppd/local/session/storage_state.json"

        self.assert_has_error(packet, "private/session artifact")

    def test_rejects_raw_crawl_output_references(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet["raw_crawl_output"] = "ppd/local/raw-crawl/devhub-response.warc"

        self.assert_has_error(packet, "raw crawl output reference is not allowed")

    def test_rejects_production_ready_label_with_unresolved_blockers(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet["production_status"] = "ready_for_production"

        self.assert_has_error(packet, "production_status cannot be")

    def test_rejects_consequential_action_enablement(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet["submission_enabled"] = True

        self.assert_has_error(packet, "consequential action enablement is not allowed")


if __name__ == "__main__":
    unittest.main()
