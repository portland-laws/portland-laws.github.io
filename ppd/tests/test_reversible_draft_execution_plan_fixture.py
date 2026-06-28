import json
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "reversible_draft_execution_plan.json"


CONSEQUENTIAL_CATEGORIES = {
    "consequential_certification",
    "consequential_upload",
    "consequential_submit",
    "financial_payment_detail_entry",
    "financial_submit_payment",
}

REVERSIBLE_CATEGORIES = {
    "local_preview",
    "reversible_draft_field_fill",
    "save_for_later",
}


def load_fixture():
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_reversible_draft_execution_plan_fixture_is_commit_safe():
    fixture = load_fixture()

    assert fixture["privacy_classification"] == "commit_safe_synthetic_fixture"
    assert fixture["live_automation_allowed"] is False
    assert fixture["stores_private_session_artifacts"] is False


def test_reversible_and_consequential_boundaries_are_separated():
    fixture = load_fixture()
    steps = fixture["execution_plan"]["ordered_steps"]
    categories = {step["category"] for step in steps}

    assert REVERSIBLE_CATEGORIES <= categories
    assert CONSEQUENTIAL_CATEGORIES <= categories

    for step in steps:
        category = step["category"]
        if category in REVERSIBLE_CATEGORIES:
            assert step["requires_exact_confirmation"] is False
            assert step["may_submit_or_certify"] is False
            assert step["may_upload_file"] is False
            assert step["may_enter_payment_details"] is False
        elif category in CONSEQUENTIAL_CATEGORIES:
            assert step["requires_authenticated_session"] is True
            assert step["requires_user_attendance"] is True
            assert step["requires_exact_confirmation"] is True
            assert step["confirmation_phrase"].startswith("I confirm I am present and authorize: ")
        else:
            raise AssertionError(f"Unexpected execution plan category: {category}")


def test_save_for_later_is_not_treated_as_submission_upload_or_payment():
    fixture = load_fixture()
    steps = fixture["execution_plan"]["ordered_steps"]
    save_step = next(step for step in steps if step["category"] == "save_for_later")

    assert save_step["may_write_devhub_state"] is True
    assert save_step["requires_exact_confirmation"] is False
    assert save_step["may_submit_or_certify"] is False
    assert save_step["may_upload_file"] is False
    assert save_step["may_enter_payment_details"] is False
    assert save_step["safe_result"] == "saved_draft_only"


def test_payment_boundaries_do_not_allow_unattended_execution():
    fixture = load_fixture()
    steps = fixture["execution_plan"]["ordered_steps"]
    payment_steps = [step for step in steps if step["category"].startswith("financial_")]

    assert payment_steps
    for step in payment_steps:
        assert step["requires_user_attendance"] is True
        assert step["requires_exact_confirmation"] is True
        assert step["safe_result"] == "blocked_until_exact_confirmation"
