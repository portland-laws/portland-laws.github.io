"""Fixture-first guardrail consumer integration checklist.

This module consumes already-sanitized PP&D guardrail activation decisions,
requirement-regeneration promotion decisions, and safe-next-action release notes.
It emits cited API contract expectations for downstream guardrail consumers
without enabling live enforcement or mutating active guardrail bundles.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping

from ppd.logic.safe_next_action_release_notes import assert_valid_release_notes_packet


PACKET_TYPE = "ppd.guardrail_consumer_integration_checklist.v1"
REQUIRED_INPUTS = (
    "guardrail_activation_decision",
    "requirement_regeneration_promotion_decision",
    "safe_next_action_release_notes",
)
REQUIRED_EXPECTATION_IDS = (
    "missing_facts",
    "stale_evidence",
    "local_pdf_preview",
    "devhub_read_only_review",
    "refused_consequential_actions",
    "manual_handoffs",
    "disabled_live_enforcement",
)
CONSEQUENTIAL_ACTIONS = (
    "payment",
    "upload",
    "submission",
    "scheduling",
    "cancellation",
    "certification",
)
FORBIDDEN_KEYS = {
    "auth_state",
    "browser_session",
    "case_facts",
    "cookie",
    "credentials",
    "downloaded_document",
    "field_value",
    "har",
    "known_facts",
    "local_path",
    "password",
    "private_case_fact",
    "private_case_facts",
    "raw_body",
    "raw_crawl_output",
    "raw_html",
    "screenshot",
    "session_state",
    "storage_state",
    "trace",
    "user_case_fact",
    "value",
}
FORBIDDEN_TEXT = (
    "/home/",
    "/Users/",
    "auth-state",
    "cookie=",
    "password=",
    "private case fact",
    "session=",
    "storage_state",
    "trace.zip",
    ".har",
    ".warc",
    "raw crawl",
    "raw html",
    "raw body",
)
PRIVATE_PATH_RE = re.compile(r"(file://|/home/|/users/|/var/folders/|/tmp/[^\s]+|\\users\\|[a-z]:\\)", re.IGNORECASE)
STALE_WORDS = ("stale", "expired", "outdated", "needs_refresh", "unknown_stale")
CURRENT_WORDS = ("current", "fresh", "validated_current")
ACK_KEYS = ("stale_acknowledged", "reviewer_acknowledged_stale_source", "stale_source_acknowledgement")
DOWNGRADED_STATUSES = ("allowed", "available", "next_safe_action", "ready", "safe", "safe_next_action")
LIVE_EXECUTION_TEXT = (
    "devhub executed",
    "devhub execution completed",
    "executed in devhub",
    "live devhub execution",
    "live llm",
    "llm executed",
    "llm run completed",
)
LIVE_EXECUTION_KEYS = {
    "devhub_execution_completed",
    "devhub_launched",
    "llm_execution_completed",
    "live_devhub_execution",
    "live_llm_execution",
}
CONSEQUENTIAL_CONTROL_KEYS = {
    "cancellation_enabled",
    "certification_enabled",
    "consequential_controls_enabled",
    "enabled_consequential_controls",
    "official_submission_enabled",
    "payment_enabled",
    "scheduling_enabled",
    "submission_enabled",
    "upload_enabled",
}


class GuardrailConsumerIntegrationChecklistError(ValueError):
    """Raised when checklist inputs or outputs violate PP&D guardrails."""


def load_fixture(path: str | Path) -> dict[str, Any]:
    """Load a committed checklist fixture."""

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise GuardrailConsumerIntegrationChecklistError("checklist fixture must be a JSON object")
    return data


def build_guardrail_consumer_integration_checklist(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic cited checklist from fixture packet inputs."""

    input_map = _mapping(inputs.get("inputs")) if "inputs" in inputs else _mapping(inputs)
    missing = [key for key in REQUIRED_INPUTS if key not in input_map]
    if missing:
        raise GuardrailConsumerIntegrationChecklistError("missing required inputs: " + ", ".join(missing))

    activation = deepcopy(_mapping(input_map["guardrail_activation_decision"]))
    promotion = deepcopy(_mapping(input_map["requirement_regeneration_promotion_decision"]))
    release_notes = deepcopy(_mapping(input_map["safe_next_action_release_notes"]))

    input_errors = _input_errors(activation, promotion, release_notes)
    if input_errors:
        raise GuardrailConsumerIntegrationChecklistError("invalid checklist inputs: " + "; ".join(input_errors))

    activation_id = _packet_id(activation, "guardrail-activation-decision")
    promotion_id = _packet_id(promotion, "requirement-regeneration-promotion-decision")
    release_id = _packet_id(release_notes, "safe-next-action-release-notes")
    activation_citations = _citations_from(activation, fallback=activation_id)
    promotion_citations = _citations_from(promotion, fallback=promotion_id)
    release_citations = _citations_from(release_notes, fallback=release_id)

    checklist = {
        "packet_type": PACKET_TYPE,
        "packet_id": "ppd-guardrail-consumer-integration-checklist-2026-05-28",
        "fixture_first": True,
        "metadata_only": True,
        "generated_from_fixtures": True,
        "live_services_called": False,
        "active_guardrail_bundles_changed": False,
        "live_enforcement_enabled": False,
        "inputs_consumed": [
            _consumed_input("guardrail_activation_decision", activation_id, activation_citations),
            _consumed_input("requirement_regeneration_promotion_decision", promotion_id, promotion_citations),
            _consumed_input("safe_next_action_release_notes", release_id, release_citations),
        ],
        "api_contract_expectations": [
            _expectation(
                "missing_facts",
                "agent_gap_analysis_api",
                [activation_id, release_id],
                _merge(activation_citations, release_citations),
                [
                    "Return missing_facts with source_evidence_ids before any draft is treated as ready.",
                    "Ask for unknown, ambiguous, or conflicting user facts instead of inferring them.",
                ],
                [
                    "Do not mark a case ready when required facts are absent.",
                    "Do not expose private user values in the checklist response.",
                ],
            ),
            _expectation(
                "stale_evidence",
                "source_freshness_api",
                [activation_id, promotion_id],
                _merge(activation_citations, promotion_citations),
                [
                    "Return stale_evidence and citation_refresh_scope when cited source evidence is stale.",
                    "Block promotion-facing readiness until reviewer acknowledgement or fixture regeneration is recorded.",
                ],
                [
                    "Do not silently reuse stale evidence for user-facing permitting advice.",
                    "Do not promote regenerated requirements into active bundles from this checklist.",
                ],
            ),
            _expectation(
                "local_pdf_preview",
                "local_pdf_preview_api",
                [activation_id, release_id],
                _merge(activation_citations, release_citations),
                [
                    "Allow deterministic local PDF field previews using redacted fixture facts only.",
                    "Return citation_ids and preview_scope for each proposed local-only mapping.",
                ],
                [
                    "Do not read private local file paths or downloaded documents.",
                    "Do not upload, submit, certify, or attach a preview to an official record.",
                ],
            ),
            _expectation(
                "devhub_read_only_review",
                "devhub_read_only_review_api",
                [activation_id, release_id],
                _merge(activation_citations, release_citations),
                [
                    "Permit only cited read-only review summaries for DevHub surfaces.",
                    "Require attended manual login before any future authenticated live review.",
                ],
                [
                    "Do not launch DevHub or open an authenticated session from this checklist.",
                    "Do not click, fill, save, upload, submit, schedule, cancel, certify, or pay in DevHub.",
                ],
            ),
            _expectation(
                "refused_consequential_actions",
                "action_policy_api",
                [activation_id, release_id],
                _merge(activation_citations, release_citations),
                [
                    "Return refused_action for payment, upload, submission, scheduling, cancellation, and certification requests.",
                    "Include blocked_actions and citations explaining the refusal boundary.",
                ],
                [
                    "Do not convert consequential official actions into safe next actions.",
                    "Do not accept exact confirmation as sufficient for unattended execution.",
                ],
                refused_actions=list(CONSEQUENTIAL_ACTIONS),
            ),
            _expectation(
                "manual_handoffs",
                "manual_handoff_api",
                [promotion_id, release_id],
                _merge(promotion_citations, release_citations),
                [
                    "Return manual_handoff_required for official, financial, certification, upload, and scheduling workflows.",
                    "Name the reviewer or user-attended decision point before live work resumes.",
                ],
                [
                    "Do not store credentials, browser state, screenshots, traces, HAR files, or private field values.",
                    "Do not claim the handoff completed an official PP&D action.",
                ],
            ),
            _expectation(
                "disabled_live_enforcement",
                "guardrail_enforcement_api",
                [activation_id, promotion_id, release_id],
                _merge(activation_citations, promotion_citations, release_citations),
                [
                    "Expose live_enforcement_enabled as false for every checklist expectation.",
                    "Expose active_guardrail_bundles_changed as false and guardrail_bundle_mutation_allowed as false.",
                ],
                [
                    "Do not activate live guardrail enforcement from decision or release-note packets.",
                    "Do not mutate active guardrail bundles, active requirements, or active process models.",
                ],
            ),
        ],
        "disabled_live_actions": _merge(
            _string_list(release_notes.get("disabled_live_actions")),
            ["live_guardrail_enforcement", "active_guardrail_bundle_mutation"],
        ),
        "consumer_validation_summary": {
            "required_expectation_count": len(REQUIRED_EXPECTATION_IDS),
            "all_expectations_cited": True,
            "consequential_actions_refused": list(CONSEQUENTIAL_ACTIONS),
            "live_enforcement_enabled": False,
            "active_guardrail_bundles_changed": False,
        },
    }

    errors = validate_guardrail_consumer_integration_checklist(checklist)
    if errors:
        raise GuardrailConsumerIntegrationChecklistError("invalid checklist output: " + "; ".join(errors))
    return checklist


def validate_guardrail_consumer_integration_checklist(packet: Mapping[str, Any]) -> list[str]:
    """Return deterministic validation errors for a checklist packet."""

    errors: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        errors.append(f"packet_type must be {PACKET_TYPE}")
    for key in ("fixture_first", "metadata_only", "generated_from_fixtures"):
        if packet.get(key) is not True:
            errors.append(f"{key} must be true")
    for key in ("live_services_called", "active_guardrail_bundles_changed", "live_enforcement_enabled"):
        if packet.get(key) is not False:
            errors.append(f"{key} must be false")

    consumed = [_mapping(item) for item in _sequence(packet.get("inputs_consumed"))]
    consumed_roles = {item.get("input_role") for item in consumed}
    for role in REQUIRED_INPUTS:
        if role not in consumed_roles:
            errors.append(f"inputs_consumed missing {role}")
    for index, item in enumerate(consumed):
        if not _text(item.get("source_packet_id")):
            errors.append(f"inputs_consumed[{index}].source_packet_id is required")
        if not _string_list(item.get("citations")):
            errors.append(f"inputs_consumed[{index}].citations must be non-empty")

    expectations = [_mapping(item) for item in _sequence(packet.get("api_contract_expectations"))]
    expectation_ids = [str(item.get("expectation_id") or "") for item in expectations]
    if expectation_ids != list(REQUIRED_EXPECTATION_IDS):
        errors.append("api_contract_expectations must appear in the required deterministic order")
    for index, item in enumerate(expectations):
        base = f"api_contract_expectations[{index}]"
        if not _text(item.get("api_surface")):
            errors.append(f"{base}.api_surface is required")
        if not _string_list(item.get("source_packet_ids")):
            errors.append(f"{base}.source_packet_ids must be non-empty")
        if not _string_list(item.get("citations")):
            errors.append(f"{base}.citations must be non-empty")
        if not _string_list(item.get("consumer_must")):
            errors.append(f"{base}.consumer_must must be non-empty")
        if not _string_list(item.get("consumer_must_not")):
            errors.append(f"{base}.consumer_must_not must be non-empty")
        if item.get("live_enforcement_enabled") is not False:
            errors.append(f"{base}.live_enforcement_enabled must be false")
        if item.get("guardrail_bundle_mutation_allowed") is not False:
            errors.append(f"{base}.guardrail_bundle_mutation_allowed must be false")

    refused = next((item for item in expectations if item.get("expectation_id") == "refused_consequential_actions"), {})
    refused_actions = set(_string_list(refused.get("refused_actions")))
    for action in CONSEQUENTIAL_ACTIONS:
        if action not in refused_actions:
            errors.append(f"refused_consequential_actions must refuse {action}")

    summary = _mapping(packet.get("consumer_validation_summary", {}))
    if summary.get("live_enforcement_enabled") is not False:
        errors.append("consumer_validation_summary.live_enforcement_enabled must be false")
    if summary.get("active_guardrail_bundles_changed") is not False:
        errors.append("consumer_validation_summary.active_guardrail_bundles_changed must be false")

    errors.extend(_manual_handoff_expectation_errors(expectations))
    errors.extend(_unsafe_control_errors(packet))
    errors.extend(_blocked_action_downgrade_errors(packet))
    errors.extend(_stale_current_errors(packet))
    errors.extend(_unsafe_content_errors(packet))
    return errors


def assert_valid_guardrail_consumer_integration_checklist(packet: Mapping[str, Any]) -> None:
    """Raise when a checklist packet is not safe for PP&D agent consumers."""

    errors = validate_guardrail_consumer_integration_checklist(packet)
    if errors:
        raise GuardrailConsumerIntegrationChecklistError("; ".join(errors))


def _input_errors(activation: Mapping[str, Any], promotion: Mapping[str, Any], release_notes: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if not _text(activation.get("packet_id")):
        errors.append("guardrail activation decision must include packet_id")
    if activation.get("live_enforcement_enabled") is not False:
        errors.append("guardrail activation decision must keep live_enforcement_enabled false")
    if activation.get("active_guardrail_bundle_mutated") is not False:
        errors.append("guardrail activation decision must not mutate active guardrail bundles")
    if activation.get("activation_allowed") not in (None, False):
        errors.append("guardrail activation decision must not allow activation")

    if not _text(promotion.get("packet_id")):
        errors.append("requirement regeneration promotion decision must include packet_id")
    if promotion.get("blocked_downstream_activation") is not True:
        errors.append("requirement regeneration promotion decision must block downstream activation")
    if promotion.get("activation_allowed") is not False:
        errors.append("requirement regeneration promotion decision must not allow activation")
    if promotion.get("active_guardrail_bundle_mutated") is not False:
        errors.append("requirement regeneration promotion decision must not mutate active guardrail bundles")

    try:
        assert_valid_release_notes_packet(release_notes)
    except ValueError as exc:
        errors.append("safe-next-action release notes failed validation: " + str(exc))
    if not _string_list(release_notes.get("disabled_live_actions")):
        errors.append("safe-next-action release notes must list disabled_live_actions")

    errors.extend(_unsafe_control_errors(activation))
    errors.extend(_unsafe_control_errors(promotion))
    errors.extend(_unsafe_control_errors(release_notes))
    errors.extend(_unsafe_content_errors(activation))
    errors.extend(_unsafe_content_errors(promotion))
    errors.extend(_unsafe_content_errors(release_notes))
    return errors


def _expectation(
    expectation_id: str,
    api_surface: str,
    source_packet_ids: list[str],
    citations: list[str],
    consumer_must: list[str],
    consumer_must_not: list[str],
    **extra: Any,
) -> dict[str, Any]:
    record = {
        "expectation_id": expectation_id,
        "api_surface": api_surface,
        "source_packet_ids": source_packet_ids,
        "citations": citations,
        "consumer_must": consumer_must,
        "consumer_must_not": consumer_must_not,
        "fixture_first": True,
        "metadata_only": True,
        "live_enforcement_enabled": False,
        "guardrail_bundle_mutation_allowed": False,
    }
    record.update(extra)
    return record


def _consumed_input(role: str, packet_id: str, citations: list[str]) -> dict[str, Any]:
    return {
        "input_role": role,
        "source_packet_id": packet_id,
        "citations": citations,
        "metadata_only": True,
        "live_execution_allowed": False,
    }


def _citations_from(packet: Mapping[str, Any], *, fallback: str) -> list[str]:
    citations: list[str] = []
    citations.extend(_string_list(packet.get("citations")))
    citations.extend(_string_list(packet.get("source_evidence_ids")))
    citations.extend(_strings_from_records(packet.get("citation_refresh_scope"), ("citation", "source_id", "source_evidence_id")))
    citations.extend(_strings_from_records(packet.get("change_citation_audit"), ("citation", "source_id", "source_evidence_id")))
    citations.extend(_strings_from_records(packet.get("readiness_claims"), ("citation", "source_id", "source_evidence_id")))
    if not citations:
        citations.append("packet:" + fallback)
    return _merge(citations)


def _strings_from_records(value: Any, keys: Iterable[str]) -> list[str]:
    output: list[str] = []
    for item in _sequence(value):
        if not isinstance(item, Mapping):
            continue
        for key in keys:
            output.extend(_string_list(item.get(key)))
    return output


def _manual_handoff_expectation_errors(expectations: list[Mapping[str, Any]]) -> list[str]:
    manual = next((item for item in expectations if item.get("expectation_id") == "manual_handoffs"), {})
    refused = next((item for item in expectations if item.get("expectation_id") == "refused_consequential_actions"), {})
    errors: list[str] = []
    manual_text = _expectation_text(manual)
    refused_text = _expectation_text(refused)
    if "manual_handoff_required" not in manual_text and "manual handoff" not in manual_text:
        errors.append("manual_handoffs expectation must require manual handoff")
    if "official" not in manual_text or "financial" not in manual_text:
        errors.append("manual_handoffs expectation must cover official and financial workflows")
    if "manual" not in refused_text or "exact confirmation" not in refused_text:
        errors.append("refused_consequential_actions must preserve manual handoff and exact-confirmation expectations")
    return errors


def _unsafe_control_errors(value: Any) -> list[str]:
    errors: list[str] = []
    for path, key, item in _walk(value):
        key_text = str(key or "")
        if key_text in LIVE_EXECUTION_KEYS and item not in (None, False, "", [], {}):
            errors.append(f"live LLM or DevHub execution claim at {path}")
        if key_text in CONSEQUENTIAL_CONTROL_KEYS and item not in (None, False, "", [], {}):
            errors.append(f"enabled consequential control at {path}")
        if isinstance(item, str):
            lowered = item.lower()
            if any(token in lowered for token in LIVE_EXECUTION_TEXT):
                errors.append(f"live LLM or DevHub execution claim at {path}")
    return errors


def _blocked_action_downgrade_errors(value: Any) -> list[str]:
    errors: list[str] = []
    for path, key, item in _walk(value):
        if key == "blocked_actions" and isinstance(item, list):
            for index, action in enumerate(item):
                if not isinstance(action, Mapping):
                    continue
                action_text = " ".join(
                    str(action.get(field) or "").lower()
                    for field in ("action", "action_id", "classification", "status", "decision")
                )
                is_consequential = any(term in action_text for term in CONSEQUENTIAL_ACTIONS)
                is_downgraded = any(status in action_text for status in DOWNGRADED_STATUSES)
                if is_consequential and is_downgraded:
                    errors.append(f"blocked consequential action is downgraded at {path}[{index}]")
    return errors


def _stale_current_errors(value: Any) -> list[str]:
    errors: list[str] = []
    for path, _, item in _walk(value):
        if not isinstance(item, Mapping):
            continue
        status_values = [
            str(item.get(key) or "").lower()
            for key in ("freshness_status", "source_status", "validation_status")
        ]
        marked_current = any(status in CURRENT_WORDS for status in status_values)
        item_text = " ".join(str(v).lower() for v in item.values() if isinstance(v, (str, int, float, bool)))
        mentions_stale = any(word in item_text for word in STALE_WORDS) or bool(_sequence(item.get("stale_evidence")))
        acknowledged = any(item.get(key) is True for key in ACK_KEYS)
        if marked_current and mentions_stale and not acknowledged:
            errors.append(f"stale source is marked current without acknowledgement at {path}")
    return errors


def _unsafe_content_errors(value: Any) -> list[str]:
    errors: list[str] = []
    for path, key, item in _walk(value):
        key_text = str(key or "")
        if key_text in FORBIDDEN_KEYS and item not in (None, False, "", [], {}):
            errors.append(f"unsafe private or raw field at {path}")
        if isinstance(item, str):
            lowered = item.lower()
            if PRIVATE_PATH_RE.search(item):
                errors.append(f"unsafe private or raw reference at {path}")
                continue
            for token in FORBIDDEN_TEXT:
                if token.lower() in lowered:
                    errors.append(f"unsafe private or raw reference at {path}")
                    break
    return errors


def _expectation_text(expectation: Mapping[str, Any]) -> str:
    pieces: list[str] = []
    for key in ("consumer_must", "consumer_must_not", "refused_actions"):
        pieces.extend(_string_list(expectation.get(key)))
    return " ".join(pieces).lower().replace("-", " ")


def _walk(value: Any, path: str = "$", key: str | None = None) -> Iterable[tuple[str, str | None, Any]]:
    yield path, key, value
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_path = f"{path}.{child_key}"
            yield from _walk(child_value, child_path, str(child_key))
    elif isinstance(value, list):
        for index, child_value in enumerate(value):
            yield from _walk(child_value, f"{path}[{index}]", None)


def _packet_id(packet: Mapping[str, Any], fallback: str) -> str:
    return _text(packet.get("packet_id")) or _text(packet.get("decision_id")) or fallback


def _mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise GuardrailConsumerIntegrationChecklistError("expected JSON object")
    return dict(value)


def _sequence(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return []


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def _merge(*groups: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for group in groups:
        for item in group:
            text = str(item).strip()
            if text and text not in seen:
                merged.append(text)
                seen.add(text)
    return merged


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""
