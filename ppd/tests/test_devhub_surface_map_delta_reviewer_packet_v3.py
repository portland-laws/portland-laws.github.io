from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.devhub.surface_map_delta_reviewer_packet_v3 import (
    OFFLINE_VALIDATION_COMMANDS,
    build_surface_map_delta_reviewer_packet_v3,
    validate_surface_map_delta_reviewer_packet_v3,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "devhub_surface_map_delta_reviewer_packet_v3"


def _load_candidate_fixture() -> dict[str, object]:
    return json.loads((FIXTURE_DIR / "candidate_packet.json").read_text(encoding="utf-8"))


def _packet() -> dict[str, object]:
    return build_surface_map_delta_reviewer_packet_v3([_load_candidate_fixture()])


def test_builds_reviewer_ready_rows_from_committed_inactive_candidate_fixture() -> None:
    packet = _packet()

    assert packet["packet_version"] == "devhub_surface_map_delta_reviewer_packet_v3"
    assert packet["mode"] == "fixture_first_inactive_devhub_surface_map_delta_reviewer_packet_v3"
    assert packet["delta_candidate_references"][0]["candidate_packet_id"] == "fixture-inactive-surface-map-delta-candidate-v3-for-review"
    assert len(packet["reviewer_ready_surface_rows"]) == 1
    assert validate_surface_map_delta_reviewer_packet_v3(packet) == []


def test_reviewer_rows_are_read_only_inactive_fixture_rows_with_evidence() -> None:
    packet = _packet()
    row = packet["reviewer_ready_surface_rows"][0]

    assert row["read_only"] is True
    assert row["fixture_only"] is True
    assert row["inactive"] is True
    assert row["official_action_allowed"] is False
    assert row["surface_map_update_allowed"] is False
    assert row["evidence_reference_ids"]
    assert {reference["raw_private_values_stored"] for reference in packet["evidence_references"]} == {False}


def test_selector_notes_holds_rollback_and_safety_attestations_are_explicit() -> None:
    packet = _packet()

    assert packet["selector_confidence_notes"][0]["confidence"] == "medium"
    assert packet["selector_confidence_notes"][0]["live_selector_verified"] is False
    assert packet["unresolved_reviewer_holds"][0]["unresolved"] is True
    assert packet["unresolved_reviewer_holds"][0]["release_requires_human_review"] is True
    assert packet["rollback_notes"][0]["active_surface_map_unchanged"] is True
    assert packet["safety_attestations"]["committed_inactive_candidate_fixtures_only"] is True


def test_validation_requires_exact_offline_commands_only() -> None:
    packet = _packet()
    assert packet["validation_commands"] == OFFLINE_VALIDATION_COMMANDS

    mutated = copy.deepcopy(packet)
    mutated["validation_commands"] = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

    assert "validation_commands_not_exact" in validate_surface_map_delta_reviewer_packet_v3(mutated)


def test_builder_rejects_invalid_candidate_fixture() -> None:
    candidate = _load_candidate_fixture()
    candidate["read_only_surface_delta_rows"] = []

    try:
        build_surface_map_delta_reviewer_packet_v3([candidate])
    except ValueError as exc:
        assert "missing_inactive_devhub_surface_map_delta_rows" in str(exc)
    else:
        raise AssertionError("invalid candidate fixture was accepted")


def test_validation_rejects_private_artifact_live_claim_and_active_mutation_flags() -> None:
    packet = _packet()
    packet["review_notes"] = "Opened DevHub and stored screenshot for review. Permit guaranteed."
    packet["auth_state"] = "not-allowed"
    packet["reviewer_ready_surface_rows"][0]["surface_map_update_allowed"] = True

    codes = set(validate_surface_map_delta_reviewer_packet_v3(packet))

    assert "private_auth_or_browser_artifact_key" in codes
    assert "prohibited_live_private_or_official_action_claim" in codes
    assert "reviewer_ready_surface_rows_allow_prohibited_action_or_mutation" in codes
