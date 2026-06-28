"""Validation for combined public-and-DevHub stale-readiness packet v1.

The validator is intentionally offline and deterministic. It checks packet shape and
claim text only; it does not crawl, authenticate, download, or mutate anything.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    path: str


_REQUIRED_NONEMPTY_FIELDS: tuple[tuple[str, str], ...] = (
    ("public_monitoring_references", "missing public monitoring references"),
    ("stale_source_hold_references", "missing stale-source hold references"),
    ("devhub_surface_delta_references", "missing DevHub surface delta references"),
    ("devhub_agent_impact_references", "missing DevHub agent impact references"),
    ("dependency_ordering", "missing dependency ordering"),
    ("reviewer_routing", "missing reviewer routing"),
    ("rollback_notes", "missing rollback notes"),
    ("validation_commands", "missing validation commands"),
)

_REQUIRED_RECOMMENDATIONS = ("proceed", "hold", "reject")

_FORBIDDEN_KEY_PARTS = (
    "credential",
    "password",
    "token",
    "secret",
    "auth_state",
    "session",
    "browser_state",
    "screenshot",
    "trace",
    "har",
    "private",
    "raw_crawl",
    "downloaded",
)

_FORBIDDEN_TEXT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("credentials_or_session_artifact", re.compile(r"\b(credential|password|token|secret|auth state|session cookie|browser state)\b", re.I)),
    ("browser_evidence_artifact", re.compile(r"\b(screenshot|trace|HAR)\b", re.I)),
    ("private_raw_or_downloaded_artifact", re.compile(r"\b(private artifact|raw crawl|downloaded document|downloaded artifact)\b", re.I)),
    ("live_devhub_or_crawl_claim", re.compile(r"\b(live DevHub|live crawl|crawled DevHub|authenticated crawl|visited DevHub)\b", re.I)),
    ("official_action_completion_claim", re.compile(r"\b(official action completed|permit submitted|application submitted|inspection scheduled|certification completed)\b", re.I)),
    ("release_promotion_claim", re.compile(r"\b(release promoted|promoted to production|production release completed|shipped to production)\b", re.I)),
    ("legal_or_permitting_guarantee", re.compile(r"\b(legal guarantee|permitting guarantee|guaranteed approval|guarantees approval|will be approved|compliance guaranteed)\b", re.I)),
)

_MUTATION_FLAG_KEYS = (
    "active_mutation",
    "mutation_active",
    "mutates_live_system",
    "can_submit",
    "can_upload",
    "can_cancel",
    "can_certify",
    "can_schedule",
)


def validate_packet(packet: dict[str, Any]) -> list[ValidationIssue]:
    """Return validation issues for a combined stale-readiness packet v1."""

    issues: list[ValidationIssue] = []

    if packet.get("schema_version") not in {"combined-public-devhub-stale-readiness-packet-v1", "v1"}:
        issues.append(ValidationIssue("missing_or_unknown_schema_version", "missing combined packet v1 schema version", "schema_version"))

    for field, message in _REQUIRED_NONEMPTY_FIELDS:
        if _is_empty(packet.get(field)):
            issues.append(ValidationIssue(f"missing_{field}", message, field))

    recommendations = packet.get("recommendations")
    if not isinstance(recommendations, dict):
        issues.append(ValidationIssue("missing_recommendations", "missing proceed/hold/reject recommendations", "recommendations"))
    else:
        for recommendation in _REQUIRED_RECOMMENDATIONS:
            if _is_empty(recommendations.get(recommendation)):
                issues.append(
                    ValidationIssue(
                        f"missing_{recommendation}_recommendation",
                        f"missing {recommendation} recommendation",
                        f"recommendations.{recommendation}",
                    )
                )

    for path, key, value in _walk(packet):
        lowered_key = key.lower()
        if any(part in lowered_key for part in _FORBIDDEN_KEY_PARTS):
            issues.append(ValidationIssue("forbidden_artifact_reference", "packet references credentials/session/browser/screenshot/trace/HAR/private/raw/downloaded artifacts", path))

        if key in _MUTATION_FLAG_KEYS and value is True:
            issues.append(ValidationIssue("active_mutation_flag", "packet contains an active mutation flag", path))

        if isinstance(value, str):
            for code, pattern in _FORBIDDEN_TEXT_PATTERNS:
                if pattern.search(value):
                    issues.append(ValidationIssue(code, f"packet contains forbidden claim or artifact reference: {code}", path))

    return issues


def assert_valid_packet(packet: dict[str, Any]) -> None:
    issues = validate_packet(packet)
    if issues:
        rendered = "; ".join(f"{issue.code} at {issue.path}" for issue in issues)
        raise ValueError(rendered)


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _walk(value: Any, path: str = "$", key: str = "$") -> Iterable[tuple[str, str, Any]]:
    yield path, key, value
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            child_key_text = str(child_key)
            yield from _walk(child_value, f"{path}.{child_key_text}", child_key_text)
    elif isinstance(value, list):
        for index, child_value in enumerate(value):
            yield from _walk(child_value, f"{path}[{index}]", str(index))
