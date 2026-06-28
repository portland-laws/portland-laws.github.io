from __future__ import annotations

import json
from pathlib import Path

from ppd.logic.file_preparation_guardrails import map_metadata_findings_to_guardrails


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "file_preparation_guardrails"
    / "synthetic_metadata_findings.json"
)


def test_metadata_findings_block_official_actions_and_offer_safe_next_steps() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    result = map_metadata_findings_to_guardrails(payload["document_metadata_findings"])

    assert result["compliance_summary"] == {
        "total_findings": 4,
        "blocking_findings": 3,
        "ready_for_official_actions": False,
    }

    blocked_action_ids = {action["action_id"] for action in result["blocked_actions"]}
    assert blocked_action_ids == {
        "certify_application",
        "submit_permit_request",
        "upload_correction_documents",
        "upload_staged_documents",
    }

    upload_block = next(
        action
        for action in result["blocked_actions"]
        if action["action_id"] == "upload_staged_documents"
    )
    assert upload_block["document_ids"] == [
        "doc_plan_set_combined_pdf",
        "doc_structural_calculations_pdf",
    ]
    assert upload_block["finding_ids"] == [
        "metadata-file-name-not-standard",
        "metadata-pdf-not-searchable",
    ]
    assert upload_block["source_evidence_ids"] == [
        "ppd-file-standards-name-drawings-v1",
        "ppd-single-pdf-searchable-v1",
    ]

    safe_action_ids = {action["action_id"] for action in result["next_safe_actions"]}
    assert safe_action_ids == {
        "rename_local_pdf_to_ppd_standard",
        "request_current_owner_authorization",
        "rebuild_searchable_plan_pdf",
        "review_optional_cover_sheet_note",
    }


def test_compliant_findings_do_not_block_actions() -> None:
    result = map_metadata_findings_to_guardrails(
        [
            {
                "finding_id": "metadata-cover-sheet-present",
                "document_id": "doc_cover_sheet_pdf",
                "status": "compliant",
                "severity": "info",
                "action_impacts": [
                    {
                        "action_id": "upload_staged_documents",
                        "reason": "Compliant metadata should not block upload staging.",
                    }
                ],
            }
        ]
    )

    assert result["blocked_actions"] == []
    assert result["compliance_summary"]["ready_for_official_actions"] is True
