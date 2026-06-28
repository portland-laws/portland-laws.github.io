from __future__ import annotations

import json
from pathlib import Path

from ppd.agent_prompt_update_candidate_packet import (
    REQUIRED_SOURCE_PACKET_IDS,
    build_candidate_packet,
    validate_candidate_packet,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "agent_prompt_update_candidate_packet.json"


def test_candidate_packet_fixture_is_valid() -> None:
    packet = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert validate_candidate_packet(packet) == []


def test_candidate_packet_consumes_required_source_packets() -> None:
    packet = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert set(REQUIRED_SOURCE_PACKET_IDS).issubset(set(packet["source_packet_ids"]))


def test_candidate_packet_has_cited_prompt_and_refusal_wording() -> None:
    packet = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    citation_ids = {citation["citation_id"] for citation in packet["citations"]}
    changes = packet["proposed_prompt_wording_changes"] + packet["proposed_refusal_wording_changes"]

    assert changes
    for change in changes:
        assert change["status"] == "candidate_only"
        assert change["proposed_wording"]
        assert set(change["citation_ids"]).issubset(citation_ids)


def test_candidate_packet_attests_no_live_or_mutating_actions() -> None:
    packet = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert packet["attestations"] == {
        "live_agent_invoked": False,
        "llm_consumer_invoked": False,
        "private_case_files_read": False,
        "prompt_state_mutated": False,
        "release_state_mutated": False,
    }


def test_builder_matches_committed_fixture() -> None:
    packet = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert build_candidate_packet() == packet
