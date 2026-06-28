from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ppd.user_handoff_checklist import (
    assert_valid_user_handoff_checklist_packet,
    build_user_handoff_checklist_packet,
    validate_user_handoff_checklist_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures"
RELEASE_NOTES_PATH = FIXTURE_DIR / "safe_next_action_packet" / "expected.json"
RELEASE_GATE_PATH = FIXTURE_DIR / "release_gate_status" / "status_packet.json"
SURFACE_CANDIDATE_PATH = FIXTURE_DIR / "devhub_surface_registry_update_candidate" / "surface_registry_update_candidate_packet.json"
HANDOFF_PACKET_PATH = FIXTURE_DIR / "user_handoff_checklist" / "user_handoff_checklist_packet.json"


def _read(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _source_packets() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    return _read(RELEASE_NOTES_PATH), _read(RELEASE_GATE_PATH), _read(SURFACE_CANDIDATE_PATH)


def test_fixture_user_handoff_checklist_packet_is_valid() -> None:
    packet = _read(HANDOFF_PACKET_PATH)

    assert validate_user_handoff_checklist_packet(packet) == ()
    assert_valid_user_handoff_checklist_packet(packet)
    assert packet["offline_only"] is True
    assert packet["llm_invoked"] is False
    assert packet["launches_devhub"] is False
    assert packet["reads_private_files"] is False
    assert packet["prerequisite_packet_links"]


def test_builder_consumes_release_gate_release_notes_and_surface_candidate() -> None:
    release_notes, release_gate, surface_candidate = _source_packets()

    packet = build_user_handoff_checklist_packet(release_notes, release_gate, surface_candidate)

    sources = packet["source_packets"]
    assert sources["agent_safe_next_action_release_notes"]["consumed"] is True
    assert sources["release_gate_status"]["packet_id"] == "ppd-release-gate-status-synthetic-v1"
    assert sources["devhub_surface_registry_update_candidate"]["packet_id"] == "devhub-surface-registry-update-candidate-synthetic-v1"
    assert packet["prerequisite_packet_links"]
    assert packet["cited_offline_user_prompts"]
    assert packet["allowed_reversible_local_previews"]
    assert packet["blocked_consequential_actions"]
    assert packet["reviewer_prompts"]
    assert packet["rollback_references"]
    assert validate_user_handoff_checklist_packet(packet) == ()


def test_allowed_previews_are_reversible_local_only_and_cited() -> None:
    packet = build_user_handoff_checklist_packet(*_source_packets())

    for preview in packet["allowed_reversible_local_previews"]:
        assert preview["local_only"] is True
        assert preview["reversible"] is True
        assert preview["network_allowed"] is False
        assert preview["devhub_launch_allowed"] is False
        assert preview["official_action_allowed"] is False
        assert preview["citations"]


def test_blocks_consequential_release_gate_and_devhub_surface_actions() -> None:
    packet = build_user_handoff_checklist_packet(*_source_packets())
    blocked = {action["action_id"]: action for action in packet["blocked_consequential_actions"]}

    assert blocked["permit_submission"]["enabled"] is False
    assert blocked["fee_payment"]["blocked"] is True
    assert blocked["devhub_home_redacted:submit"]["enabled"] is False
    assert blocked["devhub_permit_detail_redacted:pay-fee"]["requires_attended_user_confirmation"] is True


def test_rejects_missing_prerequisite_links() -> None:
    packet = build_user_handoff_checklist_packet(*_source_packets())
    packet["prerequisite_packet_links"] = []

    assert "prerequisite_packet_links must be non-empty" in validate_user_handoff_checklist_packet(packet)


def test_rejects_prerequisite_links_outside_ppd_fixtures() -> None:
    packet = build_user_handoff_checklist_packet(*_source_packets())
    packet["prerequisite_packet_links"][0]["path"] = "tests/fixtures/private-session.json"

    errors = validate_user_handoff_checklist_packet(packet)

    assert "prerequisite_packet_links[0].path must point at a committed ppd/tests/fixtures fixture" in errors


def test_rejects_uncited_user_prompts_and_enabled_blocked_actions() -> None:
    packet = build_user_handoff_checklist_packet(*_source_packets())
    broken = deepcopy(packet)
    broken["cited_offline_user_prompts"][0]["citations"] = []
    broken["blocked_consequential_actions"][0]["enabled"] = True

    errors = validate_user_handoff_checklist_packet(broken)

    assert "cited_offline_user_prompts[0].citations must be non-empty" in errors
    assert "blocked_consequential_actions[0].enabled must be false" in errors


@pytest.mark.parametrize("forbidden_key", ["auth_state", "screenshot", "raw_html", "payment_details", "archive_artifact_ref", "downloaded_file"])
def test_rejects_private_browser_raw_or_download_artifact_fields(forbidden_key: str) -> None:
    packet = build_user_handoff_checklist_packet(*_source_packets())
    packet[forbidden_key] = "not allowed"

    assert any(forbidden_key in error for error in validate_user_handoff_checklist_packet(packet))


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("legal_summary", "This guarantees permit approval after submission.", "must not guarantee legal, permitting, inspection, approval, or issuance outcomes"),
        ("crawl_note", "The raw crawl archive artifact is available as page.warc.gz.", "must not reference raw crawl, download, or archive artifacts"),
        ("live_note", "Network requests were made and DevHub was launched.", "must not claim live network, DevHub, or Playwright execution"),
    ],
)
def test_rejects_outcome_guarantees_raw_artifacts_and_live_execution_claims(field: str, value: str, expected: str) -> None:
    packet = build_user_handoff_checklist_packet(*_source_packets())
    packet[field] = value

    errors = validate_user_handoff_checklist_packet(packet)

    assert any(expected in error for error in errors)


def test_rejects_live_execution_booleans() -> None:
    packet = build_user_handoff_checklist_packet(*_source_packets())
    packet["network_requests_made"] = True
    packet["allowed_reversible_local_previews"][0]["devhub_launch_allowed"] = True

    errors = validate_user_handoff_checklist_packet(packet)

    assert "network_requests_made must be false" in errors
    assert any("must not claim live network, DevHub, Playwright, or official action execution" in error for error in errors)


@pytest.mark.parametrize("capability_id", ["fee_payment", "official_upload", "permit_submission", "inspection_scheduling", "cancellation_or_withdrawal", "certification"])
def test_rejects_enabled_payment_upload_submission_scheduling_cancellation_or_certification(capability_id: str) -> None:
    packet = build_user_handoff_checklist_packet(*_source_packets())
    packet["extra_capabilities"] = [{"capability_id": capability_id, "enabled": True, "blocked": False, "citations": ["ev-consequential-actions-blocked"]}]

    errors = validate_user_handoff_checklist_packet(packet)

    assert any("enabled must be false for payment, upload, submission, scheduling, cancellation, and certification capabilities" in error for error in errors)
    assert any("blocked must not be false for consequential capabilities" in error for error in errors)


def test_rejects_production_ready_labels_while_blockers_remain_open() -> None:
    packet = build_user_handoff_checklist_packet(*_source_packets())
    packet["production_ready"] = True
    packet["open_blockers"] = [{"blocker_id": "block-live-review", "status": "open"}]

    errors = validate_user_handoff_checklist_packet(packet)

    assert "production-ready labels are not allowed while handoff blockers remain open" in errors
