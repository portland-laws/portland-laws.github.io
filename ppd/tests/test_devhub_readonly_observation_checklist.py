from __future__ import annotations

from ppd.devhub_readonly_observation_checklist import (
    CHECKLIST_VERSION,
    PROHIBITED_FLAGS,
    REQUIRED_FIELDS,
    validate_devhub_readonly_observation_checklist,
)


def valid_packet() -> dict[str, object]:
    return {
        "checklist_version": CHECKLIST_VERSION,
        "seed_packet_references": ["ppd/tests/fixtures/devhub_readonly_observation/seed_packet.json"],
        "official_devhub_guidance_placeholders": ["Record official guidance URL and retrieval date before use."],
        "attendance_prerequisites": ["Human reviewer is present before login or observation."],
        "account_scope_reminders": ["Use only reviewer-approved account scope."],
        "readonly_route_expectations": ["Navigate read-only pages only; no submissions or mutations."],
        "manual_login_mfa_captcha_handoff_notes": ["Manual login, MFA, and CAPTCHA remain human-only handoffs."],
        "prohibited_capture_artifact_reminders": ["Do not save private sessions, auth state, screenshots, traces, or HAR files."],
        "redaction_acceptance_prerequisites": ["Reviewer must approve redaction rules before any observation notes are retained."],
        "reviewer_routing": ["Route packet to PP&D reviewer before use."],
        "rollback_notes": ["Discard observation packet if guidance, account scope, or reviewer approval changes."],
        "validation_commands": [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]],
    }


def test_valid_packet_passes() -> None:
    result = validate_devhub_readonly_observation_checklist(valid_packet())
    assert result.ok
    assert result.errors == ()


def test_required_items_are_rejected_when_missing_or_empty() -> None:
    for field in REQUIRED_FIELDS:
        packet = valid_packet()
        packet[field] = []

        result = validate_devhub_readonly_observation_checklist(packet)

        assert not result.ok
        assert f"missing required checklist item: {field}" in result.errors


def test_wrong_version_is_rejected() -> None:
    packet = valid_packet()
    packet["checklist_version"] = "devhub-readonly-observation-authorization-v0"

    result = validate_devhub_readonly_observation_checklist(packet)

    assert not result.ok
    assert f"checklist_version must be {CHECKLIST_VERSION!r}" in result.errors


def test_prohibited_flags_are_rejected_when_claimed() -> None:
    for field in PROHIBITED_FLAGS:
        packet = valid_packet()
        packet[field] = True

        result = validate_devhub_readonly_observation_checklist(packet)

        assert not result.ok
        assert f"prohibited checklist claim or artifact present: {field}" in result.errors


def test_absent_or_false_prohibited_flags_are_allowed() -> None:
    packet = valid_packet()
    for field in PROHIBITED_FLAGS:
        packet[field] = False

    result = validate_devhub_readonly_observation_checklist(packet)

    assert result.ok
