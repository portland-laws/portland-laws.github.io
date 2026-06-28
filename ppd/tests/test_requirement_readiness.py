from __future__ import annotations

import json
from pathlib import Path

from ppd.logic.requirement_readiness import validate_guardrail_requirement_inputs

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "requirement_readiness" / "guardrail_bundle_inputs.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_only_fresh_supported_human_reviewed_requirements_are_ready() -> None:
    report = validate_guardrail_requirement_inputs(_load_fixture())

    assert report.ready_requirement_ids == ("policy.ready.single_pdf_upload",)
    assert set(report.blocked_requirement_ids) == {
        "policy.stale.source",
        "policy.unsupported.path",
        "policy.unreviewed.certification",
        "policy.unfresh.evidence",
    }
    assert not report.is_ready


def test_readiness_report_exposes_deterministic_issue_codes() -> None:
    report = validate_guardrail_requirement_inputs(_load_fixture())

    issues_by_requirement = {}
    for issue in report.issues:
        issues_by_requirement.setdefault(issue.requirement_id, set()).add(issue.code)

    assert issues_by_requirement["policy.stale.source"] == {"requirement_not_fresh"}
    assert issues_by_requirement["policy.unsupported.path"] == {
        "requirement_not_supported",
        "unsupported_requirement_path",
    }
    assert issues_by_requirement["policy.unreviewed.certification"] == {"requirement_not_human_reviewed"}
    assert issues_by_requirement["policy.unfresh.evidence"] == {"source_evidence_not_fresh"}


def test_all_ready_candidate_passes_without_live_source_reads() -> None:
    candidate = {
        "guardrail_bundle_id": "bundle.ready.fixture",
        "source_evidence": [
            {"evidence_id": "evidence.ready", "freshness_status": "fresh"},
        ],
        "requirements": [
            {
                "requirement_id": "policy.ready.fixture",
                "source_evidence_ids": ["evidence.ready"],
                "freshness_status": "fresh",
                "support_status": "supported",
                "human_review_status": "approved",
                "formalization_status": "ready",
            }
        ],
    }

    report = validate_guardrail_requirement_inputs(candidate)

    assert report.is_ready
    assert report.ready_requirement_ids == ("policy.ready.fixture",)
    assert report.blocked_requirement_ids == ()
    assert report.issues == ()
