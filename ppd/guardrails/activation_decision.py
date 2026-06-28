"""Fixture-first guardrail activation decision packet validation.

This module validates reviewer decision records only. It never writes active
bundle state, enables live enforcement, or performs DevHub actions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
import json


PACKET_TYPE = "ppd.guardrail_activation_decision_packet.v1"
REQUIRED_CONSUMED_PACKETS = {"guardrail_activation_rehearsal", "release_gate_status"}
HIGH_RISK_ACTIONS = {"payment", "upload", "submission", "scheduling", "cancellation", "certification"}
REQUIRED_EXACT_CONFIRMATION_GATES = {
    "payment": "payment_confirmation",
    "upload": "upload_confirmation",
    "submission": "submission_confirmation",
    "scheduling": "scheduling_confirmation",
    "cancellation": "cancellation_confirmation",
    "certification": "certification_confirmation",
}
REQUIRED_REFUSAL_ACTIONS = {
    "payment": "enter_or_submit_payment",
    "upload": "upload_or_certify_documents",
    "submission": "submit_devhub_application",
    "scheduling": "schedule_inspection",
    "cancellation": "cancel_or_withdraw",
    "certification": "certify_acknowledgement",
}
ALLOWED_DECISIONS = {"activate", "defer"}
ACTIVATED_STATUSES = {"activated", "active", "approved_for_activation", "live_enforcement_ready"}
UNRESOLVED_BLOCKER_STATUSES = {"blocked", "open", "pending", "unresolved"}
PRIVATE_KEYS = {
    "auth_state",
    "browser_session",
    "case_fact",
    "case_facts",
    "cookie",
    "credentials",
    "field_value",
    "har",
    "known_facts",
    "password",
    "private_case_fact",
    "private_case_facts",
    "raw_crawl_output",
    "raw_html",
    "screenshot",
    "session_state",
    "storage_state",
    "trace",
    "user_case_fact",
    "user_case_facts",
    "value",
}
PRIVATE_TEXT_MARKERS = ("/home/", "/Users/", "auth-state", "storage_state", "cookie", "trace.zip", ".har")
MUTATION_FLAG_KEYS = {
    "active_bundle_mutation",
    "active_guardrail_bundle_mutated",
    "mutates_active_bundle",
    "mutates_active_guardrail_bundle",
    "mutates_active_guardrail_bundles",
    "writes_active_bundle",
    "writes_active_guardrail_bundle",
}


class ActivationDecisionPacketError(ValueError):
    """Raised when a decision packet is incomplete or unsafe."""


def load_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise ActivationDecisionPacketError("activation decision packet must be a JSON object")
    return packet


def validate_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        errors.append(f"packet_type must be {PACKET_TYPE}")
    for key in ("fixture_first", "metadata_only", "generated_from_fixtures"):
        if packet.get(key) is not True:
            errors.append(f"{key} must be true")
    if packet.get("mutates_active_guardrail_bundles") is not False:
        errors.append("mutates_active_guardrail_bundles must be false")
    if packet.get("live_enforcement_enabled") is not False:
        errors.append("live_enforcement_enabled must be false")
    if packet.get("active_bundle_mutation") is True or packet.get("writes_active_bundle") is True:
        errors.append("activation decision packet must not mutate active guardrail bundles")
    for key in ("active_bundle_changes", "active_bundle_replacement", "active_guardrail_bundle"):
        if packet.get(key) not in (None, [], {}):
            errors.append(f"activation decision packet must not include {key}")

    consumed_errors, consumed_evidence_ids = _consumed_packet_errors(packet.get("consumes"))
    errors.extend(consumed_errors)
    errors.extend(_decision_errors(packet.get("reviewer_decisions"), consumed_evidence_ids))
    errors.extend(_coverage_errors(packet, consumed_evidence_ids))
    errors.extend(_release_blocker_errors(packet))
    errors.extend(_disabled_enforcement_errors(packet.get("disabled_live_enforcement")))
    errors.extend(_rollback_errors(packet.get("rollback_notes"), consumed_evidence_ids))
    errors.extend(_private_artifact_errors(packet))
    errors.extend(_mutation_flag_errors(packet))
    return _dedupe(errors)


def assert_valid_packet(packet: Mapping[str, Any]) -> None:
    errors = validate_packet(packet)
    if errors:
        raise ActivationDecisionPacketError("; ".join(errors))


def selected_decisions(packet: Mapping[str, Any]) -> dict[str, str]:
    decisions: dict[str, str] = {}
    for item in _sequence(packet.get("reviewer_decisions")):
        record = _mapping(item)
        bundle_id = _text(record.get("predicate_bundle_id"))
        decision = _text(record.get("selected_decision"))
        if bundle_id and decision:
            decisions[bundle_id] = decision
    return decisions


def _consumed_packet_errors(value: Any) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    evidence_ids: set[str] = set()
    records = _sequence(value)
    if not records:
        return ["consumes must include prerequisite packet links"], evidence_ids
    seen: set[str] = set()
    for index, raw in enumerate(records):
        path = f"consumes[{index}]"
        record = _mapping(raw)
        packet_role = _text(record.get("packet_role"))
        seen.add(packet_role)
        if packet_role not in REQUIRED_CONSUMED_PACKETS:
            errors.append(f"{path}.packet_role must be a required consumed packet")
        for key in ("packet_id", "fixture_path"):
            if not _text(record.get(key)):
                errors.append(f"{path}.{key} is required")
        if packet_role == "guardrail_activation_rehearsal" and "activation_rehearsal" not in _text(record.get("fixture_path")):
            errors.append(f"{path}.fixture_path must link the guardrail activation rehearsal fixture")
        if _text(record.get("freshness_status")) != "current":
            errors.append(f"{path}.freshness_status must be current")
        if record.get("stale") is True:
            errors.append(f"{path} must not be stale")
        record_evidence_ids = set(_strings(record.get("evidence_ids")))
        if not record_evidence_ids:
            errors.append(f"{path}.evidence_ids must be non-empty")
        evidence_ids.update(record_evidence_ids)
    for packet_role in sorted(REQUIRED_CONSUMED_PACKETS - seen):
        errors.append(f"consumes must include {packet_role}")
    return errors, evidence_ids


def _decision_errors(value: Any, consumed_evidence_ids: set[str]) -> list[str]:
    errors: list[str] = []
    decisions = _sequence(value)
    if not decisions:
        return ["reviewer_decisions must be non-empty"]
    for index, raw in enumerate(decisions):
        path = f"reviewer_decisions[{index}]"
        record = _mapping(raw)
        selected_decision = _text(record.get("selected_decision"))
        if not _text(record.get("decision_id")):
            errors.append(f"{path}.decision_id is required")
        if not _text(record.get("predicate_bundle_id")):
            errors.append(f"{path}.predicate_bundle_id is required")
        if selected_decision not in ALLOWED_DECISIONS:
            errors.append(f"{path}.selected_decision must be activate or defer")
        if record.get("applies_to_active_bundle") is not False:
            errors.append(f"{path}.applies_to_active_bundle must be false")
        if record.get("mutates_active_bundle") is not False:
            errors.append(f"{path}.mutates_active_bundle must be false")
        evidence_ids = set(_strings(record.get("source_evidence_ids")))
        if not evidence_ids:
            errors.append(f"{path}.source_evidence_ids must be non-empty")
        for evidence_id in sorted(evidence_ids - consumed_evidence_ids):
            errors.append(f"{path}.source_evidence_ids references uncited evidence {evidence_id}")
        if selected_decision == "activate" and not evidence_ids:
            errors.append(f"{path}.selected_decision activate requires cited source_evidence_ids")
        if not _text(record.get("reason")):
            errors.append(f"{path}.reason is required")
    return errors


def _coverage_errors(packet: Mapping[str, Any], consumed_evidence_ids: set[str]) -> list[str]:
    errors: list[str] = []
    exact = _mapping(packet.get("exact_confirmation_coverage"))
    refused = _mapping(packet.get("refused_consequential_action_coverage"))
    if exact.get("all_required_categories_covered") is not True:
        errors.append("exact_confirmation_coverage.all_required_categories_covered must be true")
    if refused.get("all_required_categories_refused") is not True:
        errors.append("refused_consequential_action_coverage.all_required_categories_refused must be true")
    exact_categories = set(_strings(exact.get("covered_action_categories")))
    refused_categories = set(_strings(refused.get("refused_action_categories")))
    exact_gate_ids = set(_strings(exact.get("source_gate_ids")))
    refusal_actions = set(_strings(refused.get("source_refusal_actions")))
    for action in sorted(HIGH_RISK_ACTIONS):
        if action not in exact_categories:
            errors.append(f"exact confirmation coverage missing {action}")
        required_gate = REQUIRED_EXACT_CONFIRMATION_GATES[action]
        if required_gate not in exact_gate_ids:
            errors.append(f"exact confirmation gate missing {required_gate}")
        if action not in refused_categories:
            errors.append(f"refused consequential-action coverage missing {action}")
        required_refusal = REQUIRED_REFUSAL_ACTIONS[action]
        if required_refusal not in refusal_actions:
            errors.append(f"refusal coverage missing {required_refusal}")
    if exact.get("missing_categories") not in ([], None):
        errors.append("exact_confirmation_coverage.missing_categories must be empty")
    if refused.get("missing_categories") not in ([], None):
        errors.append("refused_consequential_action_coverage.missing_categories must be empty")
    errors.extend(_evidence_ref_errors(exact, "exact_confirmation_coverage", consumed_evidence_ids))
    errors.extend(_evidence_ref_errors(refused, "refused_consequential_action_coverage", consumed_evidence_ids))
    return errors


def _release_blocker_errors(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    decision_status = _text(packet.get("decision_status")).lower()
    selected = set(selected_decisions(packet).values())
    activated = decision_status in ACTIVATED_STATUSES or "activate" in selected or packet.get("live_enforcement_enabled") is True
    if not activated:
        return errors
    for index, raw in enumerate(_sequence(packet.get("release_gate_blockers_acknowledged"))):
        record = _mapping(raw)
        status = _text(record.get("status")).lower()
        if status in UNRESOLVED_BLOCKER_STATUSES:
            errors.append(f"release_gate_blockers_acknowledged[{index}] is unresolved and cannot be marked activated")
    return errors


def _disabled_enforcement_errors(value: Any) -> list[str]:
    record = _mapping(value)
    errors: list[str] = []
    if record.get("enabled") is not False:
        errors.append("disabled_live_enforcement.enabled must be false")
    if _text(record.get("status")) not in {"disabled", "deferred", "manual_handoff_only"}:
        errors.append("disabled_live_enforcement.status must be disabled, deferred, or manual_handoff_only")
    if record.get("allows_official_actions") is not False:
        errors.append("disabled_live_enforcement.allows_official_actions must be false")
    if not _strings(record.get("blocked_action_categories")):
        errors.append("disabled_live_enforcement.blocked_action_categories must be non-empty")
    return errors


def _rollback_errors(value: Any, consumed_evidence_ids: set[str]) -> list[str]:
    notes = _sequence(value)
    if not notes:
        return ["rollback_notes are required"]
    errors: list[str] = []
    for index, raw in enumerate(notes):
        record = _mapping(raw)
        if not _text(record.get("note_id")):
            errors.append(f"rollback_notes[{index}].note_id is required")
        if not _text(record.get("note")):
            errors.append(f"rollback_notes[{index}].note is required")
        evidence_ids = set(_strings(record.get("evidence_ids")))
        if not evidence_ids:
            errors.append(f"rollback_notes[{index}].evidence_ids must be non-empty")
        for evidence_id in sorted(evidence_ids - consumed_evidence_ids):
            errors.append(f"rollback_notes[{index}].evidence_ids references uncited evidence {evidence_id}")
    return errors


def _private_artifact_errors(value: Any, path: str = "packet") -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text.lower() in PRIVATE_KEYS and child not in (None, "", [], {}):
                errors.append(f"{path}.{key_text} uses forbidden private or live artifact field")
            errors.extend(_private_artifact_errors(child, f"{path}.{key_text}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_private_artifact_errors(child, f"{path}[{index}]"))
    elif isinstance(value, str) and any(marker in value for marker in PRIVATE_TEXT_MARKERS):
        errors.append(f"{path} references private/session artifact text")
    return errors


def _mutation_flag_errors(value: Any, path: str = "packet") -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.lower()
            child_path = f"{path}.{key_text}"
            if normalized_key in MUTATION_FLAG_KEYS and child is not False:
                errors.append(f"{child_path} must be false")
            errors.extend(_mutation_flag_errors(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_mutation_flag_errors(child, f"{path}[{index}]"))
    return errors


def _evidence_ref_errors(record: Mapping[str, Any], path: str, consumed_evidence_ids: set[str]) -> list[str]:
    errors: list[str] = []
    evidence_ids = set(_strings(record.get("evidence_ids")))
    if not evidence_ids:
        errors.append(f"{path}.evidence_ids must be non-empty")
    for evidence_id in sorted(evidence_ids - consumed_evidence_ids):
        errors.append(f"{path}.evidence_ids references uncited evidence {evidence_id}")
    return errors


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> tuple[Any, ...]:
    return tuple(value) if isinstance(value, list) else ()


def _strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped
