"""Fixture-first safe read-only agent action transcript packets.

This module consumes committed review/handoff/reconciliation fixtures and emits a
commit-safe transcript packet. It never calls an LLM, opens DevHub, reads private
case files, mutates prompts, or enables consequential actions.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any, Mapping


PACKET_TYPE = "ppd.safe_read_only_agent_action_transcript_packet.v1"
MODE = "fixture_first_safe_read_only_agent_action_transcript"

_REQUIRED_SOURCE_PACKET_KEYS = (
    "release_acceptance_review_packet",
    "agent_release_consumer_handoff_packet",
    "devhub_read_only_pilot_reconciliation_packet",
)

_REQUIRED_FALSE_ATTESTATIONS = (
    "llm_execution_enabled",
    "devhub_execution_enabled",
    "prompt_mutation_enabled",
    "consequential_controls_enabled",
    "crawler_execution_enabled",
    "processor_execution_enabled",
    "guardrail_mutation_enabled",
    "surface_registry_mutation_enabled",
    "agent_state_mutation_enabled",
)

_REQUIRED_TRUE_ATTESTATIONS = (
    "fixture_first_inputs_only",
    "offline_only",
    "read_only_only",
    "no_live_llm",
    "no_devhub_launch",
    "no_prompt_mutation",
    "no_private_case_facts",
    "no_raw_authenticated_values",
    "no_local_private_paths",
)

_FORBIDDEN_TEXT = re.compile(
    r"(/home/|/Users/|auth[_-]?state|storage[_-]?state|trace\.zip|\.har\b|screenshot|credential|password|cookie|raw authenticated)",
    re.IGNORECASE,
)

_CONSEQUENTIAL = re.compile(
    r"\b(upload|submit|certif|pay|payment|schedule|cancel|withdraw|purchase|reactivat|extension)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TranscriptPacketValidationResult:
    ok: bool
    errors: tuple[str, ...]


class TranscriptPacketError(ValueError):
    """Raised when a transcript packet cannot be built from safe fixtures."""


def load_json_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise TranscriptPacketError("packet fixture must be a JSON object")
    return packet


def build_safe_read_only_agent_action_transcript_packet(
    release_acceptance_review_packet: Mapping[str, Any],
    agent_release_consumer_handoff_packet: Mapping[str, Any] | None = None,
    devhub_read_only_pilot_reconciliation_packet: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a cited, fixture-only safe read-only transcript packet."""

    if agent_release_consumer_handoff_packet is None and devhub_read_only_pilot_reconciliation_packet is None:
        inputs = _mapping(release_acceptance_review_packet)
        release_acceptance_review_packet = _mapping(inputs.get("release_acceptance_review_packet"))
        agent_release_consumer_handoff_packet = _mapping(inputs.get("agent_release_consumer_handoff_packet"))
        devhub_read_only_pilot_reconciliation_packet = _mapping(inputs.get("devhub_read_only_pilot_reconciliation_packet"))
    else:
        release_acceptance_review_packet = _mapping(release_acceptance_review_packet)
        agent_release_consumer_handoff_packet = _mapping(agent_release_consumer_handoff_packet)
        devhub_read_only_pilot_reconciliation_packet = _mapping(devhub_read_only_pilot_reconciliation_packet)

    source_packets = {
        "release_acceptance_review_packet": release_acceptance_review_packet,
        "agent_release_consumer_handoff_packet": agent_release_consumer_handoff_packet,
        "devhub_read_only_pilot_reconciliation_packet": devhub_read_only_pilot_reconciliation_packet,
    }
    _assert_safe_source_packets(source_packets)

    packet = {
        "packet_id": "safe-read-only-agent-action-transcript-synthetic-v1",
        "packet_type": PACKET_TYPE,
        "mode": MODE,
        "fixture_first": True,
        "offline_only": True,
        "read_only_only": True,
        "consumed_source_packets": _consumed_source_packets(source_packets),
        "source_evidence_ids": _source_evidence_ids(source_packets),
        "user_question_scenarios": _user_question_scenarios(),
        "source_grounded_read_only_answers": _source_grounded_read_only_answers(),
        "missing_fact_prompts": _missing_fact_prompts(),
        "blocked_consequential_action_explanations": _blocked_consequential_action_explanations(),
        "reviewer_owner_fields": _reviewer_owner_fields(source_packets),
        "reviewer_owner": {
            "owner": "ppd-safe-read-only-agent-reviewer",
            "role": "agent transcript packet reviewer",
            "review_status": "assigned",
        },
        "no_live_llm_no_devhub_no_prompt_mutation_attestations": _attestations(),
        "safe_read_only_attestations": _attestations(),
        "messages": _messages(),
    }
    assert_valid_safe_read_only_agent_action_transcript_packet(packet)
    return packet


def validate_safe_read_only_agent_action_transcript_packet(packet: Mapping[str, Any]) -> TranscriptPacketValidationResult:
    errors: list[str] = []
    if not isinstance(packet, Mapping):
        return TranscriptPacketValidationResult(False, ("packet_must_be_object",))
    if packet.get("packet_type") != PACKET_TYPE:
        errors.append("invalid_packet_type")
    if packet.get("mode") != MODE:
        errors.append("invalid_mode")
    for field in ("fixture_first", "offline_only", "read_only_only"):
        if packet.get(field) is not True:
            errors.append(f"{field}_must_be_true")

    consumed = packet.get("consumed_source_packets")
    if not isinstance(consumed, Mapping):
        errors.append("missing_consumed_source_packets")
    else:
        for key in _REQUIRED_SOURCE_PACKET_KEYS:
            row = consumed.get(key)
            if not isinstance(row, Mapping) or not row.get("packet_id") or row.get("consumed") is not True:
                errors.append("missing_consumed_source_packet")

    evidence_ids = packet.get("source_evidence_ids")
    if not isinstance(evidence_ids, list) or not evidence_ids:
        errors.append("missing_source_evidence_ids")
        evidence = set()
    else:
        evidence = {str(item) for item in evidence_ids}

    _validate_cited_rows(errors, packet.get("user_question_scenarios"), "user_question_scenarios", ("scenario_id", "user_question"), evidence)
    _validate_cited_rows(errors, packet.get("source_grounded_read_only_answers"), "source_grounded_read_only_answers", ("answer_id", "answer"), evidence)
    _validate_cited_rows(errors, packet.get("missing_fact_prompts"), "missing_fact_prompts", ("prompt_id", "prompt"), evidence)
    _validate_cited_rows(errors, packet.get("blocked_consequential_action_explanations"), "blocked_consequential_action_explanations", ("action", "explanation"), evidence)

    owners = packet.get("reviewer_owner_fields")
    if not isinstance(owners, list) or not owners:
        errors.append("missing_reviewer_owner_fields")
    else:
        for owner in owners:
            if not isinstance(owner, Mapping) or not owner.get("owner") or not owner.get("review_scope"):
                errors.append("invalid_reviewer_owner_field")

    attestations = packet.get("no_live_llm_no_devhub_no_prompt_mutation_attestations") or packet.get("safe_read_only_attestations")
    if not isinstance(attestations, Mapping):
        errors.append("missing_attestations")
    else:
        for key in _REQUIRED_TRUE_ATTESTATIONS:
            if attestations.get(key) is not True:
                errors.append(f"{key}_attestation_missing")
        for key in _REQUIRED_FALSE_ATTESTATIONS:
            if attestations.get(key) is not False:
                errors.append(f"{key}_must_be_false")

    _scan_for_unsafe_text(errors, packet)
    return TranscriptPacketValidationResult(ok=not errors, errors=tuple(dict.fromkeys(errors)))


def assert_valid_safe_read_only_agent_action_transcript_packet(packet: Mapping[str, Any]) -> None:
    result = validate_safe_read_only_agent_action_transcript_packet(packet)
    if not result.ok:
        raise TranscriptPacketError("invalid safe read-only transcript packet: " + "; ".join(result.errors))


def _assert_safe_source_packets(source_packets: Mapping[str, Mapping[str, Any]]) -> None:
    for key in _REQUIRED_SOURCE_PACKET_KEYS:
        packet = source_packets.get(key)
        if not isinstance(packet, Mapping) or not packet.get("packet_id"):
            raise TranscriptPacketError(f"{key} with packet_id is required")
        errors: list[str] = []
        _scan_for_unsafe_text(errors, packet)
        if errors:
            raise TranscriptPacketError(f"unsafe source packet {key}: " + "; ".join(errors))


def _consumed_source_packets(source_packets: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        key: {
            "packet_id": _text(packet.get("packet_id")),
            "packet_type": _text(packet.get("packet_type")) or key,
            "consumed": True,
        }
        for key, packet in source_packets.items()
    }


def _source_evidence_ids(source_packets: Mapping[str, Mapping[str, Any]]) -> list[str]:
    ids = [
        "release-acceptance-review",
        "agent-release-consumer-handoff",
        "devhub-read-only-pilot-reconciliation",
        "plan-user-experience",
        "plan-devhub-safe-read-only",
        "plan-devhub-consequential",
        "official-devhub-tools",
        "official-devhub-faq",
        "official-submit-plans",
    ]
    for packet in source_packets.values():
        packet_id = _text(packet.get("packet_id"))
        if packet_id:
            ids.append(packet_id)
    return list(dict.fromkeys(ids))


def _user_question_scenarios() -> list[dict[str, Any]]:
    return [
        {
            "scenario_id": "scenario-read-only-status-review",
            "user_question": "Can you tell me what I can safely review before taking any DevHub action?",
            "classification": "safe_read_only",
            "citations": ["agent-release-consumer-handoff", "plan-devhub-safe-read-only", "devhub-read-only-pilot-reconciliation"],
        },
        {
            "scenario_id": "scenario-missing-document-facts",
            "user_question": "Which plan documents do you still need me to identify?",
            "classification": "missing_fact_prompt",
            "citations": ["agent-release-consumer-handoff", "official-submit-plans"],
        },
        {
            "scenario_id": "scenario-blocked-payment-submit",
            "user_question": "Can you pay or submit this permit for me?",
            "classification": "blocked_consequential_action",
            "citations": ["plan-devhub-consequential", "official-devhub-faq"],
        },
    ]


def _source_grounded_read_only_answers() -> list[dict[str, Any]]:
    return [
        {
            "answer_id": "answer-safe-review-only",
            "scenario_id": "scenario-read-only-status-review",
            "answer": "I can summarize cited PP&D guidance, compare supplied non-private facts with required facts, and describe read-only DevHub status categories when attendance and access are already handled outside this packet.",
            "read_only_scope": ["public guidance summary", "non-private fact gap review", "redacted DevHub observation summary"],
            "citations": ["plan-user-experience", "plan-devhub-safe-read-only", "devhub-read-only-pilot-reconciliation"],
        }
    ]


def _missing_fact_prompts() -> list[dict[str, Any]]:
    return [
        {
            "prompt_id": "prompt-document-readiness",
            "scenario_id": "scenario-missing-document-facts",
            "fact_id": "document_readiness_summary",
            "status": "missing",
            "prompt": "Which drawings, applications, calculations, or supporting documents are ready for review? Provide labels only, not private file paths or document contents.",
            "reason": "Document readiness affects the next safe read-only answer and must not be inferred from incomplete context.",
            "citations": ["official-submit-plans", "agent-release-consumer-handoff"],
        }
    ]


def _blocked_consequential_action_explanations() -> list[dict[str, Any]]:
    return [
        {
            "action": "submit permit request",
            "scenario_id": "scenario-blocked-payment-submit",
            "explanation": "Submitting a permit request is a consequential official action. This packet can provide a cited checklist, but the user must remain responsible for any official submission outside the fixture.",
            "blocked": True,
            "citations": ["plan-devhub-consequential", "official-devhub-faq"],
        },
        {
            "action": "submit payment",
            "scenario_id": "scenario-blocked-payment-submit",
            "explanation": "Payment entry and payment submission are financial actions. This packet cannot enter payment details or execute payment and can only summarize what the user should review manually.",
            "blocked": True,
            "citations": ["plan-devhub-consequential", "official-devhub-faq"],
        },
    ]


def _reviewer_owner_fields(source_packets: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "owner": "ppd-safe-read-only-agent-reviewer",
            "review_scope": "Approve cited user-question scenarios and source-grounded read-only answers.",
            "source_packet_ids": [_text(source_packets["agent_release_consumer_handoff_packet"].get("packet_id"))],
            "citations": ["agent-release-consumer-handoff", "release-acceptance-review"],
        },
        {
            "owner": "ppd-devhub-read-only-reconciliation-reviewer",
            "review_scope": "Confirm DevHub reconciliation evidence remains redacted, read-only, and not promoted to active state.",
            "source_packet_ids": [_text(source_packets["devhub_read_only_pilot_reconciliation_packet"].get("packet_id"))],
            "citations": ["devhub-read-only-pilot-reconciliation"],
        },
    ]


def _attestations() -> dict[str, bool]:
    values = {key: True for key in _REQUIRED_TRUE_ATTESTATIONS}
    values.update({key: False for key in _REQUIRED_FALSE_ATTESTATIONS})
    return values


def _messages() -> list[dict[str, Any]]:
    return [
        {
            "message_id": "ask-user-01",
            "message_type": "ask-user",
            "preflight_outcome": "blocked",
            "text": "I need document readiness labels before giving a next-step answer.",
            "citations": ["official-submit-plans", "agent-release-consumer-handoff"],
            "citation_backed_reasons": [{"reason": "Missing document readiness must be asked for instead of inferred.", "citations": ["official-submit-plans"]}],
            "blocked_official_actions": ["submit permit request"],
            "blocked_action_explanations": [{"action": "submit permit request", "explanation": "Official submission remains blocked and user-controlled.", "citations": ["agent-release-consumer-handoff"]}],
            "next_safe_actions": ["Ask for document labels only."],
            "asked_facts": [{"fact_id": "document_readiness_summary", "status": "missing", "prompt": "Which required document labels are ready?", "reason": "The read-only answer needs a non-private readiness summary.", "citations": ["official-submit-plans"]}],
            "exact_confirmation_gate": {"required": True, "exact_required": True, "default_refusal": True, "confirmation_satisfied": False, "blocked_actions": ["submit permit request"], "required_exact_text": "CONFIRM submit permit request"},
        },
        {
            "message_id": "local-preview-01",
            "message_type": "local-preview",
            "preflight_outcome": "local-preview",
            "text": "I can summarize a local metadata-only checklist without opening DevHub.",
            "citations": ["official-submit-plans"],
            "citation_backed_reasons": [{"reason": "Checklist review can stay local and metadata-only.", "citations": ["official-submit-plans"]}],
            "blocked_official_actions": ["upload documents to official record"],
            "blocked_action_explanations": [{"action": "upload documents to official record", "explanation": "Official upload remains blocked by this packet.", "citations": ["official-submit-plans"]}],
            "next_safe_actions": ["Prepare a cited local checklist."],
            "exact_confirmation_gate": {"required": True, "exact_required": True, "default_refusal": True, "confirmation_satisfied": False, "blocked_actions": ["upload documents to official record"], "required_exact_text": "CONFIRM upload documents to official record"},
        },
        {
            "message_id": "reversible-draft-01",
            "message_type": "reversible-draft",
            "preflight_outcome": "reversible-draft",
            "text": "Draft-only assistance must stop before certification, upload, payment, or submission.",
            "citations": ["plan-devhub-consequential", "agent-release-consumer-handoff"],
            "citation_backed_reasons": [{"reason": "The handoff packet separates reversible drafting from official actions.", "citations": ["agent-release-consumer-handoff"]}],
            "blocked_official_actions": ["certify acknowledgement", "submit permit request", "submit payment"],
            "blocked_action_explanations": [{"action": "certify acknowledgement", "explanation": "Certification remains a user-controlled official action.", "citations": ["plan-devhub-consequential"]}, {"action": "submit permit request", "explanation": "Submission remains blocked by default.", "citations": ["plan-devhub-consequential"]}, {"action": "submit payment", "explanation": "Payment remains manual and outside this packet.", "citations": ["plan-devhub-consequential"]}],
            "next_safe_actions": ["Describe draft boundaries and stop."],
            "exact_confirmation_gate": {"required": True, "exact_required": True, "default_refusal": True, "confirmation_satisfied": False, "blocked_actions": ["certify acknowledgement", "submit permit request", "submit payment"], "required_exact_text": "CONFIRM certify acknowledgement; submit permit request; submit payment"},
        },
        {
            "message_id": "manual-handoff-01",
            "message_type": "manual-handoff",
            "preflight_outcome": "manual-handoff",
            "text": "I can provide a cited checklist, then hand off any official action to the user.",
            "citations": ["plan-devhub-consequential", "official-devhub-faq"],
            "citation_backed_reasons": [{"reason": "Consequential actions require manual user control.", "citations": ["plan-devhub-consequential"]}],
            "blocked_official_actions": ["submit permit request", "schedule inspection"],
            "blocked_action_explanations": [{"action": "submit permit request", "explanation": "The packet cannot perform official submission.", "citations": ["plan-devhub-consequential"]}, {"action": "schedule inspection", "explanation": "Scheduling remains manual outside this fixture.", "citations": ["official-devhub-faq"]}],
            "next_safe_actions": ["Provide a user-controlled review checklist."],
            "exact_confirmation_gate": {"required": True, "exact_required": True, "default_refusal": True, "confirmation_satisfied": False, "blocked_actions": ["submit permit request", "schedule inspection"], "required_exact_text": "CONFIRM submit permit request; schedule inspection"},
        },
        {
            "message_id": "refused-action-01",
            "message_type": "refused-action",
            "preflight_outcome": "refused",
            "text": "I cannot enter payment details or submit a payment. I can summarize cited payment-review considerations for the user.",
            "citations": ["plan-devhub-consequential", "official-devhub-faq"],
            "citation_backed_reasons": [{"reason": "Payment workflows are financial and remain outside agent execution.", "citations": ["plan-devhub-consequential"]}],
            "blocked_official_actions": ["enter payment details", "submit payment"],
            "blocked_action_explanations": [{"action": "enter payment details", "explanation": "Payment details must not be collected or entered by this packet.", "citations": ["plan-devhub-consequential"]}, {"action": "submit payment", "explanation": "Payment submission remains user-performed.", "citations": ["official-devhub-faq"]}],
            "next_safe_actions": ["Summarize what the user should review manually."],
            "exact_confirmation_gate": {"required": True, "exact_required": True, "default_refusal": True, "confirmation_satisfied": False, "blocked_actions": ["enter payment details", "submit payment"], "required_exact_text": "CONFIRM enter payment details; submit payment"},
        },
    ]


def _validate_cited_rows(errors: list[str], rows: Any, field: str, required: tuple[str, ...], evidence: set[str]) -> None:
    if not isinstance(rows, list) or not rows:
        errors.append(f"missing_{field}")
        return
    for row in rows:
        if not isinstance(row, Mapping):
            errors.append(f"invalid_{field}_row")
            continue
        for key in required:
            if not _text(row.get(key)):
                errors.append(f"missing_{field}_{key}")
        citations = row.get("citations")
        if not isinstance(citations, list) or not citations:
            errors.append(f"missing_{field}_citations")
        elif evidence and any(str(citation) not in evidence for citation in citations):
            errors.append(f"unknown_{field}_citation")


def _scan_for_unsafe_text(errors: list[str], value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).lower() in {"private_case_facts", "raw_authenticated_values", "auth_state", "credentials"} and child:
                errors.append("private_or_raw_authenticated_content")
            _scan_for_unsafe_text(errors, child)
    elif isinstance(value, list):
        for child in value:
            _scan_for_unsafe_text(errors, child)
    elif isinstance(value, str):
        if _FORBIDDEN_TEXT.search(value):
            errors.append("private_or_session_artifact")
        live = value.lower()
        if "launched live" in live or "opened devhub" in live or "called live llm" in live:
            errors.append("live_execution_claim")
        if "will be approved" in live or "approval guaranteed" in live:
            errors.append("legal_or_permitting_outcome_guarantee")


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str:
    return str(value or "").strip()
