import json
import unittest
from datetime import datetime, timezone
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "blocked_cascade_daemon_repair"
    / "tranche12_item3.json"
)


def parse_instant(value):
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def repair_releases_blocked_item(blocked_item, repair_task):
    if blocked_item["status"] != "parked":
        return False
    if repair_task.get("kind") != "daemon-repair":
        return False
    if repair_task.get("repairs") != blocked_item["blocked_by"]:
        return False
    if repair_task.get("status") != "validated":
        return False

    blocked_at = parse_instant(blocked_item["blocked_at"])
    created_at = parse_instant(repair_task.get("created_at"))
    validated_at = parse_instant(repair_task.get("validated_at"))
    if created_at is None or validated_at is None:
        return False
    return created_at > blocked_at and validated_at >= created_at


def cascade_state_after_repairs(blocked_item, repair_tasks):
    for repair_task in repair_tasks:
        if repair_releases_blocked_item(blocked_item, repair_task):
            return "ready_for_daemon"
    return "parked"


class BlockedCascadeDaemonRepairTranche12Item3Test(unittest.TestCase):
    def setUp(self):
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture = json.load(fixture_file)

    def test_blocked_work_stays_parked_without_fresh_validated_repair(self):
        blocked_item = self.fixture["blocked_item"]
        pre_validation_repairs = self.fixture["repair_tasks"][:3]

        self.assertEqual(
            cascade_state_after_repairs(blocked_item, pre_validation_repairs),
            "parked",
        )

    def test_blocked_work_releases_after_fresh_validated_repair(self):
        blocked_item = self.fixture["blocked_item"]
        all_repairs = self.fixture["repair_tasks"]

        self.assertEqual(
            cascade_state_after_repairs(blocked_item, all_repairs),
            "ready_for_daemon",
        )


if __name__ == "__main__":
    unittest.main()
