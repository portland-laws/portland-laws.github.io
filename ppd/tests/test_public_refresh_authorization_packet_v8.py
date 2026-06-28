from __future__ import annotations

import copy
from pathlib import Path

import pytest

from ppd.agent_readiness.public_refresh_authorization_packet_v8 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    VALIDATION_COMMANDS,
    assert_valid_public_refresh_authorization_packet_v8,
    build_public_refresh_authorization_packet_v8_from_fixture,
    validate_public_refresh_authorization_packet_v8,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_refresh_authorization_packet_v8" / "source_fixture.json"


def _packet() -> dict:
    return build_public_refresh_authorization_packet_v8_from_fixture(FIXTURE_PATH)


def test_public_refresh_authorization_packet_v8_is_fixture_first() -> None:
    packet = _packet()

    assert packet["packet_type"] == "ppd.public_refresh_authorization_packet.v8"
    assert packet["packet_version"] == "v8"
    assert packet["mode"] == "fixture_first_public_refresh_authorization_packet_v8"
    assert packet["consumes_only"] == {
        "public_freshness_watchlist_handoff_v7_fixtures": True,
        "agent_api_compatibility_matrix_v7_fixtures": True,
        "current_source_registry_fixtures": True,
    }
    assert packet["boundaries"]["live_crawl_executed"] is False
    assert packet["boundaries"]["raw_artifacts_downloaded"] is False
    assert packet["boundaries"]["devhub_opened"] is False
    assert packet["boundaries"]["legal_or_permitting_guarantees_made"] is False
    assert packet["exact_offline_validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS
    assert packet["validation_commands"] == VALIDATION_COMMANDS
    assert validate_public_refresh_authorization_packet_v8(packet).valid is True


def test_public_refresh_authorization_packet_v8_assembles_reviewer_rows_and_preflights() -> None:
    packet = _packet()
    reviewer_rows = {row["source_id"]: row for row in packet["reviewer_authorization_rows"]}
    allowlist_rows = {row["source_id"]: row for row in packet["allowlist_and_robots_preflight_requirements"]}
    no_raw_body_rows = {row["source_id"]: row for row in packet["no_raw_body_persistence_requirements"]}
    hold_rows = {row["source_id"]: row for row in packet["source_freshness_hold_conditions"]}
    rollback_rows = {row["source_id"]: row for row in packet["rollback_references"]}

    assert set(reviewer_rows) == {"portland_maps_public_permits", "portland_permitting_public_forms"}
    assert set(packet["authorized_source_ids"]) == set(reviewer_rows)
    for source_id, row in reviewer_rows.items():
        assert row["authorization_decision"] == "hold_pending_reviewer_authorization"
        assert row["go_allowed"] is False
        assert row["reviewer_required"] is True
        assert row["watchlist_reference"] == f"public_freshness_watchlist_handoff_v7::{source_id}"
        assert row["compatibility_reference"] == f"agent_api_compatibility_matrix_v7::{source_id}"
        assert row["source_registry_reference"] == f"current_source_registry_v7::{source_id}"
        assert "live_crawl" in row["prohibited_actions"]
        assert allowlist_rows[source_id]["allowlist_required"] is True
        assert allowlist_rows[source_id]["robots_preflight_required"] is True
        assert allowlist_rows[source_id]["live_fetch_authorized_by_this_packet"] is False
        assert no_raw_body_rows[source_id]["no_raw_body_persisted_required"] is True
        assert hold_rows[source_id]["must_hold_currentness_claims"] is True
        assert hold_rows[source_id]["must_hold_legal_or_permitting_guarantees"] is True
        assert hold_rows[source_id]["cleared_by_this_packet"] is False
        assert rollback_rows[source_id]["rollback_reference"].startswith("rollback://ppd/public-fixtures/")
        assert rollback_rows[source_id]["active_registry_mutation"] is False


def test_public_refresh_authorization_packet_v8_rejects_missing_source_fixture_refs() -> None:
    packet = _packet()
    packet["source_fixture_refs"] = [
        ref for ref in packet["source_fixture_refs"] if ref["fixture_role"] != "agent_api_compatibility_matrix_v7"
    ]

    result = validate_public_refresh_authorization_packet_v8(packet)

    assert result.valid is False
    assert any("source_fixture_refs must include agent_api_compatibility_matrix_v7" in problem for problem in result.problems)


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("reviewer_authorization_rows", "reviewer_authorization_rows must cover every authorized_source_id"),
        ("allowlist_and_robots_preflight_requirements", "allowlist_and_robots_preflight_requirements must cover every authorized_source_id"),
        ("no_raw_body_persistence_requirements", "no_raw_body_persistence_requirements must cover every authorized_source_id"),
        ("source_freshness_hold_conditions", "source_freshness_hold_conditions must cover every authorized_source_id"),
        ("rollback_references", "rollback_references must cover every authorized_source_id"),
    ],
)
def test_public_refresh_authorization_packet_v8_rejects_missing_required_rows(field: str, expected: str) -> None:
    packet = _packet()
    packet[field] = packet[field][:-1]

    result = validate_public_refresh_authorization_packet_v8(packet)

    assert result.valid is False
    assert any(expected in problem for problem in result.problems)


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("watchlist_reference", "watchlist references"),
        ("compatibility_reference", "compatibility references"),
        ("source_registry_reference", "source registry references"),
        ("rollback_reference", "rollback references"),
    ],
)
def test_public_refresh_authorization_packet_v8_rejects_missing_reviewer_references(field: str, expected: str) -> None:
    packet = _packet()
    packet["reviewer_authorization_rows"][0][field] = ""

    result = validate_public_refresh_authorization_packet_v8(packet)

    assert result.valid is False
    assert any(expected in problem for problem in result.problems)


def test_public_refresh_authorization_packet_v8_rejects_missing_allowlist_or_robots_preflight() -> None:
    packet = _packet()
    packet["allowlist_and_robots_preflight_requirements"][0]["allowlist_required"] = False
    packet["allowlist_and_robots_preflight_requirements"][1]["robots_preflight_required"] = False

    result = validate_public_refresh_authorization_packet_v8(packet)

    assert result.valid is False
    assert any("allowlist and robots preflight requirements must be true" in problem for problem in result.problems)


def test_public_refresh_authorization_packet_v8_rejects_missing_no_raw_body_requirement() -> None:
    packet = _packet()
    packet["no_raw_body_persistence_requirements"][0]["no_raw_body_persisted_required"] = False

    result = validate_public_refresh_authorization_packet_v8(packet)

    assert result.valid is False
    assert any("no raw body persistence must be required" in problem for problem in result.problems)


def test_public_refresh_authorization_packet_v8_rejects_missing_freshness_hold_condition() -> None:
    packet = _packet()
    packet["source_freshness_hold_conditions"][0]["hold_condition"] = ""
    packet["source_freshness_hold_conditions"][0]["must_hold_currentness_claims"] = False

    result = validate_public_refresh_authorization_packet_v8(packet)

    assert result.valid is False
    assert any("source freshness hold rows must include hold conditions" in problem for problem in result.problems)
    assert any("source freshness hold rows must hold currentness claims" in problem for problem in result.problems)


def test_public_refresh_authorization_packet_v8_rejects_missing_validation_commands() -> None:
    packet = _packet()
    packet["validation_commands"] = []

    result = validate_public_refresh_authorization_packet_v8(packet)

    assert result.valid is False
    assert any("validation_commands must contain only" in problem for problem in result.problems)


def test_public_refresh_authorization_packet_v8_rejects_forbidden_execution_claims() -> None:
    packet = _packet()
    packet["boundaries"]["live_crawl_executed"] = True

    result = validate_public_refresh_authorization_packet_v8(packet)

    assert result.valid is False
    assert any("boundaries must deny live crawl" in problem for problem in result.problems)
    assert any("forbidden true value" in problem for problem in result.problems)
    with pytest.raises(ValueError):
        assert_valid_public_refresh_authorization_packet_v8(packet)


def test_public_refresh_authorization_packet_v8_rejects_downloaded_raw_private_and_auth_artifacts() -> None:
    packet = _packet()
    packet["reviewer_authorization_rows"][0]["downloaded_artifact_path"] = "downloads/body.pdf"
    packet["reviewer_authorization_rows"][0]["raw_crawl_artifact_ref"] = "raw://body"
    packet["reviewer_authorization_rows"][0]["private_session_token"] = "secret"
    packet["reviewer_authorization_rows"][0]["auth_state_path"] = "state.json"

    result = validate_public_refresh_authorization_packet_v8(packet)

    assert result.valid is False
    assert sum("forbidden artifact or private payload" in problem for problem in result.problems) >= 4


def test_public_refresh_authorization_packet_v8_rejects_official_action_guarantee_and_mutation_claims() -> None:
    packet = _packet()
    packet["official_action_completed"] = True
    packet["legal_or_permitting_guarantee"] = "permit will be approved"
    packet["rollback_references"][0]["active_registry_mutation"] = True

    result = validate_public_refresh_authorization_packet_v8(packet)

    assert result.valid is False
    assert any("forbidden true value at packet.official_action_completed" in problem for problem in result.problems)
    assert any("rollback rows must keep active registry mutation false" in problem for problem in result.problems)


def test_public_refresh_authorization_packet_v8_validation_does_not_mutate_packet() -> None:
    packet = _packet()
    before = copy.deepcopy(packet)

    validate_public_refresh_authorization_packet_v8(packet)

    assert packet == before
