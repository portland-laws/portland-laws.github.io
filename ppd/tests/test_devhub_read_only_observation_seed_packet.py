from __future__ import annotations

import pytest

from ppd.devhub.read_only_observation_seed_packet import (
    EXPECTED_PACKET_VERSION,
    assert_next_devhub_read_only_observation_seed_packet_v1,
    validate_next_devhub_read_only_observation_seed_packet_v1,
)


def valid_packet() -> dict[str, object]:
    return {
        "version": EXPECTED_PACKET_VERSION,
        "post_decision_smoke_replay_references": [
            "ppd/tests/fixtures/devhub/read_only/post_decision_smoke_replay.json"
        ],
        "official_devhub_guidance_placeholders": [
            {
                "source": "DevHub FAQ placeholder",
                "expected_update": "replace with refreshed public guidance citation before use",
            }
        ],
        "attended_read_only_observation_targets": [
            "DevHub Home account-scoped read-only headings",
            "My Permits and Requests read-only status labels",
        ],
        "authorization_prerequisites": [
            "user-owned account",
            "manual sign-in completed by user",
            "observer records redacted metadata only",
        ],
        "redaction_expectations": [
            "no credentials",
            "no cookies",
            "no local private paths",
            "no private upload contents",
        ],
        "fixture_only_capture_schema_updates": [
            {
                "field": "observed_landmark_labels",
                "source": "deterministic fixture only",
            }
        ],
        "unsupported_manual_handoff_reminders": [
            "payment, certification, upload, scheduling, cancellation, and submission remain manual handoff actions"
        ],
        "rollback_notes": [
            "delete generated fixture candidate and rerun validation if review fails"
        ],
        "reviewer_routing": ["PP&D automation reviewer", "PP&D compliance reviewer"],
        "validation_commands": [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]],
        "mutation_enabled": False,
    }


def test_accepts_complete_fixture_only_read_only_seed_packet() -> None:
    result = validate_next_devhub_read_only_observation_seed_packet_v1(valid_packet())

    assert result.accepted is True
    assert result.errors == ()


def test_rejects_each_missing_required_seed_packet_section() -> None:
    for field_name in (
        "post_decision_smoke_replay_references",
        "official_devhub_guidance_placeholders",
        "attended_read_only_observation_targets",
        "authorization_prerequisites",
        "redaction_expectations",
        "fixture_only_capture_schema_updates",
        "unsupported_manual_handoff_reminders",
        "rollback_notes",
        "reviewer_routing",
        "validation_commands",
    ):
        packet = valid_packet()
        packet[field_name] = []

        result = validate_next_devhub_read_only_observation_seed_packet_v1(packet)

        assert result.accepted is False
        assert any(field_name in error for error in result.errors)


@pytest.mark.parametrize(
    ("field_name", "bad_value", "expected_term"),
    [
        ("capture", "storage_state path was saved", "storage_state"),
        ("evidence", "screenshot captured after login", "screenshot captured"),
        ("evidence", "trace captured for review", "trace captured"),
        ("evidence", "HAR captured for replay", "har captured"),
        ("claim", "live DevHub interaction succeeded", "live devhub interaction"),
        ("claim", "form-fill completed", "form_fill"),
        ("claim", "submitted application", "submitted application"),
        ("claim", "legal guarantee for permit approval", "legal guarantee"),
        ("next_action", "pay fee", "pay fee"),
    ],
)
def test_rejects_private_artifacts_and_prohibited_claims(
    field_name: str, bad_value: str, expected_term: str
) -> None:
    packet = valid_packet()
    packet[field_name] = bad_value

    result = validate_next_devhub_read_only_observation_seed_packet_v1(packet)

    assert result.accepted is False
    assert any(expected_term in error for error in result.errors)


@pytest.mark.parametrize(
    "flag_name",
    [
        "active_mutation",
        "allow_live_mutation",
        "can_submit",
        "can_upload",
        "form_fill_enabled",
        "live_write_enabled",
        "mutation_enabled",
        "official_action_enabled",
        "write_enabled",
    ],
)
def test_rejects_truthy_active_mutation_flags(flag_name: str) -> None:
    packet = valid_packet()
    packet[flag_name] = True

    result = validate_next_devhub_read_only_observation_seed_packet_v1(packet)

    assert result.accepted is False
    assert any(flag_name in error for error in result.errors)


def test_rejects_malformed_validation_commands() -> None:
    packet = valid_packet()
    packet["validation_commands"] = [["python3", ""], "python3 ppd/daemon/ppd_daemon.py --self-test"]

    result = validate_next_devhub_read_only_observation_seed_packet_v1(packet)

    assert result.accepted is False
    assert any("validation_commands[0]" in error for error in result.errors)
    assert any("validation_commands[1]" in error for error in result.errors)


def test_assert_helper_raises_with_validation_details() -> None:
    packet = valid_packet()
    packet["version"] = "wrong-version"

    with pytest.raises(ValueError, match="version must be"):
        assert_next_devhub_read_only_observation_seed_packet_v1(packet)
