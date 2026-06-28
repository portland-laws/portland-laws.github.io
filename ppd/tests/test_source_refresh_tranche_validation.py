import copy

from ppd.source_refresh_tranche_validation import (
    require_public_source_refresh_tranche_proposal_packet,
    validate_public_source_refresh_tranche_proposal_packet,
)


def valid_packet() -> dict:
    return {
        "packet_type": "ppd_public_source_refresh_tranche_proposal",
        "packet_version": "1.0",
        "tranche_id": "public-source-refresh-tranche-fixture",
        "proposal_status": "metadata_only_review_required",
        "consumes_packet_ids": [
            "evidence-freshness-watchlist-reviewer-disposition-fixture",
            "source-registry-schedule-update-candidate-fixture",
            "source-refresh-runbook-candidate-fixture",
        ],
        "ordered_sources": [
            {
                "order_index": 1,
                "source_id": "ppd-online-permitting-tools",
                "canonical_url": "https://www.portland.gov/ppd/how-use-online-permitting-tools",
                "refresh_reason": "Public DevHub guidance is watched for action-boundary drift.",
                "proposed_frequency": "daily",
                "owner": "ppd-public-sources-owner",
                "reviewer": "ppd-freshness-reviewer",
                "source_evidence_refs": ["source-evidence://ppd-online-permitting-tools#reviewer-disposition"],
                "allowlist_evidence_ref": "allowlist://ppd-public-sources/portland-gov-hosts#www.portland.gov",
                "robots_evidence_ref": "robots://www.portland.gov/robots.txt#fixture-reviewed",
                "abort_criteria": [
                    "Abort if host is not present in the committed public-source allowlist evidence reference.",
                    "Abort if robots evidence is missing, stale, or records a disallow decision for the proposed path.",
                ],
                "runbook_step_refs": ["runbook://public-source-refresh/preflight-only"],
            },
            {
                "order_index": 2,
                "source_id": "ppd-devhub-faqs",
                "canonical_url": "https://www.portland.gov/ppd/devhub-faqs",
                "refresh_reason": "FAQ content is watched for authenticated workflow boundary drift.",
                "proposed_frequency": "daily",
                "owner": "ppd-devhub-public-owner",
                "reviewer": "ppd-freshness-reviewer",
                "source_evidence_refs": ["source-evidence://ppd-devhub-faqs#reviewer-disposition"],
                "allowlist_evidence_ref": "allowlist://ppd-public-sources/portland-gov-hosts#www.portland.gov",
                "robots_evidence_ref": "robots://www.portland.gov/robots.txt#fixture-reviewed",
                "abort_criteria": ["Abort if FAQ links require sign-in or account-scoped state to inspect."],
                "runbook_step_refs": ["runbook://public-source-refresh/action-boundary-review"],
            },
        ],
        "attestations": {
            "no_fetch_performed": True,
            "no_download_performed": True,
            "no_processor_invoked": True,
            "no_schedule_mutation_performed": True,
        },
        "reviewer_owner_fields_required": True,
    }


def codes(packet: dict) -> tuple[str, ...]:
    return validate_public_source_refresh_tranche_proposal_packet(packet).codes()


def test_accepts_valid_metadata_only_public_source_refresh_tranche_proposal() -> None:
    packet = valid_packet()

    result = validate_public_source_refresh_tranche_proposal_packet(packet)

    assert result.valid
    require_public_source_refresh_tranche_proposal_packet(packet)


def test_rejects_unordered_or_uncited_source_entries() -> None:
    packet = valid_packet()
    packet["ordered_sources"][1]["order_index"] = 3
    packet["ordered_sources"][0]["source_evidence_refs"] = []

    assert "unordered_source_entry" in codes(packet)
    assert "uncited_source_entry" in codes(packet)


def test_rejects_missing_allowlist_robots_abort_and_reviewer_owners() -> None:
    packet = valid_packet()
    source = packet["ordered_sources"][0]
    source["allowlist_evidence_ref"] = ""
    source["robots_evidence_ref"] = ""
    source["abort_criteria"] = []
    source["owner"] = ""
    source["reviewer"] = ""

    result_codes = codes(packet)

    assert "missing_allowlist_evidence" in result_codes
    assert "missing_robots_evidence" in result_codes
    assert "missing_abort_criteria" in result_codes
    assert "missing_reviewer_owners" in result_codes


def test_rejects_non_allowlisted_authenticated_download_and_archive_urls() -> None:
    packets = []
    for url in (
        "https://example.com/ppd/how-use-online-permitting-tools",
        "https://devhub.portlandoregon.gov/login",
        "https://www.portland.gov/ppd/documents/how-pay-fees/download",
        "https://www.portland.gov/ppd/archive/source.warc",
    ):
        packet = valid_packet()
        packet["ordered_sources"][0]["canonical_url"] = url
        packets.append(packet)

    assert "non_allowlisted_url" in codes(packets[0])
    assert "authenticated_url" in codes(packets[1])
    assert "raw_download_archive_reference" in codes(packets[2])
    assert "raw_download_archive_reference" in codes(packets[3])


def test_rejects_raw_body_download_archive_fields() -> None:
    packet = valid_packet()
    packet["raw_body"] = "raw source body"
    packet["download_path"] = "/tmp/source.pdf"
    packet["archive_url"] = "https://www.portland.gov/archive/source.warc"

    assert "raw_download_archive_reference" in codes(packet)


def test_rejects_live_execution_claims_outcome_guarantees_and_mutation_flags() -> None:
    packet = valid_packet()
    packet["review_notes"] = "The live crawl ran and the processor executed successfully. The permit will be approved."
    packet["live_schedule_mutated"] = True
    packet["registry_mutation_enabled"] = True

    result_codes = codes(packet)

    assert "live_crawl_or_processor_execution_claim" in result_codes
    assert "legal_or_permitting_outcome_guarantee" in result_codes
    assert "active_registry_or_schedule_mutation" in result_codes


def test_rejects_missing_no_execution_attestations() -> None:
    packet = copy.deepcopy(valid_packet())
    packet["attestations"]["no_processor_invoked"] = False

    assert "missing_no_execution_attestation" in codes(packet)
