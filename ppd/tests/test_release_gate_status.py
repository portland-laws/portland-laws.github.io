from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ppd.release_gate_status import (
    REQUIRED_PACKET_TYPE,
    assert_valid_release_gate_status_packet,
    load_release_gate_status_packet,
    validate_release_gate_status_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "release_gate_status" / "status_packet.json"


def _fixture() -> dict[str, object]:
    return load_release_gate_status_packet(FIXTURE_PATH)


def _errors(packet: dict[str, object]) -> tuple[str, ...]:
    return validate_release_gate_status_packet(packet).errors


def test_release_gate_status_fixture_is_valid() -> None:
    packet = _fixture()
    result = validate_release_gate_status_packet(packet)

    assert packet["packet_type"] == REQUIRED_PACKET_TYPE
    assert result.ok is True
    assert result.errors == ()
    assert_valid_release_gate_status_packet(packet)


def test_release_gate_status_does_not_promote_production_readiness() -> None:
    packet = _fixture()
    packet["release_status"] = "production-ready"
    packet["production_readiness"] = True

    errors = _errors(packet)

    assert "release_status must not promote production readiness" in errors
    assert "release_status cannot be production-ready while unresolved blockers remain" in errors
    assert "production_readiness must be false" in errors


def test_release_gate_status_requires_prerequisite_links_for_each_area() -> None:
    packet = _fixture()
    packet["prerequisite_packet_links"] = []

    assert "prerequisite_packet_links must include links for every required rehearsal area" in _errors(packet)

    packet = _fixture()
    links = packet["prerequisite_packet_links"]
    assert isinstance(links, list)
    packet["prerequisite_packet_links"] = links[:1]

    errors = _errors(packet)

    assert "prerequisite_packet_links must include agent_api_conformance" in errors
    assert "prerequisite_packet_links must include devhub_pilot_result_intake_readiness" in errors
    assert "prerequisite_packet_links must include guardrail_activation_rehearsal" in errors


def test_release_gate_status_requires_all_four_rehearsal_areas() -> None:
    packet = _fixture()
    rehearsals = packet["source_rehearsals"]
    assert isinstance(rehearsals, dict)
    rehearsals.pop("agent_api_conformance")

    assert "source_rehearsals.agent_api_conformance is required" in _errors(packet)


def test_release_gate_status_requires_open_blockers_for_each_area() -> None:
    packet = _fixture()
    blockers = packet["open_blockers"]
    assert isinstance(blockers, list)
    packet["open_blockers"] = blockers[:1]

    errors = _errors(packet)

    assert "open_blockers must include blocker for agent_api_conformance" in errors
    assert "open_blockers must include blocker for devhub_pilot_result_intake_readiness" in errors
    assert "open_blockers must include blocker for guardrail_activation_rehearsal" in errors


def test_release_gate_status_rejects_enabled_live_capability() -> None:
    packet = _fixture()
    capabilities = packet["disabled_live_capabilities"]
    assert isinstance(capabilities, list)
    first = capabilities[0]
    assert isinstance(first, dict)
    first["enabled"] = True

    errors = _errors(packet)

    assert "disabled_live_capabilities[0].enabled must be false" in errors
    assert "packet.disabled_live_capabilities[0].enabled must not enable live or consequential capability" in errors


def test_release_gate_status_rejects_enabled_live_crawl_or_devhub_flags() -> None:
    packet = _fixture()
    packet["live_crawl_enabled"] = True
    packet["devhub_capabilities_enabled"] = True

    errors = _errors(packet)

    assert "packet.live_crawl_enabled must not enable live or consequential capability" in errors
    assert "packet.devhub_capabilities_enabled must not enable live or consequential capability" in errors


def test_release_gate_status_rejects_forbidden_action_enablement() -> None:
    packet = _fixture()
    packet["release_actions"] = {
        "payment_enabled": True,
        "upload_enabled": True,
        "submission_enabled": True,
        "scheduling_enabled": True,
        "cancellation_enabled": True,
        "certification_enabled": True,
    }

    errors = _errors(packet)

    assert "packet.release_actions.payment_enabled must not enable live or consequential capability" in errors
    assert "packet.release_actions.upload_enabled must not enable live or consequential capability" in errors
    assert "packet.release_actions.submission_enabled must not enable live or consequential capability" in errors
    assert "packet.release_actions.scheduling_enabled must not enable live or consequential capability" in errors
    assert "packet.release_actions.cancellation_enabled must not enable live or consequential capability" in errors
    assert "packet.release_actions.certification_enabled must not enable live or consequential capability" in errors


def test_release_gate_status_rejects_non_metadata_next_step() -> None:
    packet = _fixture()
    steps = packet["allowed_metadata_only_next_steps"]
    assert isinstance(steps, list)
    first = steps[0]
    assert isinstance(first, dict)
    first["action_scope"] = "live_crawl"
    first["live_capability_enabled"] = True

    errors = _errors(packet)

    assert "allowed_metadata_only_next_steps[0].action_scope must be metadata_only" in errors
    assert "allowed_metadata_only_next_steps[0].live_capability_enabled must be false" in errors


def test_release_gate_status_requires_cited_readiness_claims() -> None:
    packet = _fixture()
    capabilities = packet["disabled_live_capabilities"]
    assert isinstance(capabilities, list)
    first = capabilities[0]
    assert isinstance(first, dict)
    first["evidence_ids"] = []

    errors = _errors(packet)

    assert "disabled_live_capabilities[0].evidence_ids must be non-empty" in errors
    assert "packet.disabled_live_capabilities[0] contains uncited readiness claim" in errors


def test_release_gate_status_requires_cited_reviewer_prompts() -> None:
    packet = _fixture()
    prompts = packet["required_reviewer_prompts"]
    assert isinstance(prompts, list)
    first = prompts[0]
    assert isinstance(first, dict)
    first["evidence_ids"] = []

    errors = _errors(packet)

    assert "required_reviewer_prompts[0].evidence_ids must be non-empty" in errors
    assert "packet.required_reviewer_prompts[0] contains uncited readiness claim" in errors


@pytest.mark.parametrize("forbidden_key", ["auth_state", "screenshot_path", "raw_html", "private_field_value"])
def test_release_gate_status_rejects_private_or_raw_artifact_keys(forbidden_key: str) -> None:
    packet = deepcopy(_fixture())
    packet[forbidden_key] = "redacted-but-not-allowed"

    assert any(forbidden_key in error for error in _errors(packet))


def test_release_gate_status_rejects_raw_crawl_output_references() -> None:
    packet = _fixture()
    packet["candidate_artifact"] = {
        "summary": "Review raw crawl output before promotion.",
        "evidence_ids": ["ev-source-registry-fixture"],
    }

    assert any("raw crawl output" in error for error in _errors(packet))
