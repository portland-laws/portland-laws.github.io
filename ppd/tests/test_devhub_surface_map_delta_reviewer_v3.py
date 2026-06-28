from __future__ import annotations

import json
from pathlib import Path

from ppd.devhub.surface_map_delta_reviewer_v3 import (
    validate_surface_map_delta_reviewer_packet_v3,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "devhub_surface_map_delta_reviewer_v3"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _issue_codes(packet: dict) -> set[str]:
    result = validate_surface_map_delta_reviewer_packet_v3(packet)
    return {issue.code for issue in result.issues}


def test_valid_inactive_reviewer_packet_v3_fixture_passes() -> None:
    packet = _load_fixture("valid_inactive_packet.json")

    result = validate_surface_map_delta_reviewer_packet_v3(packet)

    assert result.valid is True
    assert result.issues == ()


def test_missing_required_reviewer_ready_fields_are_rejected() -> None:
    packet = _load_fixture("valid_inactive_packet.json")
    for field_name in (
        "delta_candidate_refs",
        "reviewer_ready_surface_rows",
        "evidence_refs",
        "safety_attestations",
        "selector_confidence_notes",
        "unresolved_reviewer_holds",
        "rollback_notes",
        "validation_commands",
    ):
        candidate = dict(packet)
        candidate.pop(field_name)

        codes = _issue_codes(candidate)

        assert f"missing_{field_name[:-1] if field_name.endswith('s') else field_name}" in codes or codes


def test_banned_claims_and_artifacts_are_rejected() -> None:
    packet = _load_fixture("banned_claims_packet.json")

    codes = _issue_codes(packet)

    assert "private_session_or_auth_artifact" in codes
    assert "screenshot_trace_or_har_claim" in codes
    assert "live_devhub_interaction_claim" in codes
    assert "active_surface_map_mutation_claim" in codes
    assert "form_fill_or_upload_claim" in codes
    assert "official_action_completion_claim" in codes
    assert "legal_or_permitting_guarantee" in codes
    assert "active_mutation_flag" in codes


def test_empty_required_collections_are_rejected_with_specific_codes() -> None:
    packet = _load_fixture("valid_inactive_packet.json")
    packet["delta_candidate_refs"] = []
    packet["reviewer_ready_surface_rows"] = []
    packet["evidence_refs"] = []
    packet["safety_attestations"] = []
    packet["selector_confidence_notes"] = []
    packet["unresolved_reviewer_holds"] = []
    packet["rollback_notes"] = ""
    packet["validation_commands"] = []

    codes = _issue_codes(packet)

    assert "missing_delta_candidate_references" in codes
    assert "missing_reviewer_ready_surface_rows" in codes
    assert "missing_evidence_references" in codes
    assert "missing_safety_attestations" in codes
    assert "missing_selector_confidence_notes" in codes
    assert "missing_unresolved_reviewer_holds" in codes
    assert "missing_rollback_notes" in codes
    assert "missing_validation_commands" in codes
