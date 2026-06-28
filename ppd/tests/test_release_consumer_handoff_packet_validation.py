from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from ppd.agent_readiness.release_consumer_handoff_packet import (
    require_release_consumer_handoff_packet,
    validate_release_consumer_handoff_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "agent_readiness" / "release_consumer_handoff_packet.json"


class ReleaseConsumerHandoffPacketValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_valid_fixture_is_ready(self) -> None:
        result = validate_release_consumer_handoff_packet(self.fixture["valid_packet"])
        self.assertTrue(result.ready, result.problems)

    def test_required_guardrail_failures_are_rejected(self) -> None:
        for case in self.fixture["invalid_cases"]:
            with self.subTest(case=case["name"]):
                packet = deepcopy(self.fixture["valid_packet"])
                packet.update(case["patch"])
                result = validate_release_consumer_handoff_packet(packet)
                self.assertFalse(result.ready)
                self.assertTrue(
                    any(case["problem"] in problem for problem in result.problems),
                    result.problems,
                )

    def test_require_raises_for_unsafe_handoff(self) -> None:
        packet = deepcopy(self.fixture["valid_packet"])
        packet["upload_enabled"] = True
        with self.assertRaises(ValueError):
            require_release_consumer_handoff_packet(packet)


if __name__ == "__main__":
    unittest.main()
