from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.contracts.public_source_registry_promotion import (
    assert_public_source_registry_promotion_packet,
    validate_public_source_registry_promotion_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_source_registry_promotion_packets.json"


class PublicSourceRegistryPromotionPacketValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_valid_promoted_packet_passes(self) -> None:
        packet = self.fixture["valid_promoted_packet"]
        verdict = validate_public_source_registry_promotion_packet(packet)
        self.assertTrue(verdict.allowed)
        self.assertEqual((), verdict.reasons)
        assert_public_source_registry_promotion_packet(packet)

    def test_promoted_packet_rejects_required_unsafe_conditions(self) -> None:
        packet = self.fixture["invalid_promoted_packet"]
        verdict = validate_public_source_registry_promotion_packet(packet)
        self.assertFalse(verdict.allowed)
        self.assertIn("missing_rehearsal_link", verdict.reasons)
        self.assertIn("missing_release_gate_link", verdict.reasons)
        self.assertIn("missing_rollback_notes", verdict.reasons)
        self.assertIn("private_or_authenticated_url", verdict.reasons)
        self.assertIn("raw_crawl_download_or_archive_path", verdict.reasons)
        self.assertIn("unresolved_blocker_marked_promoted", verdict.reasons)
        self.assertIn("live_registry_mutation_flag", verdict.reasons)
        self.assertIn("network_execution_claim", verdict.reasons)

    def test_assert_helper_raises_with_machine_readable_reasons(self) -> None:
        with self.assertRaises(ValueError) as raised:
            assert_public_source_registry_promotion_packet(self.fixture["invalid_promoted_packet"])
        message = str(raised.exception)
        self.assertIn("missing_rehearsal_link", message)
        self.assertIn("network_execution_claim", message)


if __name__ == "__main__":
    unittest.main()
