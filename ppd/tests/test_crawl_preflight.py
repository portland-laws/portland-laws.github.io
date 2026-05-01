#!/usr/bin/env python3
"""Deterministic checks for PP&D crawl-policy and robots helpers."""

from __future__ import annotations

import unittest
from pathlib import Path

from ppd.crawler.crawl_policy import CrawlPolicy, preflight_url
from ppd.crawler.robots import RobotsPolicy


class RobotsPolicyTests(unittest.TestCase):
    def test_disallow_blocks_longest_matching_path(self) -> None:
        robots = RobotsPolicy.from_text(
            "\n".join(
                [
                    "User-agent: *",
                    "Disallow: /ppd/private",
                    "Allow: /ppd/private/public-summary",
                ]
            )
        )
        blocked = robots.can_fetch("https://www.portland.gov/ppd/private/case")
        allowed = robots.can_fetch("https://www.portland.gov/ppd/private/public-summary")
        self.assertFalse(blocked.allowed)
        self.assertEqual(blocked.reason, "robots_disallowed")
        self.assertTrue(allowed.allowed)
        self.assertEqual(allowed.reason, "robots_allowed")

    def test_no_matching_group_allows_by_default(self) -> None:
        robots = RobotsPolicy.from_text("User-agent: unrelated-bot\nDisallow: /")
        decision = robots.can_fetch("https://www.portland.gov/ppd")
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "robots_no_matching_group")


class CrawlPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = CrawlPolicy.load(Path("ppd/crawler/allowlist.json"))

    def test_allows_public_ppd_seed_after_robots(self) -> None:
        robots = RobotsPolicy.from_text("User-agent: *\nAllow: /ppd\nCrawl-delay: 2")
        decision = self.policy.preflight("https://www.portland.gov/ppd", robots_policy=robots)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason_code, "allowed")
        self.assertEqual(decision.details.get("crawl_delay_seconds"), 2.0)

    def test_rejects_non_https_and_unlisted_hosts(self) -> None:
        self.assertEqual(
            self.policy.preflight("http://www.portland.gov/ppd").reason_code,
            "scheme_not_https",
        )
        self.assertEqual(
            self.policy.preflight("https://example.com/ppd").reason_code,
            "host_not_allowlisted",
        )

    def test_rejects_private_or_consequential_devhub_paths(self) -> None:
        decision = self.policy.preflight("https://devhub.portlandoregon.gov/my-permits/payment")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, "private_or_authenticated")

    def test_rejects_content_type_outside_phase_scope(self) -> None:
        decision = self.policy.preflight("https://www.portland.gov/ppd", content_type="application/json")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, "content_type_not_allowed")

    def test_preflight_url_accepts_inline_robots_fixture(self) -> None:
        decision = preflight_url(
            "https://www.portland.gov/ppd",
            robots_text="User-agent: *\nDisallow: /admin\nAllow: /ppd",
        )
        self.assertTrue(decision.allowed)


if __name__ == "__main__":
    unittest.main()
