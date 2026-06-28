import json
import unittest
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "html_extraction"
    / "synthetic_ppd_guidance_normalized.json"
)


class SyntheticHtmlExtractionFixtureTest(unittest.TestCase):
    def setUp(self):
        with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
            self.fixture = json.load(handle)

    def test_fixture_contains_required_guidance_features(self):
        self.assertEqual(
            self.fixture["title"],
            "Apply for a Synthetic Residential Permit",
        )
        self.assertEqual(
            [crumb["text"] for crumb in self.fixture["breadcrumbs"]],
            [
                "Home",
                "Portland Permitting & Development",
                "Get a Permit",
                "Apply for a Synthetic Residential Permit",
            ],
        )

        kinds = {block["kind"] for block in self.fixture["source_order"]}
        self.assertTrue(
            {
                "title",
                "breadcrumbs",
                "heading",
                "ordered_steps",
                "warning",
                "table",
                "contact",
                "related_links",
                "updated_date",
            }.issubset(kinds)
        )

        steps = self._block("ordered-steps-prepare-request")
        self.assertEqual([item["number"] for item in steps["items"]], [1, 2, 3])
        self.assertIn("official submission", steps["items"][2]["text"])

        warning = self._block("warning-confirm-before-submission")
        self.assertEqual(warning["severity"], "warning")
        self.assertIn("official action", warning["text"])

        table = self._block("table-required-documents")
        self.assertEqual(table["headers"], ["Document", "When required", "Upload note"])
        self.assertEqual(len(table["rows"]), 2)

        contact = self._block("contact-permit-help")
        self.assertEqual(contact["name"], "PP&D Permit Help")
        self.assertEqual(contact["methods"][0]["type"], "phone")

        related = self._block("related-links")
        self.assertEqual(len(related["links"]), 2)

        self.assertEqual(self.fixture["updated_dates"][0]["date"], "2026-05-08")

    def test_source_order_and_citation_spans_are_monotonic(self):
        block_orders = [block["order"] for block in self.fixture["source_order"]]
        self.assertEqual(block_orders, sorted(block_orders))
        self.assertEqual(block_orders, list(range(1, len(block_orders) + 1)))

        citation_orders = [
            span["source_order"] for span in self.fixture["citation_spans"]
        ]
        self.assertEqual(citation_orders, sorted(citation_orders))
        self.assertEqual(citation_orders, list(range(1, len(citation_orders) + 1)))

        block_ids = {block["id"] for block in self.fixture["source_order"]}
        for span in self.fixture["citation_spans"]:
            self.assertIn(span["block_id"], block_ids)
            self.assertTrue(span["text"])

    def _block(self, block_id):
        for block in self.fixture["source_order"]:
            if block["id"] == block_id:
                return block
        self.fail(f"Missing block: {block_id}")


if __name__ == "__main__":
    unittest.main()
