from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from ppd.user_gap_analysis_packet_v6 import (
    assemble_from_fixture_paths,
    validate_user_gap_analysis_packet_v6,
)

FIXTURES = Path(__file__).parent / "fixtures" / "user_gap_analysis_packet_v6"


def _packet() -> dict[str, Any]:
    return assemble_from_fixture_paths(
        FIXTURES / "agent_guardrail_api_compatibility_packet_v6.json",
        FIXTURES / "guarded_draft_preview_handoff_packet_v6.json",
        FIXTURES / "local_pdf_draft_preview_packet_v6.json",
    )


def _issues(packet: dict[str, Any]) -> str:
    return "\n".join(validate_user_gap_analysis_packet_v6(packet))


def test_user_gap_analysis_packet_v6_uses_only_allowed_fixture_packets() -> None:
    packet = _packet()

    assert packet["packet_type"] == "fixture_first_user_gap_analysis_packet_v6"
    assert packet["source_packet_types"] == [
        "agent_guardrail_api_compatibility_packet_v6",
        "guarded_draft_preview_handoff_packet_v6",
        "local_pdf_draft_preview_packet_v6",
    ]
    assert packet["scope"] == {
        "fixture_first": True,
        "private_documents_read": False,
        "devhub_opened": False,
        "uploads_or_submissions_performed": False,
        "payments_or_scheduling_performed": False,
        "legal_or_permitting_guarantees": False,
    }
    assert validate_user_gap_analysis_packet_v6(packet) == []


def test_user_gap_analysis_packet_v6_has_gap_rows_and_safe_actions() -> None:
    packet = _packet()

    assert [row["fact_id"] for row in packet["synthetic_case_fact_inventory"]] == [
        "site_address",
        "project_scope",
    ]
    assert {row["fact_id"] for row in packet["missing_fact_rows"]} == {
        "contractor_license_number",
        "owner_signature_date",
    }
    assert packet["missing_document_labels"] == [
        "site plan with dimensions",
        "fixture-only draft preview attachment label",
    ]
    assert packet["stale_or_conflicting_evidence_rows"] == [
        {
            "evidence_id": "ev-001",
            "issue": "scope text differs between guarded draft and local PDF preview",
            "safe_resolution": "ask user to choose intended wording before any external action",
        }
    ]
    assert {row["action"] for row in packet["blocked_action_rows"]} == {
        "read_private_documents",
        "open_devhub",
        "upload",
        "submit",
        "certify",
        "pay",
        "schedule",
        "legal_or_permitting_guarantee",
    }
    assert packet["next_safe_reversible_actions"] == [
        "review_synthetic_case_fact_inventory",
        "fill_missing_fact_rows_from_user_memory",
        "label_missing_documents_without_uploading",
        "compare_fixture_citation_payloads",
        "prepare_manual_handoff_notes",
        "run_offline_validation_commands",
    ]
    assert packet["offline_validation_commands"] == [
        ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
        ["python3", "-m", "pytest", "ppd/tests/test_user_gap_analysis_packet_v6.py"],
    ]


@pytest.mark.parametrize(
    ("missing_source", "expected"),
    [
        ("agent_guardrail_api_compatibility_packet_v6", "agent_guardrail_api_compatibility_packet_v6"),
        ("guarded_draft_preview_handoff_packet_v6", "guarded_draft_preview_handoff_packet_v6"),
        ("local_pdf_draft_preview_packet_v6", "local_pdf_draft_preview_packet_v6"),
    ],
)
def test_validation_rejects_missing_required_source_references(missing_source: str, expected: str) -> None:
    packet = _packet()
    packet["source_packet_types"] = [
        source for source in packet["source_packet_types"] if source != missing_source
    ]

    assert expected in _issues(packet)


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("synthetic_case_fact_inventory", "synthetic case fact inventories"),
        ("missing_fact_rows", "missing-fact rows"),
        ("missing_document_labels", "missing-document rows"),
        ("stale_or_conflicting_evidence_rows", "stale or conflicting evidence rows"),
        ("blocked_action_rows", "blocked action rows"),
        ("next_safe_reversible_actions", "reversible next-safe-action rows"),
        ("citation_payloads", "citation payloads"),
        ("manual_handoff_notes", "manual handoff notes"),
        ("offline_validation_commands", "validation commands"),
    ],
)
def test_validation_rejects_missing_required_packet_sections(field: str, expected: str) -> None:
    packet = _packet()
    packet[field] = []

    assert expected in _issues(packet)


def test_validation_rejects_missing_blocked_action_row() -> None:
    packet = _packet()
    packet["blocked_action_rows"] = [
        row for row in packet["blocked_action_rows"] if row["action"] != "submit"
    ]

    assert "blocked action row missing: submit" in _issues(packet)


def test_validation_rejects_missing_reversible_next_safe_action_row() -> None:
    packet = _packet()
    packet["next_safe_reversible_actions"] = [
        action for action in packet["next_safe_reversible_actions"] if action != "prepare_manual_handoff_notes"
    ]

    assert "reversible next-safe-action row missing: prepare_manual_handoff_notes" in _issues(packet)


@pytest.mark.parametrize(
    ("patch", "expected"),
    [
        ({"private_document_values": {"field": "secret"}}, "private document values"),
        ({"claim": "live DevHub access completed for this packet"}, "live DevHub access claims"),
        ({"claim": "submitted permit request in the official portal"}, "official-action completion claims"),
        ({"claim": "guarantee permit approval after this review"}, "legal or permitting guarantees"),
        ({"active_mutation": True}, "active mutation flags"),
        ({"claim": "active mutation enabled for release"}, "active mutation claims"),
    ],
)
def test_validation_rejects_forbidden_values_and_claims(patch: dict[str, Any], expected: str) -> None:
    packet = deepcopy(_packet())
    packet.update(patch)

    assert expected in _issues(packet)


def test_validation_rejects_private_live_or_mutating_scope_flags() -> None:
    packet = _packet()
    packet["scope"] = dict(packet["scope"])
    packet["scope"]["private_documents_read"] = True
    packet["scope"]["devhub_opened"] = True
    packet["scope"]["uploads_or_submissions_performed"] = True
    packet["scope"]["legal_or_permitting_guarantees"] = True

    issues = _issues(packet)
    assert "scope.private_documents_read must be False" in issues
    assert "scope.devhub_opened must be False" in issues
    assert "scope.uploads_or_submissions_performed must be False" in issues
    assert "scope.legal_or_permitting_guarantees must be False" in issues
