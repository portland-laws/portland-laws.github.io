from __future__ import annotations

import json
from pathlib import Path

from ppd.crawler.source_refresh_runbook_validation import (
    findings_as_dicts,
    is_source_refresh_runbook_candidate_valid,
    validate_source_refresh_runbook_candidate,
)


FIXTURES = Path(__file__).parent / "fixtures" / "source_refresh_runbook_candidates.json"


def _fixtures() -> dict[str, object]:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def test_valid_public_preflight_candidate_has_no_findings() -> None:
    candidate = _fixtures()["valid_public_preflight"]

    findings = validate_source_refresh_runbook_candidate(candidate)

    assert findings == []
    assert is_source_refresh_runbook_candidate_valid(candidate)


def test_invalid_candidate_reports_required_refresh_runbook_blocks() -> None:
    candidate = _fixtures()["invalid_private_mutating_candidate"]

    findings = validate_source_refresh_runbook_candidate(candidate)
    codes = {finding.code for finding in findings}

    assert "outside_allowlist" in codes
    assert "private_or_authenticated_target" in codes
    assert "missing_robots_evidence" in codes
    assert "missing_policy_evidence" in codes
    assert "raw_download_or_archive_reference" in codes
    assert "live_fetch_or_processor_execution_claim" in codes
    assert "missing_rate_limit_window" in codes
    assert "missing_reviewer_checkpoints" in codes
    assert "missing_abort_escalation_notes" in codes
    assert "active_schedule_flag" in codes
    assert "registry_mutation_flag" in codes
    assert not is_source_refresh_runbook_candidate_valid(candidate)


def test_findings_serialize_as_stable_dicts() -> None:
    candidate = _fixtures()["invalid_private_mutating_candidate"]

    serialized = findings_as_dicts(validate_source_refresh_runbook_candidate(candidate))

    assert serialized
    assert all(set(item) == {"code", "field", "message"} for item in serialized)
    assert serialized == sorted(serialized, key=lambda item: serialized.index(item))
