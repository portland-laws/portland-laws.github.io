"""Validation for DevHub read-only observation redaction acceptance packets v3.

The validator is intentionally schema-light: acceptance packets may evolve, but they must
carry the required evidence groups and must not claim or preserve private/session data or
consequential DevHub actions.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable


@dataclass(frozen=True)
class AcceptanceIssue:
    """A deterministic validation finding for an acceptance packet."""

    code: str
    message: str
    path: str


_REQUIRED_EVIDENCE: tuple[tuple[str, str], ...] = (
    ("missing_observation_intake_references", "observation_intake_references"),
    ("missing_redaction_coverage_checks", "redaction_coverage_checks"),
    ("missing_private_value_omission_evidence", "private_value_omission_evidence"),
    ("missing_route_pattern_normalization_checks", "route_pattern_normalization_checks"),
    (
        "missing_selector_evidence_confidence_summaries",
        "selector_evidence_confidence_summaries",
    ),
    (
        "missing_unsupported_manual_handoff_reminders",
        "unsupported_manual_handoff_reminders",
    ),
    ("missing_fixture_promotion_holds", "fixture_promotion_holds"),
    ("missing_reviewer_routing", "reviewer_routing"),
    ("missing_rollback_notes", "rollback_notes"),
    ("missing_validation_commands", "validation_commands"),
)

_PROHIBITED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "private_session_auth_artifact",
        re.compile(
            r"\b(cookie|cookies|session\s*state|storage\s*state|auth\s*state|authorization|"
            r"bearer\s+token|access\s*token|refresh\s*token|password|credential|secret|"
            r"csrf|mfa|captcha|private\s+value|raw\s+authenticated|local\s+private\s+file)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "screenshot_trace_har_claim",
        re.compile(r"\b(screenshot|screen\s*shot|trace|har\s*file|\.har\b|video\s*capture)\b", re.IGNORECASE),
    ),
    (
        "live_devhub_interaction_claim",
        re.compile(
            r"\b(live\s+devhub|interacted\s+with\s+devhub|clicked\s+in\s+devhub|"
            r"opened\s+devhub|visited\s+devhub|authenticated\s+devhub\s+session)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "form_fill_or_upload_claim",
        re.compile(
            r"\b(filled\s+(?:the\s+)?form|form\s*fill|typed\s+into|entered\s+into|"
            r"uploaded|upload\s+completed|attached\s+(?:the\s+)?file|staged\s+upload)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "official_action_completion_claim",
        re.compile(
            r"\b(submitted|submission\s+completed|certified|paid\s+fees?|payment\s+completed|"
            r"scheduled\s+inspection|cancelled|canceled|permit\s+issued|official\s+action\s+completed)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "legal_or_permitting_guarantee",
        re.compile(
            r"\b(guarantee(?:d|s)?|will\s+be\s+approved|approval\s+guaranteed|"
            r"legally\s+sufficient|compliant\s+as\s+a\s+matter\s+of\s+law|permit\s+will\s+issue)\b",
            re.IGNORECASE,
        ),
    ),
)

_ACTIVE_MUTATION_KEYS = {
    "active_mutation",
    "active_mutation_flag",
    "active_mutation_flags",
    "mutation_enabled",
    "mutations_enabled",
    "write_enabled",
    "writes_enabled",
    "allow_mutation",
    "allows_mutation",
    "can_mutate",
}


def validate_acceptance_packet_v3(packet: dict[str, Any]) -> list[AcceptanceIssue]:
    """Return validation issues for a DevHub redaction acceptance packet v3."""

    issues: list[AcceptanceIssue] = []

    if not isinstance(packet, dict):
        return [
            AcceptanceIssue(
                code="invalid_packet_type",
                message="Acceptance packet v3 must be a JSON object.",
                path="$",
            )
        ]

    version = packet.get("packet_version") or packet.get("version")
    if version != "devhub_read_only_observation_redaction_acceptance_v3":
        issues.append(
            AcceptanceIssue(
                code="invalid_packet_version",
                message="Packet version must be devhub_read_only_observation_redaction_acceptance_v3.",
                path="$.packet_version",
            )
        )

    for code, field in _REQUIRED_EVIDENCE:
        if _is_missing(packet.get(field)):
            issues.append(
                AcceptanceIssue(
                    code=code,
                    message=f"Acceptance packet v3 requires non-empty {field} evidence.",
                    path=f"$.{field}",
                )
            )

    for path, value in _walk(packet):
        if isinstance(value, str):
            for code, pattern in _PROHIBITED_PATTERNS:
                if pattern.search(value):
                    issues.append(
                        AcceptanceIssue(
                            code=code,
                            message="Acceptance packet v3 must not include prohibited DevHub artifact or action claims.",
                            path=path,
                        )
                    )
        if _is_active_mutation_flag(path, value):
            issues.append(
                AcceptanceIssue(
                    code="active_mutation_flag",
                    message="Acceptance packet v3 must remain read-only and must not enable active mutations.",
                    path=path,
                )
            )

    return _dedupe_issues(issues)


def assert_acceptance_packet_v3(packet: dict[str, Any]) -> None:
    """Raise ValueError when an acceptance packet has validation issues."""

    issues = validate_acceptance_packet_v3(packet)
    if issues:
        formatted = "; ".join(f"{issue.code} at {issue.path}" for issue in issues)
        raise ValueError(f"Invalid DevHub redaction acceptance packet v3: {formatted}")


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if _is_identifier(str(key)) else f"{path}[{key!r}]"
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


def _is_identifier(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value))


def _is_active_mutation_flag(path: str, value: Any) -> bool:
    key = path.rsplit(".", 1)[-1].strip("[]'").lower()
    if key not in _ACTIVE_MUTATION_KEYS:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "enabled", "active", "on"}
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return value is not None


def _dedupe_issues(issues: list[AcceptanceIssue]) -> list[AcceptanceIssue]:
    seen: set[tuple[str, str]] = set()
    deduped: list[AcceptanceIssue] = []
    for issue in issues:
        key = (issue.code, issue.path)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(issue)
    return deduped
