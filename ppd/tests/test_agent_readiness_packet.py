from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ppd.agent_readiness import AgentReadinessPacketError, assemble_agent_readiness_packet


_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "agent_readiness" / "readiness_packet_fixture.json"
_NOW = datetime(2026, 5, 15, tzinfo=timezone.utc)


def _fixture() -> dict:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


def test_assembles_cited_metadata_only_agent_readiness_packet() -> None:
    packet = assemble_agent_readiness_packet(_fixture(), now=_NOW)

    assert packet["packet_type"] == "ppd.agent_readiness_packet.v1"
    assert packet["metadata_only"] is True
    assert packet["readiness_status"] == "manual_handoff_required"
    assert packet["case_id"] == "case-fixture-agent-readiness"
    assert packet["process_id"] == "ppd-residential-building-permit-v1"
    assert set(packet["citation_ids"]) == {
        "ev-devhub-faq",
        "ev-devhub-guide-submit",
        "ev-devhub-sign-guide",
        "ev-online-tools",
        "ev-submit-plans-online",
    }
    assert "value" not in json.dumps(packet).lower()
    assert packet["action_decision_output"]["requires_exact_confirmation"] is True
    assert packet["action_decision_output"]["requires_manual_handoff"] is True


def test_rejects_stale_source_evidence() -> None:
    fixture = _fixture()
    fixture["normalized_source_evidence"][0]["last_verified_at"] = "2026-01-01T00:00:00Z"

    with pytest.raises(AgentReadinessPacketError) as excinfo:
        assemble_agent_readiness_packet(fixture, now=_NOW)

    assert excinfo.value.code == "invalid_agent_readiness_packet"
    assert any("stale" in problem for problem in excinfo.value.problems)


def test_rejects_uncited_explanation() -> None:
    fixture = _fixture()
    fixture["action_decision_output"].pop("source_evidence_ids")
    fixture["action_decision_output"]["explanation"].pop("source_evidence_ids")

    with pytest.raises(AgentReadinessPacketError) as excinfo:
        assemble_agent_readiness_packet(fixture, now=_NOW)

    assert any("explanation field lacks source_evidence_ids" in problem for problem in excinfo.value.problems)


def test_rejects_private_values() -> None:
    fixture = _fixture()
    fixture["case_gap_report"]["known_facts"].append(
        {
            "fact_id": "site_address",
            "presence": "present",
            "value": "123 Example Private Address",
            "source_evidence_ids": ["ev-devhub-guide-submit"],
        }
    )

    with pytest.raises(AgentReadinessPacketError) as excinfo:
        assemble_agent_readiness_packet(fixture, now=_NOW)

    assert any("private value field" in problem for problem in excinfo.value.problems)


def test_rejects_consequential_action_without_handoff_or_exact_confirmation() -> None:
    fixture = _fixture()
    fixture["action_decision_output"]["requires_manual_handoff"] = False
    fixture["action_decision_output"]["requires_attendance"] = False
    fixture["action_decision_output"]["requires_exact_confirmation"] = False

    with pytest.raises(AgentReadinessPacketError) as excinfo:
        assemble_agent_readiness_packet(fixture, now=_NOW)

    assert any("manual handoff" in problem for problem in excinfo.value.problems)
    assert any("exact-confirmation" in problem for problem in excinfo.value.problems)


def test_rejects_raw_body_persistence_flags() -> None:
    fixture = deepcopy(_fixture())
    fixture["crawl_promotion_audit"]["raw_body_persisted"] = True

    with pytest.raises(AgentReadinessPacketError) as excinfo:
        assemble_agent_readiness_packet(fixture, now=_NOW)

    assert any("raw_body_persisted" in problem for problem in excinfo.value.problems)
