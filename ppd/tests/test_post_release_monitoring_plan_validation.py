from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.agent_readiness.post_release_monitoring_plan_validation import (
    require_post_release_monitoring_plan,
    validate_post_release_monitoring_plan,
)


_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "post_release_monitoring_plan"


class PostReleaseMonitoringPlanValidationTest(unittest.TestCase):
    def test_accepts_fixture_only_public_read_only_monitoring_plan(self) -> None:
        packet = _load_fixture("valid_monitoring_plan.json")

        result = validate_post_release_monitoring_plan(packet)

        self.assertTrue(result.ready, result.problems)
        require_post_release_monitoring_plan(packet)

    def test_rejects_uncited_private_live_mutating_monitoring_plan(self) -> None:
        packet = _load_fixture("invalid_monitoring_plan.json")

        result = validate_post_release_monitoring_plan(packet)

        self.assertFalse(result.ready)
        joined = "\n".join(result.problems)
        self.assertIn("monitoring check lacks citation", joined)
        self.assertIn("monitoring check cites unknown source evidence unknown-evidence", joined)
        self.assertIn("monitoring check lacks reviewer owner", joined)
        self.assertIn("monitoring check lacks escalation note", joined)
        self.assertIn("monitoring check lacks alert threshold", joined)
        self.assertIn("private or authenticated URL is not allowed", joined)
        self.assertIn("raw body/download/archive reference is not allowed", joined)
        self.assertIn("local private path is not allowed", joined)
        self.assertIn("live monitor/fetch/browser execution claim is not allowed", joined)
        self.assertIn("active schedule flag is not allowed", joined)
        self.assertIn("artifact mutation flag is not allowed", joined)
        with self.assertRaises(ValueError):
            require_post_release_monitoring_plan(packet)


def _load_fixture(name: str) -> dict[str, object]:
    with (_FIXTURE_DIR / name).open(encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise AssertionError(f"fixture {name} must contain a JSON object")
    return loaded


if __name__ == "__main__":
    unittest.main()
