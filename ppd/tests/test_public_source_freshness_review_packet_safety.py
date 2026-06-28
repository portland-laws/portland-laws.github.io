from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.source_freshness.public_source_freshness_review_packet import (
    build_public_source_freshness_review_packet,
)
from ppd.source_freshness.public_source_freshness_review_packet_safety import (
    validate_public_source_freshness_review_packet_safety,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_source_freshness_review_packet" / "input.json"
GENERATED_AT = "2026-05-28T23:05:00Z"


def build_packet() -> dict:
    inputs = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return build_public_source_freshness_review_packet(
        inputs["public_source_monitoring_schedule_candidate"],
        inputs["post_release_audit_findings_packet"],
        generated_at=GENERATED_AT,
    )


def safety_errors(packet: dict) -> tuple[str, ...]:
    return validate_public_source_freshness_review_packet_safety(packet).errors


def test_accepts_fixture_built_public_source_freshness_review_packet() -> None:
    result = validate_public_source_freshness_review_packet_safety(build_packet())

    assert result.valid is True
    assert result.errors == ()


@pytest.mark.parametrize(
    "url",
    [
        "https://user:pass@www.portland.gov/ppd/devhub-faqs",
        "https://www.portland.gov/ppd/devhub-faqs?token=secret",
        "https://localhost/ppd/devhub-faqs",
        "https://127.0.0.1/ppd/devhub-faqs",
        "https://www.portland.gov/account/permits",
        "https://www.portland.gov/login",
    ],
)
def test_rejects_private_or_authenticated_urls(url: str) -> None:
    packet = build_packet()
    packet["review_source_url"] = url

    assert any("private or authenticated URLs" in error for error in safety_errors(packet))


def test_rejects_non_allowlisted_hosts() -> None:
    packet = build_packet()
    packet["review_source_url"] = "https://example.com/ppd/devhub-faqs"

    assert any("host is not allowlisted: example.com" in error for error in safety_errors(packet))


@pytest.mark.parametrize(
    "url",
    [
        "https://www.portland.gov/ppd/devhub-faqs/download/report",
        "https://www.portland.gov/ppd/devhub-faqs/archive/2025",
        "https://www.portland.gov/ppd/devhub-faqs/raw/body",
        "https://www.portland.gov/ppd/devhub-faqs/export/results.zip",
        "https://www.portland.gov/ppd/devhub-faqs/report.pdf",
    ],
)
def test_rejects_raw_body_download_archive_and_document_paths(url: str) -> None:
    packet = build_packet()
    packet["review_source_url"] = url

    assert any("raw body, download, archive" in error for error in safety_errors(packet))


def test_rejects_missing_source_ids() -> None:
    packet = build_packet()
    packet["source_ids"] = []

    assert "source_ids must be non-empty" in safety_errors(packet)


def test_rejects_missing_decision_source_id() -> None:
    packet = build_packet()
    packet["reviewer_owned_source_freshness_decisions"][0]["source_id"] = ""

    assert any(".source_id is required" in error for error in safety_errors(packet))


def test_rejects_missing_robots_or_policy_prerequisites() -> None:
    packet = build_packet()
    packet["packet_level_prerequisite_evidence_ids"] = ["robots-prereq-portland-gov-20260528"]
    packet["reviewer_owned_source_freshness_decisions"][0]["prerequisite_robots_policy_evidence_ids"] = [
        "robots-prereq-portland-gov-20260528"
    ]

    errors = safety_errors(packet)

    assert "packet_level_prerequisite_evidence_ids must include robots and policy prerequisites" in errors
    assert any("prerequisite_robots_policy_evidence_ids must include robots and policy" in error for error in errors)


def test_rejects_stale_source_marked_current_without_acknowledgement() -> None:
    packet = build_packet()
    packet["source_freshness_inputs"] = [
        {
            "source_id": "ppd-devhub-faq",
            "freshness_status": "current",
            "stale_by_cadence": True,
        }
    ]

    assert any("stale source current without stale_source_acknowledgement" in error for error in safety_errors(packet))


def test_accepts_stale_source_marked_current_with_review_acknowledgement() -> None:
    packet = build_packet()
    packet["source_freshness_inputs"] = [
        {
            "source_id": "ppd-devhub-faq",
            "freshness_status": "current",
            "stale_by_cadence": True,
            "stale_source_acknowledgement": {
                "acknowledgement_id": "stale-source-ack-ppd-devhub-faq",
                "acknowledgement_status": "acknowledged_for_review_only",
            },
        }
    ]

    assert validate_public_source_freshness_review_packet_safety(packet).valid is True


@pytest.mark.parametrize(
    "key",
    [
        "fetch_urls",
        "live_fetch",
        "live_network_execution",
        "network_invoked",
    ],
)
def test_rejects_live_fetch_claims(key: str) -> None:
    packet = build_packet()
    packet["execution_policy"] = copy.deepcopy(packet["execution_policy"])
    packet["execution_policy"][key] = True

    assert any("live fetching or network execution" in error for error in safety_errors(packet))


def test_rejects_missing_reviewer_owner() -> None:
    packet = build_packet()
    packet["reviewer_owned_source_freshness_decisions"][0]["reviewer_owner"] = ""

    assert any(".reviewer_owner is required" in error for error in safety_errors(packet))


@pytest.mark.parametrize(
    "key",
    [
        "active_schedule_mutation",
        "cron_enabled",
        "schedule_mutation_enabled",
        "writes_live_schedule",
    ],
)
def test_rejects_active_schedule_mutation_flags(key: str) -> None:
    packet = build_packet()
    packet["schedule_mutation_outcome"][key] = True

    assert any("active schedule mutation" in error for error in safety_errors(packet))
