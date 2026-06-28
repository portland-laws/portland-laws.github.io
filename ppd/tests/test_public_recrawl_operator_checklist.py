from __future__ import annotations

import json
from pathlib import Path
import unittest

from ppd.crawler.public_recrawl_operator_checklist import (
    assert_public_recrawl_operator_checklist_packet_is_safe,
    issue_codes,
    validate_public_recrawl_operator_checklist_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_recrawl_operator_checklist"


class PublicRecrawlOperatorChecklistValidationTest(unittest.TestCase):
    def _load_fixture(self, name: str) -> dict[str, object]:
        with (FIXTURE_DIR / name).open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        self.assertIsInstance(payload, dict)
        return payload

    def test_accepts_safe_metadata_only_operator_checklist(self) -> None:
        packet = self._load_fixture("safe_operator_checklist_packet.json")
        issues = validate_public_recrawl_operator_checklist_packet(packet)
        self.assertEqual([], issues)
        assert_public_recrawl_operator_checklist_packet_is_safe(packet)

    def test_rejects_public_recrawl_operator_checklist_unsafe_claims(self) -> None:
        packet = self._load_fixture("unsafe_operator_checklist_packet.json")
        issues = validate_public_recrawl_operator_checklist_packet(packet)
        codes = issue_codes(issues)
        self.assertIn("live_network_execution_claim", codes)
        self.assertIn("outside_allowlist_host", codes)
        self.assertIn("private_or_authenticated_url", codes)
        self.assertIn("raw_body_persistence", codes)
        self.assertIn("downloaded_document_path", codes)
        self.assertIn("missing_abort_conditions", codes)
        self.assertIn("missing_post_run_review_prompts", codes)
        self.assertIn("direct_production_promotion", codes)

        with self.assertRaises(ValueError) as context:
            assert_public_recrawl_operator_checklist_packet_is_safe(packet)
        message = str(context.exception)
        self.assertIn("live_network_execution_claim", message)
        self.assertIn("direct_production_promotion", message)


if __name__ == "__main__":
    unittest.main()
