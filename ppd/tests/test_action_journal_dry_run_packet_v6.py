from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from ppd.action_journal_dry_run_packet_v6 import (
    CONSUMED_PACKET_TYPES,
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    REQUIRED_EVENT_TYPES,
    assemble_action_journal_dry_run_packet_v6,
    load_json,
    validate_action_journal_dry_run_packet_v6,
)
from ppd.user_gap_analysis_packet_v6 import assemble_from_fixture_paths as assemble_user_gap_packet_v6

USER_GAP_FIXTURES = Path(__file__).parent / "fixtures" / "user_gap_analysis_packet_v6"
ACTION_JOURNAL_FIXTURES = Path(__file__).parent / "fixtures" / "action_journal_dry_run_packet_v6"


def _guarded_handoff() -> dict[str, Any]:
    return load_json(USER_GAP_FIXTURES / "guarded_draft_preview_handoff_packet_v6.json")


def _user_gap_packet() -> dict[str, Any]:
    return assemble_user_gap_packet_v6(
        USER_GAP_FIXTURES / "agent_guardrail_api_compatibility_packet_v6.json",
        USER_GAP_FIXTURES / "guarded_draft_preview_handoff_packet_v6.json",
        USER_GAP_FIXTURES / "local_pdf_draft_preview_packet_v6.json",
    )


def _packet() -> dict[str, Any]:
    return assemble_action_journal_dry_run_packet_v6(_user_gap_packet(), _guarded_handoff())


def _issues(packet: dict[str, Any]) -> str:
    return "\n".join(validate_action_journal_dry_run_packet_v6(packet))


def test_action_journal_dry_run_packet_v6_matches_expected_fixture() -> None:
    expected = load_json(ACTION_JOURNAL_FIXTURES / "expected_action_journal_dry_run_packet_v6.json")

    assert _packet() == expected
    assert validate_action_journal_dry_run_packet_v6(expected) == []


def test_action_journal_dry_run_packet_v6_consumes_only_required_fixture_packets() -> None:
    packet = _packet()

    assert packet["consumes_only"] == CONSUMED_PACKET_TYPES
    assert [ref["packet_type"] for ref in packet["source_packet_refs"]] == CONSUMED_PACKET_TYPES
    assert [row["event_type"] for row in packet["event_rows"]] == REQUIRED_EVENT_TYPES
    assert all(row["source_packet_types"] == CONSUMED_PACKET_TYPES for row in packet["event_rows"])


def test_action_journal_dry_run_packet_v6_records_exact_offline_commands_only() -> None:
    packet = _packet()

    assert packet["offline_validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS
    assert all(row["offline_validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS for row in packet["event_rows"])


def test_action_journal_dry_run_packet_v6_does_not_copy_fixture_private_values() -> None:
    packet_text = str(_packet())

    assert "123 Fixture Ave" not in packet_text
    assert "Replace existing window" not in packet_text
    assert "applicant@example" not in packet_text
    assert "site_address" in packet_text
    assert "project_scope" in packet_text


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("consumes_only", "consumes_only must exactly reference"),
        ("source_packet_refs", "source_packet_refs must contain exactly two"),
        ("event_rows", "event_rows must include required v6 event types"),
        ("retention_notes", "retention_notes must be a non-empty list"),
        ("offline_validation_commands", "offline_validation_commands must exactly match"),
    ],
)
def test_validation_rejects_missing_required_sections(field: str, expected: str) -> None:
    packet = _packet()
    packet[field] = []

    assert expected in _issues(packet)


def test_validation_rejects_extra_consumed_packet_type() -> None:
    packet = _packet()
    packet["consumes_only"] = [
        "fixture_first_user_gap_analysis_packet_v6",
        "guarded_draft_preview_handoff_packet_v6",
        "local_pdf_draft_preview_packet_v6",
    ]

    assert "consumes_only must exactly reference" in _issues(packet)


@pytest.mark.parametrize(
    ("event_type", "expected"),
    [
        ("refused_action", "event_rows must include required v6 event types"),
        ("manual_handoff", "event_rows must include required v6 event types"),
        ("exact_confirmation_checkpoint", "event_rows must include required v6 event types"),
        ("completion_evidence_placeholder", "event_rows must include required v6 event types"),
    ],
)
def test_validation_rejects_missing_required_journal_rows(event_type: str, expected: str) -> None:
    packet = _packet()
    packet["event_rows"] = [row for row in packet["event_rows"] if row["event_type"] != event_type]

    assert expected in _issues(packet)


def test_validation_rejects_missing_row_evidence_and_command_drift() -> None:
    packet = _packet()
    packet["event_rows"][2]["source_evidence_ids"] = []
    packet["event_rows"][8]["offline_validation_commands"] = [["python3", "unexpected.py"]]

    issues = _issues(packet)
    assert "event_rows[2].source_evidence_ids must be a non-empty string list" in issues
    assert "event_rows[2].source_evidence_ids must include required references for refused_action" in issues
    assert "event_rows[8].offline_validation_commands must exactly match packet commands" in issues


def test_validation_rejects_missing_guarded_handoff_reference() -> None:
    packet = _packet()
    packet["source_packet_refs"][0]["source_packet_types"] = ["agent_guardrail_api_compatibility_packet_v6"]

    assert "source_packet_refs[0] must carry guarded draft preview handoff provenance" in _issues(packet)


@pytest.mark.parametrize(
    ("patch", "expected"),
    [
        ({"payment_details": "4111 1111 1111 1111"}, "prohibited sensitive key"),
        ({"claim": "opened DevHub during the journal run"}, "live DevHub claim"),
        ({"claim": "official action completed"}, "official completion claim"),
        ({"claim": "PRIVATE_FACT: unredacted field value"}, "private value"),
        ({"artifact": "review.har"}, "browser artifact"),
        ({"path_note": "/home/person/private.pdf"}, "local private path"),
        ({"legal_note": "permit approval is guaranteed"}, "legal or permitting guarantee"),
        ({"active_mutation": True}, "must not enable active mutation"),
    ],
)
def test_validation_rejects_private_live_guarantee_or_mutation_artifacts(patch: dict[str, Any], expected: str) -> None:
    packet = deepcopy(_packet())
    packet.update(patch)

    assert expected in _issues(packet)


def test_validation_rejects_true_side_effect_flags_and_missing_attestations() -> None:
    packet = _packet()
    packet["no_effect_flags"]["devhub_opened"] = True
    packet["attestations"]["no_credentials"] = False

    issues = _issues(packet)
    assert "no_effect_flags.devhub_opened must be False" in issues
    assert "attestations.no_credentials must be True" in issues
