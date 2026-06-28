from __future__ import annotations

import json
from pathlib import Path
from typing import Any


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "blocked_cascade_daemon_repair_tranche3_item4.json"
)


def _next_state(event: dict[str, Any], minimum_fresh_generation: int) -> str:
    repair_is_fresh = event["repair_generation"] >= minimum_fresh_generation
    repair_validated = event["repair_validated"] is True
    if repair_is_fresh and repair_validated:
        return "eligible"
    return "parked"


def test_blocked_cascade_work_stays_parked_until_fresh_daemon_repair_validates() -> None:
    scenario = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert scenario["scenario"] == "tranche3_item4_blocked_cascade_daemon_repair"
    assert scenario["blocked_task"] == "checkbox-257-dependent-work"
    assert scenario["required_repair_task"] == "daemon-repair-checkbox-257"

    observed = [
        _next_state(event, minimum_fresh_generation=2)
        for event in scenario["events"]
    ]
    expected = [event["expected_state"] for event in scenario["events"]]

    assert observed == expected
    assert observed[:-1] == ["parked", "parked", "parked"]
    assert observed[-1] == "eligible"
