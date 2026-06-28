from __future__ import annotations

from pathlib import Path

import pytest

from ppd.public_refresh_preflight import PreflightError, assemble_preflight, load_packet


FIXTURE = Path(__file__).parent / "fixtures" / "public_refresh_preflight" / "synthetic_next_public_refresh_seed_review_packet_v1.json"


def test_assembles_fixture_first_public_refresh_preflight() -> None:
    checklist = assemble_preflight(load_packet(FIXTURE))

    assert checklist["checklist_version"] == "public-refresh-preflight-v1"
    assert checklist["offline_only"] is True
    assert "live crawling" in checklist["input_policy"]["prohibited_actions"]
    assert "document downloads" in checklist["input_policy"]["prohibited_actions"]
    assert "raw output storage" in checklist["input_policy"]["prohibited_actions"]
    assert "DevHub opening" in checklist["input_policy"]["prohibited_actions"]
    assert "release activation" in checklist["input_policy"]["prohibited_actions"]

    seeds = checklist["seeds"]
    assert [seed["seed_id"] for seed in seeds] == [
        "ppd-permit-search-index-placeholder",
        "ppd-code-guide-placeholder",
    ]
    assert seeds[0]["allowlist_decision"] == "allow"
    assert seeds[1]["allowlist_decision"] == "skip"

    for seed in seeds:
        assert set(seed["request_method_limits"]).issubset({"GET", "HEAD"})
        assert seed["archive_manifest_expectation"]["metadata_only"] is True
        assert seed["archive_manifest_expectation"]["raw_document_storage"] is False
        assert seed["skip_reason_expectation"]
        assert seed["reviewer_routing"]
        assert seed["rollback_note"]
        assert seed["robots_check"]["offline_note"].startswith("Expectation is reviewed from fixture text only")
        assert seed["source_anchor_placeholders"][0]["kind"] == "official_source_anchor_placeholder"

    assert ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"] in checklist["validation_commands"]


def test_rejects_live_or_raw_artifact_fields() -> None:
    packet = load_packet(FIXTURE)
    packet["rows"][0]["raw_output"] = "not allowed"

    with pytest.raises(PreflightError, match="prohibited keys"):
        assemble_preflight(packet)


def test_rejects_methods_beyond_get_and_head() -> None:
    packet = load_packet(FIXTURE)
    packet["rows"][0]["request_methods"] = ["POST"]

    with pytest.raises(PreflightError, match="request method is not allowed"):
        assemble_preflight(packet)


def test_rejects_non_metadata_archive_manifest() -> None:
    packet = load_packet(FIXTURE)
    packet["rows"][0]["archive_manifest_expectation"]["metadata_only"] = False

    with pytest.raises(PreflightError, match="metadata-only"):
        assemble_preflight(packet)
