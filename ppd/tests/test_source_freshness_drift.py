import json
from pathlib import Path

import pytest

from ppd.extraction.source_freshness_drift import (
    assert_valid_source_freshness_drift_digest,
    validate_source_freshness_drift_digest,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "source_freshness_drift"


def load_fixture(name: str):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_source_freshness_drift_digest_passes():
    result = validate_source_freshness_drift_digest(load_fixture("valid_digest.json"))

    assert result.valid
    assert result.issues == ()


def test_invalid_source_freshness_drift_digest_reports_required_rejections():
    result = validate_source_freshness_drift_digest(load_fixture("invalid_digest.json"))

    assert not result.valid
    codes = {issue.code for issue in result.issues}
    assert "uncited_changed_source_claim" in codes
    assert "private_or_authenticated_source_reference" in codes
    assert "raw_or_downloaded_document_reference" in codes
    assert "live_network_run_flag" in codes
    assert "missing_affected_requirement_link" in codes
    assert "missing_affected_guardrail_link" in codes
    assert "stale_source_marked_current_without_reviewer_acknowledgement" in codes


def test_assert_valid_source_freshness_drift_digest_raises_for_policy_violations():
    with pytest.raises(ValueError, match="invalid source freshness drift digest"):
        assert_valid_source_freshness_drift_digest(load_fixture("invalid_digest.json"))


def test_changed_claim_with_citations_still_requires_requirement_and_guardrail_links():
    digest = {
        "changed_source_claims": [
            {
                "claim_id": "claim-cited-but-unlinked",
                "changed": True,
                "citation_ids": ["citation-1"],
            }
        ]
    }

    result = validate_source_freshness_drift_digest(digest)

    codes = {issue.code for issue in result.issues}
    assert "uncited_changed_source_claim" not in codes
    assert "missing_affected_requirement_link" in codes
    assert "missing_affected_guardrail_link" in codes


def test_stale_source_marked_current_passes_with_reviewer_acknowledgement():
    digest = {
        "freshness_entries": [
            {
                "source_id": "ppd-submit-plans-online",
                "observed_freshness_status": "stale",
                "freshness_status": "current",
                "reviewer_acknowledged": True,
            }
        ]
    }

    result = validate_source_freshness_drift_digest(digest)

    assert result.valid
