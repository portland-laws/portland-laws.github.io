from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.release.rollback_drill_outcome_review_packets import (
    RollbackDrillOutcomeReviewValidationError,
    validate_release_rollback_drill_outcome_review_packet,
    validate_release_rollback_drill_outcome_review_packet_or_raise,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "release" / "rollback_drill_outcome_review_packet.json"


def _fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_release_rollback_drill_outcome_review_packet_is_fixture_first() -> None:
    packet = _fixture()

    assert packet["packet_type"] == "fixture_first_release_rollback_drill_outcome_review"
    assert packet["mode"] == "simulated_fixture_only"

    source_ids = {source["source_id"] for source in packet["source_packets"]}  # type: ignore[index]
    assert source_ids == {
        "release_rollback_drill_packet",
        "post_promotion_smoke_test_plan",
        "post_release_monitoring_plan",
    }

    assert packet["simulated_rollback_observations"]
    assert all(observation["citation"] for observation in packet["simulated_rollback_observations"])  # type: ignore[index]

    assert packet["decision_thresholds"]
    assert all(threshold["condition"] for threshold in packet["decision_thresholds"])  # type: ignore[index]
    assert all(threshold["decision"] for threshold in packet["decision_thresholds"])  # type: ignore[index]

    assert packet["affected_artifact_references"]
    assert all(artifact["mutation_allowed"] is False for artifact in packet["affected_artifact_references"])  # type: ignore[index]

    reviewer_owner_fields = packet["reviewer_owner_fields"]  # type: ignore[index]
    assert reviewer_owner_fields["review_owner"]
    assert reviewer_owner_fields["rollback_decision_reviewer"]
    assert reviewer_owner_fields["follow_up_owner"]

    follow_ups = packet["follow_up_work_items"]
    assert follow_ups
    assert all(item["owner"] for item in follow_ups)  # type: ignore[index]
    assert all(item["status"] == "open" for item in follow_ups)  # type: ignore[index]


def test_release_rollback_drill_outcome_review_packet_has_non_mutation_attestations() -> None:
    packet = _fixture()

    required_attestations = {
        "no_active_rollback_executed",
        "no_publication_performed",
        "no_registry_mutation",
        "no_manifest_mutation",
        "no_requirements_mutation",
        "no_process_model_mutation",
        "no_guardrail_mutation",
        "no_release_notes_mutation",
        "no_schedule_mutation",
        "no_agent_state_mutation",
    }

    attestations = packet["attestations"]
    assert set(attestations) == required_attestations  # type: ignore[arg-type]
    assert all(attestations.values())  # type: ignore[union-attr]


def test_valid_release_rollback_drill_outcome_review_packet_passes_validation() -> None:
    packet = _fixture()

    result = validate_release_rollback_drill_outcome_review_packet(packet)

    assert result.ok
    assert result.errors == ()
    validate_release_rollback_drill_outcome_review_packet_or_raise(packet)


def test_release_rollback_drill_outcome_review_packet_rejects_required_guardrails() -> None:
    packet = copy.deepcopy(_fixture())
    packet["simulated_rollback_observations"] = [{"finding": "Rollback was executed and the permit will be approved."}]
    packet["decision_thresholds"] = []
    packet["affected_artifact_references"] = []
    packet["reviewer_owner_fields"] = {"review_owner": ""}
    packet["follow_up_work_items"] = []
    packet["session_trace"] = "trace.zip"
    packet["raw_download_ref"] = "raw_crawl/downloads/release.warc.gz"
    packet["local_private_path"] = "/home/example/private-release-note.txt"
    packet["published"] = True
    packet["active_artifact_mutation"] = True
    packet["consequential_controls"] = [
        {"id": "publish-release", "action": "publish release", "enabled": True}
    ]

    result = validate_release_rollback_drill_outcome_review_packet(packet)

    assert not result.ok
    joined_errors = "\n".join(result.errors)
    assert "uncited" in joined_errors
    assert "missing decision thresholds" in joined_errors
    assert "missing affected-artifact references" in joined_errors
    assert "missing reviewer owners" in joined_errors
    assert "missing follow-up work items" in joined_errors
    assert "private/session artifact" in joined_errors
    assert "local private path" in joined_errors
    assert "raw crawl/download/archive reference" in joined_errors
    assert "live rollback or publication" in joined_errors
    assert "legal or permitting outcome guarantee" in joined_errors
    assert "enabled consequential control" in joined_errors
    assert "active artifact mutation flag" in joined_errors


def test_release_rollback_drill_outcome_review_raise_helper_reports_all_errors() -> None:
    packet = copy.deepcopy(_fixture())
    packet["simulated_rollback_observations"] = [{"finding": "Published to production and guaranteed permit issuance."}]
    packet["decision_thresholds"] = []
    packet["affected_artifact_references"] = []
    packet["reviewer_owner_fields"] = {}
    packet["follow_up_work_items"] = []
    packet["trace_artifact"] = "trace.zip"
    packet["write_enabled"] = True

    try:
        validate_release_rollback_drill_outcome_review_packet_or_raise(packet)
    except RollbackDrillOutcomeReviewValidationError as exc:
        assert len(exc.errors) >= 8
    else:
        raise AssertionError("expected rollback drill outcome review validation to fail")
