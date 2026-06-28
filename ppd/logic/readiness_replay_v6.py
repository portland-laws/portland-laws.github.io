"""Validation for post-recompile agent readiness replay v6 packets.

The replay packet is intentionally commit-safe: it may cite deterministic evidence,
checks, and validation commands, but it must not claim live activation, live crawl
execution, official action completion, guarantees, active mutation, or private
session artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


REPLAY_PHASE = "post_recompile_agent_readiness_replay"
REPLAY_VERSION = 6

REQUIRED_REFERENCE_FIELDS = (
    "reviewer_packet_ref",
    "inactive_guardrail_staging_ref",
)

REQUIRED_RESPONSE_CHECKS = (
    "missing_information_response_check",
    "stale_evidence_stop_check",
    "reversible_draft_or_local_pdf_preview_check",
    "exact_confirmation_checkpoint_check",
    "refused_consequential_or_financial_action_check",
    "rollback_visibility_check",
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
    "auth_state",
    "bearer",
    "captcha",
    "cookie",
    "credential",
    "har",
    "mfa",
    "password",
    "payment_detail",
    "private_upload",
    "raw_crawl_output",
    "screenshot",
    "session",
    "storage_state",
    "token",
    "trace",
)

PRIVATE_ARTIFACT_VALUE_MARKERS = (
    ".har",
    "auth-state",
    "auth_state",
    "bearer ",
    "cookie=",
    "cookies.json",
    "password",
    "playwright/.auth",
    "raw-crawl",
    "session.json",
    "storage-state",
    "storage_state",
    "trace.zip",
)

FORBIDDEN_TEXT_MARKERS = (
    "activated agent",
    "agent activated",
    "completed official action",
    "executed live crawl",
    "guaranteed permit",
    "guaranteed approval",
    "live crawl executed",
    "made official change",
    "mutation enabled",
    "submitted application",
    "submitted permit",
)


@dataclass(frozen=True)
class ValidationIssue:
    """A deterministic validation failure for a readiness replay packet."""

    code: str
    path: str
    message: str


def validate_post_recompile_agent_readiness_replay_v6(packet: Mapping[str, Any]) -> list[ValidationIssue]:
    """Return all validation issues for a replay v6 packet.

    The validator is deliberately schema-light so callers can evolve packet
    metadata without changing this gate. It enforces the safety-critical fields
    named by the PP&D task and recursively rejects private/auth/live artifacts.
    """

    issues: list[ValidationIssue] = []

    if packet.get("replay_version") != REPLAY_VERSION:
        issues.append(
            ValidationIssue(
                "invalid_replay_version",
                "replay_version",
                "post-recompile readiness replay must declare replay_version 6",
            )
        )

    if packet.get("phase") != REPLAY_PHASE:
        issues.append(
            ValidationIssue(
                "invalid_replay_phase",
                "phase",
                "post-recompile readiness replay must declare the expected phase",
            )
        )

    references = _mapping_at(packet, "required_references")
    if references is None:
        issues.append(
            ValidationIssue(
                "missing_required_references",
                "required_references",
                "readiness replay must include required reviewer and inactive guardrail references",
            )
        )
        references = {}

    for field in REQUIRED_REFERENCE_FIELDS:
        if not _present(references.get(field)):
            issues.append(
                ValidationIssue(
                    "missing_required_reference",
                    f"required_references.{field}",
                    f"readiness replay is missing {field}",
                )
            )

    guardrail_state = references.get("inactive_guardrail_staging_ref")
    if isinstance(guardrail_state, Mapping) and guardrail_state.get("active") is True:
        issues.append(
            ValidationIssue(
                "active_guardrail_staging_reference",
                "required_references.inactive_guardrail_staging_ref.active",
                "guardrail staging reference must be inactive for replay validation",
            )
        )

    response_checks = _mapping_at(packet, "response_checks")
    if response_checks is None:
        issues.append(
            ValidationIssue(
                "missing_response_checks",
                "response_checks",
                "readiness replay must include all response safety checks",
            )
        )
        response_checks = {}

    for field in REQUIRED_RESPONSE_CHECKS:
        if not _present(response_checks.get(field)):
            issues.append(
                ValidationIssue(
                    "missing_response_check",
                    f"response_checks.{field}",
                    f"readiness replay is missing {field}",
                )
            )

    validation_commands = packet.get("validation_commands")
    if not _valid_validation_commands(validation_commands):
        issues.append(
            ValidationIssue(
                "missing_validation_commands",
                "validation_commands",
                "readiness replay must include deterministic validation commands as argv arrays",
            )
        )

    for field in FORBIDDEN_TRUTHY_FIELDS:
        if _truthy(packet.get(field)):
            issues.append(
                ValidationIssue(
                    "forbidden_active_claim",
                    field,
                    f"readiness replay must not include truthy {field}",
                )
            )

    issues.extend(_scan_for_forbidden_artifacts(packet))
    return issues


def assert_post_recompile_agent_readiness_replay_v6(packet: Mapping[str, Any]) -> None:
    """Raise ValueError if a replay packet fails validation."""

    issues = validate_post_recompile_agent_readiness_replay_v6(packet)
    if issues:
        details = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise ValueError(details)


def _mapping_at(packet: Mapping[str, Any], key: str) -> Mapping[str, Any] | None:
    value = packet.get(key)
    if isinstance(value, Mapping):
        return value
    return None


def _present(value: Any) -> bool:
    if value is None:
        return False
    if value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return len(value) > 0
    if isinstance(value, Mapping):
        return bool(value)
    return True


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in {"", "false", "none", "no", "0"}
    return bool(value)


def _valid_validation_commands(value: Any) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray, str)):
        return False
    if not value:
        return False
    for command in value:
        if not isinstance(command, Sequence) or isinstance(command, (bytes, bytearray, str)):
            return False
        if not command:
            return False
        if any(not isinstance(part, str) or not part.strip() for part in command):
            return False
    return True


def _scan_for_forbidden_artifacts(value: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for path, item in _walk(value):
        leaf = path.rsplit(".", 1)[-1].lower()
        if any(marker in leaf for marker in PRIVATE_ARTIFACT_KEY_PARTS):
            issues.append(
                ValidationIssue(
                    "forbidden_private_or_auth_artifact",
                    path,
                    "readiness replay must not include private, session, auth, trace, screenshot, HAR, raw crawl, or payment artifacts",
                )
            )
        if isinstance(item, str):
            lowered = item.lower()
            if any(marker in lowered for marker in PRIVATE_ARTIFACT_VALUE_MARKERS):
                issues.append(
                    ValidationIssue(
                        "forbidden_private_or_auth_artifact",
                        path,
                        "readiness replay text references a private/session/auth artifact",
                    )
                )
            if any(marker in lowered for marker in FORBIDDEN_TEXT_MARKERS):
                issues.append(
                    ValidationIssue(
                        "forbidden_readiness_claim",
                        path,
                        "readiness replay text includes an active, live, official-action, guarantee, or mutation claim",
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
