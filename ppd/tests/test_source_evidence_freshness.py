from __future__ import annotations

import json
from pathlib import Path

from ppd.extraction.source_evidence_freshness import (
    evaluate_document_preparation_source_evidence,
    evaluate_fixture_case,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "source_evidence_freshness"
    / "file_naming_single_pdf_evidence.json"
)


def test_fixture_cases_match_expected_readiness() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    for case in fixture["cases"]:
        result = evaluate_fixture_case(case)
        rule_statuses = {finding["rule"]: finding["status"] for finding in result["findings"]}

        assert result["ready"] is case["expected_ready"], case["case_id"]
        assert result["status"] == case["expected_status"], case["case_id"]
        assert rule_statuses == case["expected_rule_statuses"], case["case_id"]


def test_missing_capture_date_is_not_fresh_enough_for_readiness() -> None:
    result = evaluate_document_preparation_source_evidence(
        [
            {
                "evidence_id": "ppd-file-naming-undated",
                "source_name": "PP&D File Naming Standards and Preparing PDFs",
                "canonical_url": "https://www.portland.gov/ppd/spp-file-naming-standards-preparing-pdfs",
                "captured_at": "",
                "supports_rules": ["file_naming"],
            },
            {
                "evidence_id": "ppd-single-pdf-2026-05-08",
                "source_name": "PP&D Submit Plans Online Single PDF Process",
                "canonical_url": "https://www.portland.gov/ppd/get-permit/submit-plans-online",
                "captured_at": "2026-05-08",
                "supports_rules": ["single_pdf"],
            },
        ],
        as_of="2026-05-14",
    )

    findings = {finding.rule: finding for finding in result.findings}
    assert result.ready is False
    assert result.status == "blocked_by_source_evidence"
    assert findings["file_naming"].status == "stale"
    assert findings["single_pdf"].status == "fresh"
