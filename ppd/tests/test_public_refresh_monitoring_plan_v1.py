from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.agent_readiness.public_refresh_monitoring_plan_v1 import (
    require_public_refresh_monitoring_plan_v1,
    validate_public_refresh_monitoring_plan_v1,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "agent_readiness"
VALID_PACKET_PATH = FIXTURE_DIR / "public_refresh_monitoring_plan_v1_valid.json"
REJECTION_CASES_PATH = FIXTURE_DIR / "public_refresh_monitoring_plan_v1_rejection_cases.json"


def _valid_packet() -> dict:
    return json.loads(VALID_PACKET_PATH.read_text(encoding="utf-8"))


def test_public_refresh_monitoring_plan_v1_accepts_valid_fixture() -> None:
    packet = _valid_packet()

    result = validate_public_refresh_monitoring_plan_v1(packet)

    assert result.ready, result.problems
    require_public_refresh_monitoring_plan_v1(packet)


def test_public_refresh_monitoring_plan_v1_rejects_required_failure_cases() -> None:
    cases = json.loads(REJECTION_CASES_PATH.read_text(encoding="utf-8"))
    assert cases
    for case in cases:
        packet = _valid_packet()
        _deep_update(packet, case["patch"])

        result = validate_public_refresh_monitoring_plan_v1(packet)

        assert not result.ready, case["case_id"]
        assert any(case["expected_problem"] in problem for problem in result.problems), (case["case_id"], result.problems)


def test_public_refresh_monitoring_plan_v1_rejects_removed_required_coverage() -> None:
    required = {
        "official_anchor_coverage": "official anchors coverage",
        "file_preparation_or_fee_payment_guidance_coverage": "file preparation or fee/payment guidance coverage",
        "devhub_public_guidance_coverage": "DevHub public guidance coverage",
        "forms_index_coverage": "forms index coverage",
        "linked_portland_maps_coverage": "linked Portland Maps guidance coverage",
    }
    for key, expected in required.items():
        packet = _valid_packet()
        packet["coverage"][key] = False
        packet["normalized_source_evidence"] = [
            item
            for item in packet["normalized_source_evidence"]
            if key not in item.get("coverage_tags", [])
        ]

        result = validate_public_refresh_monitoring_plan_v1(packet)

        assert not result.ready, key
        assert any(expected in problem for problem in result.problems), result.problems


def _deep_update(target: dict, patch: dict) -> None:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = copy.deepcopy(value)
