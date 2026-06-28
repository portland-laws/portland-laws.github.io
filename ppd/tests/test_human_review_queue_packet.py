from __future__ import annotations

import unittest
from copy import deepcopy
from pathlib import Path

from ppd.agent_readiness.e2e_digest import load_e2e_readiness_digest_fixture
from ppd.agent_readiness.human_review_queue import (
    HumanReviewQueuePacketError,
    build_human_review_queue_packet,
    load_human_review_queue_expected_fixture,
    validate_human_review_queue_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures"
DIGEST_FIXTURE_PATH = FIXTURE_DIR / "e2e_readiness_digest" / "synthetic_case_status.json"
EXPECTED_QUEUE_PATH = FIXTURE_DIR / "human_review_queue" / "single_pdf_review_queue_expected.json"


class HumanReviewQueuePacketTest(unittest.TestCase):
    def test_builds_ordered_human_review_queue_without_production_readiness(self) -> None:
        digest = load_e2e_readiness_digest_fixture(DIGEST_FIXTURE_PATH)
        expected = load_human_review_queue_expected_fixture(EXPECTED_QUEUE_PATH)

        packet = build_human_review_queue_packet(digest)

        self.assertEqual(packet["packet_type"], expected["packet_type"])
        self.assertEqual(packet["case_id"], expected["case_id"])
        self.assertEqual(packet["process_id"], expected["process_id"])
        self.assertEqual(packet["review_status"], expected["review_status"])
        self.assertIs(packet["production_ready"], False)
        self.assertIs(packet["official_readiness"], False)
        self.assertIs(packet["live_services_called"], False)
        self.assertIs(packet["blocked_from_production"], True)
        self.assertEqual([item["category"] for item in packet["review_items"]], expected["review_item_categories"])
        self.assertEqual([item["review_item_id"] for item in packet["review_items"]], expected["review_item_ids"])
        self.assertEqual([item["order"] for item in packet["review_items"]], [1, 2, 3, 4, 5, 6])
        self.assertTrue(all(item["status"] == "human_review_required" for item in packet["review_items"]))
        self.assertTrue(all(item["production_ready"] is False for item in packet["review_items"]))
        self.assertIn("ev-ppd-fee-payment", packet["review_items"][4]["source_evidence_ids"])
        self.assertIn("ev-ppd-file-naming", packet["review_items"][4]["source_evidence_ids"])
        self.assertTrue(packet["review_items"][5]["blocking_reasons"])
        self.assertEqual(validate_human_review_queue_packet(packet), [])

    def test_rejects_digest_that_claims_official_readiness(self) -> None:
        digest = load_e2e_readiness_digest_fixture(DIGEST_FIXTURE_PATH)
        digest["official_readiness"] = True

        with self.assertRaises(HumanReviewQueuePacketError) as context:
            build_human_review_queue_packet(digest)

        self.assertIn("digest must not mark official_readiness", context.exception.problems)

    def test_validation_rejects_production_ready_review_item(self) -> None:
        digest = load_e2e_readiness_digest_fixture(DIGEST_FIXTURE_PATH)
        packet = build_human_review_queue_packet(digest)
        unsafe_packet = deepcopy(packet)
        unsafe_packet["review_items"][0]["production_ready"] = True

        problems = validate_human_review_queue_packet(unsafe_packet)

        self.assertIn("review_items[0] must not mark production_ready", problems)
        self.assertIn("human review queue contains production-ready status", problems)

    def test_validation_rejects_reordered_categories(self) -> None:
        digest = load_e2e_readiness_digest_fixture(DIGEST_FIXTURE_PATH)
        packet = build_human_review_queue_packet(digest)
        reordered_packet = deepcopy(packet)
        reordered_packet["review_items"][0], reordered_packet["review_items"][1] = (
            reordered_packet["review_items"][1],
            reordered_packet["review_items"][0],
        )
        reordered_packet["review_items"][0]["order"] = 1
        reordered_packet["review_items"][1]["order"] = 2

        problems = validate_human_review_queue_packet(reordered_packet)

        self.assertIn("human review queue categories are not in the required order", problems)


if __name__ == "__main__":
    unittest.main()
