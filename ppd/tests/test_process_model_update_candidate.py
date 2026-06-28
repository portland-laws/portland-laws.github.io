from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.logic.process_model_update_candidate import (
    DIFF_TYPES,
    build_process_model_update_candidate,
    validate_process_model_update_candidate,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "process_model_update_candidate"


def _load_fixture(name: str) -> dict:
    with (FIXTURE_DIR / name).open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def _valid_packet() -> dict:
    return build_process_model_update_candidate(
        _load_fixture("requirement_rerun_review.json"),
        _load_fixture("impact_rehearsal_packet.json"),
        generated_at="2026-05-29T00:00:00Z",
    )


def _codes(packet: dict) -> str:
    try:
        validate_process_model_update_candidate(packet)
    except ValueError as exc:
        return str(exc)
    raise AssertionError("Expected process-model update candidate validation to fail")


def test_builds_cited_proposed_diffs_without_active_mutation() -> None:
    packet = _valid_packet()

    assert packet["packet_type"] == "process_model_update_candidate"
    assert packet["process_model_id"] == "residential-building-permit-draft"
    assert set(packet["proposed_diffs"]) == set(DIFF_TYPES)
    assert packet["attestations"] == {
        "fixture_first": True,
        "compiled_process_models": False,
        "promoted_process_models": False,
        "mutated_active_process_models": False,
        "no_active_process_mutation": True,
    }

    assert len(packet["proposed_diffs"]["stage"]) == 1
    assert len(packet["proposed_diffs"]["required_fact"]) == 1
    assert len(packet["proposed_diffs"]["document_rule"]) == 1
    assert len(packet["proposed_diffs"]["deadline"]) == 1
    assert len(packet["proposed_diffs"]["exception"]) == 1
    assert len(packet["proposed_diffs"]["unsupported_path"]) == 1

    rejected_targets = {
        diff["target_id"]
        for diffs in packet["proposed_diffs"].values()
        for diff in diffs
    }
    assert "deadline-unconfirmed-fee-payment" not in rejected_targets

    for diffs in packet["proposed_diffs"].values():
        for diff in diffs:
            assert diff["citations"]
            assert diff["reviewer_owner"]
            assert diff["rollback_note"]
            assert diff["impact_rehearsal_refs"] == ["process-model-impact-rehearsal-2026-05-29-fixture"]

    validate_process_model_update_candidate(packet)


def test_validation_rejects_compile_or_promotion_attestation() -> None:
    packet = _valid_packet()
    packet["attestations"]["promoted_process_models"] = True

    assert "promoted_process_models" in _codes(packet)


def test_validation_rejects_uncited_diff_missing_review_owner_and_rollback_note() -> None:
    packet = _valid_packet()
    diff = packet["proposed_diffs"]["stage"][0]
    diff["citations"] = []
    diff["reviewer_owner"] = ""
    diff["rollback_note"] = ""
    packet["reviewer_owners"] = []
    packet["rollback_notes"] = []

    message = _codes(packet)

    assert "missing citations" in message
    assert "missing reviewer_owner" in message
    assert "missing rollback_note" in message
    assert "missing reviewer_owners" in message
    assert "missing rollback_notes" in message


def test_validation_rejects_unknown_process_and_requirement_ids() -> None:
    packet = _valid_packet()
    packet["known_process_model_ids"] = ["known-process"]
    packet["known_requirement_ids"] = ["known-requirement"]

    message = _codes(packet)

    assert "unknown process_model_id" in message
    assert "unknown requirement_id" in message


def test_validation_rejects_stale_current_evidence_without_acknowledgement() -> None:
    packet = _valid_packet()
    packet["proposed_diffs"]["deadline"][0]["current"] = {
        "current_evidence": {"freshness_status": "stale"}
    }

    assert "stale current evidence without acknowledgement" in _codes(packet)

    acknowledged = copy.deepcopy(packet)
    acknowledged["proposed_diffs"]["deadline"][0]["stale_current_evidence_acknowledged"] = True
    validate_process_model_update_candidate(acknowledged)


def test_validation_rejects_private_case_facts_local_paths_and_execution_claims() -> None:
    packet = _valid_packet()
    packet["private_case_facts"] = {"project_address": "123 Private St"}
    packet["review_notes"] = "ran live crawler and compiled the process model"
    packet["local_artifact_path"] = "/home/alex/private/devhub/session.json"

    message = _codes(packet)

    assert "private case facts" in message
    assert "live crawler/compiler execution claim" in message
    assert "local private path" in message


def test_validation_rejects_outcome_guarantees_and_active_process_mutation_flags() -> None:
    packet = _valid_packet()
    packet["active_process_model_mutation"] = True
    packet["review_notes"] = "This guarantees issuance and the permit will be approved."

    message = _codes(packet)

    assert "active process-model mutation flag" in message
    assert "legal or permitting outcome guarantee" in message
