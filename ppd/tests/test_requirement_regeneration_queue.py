from pathlib import Path

from ppd.logic.requirement_regeneration_queue import build_regeneration_queue_from_files


FIXTURES = Path(__file__).parent / "fixtures" / "requirement_regeneration_queue"


def test_fixture_first_queue_maps_changed_sources_to_blocked_review_work() -> None:
    queue = build_regeneration_queue_from_files(
        FIXTURES / "public_recrawl_execution_rehearsal_plan.json",
        FIXTURES / "source_freshness_drift_digest.json",
        FIXTURES / "source_dependency_index.json",
    )

    assert queue["queue_policy"] == {
        "fixture_first": True,
        "live_crawl_required": False,
        "blocks_downstream_activation_until_review_acknowledgement": True,
    }

    items = {item["source_id"]: item for item in queue["queue_items"]}
    assert sorted(items) == ["ppd-devhub-application-guide", "ppd-spp-file-naming-standards"]

    application_guide = items["ppd-devhub-application-guide"]
    assert application_guide["affected_requirement_ids"] == [
        "req-devhub-acknowledgement-gate",
        "req-devhub-dynamic-questions",
    ]
    assert application_guide["affected_process_model_ids"] == ["process-building-permit-plan-review"]
    assert application_guide["affected_guardrail_bundle_ids"] == ["guardrail-building-permit-plan-review"]
    assert application_guide["human_review_owners"] == ["devhub-workflow-review", "requirements-counsel"]
    assert application_guide["blocked_downstream_activation"] is True
    assert application_guide["reviewer_acknowledgement_required"] is True
    assert application_guide["activation_block_reason"] == "reviewer_acknowledgement_required_before_guardrail_or_process_activation"
    assert "ppd/tests/fixtures/requirement_regeneration_queue/ppd-devhub-application-guide.changed_devhub_action_guidance.json" in application_guide["required_synthetic_fixtures"]

    file_standards = items["ppd-spp-file-naming-standards"]
    assert file_standards["affected_requirement_ids"] == [
        "req-single-pdf-file-composition",
        "req-spp-file-naming",
    ]
    assert file_standards["affected_process_model_ids"] == ["process-submit-plans-online"]
    assert file_standards["affected_guardrail_bundle_ids"] == ["guardrail-submit-plans-online"]
    assert file_standards["human_review_owners"] == ["document-intake-review"]
    assert file_standards["required_synthetic_fixtures"] == [
        "ppd/tests/fixtures/requirement_regeneration_queue/ppd-spp-file-naming-standards.changed_file_rule.json",
        "ppd/tests/fixtures/requirement_regeneration_queue/ppd-spp-file-naming-standards.changed_required_document.json",
        "ppd/tests/fixtures/requirement_regeneration_queue/spp_file_naming_guardrail_fixture.json",
    ]
