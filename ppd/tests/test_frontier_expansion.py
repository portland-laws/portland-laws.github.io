import json
import unittest
from pathlib import Path

from ppd.contracts.frontier import (
    DiscoveredFrontierLink,
    FrontierContentType,
    FrontierExpansion,
    FrontierExpansionSummary,
    FrontierLinkRelation,
    SkippedFrontierUrl,
    SkippedUrlReason,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "frontier_expansion.json"


def build_expansion(data: dict) -> FrontierExpansion:
    discovered = tuple(
        DiscoveredFrontierLink(
            id=item["id"],
            source_url=item["sourceUrl"],
            raw_href=item["rawHref"],
            normalized_url=item["normalizedUrl"],
            label=item["label"],
            content_type=FrontierContentType(item["contentType"]),
            relation=FrontierLinkRelation(item["relation"]),
            allowed_domain=bool(item["allowedDomain"]),
            crawl_candidate=bool(item["crawlCandidate"]),
            evidence_selector=item.get("evidenceSelector"),
        )
        for item in data["discoveredLinks"]
    )
    skipped = tuple(
        SkippedFrontierUrl(
            id=item["id"],
            source_url=item["sourceUrl"],
            raw_href=item["rawHref"],
            normalized_url=item["normalizedUrl"],
            label=item.get("label", ""),
            content_type=FrontierContentType(item["contentType"]),
            reason=SkippedUrlReason(item["reason"]),
            evidence_selector=item.get("evidenceSelector"),
        )
        for item in data["skippedUrls"]
    )
    summary = FrontierExpansionSummary(
        total_links_seen=int(data["summary"]["totalLinksSeen"]),
        discovered_count=int(data["summary"]["discoveredCount"]),
        skipped_count=int(data["summary"]["skippedCount"]),
        crawl_candidate_count=int(data["summary"]["crawlCandidateCount"]),
        content_type_counts=dict(data["summary"]["contentTypeCounts"]),
        skipped_reason_counts=dict(data["summary"]["skippedReasonCounts"]),
    )
    return FrontierExpansion(
        fixture_id=data["fixtureId"],
        source_document_id=data["sourceDocumentId"],
        source_url=data["sourceUrl"],
        expanded_at=data["expandedAt"],
        allowed_domains=tuple(data["allowedDomains"]),
        discovered_links=discovered,
        skipped_urls=skipped,
        summary=summary,
    )


class FrontierExpansionTests(unittest.TestCase):
    def load_fixture(self) -> dict:
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fixture_validates(self) -> None:
        expansion = build_expansion(self.load_fixture())
        self.assertFalse(expansion.validate())

    def test_fixture_covers_required_classifications(self) -> None:
        data = self.load_fixture()
        content_types = {item["contentType"] for item in data["discoveredLinks"] + data["skippedUrls"]}
        skip_reasons = {item["reason"] for item in data["skippedUrls"]}

        self.assertTrue({"html", "pdf", "mailto", "phone", "portal_action", "external_site", "other"} <= content_types)
        self.assertTrue(
            {
                "duplicate_url",
                "disallowed_domain",
                "unsupported_scheme",
                "fragment_only",
                "private_or_authenticated",
            }
            <= skip_reasons
        )

    def test_crawl_candidate_urls_are_unique(self) -> None:
        data = self.load_fixture()
        urls = [item["normalizedUrl"] for item in data["discoveredLinks"] if item["crawlCandidate"]]
        self.assertEqual(len(urls), len(set(urls)))


if __name__ == "__main__":
    unittest.main()
