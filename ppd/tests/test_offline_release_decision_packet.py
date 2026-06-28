from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.agent_readiness.offline_release_decision_packet import (
    assert_valid_offline_release_decision_packet,
    build_offline_release_decision_packet,
    validate_offline_release_decision_packet,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "offline_release_decision" / "input_packets.json"


def _load_fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_builds_cited_no_go_release_decision_packet() -> None:
    packet = build_offline_release_decision_packet(_load_fixture())

    assert packet["packet_type"] == "ppd.offline_release_decision_packet.v1"
    assert packet["fixture_only"] is True
    assert packet["recommendations"] == [
        {
            "recommendation_id": "release-decision-primary",
            "decision": "no_go",
            "summary": "Do not promote or claim release readiness until unresolved blockers and failed validation commands are cleared.",
            "source_evidence_ids": ["evidence-archive-manifest-readiness", "evidence-process-model-candidate"],
            "validation_command_ref_ids": [
                "validation-command-ppd-daemon-self-test",
                "validation-command-offline-readiness-validation",
            ],
        }
    ]
    assert {blocker["candidate_id"] for blocker in packet["unresolved_blocker_summaries"]} == {
        "archive-manifest-readiness-devhub-faq-refresh",
        "process-model-devhub-upload-staging-candidate",
    }
    assert {request["role"] for request in packet["operator_signoff_requests"]} == {
        "archive_operator",
        "process_model_reviewer",
    }
    assert len(packet["rollback_checkpoints"]) == 2
    assert {ref["command_ref_id"] for ref in packet["validation_command_references"]} == {
        "validation-command-ppd-daemon-self-test",
        "validation-command-offline-readiness-validation",
    }
    assert all(attestation["value"] is True for attestation in packet["no_promotion_attestations"])
    assert packet["release_state_effects"] == {
        "mutates_registries": False,
        "mutates_manifests": False,
        "mutates_requirements": False,
        "mutates_process_models": False,
        "mutates_guardrails": False,
        "promotes_release": False,
        "launches_devhub": False,
        "uses_live_network": False,
    }
    assert_valid_offline_release_decision_packet(packet)


def test_build_adds_failed_validation_command_as_no_go_blocker() -> None:
    fixture = _load_fixture()
    fixture["offline_release_readiness_packet"]["release_blockers"] = []
    fixture["readiness_validation_results"][0]["returncode"] = 1

    packet = build_offline_release_decision_packet(fixture)

    assert packet["recommendations"][0]["decision"] == "no_go"
    assert any(blocker["reason"] == "validation_command_failed" for blocker in packet["unresolved_blocker_summaries"])


def test_build_allows_operator_review_only_when_blockers_and_commands_are_clear() -> None:
    fixture = _load_fixture()
    fixture["offline_release_readiness_packet"]["release_blockers"] = []

    packet = build_offline_release_decision_packet(fixture)

    assert packet["recommendations"][0]["decision"] == "go_for_operator_review_only"
    assert packet["unresolved_blocker_summaries"] == []
    assert packet["release_state_effects"]["promotes_release"] is False


def test_build_rejects_live_execution_raw_private_artifacts_and_mutation_flags() -> None:
    fixture = _load_fixture()
    fixture["readiness_validation_results"][0]["summary"] = "live DevHub run completed"
    with pytest.raises(ValueError, match="live execution"):
        build_offline_release_decision_packet(fixture)

    fixture = _load_fixture()
    fixture["offline_release_readiness_packet"]["validation_evidence_references"][0]["description"] = "/tmp/raw-html/body.html"
    with pytest.raises(ValueError, match="private, authenticated, download, archive, or raw"):
        build_offline_release_decision_packet(fixture)

    fixture = _load_fixture()
    fixture["offline_release_readiness_packet"]["promotion_enabled"] = True
    with pytest.raises(ValueError, match="mutation or promotion"):
        build_offline_release_decision_packet(fixture)


def test_build_rejects_private_authenticated_urls_and_archive_download_references() -> None:
    fixture = _load_fixture()
    fixture["offline_release_readiness_packet"]["validation_evidence_references"][0]["download_url"] = "https://www.portland.gov/ppd/documents/raw/download"
    with pytest.raises(ValueError, match="download, archive, or raw"):
        build_offline_release_decision_packet(fixture)

    fixture = _load_fixture()
    fixture["offline_release_readiness_packet"]["validation_evidence_references"][0]["authenticated_url"] = "https://devhub.portlandoregon.gov/private/case?token=redacted"
    with pytest.raises(ValueError, match="private, authenticated"):
        build_offline_release_decision_packet(fixture)


def test_build_rejects_legal_or_permitting_outcome_guarantees_and_consequential_controls() -> None:
    fixture = _load_fixture()
    fixture["readiness_validation_results"][0]["summary"] = "Permit will be approved after this packet."
    with pytest.raises(ValueError, match="outcome guarantee"):
        build_offline_release_decision_packet(fixture)

    fixture = _load_fixture()
    fixture["offline_release_readiness_packet"]["submit_enabled"] = True
    with pytest.raises(ValueError, match="consequential control"):
        build_offline_release_decision_packet(fixture)


def test_validation_rejects_uncited_recommendation_missing_rollbacks_and_active_effects() -> None:
    packet = build_offline_release_decision_packet(_load_fixture())
    broken = copy.deepcopy(packet)
    broken["recommendations"][0]["source_evidence_ids"] = []
    broken["rollback_checkpoints"] = []
    broken["release_state_effects"]["mutates_guardrails"] = True

    result = validate_offline_release_decision_packet(broken)

    assert result.valid is False
    assert any("recommendations[0] lacks source_evidence_ids" in problem for problem in result.problems)
    assert any("rollback_checkpoints must include at least one checkpoint" in problem for problem in result.problems)
    assert any("mutates_guardrails" in problem for problem in result.problems)


def test_validation_rejects_ignored_blockers_missing_signoffs_and_untracked_failed_commands() -> None:
    packet = build_offline_release_decision_packet(_load_fixture())
    broken = copy.deepcopy(packet)
    broken["recommendations"][0]["decision"] = "go_for_operator_review_only"
    broken["operator_signoff_requests"] = []
    broken["validation_command_references"][0]["returncode"] = 1
    broken["unresolved_blocker_summaries"] = [
        blocker for blocker in broken["unresolved_blocker_summaries"] if blocker["candidate_id"] != "validation-command-ppd-daemon-self-test"
    ]

    result = validate_offline_release_decision_packet(broken)

    assert result.valid is False
    assert any("ignores unresolved readiness blockers" in problem for problem in result.problems)
    assert any("operator_signoff_requests must include at least one required signoff" in problem for problem in result.problems)
    assert any("failed validation command is not represented as a blocker" in problem for problem in result.problems)
