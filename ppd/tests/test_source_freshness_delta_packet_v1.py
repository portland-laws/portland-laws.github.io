from __future__ import annotations

from pathlib import Path

import pytest

from ppd.source_freshness_delta_packet_v1 import (
    PACKET_VERSION,
    build_source_freshness_delta_packet_v1_from_fixture,
    require_valid_source_freshness_delta_packet_v1,
    validate_source_freshness_delta_packet_v1,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "source_freshness_delta_packet_v1" / "prior_current_rows.json"


def _packet() -> dict:
    return build_source_freshness_delta_packet_v1_from_fixture(FIXTURE_PATH)


def _codes(packet: dict) -> set[str]:
    return {issue.code for issue in validate_source_freshness_delta_packet_v1(packet)}


def test_builds_fixture_first_source_freshness_delta_packet_v1() -> None:
    packet = _packet()

    assert packet["packet_version"] == PACKET_VERSION
    assert packet["metadata_only"] is True
    assert packet["fixture_first"] is True
    assert packet["network_access_performed"] is False
    assert packet["raw_downloads_performed"] is False
    assert packet["processor_execution_performed"] is False
    assert packet["devhub_access_performed"] is False
    assert packet["official_action_completed"] is False
    assert packet["active_mutation_performed"] is False
    assert validate_source_freshness_delta_packet_v1(packet) == []


def test_compares_hashes_visible_dates_missing_rows_and_links() -> None:
    packet = _packet()
    by_kind = {}
    for delta in packet["source_deltas"]:
        by_kind.setdefault(delta["delta_kind"], []).append(delta)

    assert by_kind["changed_hash"][0]["source_id"] == "ppd-apply-permits"
    assert by_kind["visible_updated_date_changed"][0]["current_value"] == "2026-05-20"
    assert by_kind["missing_source_row"][0]["source_id"] == "ppd-retired-handout"
    assert by_kind["new_source_row"][0]["source_id"] == "ppd-new-devhub-guide"
    assert by_kind["new_official_link"][0]["current_value"] == "https://www.portland.gov/ppd/devhub-faqs"
    assert by_kind["removed_official_link"][0]["previous_value"] == "https://www.portland.gov/ppd/old-fee-help"


def test_requires_prior_current_hash_date_and_link_comparison_rows() -> None:
    packet = _packet()
    assert packet["source_row_sets"]["prior_source_rows"]
    assert packet["source_row_sets"]["current_source_rows"]
    assert packet["hash_comparisons"]
    assert packet["visible_date_comparisons"]
    assert packet["link_comparisons"]

    packet["source_row_sets"]["prior_source_rows"] = []
    packet["hash_comparisons"] = []
    packet["visible_date_comparisons"] = []
    packet["link_comparisons"] = []

    codes = _codes(packet)

    assert "prior_source_rows" in codes
    assert "hash_comparisons_source_ids" in codes
    assert "visible_date_comparisons_source_ids" in codes
    assert "link_comparison_source_ids" in codes
    assert "added_link_rows" in codes
    assert "removed_link_rows" in codes


def test_rejects_missing_required_delta_rows() -> None:
    packet = _packet()
    packet["source_deltas"] = [row for row in packet["source_deltas"] if row["delta_kind"] != "removed_official_link"]

    assert "required_delta_kind" in _codes(packet)


def test_recommends_reviewer_holds_for_changed_missing_and_link_delta_sources() -> None:
    packet = _packet()

    hold_source_ids = {row["source_id"] for row in packet["reviewer_hold_recommendations"]}

    assert hold_source_ids == {"ppd-apply-permits", "ppd-devhub-faq", "ppd-retired-handout"}
    assert all(row["allowed_next_step"] == "offline_reviewer_compare_public_metadata_fixture_only" for row in packet["reviewer_hold_recommendations"])


def test_rejects_missing_reviewer_holds_and_validation_commands() -> None:
    packet = _packet()
    packet["reviewer_hold_recommendations"] = []
    packet["offline_validation_commands"] = []

    codes = _codes(packet)

    assert "reviewer_hold_recommendations" in codes
    assert "offline_validation_commands" in codes


def test_rejects_private_session_browser_raw_or_downloaded_artifacts() -> None:
    packet = _packet()
    packet["session_file"] = ".auth/devhub.json"
    packet["browser_state"] = "state retained"
    packet["source_deltas"][0]["raw_body"] = "raw"
    packet["source_deltas"][1]["downloaded_document"] = "download.pdf"

    assert "forbidden_key" in _codes(packet)


def test_rejects_live_devhub_guarantee_official_action_and_active_mutation_claims() -> None:
    packet = _packet()
    packet["network_access_performed"] = True
    packet["devhub_access_performed"] = True
    packet["official_action_completed"] = True
    packet["reviewer_hold_recommendations"][0]["allowed_next_step"] = "live_crawl"
    packet["review_note"] = "permit issued with guaranteed legal compliance"
    packet["active_guardrail_mutation"] = True

    codes = _codes(packet)

    assert "network_access_performed" in codes
    assert "devhub_access_performed" in codes
    assert "official_action_completed" in codes
    assert "allowed_next_step" in codes
    assert "forbidden_text" in codes
    assert "active_mutation_flag" in codes


def test_rejects_private_or_authenticated_urls() -> None:
    packet = _packet()
    packet["source_deltas"][0]["canonical_url"] = "https://example.com/private"
    packet["source_deltas"][1]["current_value"] = "https://www.portland.gov/login?token=secret"

    codes = _codes(packet)

    assert "url_host" in codes
    assert "authenticated_url" in codes


def test_assert_raises_with_issue_codes() -> None:
    packet = _packet()
    packet["source_deltas"] = []

    with pytest.raises(ValueError, match="source_deltas"):
        require_valid_source_freshness_delta_packet_v1(packet)
