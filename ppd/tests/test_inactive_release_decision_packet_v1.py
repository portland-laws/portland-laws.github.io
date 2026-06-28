from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from ppd.inactive_release_decision_packet_v1 import (
    assert_valid_inactive_release_decision_packet_v1,
    validate_inactive_release_decision_packet_v1,
)

FIXTURES = Path(__file__).parent / "fixtures" / "inactive_release_decision_packet_v1"


def _valid_packet() -> dict[str, Any]:
    data = json.loads((FIXTURES / "valid_packet.json").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _codes(packet: dict[str, Any]) -> set[str]:
    return {issue["code"] for issue in validate_inactive_release_decision_packet_v1(packet)}


def test_accepts_complete_inactive_release_decision_packet_v1() -> None:
    packet = _valid_packet()

    assert validate_inactive_release_decision_packet_v1(packet) == []
    assert_valid_inactive_release_decision_packet_v1(packet)


@pytest.mark.parametrize(
    ("field", "code"),
    [
        ("promotion_candidate_references", "missing_promotion_candidate_references"),
        ("readiness_replay_references", "missing_readiness_replay_references"),
        ("dependency_ordering", "missing_dependency_ordering"),
        ("human_reviewer_routing", "missing_human_reviewer_routing"),
        ("release_blocker_summaries", "missing_release_blocker_summaries"),
        ("smoke_replay_requirements", "missing_smoke_replay_requirements"),
        ("rollback_notes", "missing_rollback_notes"),
        ("validation_commands", "missing_validation_commands"),
    ],
)
def test_rejects_missing_required_release_review_sections(field: str, code: str) -> None:
    packet = _valid_packet()
    packet.pop(field)

    assert code in _codes(packet)


@pytest.mark.parametrize(
    ("decision", "code"),
    [
        ("approve", "missing_approve_decision"),
        ("hold", "missing_hold_decision"),
        ("reject", "missing_reject_decision"),
    ],
)
def test_rejects_missing_required_approve_hold_reject_decisions(decision: str, code: str) -> None:
    packet = _valid_packet()
    packet["release_decisions"] = [
        row for row in packet["release_decisions"] if isinstance(row, dict) and row.get("decision") != decision
    ]

    assert code in _codes(packet)


@pytest.mark.parametrize(
    ("mutator", "code"),
    [
        (lambda packet: packet.update({"downloaded_document_path": "/tmp/private/raw.pdf"}), "private_or_raw_artifact"),
        (lambda packet: packet["rollback_notes"][0].update({"operator_note": "live crawl completed"}), "live_crawl_or_devhub_claim"),
        (lambda packet: packet["rollback_notes"][0].update({"operator_note": "DevHub was accessed"}), "live_crawl_or_devhub_claim"),
        (lambda packet: packet["rollback_notes"][0].update({"operator_note": "release was promoted"}), "release_promotion_claim"),
        (lambda packet: packet["rollback_notes"][0].update({"operator_note": "official action completed"}), "official_action_completion_claim"),
        (lambda packet: packet["rollback_notes"][0].update({"operator_note": "permit will be issued"}), "legal_or_permitting_guarantee"),
        (lambda packet: packet.update({"active_release_state_mutation": True}), "active_mutation_flag"),
        (lambda packet: packet.update({"active_mutation_flags": ["release_state"]}), "active_mutation_flag"),
        (lambda packet: packet.update({"validation_commands": [["python3", "ppd/crawler/live_run.py"]]}), "unsafe_validation_command"),
    ],
)
def test_rejects_unsafe_artifacts_claims_and_mutation_flags(
    mutator: Callable[[dict[str, Any]], object], code: str
) -> None:
    packet = copy.deepcopy(_valid_packet())
    mutator(packet)

    assert code in _codes(packet)
    with pytest.raises(ValueError, match=code):
        assert_valid_inactive_release_decision_packet_v1(packet)
