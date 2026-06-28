from __future__ import annotations

import pytest

from ppd.logic.safe_next_action_release_notes import (
    assert_valid_release_notes_packet,
    validate_release_notes_packet,
)


def _base_packet() -> dict:
    return {
        "packet_type": "agent_safe_next_action_release_notes",
        "status": "blocked",
        "prerequisites": [
            {
                "label": "Confirm permit type guidance",
                "source_url": "https://www.portland.gov/ppd/get-permit/apply-permits",
            }
        ],
        "claims": [
            {
                "claim": "The next safe action is to review missing facts before drafting.",
                "user_facing": True,
                "source_evidence_ids": ["ppd-apply-permits"],
            }
        ],
        "capabilities": [
            {"name": "read status", "enabled": True},
            {"name": "submit application", "enabled": False},
        ],
        "blockers": ["User has not confirmed permit type."],
    }


def _codes(packet: dict) -> set[str]:
    return {issue.code for issue in validate_release_notes_packet(packet)}


def test_accepts_cited_blocked_read_only_packet() -> None:
    assert validate_release_notes_packet(_base_packet()) == []


def test_rejects_prerequisite_without_link() -> None:
    packet = _base_packet()
    packet["prerequisites"] = [{"label": "Confirm permit type guidance"}]

    assert "missing_prerequisite_link" in _codes(packet)


def test_rejects_uncited_user_facing_claim() -> None:
    packet = _base_packet()
    packet["claims"] = [{"claim": "The user can proceed with the next step.", "user_facing": True}]

    assert "uncited_user_facing_claim" in _codes(packet)


def test_rejects_legal_or_permitting_outcome_guarantee() -> None:
    packet = _base_packet()
    packet["claims"][0]["claim"] = "This package guarantees permit approval."

    assert "outcome_guarantee" in _codes(packet)


def test_rejects_private_session_artifacts() -> None:
    packet = _base_packet()
    packet["notes"] = "Validated using storage_state and a trace.zip artifact."

    assert "private_or_session_artifact" in _codes(packet)


def test_rejects_raw_crawl_download_archive_references() -> None:
    packet = _base_packet()
    packet["notes"] = "Evidence came from raw crawl output and a downloaded PDF."

    assert "raw_crawl_download_archive_reference" in _codes(packet)


def test_rejects_live_network_or_devhub_execution_claims() -> None:
    packet = _base_packet()
    packet["notes"] = "The agent logged in to DevHub and ran live browser execution."

    assert "live_network_or_devhub_execution_claim" in _codes(packet)


def test_rejects_boolean_live_execution_flags() -> None:
    packet = _base_packet()
    packet["live_network"] = True

    assert "live_network_or_devhub_execution_claim" in _codes(packet)


def test_rejects_production_ready_label_when_blockers_exist() -> None:
    packet = _base_packet()
    packet["status"] = "production-ready"

    assert "production_ready_with_blockers" in _codes(packet)


def test_rejects_enabled_payment_upload_submission_scheduling_cancellation_and_certification() -> None:
    forbidden_names = [
        "payment",
        "upload corrections",
        "submit application",
        "schedule inspection",
        "cancel permit",
        "certify acknowledgement",
    ]
    for name in forbidden_names:
        packet = _base_packet()
        packet["capabilities"] = [{"name": name, "enabled": True}]
        assert "enabled_consequential_capability" in _codes(packet), name


def test_rejects_enabled_consequential_boolean_fields() -> None:
    packet = _base_packet()
    packet["can_submit"] = True

    assert "enabled_consequential_capability" in _codes(packet)


def test_assert_valid_raises_with_issue_codes() -> None:
    packet = _base_packet()
    packet["can_pay"] = True

    with pytest.raises(ValueError, match="enabled_consequential_capability"):
        assert_valid_release_notes_packet(packet)
