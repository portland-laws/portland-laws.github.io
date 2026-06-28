"""Fail-closed validation for guardrail recompile reviewer packet v7.

The validator is fixture-first and deterministic. It inspects committed reviewer
packet mappings only; it does not crawl, authenticate, download, mutate, upload,
submit, certify, pay, schedule, or guarantee permitting outcomes.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import re
from typing import Any

PACKET_TYPE = "ppd.guardrail_recompile_reviewer_packet.v7"
PACKET_VERSION = "v7"
PACKET_MODE = "fixture_first_inactive_guardrail_recompile_review_only"
EXPECTED_VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

REQUIRED_FIELDS: tuple[tuple[str, str], ...] = (
    ("staging_packet_references", "missing staging packet references"),
    ("reviewer_comparison_rows", "missing reviewer comparison rows"),
    ("inactive_guardrail_status_notes", "missing inactive guardrail status notes"),
    ("source_evidence_continuity_checks", "missing source evidence continuity checks"),
    ("deterministic_predicate_review_prompts", "missing deterministic predicate review prompts"),
    ("exact_confirmation_preservation_summaries", "missing exact-confirmation preservation summaries"),
    ("refused_action_preservation_summaries", "missing refused-action preservation summaries"),
    ("stale_evidence_hold_carry_forward_rows", "missing stale-evidence hold carry-forward rows"),
    ("rollback_readiness_notes", "missing rollback readiness notes"),
    ("signoff_owner_placeholders", "missing signoff-owner placeholders"),
    ("validation_commands", "missing validation commands"),
)

FALSE_ATTESTATIONS = (
    "guardrails_activated",
    "live_crawl_executed",
    "devhub_opened",
    "private_documents_read",
    "uploads_attempted",
    "submissions_attempted",
    "certifications_attempted",
    "payments_attempted",
    "inspection_scheduling_attempted",
    "legal_or_permitting_guarantee",
)

PROHIBITED_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "active_activation_claim",
        re.compile(r"\b(activated|activation\s+complete|enabled\s+in\s+production|live\s+activation|currently\s+active)\b", re.IGNORECASE),
        "active activation claims are not allowed",
    ),
    (
        "live_crawl_execution_claim",
        re.compile(r"\b(live\s+crawl|executed\s+(?:a\s+)?crawl|ran\s+(?:a\s+)?crawl|crawled\s+live|scraped\s+live)\b", re.IGNORECASE),
        "live crawl execution claims are not allowed",
    ),
    (
        "downloaded_or_raw_crawl_artifact",
        re.compile(r"\b(downloaded|raw\s+crawl|crawl\s+artifact|har\s+file|screenshot\s+trace|captured\s+html|saved\s+pdf|raw\s+html|raw\s+pdf)\b", re.IGNORECASE),
        "downloaded or raw crawl artifacts are not allowed",
    ),
    (
        "private_session_auth_artifact",
        re.compile(r"\b(session\s+cookie|auth\s+token|bearer\s+token|password|private\s+key|devhub\s+session|storage\s+state|credential|cookies?)\b", re.IGNORECASE),
        "private, session, or auth artifacts are not allowed",
    ),
    (
        "official_action_completion_claim",
        re.compile(r"\b(official(?:ly)?\s+completed|submitted\s+to\s+the\s+city|permit\s+submitted|application\s+filed|certified\s+complete|inspection\s+scheduled|payment\s+submitted|uploaded\s+corrections)\b", re.IGNORECASE),
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


@dataclass(frozen=True)
class ReviewerPacketV7Issue:
    code: str
    path: str
    message: str


class ReviewerPacketV7ValidationError(ValueError):
    """Raised when a guardrail recompile reviewer packet v7 is invalid."""


def validate_packet(packet: Mapping[str, Any]) -> list[ReviewerPacketV7Issue]:
    """Return deterministic validation issues for reviewer packet v7."""

    issues: list[ReviewerPacketV7Issue] = []
    if not isinstance(packet, Mapping):
        return [ReviewerPacketV7Issue("invalid_packet", "$", "packet must be an object")]

    expected_scalars = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "mode": PACKET_MODE,
        "fixture_first": True,
        "inactive_only": True,
        "consumes_only_inactive_guardrail_recompile_staging_packet_v7_fixtures": True,
        "activation_allowed": False,
    }
    for field, expected in expected_scalars.items():
        if packet.get(field) != expected:
            issues.append(ReviewerPacketV7Issue("invalid_packet_field", f"$.{field}", f"{field} must be {expected!r}"))

    for field, message in REQUIRED_FIELDS:
        value = packet.get(field)
        if _is_missing(value):
            issues.append(ReviewerPacketV7Issue(f"missing_{field}", f"$.{field}", message))
        elif field == "validation_commands" and value != EXPECTED_VALIDATION_COMMANDS:
            issues.append(ReviewerPacketV7Issue("invalid_validation_commands", "$.validation_commands", "validation commands must match exact offline commands"))
        elif field != "validation_commands" and not _is_mapping_list(value):
            issues.append(ReviewerPacketV7Issue(f"invalid_{field}", f"$.{field}", f"{field} must be a non-empty list of objects"))

    attestations = packet.get("attestations")
    if not isinstance(attestations, Mapping):
        issues.append(ReviewerPacketV7Issue("missing_attestations", "$.attestations", "attestations are required"))
    else:
        for flag in FALSE_ATTESTATIONS:
            if attestations.get(flag) is not False:
                issues.append(ReviewerPacketV7Issue("attestation_not_false", f"$.attestations.{flag}", f"{flag} must be false"))

    _collect_row_activation_issues(packet, issues)

    text = _flatten_text(packet)
    for code, pattern, message in PROHIBITED_PATTERNS:
        if pattern.search(text):
            issues.append(ReviewerPacketV7Issue(code, "$", message))

    if _has_truthy_active_mutation_flag(packet):
        issues.append(ReviewerPacketV7Issue("active_mutation_flag", "$", "active mutation flags are not allowed"))

    return issues


def reject_packet(packet: Mapping[str, Any]) -> None:
    """Raise when reviewer packet v7 violates inactive review-only rules."""

    issues = validate_packet(packet)
    if issues:
        detail = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise ReviewerPacketV7ValidationError("guardrail recompile reviewer packet v7 is invalid: " + detail)


def _collect_row_activation_issues(packet: Mapping[str, Any], issues: list[ReviewerPacketV7Issue]) -> None:
    for field, _message in REQUIRED_FIELDS:
        if field == "validation_commands":
            continue
        rows = packet.get(field)
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
            continue
        for index, row in enumerate(rows):
            if isinstance(row, Mapping) and row.get("activation_allowed") is not False:
                issues.append(ReviewerPacketV7Issue("row_activation_not_false", f"$.{field}[{index}].activation_allowed", "review rows must keep activation_allowed false"))


def _is_mapping_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, Mapping) for item in value)


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping):
        return not value
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value) == 0
    return False


def _flatten_text(value: Any) -> str:
    if isinstance(value, Mapping):
        return "\n".join(str(key) + "\n" + _flatten_text(item) for key, item in value.items())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return "\n".join(_flatten_text(item) for item in value)
    return str(value)


def _has_truthy_active_mutation_flag(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).lower()
            if normalized in {"active_mutation", "mutate_active", "activation_flag", "apply_live", "write_active", "commit_active"}:
                if item is True:
                    return True
                if isinstance(item, int) and item == 1:
                    return True
                if isinstance(item, str) and item.strip().lower() in {"true", "1", "yes", "on"}:
                    return True
            if _has_truthy_active_mutation_flag(item):
                return True
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_has_truthy_active_mutation_flag(item) for item in value)
    return False
