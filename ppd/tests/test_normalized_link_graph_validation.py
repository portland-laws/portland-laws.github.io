from __future__ import annotations

import json
from pathlib import Path
import unittest

from ppd.contracts.normalized_link_graph import validate_normalized_link_graph


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "normalized_link_graph"


class NormalizedLinkGraphValidationTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        graph = _load_fixture("valid_link_graph.json")

        findings = validate_normalized_link_graph(graph)

        self.assertEqual([], findings)

    def test_rejects_noncanonical_source_index_url(self) -> None:
        graph = _load_fixture("valid_link_graph.json")
        graph["sourceIndex"][0]["canonicalUrl"] = "https://www.Portland.gov/ppd/single-pdf-process#overview"

        findings = validate_normalized_link_graph(graph)

        self.assertFinding(findings, "$.sourceIndex[0].canonicalUrl", "canonicalUrl must already be canonicalized")

    def test_rejects_document_canonical_mismatch(self) -> None:
        graph = _load_fixture("valid_link_graph.json")
        graph["documents"][0]["canonicalUrl"] = "https://www.portland.gov/ppd/other-page"

        findings = validate_normalized_link_graph(graph)

        self.assertFinding(findings, "$.documents[0].canonicalUrl", "must match referenced source-index canonicalUrl")

    def test_rejects_unrecognized_content_type(self) -> None:
        graph = _load_fixture("valid_link_graph.json")
        graph["documents"][0]["links"][0]["contentType"] = "webpage"

        findings = validate_normalized_link_graph(graph)

        self.assertFinding(findings, "$.documents[0].links[0].contentType", "contentType is not recognized")

    def test_rejects_missing_source_index_reference(self) -> None:
        graph = _load_fixture("valid_link_graph.json")
        graph["documents"][0]["links"][1]["targetSourceIndexId"] = "missing-source"

        findings = validate_normalized_link_graph(graph)

        self.assertFinding(findings, "$.documents[0].links[1].targetSourceIndexId", "must reference sourceIndex")

    def test_rejects_link_content_type_mismatch_with_source_index(self) -> None:
        graph = _load_fixture("valid_link_graph.json")
        graph["documents"][0]["links"][1]["contentType"] = "html"

        findings = validate_normalized_link_graph(graph)

        self.assertFinding(findings, "$.documents[0].links[1].contentType", "must match referenced source-index contentType")

    def test_rejects_private_devhub_urls(self) -> None:
        graph = _load_fixture("valid_link_graph.json")
        graph["documents"][0]["links"].append(
            {
                "label": "Private upload",
                "targetCanonicalUrl": "https://devhub.portlandoregon.gov/upload/corrections",
                "contentType": "skipped",
                "skippedReason": "private_devhub_path",
            }
        )

        findings = validate_normalized_link_graph(graph)

        self.assertFinding(findings, "$.documents[0].links[4].targetCanonicalUrl", "private DevHub URL")

    def test_rejects_live_crawl_and_private_artifacts(self) -> None:
        graph = _load_fixture("valid_link_graph.json")
        graph["documents"][0]["rawHtml"] = "raw crawl body"
        graph["documents"][0]["tracePath"] = "ppd/data/private/devhub/session/trace.zip"
        graph["documents"][0]["documentPath"] = "ppd/data/raw/downloads/form.pdf"
        graph["documents"][0]["token"] = "secret-fixture-token"

        findings = validate_normalized_link_graph(graph)

        self.assertFinding(findings, "$.documents[0].rawHtml", "raw response body")
        self.assertFinding(findings, "$.documents[0].tracePath", "private or live crawl artifact")
        self.assertFinding(findings, "$.documents[0].documentPath", "downloaded document path")
        self.assertFinding(findings, "$.documents[0].token", "credential field")

    def assertFinding(self, findings, path_fragment: str, reason_fragment: str) -> None:
        matched = [
            finding
            for finding in findings
            if path_fragment in finding.path and reason_fragment in finding.reason
        ]
        self.assertTrue(matched, f"missing finding for {path_fragment!r} / {reason_fragment!r}: {findings!r}")


def _load_fixture(name: str) -> dict:
    with (FIXTURE_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


if __name__ == "__main__":
    unittest.main()
