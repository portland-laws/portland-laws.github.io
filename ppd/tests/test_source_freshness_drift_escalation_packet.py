from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.source_freshness.source_freshness_drift_escalation_packet import (
    SourceFreshnessDriftEscalationPacketError,
    build_source_freshness_drift_escalation_packet,
    require_valid_source_freshness_drift_escalation_packet,
    validate_source_freshness_drift_escalation_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "source_freshness_drift_escalation_packet" / "input.json"


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _packet() -> dict:
    fixture = _fixture()
    return build_source_freshness_drift_escalation_packet(
        fixture["source_freshness_badge_packet"],
        fixture["public_source_refresh_intake_evidence_packet"],
        fixture["source_registry_update_candidate_packet"],
        generated_at="2026-05-29T12:00:00Z",
    )


def test_builds_fixture_first_drift_escalation_packet() -> None:
    packet = _packet()
    result = validate_source_freshness_drift_escalation_packet(packet)

    assert result.valid is True
    assert packet["packet_type"] == "ppd_source_freshness_drift_escalation_packet"
    assert packet["fixture_first"] is True
    assert packet["metadata_only"] is True
    assert packet["live_network_invoked"] is False
    assert packet["fetch_urls"] is False
    assert packet["processor_invoked"] is False
    assert packet["documents_downloaded"] is False
    assert packet["source_registry_mutated"] is False
    assert packet["escalation_summary"]["source_count"] == 2


def test_packet_contains_cited_stale_categories_reviewer_assignments_rerun_triggers_and_attestations() -> None:
    packet = _packet()

    categories = {row["source_id"]: row for row in packet["stale_source_categories"]}
    assignments = {row["source_id"]: row for row in packet["reviewer_owner_assignments"]}
    attestations = {row["source_id"]: row for row in packet["no_live_refresh_attestations"]}
    triggers = packet["expected_requirement_rerun_triggers"]

    devhub_category = categories["src-devhub-submit-permit-application-guide"]
    assert devhub_category["stale_source_category"] == "registry_metadata_changed"
    assert "registry_update_candidate_changed_fields" in devhub_category["category_reasons"]
    assert any(reason.startswith("freshness_badge_review_due_daily") for reason in devhub_category["category_reasons"])
    assert {citation["artifact_type"] for citation in devhub_category["citations"]} == {
        "source_freshness_badge_packet",
        "public_source_refresh_intake_evidence_packet",
        "source_registry_update_candidate_packet",
    }

    assert assignments["src-devhub-submit-permit-application-guide"]["reviewer_owner"] == "ppd-devhub-source-reviewer"
    assert assignments["src-ppd-forms-index"]["reviewer_owner"] == "ppd-forms-source-reviewer"
    assert triggers[0]["affected_requirement_ids"] == [
        "req-devhub-certification-gate",
        "req-devhub-dynamic-questions",
        "req-devhub-required-uploads",
    ]
    assert triggers[0]["expected_rerun_action"] == "rerun_requirement_and_guardrail_validation_after_reviewer_accepts_source_refresh"
    assert all(attestation["live_network_invoked"] is False for attestation in attestations.values())
    assert all(attestation["processor_invoked"] is False for attestation in attestations.values())
    assert all(attestation["documents_downloaded"] is False for attestation in attestations.values())
    assert all(attestation["source_registry_mutated"] is False for attestation in attestations.values())


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda packet: packet.update({"live_network_invoked": True}), "live_network_invoked must be false"),
        (lambda packet: packet.update({"fetch_urls": True}), "fetch_urls must be false"),
        (lambda packet: packet.update({"processor_invoked": True}), "processor_invoked must be false"),
        (lambda packet: packet.update({"processor_executed": True}), "processor_executed must be false"),
        (lambda packet: packet.update({"live_crawl_invoked": True}), "live_crawl_invoked must be false"),
        (lambda packet: packet.update({"documents_downloaded": True}), "documents_downloaded must be false"),
        (lambda packet: packet.update({"source_registry_mutated": True}), "source_registry_mutated must be false"),
        (lambda packet: packet.update({"active_source_registry_mutation_flags": True}), "active_source_registry_mutation_flags must be false"),
        (lambda packet: packet["stale_source_categories"][0].update({"citations": []}), "citations must not be empty"),
        (lambda packet: packet["stale_source_categories"][0].update({"reviewer_owner": ""}), "reviewer_owner is required"),
        (lambda packet: packet["stale_source_categories"][0].update({"canonical_url": "https://example.com/ppd"}), "non-allowlisted or private/authenticated URL"),
        (lambda packet: packet["stale_source_categories"][0].update({"canonical_url": "https://devhub.portlandoregon.gov/permit/private-case-123"}), "forbidden private or authenticated URL"),
        (lambda packet: packet["stale_source_categories"][0].update({"canonical_url": "https://www.portland.gov/ppd/documents/how-pay-fees/download"}), "forbidden raw, download, archive"),
        (lambda packet: packet["stale_source_categories"][0]["citations"][0].update({"artifact_type": "uncited_live_claim"}), "artifact_type is not an allowed fixture artifact"),
        (lambda packet: packet["stale_source_categories"][0]["citations"][0].update({"source_id": "different-source"}), "source_id must match stale source category"),
        (lambda packet: packet["reviewer_owner_assignments"][0].update({"reviewer_owner": ""}), "reviewer_owner is required"),
        (lambda packet: packet.update({"expected_requirement_rerun_triggers": []}), "expected_requirement_rerun_triggers must not be empty"),
        (lambda packet: packet["expected_requirement_rerun_triggers"][0].update({"citations": []}), "citations must not be empty"),
        (lambda packet: packet["expected_requirement_rerun_triggers"][0].update({"affected_requirement_ids": [], "affected_process_model_ids": [], "affected_guardrail_bundle_ids": []}), "must identify affected downstream ids"),
        (lambda packet: packet["no_live_refresh_attestations"][0].update({"live_network_invoked": True}), "live_network_invoked must be false"),
        (lambda packet: packet["no_live_refresh_attestations"][0].update({"processor_invoked": True}), "processor_invoked must be false"),
        (lambda packet: packet["no_live_refresh_attestations"][0].update({"citation_ids": []}), "citation_ids must not be empty"),
        (lambda packet: packet.update({"debug_path": "/tmp/ppd/raw-crawl/page.html"}), "forbidden raw, download, archive"),
        (lambda packet: packet.update({"archive_ref": "warc://public-crawl/source.warc.gz"}), "forbidden raw, download, archive"),
        (lambda packet: packet.update({"liveRefreshUsed": True}), "liveRefreshUsed must be false"),
        (lambda packet: packet.update({"registryUpdated": True}), "registryUpdated must be false"),
        (lambda packet: packet.update({"permittingOutcomeGuarantee": "permit will be approved"}), "legal or permitting outcome guarantees are not allowed"),
    ],
)
def test_drift_escalation_packet_rejects_unsafe_or_incomplete_mutations(mutation, expected: str) -> None:
    packet = copy.deepcopy(_packet())
    mutation(packet)

    with pytest.raises(SourceFreshnessDriftEscalationPacketError) as exc_info:
        require_valid_source_freshness_drift_escalation_packet(packet)

    assert expected in str(exc_info.value)


def test_packet_rejects_only_packet_level_placeholder_rerun_trigger() -> None:
    packet = copy.deepcopy(_packet())
    packet["expected_requirement_rerun_triggers"] = [
        {
            "trigger_id": "requirement-rerun-trigger-none-required",
            "source_id": "packet",
            "trigger_type": "no_registry_candidate_requirement_links",
            "affected_requirement_ids": [],
            "affected_process_model_ids": [],
            "affected_guardrail_bundle_ids": [],
            "expected_rerun_action": "no_requirement_rerun_until_registry_candidate_supplies_downstream_links",
            "reviewer_owner": "ppd-source-reviewer",
            "citations": [],
        }
    ]

    with pytest.raises(SourceFreshnessDriftEscalationPacketError) as exc_info:
        require_valid_source_freshness_drift_escalation_packet(packet)

    message = str(exc_info.value)
    assert "expected_requirement_rerun_triggers must include at least one source-specific rerun trigger" in message
    assert "citations must not be empty" in message


def test_builder_rejects_live_refresh_claims_in_inputs() -> None:
    fixture = _fixture()
    fixture["public_source_refresh_intake_evidence_packet"]["live_network_invoked"] = True

    with pytest.raises(SourceFreshnessDriftEscalationPacketError) as exc_info:
        build_source_freshness_drift_escalation_packet(
            fixture["source_freshness_badge_packet"],
            fixture["public_source_refresh_intake_evidence_packet"],
            fixture["source_registry_update_candidate_packet"],
        )

    assert "live_network_invoked" in str(exc_info.value)


def test_builder_rejects_registry_mutation_claims_in_inputs() -> None:
    fixture = _fixture()
    fixture["source_registry_update_candidate_packet"]["registryUpdated"] = True

    with pytest.raises(SourceFreshnessDriftEscalationPacketError) as exc_info:
        build_source_freshness_drift_escalation_packet(
            fixture["source_freshness_badge_packet"],
            fixture["public_source_refresh_intake_evidence_packet"],
            fixture["source_registry_update_candidate_packet"],
        )

    assert "registryUpdated must be false" in str(exc_info.value)
