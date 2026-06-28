from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.extraction.rerun_rehearsal_validation import (
    RehearsalPacketValidationError,
    assert_valid_rehearsal_packet,
    validate_rehearsal_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "requirement_rerun_rehearsal"


def _load_fixture(name: str) -> dict:
    with (FIXTURE_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def test_accepts_cited_public_rehearsal_packet() -> None:
    packet = _load_fixture("valid_packet.json")

    assert validate_rehearsal_packet(packet) == []
    assert_valid_rehearsal_packet(packet)


def test_rejects_uncited_and_unknown_ids() -> None:
    packet = _load_fixture("invalid_packet.json")

    codes = {issue.code for issue in validate_rehearsal_packet(packet)}

    assert "uncited_requirement_delta" in codes
    assert "unknown_source_id" in codes
    assert "unknown_document_id" in codes
    assert "unknown_requirement_id" in codes


def test_rejects_private_raw_live_unreviewed_stale_unowned_and_mutating_packet() -> None:
    packet = _load_fixture("invalid_packet.json")

    codes = {issue.code for issue in validate_rehearsal_packet(packet)}

    assert "private_or_authenticated_url" in codes
    assert "private_or_authenticated_source" in codes
    assert "raw_source_text_or_downloaded_document_reference" in codes
    assert "live_extraction_claim" in codes
    assert "formalized_requirement_missing_review_status" in codes
    assert "stale_candidate_missing_withdrawal_note" in codes
    assert "missing_reviewer_owner" in codes
    assert "active_requirement_mutation_flag" in codes


def test_assertion_raises_with_deterministic_issue_list() -> None:
    packet = _load_fixture("invalid_packet.json")

    with pytest.raises(RehearsalPacketValidationError) as raised:
        assert_valid_rehearsal_packet(packet)

    assert raised.value.issues
    assert raised.value.issues == tuple(validate_rehearsal_packet(packet))
