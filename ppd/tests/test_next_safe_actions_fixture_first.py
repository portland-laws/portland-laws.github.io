from pathlib import Path

from ppd.logic.next_safe_actions import build_next_safe_actions, load_fixture_bundle


FIXTURES = Path(__file__).parent / "fixtures" / "next_safe_actions"


def test_fixture_first_next_safe_actions_response_is_cited_and_guarded() -> None:
    process_model, user_gap_analysis, guardrail_bundle = load_fixture_bundle(FIXTURES)

    response = build_next_safe_actions(
        process_model=process_model,
        user_gap_analysis=user_gap_analysis,
        guardrail_bundle=guardrail_bundle,
    )

    assert response["case_id"] == "case-demo-adu-001"
    assert response["process_id"] == "process-residential-adu-devhub-demo"
    assert response["guardrail_bundle_id"] == "guardrails-residential-adu-devhub-demo"

    missing = response["missing_questions"]
    assert [item["id"] for item in missing] == [
        "contractor_license_status",
        "single_pdf_plan_set",
    ]
    assert all(item["citations"] for item in missing)
    assert missing[0]["citations"][0]["evidence_id"] == "ev-standard-trade-license"
    assert missing[1]["citations"][0]["evidence_id"] == "ev-single-pdf-guidance"

    warnings = response["evidence_warnings"]
    assert {item["kind"] for item in warnings} == {
        "stale_evidence",
        "conflicting_evidence",
    }
    assert all(item["citations"] for item in warnings)
    assert any(
        item["id"] == "conflict-plan-format" and item["severity"] == "blocker"
        for item in warnings
    )

    reversible = response["reversible_draft_actions"]
    assert [item["action_type"] for item in reversible] == ["draft_form_values"]
    assert reversible[0]["draft_only"] is True
    assert reversible[0]["requires_user_confirmation_before_official_action"] is True
    assert reversible[0]["citations"][0]["evidence_id"] == "ev-devhub-save-later"

    blocked = response["blocked_consequential_actions"]
    blocked_types = {item["action_type"] for item in blocked}
    assert blocked_types == {"upload_to_official_record", "submit_permit_request"}
    assert all(item["requires_attended_handoff"] for item in blocked)
    assert any(item["reason_code"] == "gap_analysis_block" for item in blocked)
    assert any(item["reason_code"] == "requires_exact_confirmation" for item in blocked)
