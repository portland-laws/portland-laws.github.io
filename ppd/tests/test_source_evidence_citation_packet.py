import copy
import unittest
from pathlib import Path

from ppd.readiness.burndown_queue import load_burndown_queue_fixture
from ppd.readiness.source_evidence_citation_packet import (
    SourceEvidenceCitationPacketError,
    build_source_evidence_citation_packet,
    load_source_evidence_citation_packet_fixture,
    validate_source_evidence_citation_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "readiness"
BURNDOWN_FIXTURE = FIXTURE_DIR / "burndown_queue.json"
PACKET_FIXTURE = FIXTURE_DIR / "source_evidence_citation_packet.json"


class SourceEvidenceCitationPacketTest(unittest.TestCase):
    def setUp(self) -> None:
        self.queue = load_burndown_queue_fixture(BURNDOWN_FIXTURE)

    def test_builds_review_only_packet_from_burndown_queue(self) -> None:
        packet = build_source_evidence_citation_packet(self.queue)

        self.assertEqual([], validate_source_evidence_citation_packet(packet))
        self.assertEqual("fixture_first", packet["mode"])
        self.assertFalse(packet["crawl_enabled"])
        self.assertFalse(packet["download_enabled"])
        self.assertFalse(packet["active_source_record_replacement_enabled"])
        self.assertFalse(packet["source_registry_promotion_enabled"])
        self.assertEqual(4, packet["review_summary"]["review_count"])
        self.assertEqual(4, packet["review_summary"]["normalized_record_count"])

    def test_committed_fixture_is_valid_and_reviews_required_fields(self) -> None:
        packet = load_source_evidence_citation_packet_fixture(PACKET_FIXTURE)

        self.assertEqual([], validate_source_evidence_citation_packet(packet))
        for review in packet["reviews"]:
            self.assertTrue(review["synthetic_source_id"].startswith("synthetic-"))
            self.assertEqual("current_fixture_only_not_live_verified", review["source_id_freshness_status"])
            self.assertIn("#/ordered_blockers/", review["citation_span_anchor"])
            self.assertTrue(review["normalized_record_ids"])
            self.assertEqual(64, len(review["document_hash"]))
            self.assertEqual("fixture_only_not_live_verified", review["visible_update_date"])
            self.assertTrue(review["downstream_requirement_links"])
        for record in packet["normalized_records"]:
            self.assertEqual("metadata_only_no_raw_body", record["body_storage"])
            self.assertEqual("review_only_no_source_registry_promotion", record["promotion_action"])

    def test_rejects_live_crawl_download_active_replacement_or_registry_promotion(self) -> None:
        packet = build_source_evidence_citation_packet(self.queue)
        packet["crawl_enabled"] = True
        packet["download_enabled"] = True
        packet["active_source_record_replacement_enabled"] = True
        packet["source_registry_promotion_enabled"] = True

        errors = validate_source_evidence_citation_packet(packet)

        self.assertIn("crawl_enabled must be false", errors)
        self.assertIn("download_enabled must be false", errors)
        self.assertIn("active_source_record_replacement_enabled must be false", errors)
        self.assertIn("source_registry_promotion_enabled must be false", errors)

    def test_rejects_non_synthetic_source_id_missing_anchor_and_bad_hash(self) -> None:
        packet = build_source_evidence_citation_packet(self.queue)
        packet["reviews"][0]["synthetic_source_id"] = "official-source-id"
        packet["reviews"][0]["citation_span_anchor"] = "https://www.portland.gov/ppd"
        packet["reviews"][0]["document_hash"] = "not-a-sha256"

        errors = validate_source_evidence_citation_packet(packet)

        self.assertTrue(any("synthetic_source_id must be synthetic" in error for error in errors), errors)
        self.assertTrue(any("citation_span_anchor must point into the burn-down fixture" in error for error in errors), errors)
        self.assertTrue(any("document_hash must be a 64-character" in error for error in errors), errors)

    def test_rejects_missing_visible_update_review_and_downstream_requirement_link(self) -> None:
        packet = build_source_evidence_citation_packet(self.queue)
        packet["reviews"][1]["visible_update_date"] = "2026-05-28"
        packet["reviews"][1]["downstream_requirement_links"] = []

        errors = validate_source_evidence_citation_packet(packet)

        self.assertTrue(any("visible_update_date must be fixture_only_not_live_verified" in error for error in errors), errors)
        self.assertTrue(any("downstream_requirement_links must be a non-empty list" in error for error in errors), errors)

    def test_rejects_uncited_normalized_records(self) -> None:
        packet = build_source_evidence_citation_packet(self.queue)
        packet["normalized_records"].append(
            {
                "record_id": "normalized-uncited-record",
                "source_id": packet["source_registry_snapshot"]["registered_source_ids"][0],
                "source_id_freshness_status": "current_fixture_only_not_live_verified",
                "source_evidence_ids": [packet["reviews"][0]["source_evidence_id"]],
                "citation_span_anchors": [packet["reviews"][0]["citation_span_anchor"]],
                "body_storage": "metadata_only_no_raw_body",
                "document_ref": "fixture_metadata_only:normalized-uncited-record",
                "promotion_action": "review_only_no_source_registry_promotion",
            }
        )
        packet["review_summary"]["normalized_record_count"] = len(packet["normalized_records"])

        errors = validate_source_evidence_citation_packet(packet)

        self.assertTrue(any("record_id must be cited by a review" in error for error in errors), errors)

    def test_rejects_normalized_records_with_missing_or_stale_source_ids(self) -> None:
        packet = build_source_evidence_citation_packet(self.queue)
        packet["normalized_records"][0]["source_id"] = "synthetic-missing-source"
        packet["normalized_records"][1]["source_id_freshness_status"] = "stale_requires_review"
        packet["source_registry_snapshot"]["stale_source_ids"] = [packet["reviews"][1]["synthetic_source_id"]]

        errors = validate_source_evidence_citation_packet(packet)

        self.assertTrue(any("source_id must be present in source_registry_snapshot" in error for error in errors), errors)
        self.assertTrue(any("source_id_freshness_status must be current_fixture_only_not_live_verified" in error for error in errors), errors)
        self.assertIn("source_registry_snapshot.stale_source_ids must be empty", errors)

    def test_rejects_private_authenticated_urls_raw_bodies_and_downloaded_paths(self) -> None:
        packet = build_source_evidence_citation_packet(self.queue)
        packet["normalized_records"][0]["document_ref"] = "https://devhub.portlandoregon.gov/account/permits?token=secret"
        packet["normalized_records"][1]["raw_html_body"] = "private body"
        packet["normalized_records"][2]["document_ref"] = "/home/user/Downloads/devhub-document.pdf"

        errors = validate_source_evidence_citation_packet(packet)

        self.assertTrue(any("private/authenticated URL" in error for error in errors), errors)
        self.assertTrue(any("raw_html_body uses forbidden" in error for error in errors), errors)
        self.assertTrue(any("downloaded document path" in error for error in errors), errors)

    def test_rejects_source_record_replacement_and_direct_registry_promotion(self) -> None:
        packet = build_source_evidence_citation_packet(self.queue)
        packet["reviews"][2]["source_record_action"] = "replace_active_source_record"
        packet["normalized_records"][2]["promotion_action"] = "promote_to_source_registry"

        errors = validate_source_evidence_citation_packet(packet)

        self.assertTrue(any("source_record_action must not replace active source records" in error for error in errors), errors)
        self.assertTrue(any("promotion_action must be review-only" in error for error in errors), errors)
        self.assertTrue(any("forbidden" in error for error in errors), errors)

    def test_rejects_invalid_burndown_queue_before_packet_build(self) -> None:
        queue = copy.deepcopy(self.queue)
        queue["live_crawl_enabled"] = True

        with self.assertRaisesRegex(SourceEvidenceCitationPacketError, "invalid burn-down queue"):
            build_source_evidence_citation_packet(queue)


if __name__ == "__main__":
    unittest.main()
