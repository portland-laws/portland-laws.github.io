from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ppd.public_data_dry_run_release_packet import (
    FORBIDDEN_CAPABILITIES,
    REQUIRED_CHECKLIST_SECTIONS,
    REQUIRED_OUTPUT_TYPES,
    assert_public_data_dry_run_release_packet,
    build_public_data_dry_run_release_packet,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_data_dry_run_release_packet" / "release_packet.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def assert_rejected(packet: dict, expected: str) -> None:
    with pytest.raises(ValueError) as excinfo:
        build_public_data_dry_run_release_packet(packet)
    assert expected in str(excinfo.value)


def test_public_data_dry_run_release_packet_links_required_outputs_into_operator_checklist() -> None:
    packet = assert_public_data_dry_run_release_packet(load_fixture())

    assert packet.packet_id == "fixture-ppd-public-data-dry-run-release-2026-05-28"
    assert set(packet.output_types) == set(REQUIRED_OUTPUT_TYPES)
    assert set(packet.checklist_sections) == set(REQUIRED_CHECKLIST_SECTIONS)
    assert packet.ready_for_live_release is False
    assert set(packet.disabled_capabilities) == set(FORBIDDEN_CAPABILITIES)


def test_public_data_dry_run_release_packet_keeps_all_consequential_capabilities_disabled() -> None:
    packet = load_fixture()
    summary = build_public_data_dry_run_release_packet(packet)

    assert summary.ready_for_live_release is False
    for capability in FORBIDDEN_CAPABILITIES:
        assert packet["disabled_capabilities"][capability] is True
        assert packet["consequential_action_boundary"][capability] in {
            "blocked",
            "manual_handoff",
            "not_enabled",
            "not_ready",
            "refused",
        }


def test_public_data_dry_run_release_packet_rejects_missing_linked_output() -> None:
    packet = load_fixture()
    packet["linked_outputs"] = [
        output for output in packet["linked_outputs"] if output["output_type"] != "guardrail_candidate"
    ]

    assert_rejected(packet, "missing linked output: guardrail_candidate")


def test_public_data_dry_run_release_packet_rejects_live_execution_flags() -> None:
    packet = load_fixture()
    packet["ready_for_live_release"] = True
    packet["disabled_capabilities"]["live_crawl"] = False
    packet["linked_outputs"][0]["enables_live_execution"] = True

    assert_rejected(packet, "ready_for_live_release must remain false")
    assert_rejected(packet, "disabled_capabilities.live_crawl must be true")
    assert_rejected(packet, "linked_outputs[0].enables_live_execution must be false")


def test_public_data_dry_run_release_packet_rejects_private_artifacts_and_raw_bodies() -> None:
    packet = load_fixture()
    packet["linked_outputs"][0]["local_path"] = "/home/user/private/devhub.pdf"
    packet["linked_outputs"][1]["raw_html"] = "raw page body"

    assert_rejected(packet, "private value field is not allowed")
    assert_rejected(packet, "raw body field is not allowed")


def test_public_data_dry_run_release_packet_rejects_operator_checklist_execution() -> None:
    packet = deepcopy(load_fixture())
    packet["operator_review_checklist"][0]["agent_may_execute"] = True
    packet["operator_review_checklist"][1]["decision"] = "ready_for_submission"

    assert_rejected(packet, "operator_review_checklist[0].agent_may_execute must be false")
    assert_rejected(packet, "operator_review_checklist[1].decision cannot enable consequential work")
