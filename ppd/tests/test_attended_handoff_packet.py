from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.devhub.handoff_packet import HandoffPacketError, normalize_attended_handoff_packet_dict


_FIXTURE = Path(__file__).parent / "fixtures" / "devhub" / "attended_handoff_packet_minimal.json"


def _fixture_packet() -> dict[str, object]:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def test_normalizes_minimal_attended_handoff_packet() -> None:
    normalized = normalize_attended_handoff_packet_dict(_fixture_packet())

    assert normalized == {
        "task_id": "supervisor-20260512-029",
        "handoff_reason": "User must complete DevHub sign-in and review the next account-scoped page before automation continues.",
        "attendance_required": True,
        "source_url": "https://devhub.portlandoregon.gov/",
        "page_title": "DevHub",
        "visible_headings": ["DevHub"],
        "required_user_actions": [
            "Complete PortlandOregon.gov sign-in manually if prompted",
            "Confirm the visible DevHub page before any draft assistance continues",
        ],
        "safe_next_actions": [
            "Record redacted page title and headings",
            "Review public guidance citations for the next reversible draft step",
        ],
        "blocked_actions": [
            "Do not submit applications",
            "Do not upload documents",
            "Do not certify acknowledgements",
            "Do not enter or submit payment details",
        ],
        "evidence_refs": [
            "https://www.portland.gov/ppd/devhub-sign-guide",
            "https://www.portland.gov/ppd/how-use-online-permitting-tools",
        ],
        "warnings": [
            "No credentials, cookies, screenshots, traces, HAR files, browser storage, or private form values may be stored."
        ],
    }


def test_rejects_session_state_material() -> None:
    packet = _fixture_packet()
    packet["storageState"] = {"cookies": []}

    with pytest.raises(HandoffPacketError, match="private session material"):
        normalize_attended_handoff_packet_dict(packet)


def test_rejects_browser_actions() -> None:
    packet = _fixture_packet()
    packet["browser_actions"] = [{"click": "Sign In/Register"}]

    with pytest.raises(HandoffPacketError, match="browser actions"):
        normalize_attended_handoff_packet_dict(packet)


def test_rejects_unattended_packet() -> None:
    packet = _fixture_packet()
    packet["attendance_required"] = False

    with pytest.raises(HandoffPacketError, match="require user attendance"):
        normalize_attended_handoff_packet_dict(packet)


def test_rejects_consequential_safe_next_action() -> None:
    packet = _fixture_packet()
    packet["safe_next_actions"] = ["Submit permit application"]

    with pytest.raises(HandoffPacketError, match="consequential official actions"):
        normalize_attended_handoff_packet_dict(packet)


def test_rejects_local_private_paths() -> None:
    packet = _fixture_packet()
    packet["warnings"] = ["Read /home/example/private-upload.pdf"]

    with pytest.raises(HandoffPacketError, match="local private path"):
        normalize_attended_handoff_packet_dict(packet)
