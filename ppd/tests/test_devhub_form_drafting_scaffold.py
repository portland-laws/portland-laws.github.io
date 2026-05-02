from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.devhub.form_drafting_scaffold import (
    DraftPreviewError,
    assert_preview_does_not_touch_live_devhub,
    build_draft_action_preview,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "form_drafting_scaffold_fixture.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def draftable_fixture_only() -> dict:
    fixture = load_fixture()
    fixture["fields"] = [field for field in fixture["fields"] if field["fieldId"] != "plan_upload"]
    return fixture


def test_form_drafting_scaffold_returns_preview_only_actions() -> None:
    preview = build_draft_action_preview(
        draftable_fixture_only(),
        {
            "project_description": "Replace branch circuit in existing tenant space.",
            "work_category": "Electrical",
            "owner_acknowledges_draft_notice": True,
        },
    )

    preview_json = preview.to_json()
    assert preview_json["mode"] == "preview_only"
    assert preview_json["touchesLiveDevhub"] is False
    assert preview_json["refusedActions"] == []
    assert [action["fieldId"] for action in preview_json["actions"]] == [
        "project_description",
        "work_category",
        "owner_acknowledges_draft_notice",
    ]
    assert {action["browserExecution"] for action in preview_json["actions"]} == {"not_performed"}
    assert {action["classification"] for action in preview_json["actions"]} == {"reversible_draft_edit"}
    assert all(action["afterPreviewValue"] in {"[REDACTED]", "true"} for action in preview_json["actions"])
    assert_preview_does_not_touch_live_devhub(preview)


def test_form_drafting_scaffold_refuses_live_or_unmarked_fixtures() -> None:
    fixture = draftable_fixture_only()
    fixture["environment"] = "live"
    fixture["fixtureSource"] = "live_devhub_page"

    with pytest.raises(DraftPreviewError, match="mocked DevHub fixtures"):
        build_draft_action_preview(fixture, {"project_description": "Draft value"})


def test_form_drafting_scaffold_refuses_upload_controls_in_fixture_validation() -> None:
    with pytest.raises(DraftPreviewError, match="upload"):
        build_draft_action_preview(load_fixture(), {"project_description": "Draft value"})


def test_form_drafting_scaffold_refuses_unknown_and_invalid_option_actions() -> None:
    preview = build_draft_action_preview(
        draftable_fixture_only(),
        {
            "unknown_field": "Draft value",
            "work_category": "Demolition",
        },
    )

    refused = preview.to_json()["refusedActions"]
    assert refused == [
        {
            "fieldId": "unknown_field",
            "reason": "field is absent from mocked DevHub fixture",
        },
        {
            "fieldId": "work_category",
            "reason": "proposed value is not one of the mocked fixture options",
        },
    ]
    assert preview.to_json()["actions"] == []
