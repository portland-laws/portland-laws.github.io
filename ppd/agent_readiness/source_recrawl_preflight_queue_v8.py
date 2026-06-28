"""Validation for source recrawl preflight queue v8 packets.

The v8 queue is intentionally a preflight artifact only. It may describe public
source candidates and policy placeholders, but it must not claim live crawl
execution, downloaded/raw artifacts, authenticated data, official completion, or
active mutation readiness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse


BLOCKED_CLAIM_FIELDS = (
    "live_crawl_execution_claims",
    "downloaded_or_raw_crawl_artifacts",
    "private_session_auth_artifacts",
    "official_action_completion_claims",
    "legal_or_permitting_guarantees",
)

BLOCKED_MUTATION_VALUES = {"active", "enabled", "true", "yes", "mutating", "write"}

REQUIRED_SKIPPED_REASON_CODES = {
    "outside_allowlist",
    "unsupported_scheme",
    "private_authenticated",
    "disallowed_by_robots_or_policy",
    "raw_download_not_permitted",
    "too_large",
    "unsupported_content_type",
}

REQUIRED_VALIDATION_COMMANDS = (
    ("python3", "ppd/daemon/ppd_daemon.py", "--self-test"),
)

ALLOWED_PUBLIC_SCHEMES = {"https"}


@dataclass(frozen=True)
class ValidationResult:
    """Result for a source recrawl preflight queue validation."""

    accepted: bool
    errors: tuple[str, ...]


def validate_source_recrawl_preflight_queue_v8(packet: Mapping[str, Any]) -> ValidationResult:
    """Validate that a v8 source recrawl queue packet is complete and inert."""

    errors: list[str] = []

    if not _non_empty_string(packet.get("authorization_reference")):
        errors.append("missing authorization_reference")

    registry_refs = packet.get("source_registry_references")
    if not _non_empty_sequence(registry_refs):
        errors.append("missing source_registry_references")

    candidates = packet.get("ordered_public_source_candidates")
    if not _non_empty_sequence(candidates):
        errors.append("missing ordered_public_source_candidates")
    else:
        _validate_candidates(candidates, errors)

    canonical_checks = packet.get("canonical_url_checks")
    if not _non_empty_sequence(canonical_checks):
        errors.append("missing canonical_url_checks")

    allowlist_decisions = packet.get("allowlist_decisions")
    if not _non_empty_sequence(allowlist_decisions):
        errors.append("missing allowlist_decisions")

    robots_policy_placeholders = packet.get("robots_policy_decision_placeholders")
    if not _non_empty_sequence(robots_policy_placeholders):
        errors.append("missing robots_policy_decision_placeholders")

    skipped_url_reason_rows = packet.get("skipped_url_reason_rows")
    if not _non_empty_sequence(skipped_url_reason_rows):
        errors.append("missing skipped_url_reason_rows")
    else:
        _validate_skipped_reason_rows(skipped_url_reason_rows, errors)

    handoff_flags = packet.get("processor_handoff_eligibility_flags")
    if not isinstance(handoff_flags, Mapping) or not handoff_flags:
        errors.append("missing processor_handoff_eligibility_flags")
    else:
        _validate_handoff_flags(handoff_flags, errors)

    validation_commands = packet.get("validation_commands")
    if not _non_empty_sequence(validation_commands):
        errors.append("missing validation_commands")
    elif not _contains_required_validation_commands(validation_commands):
        errors.append("validation_commands must include ppd daemon self-test")

    _validate_blocked_claims(packet, errors)
    _validate_mutation_flags(packet, errors)

    return ValidationResult(accepted=not errors, errors=tuple(errors))


def build_source_recrawl_preflight_queue_v8_fixture() -> dict[str, Any]:
    """Return a minimal accepted fixture for deterministic tests and demos."""

    return {
        "queue_version": "v8",
        "authorization_reference": "ppd-public-recrawl-preflight-authorization-2026-06-02",
        "source_registry_references": [
            {
                "source_id": "ppd-landing-page",
                "canonical_url": "https://www.portland.gov/ppd",
                "registry_status": "referenced_before_recrawl",
            }
        ],
        "ordered_public_source_candidates": [
            {
                "order": 1,
                "source_id": "ppd-landing-page",
                "url": "https://www.portland.gov/ppd",
                "source_type": "public_html",
            }
        ],
        "canonical_url_checks": [
            {
                "source_id": "ppd-landing-page",
                "input_url": "https://www.portland.gov/ppd",
                "canonical_url": "https://www.portland.gov/ppd",
                "status": "placeholder_pending_preflight_resolution",
            }
        ],
        "allowlist_decisions": [
            {
                "source_id": "ppd-landing-page",
                "host": "www.portland.gov",
                "decision": "allowlisted_public_official_source",
            }
        ],
        "robots_policy_decision_placeholders": [
            {
                "source_id": "ppd-landing-page",
                "robots_decision": "placeholder_required_before_fetch",
                "policy_decision": "placeholder_required_before_fetch",
            }
        ],
        "skipped_url_reason_rows": [
            {"reason_code": reason_code, "example_url": "https://example.invalid/placeholder"}
            for reason_code in sorted(REQUIRED_SKIPPED_REASON_CODES)
        ],
        "processor_handoff_eligibility_flags": {
            "authorization_reference_present": True,
            "source_registry_references_present": True,
            "ordered_public_source_candidates_present": True,
            "canonical_url_checks_present": True,
            "allowlist_decisions_present": True,
            "robots_policy_placeholders_present": True,
            "skipped_url_reason_rows_present": True,
            "no_live_crawl_execution_claims": True,
            "no_downloaded_or_raw_crawl_artifacts": True,
            "no_private_session_auth_artifacts": True,
            "no_official_action_completion_claims": True,
            "no_legal_or_permitting_guarantees": True,
            "active_mutation_flags_disabled": True,
            "eligible_for_processor_handoff": False,
        },
        "validation_commands": [list(command) for command in REQUIRED_VALIDATION_COMMANDS],
        "live_crawl_execution_claims": [],
        "downloaded_or_raw_crawl_artifacts": [],
        "private_session_auth_artifacts": [],
        "official_action_completion_claims": [],
        "legal_or_permitting_guarantees": [],
        "active_mutation_flags": [],
    }


def _validate_candidates(candidates: Sequence[Any], errors: list[str]) -> None:
    expected_order = 1
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, Mapping):
            errors.append(f"ordered_public_source_candidates[{index}] must be an object")
            continue

        order = candidate.get("order")
        if order != expected_order:
            errors.append("ordered_public_source_candidates must be explicitly ordered starting at 1")
        expected_order += 1

        url = candidate.get("url")
        if not _is_public_https_url(url):
            errors.append(f"ordered_public_source_candidates[{index}] must use a public https url")

        source_id = candidate.get("source_id")
        if not _non_empty_string(source_id):
            errors.append(f"ordered_public_source_candidates[{index}] missing source_id")


def _validate_skipped_reason_rows(rows: Sequence[Any], errors: list[str]) -> None:
    observed: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(f"skipped_url_reason_rows[{index}] must be an object")
            continue
        reason_code = row.get("reason_code")
        if _non_empty_string(reason_code):
            observed.add(reason_code)
        else:
            errors.append(f"skipped_url_reason_rows[{index}] missing reason_code")

    missing = sorted(REQUIRED_SKIPPED_REASON_CODES - observed)
    if missing:
        errors.append("skipped_url_reason_rows missing required reason codes: " + ", ".join(missing))


def _validate_handoff_flags(flags: Mapping[str, Any], errors: list[str]) -> None:
    required_true_flags = (
        "authorization_reference_present",
        "source_registry_references_present",
        "ordered_public_source_candidates_present",
        "canonical_url_checks_present",
        "allowlist_decisions_present",
        "robots_policy_placeholders_present",
        "skipped_url_reason_rows_present",
        "no_live_crawl_execution_claims",
        "no_downloaded_or_raw_crawl_artifacts",
        "no_private_session_auth_artifacts",
        "no_official_action_completion_claims",
        "no_legal_or_permitting_guarantees",
        "active_mutation_flags_disabled",
    )
    for flag in required_true_flags:
        if flags.get(flag) is not True:
            errors.append(f"processor_handoff_eligibility_flags.{flag} must be true")

    if flags.get("eligible_for_processor_handoff") is not False:
        errors.append("processor_handoff_eligibility_flags.eligible_for_processor_handoff must remain false until external validation")


def _validate_blocked_claims(packet: Mapping[str, Any], errors: list[str]) -> None:
    for field in BLOCKED_CLAIM_FIELDS:
        value = packet.get(field)
        if value in (None, [], (), ""):
            continue
        errors.append(f"{field} must be empty in preflight queue v8")


def _validate_mutation_flags(packet: Mapping[str, Any], errors: list[str]) -> None:
    value = packet.get("active_mutation_flags")
    if value in (None, [], (), ""):
        return
    if isinstance(value, Mapping):
        active_items = [key for key, flag_value in value.items() if _is_active_mutation_value(flag_value)]
        if active_items:
            errors.append("active_mutation_flags must not contain enabled mutation flags")
        return
    if isinstance(value, Sequence) and not isinstance(value, str):
        if value:
            errors.append("active_mutation_flags must be empty")
        return
    if _is_active_mutation_value(value):
        errors.append("active_mutation_flags must not be active")


def _contains_required_validation_commands(commands: Sequence[Any]) -> bool:
    normalized = {tuple(command) for command in commands if isinstance(command, Sequence) and not isinstance(command, str)}
    return all(command in normalized for command in REQUIRED_VALIDATION_COMMANDS)


def _is_public_https_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in ALLOWED_PUBLIC_SCHEMES and bool(parsed.netloc) and not parsed.username and not parsed.password


def _is_active_mutation_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in BLOCKED_MUTATION_VALUES
    return bool(value)


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str) and bool(value)


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
