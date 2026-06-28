from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from ppd.agent_missing_information import (
    MissingInformationRequest,
    load_missing_information_fixture,
)


class AgentMissingInformationApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture_path = (
            Path(__file__).parent
            / "fixtures"
            / "missing_information"
            / "synthetic_residential_addition_case.json"
        )

    def test_fixture_returns_only_follow_up_fact_statuses(self) -> None:
        payload = load_missing_information_fixture(
            MissingInformationRequest("synthetic_residential_addition_case"),
            fixture_path=self.fixture_path,
        )

        self.assertEqual(payload["case_id"], "synthetic_residential_addition_case")
        self.assertTrue(payload["facts"])
        self.assertEqual(
            {fact["status"] for fact in payload["facts"]},
            {"missing", "stale", "ambiguous", "conflicting"},
        )

    def test_fixture_redacts_private_values_and_omits_local_paths(self) -> None:
        payload = load_missing_information_fixture(fixture_path=self.fixture_path)
        serialized = json.dumps(payload, sort_keys=True)

        self.assertNotRegex(serialized, re.compile(r"(?:^|\s)/(?:home|Users|tmp|var|private|mnt|Volumes)/"))
        self.assertNotRegex(serialized, re.compile(r"[A-Za-z]:\\\\"))
        self.assertNotIn("file://", serialized)

        for fact in payload["facts"]:
            self.assertIn("question", fact)
            self.assertNotIn("local_path", fact)
            self.assertNotIn("file_path", fact)
            self.assertIn(fact.get("current_value"), (None, "[REDACTED]"))


if __name__ == "__main__":
    unittest.main()
