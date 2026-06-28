from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.logic.guardrail_recompilation_rehearsal_packet import build_guardrail_recompilation_rehearsal_packet
from ppd.logic.guardrail_recompilation_rehearsal_safety import (
    finding_codes,
    require_guardrail_recompilation_rehearsal_safety,
    validate_guardrail_recompilation_rehearsal_safety,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures"
REVIEWED_REQUIREMENTS_PATH = FIXTURE_DIR / "guardrail_recompilation_rehearsal" / "reviewed_synthetic_requirement_candidates.json"
PROCESS_MODEL_PATH = FIXTURE_DIR / "process_models" / "synthetic_public_process.json"


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _build_packet() -> dict:
    return build_guardrail_recompilation_rehearsal_packet(
        _load_json(REVIEWED_REQUIREMENTS_PATH),
        [_load_json(PROCESS_MODEL_PATH)],
        active_guardrail_bundle_id="guardrail-bundle-single-pdf-active",
        active_guardrail_bundle_revision="active-2026-05-29",
    )


def test_valid_rehearsal_packet_passes_safety_validation() -> None:
    packet = _build_packet()

    assert validate_guardrail_recompilation_rehearsal_safety(packet) == []
    require_guardrail_recompilation_rehearsal_safety(packet)


def test_safety_validation_rejects_uncited_predicate_diff() -> None:
    packet = _build_packet()
    packet["predicate_diff_candidates"][0]["source_evidence_ids"] = []

    codes = finding_codes(validate_guardrail_recompilation_rehearsal_safety(packet))

    assert "uncited_predicate_diff" in codes


def test_safety_validation_rejects_unknown_requirement_and_process_ids() -> None:
    packet = _build_packet()
    packet["source_requirement_candidate_ids"] = ["known-requirement-diff"]
    packet["predicate_diff_candidates"][0]["source_requirement_ids"] = ["unknown-requirement-diff"]
    packet["predicate_diff_candidates"][0]["affected_process_ids"] = ["unknown-process"]

    codes = finding_codes(validate_guardrail_recompilation_rehearsal_safety(packet))

    assert "unknown_requirement_id" in codes
    assert "unknown_process_id" in codes


def test_safety_validation_rejects_stale_current_evidence_without_acknowledgement() -> None:
    packet = _build_packet()
    packet["source_evidence_registry"] = [
        {
            "source_evidence_id": "source-evidence.stale-current",
            "freshness_status": "stale",
            "evidence_role": "current_source_evidence",
        }
    ]

    codes = finding_codes(validate_guardrail_recompilation_rehearsal_safety(packet))

    assert "stale_current_evidence_unacknowledged" in codes

    acknowledged = copy.deepcopy(packet)
    acknowledged["source_evidence_registry"][0]["stale_current_evidence_acknowledged"] = True
    assert "stale_current_evidence_unacknowledged" not in finding_codes(
        validate_guardrail_recompilation_rehearsal_safety(acknowledged)
    )


def test_safety_validation_rejects_private_facts_execution_claims_and_guarantees() -> None:
    packet = _build_packet()
    packet["private_case_facts"] = {"owner_name": "redacted"}
    packet["compiler_evidence"] = {"live_compiler_execution_claimed": True}
    packet["reviewer_note"] = "This guarantees approval and the permit will be approved."

    codes = finding_codes(validate_guardrail_recompilation_rehearsal_safety(packet))

    assert "private_case_facts_present" in codes
    assert "live_execution_claim" in codes
    assert "outcome_guarantee" in codes


def test_safety_validation_rejects_enabled_consequential_actions_and_mutation_flags() -> None:
    packet = _build_packet()
    packet["blocked_action_expectations"][0]["enabled"] = True
    packet["activation_state"]["active_guardrail_bundle_mutation_enabled"] = True

    codes = finding_codes(validate_guardrail_recompilation_rehearsal_safety(packet))

    assert "consequential_action_enabled" in codes
    assert "active_guardrail_bundle_mutation_enabled" in codes
