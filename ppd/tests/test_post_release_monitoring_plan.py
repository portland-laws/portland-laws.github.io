from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.monitoring.post_release import build_post_release_monitoring_plan


class PostReleaseMonitoringPlanTests(unittest.TestCase):
    def test_fixture_inputs_build_cited_watch_plan_without_live_side_effects(self) -> None:
        fixture_path = Path(__file__).parent / "fixtures" / "post_release_monitoring" / "sample_inputs.json"
        packet = json.loads(fixture_path.read_text(encoding="utf-8"))

        plan = build_post_release_monitoring_plan(packet)

        self.assertTrue(plan["does_not_run_monitors"])
        self.assertTrue(plan["does_not_fetch_sources"])
        self.assertTrue(plan["does_not_launch_browsers"])
        self.assertTrue(plan["does_not_mutate_schedules"])
        self.assertEqual(len(plan["monitoring_checks"]), 2)
        self.assertEqual(len(plan["stale_source_watch_items"]), 1)
        self.assertEqual(len(plan["devhub_drift_watch_items"]), 2)
        self.assertGreaterEqual(len(plan["guardrail_regression_watch_items"]), 3)

        for check in plan["monitoring_checks"]:
            self.assertTrue(check["citations"], check)
            self.assertIn("owner", check)
            self.assertIn("alert_threshold", check)

        stale_watch = plan["stale_source_watch_items"][0]
        self.assertEqual(stale_watch["source_id"], "source-submit-plans-online")
        self.assertEqual(stale_watch["alert_level"], "warning")
        self.assertIn("citation", stale_watch)

        non_read_only_drift = [
            item for item in plan["devhub_drift_watch_items"] if item["packet_id"] == "devhub-fee-payment-action-ignored"
        ][0]
        self.assertEqual(non_read_only_drift["alert_level"], "critical")
        self.assertFalse(non_read_only_drift["read_only_surface"])
        self.assertTrue(
            any("not marked read-only" in note for note in plan["abort_escalation_notes"]),
            plan["abort_escalation_notes"],
        )

        owners = plan["reviewer_owners"]
        self.assertIn("ppd_legal_guardrail_reviewer", owners)
        self.assertIn("ppd_devhub_surface_reviewer", owners)

    def test_missing_citation_adds_abort_note(self) -> None:
        packet = {
            "plan_id": "missing-citation-fixture",
            "generated_from_fixture_at": "2026-05-29T00:00:00Z",
            "source_evidence": [],
            "release_notes_candidates": [
                {
                    "candidate_id": "rn-missing",
                    "title": "Missing evidence candidate",
                    "risk_level": "high",
                    "source_evidence_ids": ["missing-evidence"],
                    "guardrail_bundle_ids": ["guardrail-missing"],
                }
            ],
            "source_freshness_badges": [],
            "devhub_drift_comparison_packets": [],
        }

        plan = build_post_release_monitoring_plan(packet)

        self.assertEqual(plan["monitoring_checks"][0]["citations"], [])
        self.assertTrue(any("missing source evidence fixture" in note for note in plan["abort_escalation_notes"]))
        self.assertTrue(any("no source citations" in note for note in plan["abort_escalation_notes"]))


if __name__ == "__main__":
    unittest.main()
