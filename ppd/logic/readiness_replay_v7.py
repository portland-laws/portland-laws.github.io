"""Validation for post-recompile agent readiness replay v7 packets.

The replay packet is commit-safe and fixture-first. It may cite deterministic
review packets, inactive staging references, response checks, and validation
commands, but it must not include private/session/auth artifacts, live crawl or
activation claims, official-action completion claims, guarantees, or active
mutation flags.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


REPLAY_PHASE = "post_recompile_agent_readiness_replay"
REPLAY_VERSION = 7

REQUIRED_REFERENCE_FIELDS = (
    "reviewer_packet_ref",
    "inactive_guardrail_staging_ref",
)

REQUIRED_RESPONSE_CHECKS = (
    "missing_information_response_check",
    "stale_evidence_stop_check",
    "reversible_draft_check",
    "local_pdf_preview_check",
    "exact_confirmation_checkpoint_check",
    "refused_consequential_action_check",
    "refused_financial_action_check",
    "rollback_visibility_check",
    "source_citation_explanation_check",
    "manual_handoff_check",
)

FORBIDDEN_TRUTHY_FIELDS = (
    "active_activation_claims",
    "live_crawl_execution_claims",
    "official_action_completion_claims",
    "legal_or_permitting_guarantees",
    "active_mutation_flags",
)

PRIVATE_ARTIFACT_KEY_PARTS = (
    "auth",
    "auth_state",
    "bearer",
    "captcha",
    "card",
    "cookie",
    "credential",
    "downloaded_document",
    "har",
    "mfa",
    "password",
    "payment_detail",
    "private",
    "private_upload",
    "raw_crawl",
    "raw_crawl_output",
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

FORBIDDEN_TEXT_MARKERS = (
    "activated agent",
    "agent activated",
    "activation complete",
    "applied live mutation",
    "certified complete",
    "completed official action",
    "enabled in production",
    "executed live crawl",
    "guaranteed approval",
    "guaranteed permit",
    "inspection scheduled",
    "legal advice",
    "live crawl executed",
    "made official change",
    "mutation enabled",
    "payment submitted",
    "permit approval is assured",
    "submitted application",
    "submitted permit",
    "uploaded corrections",
    "will be approved",
)

ACTIVE_MUTATION_KEYS = (
    "active_mutation",
    "active_mutation_flags",
    "apply_live",
    "commit_active",
    "mutation_enabled",
    "mutate_active",
    "write_active",
)


@dataclass(frozen=True)
class ValidationIssue:
    """A deterministic validation failure for a readiness replay packet."""

    code: str
    path: str
    message: str


def validate_post_recompile_agent_readiness_replay_v7(packet: Mapping[str, Any]) -> list[ValidationIssue]:
    """Return all validation issues for a replay v7 packet."""

    issues: list[ValidationIssue] = []

    if packet.get("replay_version") != REPLAY_VERSION:
        issues.append(ValidationIssue("invalid_replay_version", "replay_version", "replay_version must be 7"))

    if packet.get("phase") != REPLAY_PHASE:
        issues.append(ValidationIssue("invalid_replay_phase", "phase", "phase must identify post-recompile replay"))

    references = _mapping_at(packet, "required_references")
    if references is None:
        issues.append(ValidationIssue("missing_required_references", "required_references", "required references are missing"))
        references = {}

    for field in REQUIRED_REFERENCE_FIELDS:
        if not _present(references.get(field)):
            issues.append(ValidationIssue("missing_required_reference", f"required_references.{field}", f"missing {field}"))

    staging_ref = references.get("inactive_guardrail_staging_ref")
    if isinstance(staging_ref, Mapping):
        if staging_ref.get("active") is True or staging_ref.get("inactive") is False:
            issues.append(
                ValidationIssue(
                    "active_guardrail_staging_reference",
                    "required_references.inactive_guardrail_staging_ref",
                    "inactive guardrail staging reference must not be active",
                )
            )

    response_checks = _mapping_at(packet, "response_checks")
    if response_checks is None:
        issues.append(ValidationIssue("missing_response_checks", "response_checks", "response checks are missing"))
        response_checks = {}

    for field in REQUIRED_RESPONSE_CHECKS:
        if not _present(response_checks.get(field)):
            issues.append(ValidationIssue("missing_response_check", f"response_checks.{field}", f"missing {field}"))

    if not _valid_validation_commands(packet.get("validation_commands")):
        issues.append(
            ValidationIssue(
                "missing_validation_commands",
                "validation_commands",
                "validation commands must be non-empty argv-style command arrays",
            )
        )

    for field in FORBIDDEN_TRUTHY_FIELDS:
        if _truthy(packet.get(field)):
            issues.append(ValidationIssue("forbidden_active_claim", field, f"truthy {field} is forbidden"))

    issues.extend(_scan_for_forbidden_content(packet))
    return sorted(set(issues), key=lambda issue: (issue.path, issue.code, issue.message))


def assert_post_recompile_agent_readiness_replay_v7(packet: Mapping[str, Any]) -> None:
    """Raise ValueError if a replay packet fails validation."""

    issues = validate_post_recompile_agent_readiness_replay_v7(packet)
    if issues:
        details = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise ValueError(details)


def _mapping_at(packet: Mapping[str, Any], key: str) -> Mapping[str, Any] | None:
    value = packet.get(key)
    if isinstance(value, Mapping):
        return value
    return None


def _present(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return len(value) > 0
    return True


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in {"", "false", "none", "no", "0"}
    return bool(value)


def _valid_validation_commands(value: Any) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray, str)) or not value:
        return False
    for command in value:
        if not isinstance(command, Sequence) or isinstance(command, (bytes, bytearray, str)) or not command:
            return False
        if any(not isinstance(part, str) or not part.strip() for part in command):
            return False
    return True


def _scan_for_forbidden_content(value: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for path, item in _walk(value):
        leaf = path.rsplit(".", 1)[-1].lower()
        if any(marker in leaf for marker in PRIVATE_ARTIFACT_KEY_PARTS):
            issues.append(
                ValidationIssue(
                    "forbidden_private_or_auth_artifact",
                    path,
                    "private, session, auth, trace, HAR, raw crawl, downloaded, or payment artifacts are forbidden",
                )
            )
        if leaf in ACTIVE_MUTATION_KEYS and _truthy(item):
            issues.append(ValidationIssue("forbidden_active_mutation_flag", path, "active mutation flags are forbidden"))
        if isinstance(item, str):
            lowered = item.lower()
            if any(marker in lowered for marker in PRIVATE_ARTIFACT_VALUE_MARKERS):
                issues.append(ValidationIssue("forbidden_private_or_auth_artifact", path, "private/session/auth artifact reference is forbidden"))
            if any(marker in lowered for marker in FORBIDDEN_TEXT_MARKERS):
                issues.append(
                    ValidationIssue(
                        "forbidden_readiness_claim",
                        path,
                        "active activation, live crawl, official action, guarantee, or mutation claims are forbidden",
                    )
                )
    return issues


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
