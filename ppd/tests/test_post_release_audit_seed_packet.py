from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.post_release_audit_seed_packet import (
    assert_post_release_audit_seed_packet_safe,
    validate_post_release_audit_seed_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "post_release_audit_seed_packets"


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


class PostReleaseAuditSeedPacketValidationTests(unittest.TestCase):
    def test_safe_seed_packet_is_allowed(self) -> None:
        verdict = validate_post_release_audit_seed_packet(load_fixture("safe_seed_packet.json"))

        self.assertTrue(verdict.allowed)
        self.assertEqual((), verdict.reasons)

    def test_unsafe_seed_packet_reports_required_blockers(self) -> None:
        verdict = validate_post_release_audit_seed_packet(load_fixture("unsafe_seed_packet.json"))

        self.assertFalse(verdict.allowed)
        self.assertIn("missing_prerequisite_links", verdict.reasons)
        self.assertIn("uncited_audit_claims", verdict.reasons)
        self.assertIn("private_or_session_artifact_reference", verdict.reasons)
        self.assertIn("raw_crawl_download_or_archive_reference", verdict.reasons)
        self.assertIn("legal_or_permitting_outcome_guarantee", verdict.reasons)
        self.assertIn("production_ready_label_with_blockers", verdict.reasons)
        self.assertIn("live_network_or_devhub_execution_claim", verdict.reasons)
        self.assertIn("enabled_consequential_capability", verdict.reasons)

    def test_assertion_helper_rejects_unsafe_packet(self) -> None:
        with self.assertRaisesRegex(ValueError, "post-release audit seed packet rejected"):
            assert_post_release_audit_seed_packet_safe(load_fixture("unsafe_seed_packet.json"))

    def test_each_consequential_enabled_capability_is_rejected(self) -> None:
        base = load_fixture("safe_seed_packet.json")
        for capability in ("payment", "upload", "submission", "scheduling", "cancellation", "certification"):
            packet = dict(base)
            packet["capabilities"] = [{"name": capability, "enabled": True}]

            verdict = validate_post_release_audit_seed_packet(packet)

            self.assertFalse(verdict.allowed, capability)
            self.assertIn("enabled_consequential_capability", verdict.reasons)


if __name__ == "__main__":
    unittest.main()
