from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ppd.extraction.source_evidence_freshness_badges import (
    build_source_evidence_freshness_badge_packet,
    reject_source_evidence_freshness_badge_packet,
    validate_source_evidence_freshness_badge_packet,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "source_evidence_freshness_badges"
KNOWN_SOURCE_IDS = {
    "ppd-devhub-faq",
    "ppd-submit-plans-online",
    "ppd-file-naming-standards",
    "ppd-fee-payment-guide",
}
KNOWN_REQUIREMENT_IDS = {
    "req-devhub-account-services",
    "req-single-pdf-separate-documents",
    "req-file-name-format",
    "req-payment-final-submit-gate",
}
KNOWN_GUARDRAIL_IDS = {
    "guardrail-bundle-devhub-readonly",
    "guardrail-bundle-upload-staging",
    "guardrail-bundle-document-prep",
    "guardrail-bundle-payment",
}


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _badge_packet() -> dict:
    return build_source_evidence_freshness_badge_packet(
        _load_fixture("public_source_change_impact_triage_packet.json"),
        _load_fixture("public_source_to_guardrail_traceability_audit_packet.json"),
        generated_at="2026-05-29T00:00:00+00:00",
    )


def _codes(packet: dict) -> set[str]:
    return {
        finding.code
        for finding in validate_source_evidence_freshness_badge_packet(
            packet,
            known_source_ids=KNOWN_SOURCE_IDS,
            known_requirement_ids=KNOWN_REQUIREMENT_IDS,
            known_guardrail_bundle_ids=KNOWN_GUARDRAIL_IDS,
        )
    }


def test_builds_all_expected_badge_states_from_fixture_packets() -> None:
    badge_packet = _badge_packet()

    states_by_source = {
        candidate["source_id"]: candidate["badge_state"]
        for candidate in badge_packet["badge_candidates"]
    }

    assert badge_packet["packet_type"] == "source_evidence_freshness_badge_candidates"
    assert states_by_source == {
        "ppd-devhub-faq": "current",
        "ppd-submit-plans-online": "stale",
        "ppd-file-naming-standards": "needs-review",
        "ppd-fee-payment-guide": "deferred",
    }
    assert badge_packet["mutation_policy"] == {
        "mutates_requirements": False,
        "mutates_process_models": False,
        "mutates_guardrail_bundles": False,
        "mutates_source_registries": False,
    }


def test_badge_candidates_are_cited_and_guardrail_scoped() -> None:
    badge_packet = _badge_packet()

    stale_candidate = next(
        candidate
        for candidate in badge_packet["badge_candidates"]
        if candidate["source_id"] == "ppd-submit-plans-online"
    )

    assert stale_candidate["guardrail_bundle_id"] == "guardrail-bundle-upload-staging"
    assert stale_candidate["requirement_ids"] == ["req-single-pdf-separate-documents"]
    assert stale_candidate["affected_guardrail_bundle_ids"] == ["guardrail-bundle-upload-staging"]
    assert [citation["packet"] for citation in stale_candidate["citations"]] == [
        "public_source_change_impact_triage",
        "public_source_to_guardrail_traceability_audit",
    ]
    assert all(citation["canonical_url"] for citation in stale_candidate["citations"])


def test_builder_does_not_mutate_input_packets() -> None:
    triage_packet = _load_fixture("public_source_change_impact_triage_packet.json")
    traceability_packet = _load_fixture("public_source_to_guardrail_traceability_audit_packet.json")
    original_triage = deepcopy(triage_packet)
    original_traceability = deepcopy(traceability_packet)

    build_source_evidence_freshness_badge_packet(
        triage_packet,
        traceability_packet,
        generated_at="2026-05-29T00:00:00+00:00",
    )

    assert triage_packet == original_triage
    assert traceability_packet == original_traceability


def test_validator_accepts_fixture_backed_badge_packet() -> None:
    assert _codes(_badge_packet()) == set()


def test_validator_rejects_uncited_badge_decisions() -> None:
    packet = _badge_packet()
    packet["badge_candidates"][0]["citations"] = []

    assert "uncited_badge_decision" in _codes(packet)


def test_validator_rejects_unknown_source_requirement_and_guardrail_ids() -> None:
    packet = _badge_packet()
    packet["badge_candidates"][0]["source_id"] = "unknown-source"
    packet["badge_candidates"][0]["requirement_ids"] = ["unknown-requirement"]
    packet["badge_candidates"][0]["guardrail_bundle_id"] = "unknown-guardrail"

    codes = _codes(packet)

    assert "unknown_source_id" in codes
    assert "unknown_requirement_id" in codes
    assert "unknown_guardrail_id" in codes


def test_validator_rejects_stale_sources_marked_current_without_acknowledgement() -> None:
    packet = _badge_packet()
    candidate = packet["badge_candidates"][0]
    candidate["badge_state"] = "current"
    candidate["source_freshness_status"] = "stale"
    candidate["change_state"] = "changed"

    assert "stale_source_marked_current_without_acknowledgement" in _codes(packet)


def test_validator_allows_stale_sources_marked_current_with_acknowledgement() -> None:
    packet = _badge_packet()
    candidate = packet["badge_candidates"][0]
    candidate["badge_state"] = "current"
    candidate["source_freshness_status"] = "stale"
    candidate["change_state"] = "changed"
    candidate["stale_current_acknowledgement"] = {
        "acknowledged": True,
        "reviewer": "ppd-reviewer",
        "reason": "Fixture covers explicit human acknowledgement before preserving current badge.",
    }

    assert "stale_source_marked_current_without_acknowledgement" not in _codes(packet)


def test_validator_rejects_private_or_authenticated_urls() -> None:
    packet = _badge_packet()
    packet["badge_candidates"][0]["citations"][0]["canonical_url"] = (
        "https://devhub.portlandoregon.gov/account/permits/123"
    )
    packet["badge_candidates"][0]["citations"][0]["source_type"] = "devhub_authenticated"

    assert "private_or_authenticated_url" in _codes(packet)


def test_validator_rejects_raw_crawl_download_and_archive_references() -> None:
    packet = _badge_packet()
    packet["badge_candidates"][0]["raw_body_path"] = "/tmp/ppd/raw-crawl/devhub.html"
    packet["badge_candidates"][0]["download_path"] = "/home/user/Downloads/source.pdf"
    packet["badge_candidates"][0]["archive_artifact_ref"] = "archive://public-crawl/source.warc.gz"

    assert "raw_artifact_reference" in _codes(packet)


def test_validator_rejects_live_fetch_claims() -> None:
    packet = _badge_packet()
    packet["badge_candidates"][0]["live_fetch_claim"] = "Browser fetched this source live during badge review."

    assert "live_fetch_claim" in _codes(packet)


def test_validator_rejects_active_artifact_mutation_flags() -> None:
    packet = _badge_packet()
    packet["mutation_policy"]["mutates_guardrail_bundles"] = True
    packet["badge_candidates"][0]["mutates_active_artifacts"] = True

    assert "active_artifact_mutation" in _codes(packet)


def test_reject_helper_raises_with_finding_codes() -> None:
    packet = _badge_packet()
    packet["badge_candidates"][0]["citations"] = []

    with pytest.raises(ValueError, match="uncited_badge_decision"):
        reject_source_evidence_freshness_badge_packet(
            packet,
            known_source_ids=KNOWN_SOURCE_IDS,
            known_requirement_ids=KNOWN_REQUIREMENT_IDS,
            known_guardrail_bundle_ids=KNOWN_GUARDRAIL_IDS,
        )
