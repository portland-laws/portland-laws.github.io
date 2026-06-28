"""Validation for inactive guardrail recompile staging packet v7.

This module intentionally validates only deterministic packet structure and text.
It does not crawl, authenticate, download artifacts, or mutate guardrails.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class PacketValidationIssue:
    """A deterministic validation failure for staging packet v7."""

    code: str
    message: str


REQUIRED_FIELDS: tuple[tuple[str, str], ...] = (
    ("process_model_impact_queue_refs", "missing process model impact queue references"),
    ("affected_guardrail_bundle_rows", "missing affected GuardrailBundle rows"),
    ("deterministic_predicate_change_placeholders", "missing deterministic predicate change placeholders"),
    ("deontic_rule_review_placeholders", "missing deontic rule review placeholders"),
    ("temporal_rule_review_placeholders", "missing temporal rule review placeholders"),
    ("reversible_action_predicate_preservation_notes", "missing reversible-action predicate preservation notes"),
    ("exact_confirmation_gate_preservation_notes", "missing exact-confirmation gate preservation notes"),
    ("refused_action_gate_preservation_notes", "missing refused-action gate preservation notes"),
    ("stale_evidence_hold_propagation_rows", "missing stale-evidence hold propagation rows"),
    ("rollback_checkpoint_placeholders", "missing rollback checkpoint placeholders"),
    ("reviewer_signoff_placeholders", "missing reviewer signoff placeholders"),
    ("validation_commands", "missing validation commands"),
)

PROHIBITED_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "active_guardrail_mutation_claim",
        re.compile(r"\b(mutat(?:e|ed|es|ing)|modified|updated|patched|rewrote)\b.{0,80}\b(active\s+)?guardrail", re.IGNORECASE),
        "active guardrail mutation claims are not allowed",
    ),
    (
        "guardrail_activation_claim",
        re.compile(r"\b(activated|enabled|turned\s+on|promoted)\b.{0,80}\bguardrail", re.IGNORECASE),
        "guardrail activation claims are not allowed",
    ),
    (
        "live_crawl_execution_claim",
        re.compile(r"\b(live\s+crawl|executed\s+(?:a\s+)?crawl|ran\s+(?:a\s+)?crawl|crawled\s+live|scraped\s+live)\b", re.IGNORECASE),
        "live crawl execution claims are not allowed",
    ),
    (
        "downloaded_or_raw_crawl_artifact",
        re.compile(r"\b(downloaded|raw\s+crawl|crawl\s+artifact|har\s+file|screenshot\s+trace|captured\s+html|saved\s+pdf)\b", re.IGNORECASE),
        "downloaded or raw crawl artifacts are not allowed",
    ),
    (
        "private_session_auth_artifact",
        re.compile(r"\b(session\s+cookie|auth\s+token|bearer\s+token|password|private\s+key|devhub\s+session|storage\s+state)\b", re.IGNORECASE),
        "private, session, or auth artifacts are not allowed",
    ),
    (
        "official_action_completion_claim",
        re.compile(r"\b(official(?:ly)?\s+completed|submitted\s+to\s+the\s+city|permit\s+submitted|application\s+filed|certified\s+complete)\b", re.IGNORECASE),
        "official-action completion claims are not allowed",
    ),
    (
        "legal_or_permitting_guarantee",
        re.compile(r"\b(guarantee[sd]?|warrant(?:y|ies|ed)?|legal\s+advice|permit\s+approval\s+is\s+assured|will\s+be\s+approved)\b", re.IGNORECASE),
        "legal or permitting guarantees are not allowed",
    ),
    (
        "active_mutation_flag",
        re.compile(r"\b(active_mutation|mutate_active|activation_flag|apply_live|write_active|commit_active)\b\s*[:=]\s*(?:true|1|yes|on)", re.IGNORECASE),
        "active mutation flags are not allowed",
    ),
)


def validate_packet(packet: Mapping[str, Any]) -> list[PacketValidationIssue]:
    """Return deterministic validation issues for an inactive packet v7."""

    issues: list[PacketValidationIssue] = []

    if packet.get("packet_version") != 7:
        issues.append(PacketValidationIssue("invalid_packet_version", "packet_version must be 7"))

    if packet.get("guardrail_mode") != "inactive":
        issues.append(PacketValidationIssue("invalid_guardrail_mode", "guardrail_mode must be inactive"))

    for field, message in REQUIRED_FIELDS:
        if _is_missing(packet.get(field)):
            issues.append(PacketValidationIssue(f"missing_{field}", message))

    text = _flatten_text(packet)
    for code, pattern, message in PROHIBITED_PATTERNS:
        if pattern.search(text):
            issues.append(PacketValidationIssue(code, message))

    if _has_truthy_active_mutation_flag(packet):
        issues.append(PacketValidationIssue("active_mutation_flag", "active mutation flags are not allowed"))

    return issues


def reject_packet(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when packet v7 violates inactive staging rules."""

    issues = validate_packet(packet)
    if issues:
        detail = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        raise ValueError(detail)


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping):
        return not value
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return len(value) == 0
    return False


def _flatten_text(value: Any) -> str:
    if isinstance(value, Mapping):
        return "\n".join(str(key) + "\n" + _flatten_text(item) for key, item in value.items())
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return "\n".join(_flatten_text(item) for item in value)
    return str(value)


def _has_truthy_active_mutation_flag(packet: Mapping[str, Any]) -> bool:
    for key, value in packet.items():
        normalized = str(key).lower()
        if normalized in {"active_mutation", "mutate_active", "activation_flag", "apply_live", "write_active", "commit_active"}:
            if value is True:
                return True
            if isinstance(value, int) and value == 1:
                return True
            if isinstance(value, str) and value.strip().lower() in {"true", "1", "yes", "on"}:
                return True
        if isinstance(value, Mapping) and _has_truthy_active_mutation_flag(value):
            return True
    return False
