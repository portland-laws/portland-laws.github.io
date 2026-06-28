from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.agent_readiness.offline_release_readiness_packet import (
    assert_valid_offline_release_readiness_packet,
    compile_offline_release_readiness_packet,
    validate_offline_release_readiness_packet,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "offline_release_readiness" / "source_candidate_packet.json"


def _load_fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_compile_offline_release_readiness_packet_consolidates_blockers_and_attestations() -> None:
    packet = compile_offline_release_readiness_packet(_load_fixture())

    assert packet["fixture_only"] is True
    assert packet["packet_status"] == "blocked_no_promotion"
    assert packet["release_blockers"]
    assert {blocker["candidate_id"] for blocker in packet["release_blockers"]} >= {
        "archive-manifest-readiness-devhub-faq-refresh",
        "requirement-rerun-devhub-faq-action-gates",
        "process-model-devhub-upload-staging-candidate",
    }
    assert len(packet["required_operator_signoffs"]) == 6
    assert len(packet["rollback_checkpoints"]) == 6
    assert len(packet["validation_evidence_references"]) == 6
    assert all(attestation["value"] is True for attestation in packet["no_promotion_attestations"])
    assert packet["execution_boundaries"] == {
        "live_network": False,
        "launches_devhub": False,
        "uses_authenticated_session": False,
        "writes_registries": False,
        "writes_manifests": False,
        "writes_requirements": False,
        "writes_process_models": False,
        "writes_guardrails": False,
        "performs_promotion": False,
    }
    assert_valid_offline_release_readiness_packet(packet)


def test_compile_adds_blocker_for_missing_required_input_collection() -> None:
    fixture = _load_fixture()
    fixture["guardrail_bundle_update_candidates"] = []

    packet = compile_offline_release_readiness_packet(fixture)

    assert any(blocker["candidate_id"] == "guardrail_bundle_update_candidates" for blocker in packet["release_blockers"])


def test_compile_rejects_registry_manifest_process_and_guardrail_mutation_flags() -> None:
    for collection, flag in (
        ("source_registry_update_candidates", "mutate_registry"),
        ("archive_manifest_promotion_readiness", "promotion_enabled"),
        ("process_model_update_candidates", "mutate_process_model"),
        ("guardrail_bundle_update_candidates", "guardrail_promotion_enabled"),
    ):
        fixture = _load_fixture()
        fixture[collection][0][flag] = True
        with pytest.raises(ValueError, match="mutation|promotion"):
            compile_offline_release_readiness_packet(fixture)


def test_compile_rejects_private_paths_and_session_artifacts() -> None:
    fixture = _load_fixture()
    fixture["agent_regression_rerun_plans"][0]["session_state"] = "private browser state"
    with pytest.raises(ValueError, match="private/session"):
        compile_offline_release_readiness_packet(fixture)

    fixture = _load_fixture()
    fixture["validation_evidence"][0]["artifact_ref"] = "/home/example/devhub/session.json"
    with pytest.raises(ValueError, match="raw output or private local path"):
        compile_offline_release_readiness_packet(fixture)


def test_compile_blocks_unknown_or_missing_citations_without_mutating_anything() -> None:
    fixture = _load_fixture()
    fixture["source_registry_update_candidates"][0]["source_evidence_ids"] = ["missing-evidence-id"]
    fixture["agent_regression_rerun_plans"][0].pop("source_evidence_ids")

    packet = compile_offline_release_readiness_packet(fixture)
    reasons = {blocker["reason"] for blocker in packet["release_blockers"]}

    assert "unknown_citation" in reasons
    assert "missing_citation" in reasons
    assert packet["execution_boundaries"]["writes_registries"] is False
    assert packet["execution_boundaries"]["writes_manifests"] is False
    assert packet["execution_boundaries"]["writes_process_models"] is False
    assert packet["execution_boundaries"]["writes_guardrails"] is False


def test_validation_rejects_release_packet_missing_no_promotion_attestation_and_boundaries() -> None:
    compiled = compile_offline_release_readiness_packet(_load_fixture())
    broken = copy.deepcopy(compiled)
    broken["no_promotion_attestations"][0]["value"] = False
    broken["execution_boundaries"]["performs_promotion"] = True

    result = validate_offline_release_readiness_packet(broken)

    assert result.valid is False
    assert any("no-promotion attestation" in problem for problem in result.problems)
    assert any("performs_promotion" in problem for problem in result.problems)
