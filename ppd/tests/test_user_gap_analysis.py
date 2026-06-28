from __future__ import annotations

import json
from pathlib import Path

from ppd.logic.user_gap_analysis import analyze_user_gaps

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "user_gap_analysis"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_user_gap_analysis_reports_missing_inputs_and_blocks_consequential_actions() -> None:
    fixture = _load_fixture("minimal_case.json")

    result = analyze_user_gaps(
        case_id=fixture["case_id"],
        process_model=fixture["process_model"],
        known_facts=fixture["known_facts"],
        user_documents=fixture["user_documents"],
    ).to_dict()

    assert result["case_id"] == "case-fixture-001"
    assert result["process_id"] == "residential-building-permit-fixture"
    assert result["missing_facts"] == ["contractor_license_number"]
    assert result["missing_documents"] == ["structural_calculations"]
    assert result["matched_documents"] == [
        {
            "requirement_id": "plans_single_pdf",
            "document_id": "doc-001",
            "label": "Single PDF drawing set",
        }
    ]

    blocked_action_ids = {action["action_id"] for action in result["blocked_actions"]}
    assert "upload_plans" in blocked_action_ids
    assert "certify_application" in blocked_action_ids
    assert "submit_permit_request" in blocked_action_ids
    assert "submit_payment" in blocked_action_ids
    assert "schedule_inspection" in blocked_action_ids
    assert "review_public_requirements" not in blocked_action_ids

    for action in result["blocked_actions"]:
        assert action["requires_exact_confirmation"] is True
        assert action["requires_attendance"] is True

    assert result["required_confirmations"] == sorted(blocked_action_ids)
    assert result["next_safe_actions"] == [
        "review_public_requirements",
        "ask_user_for_missing_facts",
        "ask_user_for_missing_documents",
    ]


def test_user_gap_analysis_allows_only_reversible_draft_when_inputs_are_complete() -> None:
    fixture = _load_fixture("minimal_case.json")
    known_facts = dict(fixture["known_facts"])
    known_facts["contractor_license_number"] = "CCB000000"
    user_documents = list(fixture["user_documents"])
    user_documents.append(
        {
            "document_id": "doc-002",
            "document_type": "structural_calculations",
            "label": "Structural calculations",
            "freshness_status": "current",
        }
    )

    result = analyze_user_gaps(
        case_id=fixture["case_id"],
        process_model=fixture["process_model"],
        known_facts=known_facts,
        user_documents=user_documents,
        requested_actions=["prepare_reversible_draft_plan", "submit_permit_request"],
    ).to_dict()

    assert result["missing_facts"] == []
    assert result["missing_documents"] == []
    assert result["next_safe_actions"] == [
        "review_public_requirements",
        "prepare_reversible_draft_plan",
    ]
    assert result["required_confirmations"] == ["submit_permit_request"]
    assert result["blocked_actions"] == [
        {
            "action_id": "submit_permit_request",
            "reason": "Consequential PP&D action requires attended user review and exact confirmation.",
            "requires_exact_confirmation": True,
            "requires_attendance": True,
        }
    ]
