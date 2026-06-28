from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.devhub.observation_redaction_acceptance_packet_v3 import (
    OFFLINE_VALIDATION_COMMANDS,
    ObservationRedactionAcceptancePacketV3Error,
    build_acceptance_packet_v3,
    validate_acceptance_packet_v3,
)
from ppd.devhub.read_only_observation_intake_schema_v3 import validate_observation_intake_v3

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "observation_intake_schema_v3_synthetic_rows.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_fixture_satisfies_intake_schema_v3() -> None:
    fixture = load_fixture()

    result = validate_observation_intake_v3(fixture)

    assert result.ok, [error.code for error in result.errors]


def test_builds_redaction_acceptance_packet_v3_from_synthetic_rows_only() -> None:
    packet = build_acceptance_packet_v3(load_fixture())

    assert validate_acceptance_packet_v3(packet) == []
    assert packet["devhub_access"] == "not_opened"
    assert packet["browser_artifacts"] == "not_created"
    assert packet["official_actions"] == "blocked"
    assert packet["exact_offline_validation_commands"] == OFFLINE_VALIDATION_COMMANDS
    assert {check["coverage_status"] for check in packet["redaction_coverage_checks"]} == {"covered"}
    assert all(check["stores_private_value"] is False for check in packet["redaction_coverage_checks"])


def test_packet_includes_route_selector_handoff_hold_routing_and_rollback_sections() -> None:
    packet = build_acceptance_packet_v3(load_fixture())

    assert packet["route_pattern_normalization_checks"]
    assert all("{id}" in check["normalized_route_pattern"] for check in packet["route_pattern_normalization_checks"])
    assert packet["selector_evidence_confidence_summaries"]
    assert packet["unsupported_manual_handoff_reminders"]
    assert packet["fixture_promotion_holds"]
    assert packet["reviewer_routing"]
    assert packet["rollback_notes"]


def test_rejects_private_value_columns_even_when_fixture_shape_is_otherwise_valid() -> None:
    fixture = load_fixture()
    fixture["redacted_observation_rows"][0]["actual_value"] = "synthetic private value should not be stored"

    with pytest.raises(ObservationRedactionAcceptancePacketV3Error):
        build_acceptance_packet_v3(fixture)


def test_rejects_non_synthetic_intake_source() -> None:
    fixture = copy.deepcopy(load_fixture())
    fixture["synthetic_fixture_only"] = False

    with pytest.raises(ObservationRedactionAcceptancePacketV3Error):
        build_acceptance_packet_v3(fixture)
