from __future__ import annotations

import json
from pathlib import Path

from ppd.devhub.correction_upload_boundary_packet import (
    BLOCKED_BOUNDARIES,
    SAFE_BOUNDARIES,
    validate_correction_upload_boundary_packet,
)


def _fixture_path() -> Path:
    return Path(__file__).parent / "fixtures" / "devhub" / "correction_upload_boundary_packet.json"


def _load_packet() -> dict:
    return json.loads(_fixture_path().read_text(encoding="utf-8"))


def test_correction_upload_boundary_packet_validates() -> None:
    packet = _load_packet()

    validate_correction_upload_boundary_packet(packet)


def test_packet_separates_safe_local_review_from_blocked_official_actions() -> None:
    packet = _load_packet()
    boundaries = {boundary["kind"]: boundary for boundary in packet["boundaries"]}

    assert SAFE_BOUNDARIES.issubset(boundaries)
    assert BLOCKED_BOUNDARIES.issubset(boundaries)

    for kind in SAFE_BOUNDARIES:
        assert boundaries[kind]["decision"] == "allowed_local_only"
        assert boundaries[kind]["manual_handoff_required"] is False

    for kind in BLOCKED_BOUNDARIES:
        assert boundaries[kind]["decision"] == "blocked_requires_attended_user"
        assert boundaries[kind]["manual_handoff_required"] is True
        assert "upload" in " ".join(boundaries[kind].get("agent_must_not", [])).lower() or kind == "certification_or_submission"


def test_next_safe_actions_are_citation_backed_and_non_official() -> None:
    packet = _load_packet()
    citation_ids = {evidence["citation_id"] for evidence in packet["source_evidence"]}

    for action in packet["next_safe_actions"]:
        assert action["requires_devhub_login"] is False
        assert action["changes_official_record"] is False
        assert action["citation_ids"]
        assert set(action["citation_ids"]).issubset(citation_ids)


def test_manual_handoff_blocks_agent_upload_certification_and_submission() -> None:
    packet = _load_packet()
    handoff = packet["manual_handoff"]

    assert handoff["requires_user_attendance"] is True
    assert handoff["requires_exact_confirmation_before_official_action"] is True
    assert handoff["agent_may_click_upload"] is False
    assert handoff["agent_may_certify_or_submit"] is False
    assert "may not click upload" in handoff["text"].lower()
