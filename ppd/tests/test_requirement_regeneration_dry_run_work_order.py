from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ppd.extraction.requirement_regeneration_dry_run_work_order import (
    RequirementRegenerationDryRunWorkOrderError,
    build_requirement_regeneration_dry_run_work_order,
    load_json_object,
    validate_requirement_regeneration_dry_run_work_order,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "requirement_regeneration_dry_run_work_order"


def valid_input() -> dict[str, object]:
    return load_json_object(FIXTURE_DIR / "input.json")


def finding_codes(packet: dict[str, object]) -> set[str]:
    return {finding.code for finding in validate_requirement_regeneration_dry_run_work_order(packet)}


def test_builds_fixture_first_dry_run_work_order_without_live_actions() -> None:
    work_order = build_requirement_regeneration_dry_run_work_order(valid_input())

    assert work_order["packet_type"] == "requirement_regeneration_dry_run_work_order"
    assert work_order["mode"] == "fixture_first_offline_dry_run"
    assert work_order["expected_requirement_ids"] == [
        "req-exact-confirmation-for-certification",
        "req-plan-set-single-pdf",
        "req-upload-staging-before-submit",
    ]
    assert work_order["execution_boundaries"] == {
        "fixture_only": True,
        "network_actions_performed": False,
        "processor_invoked": False,
        "regenerate_active_requirements": False,
        "mutates_active_requirements": False,
        "promotion_allowed": False,
    }
    assert work_order["no_promotion_attestations"] == {
        "active_requirements_regenerated": False,
        "active_requirements_mutated": False,
        "promotion_allowed": False,
        "processors_invoked": False,
        "urls_fetched": False,
        "devhub_launched": False,
        "requires_separate_human_promotion_packet": True,
    }


def test_work_order_records_prerequisite_links_and_known_ids() -> None:
    work_order = build_requirement_regeneration_dry_run_work_order(valid_input())

    assert {item["packet_role"] for item in work_order["prerequisite_links"]} == {
        "public_source_change_impact_triage_packet",
        "requirement_regeneration_promotion_decision_packet",
    }
    assert work_order["known_source_ids"] == [
        "src-devhub-submit-guide",
        "src-single-pdf-guidance",
    ]
    assert work_order["known_requirement_ids"] == [
        "req-exact-confirmation-for-certification",
        "req-plan-set-single-pdf",
        "req-upload-staging-before-submit",
    ]


def test_offline_regeneration_inputs_are_cited_and_reviewer_owned() -> None:
    work_order = build_requirement_regeneration_dry_run_work_order(valid_input())
    inputs = {item["requirement_id"]: item for item in work_order["offline_regeneration_inputs"]}

    upload = inputs["req-upload-staging-before-submit"]
    assert upload["source_id"] == "src-devhub-submit-guide"
    assert upload["citation_ids"] == [
        "ev-devhub-submit-guide-acknowledgement",
        "ev-devhub-submit-guide-steps",
        "src-devhub-submit-guide",
    ]
    assert upload["reviewer_owners"] == ["ppd-public-source-reviewer"]
    assert upload["offline_only"] is True
    assert upload["processor_invocation_allowed"] is False
    assert upload["active_requirement_regeneration_allowed"] is False


def test_stale_source_handling_blocks_regeneration_before_acknowledgement() -> None:
    work_order = build_requirement_regeneration_dry_run_work_order(valid_input())

    assert work_order["stale_source_handling"] == [
        {
            "source_id": "src-devhub-submit-guide",
            "acknowledgement": "src-devhub-submit-guide:ppd-public-source-reviewer:source review is older than the monitoring cadence for DevHub submission guidance",
            "handling": "defer_regeneration_until_reviewer_acknowledges_stale_source",
            "regeneration_allowed_before_acknowledgement": False,
            "promotion_allowed_before_acknowledgement": False,
        }
    ]


def test_reviewer_checkpoints_and_rollback_references_block_promotion() -> None:
    work_order = build_requirement_regeneration_dry_run_work_order(valid_input())

    checkpoints = {item["requirement_id"]: item for item in work_order["reviewer_checkpoints"]}
    assert checkpoints["req-upload-staging-before-submit"]["blocks_promotion"] is True
    assert checkpoints["req-upload-staging-before-submit"]["blocks_processor_invocation"] is True
    assert checkpoints["req-upload-staging-before-submit"]["stale_source_ids_to_check"] == [
        "src-devhub-submit-guide"
    ]

    assert work_order["rollback_references"] == [
        {
            "rollback_ref_id": "rollback.guardrail-building-permit-application.rev-2026-05-08",
            "active_guardrail_bundle_id": "guardrail-building-permit-application",
            "active_guardrail_bundle_revision": "rev.2026-05-08",
            "rollback_action": "discard_dry_run_work_order_and_metadata_only_candidates",
            "local_discard_only": True,
            "active_artifact_restore_required": False,
        }
    ]


def test_valid_work_order_passes_validation() -> None:
    work_order = build_requirement_regeneration_dry_run_work_order(valid_input())

    assert validate_requirement_regeneration_dry_run_work_order(work_order) == []


@pytest.mark.parametrize(
    ("mutator", "expected_code"),
    [
        (
            lambda packet: packet.update({"prerequisite_links": []}),
            "missing_prerequisite_link",
        ),
        (
            lambda packet: packet["offline_regeneration_inputs"][0].update({"citation_ids": []}),
            "uncited_regeneration_input",
        ),
        (
            lambda packet: packet["offline_regeneration_inputs"][0].update({"requirement_id": "req-unknown"}),
            "unknown_requirement_id",
        ),
        (
            lambda packet: packet["offline_regeneration_inputs"][0].update({"source_id": "src-unknown"}),
            "unknown_source_id",
        ),
        (
            lambda packet: packet.update({"expected_requirement_ids": ["req-upload-staging-before-submit"]}),
            "expected_requirement_id_mismatch",
        ),
        (
            lambda packet: packet["offline_regeneration_inputs"][0].update({"processor_invocation_allowed": True}),
            "forbidden_live_or_mutating_claim",
        ),
        (
            lambda packet: packet["offline_regeneration_inputs"][0].update({"active_requirement_regeneration_allowed": True}),
            "forbidden_live_or_mutating_claim",
        ),
        (
            lambda packet: packet.update({"raw_download_ref": "downloads/devhub-guide.pdf"}),
            "forbidden_private_or_raw_artifact",
        ),
        (
            lambda packet: packet.update({"archive_artifact_ref": "warc://raw-crawl"}),
            "forbidden_private_or_raw_artifact",
        ),
        (
            lambda packet: packet.update({"processor_invoked": True}),
            "forbidden_live_or_mutating_claim",
        ),
        (
            lambda packet: packet.update({"network_actions_performed": True}),
            "forbidden_live_or_mutating_claim",
        ),
        (
            lambda packet: packet.update({"reviewer_checkpoints": []}),
            "missing_reviewer_checkpoints",
        ),
        (
            lambda packet: packet["reviewer_checkpoints"][0].update({"reviewer_owner": ""}),
            "missing_reviewer_owner",
        ),
        (
            lambda packet: packet["reviewer_checkpoints"][0].update({"blocks_promotion": False}),
            "checkpoint_does_not_block_promotion",
        ),
        (
            lambda packet: packet["reviewer_checkpoints"][0].update({"blocks_processor_invocation": False}),
            "checkpoint_does_not_block_processor_invocation",
        ),
        (
            lambda packet: packet["stale_source_handling"][0].update({"regeneration_allowed_before_acknowledgement": True}),
            "forbidden_live_or_mutating_claim",
        ),
        (
            lambda packet: packet.update({"rollback_references": []}),
            "missing_rollback_references",
        ),
        (
            lambda packet: packet["rollback_references"][0].update({"local_discard_only": False}),
            "rollback_not_local_discard_only",
        ),
        (
            lambda packet: packet["no_promotion_attestations"].update({"promotion_allowed": True}),
            "forbidden_live_or_mutating_claim",
        ),
        (
            lambda packet: packet.update({"status": "production-ready"}),
            "production_ready_label_before_review",
        ),
        (
            lambda packet: packet.update({"production_ready": True}),
            "production_ready_label_before_review",
        ),
    ],
)
def test_validation_rejects_unsafe_or_incomplete_work_orders(mutator, expected_code: str) -> None:
    packet = build_requirement_regeneration_dry_run_work_order(valid_input())
    mutator(packet)

    assert expected_code in finding_codes(packet)


def test_builder_rejects_live_fetch_or_processor_claims_in_inputs() -> None:
    packet = deepcopy(valid_input())
    packet["public_source_change_impact_triage_packet"]["live_fetch_performed"] = True

    with pytest.raises(RequirementRegenerationDryRunWorkOrderError) as excinfo:
        build_requirement_regeneration_dry_run_work_order(packet)

    assert {finding.code for finding in excinfo.value.findings} == {
        "forbidden_live_or_mutating_claim"
    }


def test_builder_rejects_raw_or_private_artifact_references_in_inputs() -> None:
    packet = deepcopy(valid_input())
    packet["requirement_regeneration_promotion_decision_packet"]["raw_pdf_reference"] = "raw-download.pdf"

    with pytest.raises(RequirementRegenerationDryRunWorkOrderError) as excinfo:
        build_requirement_regeneration_dry_run_work_order(packet)

    assert {finding.code for finding in excinfo.value.findings} == {
        "forbidden_private_or_raw_artifact"
    }
