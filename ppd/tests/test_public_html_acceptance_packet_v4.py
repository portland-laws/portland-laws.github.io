from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.validation.public_html_acceptance_packet_v4 import (
    require_public_html_acceptance_packet_v4,
    validate_public_html_acceptance_packet_v4,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_html_acceptance_packet_v4" / "valid_packet.json"


def load_valid_packet() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def assert_rejected(packet: dict, expected_fragment: str) -> None:
    result = validate_public_html_acceptance_packet_v4(packet)
    assert result.accepted is False
    assert any(expected_fragment in error for error in result.errors), result.errors


def test_valid_fixture_packet_is_accepted() -> None:
    result = validate_public_html_acceptance_packet_v4(load_valid_packet())
    assert result.accepted is True
    assert result.errors == ()
    require_public_html_acceptance_packet_v4(load_valid_packet())


def test_rejects_missing_ordered_structure() -> None:
    packet = load_valid_packet()
    packet.pop("ordered_structure")
    assert_rejected(packet, "ordered_structure")


def test_rejects_unordered_structure() -> None:
    packet = load_valid_packet()
    packet["ordered_structure"] = list(reversed(packet["ordered_structure"]))
    assert_rejected(packet, "required order")


def test_rejects_missing_callout_rows() -> None:
    packet = load_valid_packet()
    packet["document_structure"]["callout_rows"] = []
    assert_rejected(packet, "callout_rows")


def test_rejects_missing_warning_rows() -> None:
    packet = load_valid_packet()
    packet["document_structure"]["warning_rows"] = []
    assert_rejected(packet, "warning_rows")


def test_rejects_missing_table_rows_where_expected() -> None:
    packet = load_valid_packet()
    packet["document_structure"]["table_rows"] = []
    assert_rejected(packet, "table_rows")


def test_rejects_missing_expected_table_row_groups() -> None:
    packet = load_valid_packet()
    packet["document_structure"]["expected_table_row_groups"] = []
    assert_rejected(packet, "expected_table_row_groups")


def test_rejects_missing_downloadable_link_metadata() -> None:
    packet = load_valid_packet()
    packet["source_metadata"]["downloadable_link_metadata"] = []
    assert_rejected(packet, "downloadable_link_metadata")


def test_rejects_downloadable_link_raw_persistence() -> None:
    packet = load_valid_packet()
    packet["source_metadata"]["downloadable_link_metadata"][0]["raw_download_persisted"] = True
    assert_rejected(packet, "raw downloads")


def test_rejects_missing_citation_spans() -> None:
    packet = load_valid_packet()
    packet["document_structure"]["citation_spans"] = []
    assert_rejected(packet, "citation_spans")


def test_rejects_missing_extraction_confidence() -> None:
    packet = load_valid_packet()
    packet["document_structure"].pop("extraction_confidence")
    assert_rejected(packet, "extraction_confidence")


def test_rejects_out_of_range_extraction_confidence() -> None:
    packet = load_valid_packet()
    packet["document_structure"]["extraction_confidence"] = 1.4
    assert_rejected(packet, "extraction_confidence")


def test_rejects_missing_reviewer_holds() -> None:
    packet = load_valid_packet()
    packet["review_controls"]["reviewer_holds"] = []
    assert_rejected(packet, "reviewer_holds")


def test_rejects_reviewer_hold_not_required_before_acceptance() -> None:
    packet = load_valid_packet()
    packet["review_controls"]["reviewer_holds"][0]["required_before_acceptance"] = False
    assert_rejected(packet, "reviewer_holds must be required")


def test_rejects_missing_validation_commands() -> None:
    packet = load_valid_packet()
    packet["validation_commands"] = []
    assert_rejected(packet, "validation_commands")


def test_rejects_raw_and_downloaded_artifacts() -> None:
    for kind in ("raw_html", "raw_download", "downloaded_pdf", "warc"):
        packet = load_valid_packet()
        packet["artifacts"] = [{"kind": kind, "committed": True, "privacy_classification": "public"}]
        assert_rejected(packet, "prohibited artifact kind")


def test_rejects_private_session_and_browser_artifacts() -> None:
    for kind in ("auth_state", "session_cookie", "browser_profile", "trace", "har", "screenshot"):
        packet = load_valid_packet()
        packet["artifacts"] = [{"kind": kind, "committed": True, "privacy_classification": "session"}]
        assert_rejected(packet, "prohibited artifact kind")


def test_rejects_committed_private_artifact_even_with_unknown_kind() -> None:
    packet = load_valid_packet()
    packet["artifacts"] = [{"kind": "local_capture", "committed": True, "privacy_classification": "private"}]
    assert_rejected(packet, "private, session, and browser artifacts")


def test_rejects_live_crawl_or_devhub_claims() -> None:
    packet = load_valid_packet()
    packet["notes"] = "This packet was produced by a live crawl and authenticated DevHub login."
    assert_rejected(packet, "live crawl or DevHub claim")


def test_rejects_safety_attestation_live_crawl_flag() -> None:
    packet = load_valid_packet()
    packet["safety_attestation"]["live_crawl_performed"] = True
    assert_rejected(packet, "live_crawl_performed")


def test_rejects_legal_or_permitting_guarantees() -> None:
    packet = load_valid_packet()
    packet["notes"] = "This is a legal guarantee that the permit will be approved."
    assert_rejected(packet, "legal or permitting guarantee")


def test_rejects_active_mutation_flags() -> None:
    for key in (
        "mutates_remote_state",
        "writes_to_devhub",
        "submits_application",
        "uploads_documents",
        "pays_fees",
        "schedules_inspection",
        "cancels_request",
        "certifies_information",
    ):
        packet = load_valid_packet()
        packet["mutation_flags"][key] = True
        assert_rejected(packet, key)


def test_require_raises_value_error_for_invalid_packet() -> None:
    packet = copy.deepcopy(load_valid_packet())
    packet["validation_commands"] = []
    try:
        require_public_html_acceptance_packet_v4(packet)
    except ValueError as exc:
        assert "public HTML acceptance packet v4 rejected" in str(exc)
    else:
        raise AssertionError("invalid packet should raise ValueError")
