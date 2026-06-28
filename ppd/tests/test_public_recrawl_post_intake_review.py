from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from ppd.extraction.public_recrawl_post_intake_review import (
    build_post_intake_review_packet,
    validate_post_intake_review_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_recrawl_post_intake_review"


def _load_fixture(name: str):
    with (FIXTURE_DIR / name).open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def _valid_packet():
    return build_post_intake_review_packet(
        _load_fixture("intake_reconciliation_packet.json"),
        _load_fixture("freshness_badges.json"),
    )


def _errors_for(packet):
    return validate_post_intake_review_packet(packet).errors


def test_public_recrawl_post_intake_review_packet_is_side_effect_free_and_valid():
    packet = _valid_packet()

    assert packet["packet_type"] == "public_recrawl_post_intake_review"
    assert packet["side_effect_policy"] == {
        "fetch_urls": False,
        "invoke_processors": False,
        "write_archive_artifacts": False,
        "source_registry_mutation": False,
        "archive_manifest_mutation": False,
        "source": "fixture_or_precomputed_metadata_only",
    }
    assert packet["input_packet_ids"] == {
        "intake_reconciliation_packet_id": "public-recrawl-intake-reconciliation-2026-05-29-fixture",
        "freshness_badges_packet_id": "source-evidence-freshness-badges-2026-05-29-fixture",
    }
    assert _errors_for(packet) == []


def test_public_recrawl_post_intake_review_triages_changed_sources_and_freshness():
    packet = _valid_packet()
    decisions = {item["source_id"]: item for item in packet["source_level_triage_decisions"]}

    assert decisions["ppd-devhub-faq"]["triage_decision"] == "changed_source_review"
    assert decisions["ppd-devhub-faq"]["review_required"] is True
    assert decisions["ppd-devhub-faq"]["reviewer_owner"] == "ppd-public-recrawl-reviewer"
    assert "content_hash_changed" in decisions["ppd-devhub-faq"]["reasons"]

    assert decisions["ppd-fee-payment-guide"]["triage_decision"] == "hold_for_senior_review"
    assert decisions["ppd-fee-payment-guide"]["freshness_status"] == "conflicting"

    assert decisions["ppd-submit-plans-online"]["triage_decision"] == "freshness_monitor"
    assert decisions["ppd-submit-plans-online"]["freshness_status"] == "stale"

    queues = packet["changed_source_reviewer_queues"]
    assert queues["changed_source_review"] == ["ppd-devhub-faq", "ppd-new-public-example"]
    assert queues["urgent_review"] == ["ppd-fee-payment-guide"]
    assert queues["freshness_monitor"] == ["ppd-submit-plans-online"]
    assert packet["changed_source_reviewer_queue_owners"]["urgent_review"] == {
        "ppd-fee-payment-guide": "ppd-senior-source-reviewer"
    }


def test_public_recrawl_post_intake_review_blocks_promotion_for_review_required_sources():
    packet = _valid_packet()

    blocker_pairs = {(item["source_id"], item["blocker_type"]) for item in packet["promotion_blockers"]}
    assert ("ppd-devhub-faq", "changed_source_review_required") in blocker_pairs
    assert ("ppd-new-public-example", "changed_source_review_required") in blocker_pairs
    assert ("ppd-fee-payment-guide", "senior_review_required") in blocker_pairs
    assert ("ppd-fee-payment-guide", "freshness_badge_not_current") in blocker_pairs
    assert ("ppd-submit-plans-online", "freshness_badge_not_current") in blocker_pairs
    assert all(item["reviewer_owner"] for item in packet["promotion_blockers"])
    assert packet["operator_abort_recommendations"] == []


@pytest.mark.parametrize(
    ("mutator", "expected"),
    [
        (
            lambda packet: packet["source_level_triage_decisions"][0].update({"source_evidence_ids": [], "citation_refs": []}),
            "must cite source_evidence_ids or citation_refs",
        ),
        (
            lambda packet: packet["source_level_triage_decisions"][0].update({"source_id": "unknown-source"}),
            "references an unknown source",
        ),
        (
            lambda packet: packet["source_level_triage_decisions"][0].update({"source_evidence_ids": ["unknown-evidence"]}),
            "references unknown evidence id",
        ),
        (
            lambda packet: packet["source_level_triage_decisions"][0].update({"raw_body": "raw"}),
            "raw body, download, or archive reference",
        ),
        (
            lambda packet: packet["source_level_triage_decisions"][0].update({"downloaded_document_path": "/tmp/fee.pdf"}),
            "raw body, download, or archive reference",
        ),
        (
            lambda packet: packet["source_level_triage_decisions"][0].update({"archive_artifact_ref": "warc://capture"}),
            "raw body, download, or archive reference",
        ),
        (
            lambda packet: packet["source_level_triage_decisions"][0].update({"canonical_url": "https://example.com/ppd"}),
            "allowlisted public URL",
        ),
        (
            lambda packet: packet["source_level_triage_decisions"][0].update({"canonical_url": "https://devhub.portlandoregon.gov/account"}),
            "allowlisted public URL",
        ),
        (
            lambda packet: packet["source_level_triage_decisions"][0].update({"source_type": "devhub_authenticated"}),
            "private or authenticated",
        ),
        (
            lambda packet: packet.update({"live_fetch_attempted": True}),
            "claims live fetch or processor execution",
        ),
        (
            lambda packet: packet.update({"processor_invoked": True}),
            "claims live fetch or processor execution",
        ),
        (
            lambda packet: packet.update({"source_registry_mutation_enabled": True}),
            "claims active source registry or archive mutation",
        ),
        (
            lambda packet: packet.update({"archive_artifact_written": True}),
            "claims active source registry or archive mutation",
        ),
        (
            lambda packet: packet.update({"promotion_blockers": []}),
            "requires at least one promotion blocker",
        ),
        (
            lambda packet: packet["source_level_triage_decisions"][0].update({"reviewer_owner": ""}),
            "reviewer_owner is required",
        ),
        (
            lambda packet: packet["changed_source_reviewer_queue_owners"]["changed_source_review"].pop("ppd-devhub-faq"),
            "changed_source_reviewer_queue_owners.changed_source_review.ppd-devhub-faq is required",
        ),
    ],
)
def test_public_recrawl_post_intake_review_validation_rejects_unsafe_packets(mutator, expected):
    packet = _valid_packet()
    mutator(packet)

    assert any(expected in error for error in _errors_for(packet))


def test_public_recrawl_post_intake_review_builder_rejects_unsafe_inputs():
    intake = _load_fixture("intake_reconciliation_packet.json")
    badges = _load_fixture("freshness_badges.json")
    unsafe_intake = deepcopy(intake)
    unsafe_intake["sources"][0]["live_fetch_attempted"] = True

    with pytest.raises(ValueError, match="live fetch or processor execution"):
        build_post_intake_review_packet(unsafe_intake, badges)
