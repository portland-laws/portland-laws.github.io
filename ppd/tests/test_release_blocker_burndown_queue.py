import copy
import unittest
from pathlib import Path

from ppd.readiness.burndown_queue import (
    build_burndown_queue,
    load_burndown_queue_fixture,
    validate_burndown_queue,
)
from ppd.readiness.reconciliation import REQUIRED_DISABLED_CAPABILITIES, load_packet


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "readiness"
RECONCILIATION_FIXTURE = FIXTURE_DIR / "reconciliation_packet.json"
BURNDOWN_FIXTURE = FIXTURE_DIR / "burndown_queue.json"


class ReleaseBlockerBurndownQueueTest(unittest.TestCase):
    def setUp(self) -> None:
        self.reconciliation_packet = load_packet(RECONCILIATION_FIXTURE)
        self.expected_queue = load_burndown_queue_fixture(BURNDOWN_FIXTURE)

    def test_builds_expected_fixture_first_queue(self) -> None:
        queue = build_burndown_queue(self.reconciliation_packet)

        self.assertEqual(self.expected_queue, queue)
        self.assertEqual([], validate_burndown_queue(queue))
        self.assertEqual("fixture_first", queue["mode"])
        self.assertFalse(queue["production_ready"])
        self.assertFalse(queue["live_crawl_enabled"])
        self.assertFalse(queue["devhub_automation_enabled"])

    def test_orders_unresolved_blockers_by_required_burndown_dimensions(self) -> None:
        queue = build_burndown_queue(self.reconciliation_packet)

        self.assertEqual(
            [
                "source_freshness",
                "guardrail_staleness",
                "regression_coverage",
                "attended_pilot_evidence_readiness",
            ],
            [item["priority_dimension"] for item in queue["ordered_blockers"]],
        )
        self.assertEqual(
            [
                "registry-candidate-not-promoted",
                "guardrail-audit-stale",
                "agent-regression-fixture-only",
                "pilot-evidence-template-only",
            ],
            [item["blocker_id"] for item in queue["ordered_blockers"]],
        )
        self.assertEqual([1, 2, 3, 4], [item["rank"] for item in queue["ordered_blockers"]])

    def test_each_queue_item_has_owner_prompt_and_prerequisite_packet(self) -> None:
        queue = build_burndown_queue(self.reconciliation_packet)

        for item in queue["ordered_blockers"]:
            self.assertEqual("open", item["status"])
            self.assertTrue(item["source_evidence_ids"])
            self.assertTrue(item["owner_prompt"])
            self.assertTrue(item["prerequisite_packet_id"])
            self.assertTrue(item["prerequisite_packet_version"])
            self.assertEqual(
                "fixture_only_no_live_crawl_no_devhub_automation",
                item["automation_boundary"],
            )

    def test_keeps_live_and_consequential_capabilities_disabled(self) -> None:
        queue = build_burndown_queue(self.reconciliation_packet)

        self.assertTrue(REQUIRED_DISABLED_CAPABILITIES.issubset(set(queue["disabled_capabilities"])))
        self.assertFalse(queue["production_ready"])
        self.assertFalse(queue["live_crawl_enabled"])
        self.assertFalse(queue["devhub_automation_enabled"])

    def test_rejects_invalid_reconciliation_packet_before_queue_build(self) -> None:
        packet = copy.deepcopy(self.reconciliation_packet)
        packet["release_blockers"][0]["source_evidence_ids"] = ["missing-evidence"]

        with self.assertRaisesRegex(ValueError, "invalid reconciliation packet"):
            build_burndown_queue(packet)

    def test_queue_validator_rejects_release_ready_label(self) -> None:
        queue = build_burndown_queue(self.reconciliation_packet)
        queue["release_status"] = "ready_for_release"

        errors = validate_burndown_queue(queue)

        self.assertTrue(any("release-ready" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
