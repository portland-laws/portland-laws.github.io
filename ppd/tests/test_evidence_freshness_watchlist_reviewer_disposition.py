from __future__ import annotations

import json
from pathlib import Path

from ppd.validation.evidence_freshness_watchlist_reviewer_disposition import (
    validate_disposition_packet,
)


FIXTURES = Path(__file__).parent / "fixtures" / "evidence_freshness_watchlist"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_accepts_minimal_cited_offline_reviewer_packet() -> None:
    packet = _load_fixture("valid_reviewer_disposition_packet.json")

    assert validate_disposition_packet(packet) == []


def test_rejects_forbidden_reviewer_disposition_packet_content() -> None:
    packet = _load_fixture("invalid_reviewer_disposition_packet.json")

    codes = {finding.code for finding in validate_disposition_packet(packet)}

    assert "uncited_decision" in codes
    assert "missing_consumed_packet_refs" in codes
    assert "missing_offline_validation_commands" in codes
    assert "missing_reviewer_owner" in codes
    assert "non_allowlisted_url" in codes
    assert "authenticated_or_session_url" in codes
    assert "raw_body_download_or_archive_reference" in codes
    assert "private_or_session_artifact" in codes
    assert "live_crawl_or_processor_execution_claim" in codes
    assert "legal_or_permitting_outcome_guarantee" in codes
    assert "active_mutation_flag" in codes
