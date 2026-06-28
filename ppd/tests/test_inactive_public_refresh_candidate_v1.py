from pathlib import Path

import pytest

from ppd.promotion.inactive_public_refresh_candidate_v1 import (
    ReviewerBundlePacketRow,
    assemble_inactive_public_refresh_candidate_from_fixture,
    assemble_inactive_public_refresh_candidate_v1,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "inactive_public_refresh_candidate_v1"
    / "reviewer_bundle_packets.jsonl"
)


def test_fixture_assembles_inactive_public_refresh_candidate_v1() -> None:
    candidate = assemble_inactive_public_refresh_candidate_from_fixture(FIXTURE_PATH)

    assert candidate["candidate_id"] == "inactive-public-refresh-promotion-candidate-v1"
    assert candidate["promotion_state"] == "inactive_candidate_only"
    assert candidate["input_policy"] == {
        "source": "synthetic_reviewer_bundle_packet_rows_only",
        "live_crawling_allowed": False,
        "document_download_allowed": False,
        "raw_output_storage_allowed": False,
        "devhub_open_allowed": False,
        "active_artifact_promotion_allowed": False,
        "release_activation_allowed": False,
        "official_actions_allowed": False,
    }

    manifests = candidate["manifests"]
    assert manifests["source_registries"][0]["source_id"] == "src-ppd-landing"
    assert manifests["archive_manifests"][0]["no_raw_body_persisted"] is True
    assert manifests["document_records"][0]["document_id"] == "doc-ppd-landing"
    assert manifests["requirement_nodes"][0]["requirement_id"] == "req-safe-public-refresh"
    assert manifests["process_models"][0]["process_id"] == "proc-general-ppd-public"
    assert manifests["guardrail_bundles"][0]["guardrail_bundle_id"] == "guard-inactive-public-refresh-v1"
    assert manifests["agent_readiness_references"][0]["readiness_state"] == "inactive_reference_only"

    assert all(item["satisfied"] is True for item in candidate["promotion_preconditions"])
    assert all(
        item["approval_status"] == "approved_for_inactive_candidate"
        for item in candidate["reviewer_approvals"]
    )
    assert candidate["rollback_checkpoints"][0]["active_artifacts_touched"] is False
    assert candidate["offline_validation_commands"] == [
        ["python3", "-m", "py_compile", "ppd/promotion/inactive_public_refresh_candidate_v1.py"],
        ["python3", "-m", "pytest", "ppd/tests/test_inactive_public_refresh_candidate_v1.py"],
    ]


def test_rejects_non_synthetic_packet_rows() -> None:
    with pytest.raises(ValueError, match="must be marked synthetic"):
        ReviewerBundlePacketRow.from_mapping(
            {
                "packet_id": "bad-row",
                "packet_kind": "source_registry",
                "payload": {"source_id": "src-bad"},
            }
        )


def test_rejects_forbidden_raw_or_private_payload_keys() -> None:
    with pytest.raises(ValueError, match="forbidden payload key"):
        ReviewerBundlePacketRow.from_mapping(
            {
                "packet_id": "bad-raw-row",
                "packet_kind": "document_record",
                "payload": {"synthetic": True, "raw_output": "not commit safe"},
            }
        )


def test_requires_all_core_manifest_packet_types() -> None:
    rows = [
        ReviewerBundlePacketRow.from_mapping(
            {
                "packet_id": "only-source",
                "packet_kind": "source_registry",
                "payload": {"synthetic": True, "source_id": "src-only"},
            }
        )
    ]

    with pytest.raises(ValueError, match="Missing required ArchiveManifest"):
        assemble_inactive_public_refresh_candidate_v1(rows)
