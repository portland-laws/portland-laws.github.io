from __future__ import annotations

import json
from pathlib import Path

from ppd.acceptance.release_review import validate_release_acceptance_review_packet


FIXTURES = Path(__file__).parent / "fixtures" / "release_acceptance_review"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_release_acceptance_review_accepts_cited_traceable_packet() -> None:
    result = validate_release_acceptance_review_packet(_load_fixture("valid_packet.json"))

    assert result.ok
    assert result.issues == ()


def test_release_acceptance_review_rejects_required_guardrail_failures() -> None:
    result = validate_release_acceptance_review_packet(_load_fixture("invalid_packet.json"))

    assert not result.ok
    codes = {issue.code for issue in result.issues}
    assert "uncited_checklist_item" in codes
    assert "missing_consumed_packet_refs" in codes
    assert "missing_open_blocker_disposition" in codes
    assert "missing_reviewer_owner" in codes
    assert "incomplete_validation_rerun_expectation" in codes
    assert "private_or_session_artifact" in codes
    assert "raw_crawl_download_archive_reference" in codes
    assert "live_publication_claim" in codes
    assert "legal_or_permitting_outcome_guarantee" in codes
    assert "enabled_consequential_control" in codes
    assert "active_artifact_mutation_flag" in codes


def test_release_acceptance_review_rejects_absent_core_sections() -> None:
    result = validate_release_acceptance_review_packet({"packet_id": "empty-review"})

    assert not result.ok
    codes = {issue.code for issue in result.issues}
    assert "missing_checklist" in codes
    assert "missing_consumed_packet_refs" in codes
    assert "missing_reviewer_owner" in codes
    assert "missing_validation_rerun_expectations" in codes
