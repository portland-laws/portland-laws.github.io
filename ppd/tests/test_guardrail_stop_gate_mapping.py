"""Fixture-only validation for process stop gate to agent action gate mappings."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "guardrails" / "stop_gate_action_gate_mapping.json"
ALLOWED_ACTION_CLASSES = {"safe_read_only", "reversible_draft_edit"}


class GuardrailStopGateMappingFixtureTest(unittest.TestCase):
    def test_maps_one_process_stop_gate_to_agent_action_gate(self) -> None:
        fixture = _load_fixture()
        mapping = fixture["mappings"][0]

        process_stop_gate = mapping["processStopGate"]
        agent_action_gate = mapping["agentActionGate"]

        self.assertEqual(
            process_stop_gate["stopGateId"],
            agent_action_gate["mappedFromStopGateId"],
        )
        self.assertIn(agent_action_gate["actionClass"], ALLOWED_ACTION_CLASSES)
        self.assertTrue(agent_action_gate["consequenceSummary"].strip())
        self.assertEqual(
            process_stop_gate["sourceEvidenceIds"],
            agent_action_gate["sourceEvidenceIds"],
        )
        self.assertTrue(agent_action_gate["sourceEvidenceIds"])
        self.assertTrue(all(str(evidence_id).strip() for evidence_id in agent_action_gate["sourceEvidenceIds"]))


def _load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        fixture = json.load(fixture_file)
    if not isinstance(fixture, dict):
        raise AssertionError("guardrail mapping fixture must be a JSON object")
    return fixture


if __name__ == "__main__":
    unittest.main()
