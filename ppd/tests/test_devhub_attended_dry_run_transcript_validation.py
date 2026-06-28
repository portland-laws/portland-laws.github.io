import json
import re
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub"
    / "attended_dry_run_redacted_transcript.json"
)

ACTION_JOURNAL_SAFE_EVENT_TYPES = {
    "devhub_attended_preflight",
    "devhub_attempted_action",
    "exact_confirmation_checkpoint",
    "manual_handoff",
    "post_action_hardening_review",
    "refused_action",
    "reversible_draft_plan",
}

CLASSIFICATION_HINT_TO_EVENT_TYPE = {
    "attended_preflight": "devhub_attended_preflight",
    "blocked_official_control": "refused_action",
    "exact_confirmation_checkpoint": "exact_confirmation_checkpoint",
    "manual_handoff": "manual_handoff",
    "post_action_hardening_review": "post_action_hardening_review",
    "read_only_review": "devhub_attempted_action",
    "reversible_draft": "reversible_draft_plan",
}

REQUIRED_COVERAGE = {
    "read_only_review": "devhub_attempted_action",
    "reversible_draft": "reversible_draft_plan",
    "exact_confirmation_checkpoint": "exact_confirmation_checkpoint",
    "manual_handoff": "manual_handoff",
    "blocked_official_control": "refused_action",
}

FORBIDDEN_STORED_VALUE_KEYS = {
    "auth_state",
    "captcha_response",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "har",
    "mfa_code",
    "password",
    "payment_card_number",
    "payment_cvv",
    "raw_page_text",
    "screenshot",
    "session_storage",
    "trace",
}

PRIVATE_VALUE_PATTERNS = (
    re.compile(r"\b\d{12,19}\b"),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"/Users/|/home/[^/\s]+/|[A-Za-z]:\\\\"),
)

ALLOWED_VALUE_MARKERS = {"[REDACTED]", "[NOT_STORED]", "[USER_PRESENT]", "[MANUAL]"}


def _load_fixture() -> dict:
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def _classify_step(step: dict) -> str:
    return CLASSIFICATION_HINT_TO_EVENT_TYPE[step["classification_hint"]]


def _walk_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _walk_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_strings(nested)


def test_fixture_is_redacted_and_fixture_only():
    fixture = _load_fixture()

    assert fixture["fixture_kind"] == "synthetic_redacted_transcript"
    assert fixture["privacy_policy"]["private_page_values_stored"] is False
    assert set(fixture["privacy_policy"]["allowed_value_markers"]) == ALLOWED_VALUE_MARKERS
    assert "no live DevHub session" in fixture["source"]


def test_transcript_steps_classify_to_action_journal_safe_event_types():
    fixture = _load_fixture()
    classified_events = []

    for step in fixture["steps"]:
        event_type = _classify_step(step)
        classified_events.append(event_type)

        assert event_type == step["expected_event_type"]
        assert event_type in ACTION_JOURNAL_SAFE_EVENT_TYPES
        assert step["requires_attendance"] is True

    assert set(REQUIRED_COVERAGE.values()).issubset(classified_events)


def test_required_devhub_dry_run_categories_are_covered():
    fixture = _load_fixture()
    hints_by_event_type = {
        step["classification_hint"]: step["expected_event_type"] for step in fixture["steps"]
    }

    for classification_hint, event_type in REQUIRED_COVERAGE.items():
        assert hints_by_event_type[classification_hint] == event_type


def test_exact_confirmation_checkpoints_do_not_store_private_values():
    fixture = _load_fixture()
    checkpoints = [
        step
        for step in fixture["steps"]
        if step["expected_event_type"] == "exact_confirmation_checkpoint"
    ]

    assert checkpoints
    for checkpoint in checkpoints:
        assert checkpoint["requires_exact_confirmation"] is True
        assert checkpoint["stored_page_values"] == {}
        assert "confirmation_phrase" in checkpoint


def test_blocked_official_controls_are_refused_actions():
    fixture = _load_fixture()
    blocked_intents = {
        "attempt_submit_permit_request",
        "attempt_certify_acknowledgement",
        "attempt_upload_correction",
        "attempt_schedule_inspection",
        "attempt_submit_payment",
    }

    refused_intents = {
        step["intent"]
        for step in fixture["steps"]
        if step["expected_event_type"] == "refused_action"
    }

    assert blocked_intents.issubset(refused_intents)


def test_journal_safe_steps_do_not_include_private_page_values():
    fixture = _load_fixture()

    for step in fixture["steps"]:
        stored_page_values = step.get("stored_page_values", {})
        assert set(stored_page_values).isdisjoint(FORBIDDEN_STORED_VALUE_KEYS)

        for value in _walk_strings(stored_page_values):
            assert value in ALLOWED_VALUE_MARKERS
            for private_pattern in PRIVATE_VALUE_PATTERNS:
                assert private_pattern.search(value) is None

        for value in _walk_strings(step):
            for private_pattern in PRIVATE_VALUE_PATTERNS:
                assert private_pattern.search(value) is None
