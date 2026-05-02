"""Fixture-only guardrail compiler for online trade permit purchase tests.

This module intentionally compiles only deterministic fixture data. It does not
open DevHub, crawl public sites, authenticate, submit, pay, cancel, certify, or
schedule inspections.
"""

from __future__ import annotations

from typing import Any, Mapping


STOP_CLASSIFICATIONS = {"financial", "consequential"}
REQUIRED_EXACT_CONFIRMATION = "exact_session_confirmation"


def compile_online_trade_purchase_guardrails(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Compile a fixture-backed guardrail report for an online trade permit purchase.

    The fixture is expected to contain a process model and a redacted user case.
    The report is deliberately small and deterministic so tests can prove missing
    information and action gates without touching live DevHub state.
    """

    process = _mapping(fixture.get("process"))
    user_case = _mapping(fixture.get("user_case"))
    facts = _mapping(user_case.get("facts"))
    documents = set(_list(user_case.get("documents")))
    acknowledgments = set(_list(user_case.get("acknowledgments")))
    decisions = set(_list(user_case.get("decisions")))

    missing_facts = []
    for required in _list(process.get("required_facts")):
        item = _mapping(required)
        fact_id = str(item.get("id", ""))
        if not fact_id:
            continue
        value = facts.get(fact_id)
        if value in (None, "", [], {}):
            missing_facts.append(_requested_item(item, "fact"))

    missing_documents = []
    for required in _list(process.get("required_documents")):
        item = _mapping(required)
        document_id = str(item.get("id", ""))
        if document_id and document_id not in documents:
            missing_documents.append(_requested_item(item, "file"))

    missing_acknowledgments = []
    for required in _list(process.get("required_acknowledgments")):
        item = _mapping(required)
        acknowledgment_id = str(item.get("id", ""))
        if acknowledgment_id and acknowledgment_id not in acknowledgments:
            missing_acknowledgments.append(_requested_item(item, "acknowledgment"))

    missing_decisions = []
    for required in _list(process.get("required_decisions")):
        item = _mapping(required)
        decision_id = str(item.get("id", ""))
        if decision_id and decision_id not in decisions:
            missing_decisions.append(_requested_item(item, "decision"))

    action_gates = []
    for gate in _list(process.get("action_gates")):
        item = _mapping(gate)
        action_gates.append(_compile_action_gate(item, user_case))

    return {
        "process_id": str(process.get("id", "")),
        "permit_type": str(process.get("permit_type", "")),
        "missing_facts": missing_facts,
        "missing_documents": missing_documents,
        "missing_acknowledgments": missing_acknowledgments,
        "missing_decisions": missing_decisions,
        "action_gates": action_gates,
        "citation_errors": _citation_errors(process),
    }


def _compile_action_gate(gate: Mapping[str, Any], user_case: Mapping[str, Any]) -> dict[str, Any]:
    confirmations = _mapping(user_case.get("confirmations"))
    gate_id = str(gate.get("id", ""))
    classification = str(gate.get("classification", ""))
    required_confirmation = str(gate.get("requires_confirmation", ""))
    provided_confirmation = str(confirmations.get(gate_id, ""))
    citations = _list(gate.get("citations"))

    requires_stop = classification in STOP_CLASSIFICATIONS or required_confirmation == REQUIRED_EXACT_CONFIRMATION
    allowed = True
    reasons = []
    if requires_stop and provided_confirmation != REQUIRED_EXACT_CONFIRMATION:
        allowed = False
        reasons.append("missing exact session-specific user confirmation")
    if not citations:
        allowed = False
        reasons.append("missing citation-backed action gate evidence")

    return {
        "id": gate_id,
        "action": str(gate.get("action", "")),
        "classification": classification,
        "status": "allowed" if allowed else "blocked",
        "requires_confirmation": required_confirmation,
        "provided_confirmation": provided_confirmation,
        "citations": citations,
        "reasons": reasons,
    }


def _requested_item(item: Mapping[str, Any], item_type: str) -> dict[str, Any]:
    return {
        "id": str(item.get("id", "")),
        "type": item_type,
        "label": str(item.get("label", "")),
        "category": str(item.get("category", "")),
        "citations": _list(item.get("citations")),
    }


def _citation_errors(process: Mapping[str, Any]) -> list[str]:
    errors = []
    collections = (
        ("required_facts", "required fact"),
        ("required_documents", "required document"),
        ("required_acknowledgments", "required acknowledgment"),
        ("required_decisions", "required decision"),
        ("action_gates", "action gate"),
    )
    for key, label in collections:
        for item in _list(process.get(key)):
            mapped = _mapping(item)
            if not _list(mapped.get("citations")):
                errors.append(f"{label} {mapped.get('id', '')} is missing citations")
    return errors


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []
