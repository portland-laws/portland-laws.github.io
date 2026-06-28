from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ppd.extraction.public_source_change_impact_triage import (
    PublicSourceChangeImpactTriageValidationError,
    load_triage_packet,
    public_source_change_impact_triage_violations,
    triage_public_source_changes,
    validate_public_source_change_impact_triage_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_source_change_impact_triage"


def valid_packet() -> dict[str, object]:
    return load_triage_packet(FIXTURE_DIR / "packet.json")


def violation_codes(packet: dict[str, object]) -> set[str]:
    return {violation.code for violation in public_source_change_impact_triage_violations(packet)}


def test_fixture_first_triage_rolls_up_impacts_without_network_actions() -> None:
    packet = valid_packet()

    result = triage_public_source_changes(packet)

    assert result["packet_type"] == "public_source_change_impact_triage"
    assert result["mode"] == "fixture_first_offline"
    assert result["network_actions_performed"] is False
    assert result["active_guardrail_bundles_mutated"] is False
    assert result["monitoring_schedule_mutated"] is False

    records = {record["source_id"]: record for record in result["impact_records"]}
    submit_guide = records["src-devhub-submit-guide"]
    assert submit_guide["cited_source_ids"] == [
        "ev-devhub-submit-guide-acknowledgement",
        "ev-devhub-submit-guide-steps",
        "src-devhub-submit-guide",
    ]
    assert submit_guide["affected_requirement_ids"] == [
        "req-exact-confirmation-for-certification",
        "req-upload-staging-before-submit",
    ]
    assert submit_guide["affected_process_ids"] == ["process-building-permit-application"]
    assert submit_guide["affected_guardrail_bundle_ids"] == [
        "guardrail-building-permit-application"
    ]
    assert submit_guide["reviewer_owners"] == ["ppd-public-source-reviewer"]
    assert submit_guide["stale_source_acknowledgements"] == [
        "src-devhub-submit-guide:ppd-public-source-reviewer:source review is older than the monitoring cadence for DevHub submission guidance"
    ]
    assert (
        submit_guide["offline_triage_decision"]
        == "offline_review_required_before_guardrail_update"
    )
    assert "guardrail_bundles_affected_without_mutation" in submit_guide["decision_reasons"]


def test_schedule_only_source_keeps_guardrail_bundle_unmutated() -> None:
    packet = valid_packet()

    records = {
        record["source_id"]: record
        for record in triage_public_source_changes(packet)["impact_records"]
    }

    single_pdf = records["src-single-pdf-guidance"]
    assert single_pdf["affected_requirement_ids"] == ["req-plan-set-single-pdf"]
    assert single_pdf["affected_guardrail_bundle_ids"] == [
        "guardrail-document-preparation"
    ]
    assert single_pdf["stale_source_acknowledgements"] == []
    assert single_pdf["offline_triage_decision"] == "offline_triage_required"


def test_valid_packet_passes_explicit_validation() -> None:
    validate_public_source_change_impact_triage_packet(valid_packet())


@pytest.mark.parametrize(
    ("mutator", "expected_code"),
    [
        (
            lambda packet: packet.pop("prerequisite_links"),
            "missing_prerequisite_links",
        ),
        (
            lambda packet: packet["public_source_to_guardrail_traceability_audit"]["traceability"][0].pop("affected_id_citations"),
            "affected_ids_without_citations",
        ),
        (
            lambda packet: packet["public_source_to_guardrail_traceability_audit"]["traceability"][0]["requirement_ids"].append("req-unknown"),
            "unknown_requirement_id",
        ),
        (
            lambda packet: packet["public_source_to_guardrail_traceability_audit"]["traceability"][0]["process_ids"].append("process-unknown"),
            "unknown_process_id",
        ),
        (
            lambda packet: packet["public_source_to_guardrail_traceability_audit"]["traceability"][0]["guardrail_bundle_ids"].append("guardrail-unknown"),
            "unknown_guardrail_bundle_id",
        ),
        (
            lambda packet: packet["public_source_monitoring_schedule_candidate"]["candidates"][0].update({"source_id": "src-unknown"}),
            "unknown_source_id",
        ),
        (
            lambda packet: packet["public_source_monitoring_schedule_candidate"]["candidates"][0].update({"canonical_url": "https://devhub.portlandoregon.gov/my-permits?token=secret"}),
            "private_or_authenticated_url",
        ),
        (
            lambda packet: packet["public_source_monitoring_schedule_candidate"]["candidates"][0].update({"raw_body": "raw page body"}),
            "raw_body_download_or_archive_reference",
        ),
        (
            lambda packet: packet["public_source_monitoring_schedule_candidate"]["candidates"][0].update({"downloaded_path": "/home/user/Downloads/devhub.pdf"}),
            "private_or_downloaded_artifact_reference",
        ),
        (
            lambda packet: packet["public_source_monitoring_schedule_candidate"]["candidates"][0].update({"live_fetch_performed": True}),
            "live_fetch_or_crawl_claim",
        ),
        (
            lambda packet: packet["public_source_freshness_review"]["sources"][0].update({"acknowledgement_required": False, "acknowledgement_owner": "", "stale_reason": ""}),
            "stale_current_claim_without_acknowledgement",
        ),
        (
            lambda packet: packet["public_source_to_guardrail_traceability_audit"]["traceability"][0].update({"reviewer_owner": ""}),
            "missing_reviewer_owner",
        ),
        (
            lambda packet: packet["public_source_monitoring_schedule_candidate"]["candidates"][0].update({"schedule_mutation_requested": True}),
            "active_bundle_or_schedule_mutation_flag",
        ),
        (
            lambda packet: packet.update({"active_guardrail_bundles_mutated": True}),
            "active_bundle_or_schedule_mutation_flag",
        ),
    ],
)
def test_rejects_unsafe_triage_packet_patterns(mutator, expected_code: str) -> None:
    packet = deepcopy(valid_packet())
    mutator(packet)

    assert expected_code in violation_codes(packet)


def test_raises_with_all_violations_for_callers_that_need_fail_fast() -> None:
    packet = deepcopy(valid_packet())
    packet["public_source_to_guardrail_traceability_audit"]["traceability"][0][
        "affected_id_citations"
    ]["req-upload-staging-before-submit"] = ["ev-missing"]
    packet["public_source_monitoring_schedule_candidate"]["candidates"][0][
        "live_crawl_performed"
    ] = True

    with pytest.raises(PublicSourceChangeImpactTriageValidationError) as excinfo:
        validate_public_source_change_impact_triage_packet(packet)

    assert {violation.code for violation in excinfo.value.violations} == {
        "live_fetch_or_crawl_claim",
        "unknown_citation_source_id",
    }
