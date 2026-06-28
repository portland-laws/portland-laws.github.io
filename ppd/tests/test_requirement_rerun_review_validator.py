from __future__ import annotations

import json
from pathlib import Path

from ppd.validators.requirement_rerun_review import validate_requirement_rerun_review_packet


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "requirement_rerun_review"
KNOWN = {
    "known_source_ids": {"src-public-code"},
    "known_document_ids": {"doc-ppd-33.10"},
    "known_requirement_ids": {"req-33-10-review"},
}


def _load(name: str):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_accepts_minimal_audited_packet() -> None:
    issues = validate_requirement_rerun_review_packet(_load("valid_packet.json"), **KNOWN)
    assert issues == []


def test_rejects_unsafe_or_unaudited_packet() -> None:
    issues = validate_requirement_rerun_review_packet(_load("invalid_packet.json"), **KNOWN)
    codes = {issue.code for issue in issues}
    assert "uncited_disposition_decision" in codes
    assert "unknown_source_id" in codes
    assert "unknown_document_id" in codes
    assert "unknown_requirement_id" in codes
    assert "private_or_authenticated_url" in codes
    assert "raw_or_downloaded_reference" in codes
    assert "live_extraction_claim" in codes
    assert "formalized_without_human_review" in codes
    assert "missing_stale_withdrawal_rationale" in codes
    assert "missing_reviewer_owner" in codes
    assert "active_requirement_mutation" in codes
