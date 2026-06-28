"""Regression tests for agent-facing PP&D readiness contract packets."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

from ppd.agent_readiness.contract_packet_validation import (
    validate_agent_facing_readiness_contract_packet,
)


_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "agent_readiness" / "contract_packet_validation_cases.json"
_NOW = datetime(2026, 5, 28, tzinfo=timezone.utc)


class AgentReadinessContractPacketValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_valid_packet_is_ready(self) -> None:
        result = validate_agent_facing_readiness_contract_packet(
            self.fixture["valid_packet"],
            now=_NOW,
        )

        self.assertTrue(result.ready, result.problems)
        self.assertEqual((), result.problems)

    def test_invalid_contract_packets_are_rejected_with_targeted_problem(self) -> None:
        base_packet = self.fixture["valid_packet"]

        for case in self.fixture["invalid_packets"]:
            with self.subTest(case=case["name"]):
                packet = deepcopy(base_packet)
                self._deep_update(packet, case["patch"])

                result = validate_agent_facing_readiness_contract_packet(packet, now=_NOW)

                self.assertFalse(result.ready)
                joined = "\n".join(result.problems)
                self.assertIn(case["expected_problem"], joined)

    def _deep_update(self, target: dict[str, object], patch: dict[str, object]) -> None:
        for key, value in patch.items():
            existing = target.get(key)
            if isinstance(existing, dict) and isinstance(value, dict):
                self._deep_update(existing, value)
            else:
                target[key] = value


if __name__ == "__main__":
    unittest.main()
