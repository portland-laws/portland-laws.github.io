from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ppd.public_refresh.public_metadata_manifest_dry_run_v5 import (
    DRY_RUN_VERSION,
    MODE,
    VALIDATION_COMMANDS,
    PublicMetadataManifestDryRunV5Error,
    PublicMetadataManifestDryRunV5ValidationError,
    assemble_public_metadata_manifest_dry_run_v5,
    assert_valid_public_metadata_manifest_dry_run_v5,
    load_preflight_fixture,
    validate_public_metadata_manifest_dry_run_v5,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures"
PREFLIGHT_FIXTURE = FIXTURE_DIR / "public_refresh_preflight_packet_v5" / "expected_packet.json"
EXPECTED_FIXTURE = FIXTURE_DIR / "public_metadata_manifest_dry_run_v5" / "expected_packet.json"


def _preflight_packet() -> dict[str, Any]:
    return load_preflight_fixture(PREFLIGHT_FIXTURE)


def _expected_packet() -> dict[str, Any]:
    return json.loads(EXPECTED_FIXTURE.read_text(encoding="utf-8"))


def _valid_packet() -> dict[str, Any]:
    return assemble_public_metadata_manifest_dry_run_v5(_preflight_packet())


def test_assembles_expected_fixture_first_public_metadata_manifest_dry_run_v5() -> None:
    packet = _valid_packet()

    assert packet == _expected_packet()
    assert packet["dry_run_version"] == DRY_RUN_VERSION
    assert packet["mode"] == MODE
    assert packet["input_packet_version"] == "public-refresh-preflight-packet-v5"
    assert packet["offline_only"] is True
    assert packet["validation_commands"] == VALIDATION_COMMANDS
    assert validate_public_metadata_manifest_dry_run_v5(packet) == []


def test_synthetic_archive_manifest_rows_are_metadata_only_placeholders() -> None:
    packet = _valid_packet()
    rows = packet["synthetic_archive_manifest_rows"]

    assert len(rows) == 2
    assert {row["skipped_reason"] for row in rows} == {"not_skipped", "robots_or_policy_disallowed"}
    for row in rows:
        assert row["redirect_chain"][0]["status"] == "placeholder:not-requested"
        assert str(row["http_status"]).startswith("placeholder:")
        assert str(row["content_hash"]).startswith("placeholder:not-computed")
        assert row["processor_name"] == "placeholder:processor-not-invoked"
        assert row["processor_version"] == "placeholder:processor-not-invoked"
        assert row["archive_artifact_ref"] == "placeholder:no-archive-artifact-created"
        assert row["normalized_document_ref"]["document_ref"].startswith("normalized-document-placeholder://")
        assert row["no_raw_body_persisted"] is True


def test_reviewer_hold_skip_and_rollback_notes_are_preserved() -> None:
    packet = _valid_packet()

    assert packet["skipped_reasons"] == [
        {
            "seed_id": "seed-file-standards-review-hold",
            "skipped_reason": "robots_or_policy_disallowed",
            "processor_handoff_state": "blocked_by_skip_or_reviewer_hold",
            "reviewer_hold": "true",
        }
    ]
    held_row = packet["synthetic_archive_manifest_rows"][1]
    assert held_row["reviewer_hold"] is True
    assert held_row["http_status"] == "placeholder:skipped-before-request"
    assert held_row["rollback_note"] == "Keep this candidate out of the refresh manifest until the stale-source hold is cleared."


def test_source_fixture_policy_refuses_live_crawl_download_raw_body_devhub_and_guarantees() -> None:
    packet = _valid_packet()
    policy = packet["source_fixture_policy"]

    assert policy == {
        "accepted_input": "public refresh preflight packet v5 fixture only",
        "live_crawl_permitted": False,
        "document_download_permitted": False,
        "raw_body_storage_permitted": False,
        "devhub_access_permitted": False,
        "legal_or_permitting_guarantees_permitted": False,
    }
    assert packet["prohibited_actions"] == [
        "live_crawl",
        "download_document",
        "store_raw_body",
        "open_devhub",
        "persist_private_session",
        "promote_archive_manifest",
        "legal_or_permitting_guarantee",
    ]


@pytest.mark.parametrize(
    ("field", "expected_error"),
    [
        ("input_packet_version", "missing packet.input_packet_version"),
        ("selected_public_sources", "missing packet.selected_public_sources"),
        ("synthetic_archive_manifest_rows", "missing packet.synthetic_archive_manifest_rows"),
        ("redirect_chain_placeholder_policy", "missing packet.redirect_chain_placeholder_policy"),
        ("http_status_placeholder_policy", "missing packet.http_status_placeholder_policy"),
        ("content_hash_placeholder_policy", "missing packet.content_hash_placeholder_policy"),
        ("processor_placeholder_policy", "missing packet.processor_placeholder_policy"),
        ("skipped_reasons", "missing packet.skipped_reasons"),
        ("no_raw_body_flags", "missing packet.no_raw_body_flags"),
        ("reviewer_holds", "missing packet.reviewer_holds"),
        ("rollback_notes", "missing packet.rollback_notes"),
        ("validation_commands", "missing packet.validation_commands"),
    ],
)
def test_validate_rejects_missing_required_dry_run_sections(field: str, expected_error: str) -> None:
    packet = _valid_packet()
    del packet[field]

    errors = validate_public_metadata_manifest_dry_run_v5(packet)

    assert expected_error in errors


@pytest.mark.parametrize(
    "mutator, expected_fragment",
    [
        (
            lambda packet: packet["selected_public_sources"][0].pop("source_registry_ref"),
            "missing packet.selected_public_sources[0].source_registry_ref",
        ),
        (
            lambda packet: packet["synthetic_archive_manifest_rows"][0].pop("redirect_chain"),
            "missing redirect-chain or HTTP status placeholders",
        ),
        (
            lambda packet: packet["synthetic_archive_manifest_rows"][0].pop("http_status"),
            "missing packet.synthetic_archive_manifest_rows[0].http_status",
        ),
        (
            lambda packet: packet["synthetic_archive_manifest_rows"][0].pop("content_hash"),
            "missing packet.synthetic_archive_manifest_rows[0].content_hash",
        ),
        (
            lambda packet: packet["synthetic_archive_manifest_rows"][0].pop("processor_name"),
            "missing packet.synthetic_archive_manifest_rows[0].processor_name",
        ),
        (
            lambda packet: packet["synthetic_archive_manifest_rows"][0].pop("processor_version"),
            "missing packet.synthetic_archive_manifest_rows[0].processor_version",
        ),
        (
            lambda packet: packet["synthetic_archive_manifest_rows"][0].pop("normalized_document_ref"),
            "missing normalized document references",
        ),
        (
            lambda packet: packet["synthetic_archive_manifest_rows"][0].pop("skipped_reason"),
            "missing packet.synthetic_archive_manifest_rows[0].skipped_reason",
        ),
        (
            lambda packet: packet["synthetic_archive_manifest_rows"][0].pop("no_raw_body_persisted"),
            "packet.synthetic_archive_manifest_rows[0].no_raw_body_persisted must be true",
        ),
        (
            lambda packet: packet["reviewer_holds"].pop("candidate_holds"),
            "missing reviewer holds",
        ),
        (
            lambda packet: packet["rollback_notes"].pop("candidate_level"),
            "missing rollback notes",
        ),
    ],
)
def test_validate_rejects_missing_manifest_dry_run_evidence(mutator: Any, expected_fragment: str) -> None:
    packet = _valid_packet()
    mutator(packet)

    errors = validate_public_metadata_manifest_dry_run_v5(packet)

    assert expected_fragment in errors


@pytest.mark.parametrize(
    "field, value",
    [
        ("live_crawl_claim", "live crawl completed for this manifest"),
        ("raw_body_artifact", "raw body artifact saved to fixture"),
        ("download_claim", "downloaded document is available"),
        ("private_session_artifact", "auth_state and session_state captured"),
        ("legal_guarantee", "legal guarantee and approval guaranteed"),
        ("mutation_claim", "active mutation enabled for release"),
    ],
)
def test_validate_rejects_forbidden_claim_text(field: str, value: str) -> None:
    packet = _valid_packet()
    packet[field] = value

    errors = validate_public_metadata_manifest_dry_run_v5(packet)

    assert any("forbidden live, raw, downloaded, private, auth, guarantee, or mutation claim" in error for error in errors)


@pytest.mark.parametrize(
    "field, value",
    [
        ("active_mutation", True),
        ("active_mutation_flags", ["mutates_registry"]),
        ("live_crawl_enabled", True),
        ("download_enabled", True),
        ("auth_enabled", True),
        ("archive_promotion_enabled", True),
    ],
)
def test_validate_rejects_active_mutation_flags(field: str, value: Any) -> None:
    packet = _valid_packet()
    packet["unsafe_flags"] = {field: value}

    errors = validate_public_metadata_manifest_dry_run_v5(packet)

    assert any("active mutation flag must be false, empty, or absent" in error for error in errors)


def test_assert_valid_public_metadata_manifest_dry_run_raises_validation_error() -> None:
    packet = _valid_packet()
    packet["source_fixture_policy"]["live_crawl_permitted"] = True

    with pytest.raises(PublicMetadataManifestDryRunV5ValidationError, match="live_crawl_permitted"):
        assert_valid_public_metadata_manifest_dry_run_v5(packet)


def test_rejects_non_object_preflight_packet() -> None:
    with pytest.raises(PublicMetadataManifestDryRunV5Error, match="preflight packet must be a JSON object"):
        assemble_public_metadata_manifest_dry_run_v5([])  # type: ignore[arg-type]


def test_rejects_invalid_preflight_packet_fixture() -> None:
    packet = _preflight_packet()
    packet["offline_only"] = False

    with pytest.raises(ValueError, match="public refresh preflight packet v5 rejected"):
        assemble_public_metadata_manifest_dry_run_v5(packet)
