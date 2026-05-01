"""Fixture checks for public PP&D HTML guidance extraction."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.extraction.html import extract_public_guidance_html


FIXTURE_PATH = Path("ppd/tests/fixtures/html_public_guidance.json")


class HtmlExtractionFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["fixtures"]

    def test_fixture_file_is_public_and_curated(self) -> None:
        self.assertGreaterEqual(len(self.fixtures), 3)
        for fixture in self.fixtures:
            self.assertTrue(fixture["source_url"].startswith("https://www.portland.gov/ppd"))
            self.assertNotIn("storage-state", fixture["html"].lower())
            self.assertNotIn("auth-state", fixture["html"].lower())
            self.assertNotIn("payment card", fixture["html"].lower())

    def test_expected_extraction_matches_html(self) -> None:
        for fixture in self.fixtures:
            with self.subTest(fixture=fixture["id"]):
                parsed = extract_public_guidance_html(
                    fixture["html"],
                    base_url=fixture.get("base_url", fixture["source_url"]),
                )
                expected = fixture["expected"]
                self.assertEqual(parsed.title, expected["title"])
                self.assertEqual(list(parsed.headings), expected.get("headings", []))
                self.assertEqual(list(parsed.list_items), expected.get("list_items", []))
                self.assertEqual(
                    [{"url": link.url, "label": link.label} for link in parsed.links],
                    expected.get("links", []),
                )
                self.assertEqual(
                    [{"src": image.src, "alt": image.alt} for image in parsed.images],
                    expected.get("images", []),
                )
                self.assertEqual(
                    [
                        {"headers": list(table.headers), "rows": [list(row) for row in table.rows]}
                        for table in parsed.tables
                    ],
                    expected.get("tables", []),
                )
                if "modified_date" in expected:
                    self.assertEqual(parsed.modified_date, expected["modified_date"])


if __name__ == "__main__":
    unittest.main()
