from __future__ import annotations

import copy
from pathlib import Path

import pytest

from ppd.devhub.draft_fill_plan import load_draft_fill_plan, require_draft_fill_allowed, validate_draft_fill_plan


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "draft_fill_plan_valid.json"


def test_valid_fixture_allows_only_reversible_attended_previewed_field_fill() -> None:
    plan = load_draft_fill_plan(FIXTURE_PATH)

    result = validate_draft_fill_plan(plan)

    assert result.allowed is True
    assert result.errors == ()
    require_draft_fill_allowed(plan)


@pytest.mark.parametrize(
    ("field_key", "expected_error"),
    [
        ("source_evidence_ids", "source_evidence_ids must include at least one evidence ID"),
        ("user_case_fact_ids", "user_case_fact_ids must include at least one fact ID"),
    ],
)
def test_each_filled_value_requires_evidence_and_user_case_fact(field_key: str, expected_error: str) -> None:
    plan = load_draft_fill_plan(FIXTURE_PATH)
    plan["fields"][0][field_key] = []

    result = validate_draft_fill_plan(plan)

    assert result.allowed is False
    assert any(expected_error in error for error in result.errors)


def test_unknown_evidence_or_fact_ids_block_field_fill() -> None:
    plan = load_draft_fill_plan(FIXTURE_PATH)
    plan["fields"][0]["source_evidence_ids"] = ["missing-evidence"]
    plan["fields"][1]["user_case_fact_ids"] = ["missing-fact"]

    result = validate_draft_fill_plan(plan)

    assert result.allowed is False
    assert "unknown evidence ID 'missing-evidence'" in "; ".join(result.errors)
    assert "unknown fact ID 'missing-fact'" in "; ".join(result.errors)


@pytest.mark.parametrize(
    ("path", "value", "expected_error"),
    [
        (("attendance", "user_present"), False, "attendance.user_present must be true"),
        (("preview", "rendered"), False, "preview.rendered must be true"),
        (("preview", "acknowledged_by_user"), False, "preview.acknowledged_by_user must be true"),
        (("action", "reversible"), False, "action.reversible must be true"),
    ],
)
def test_attendance_preview_and_reversibility_are_required(path: tuple[str, str], value: bool, expected_error: str) -> None:
    plan = load_draft_fill_plan(FIXTURE_PATH)
    section, key = path
    plan[section][key] = value

    result = validate_draft_fill_plan(plan)

    assert result.allowed is False
    assert expected_error in result.errors


def test_consequential_devhub_action_is_not_allowed() -> None:
    plan = load_draft_fill_plan(FIXTURE_PATH)
    plan["action"] = copy.deepcopy(plan["action"])
    plan["action"]["action_type"] = "submit"

    result = validate_draft_fill_plan(plan)

    assert result.allowed is False
    assert "action.action_type must be 'devhub_field_fill'" in result.errors
    assert "consequential action 'submit' is not allowed by draft-fill planning" in result.errors


def test_live_executor_name_is_rejected_by_fixture_validator() -> None:
    plan = load_draft_fill_plan(FIXTURE_PATH)
    plan["action"]["executor"] = "playwright_devhub_executor"

    result = validate_draft_fill_plan(plan)

    assert result.allowed is False
    assert "action.executor must not name a live DevHub executor" in result.errors
