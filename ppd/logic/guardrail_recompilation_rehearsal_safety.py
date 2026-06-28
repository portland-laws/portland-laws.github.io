"""Safety validation for guardrail recompilation rehearsal packets.

The validators in this module are intentionally packet-shape tolerant. PP&D has
more than one fixture-first rehearsal packet format, but all of them must stay
review-only, cited, public-fact-only, and unable to claim live execution or
mutate active guardrail bundles.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any


_CONSEQUENTIAL_ACTIONS = {
    "cancel permit request",
    "certify acknowledgement",
    "purchase trade permit",
    "request extension",
    "schedule inspection",
    "submit payment",
    "submit permit request",
    "upload corrections",
    "upload permit documents",
    "withdraw permit request",
}

_STALE_VALUES = {
    "expired",
    "needs_recrawl",
    "outdated",
    "stale",
    "stale_current",
    "stale-current",
}

_CURRENT_VALUES = {
    "current",
    "current_evidence",
    "current-source",
    "current_source",
    "current-source-evidence",
    "current_source_evidence",
}

_PRIVATE_VALUES = {
    "account_scoped_private",
    "authenticated_private",
    "case_fact",
    "private",
    "private_authenticated",
    "private_case_fact",
    "user_private",
}

_REQUIREMENT_ID_KEYS = {
    "requirement_id",
    "source_requirement_candidate_id",
    "source_requirement_diff_id",
}

_REQUIREMENT_ID_LIST_KEYS = {
    "requirement_ids",
    "source_requirement_candidate_ids",
    "source_requirement_diff_ids",
    "source_requirement_ids",
}

_KNOWN_REQUIREMENT_ID_KEYS = {
    "known_requirement_ids",
    "reviewed_requirement_candidate_ids",
    "source_requirement_candidate_ids",
    "source_requirement_diff_ids",
}

_PROCESS_ID_KEYS = {
    "process_id",
    "process_model_id",
}

_PROCESS_ID_LIST_KEYS = {
    "affected_process_ids",
    "affected_process_model_ids",
    "source_process_model_fixture_ids",
}

_MUTATION_FLAG_KEYS = {
    "active_bundle_mutated",
    "active_guardrail_bundle_mutated",
    "active_guardrail_bundle_mutation_enabled",
    "active_guardrail_bundle_patch_enabled",
    "active_guardrail_bundle_write_enabled",
    "compile_and_promote_enabled",
    "guardrail_bundle_promotion_enabled",
    "mutation_enabled",
    "promotion_enabled",
}

_LIVE_EXECUTION_KEYS = {
    "compiler_executed",
    "consumer_executed",
    "consumer_execution_claimed",
    "consumer_smoke_test_executed",
    "live_compiler_execution",
    "live_compiler_execution_claimed",
    "live_consumer_execution",
    "live_consumer_execution_claimed",
    "live_execution_claimed",
}

_GUARANTEE_KEYS = {
    "approval_guarantee",
    "guaranteed_outcome",
    "legal_outcome_guarantee",
    "outcome_guarantee",
    "permit_approval_guarantee",
    "permitting_outcome_guarantee",
}

_GUARANTEE_PHRASES = {
    "guarantee approval",
    "guaranteed approval",
    "guaranteed permit",
    "guarantees approval",
    "permit will be approved",
    "will be approved",
}


@dataclass(frozen=True)
class GuardrailRecompilationSafetyFinding:
    code: str
    path: str
    message: str


class GuardrailRecompilationSafetyError(ValueError):
    """Raised when a rehearsal packet contains unsafe claims or references."""


def validate_guardrail_recompilation_rehearsal_safety(packet: Mapping[str, Any]) -> list[GuardrailRecompilationSafetyFinding]:
    """Return safety findings for a guardrail recompilation rehearsal packet."""

    if not isinstance(packet, Mapping):
        return [GuardrailRecompilationSafetyFinding("invalid_packet", "$", "Packet must be an object.")]

    findings: list[GuardrailRecompilationSafetyFinding] = []
    known_requirement_ids = _known_requirement_ids(packet)
    known_process_ids = _known_process_ids(packet)

    for path, value in _walk(packet):
        key = _last_key(path)
        lowered_key = key.lower()

        if key in _MUTATION_FLAG_KEYS and value is not False:
            findings.append(GuardrailRecompilationSafetyFinding("active_guardrail_bundle_mutation_enabled", path, "Active guardrail bundle mutation flags must be false."))

        if key in _LIVE_EXECUTION_KEYS and value:
            findings.append(GuardrailRecompilationSafetyFinding("live_execution_claim", path, "Rehearsal packets must not claim live compiler or consumer execution."))

        if key in _GUARANTEE_KEYS and value:
            findings.append(GuardrailRecompilationSafetyFinding("outcome_guarantee", path, "Rehearsal packets must not include legal or permitting outcome guarantees."))

        if "private_case_fact" in lowered_key or lowered_key in {"case_fact", "case_facts", "known_facts", "user_case_facts"}:
            findings.append(GuardrailRecompilationSafetyFinding("private_case_facts_present", path, "Rehearsal packets must not carry private case facts."))

        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in _PRIVATE_VALUES:
                findings.append(GuardrailRecompilationSafetyFinding("private_case_facts_present", path, "Rehearsal packets must not include private fact classifications."))
            if any(phrase in normalized for phrase in _GUARANTEE_PHRASES):
                findings.append(GuardrailRecompilationSafetyFinding("outcome_guarantee", path, "Rehearsal packets must not guarantee legal or permitting outcomes."))
            if "live compiler" in normalized or "live consumer" in normalized:
                findings.append(GuardrailRecompilationSafetyFinding("live_execution_claim", path, "Rehearsal packets must not claim live compiler or consumer execution."))

    _validate_predicate_diffs(packet, findings)
    _validate_unknown_ids(packet, known_requirement_ids, known_process_ids, findings)
    _validate_stale_current_evidence(packet, findings)
    _validate_consequential_actions(packet, findings)
    return findings


def require_guardrail_recompilation_rehearsal_safety(packet: Mapping[str, Any]) -> None:
    findings = validate_guardrail_recompilation_rehearsal_safety(packet)
    if findings:
        detail = "; ".join(f"{item.code} at {item.path}: {item.message}" for item in findings)
        raise GuardrailRecompilationSafetyError("unsafe guardrail recompilation rehearsal packet: " + detail)


def finding_codes(findings: Iterable[GuardrailRecompilationSafetyFinding]) -> set[str]:
    return {finding.code for finding in findings}


def _validate_predicate_diffs(packet: Mapping[str, Any], findings: list[GuardrailRecompilationSafetyFinding]) -> None:
    diff_groups = (
        ("predicate_diff_candidates", "predicate_diff_id"),
        ("draft_predicate_changes", "predicate_id"),
    )
    for group_key, id_key in diff_groups:
        for index, diff in enumerate(_mapping_list(packet.get(group_key))):
            path = f"$.{group_key}[{index}]"
            if not _text(diff.get(id_key)):
                findings.append(GuardrailRecompilationSafetyFinding("missing_predicate_diff_id", f"{path}.{id_key}", "Predicate diffs must have stable IDs."))
            if not _strings(diff.get("source_evidence_ids")) and not _strings(diff.get("source_requirement_diff_ids")):
                findings.append(GuardrailRecompilationSafetyFinding("uncited_predicate_diff", path, "Predicate diffs must cite source evidence or source requirement diffs."))


def _validate_unknown_ids(
    packet: Mapping[str, Any],
    known_requirement_ids: set[str],
    known_process_ids: set[str],
    findings: list[GuardrailRecompilationSafetyFinding],
) -> None:
    for path, value in _walk(packet):
        key = _last_key(path)
        if key in _REQUIREMENT_ID_KEYS:
            requirement_id = _text(value)
            if known_requirement_ids and requirement_id and requirement_id not in known_requirement_ids:
                findings.append(GuardrailRecompilationSafetyFinding("unknown_requirement_id", path, "Requirement reference is not present in the packet requirement registry."))
        if key in _REQUIREMENT_ID_LIST_KEYS:
            for requirement_id in _strings(value):
                if known_requirement_ids and requirement_id not in known_requirement_ids:
                    findings.append(GuardrailRecompilationSafetyFinding("unknown_requirement_id", path, "Requirement reference is not present in the packet requirement registry."))
                    break
        if key in _PROCESS_ID_KEYS:
            process_id = _text(value)
            if known_process_ids and process_id and process_id not in known_process_ids:
                findings.append(GuardrailRecompilationSafetyFinding("unknown_process_id", path, "Process reference is not present in the packet process registry."))
        if key in _PROCESS_ID_LIST_KEYS:
            for process_id in _strings(value):
                if known_process_ids and process_id not in known_process_ids:
                    findings.append(GuardrailRecompilationSafetyFinding("unknown_process_id", path, "Process reference is not present in the packet process registry."))
                    break


def _validate_stale_current_evidence(packet: Mapping[str, Any], findings: list[GuardrailRecompilationSafetyFinding]) -> None:
    packet_acknowledged = packet.get("stale_current_evidence_acknowledged") is True
    for path, value in _walk(packet):
        if not isinstance(value, Mapping):
            continue
        statuses = {
            _text(value.get("freshness_status")).lower(),
            _text(value.get("source_freshness_status")).lower(),
            _text(value.get("staleness_status")).lower(),
        }
        roles = {
            _text(value.get("evidence_role")).lower(),
            _text(value.get("source_evidence_role")).lower(),
        }
        stale = bool(statuses & _STALE_VALUES)
        current = value.get("current_evidence") is True or value.get("is_current") is True or bool(roles & _CURRENT_VALUES)
        acknowledged = packet_acknowledged or value.get("stale_current_acknowledged") is True or value.get("stale_current_evidence_acknowledged") is True
        if stale and current and not acknowledged:
            findings.append(GuardrailRecompilationSafetyFinding("stale_current_evidence_unacknowledged", path, "Evidence cannot be both current and stale unless the packet explicitly acknowledges the stale-current condition."))


def _validate_consequential_actions(packet: Mapping[str, Any], findings: list[GuardrailRecompilationSafetyFinding]) -> None:
    for path, value in _walk(packet):
        if not isinstance(value, Mapping):
            continue
        action = _text(value.get("action") or value.get("blocked_action") or value.get("action_name")).lower()
        if action not in _CONSEQUENTIAL_ACTIONS:
            continue
        enabled = value.get("enabled") is True or value.get("execution_allowed") is True or value.get("autonomous_execution_allowed") is True
        decision = _text(value.get("expected_decision") or value.get("decision")).lower()
        if enabled or decision in {"allow", "allowed", "execute", "proceed"}:
            findings.append(GuardrailRecompilationSafetyFinding("consequential_action_enabled", path, "Consequential actions must remain blocked until attended exact confirmation."))


def _known_requirement_ids(packet: Mapping[str, Any]) -> set[str]:
    values: set[str] = set()
    for key in _KNOWN_REQUIREMENT_ID_KEYS:
        values.update(_strings(packet.get(key)))
    return values


def _known_process_ids(packet: Mapping[str, Any]) -> set[str]:
    values = set(_strings(packet.get("affected_process_ids")))
    values.update(_strings(packet.get("affected_process_model_ids")))
    values.update(_strings(packet.get("source_process_model_fixture_ids")))
    return values


def _mapping_list(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, Iterable) or isinstance(value, (bytes, Mapping)):
        return []
    return [_text(item) for item in value if _text(item)]


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _last_key(path: str) -> str:
    tail = path.rsplit(".", 1)[-1]
    return tail.split("[", 1)[0]


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = path + "." + str(key)
            yield child_path, child
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, child
            yield from _walk(child, child_path)
