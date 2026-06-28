from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.crawler.public_source_refresh_dry_run_acceptance_checklist import (
    PublicSourceRefreshDryRunAcceptanceChecklistError,
    build_public_source_refresh_dry_run_acceptance_checklist_packet,
    require_public_source_refresh_dry_run_acceptance_checklist_packet,
    validate_public_source_refresh_dry_run_acceptance_checklist_packet,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "public_source_refresh_dry_run_acceptance_checklist"
    / "input_packets.json"
)


def _fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _issue_codes(packet: dict[str, object]) -> set[str]:
    return set(validate_public_source_refresh_dry_run_acceptance_checklist_packet(packet))


def test_builds_fixture_first_public_source_refresh_dry_run_acceptance_checklist() -> None:
    packet = build_public_source_refresh_dry_run_acceptance_checklist_packet(_fixture())

    require_public_source_refresh_dry_run_acceptance_checklist_packet(packet)
    assert packet["packet_type"] == "ppd_public_source_refresh_dry_run_acceptance_checklist"
    assert packet["mode"] == "fixture_first_metadata_only_acceptance"
    assert [gate["order"] for gate in packet["preflight_gates"]] == [1, 2, 3, 4]
    assert [check["source_id"] for check in packet["per_source_abort_checks"]] == [
        "ppd-online-tools",
        "devhub-faq",
    ]
    assert packet["reviewer_owner_fields"] == {
        "reviewer": "ppd-refresh-reviewer",
        "owner": "ppd-refresh-owner",
    }
    assert packet["attestations"] == {
        "no_fetch": True,
        "no_download": True,
        "no_processor": True,
        "no_registry_mutation": True,
        "no_schedule_mutation": True,
    }


def test_rejects_unordered_or_uncited_preflight_gates() -> None:
    packet = build_public_source_refresh_dry_run_acceptance_checklist_packet(_fixture())
    packet["preflight_gates"][1]["order"] = 4
    packet["preflight_gates"][2]["evidence_refs"] = []

    codes = _issue_codes(packet)
    assert "unordered_preflight_gates" in codes
    assert "uncited_preflight_gate" in codes
    with pytest.raises(PublicSourceRefreshDryRunAcceptanceChecklistError):
        require_public_source_refresh_dry_run_acceptance_checklist_packet(packet)


def test_rejects_missing_source_abort_checks_and_evidence() -> None:
    packet = build_public_source_refresh_dry_run_acceptance_checklist_packet(_fixture())
    first_source = packet["per_source_abort_checks"][0]
    first_source["abort_checks"] = []
    first_source["allowlist_evidence_refs"] = []
    first_source["robots_evidence_refs"] = []

    codes = _issue_codes(packet)
    assert "missing_abort_checks" in codes
    assert "missing_allowlist_evidence" in codes
    assert "missing_robots_evidence" in codes


def test_rejects_missing_metadata_outputs_reviewer_owner_and_required_attestations() -> None:
    packet = build_public_source_refresh_dry_run_acceptance_checklist_packet(_fixture())
    packet["expected_metadata_only_outputs"] = []
    packet["reviewer_owner_fields"] = {"reviewer": "", "owner": ""}
    packet["attestations"]["no_processor"] = False
    packet["attestations"].pop("no_schedule_mutation")

    codes = _issue_codes(packet)
    assert "missing_expected_metadata_only_outputs" in codes
    assert "missing_reviewer_owner_fields" in codes
    assert "missing_no_processor_attestation" in codes
    assert "missing_no_schedule_mutation_attestation" in codes


def test_rejects_live_fetch_raw_artifacts_authenticated_urls_and_mutations() -> None:
    packet = build_public_source_refresh_dry_run_acceptance_checklist_packet(_fixture())
    packet["per_source_abort_checks"][0]["canonical_url"] = "https://devhub.portlandoregon.gov/account/my-permits"
    packet["download_ref"] = "downloaded-documents/devhub-faq.pdf"
    packet["fetch_allowed"] = True
    packet["notes"] = "processor executed and registry was updated"

    codes = _issue_codes(packet)
    assert "authenticated_url" in codes
    assert "raw_body_download_or_archive_reference" in codes
    assert "unsafe_live_or_mutation_flag" in codes
    assert "unsafe_live_mutation_or_guarantee_claim" in codes


def test_rejects_non_allowlisted_urls_and_live_download_commands() -> None:
    packet = build_public_source_refresh_dry_run_acceptance_checklist_packet(_fixture())
    packet["operator_command"] = "curl -L https://example.com/not-allowed.pdf -o out.pdf"
    packet["evidence_url"] = "https://example.com/not-allowed"

    codes = _issue_codes(packet)
    assert "command_string_performs_live_fetch_or_download" in codes
    assert "non_allowlisted_url" in codes


def test_rejects_raw_artifact_strings_permit_guarantees_and_active_mutation_flags() -> None:
    packet = build_public_source_refresh_dry_run_acceptance_checklist_packet(_fixture())
    packet["raw_artifact_note"] = "Review warc://public-refresh/devhub-faq.warc before acceptance."
    packet["legal_note"] = "This packet guarantees issuance and the permit will be approved."
    packet["registry_mutation_flag"] = "active"
    packet["schedule_update_enabled"] = True

    codes = _issue_codes(packet)
    assert "raw_body_download_or_archive_reference" in codes
    assert "legal_or_permitting_outcome_guarantee" in codes
    assert "active_registry_or_schedule_mutation_flag" in codes


def test_builder_requires_all_three_input_packets() -> None:
    fixture = copy.deepcopy(_fixture())
    fixture.pop("public_source_refresh_operator_dry_run_transcript")

    with pytest.raises(PublicSourceRefreshDryRunAcceptanceChecklistError, match="missing_required_input_packet"):
        build_public_source_refresh_dry_run_acceptance_checklist_packet(fixture)
