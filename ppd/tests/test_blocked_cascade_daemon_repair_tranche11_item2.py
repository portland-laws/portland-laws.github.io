"""Generated blocked-cascade daemon-repair coverage for tranche 11 item 2."""

import json
import unittest
from datetime import datetime
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "blocked_cascade_daemon_repair"
    / "tranche11_item2.json"
)


def _parse_instant(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _eligible_after_validated_repair(blocked_work, validations):
    eligible = []
    still_parked = []

    for item in blocked_work:
        blocked_at = _parse_instant(item["blocked_at"])
        repair_task_id = item["repair_task_id"]
        has_fresh_repair = any(
            validation.get("task_id") == repair_task_id
            and validation.get("kind") == "daemon-repair"
            and validation.get("status") == "passed"
            and _parse_instant(validation["validated_at"]) > blocked_at
            for validation in validations
        )

        if has_fresh_repair:
            eligible.append(item["id"])
        else:
            still_parked.append(item["id"])

    return {"eligible": eligible, "parked": still_parked}


class BlockedCascadeDaemonRepairTranche11Item2Test(unittest.TestCase):
    def setUp(self):
        with FIXTURE_PATH.open(encoding="utf-8") as handle:
            self.fixture = json.load(handle)

    def test_blocked_ppd_work_stays_parked_without_fresh_daemon_repair(self):
        result = _eligible_after_validated_repair(
            self.fixture["blocked_work"],
            self.fixture["validations"]["stale_or_unrelated"],
        )

        self.assertEqual([], result["eligible"])
        self.assertEqual(
            self.fixture["expected"]["parked_before_fresh_repair"],
            result["parked"],
        )

    def test_fresh_daemon_repair_validation_unparks_blocked_cascade(self):
        result = _eligible_after_validated_repair(
            self.fixture["blocked_work"],
            self.fixture["validations"]["stale_or_unrelated"]
            + self.fixture["validations"]["fresh_daemon_repair"],
        )

        self.assertEqual(
            self.fixture["expected"]["released_after_fresh_repair"],
            result["eligible"],
        )
        self.assertEqual([], result["parked"])


if __name__ == "__main__":
    unittest.main()
