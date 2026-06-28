"""Fail-closed validation for post-recompile release decision packet v7.

This validator is fixture-first and deterministic. It checks release decision
packet mappings only; it does not crawl, authenticate, download, mutate, upload,
submit, certify, pay, schedule, or guarantee legal or permitting outcomes.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import re
from typing import Any

from ppd.agent_readiness.post_recompile_release_decision_packet_v7 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    MODE,
    PACKET_TYPE,
    PACKET_VERSION,
    REPLAY_ID,
    VALIDATION_COMMANDS,
)

REQUIRED_SECTIONS: tuple[tuple[str, str], ...] = (
    ("source_fixture_refs", "missing readiness replay references"),
    ("go_no_go_rows", "missing go/no-go rows"),
    ("unresolved_hold_inventory", "missing unresolved hold inventory"),
    ("citation_continuity_summaries", "missing citation continuity summaries"),
    ("agent_compatibility_notes", "missing agent compatibility notes"),
    ("inactive_guardrail_promotion_eligibility_placeholders", "missing inactive guardrail promotion eligibility placeholders"),
    ("rollback_owner_placeholders", "missing rollback owner placeholders"),
    ("monitoring_handoff_reminders", "missing monitoring handoff reminders"),
    ("reviewer_signoff_placeholders", "missing reviewer signoff placeholders"),
    ("offline_validation_commands", "missing validation commands"),
    ("validation_commands", "missing validation commands"),
)

REQUIRED_TRUE_FLAGS = (
    "fixture_first",
    "post_recompile_replay_fixture_only",
    "manual_reviewer_decision_required",
    "unresolved_holds_review_required",
    "citation_continuity_review_required",
    "agent_compatibility_review_required",
    "inactive_guardrail_promotion_eligibility_review_required",
    "rollback_owner_assignment_required",
    "monitoring_handoff_required",
    "reviewer_signoff_required",
)

REQUIRED_FALSE_FLAGS = (
    "active_guardrail_mutation",
    "active_guardrail_bundle_mutation",
    "active_prompt_mutation",
    "active_process_model_mutation",
    "active_requirement_mutation",
    "active_source_mutation",
    "active_devhub_surface_mutation",
    "active_release_state_mutation",
    "active_mutation",
    "guardrails_changed",
    "guardrail_bundles_changed",
    "promotion_executed",
    "activation_executed",
    "opens_devhub",
    "crawls_live_sites",
    "reads_private_documents",
    "uploads",
    "submits",
    "certifies",
    "pays",
    "schedules",
    "legal_or_permitting_guarantee",
)

PRIVATE_ARTIFACT_KEY_PARTS = (
    "auth",
    "auth_state",
    "bearer",
    "browser",
    "card",
    "cookie",
    "credential",
    "devhub_session",
    "download",
    "downloaded",
    "har",
    "mfa",
    "password",
    "payment",
    "private",
    "raw_crawl",
    "raw_output",
    "screenshot",
    "session",
    "storage_state",
    "token",
    "trace",
)

PRIVATE_ARTIFACT_VALUE_MARKERS = (
    "/private/",
    "/session/",
    ".har",
    "auth-state",
    "auth_state",
    "bearer ",
    "cookie=",
    "cookies.json",
    "downloaded/",
    "password",
    "playwright/.auth",
    "raw-crawl",
    "raw_crawl",
    "session.json",
    "storage-state",
    "storage_state",
    "trace.zip",
)

FORBIDDEN_TEXT_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "active_activation_claim",
        re.compile(r"\b(activated|activation\s+complete|release\s+is\s+active|promoted\s+to\s+active|enabled\s+in\s+production|live\s+activation)\b", re.IGNORECASE),
        "active activation claims are not allowed",
    ),
    (
        "live_crawl_execution_claim",
        re.compile(r"\b(live\s+crawl|executed\s+(?:a\s+)?crawl|ran\s+(?:a\s+)?crawl|crawled\s+live|scraped\s+live|opened\s+devhub|authenticated\s+devhub|live\s+browser)\b", re.IGNORECASE),
        "live crawl execution claims are not allowed",
    ),
    (
        "private_session_auth_artifact",
        re.compile(r"\b(session\s+cookie|session\s+token|auth\s+token|bearer\s+token|password|private\s+document|private\s+upload|devhub\s+session|storage\s+state|credential|cookies?|har\s+file|trace\s+file|screenshot\s+artifact|raw\s+crawl\s+output|downloaded\s+document)\b", re.IGNORECASE),
        "private, session, or auth artifacts are not allowed",
    ),
    (
        "official_action_completion_claim",
        re.compile(r"\b(official(?:ly)?\s+completed|official\s+action\s+completed|submitted\s+to\s+the\s+city|submitted\s+permit|submitted\s+application|uploaded\s+to\s+the\s+official\s+record|certified\s+complete|paid\s+fee|payment\s+submitted|scheduled\s+inspection|cancelled\s+permit|withdrew\s+application)\b", re.IGNORECASE),
        "official-action completion claims are not allowed",
    ),
    (
        "legal_or_permitting_guarantee",
        re.compile(r"\b(legal\s+advice|legally\s+sufficient|permit\s+approval\s+guaranteed|guaranteed\s+approval|guaranteed\s+permit|will\s+be\s+approved|will\s+receive\s+a\s+permit|permit\s+approval\s+is\s+assured)\b", re.IGNORECASE),
        "legal or permitting guarantees are not allowed",
    ),
    (
        "active_mutation_claim",
        re.compile(r"\b(active\s+mutation|mutated\s+active|changed\s+active|production\s+mutation|active\s+state\s+changed|applied\s+live\s+mutation|mutation\s+enabled)\b", re.IGNORECASE),
        "active mutation claims are not allowed",
    ),
)

ACTIVE_MUTATION_KEYS = frozenset(
    {
        "active_mutation",
        "active_mutation_flag",
        "active_mutation_flags",
        "apply_live",
        "commit_active",
        "mutation_enabled",
        "mutate_active",
        "write_active",
    }
)


@dataclass(frozen=True)
class ReleaseDecisionPacketV7Issue:
    code: str
    path: str
    message: str


class ReleaseDecisionPacketV7ValidationError(ValueError):
    """Raised when a post-recompile release decision packet v7 is invalid."""


def validate_packet(packet: Mapping[str, Any]) -> list[ReleaseDecisionPacketV7Issue]:
    """Return deterministic validation issues for release decision packet v7."""

    if not isinstance(packet, Mapping):
        return [ReleaseDecisionPacketV7Issue("invalid_packet", "$", "packet must be an object")]

    issues: list[ReleaseDecisionPacketV7Issue] = []
    _validate_packet_identity(packet, issues)
    _validate_required_sections(packet, issues)
    _validate_replay_reference(packet, issues)
    _validate_required_flags(packet, issues)
    _validate_go_no_go_rows(packet, issues)
    _validate_placeholder_sections(packet, issues)
    _validate_forbidden_payload(packet, issues)
    return sorted(set(issues), key=lambda issue: (issue.path, issue.code, issue.message))


def reject_packet(packet: Mapping[str, Any]) -> None:
    """Raise when release decision packet v7 violates offline review-only rules."""

    issues = validate_packet(packet)
    if issues:
        details = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise ReleaseDecisionPacketV7ValidationError("post-recompile release decision packet v7 is invalid: " + details)


def _validate_packet_identity(packet: Mapping[str, Any], issues: list[ReleaseDecisionPacketV7Issue]) -> None:
    expected_scalars = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "mode": MODE,
    }
    for field, expected in expected_scalars.items():
        if packet.get(field) != expected:
            issues.append(ReleaseDecisionPacketV7Issue("invalid_packet_field", f"$.{field}", f"{field} must be {expected!r}"))


def _validate_required_sections(packet: Mapping[str, Any], issues: list[ReleaseDecisionPacketV7Issue]) -> None:
    for section, message in REQUIRED_SECTIONS:
        value = packet.get(section)
        if _is_missing(value):
            issues.append(ReleaseDecisionPacketV7Issue(f"missing_{section}", f"$.{section}", message))
            continue
        if section == "offline_validation_commands":
            if value != EXACT_OFFLINE_VALIDATION_COMMANDS:
                issues.append(ReleaseDecisionPacketV7Issue("invalid_offline_validation_commands", "$.offline_validation_commands", "offline validation commands must exactly match release decision packet v7 commands"))
        elif section == "validation_commands":
            if value != VALIDATION_COMMANDS:
                issues.append(ReleaseDecisionPacketV7Issue("invalid_validation_commands", "$.validation_commands", "validation commands must contain only the PP&D daemon self-test command"))
        elif not _is_mapping_list(value):
            issues.append(ReleaseDecisionPacketV7Issue(f"invalid_{section}", f"$.{section}", f"{section} must be a non-empty list of objects"))


def _validate_replay_reference(packet: Mapping[str, Any], issues: list[ReleaseDecisionPacketV7Issue]) -> None:
    refs = packet.get("source_fixture_refs")
    valid_ref = False
    if isinstance(refs, Sequence) and not isinstance(refs, (str, bytes, bytearray)):
        for ref in refs:
            if not isinstance(ref, Mapping):
                continue
            if ref.get("fixture_role") == "post_recompile_agent_readiness_replay_v7" and ref.get("replay") == REPLAY_ID and _present(ref.get("path")):
                valid_ref = True
    if not valid_ref:
        issues.append(ReleaseDecisionPacketV7Issue("missing_readiness_replay_reference", "$.source_fixture_refs", "source fixture refs must include a post-recompile agent readiness replay v7 reference"))

    consumes = packet.get("consumes_only")
    if not isinstance(consumes, Mapping):
        issues.append(ReleaseDecisionPacketV7Issue("missing_replay_consumption_attestation", "$.consumes_only", "consumes_only must require post-recompile agent readiness replay v7 fixtures"))
        return
    if consumes.get("post_recompile_agent_readiness_replay_v7_fixtures") is not True:
        issues.append(ReleaseDecisionPacketV7Issue("invalid_replay_consumption_attestation", "$.consumes_only.post_recompile_agent_readiness_replay_v7_fixtures", "consumes_only must require post-recompile agent readiness replay v7 fixtures"))
    if consumes.get("replay") != REPLAY_ID:
        issues.append(ReleaseDecisionPacketV7Issue("invalid_replay_consumption_attestation", "$.consumes_only.replay", f"consumes_only.replay must be {REPLAY_ID}"))


def _validate_required_flags(packet: Mapping[str, Any], issues: list[ReleaseDecisionPacketV7Issue]) -> None:
    for field in REQUIRED_TRUE_FLAGS:
        if packet.get(field) is not True:
            issues.append(ReleaseDecisionPacketV7Issue("required_flag_not_true", f"$.{field}", f"{field} must be true"))
    for field in REQUIRED_FALSE_FLAGS:
        if packet.get(field) is not False:
            issues.append(ReleaseDecisionPacketV7Issue("required_flag_not_false", f"$.{field}", f"{field} must be false"))


def _validate_go_no_go_rows(packet: Mapping[str, Any], issues: list[ReleaseDecisionPacketV7Issue]) -> None:
    rows = packet.get("go_no_go_rows")
    if not _is_mapping_list(rows):
        return
    seen: set[str] = set()
    for index, row in enumerate(rows):
        path = f"$.go_no_go_rows[{index}]"
        row_id = row.get("row_id")
        if not _present(row_id):
            issues.append(ReleaseDecisionPacketV7Issue("missing_go_no_go_row_field", f"{path}.row_id", "go/no-go row_id is required"))
        elif str(row_id) in seen:
            issues.append(ReleaseDecisionPacketV7Issue("duplicate_go_no_go_row", f"{path}.row_id", f"duplicate go/no-go row id {row_id}"))
        else:
            seen.add(str(row_id))
        for field in ("scenario", "source_fixture", "response_type", "evidence_status", "basis"):
            if not _present(row.get(field)):
                issues.append(ReleaseDecisionPacketV7Issue("missing_go_no_go_row_field", f"{path}.{field}", f"{field} is required"))
        if row.get("recommendation") not in {"NO_GO", "GO_WITH_CAVEATS"}:
            issues.append(ReleaseDecisionPacketV7Issue("invalid_go_no_go_recommendation", f"{path}.recommendation", "recommendation must be NO_GO or GO_WITH_CAVEATS"))
        if row.get("activation_allowed") is not False:
            issues.append(ReleaseDecisionPacketV7Issue("activation_not_allowed", f"{path}.activation_allowed", "go/no-go rows must keep activation_allowed false"))
        if row.get("manual_reviewer_decision_required") is not True:
            issues.append(ReleaseDecisionPacketV7Issue("missing_manual_reviewer_decision", f"{path}.manual_reviewer_decision_required", "go/no-go rows must require a manual reviewer decision"))


def _validate_placeholder_sections(packet: Mapping[str, Any], issues: list[ReleaseDecisionPacketV7Issue]) -> None:
    rules = (
        ("unresolved_hold_inventory", "hold_id", "promotion_blocked", True),
        ("citation_continuity_summaries", "citation_summary_id", "requires_manual_review", True),
        ("agent_compatibility_notes", "compatibility_note_id", "requires_manual_review", True),
        ("inactive_guardrail_promotion_eligibility_placeholders", "eligibility_placeholder_id", "activation_allowed", False),
        ("rollback_owner_placeholders", "rollback_owner_placeholder_id", "active_state_changed", False),
        ("monitoring_handoff_reminders", "monitoring_reminder_id", "handoff_required", True),
        ("reviewer_signoff_placeholders", "reviewer_signoff_placeholder_id", "signoff_required", True),
    )
    for section, id_field, status_field, expected in rules:
        rows = packet.get(section)
        if not _is_mapping_list(rows):
            continue
        for index, row in enumerate(rows):
            path = f"$.{section}[{index}]"
            if not _present(row.get(id_field)):
                issues.append(ReleaseDecisionPacketV7Issue("missing_placeholder_id", f"{path}.{id_field}", f"{id_field} is required"))
            if row.get(status_field) != expected:
                issues.append(ReleaseDecisionPacketV7Issue("invalid_placeholder_status", f"{path}.{status_field}", f"{status_field} must be {expected!r}"))


def _validate_forbidden_payload(packet: Mapping[str, Any], issues: list[ReleaseDecisionPacketV7Issue]) -> None:
    for path, value in _walk(packet):
        leaf = path.rsplit(".", 1)[-1].lower().replace("-", "_")
        if leaf in ACTIVE_MUTATION_KEYS and _truthy(value):
            issues.append(ReleaseDecisionPacketV7Issue("active_mutation_flag", path, "active mutation flags are not allowed"))
        if any(part in leaf for part in PRIVATE_ARTIFACT_KEY_PARTS) and _truthy(value) and not _allowed_artifact_key_path(path):
            issues.append(ReleaseDecisionPacketV7Issue("private_session_auth_artifact", path, "private, session, auth, trace, HAR, raw crawl, downloaded, or payment artifacts are forbidden"))
        if isinstance(value, str):
            lowered = value.lower()
            if any(marker in lowered for marker in PRIVATE_ARTIFACT_VALUE_MARKERS):
                issues.append(ReleaseDecisionPacketV7Issue("private_session_auth_artifact", path, "private/session/auth artifact references are forbidden"))
            for code, pattern, message in FORBIDDEN_TEXT_PATTERNS:
                if pattern.search(value):
                    issues.append(ReleaseDecisionPacketV7Issue(code, path, message))


def _allowed_artifact_key_path(path: str) -> bool:
    return path.startswith("$.source_fixture_refs[") and path.endswith(".path")


def _walk(value: Any, path: str = "$", seen: set[int] | None = None) -> Iterable[tuple[str, Any]]:
    if seen is None:
        seen = set()
    value_id = id(value)
    if value_id in seen:
        return
    if isinstance(value, (Mapping, list, tuple, set)):
        seen.add(value_id)
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).replace(".", "_")
            yield from _walk(child, f"{path}.{key_text}", seen)
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]", seen)
    elif isinstance(value, set):
        for index, child in enumerate(sorted(value, key=repr)):
            yield from _walk(child, f"{path}[{index}]", seen)


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


def _present(value: Any) -> bool:
    return not _is_missing(value) and value is not False


def _truthy(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return value.strip().lower() not in {"", "false", "none", "no", "0"}
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return bool(value)
    return bool(value)
