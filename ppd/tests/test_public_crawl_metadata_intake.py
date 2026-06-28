from __future__ import annotations

import json
from pathlib import Path

from ppd.crawler.public_crawl_metadata_intake import (
    validate_public_crawl_metadata_dry_run_intake,
    validate_public_crawl_metadata_dry_run_intake_dict,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_crawl_metadata_intake"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def codes(packet: dict) -> set[str]:
    return {violation.code for violation in validate_public_crawl_metadata_dry_run_intake(packet)}


def test_accepts_public_allowlisted_dry_run_metadata_packet() -> None:
    result = validate_public_crawl_metadata_dry_run_intake_dict(load_fixture("valid_packet.json"))

    assert result == {"accepted": True, "violations": []}


def test_rejects_private_or_authenticated_urls() -> None:
    packet = load_fixture("valid_packet.json")
    packet["requested_url"] = "https://devhub.portlandoregon.gov/account/my-permits?token=secret"

    assert "private_or_authenticated_url" in codes(packet)


def test_rejects_non_allowlisted_hosts() -> None:
    packet = load_fixture("valid_packet.json")
    packet["discovered_urls"].append("https://example.com/ppd")

    assert "non_allowlisted_host" in codes(packet)


def test_rejects_raw_body_download_archive_paths() -> None:
    packet = load_fixture("valid_packet.json")
    packet["artifacts"] = {
        "raw_body_path": "ppd/local/raw/body.html",
        "download_path": "ppd/local/downloads/form.pdf",
        "warc_path": "ppd/local/archive/capture.warc.gz",
    }

    assert "raw_artifact_path_forbidden" in codes(packet)


def test_rejects_missing_promotion_manifest_link() -> None:
    packet = load_fixture("valid_packet.json")
    del packet["promotion_manifest_url"]

    assert "missing_promotion_manifest" in codes(packet)


def test_rejects_missing_robots_or_policy_evidence() -> None:
    packet = load_fixture("valid_packet.json")
    packet["robots_evidence"] = []
    packet["policy_evidence"] = {}

    violation_codes = codes(packet)

    assert "missing_robots_evidence" in violation_codes
    assert "missing_policy_evidence" in violation_codes


def test_rejects_live_network_execution_claims() -> None:
    packet = load_fixture("valid_packet.json")
    packet["live_network_execution"] = True
    packet["notes"] = "Operator says real crawl completed during the dry run."

    assert "live_execution_claim_forbidden" in codes(packet)


def test_rejects_missing_abort_decision() -> None:
    packet = load_fixture("valid_packet.json")
    packet["abort_decision"] = {"reason": "review pending"}

    assert "missing_abort_decision" in codes(packet)


def test_rejects_real_crawl_or_download_completed_claims() -> None:
    packet = load_fixture("valid_packet.json")
    packet["crawl_completed"] = True
    packet["download_completed"] = "yes"

    assert "live_execution_claim_forbidden" in codes(packet)
