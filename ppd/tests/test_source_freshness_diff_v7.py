from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from ppd.source_freshness_diff_v7 import (
    OFFLINE_VALIDATION_COMMANDS,
    build_source_freshness_diff_v7,
    build_source_freshness_diff_v7_from_paths,
    load_json,
    validate_source_freshness_diff_v7,
)

FIXTURES = Path(__file__).parent / "fixtures" / "source_freshness_diff_v7"


def _valid_packet() -> dict[str, Any]:
    return build_source_freshness_diff_v7_from_paths(
        FIXTURES / "processor_handoff_manifest_v7.json",
        FIXTURES / "prior_metadata_v7.json",
        FIXTURES / "current_metadata_v7.json",
    )


def test_builds_changed_unchanged_and_placeholder_rows_from_fixtures() -> None:
    result = _valid_packet()

    assert result["schema"] == "ppd.source_freshness_diff.v7"
    assert result["source"]["dry_run"] is True
    assert result["source"]["raw_artifacts_downloaded"] is False
    assert result["source"]["devhub_opened"] is False
    assert result["source"]["official_actions_performed"] is False

    changed = {row["source_id"]: row for row in result["changed_source_rows"]}
    unchanged = {row["source_id"]: row for row in result["unchanged_source_rows"]}

    assert changed["ppd-submit-plans-online"]["change_kind"] == "content_hash_changed"
    assert changed["ppd-devhub-faq"]["change_kind"] == "new_source"
    assert unchanged["ppd-online-tools"]["change_kind"] == "unchanged"

    changed_ids = set(changed)
    assert {row["source_id"] for row in result["affected_citation_placeholders"]} == changed_ids
    assert {row["source_id"] for row in result["affected_requirement_placeholders"]} == changed_ids
    assert {row["source_id"] for row in result["downstream_reextraction_queue_suggestions"]} == changed_ids
    assert {row["source_id"] for row in result["reviewer_owner_placeholders"]} == changed_ids
    assert result["validation_commands"] == OFFLINE_VALIDATION_COMMANDS
    assert result["legal_or_permitting_guarantees"] == []


def test_rejects_non_dry_run_manifest() -> None:
    manifest = load_json(FIXTURES / "processor_handoff_manifest_v7.json")
    prior = load_json(FIXTURES / "prior_metadata_v7.json")
    current = load_json(FIXTURES / "current_metadata_v7.json")
    manifest["dry_run"] = False

    with pytest.raises(ValueError, match="dry-run"):
        build_source_freshness_diff_v7(manifest, prior, current)


def test_rejects_live_artifact_fields_in_fixtures() -> None:
    manifest = load_json(FIXTURES / "processor_handoff_manifest_v7.json")
    prior = load_json(FIXTURES / "prior_metadata_v7.json")
    current = load_json(FIXTURES / "current_metadata_v7.json")
    current["sources"][0]["download_path"] = "/tmp/raw.pdf"

    with pytest.raises(ValueError, match="forbidden live artifact field"):
        build_source_freshness_diff_v7(manifest, prior, current)


@pytest.mark.parametrize(
    "ref_key",
    ["handoff_manifest_id", "prior_metadata_id", "current_metadata_id"],
)
def test_validator_rejects_missing_fixture_references(ref_key: str) -> None:
    packet = _valid_packet()
    packet["source"][ref_key] = ""

    with pytest.raises(ValueError, match=ref_key):
        validate_source_freshness_diff_v7(packet)


@pytest.mark.parametrize(
    "list_key",
    [
        "changed_source_rows",
        "unchanged_source_rows",
        "affected_citation_placeholders",
        "affected_requirement_placeholders",
        "downstream_reextraction_queue_suggestions",
        "stale_evidence_hold_updates",
        "reviewer_owner_placeholders",
    ],
)
def test_validator_rejects_missing_required_rows_and_placeholders(list_key: str) -> None:
    packet = _valid_packet()
    packet[list_key] = []

    with pytest.raises(ValueError, match=list_key):
        validate_source_freshness_diff_v7(packet)


def test_validator_rejects_missing_affected_citation_for_changed_source() -> None:
    packet = _valid_packet()
    packet["affected_citation_placeholders"] = packet["affected_citation_placeholders"][:1]

    with pytest.raises(ValueError, match="affected_citation_placeholders"):
        validate_source_freshness_diff_v7(packet)


def test_validator_rejects_missing_affected_requirement_for_changed_source() -> None:
    packet = _valid_packet()
    packet["affected_requirement_placeholders"] = packet["affected_requirement_placeholders"][:1]

    with pytest.raises(ValueError, match="affected_requirement_placeholders"):
        validate_source_freshness_diff_v7(packet)


def test_validator_rejects_missing_downstream_reextraction_suggestion_for_changed_source() -> None:
    packet = _valid_packet()
    packet["downstream_reextraction_queue_suggestions"] = packet["downstream_reextraction_queue_suggestions"][:1]

    with pytest.raises(ValueError, match="downstream_reextraction_queue_suggestions"):
        validate_source_freshness_diff_v7(packet)


def test_validator_rejects_missing_stale_evidence_hold_for_changed_source() -> None:
    packet = _valid_packet()
    packet["stale_evidence_hold_updates"] = packet["stale_evidence_hold_updates"][:1]

    with pytest.raises(ValueError, match="stale_evidence_hold_updates"):
        validate_source_freshness_diff_v7(packet)


def test_validator_rejects_missing_reviewer_owner_for_changed_source() -> None:
    packet = _valid_packet()
    packet["reviewer_owner_placeholders"] = packet["reviewer_owner_placeholders"][:1]

    with pytest.raises(ValueError, match="reviewer_owner_placeholders"):
        validate_source_freshness_diff_v7(packet)


def test_validator_rejects_missing_validation_commands() -> None:
    packet = _valid_packet()
    packet["validation_commands"] = []

    with pytest.raises(ValueError, match="validation_commands"):
        validate_source_freshness_diff_v7(packet)


@pytest.mark.parametrize(
    "flag",
    [
        "live_crawl_executed",
        "raw_artifacts_downloaded",
        "devhub_opened",
        "private_documents_read",
        "official_actions_performed",
        "official_action_completed",
        "active_mutation",
    ],
)
def test_validator_rejects_forbidden_true_claims(flag: str) -> None:
    packet = _valid_packet()
    packet["source"][flag] = True

    with pytest.raises(ValueError, match="forbidden active/live/private/mutating claim"):
        validate_source_freshness_diff_v7(packet)


@pytest.mark.parametrize(
    "field",
    ["raw_artifact_path", "download_path", "private_document_path", "devhub_session_path", "auth_state_path"],
)
def test_validator_rejects_downloaded_raw_private_session_or_auth_artifacts(field: str) -> None:
    packet = _valid_packet()
    packet["changed_source_rows"][0][field] = "/tmp/unsafe-artifact"

    with pytest.raises(ValueError, match="forbidden live artifact field"):
        validate_source_freshness_diff_v7(packet)


def test_validator_rejects_legal_or_permitting_guarantees() -> None:
    packet = _valid_packet()
    packet["legal_or_permitting_guarantees"] = ["permit approval guaranteed"]

    with pytest.raises(ValueError, match="legal or permitting guarantees"):
        validate_source_freshness_diff_v7(packet)


def test_validator_rejects_reextraction_queue_that_requires_live_crawl() -> None:
    packet = _valid_packet()
    packet["downstream_reextraction_queue_suggestions"][0]["requires_live_crawl"] = True

    with pytest.raises(ValueError, match="forbidden active/live/private/mutating claim"):
        validate_source_freshness_diff_v7(packet)


def test_validator_rejects_changed_and_unchanged_overlap() -> None:
    packet = _valid_packet()
    packet["unchanged_source_rows"].append(deepcopy(packet["changed_source_rows"][0]))

    with pytest.raises(ValueError, match="must not overlap"):
        validate_source_freshness_diff_v7(packet)
