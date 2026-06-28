from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.devhub.read_only_observation_redaction_review import (
    assert_valid_read_only_observation_redaction_review_packet,
    build_read_only_observation_redaction_review_packet,
    validate_read_only_observation_redaction_review_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures"
READINESS_PATH = FIXTURE_DIR / "devhub_read_only_readiness_decision" / "read_only_readiness_decision_packet.json"
OPERATOR_CHECKLIST_PATH = FIXTURE_DIR / "devhub" / "read_only_pilot_operator_checklist.json"
EXPECTED_PATH = FIXTURE_DIR / "devhub_read_only_observation_redaction_review" / "review_packet.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict[str, object]:
    return _load(EXPECTED_PATH)


def test_redaction_review_packet_builds_from_readiness_and_operator_checklist_without_browser_launch() -> None:
    packet = build_read_only_observation_redaction_review_packet(
        _load(READINESS_PATH),
        _load(OPERATOR_CHECKLIST_PATH),
    )

    assert packet["packet_type"] == "ppd.devhub.read_only_observation_redaction_review.v1"
    assert packet["fixture_first"] is True
    assert packet["offline_only"] is True
    assert packet["synthetic_only"] is True
    assert packet["launches_browser"] is False
    assert packet["launches_devhub"] is False
    assert packet["launches_playwright"] is False
    assert packet["stores_browser_artifacts"] is False
    assert packet["stores_private_artifacts"] is False
    assert packet["source_packets"]["readiness_decision_packet"]["consumed"] is True
    assert packet["source_packets"]["read_only_pilot_operator_checklist"]["consumed"] is True
    assert validate_read_only_observation_redaction_review_packet(packet) == ()


def test_committed_redaction_review_fixture_is_valid_and_has_required_review_sections() -> None:
    packet = _fixture()

    assert_valid_read_only_observation_redaction_review_packet(packet)
    assert {row["field_name"] for row in packet["synthetic_observation_fields"]} >= {
        "stable_surface_id",
        "page_heading",
        "accessible_landmark_summary",
        "redacted_label_category",
        "synthetic_record_status_label",
        "operator_decision_code",
        "redacted_timestamp",
    }
    assert all(row["raw_value_allowed"] is False for row in packet["synthetic_observation_fields"])
    assert all(row["private_value_allowed"] is False for row in packet["allowed_metadata"])
    assert any("screenshots" in row["prohibition"] for row in packet["private_artifact_prohibitions"])
    assert any("HAR" in row["prohibition"] or "har_files" in row["prohibition"] for row in packet["private_artifact_prohibitions"])
    assert any(row["owner_id"] == "devhub_pilot_operator" for row in packet["reviewer_owners"])


def test_redaction_review_rejects_private_artifact_fields() -> None:
    packet = _fixture()
    packet["screenshot"] = "private-browser-artifact.png"

    errors = validate_read_only_observation_redaction_review_packet(packet)

    assert any("forbidden private artifact key" in error for error in errors)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("session_state", {"user": "devhub"}),
        ("trace_path", "trace.zip"),
        ("har_path", "/home/operator/devhub/network.har"),
        ("storage_state", {"cookies": []}),
        ("local_private_file_path", "/Users/operator/Documents/private-upload.pdf"),
        ("raw_authenticated_page_value", "Permit record owner: Jane Applicant"),
    ],
)
def test_redaction_review_rejects_private_session_and_local_artifacts(field: str, value: object) -> None:
    packet = _fixture()
    packet[field] = value

    errors = validate_read_only_observation_redaction_review_packet(packet)

    assert any("forbidden private artifact" in error for error in errors)


@pytest.mark.parametrize(
    "claim",
    [
        "The worker solved CAPTCHA before recording the observation.",
        "MFA was completed by automation during the pilot.",
        "Account creation was automated for the DevHub login.",
        "Playwright clicked in DevHub and captured the live browser result.",
    ],
)
def test_redaction_review_rejects_auth_automation_and_live_browser_claims(claim: str) -> None:
    packet = _fixture()
    packet["review_notes"] = [claim]

    errors = validate_read_only_observation_redaction_review_packet(packet)

    assert any("automation claim" in error or "live browser execution claim" in error for error in errors)


def test_redaction_review_rejects_missing_abort_prompts() -> None:
    packet = _fixture()
    packet["abort_prompts"] = []

    errors = validate_read_only_observation_redaction_review_packet(packet)

    assert "abort_prompts must be non-empty" in errors


def test_redaction_review_rejects_missing_reviewer_owners() -> None:
    packet = _fixture()
    packet["reviewer_owners"] = []

    errors = validate_read_only_observation_redaction_review_packet(packet)

    assert "reviewer_owners must be non-empty" in errors


def test_redaction_review_rejects_enabled_consequential_controls() -> None:
    packet = _fixture()
    packet["controls"] = [
        {
            "control_id": "submit",
            "label": "Submit application",
            "enabled": True,
        }
    ]

    errors = validate_read_only_observation_redaction_review_packet(packet)

    assert any("enabled consequential control" in error for error in errors)


def test_redaction_review_rejects_missing_private_artifact_prohibition_coverage() -> None:
    packet = _fixture()
    packet["private_artifact_prohibitions"] = [
        row for row in copy.deepcopy(packet["private_artifact_prohibitions"]) if "screenshot" not in row["prohibition"].lower()
    ]
    packet["redaction_rules"] = [
        row for row in copy.deepcopy(packet["redaction_rules"]) if "screenshot" not in row["target"].lower()
    ]
    packet["abort_prompts"] = [
        row for row in copy.deepcopy(packet["abort_prompts"]) if "screenshot" not in row["prompt"].lower()
    ]

    errors = validate_read_only_observation_redaction_review_packet(packet)

    assert any("private artifact prohibitions must cover screenshots" in error for error in errors)
