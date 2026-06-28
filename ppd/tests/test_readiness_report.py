from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.readiness_report import build_readiness_report, load_fixture, report_as_json


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "readiness_report" / "minimal_readiness_fixture.json"


class ReadinessReportTests(unittest.TestCase):
    def test_minimal_fixture_is_ready(self) -> None:
        fixture = load_fixture(FIXTURE_PATH)

        report = build_readiness_report(fixture)

        self.assertTrue(report["ready"])
        self.assertEqual(report["fixture_id"], "synthetic-ppd-readiness-minimal-v1")
        self.assertEqual(report["blocking_check_ids"], [])
        self.assertGreaterEqual(report["counts"]["requirements"], 2)
        self.assertTrue(all(check["status"] == "pass" for check in report["checks"]))

    def test_report_serialization_is_deterministic(self) -> None:
        fixture = load_fixture(FIXTURE_PATH)
        first = report_as_json(build_readiness_report(fixture))
        second = report_as_json(build_readiness_report(fixture))

        self.assertEqual(first, second)
        parsed = json.loads(first)
        self.assertEqual(parsed["report_version"], "ppd-readiness-report-v1")

    def test_missing_guardrail_bundle_blocks_readiness(self) -> None:
        fixture = load_fixture(FIXTURE_PATH)
        fixture["guardrail_bundles"] = []

        report = build_readiness_report(fixture)

        self.assertFalse(report["ready"])
        self.assertIn("guardrails_cover_process_models", report["blocking_check_ids"])


if __name__ == "__main__":
    unittest.main()
