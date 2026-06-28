import json
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "next_safe_action" / "recommendations.json"


def load_fixture():
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_next_safe_action_fixture_has_required_sections():
    fixture = load_fixture()

    assert fixture["schema_version"] == "2026-05-14.next_safe_action.v1"
    assert fixture["case_id"]
    assert fixture["process_id"]
    assert fixture["user_gap_analysis"]["missing_facts"]
    assert fixture["process_dependency_graph_state"]["nodes"]
    assert fixture["process_dependency_graph_state"]["edges"]
    assert fixture["action_classification"]["actions"]
    assert fixture["guardrail_bundle_results"]["validation_status"] == "fixture_validated"
    assert fixture["next_safe_action_recommendations"]


def test_recommendations_cover_all_agent_facing_outcomes():
    fixture = load_fixture()
    recommendations = fixture["next_safe_action_recommendations"]
    observed = {recommendation["recommendation"] for recommendation in recommendations}

    assert observed == {
        "read-only",
        "reversible-draft",
        "manual-handoff",
        "refused-action",
    }


def test_action_ids_are_classified_before_they_are_recommended():
    fixture = load_fixture()
    classified_action_ids = {
        action["action_id"] for action in fixture["action_classification"]["actions"]
    }

    for recommendation in fixture["next_safe_action_recommendations"]:
        assert recommendation["action_id"] in classified_action_ids
        assert recommendation["reason"]
        assert isinstance(recommendation["must_not_do"], list)


def test_guardrails_block_financial_and_unattended_official_actions():
    fixture = load_fixture()
    recommendations_by_action = {
        recommendation["action_id"]: recommendation
        for recommendation in fixture["next_safe_action_recommendations"]
    }

    payment = recommendations_by_action["submit_payment"]
    submission = recommendations_by_action["submit_permit_request"]

    assert payment["recommendation"] == "refused-action"
    assert payment["allowed"] is False
    assert "submit_payment" in payment["must_not_do"]

    assert submission["recommendation"] == "refused-action"
    assert submission["allowed"] is False
    assert "obtain_user_present_exact_confirmation" in submission["required_before_action"]


def test_reversible_draft_does_not_include_consequential_actions():
    fixture = load_fixture()
    draft_recommendations = [
        recommendation
        for recommendation in fixture["next_safe_action_recommendations"]
        if recommendation["recommendation"] == "reversible-draft"
    ]

    assert draft_recommendations
    for recommendation in draft_recommendations:
        prohibited = set(recommendation["must_not_do"])
        assert "submit" in prohibited
        assert "certify" in prohibited
        assert "upload_to_official_record" in prohibited
        assert "pay" in prohibited


def test_gap_analysis_blocks_match_guardrail_failures():
    fixture = load_fixture()
    blocked_actions = set(fixture["user_gap_analysis"]["blocked_actions"])
    predicate_results = fixture["guardrail_bundle_results"]["deterministic_predicates"]
    failed_predicates = {
        predicate["predicate_id"]
        for predicate in predicate_results
        if predicate["result"] == "fail"
    }

    assert "submit_permit_request" in blocked_actions
    assert "enter_payment_details" in blocked_actions
    assert "required_documents_complete" in failed_predicates
    assert "applicant_role_unambiguous" in failed_predicates
