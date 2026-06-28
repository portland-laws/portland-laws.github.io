from __future__ import annotations

import unittest

from ppd.crawler.public_source_recrawl_dry_run_command_plan import (
    assert_valid_public_source_recrawl_dry_run_command_plan,
    validate_public_source_recrawl_dry_run_command_plan,
)


class PublicSourceRecrawlDryRunCommandPlanTests(unittest.TestCase):
    def test_accepts_public_allowlisted_planning_only_plan(self) -> None:
        plan = {
            "targets": [{"url": "https://www.portland.gov/bds/documents"}],
            "robots_txt_evidence": "robots.txt reviewed for allowed public document paths",
            "policy_evidence": "public PP&D source page documents public records access",
            "rate_limit_notes": "one request at a time with backoff on 429 or 5xx",
            "abort_conditions": ["robots disallow", "authentication required", "unexpected binary body"],
            "dry_run": True,
        }

        assert_valid_public_source_recrawl_dry_run_command_plan(plan)
        self.assertEqual(validate_public_source_recrawl_dry_run_command_plan(plan), [])

    def test_rejects_unsafe_or_unverifiable_plan_fields(self) -> None:
        plan = {
            "targets": [
                {"url": "https://private.example.test/documents", "authenticated": True},
                {"url": "http://www.portland.gov/bds/documents"},
            ],
            "raw_body_path": "ppd/raw/body.html",
            "download_path": "ppd/downloads/file.pdf",
            "live_fetch": True,
            "execute_processors": True,
            "enable_schedule": True,
        }

        codes = {issue.code for issue in validate_public_source_recrawl_dry_run_command_plan(plan)}

        self.assertIn("private_or_authenticated_target", codes)
        self.assertIn("non_allowlisted_target", codes)
        self.assertIn("non_https_target", codes)
        self.assertIn("missing_robots_evidence", codes)
        self.assertIn("missing_policy_evidence", codes)
        self.assertIn("raw_output_path", codes)
        self.assertIn("live_fetch_or_processor_execution", codes)
        self.assertIn("missing_rate_limit_notes", codes)
        self.assertIn("missing_abort_conditions", codes)
        self.assertIn("schedule_mutation", codes)


if __name__ == "__main__":
    unittest.main()
