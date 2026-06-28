from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.agent_readiness.public_refresh_post_decision_smoke_replay_packet_v1 import (
    REQUIRED_SCENARIO_FIELDS,
    assert_valid_public_refresh_post_decision_smoke_replay_packet_v1,
    validate_public_refresh_post_decision_smoke_replay_packet_v1,
)


FIXTURE = Path(__file__).parent / "fixtures" / "public_refresh_post_decision_smoke_replay_packet_v1" / "valid_packet.json"


def load_valid_packet() -> dict:
    with FIXTURE.open(encoding="utf-8") as packet_file:
        return json.load(packet_file)


def error_codes(packet: dict) -> set[str]:
    return {issue.code for issue in validate_public_refresh_post_decision_smoke_replay_packet_v1(packet)}


def test_valid_fixture_passes() -> None:
    assert_valid_public_refresh_post_decision_smoke_replay_packet_v1(load_valid_packet())


@pytest.mark.parametrize("field,code", REQUIRED_SCENARIO_FIELDS.items())
def test_rejects_missing_required_scenario_sections(field: str, code: str) -> None:
    packet = load_valid_packet()
    packet = copy.deepcopy(packet)
    packet["smoke_scenarios"][0].pop(field)

    assert code in error_codes(packet)


def test_rejects_missing_validation_commands() -> None:
    packet = load_valid_packet()
    packet.pop("validation_commands")

    assert "missing_validation_commands" in error_codes(packet)


@pytest.mark.parametrize(
    "field_name",
    [
        "private_artifact",
        "raw_crawl_output",
        "raw_download",
        "downloaded_artifact",
        "downloaded_document",
        "session_state",
        "browser_trace",
    ],
)
def test_rejects_private_raw_downloaded_and_session_artifact_keys(field_name: str) -> None:
    packet = load_valid_packet()
    packet[field_name] = "artifact reference is not allowed"

    assert "private_raw_or_downloaded_artifact_reference" in error_codes(packet)


@pytest.mark.parametrize(
    "claim",
    [
        "The live crawl completed for this replay.",
        "Live extraction completed for the public source.",
    ],
)
def test_rejects_live_extraction_or_crawl_claims(claim: str) -> None:
    packet = load_valid_packet()
    packet["notes"] = claim

    assert "live_extraction_or_crawl_claim" in error_codes(packet)


@pytest.mark.parametrize(
    "claim",
    [
        "DevHub was opened to confirm the smoke replay.",
        "The authenticated session observed DevHub during validation.",
    ],
)
def test_rejects_devhub_claims(claim: str) -> None:
    packet = load_valid_packet()
    packet["notes"] = claim

    assert "devhub_claim" in error_codes(packet)


def test_rejects_release_activation_claims() -> None:
    packet = load_valid_packet()
    packet["notes"] = "The release was activated after the replay."

    assert "release_activation_claim" in error_codes(packet)


def test_rejects_active_artifact_mutation_claims() -> None:
    packet = load_valid_packet()
    packet["active_artifact_mutation"] = True

    assert "active_mutation_flag" in error_codes(packet)


@pytest.mark.parametrize(
    "field_name",
    [
        "active_guardrail_mutation",
        "active_prompt_mutation",
        "release_promotion_enabled",
        "surface_registry_write_enabled",
    ],
)
def test_rejects_active_mutation_flags(field_name: str) -> None:
    packet = load_valid_packet()
    packet[field_name] = True

    assert "active_mutation_flag" in error_codes(packet)


def test_rejects_official_action_completion_claims() -> None:
    packet = load_valid_packet()
    packet["notes"] = "Official action completed during this replay."

    assert "official_action_completion_claim" in error_codes(packet)


@pytest.mark.parametrize(
    "claim",
    [
        "Permit approval guaranteed by the replay packet.",
        "This packet is a legal guarantee for the applicant.",
    ],
)
def test_rejects_legal_or_permitting_guarantees(claim: str) -> None:
    packet = load_valid_packet()
    packet["notes"] = claim

    assert "legal_or_permitting_guarantee" in error_codes(packet)
