from copy import deepcopy
from pathlib import Path

import pytest

from ppd.public_refresh_seed_review import (
    BLOCKED_ACTIONS,
    PublicRefreshSeedReviewValidationError,
    build_packet_from_files,
    validate_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_refresh_seed_review"


def _packet():
    return build_packet_from_files(
        FIXTURE_DIR / "synthetic_post_activation_monitoring_rows.json",
        FIXTURE_DIR / "official_source_anchor_placeholders.json",
    )


def _packet_without(path):
    packet = deepcopy(_packet())
    cursor = packet
    for key in path[:-1]:
        cursor = cursor[key]
    del cursor[path[-1]]
    return packet


def test_packet_ranks_synthetic_seed_candidates_without_live_actions():
    packet = _packet()

    assert packet["packet_version"] == "next-public-refresh-seed-review-v1"
    assert packet["mode"] == "fixture-first-offline-review"
    assert packet["prohibited_actions"] == list(BLOCKED_ACTIONS)
    assert [candidate["seed_id"] for candidate in packet["candidates"]] == [
        "seed-land-use-notices-index",
        "seed-permit-center-fee-schedule",
        "seed-appeals-summaries",
    ]


def test_packet_records_preflight_manifest_citation_guardrail_and_review_fields():
    packet = _packet()
    by_seed = {candidate["seed_id"]: candidate for candidate in packet["candidates"]}

    land_use = by_seed["seed-land-use-notices-index"]
    assert land_use["monitoring_plan_reference"] == "post-activation-monitoring-plan-v1#probe-land-use-notices"
    assert land_use["robots_allowlist_preflight_needs"] == [
        "confirm robots placeholder remains allowlisted before any future crawl",
        "route allowlist placeholder for human confirmation",
    ]
    assert "metadata-only" in land_use["expected_metadata_only_archive_manifest_impact"]
    assert land_use["citation_span_refresh_need"] == "refresh required"
    assert land_use["human_review_routing"]["queue"] == "citation span refresh review"
    assert "do not open DevHub" in land_use["human_review_routing"]["review_note"]

    appeals = by_seed["seed-appeals-summaries"]
    assert appeals["stale_source_guardrail_hold_impact"] == "hold blocks public refresh seed until reviewed"
    assert appeals["human_review_routing"]["queue"] == "stale-source guardrail review"
    assert appeals["rollback_notes"] == "remove this seed from the next metadata-only manifest draft; retain prior public corpus pointers"


def test_packet_uses_only_official_source_anchor_placeholders():
    packet = _packet()

    assert packet["official_source_anchor_placeholders"] == [
        "official://portland-ppd/source-anchor/appeals",
        "official://portland-ppd/source-anchor/bds-fees",
        "official://portland-ppd/source-anchor/land-use-notices",
    ]
    for candidate in packet["candidates"]:
        assert candidate["official_source_anchor"].startswith("official://")
        assert "public_url_placeholder" not in candidate


def test_validation_commands_are_exact_offline_commands():
    packet = _packet()

    assert packet["validation_commands"] == [
        ["python3", "-m", "py_compile", "ppd/public_refresh_seed_review.py"],
        ["python3", "-m", "pytest", "ppd/tests/test_public_refresh_seed_review.py"],
    ]


def test_rejects_source_anchor_that_requires_official_action(tmp_path):
    monitoring = FIXTURE_DIR / "synthetic_post_activation_monitoring_rows.json"
    bad_anchor = tmp_path / "bad_anchor.json"
    bad_anchor.write_text(
        """[
          {
            "anchor_id": "anchor-bds-fees",
            "agency": "placeholder",
            "official_placeholder": "official://portland-ppd/source-anchor/bds-fees",
            "devhub_open_required": true,
            "auth_required": false,
            "document_download_required": false
          }
        ]""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="prohibited action"):
        build_packet_from_files(monitoring, bad_anchor)


@pytest.mark.parametrize(
    "path, message",
    [
        (["monitoring_plan_references"], "missing monitoring_plan_references"),
        (["official_source_anchor_placeholders"], "missing official_source_anchor_placeholders"),
        (["candidates"], "missing ranked seed candidates"),
        (["candidates", 0, "monitoring_plan_reference"], "monitoring_plan_reference"),
        (["candidates", 0, "official_source_anchor"], "official_source_anchor"),
        (["candidates", 0, "rank"], "rank"),
        (["candidates", 0, "robots_allowlist_preflight_needs"], "robots_allowlist_preflight_needs"),
        (["candidates", 0, "expected_metadata_only_archive_manifest_impact"], "expected_metadata_only_archive_manifest_impact"),
        (["candidates", 0, "citation_span_refresh_need"], "citation_span_refresh_need"),
        (["candidates", 0, "stale_source_guardrail_hold_impact"], "stale_source_guardrail_hold_impact"),
        (["candidates", 0, "human_review_routing"], "human_review_routing"),
        (["candidates", 0, "rollback_notes"], "rollback_notes"),
        (["validation_commands"], "validation_commands"),
    ],
)
def test_validator_rejects_missing_required_review_packet_fields(path, message):
    packet = _packet_without(path)

    errors = validate_packet(packet)

    assert any(message in error for error in errors)


def test_validator_rejects_empty_review_routing_fields():
    packet = _packet()
    packet["candidates"][0]["human_review_routing"]["queue"] = ""

    errors = validate_packet(packet)

    assert any("human_review_routing.queue" in error for error in errors)


@pytest.mark.parametrize(
    "field, value, message",
    [
        ("private_artifact_ref", "file:///home/user/private/session_state.json", "forbidden"),
        ("raw_output_ref", "raw crawl output captured", "forbidden"),
        ("downloaded_artifact_ref", "downloaded document archive.zip", "forbidden"),
        ("live_claim", "live crawl completed for this packet", "forbidden"),
        ("devhub_claim", "opened DevHub session during review", "forbidden"),
        ("release_claim", "release activated after review", "forbidden"),
        ("official_claim", "official action completed", "forbidden"),
        ("guarantee", "guarantee permit approval", "forbidden"),
    ],
)
def test_validator_rejects_private_artifacts_and_unsafe_claims(field, value, message):
    packet = _packet()
    packet[field] = value

    errors = validate_packet(packet)

    assert any(message in error for error in errors)


@pytest.mark.parametrize(
    "flag",
    [
        "active_mutation",
        "active_mutation_enabled",
        "mutates_sources",
        "mutates_guardrails",
        "mutates_release_state",
        "release_activation_enabled",
        "official_action_enabled",
        "live_crawl_enabled",
        "devhub_enabled",
    ],
)
def test_validator_rejects_active_mutation_flags(flag):
    packet = _packet()
    packet[flag] = True

    errors = validate_packet(packet)

    assert any("active mutation flag" in error for error in errors)


def test_builder_rejects_missing_monitoring_plan_reference(tmp_path):
    monitoring = tmp_path / "monitoring.json"
    monitoring.write_text(
        """[
          {
            "seed_id": "seed-permit-center-fee-schedule",
            "title": "Permit Center fee schedule metadata seed",
            "official_source_anchor_id": "anchor-bds-fees"
          }
        ]""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing monitoring plan reference"):
        build_packet_from_files(monitoring, FIXTURE_DIR / "official_source_anchor_placeholders.json")


def test_builder_raises_validation_error_if_output_is_not_valid():
    packet = _packet()
    packet["active_mutation"] = True

    errors = validate_packet(packet)

    with pytest.raises(PublicRefreshSeedReviewValidationError):
        if errors:
            raise PublicRefreshSeedReviewValidationError(errors)
