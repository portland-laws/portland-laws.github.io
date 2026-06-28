"""Validation for guardrail recompile reviewer packet v6."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

REQUIRED_FIELDS = {
    "staging_packet_references": "missing staging packet references",
    "reviewer_comparison_rows": "missing reviewer comparison rows",
    "inactive_guardrail_status_notes": "missing inactive guardrail status notes",
    "source_evidence_continuity_checks": "missing source evidence continuity checks",
    "deterministic_predicate_review_prompts": "missing deterministic predicate review prompts",
    "exact_confirmation_or_refused_action_preservation_summary": "missing exact-confirmation or refused-action preservation summaries",
    "stale_evidence_hold_propagation": "missing stale-evidence hold propagation",
    "rollback_checkpoint_placeholders": "missing rollback checkpoint placeholders",
    "signoff_owner_placeholders": "missing signoff-owner placeholders",
    "validation_commands": "missing validation commands",
}

FORBIDDEN_PATTERNS = {
    "active activation claims": re.compile(r"\b(activated|activation complete|enabled in production|live activation)\b", re.IGNORECASE),
    "live crawl execution claims": re.compile(r"\b(live crawl ran|executed live crawl|crawled devhub|crawler completed)\b", re.IGNORECASE),
    "downloaded or raw crawl artifacts": re.compile(r"\b(downloaded document|raw crawl|crawl artifact|har file|trace zip)\b", re.IGNORECASE),
    "private/session/auth artifacts": re.compile(r"\b(session cookie|auth token|private devhub session|storage state|credentials)\b", re.IGNORECASE),
    "official-action completion claims": re.compile(r"\b(permit submitted|application submitted|inspection scheduled|official action completed)\b", re.IGNORECASE),
    "legal or permitting guarantees": re.compile(r"\b(legally guaranteed|permit guaranteed|approval guaranteed|compliance guaranteed)\b", re.IGNORECASE),
    "active mutation flags": re.compile(r"\b(mutate\s*:\s*true|write\s*:\s*true|submit\s*:\s*true|dry_run\s*:\s*false)\b", re.IGNORECASE),
}


def validate_guardrail_recompile_reviewer_packet_v6(packet: Mapping[str, Any]) -> list[str]:
    """Return deterministic validation errors for a reviewer packet v6 mapping."""
    errors: list[str] = []

    for field, message in REQUIRED_FIELDS.items():
        if _is_missing(packet.get(field)):
            errors.append(message)

    searchable_text = "\n".join(_walk_text(packet))
    for message, pattern in FORBIDDEN_PATTERNS.items():
        if pattern.search(searchable_text):
            errors.append(message)

    return errors


def assert_guardrail_recompile_reviewer_packet_v6(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a reviewer packet v6 fails validation."""
    errors = validate_guardrail_recompile_reviewer_packet_v6(packet)
    if errors:
        raise ValueError("; ".join(errors))


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping):
        return len(value) == 0
    if isinstance(value, Sequence) and not isinstance(value, bytes):
        return len(value) == 0
    return False


def _walk_text(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        text: list[str] = []
        for key, item in value.items():
            text.extend(_walk_text(key))
            text.extend(_walk_text(item))
        return text
    if isinstance(value, Sequence) and not isinstance(value, bytes):
        text = []
        for item in value:
            text.extend(_walk_text(item))
        return text
    return [str(value)] if isinstance(value, bool) else []
