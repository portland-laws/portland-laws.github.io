"""Fixture-first validation for guardrail bundle activation rehearsals.

This module validates rehearsal packets only. It does not promote, activate,
write, or mutate any guardrail bundle state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
import json


class ActivationRehearsalError(ValueError):
    """Raised when a rehearsal packet is incomplete or unsafe."""


HIGH_RISK_ACTIONS = {"payment", "upload", "submission", "scheduling", "cancellation", "certification"}
UNRESOLVED_REVIEW_STATUSES = {"", "blocked", "needs_review", "open", "pending", "unresolved"}
ACTIVATED_STATUSES = {"active", "activated", "production_ready", "ready_for_activation"}
PRIVATE_CLASSIFICATIONS = {"private", "private_case_fact", "confidential", "sensitive", "user_private"}
PRIVATE_VALUE_KEYS = {"answer", "case_fact_value", "entered_value", "field_value", "private_value", "raw_value", "user_input", "user_supplied_value", "value"}
PRIVATE_PATH_MARKERS = ("/home/", "/Users/", "auth-state", "cookie", "trace", "har", "screenshot")


def load_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise ActivationRehearsalError("rehearsal packet must be a JSON object")
    return packet


def predicate_names(packet: Mapping[str, Any], side: str) -> set[str]:
    predicates = packet.get("predicate_diff", {}).get(side, [])
    if not isinstance(predicates, list):
        raise ActivationRehearsalError(f"predicate_diff.{side} must be a list")
    names: set[str] = set()
    for predicate in predicates:
        if not isinstance(predicate, Mapping) or not isinstance(predicate.get("name"), str):
            raise ActivationRehearsalError(f"predicate_diff.{side} entries must have string names")
        names.add(predicate["name"])
    return names


def validate_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if packet.get("packet_type") != "guardrail_bundle_activation_rehearsal":
        errors.append("packet_type must be guardrail_bundle_activation_rehearsal")
    activation_status = _norm(packet.get("activation_status"))
    if activation_status != "disabled_by_default":
        errors.append("activation_status must remain disabled_by_default")
    errors.extend(_active_bundle_mutation_errors(packet))
    errors.extend(_consumption_errors(packet))
    errors.extend(_predicate_diff_errors(packet))
    errors.extend(_high_risk_action_errors(packet))
    errors.extend(_private_case_fact_errors(packet))
    errors.extend(_review_item_errors(packet, activation_status))
    citations = packet.get("citation_coverage", {})
    if not isinstance(citations, Mapping):
        errors.append("citation_coverage must be an object")
    elif citations.get("required_citations") != citations.get("covered_citations") or citations.get("missing_citations"):
        errors.append("citation coverage must cover every required citation")
    rollback = packet.get("rollback_notes", [])
    if not isinstance(rollback, list) or not rollback:
        errors.append("rollback notes are required")
    return errors


def assert_valid_packet(packet: Mapping[str, Any]) -> None:
    errors = validate_packet(packet)
    if errors:
        raise ActivationRehearsalError("; ".join(errors))


def _active_bundle_mutation_errors(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if packet.get("mutates_active_bundles") is not False:
        errors.append("mutates_active_bundles must be false")
    if packet.get("active_bundle_mutation") is True or packet.get("writes_active_bundle") is True:
        errors.append("activation rehearsal must not mutate active bundles")
    for key in ("active_bundle_changes", "active_bundle_replacement", "active_guardrail_bundle"):
        if packet.get(key) not in (None, [], {}):
            errors.append(f"activation rehearsal must not include {key}")
    return errors


def _consumption_errors(packet: Mapping[str, Any]) -> list[str]:
    consumed = packet.get("consumes", {})
    if not isinstance(consumed, Mapping):
        return ["consumes must be an object"]
    errors: list[str] = []
    if not consumed.get("promotion_review_fixture"):
        errors.append("promotion review fixture reference is required")
    if not consumed.get("agent_readiness_contract_fixture"):
        errors.append("agent-facing readiness contract fixture reference is required")
    if consumed.get("consumption_mode") != "fixture_only":
        errors.append("consumption_mode must be fixture_only")
    links = consumed.get("readiness_contract_links")
    if not isinstance(links, list) or not links:
        errors.append("readiness_contract_links are required")
        return errors
    for index, link in enumerate(links):
        if not isinstance(link, Mapping):
            errors.append(f"readiness_contract_links[{index}] must be an object")
            continue
        link_id = str(link.get("link_id") or f"readiness_contract_links[{index}]")
        if not link.get("fixture_path") and not link.get("contract_id"):
            errors.append(f"readiness contract link {link_id} must include a fixture_path or contract_id")
        if not _strings(link.get("source_evidence_ids")):
            errors.append(f"readiness contract link {link_id} must cite source evidence")
        if _norm(link.get("freshness_status")) != "current":
            errors.append(f"readiness contract link {link_id} must be current")
        if link.get("stale") is True:
            errors.append(f"readiness contract link {link_id} is stale")
    return errors


def _predicate_diff_errors(packet: Mapping[str, Any]) -> list[str]:
    try:
        draft_names = predicate_names(packet, "draft")
        active_names = predicate_names(packet, "active")
    except ActivationRehearsalError as exc:
        return [str(exc)]
    diff = packet.get("predicate_diff", {})
    if not isinstance(diff, Mapping):
        return ["predicate_diff must be an object"]
    recorded = diff.get("recorded_changes", {})
    if not isinstance(recorded, Mapping):
        return ["predicate_diff.recorded_changes must be an object"]
    errors: list[str] = []
    added = sorted(_strings(recorded.get("added")))
    removed = sorted(_strings(recorded.get("removed")))
    changed = sorted(_strings(recorded.get("changed")))
    if sorted(draft_names - active_names) != added:
        errors.append("predicate_diff.recorded_changes.added does not match draft-active diff")
    if sorted(active_names - draft_names) != removed:
        errors.append("predicate_diff.recorded_changes.removed does not match active-draft diff")
    citations = diff.get("diff_citations", {})
    if not isinstance(citations, Mapping):
        errors.append("predicate_diff.diff_citations must cite every recorded predicate diff")
        citations = {}
    for name in added + removed + changed:
        if not _strings(citations.get(name)):
            errors.append(f"predicate diff is uncited: {name}")
    return errors


def _high_risk_action_errors(packet: Mapping[str, Any]) -> list[str]:
    refused = packet.get("refused_consequential_actions", [])
    gates = packet.get("exact_confirmation_gates", [])
    errors: list[str] = []
    if not isinstance(refused, list):
        errors.append("refused_consequential_actions must be a list")
        refused = []
    if not isinstance(gates, list):
        errors.append("exact_confirmation_gates must be a list")
        gates = []
    refused_categories = {_action_category(item) for item in refused if isinstance(item, Mapping) and item.get("refused") is True}
    gate_categories = {_action_category(item) for item in gates if isinstance(item, Mapping) and item.get("required") is True and item.get("exact_phrase")}
    for action in sorted(HIGH_RISK_ACTIONS):
        if action not in refused_categories:
            errors.append(f"high-risk action {action} is missing a refusal rule")
        if action not in gate_categories:
            errors.append(f"high-risk action {action} is missing an exact-confirmation gate")
    return errors


def _private_case_fact_errors(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("case_facts", "known_facts", "private_case_facts", "user_case_facts"):
        value = packet.get(key)
        if value not in (None, [], {}):
            _scan_private(value, key, errors)
    return errors


def _review_item_errors(packet: Mapping[str, Any], activation_status: str) -> list[str]:
    review_items = packet.get("review_items", [])
    if review_items in (None, []):
        return []
    if not isinstance(review_items, list):
        return ["review_items must be a list"]
    errors: list[str] = []
    for index, item in enumerate(review_items):
        if not isinstance(item, Mapping):
            errors.append(f"review_items[{index}] must be an object")
            continue
        item_id = item.get("item_id") or f"review_items[{index}]"
        status = _norm(item.get("status"))
        marked_activated = item.get("marked_activated") is True or _norm(item.get("activation_mark")) in ACTIVATED_STATUSES
        if status in UNRESOLVED_REVIEW_STATUSES and (activation_status in ACTIVATED_STATUSES or marked_activated):
            errors.append(f"unresolved review item is marked activated: {item_id}")
    return errors


def _scan_private(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        if _norm(value.get("privacy_classification") or value.get("classification")) in PRIVATE_CLASSIFICATIONS:
            errors.append(f"private case fact is not allowed: {path}")
        for key, child in value.items():
            key_text = str(key)
            if key_text.lower() in PRIVATE_VALUE_KEYS and child not in (None, "", [], {}):
                errors.append(f"private case fact value is not allowed: {path}.{key_text}")
            _scan_private(child, f"{path}.{key_text}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_private(child, f"{path}[{index}]", errors)
    elif isinstance(value, str) and any(marker in value for marker in PRIVATE_PATH_MARKERS):
        errors.append(f"private local path or artifact marker is not allowed: {path}")


def _action_category(record: Mapping[str, Any]) -> str:
    return _norm(record.get("action_category") or record.get("category") or record.get("action_type") or record.get("action"))


def _norm(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]
