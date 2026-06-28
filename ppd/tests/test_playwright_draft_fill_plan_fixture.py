import json
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "playwright_draft_fill_plan_fixture.json"


PROHIBITED_ACTION_FLAGS = {
    "may_open_authenticated_browser",
    "may_fill_live_fields",
    "may_click_save_draft",
    "may_upload_documents",
    "may_submit_application",
    "may_certify_or_acknowledge",
    "may_enter_payment_details",
    "may_schedule_or_cancel",
}


ALLOWED_PREVIEW_ACTIONS = {
    "rank_candidate_selectors",
    "map_known_facts_to_field_preview_values",
    "ask_questions_for_missing_facts",
    "render_local_draft_fill_summary",
}


def load_fixture():
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_playwright_draft_fill_plan_fixture_is_draft_preview_only():
    fixture = load_fixture()
    limits = fixture["automation_limits"]

    assert limits["mode"] == "reversible_draft_preview_only"
    for flag in PROHIBITED_ACTION_FLAGS:
        assert limits[flag] is False

    assert set(limits["allowed_preview_actions"]) == ALLOWED_PREVIEW_ACTIONS
    assert fixture["source_mode"] == "mocked_no_live_crawl"


def test_selector_candidates_are_ranked_by_evidence_confidence():
    fixture = load_fixture()

    for field in fixture["field_previews"]:
        candidates = field["selector_candidates"]
        assert candidates, field["field_id"]
        ranks = [candidate["rank"] for candidate in candidates]
        confidences = [candidate["confidence"] for candidate in candidates]

        assert ranks == list(range(1, len(candidates) + 1))
        assert confidences == sorted(confidences, reverse=True)

        for candidate in candidates:
            assert 0 <= candidate["confidence"] <= 1
            assert candidate["selector"]
            assert candidate["strategy"] in {
                "accessible_label",
                "accessible_role_name",
                "stable_attribute",
                "semantic_input_type",
            }
            assert candidate["evidence"]


def test_missing_user_facts_map_to_questions_and_unfilled_previews():
    fixture = load_fixture()
    missing_facts = fixture["missing_user_facts"]
    fields_by_id = {field["field_id"]: field for field in fixture["field_previews"]}

    assert missing_facts
    for missing_fact in missing_facts:
        assert missing_fact["fact_key"]
        assert missing_fact["question"].endswith("?")
        assert missing_fact["reason"]
        assert missing_fact["answer_type"]

        for field_id in missing_fact["required_for_field_ids"]:
            field = fields_by_id[field_id]
            assert field["draft_preview_value"] is None
            assert field["allowed_action"] == "ask_question_before_preview"
            assert field["preview_value_source"] == f"missing_user_facts.{missing_fact['fact_key']}"


def test_known_fact_fields_are_local_previews_only():
    fixture = load_fixture()
    known_facts = fixture["known_case_facts"]

    for field in fixture["field_previews"]:
        if field["preview_value_source"].startswith("known_case_facts."):
            fact_key = field["preview_value_source"].split(".", 1)[1]
            assert field["draft_preview_value"] == known_facts[fact_key]
            assert field["allowed_action"] == "local_preview_only"
            assert 0 < field["confidence"] <= 1


def test_fixture_blocks_consequential_devhub_actions():
    fixture = load_fixture()
    blocked_actions = {blocked["action"]: blocked["reason"] for blocked in fixture["blocked_actions"]}

    assert "click_submit_application" in blocked_actions
    assert "click_certification_checkbox" in blocked_actions
    assert "upload_plan_pdf" in blocked_actions
    assert "enter_payment_method" in blocked_actions
    assert "save_live_devhub_draft" in blocked_actions

    for reason in blocked_actions.values():
        assert reason


def test_fixture_does_not_reference_private_browser_artifacts():
    fixture_text = FIXTURE_PATH.read_text(encoding="utf-8").lower()

    forbidden_terms = [
        "cookie",
        "storage_state",
        "auth_state",
        "trace.zip",
        ".har",
        "captcha",
        "mfa secret",
        "password",
        "payment card",
    ]
    for forbidden_term in forbidden_terms:
        assert forbidden_term not in fixture_text
