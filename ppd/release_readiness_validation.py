"""Offline release readiness packet validation for PP&D guardrails.

The validator is intentionally conservative. It accepts plain dictionaries loaded
from deterministic fixtures or authored release packets and returns structured
violations without performing network, crawler, processor, compiler, LLM, or
DevHub actions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse


_PRIVATE_HOST_PATTERNS = (
    re.compile(r"(^|\.)(localhost|local|internal|lan|home|corp|intranet)$", re.IGNORECASE),
    re.compile(r"^10\."),
    re.compile(r"^127\."),
    re.compile(r"^169\.254\."),
    re.compile(r"^172\.(1[6-9]|2[0-9]|3[0-1])\."),
    re.compile(r"^192\.168\."),
)

_RAW_REFERENCE_RE = re.compile(
    r"\b(raw\s+body|download(?:ed)?\s+(?:file|document|artifact)|archive\s+(?:file|copy|dump)|"
    r"crawl\s+(?:dump|output)|html\s+dump|pdf\s+download)\b",
    re.IGNORECASE,
)

_LIVE_EXECUTION_RE = re.compile(
    r"\b(live\s+(?:crawler|processor|compiler|llm|devhub)|ran\s+(?:the\s+)?(?:crawler|processor|compiler|llm)|"
    r"executed\s+(?:the\s+)?(?:crawler|processor|compiler|llm|devhub)|devhub\s+(?:session|automation|run)|"
    r"submitted\s+to\s+devhub|compiled\s+live)\b",
    re.IGNORECASE,
)

_OUTCOME_GUARANTEE_RE = re.compile(
    r"\b(permit\s+(?:will|shall)\s+be\s+(?:approved|issued)|approval\s+(?:is\s+)?guaranteed|"
    r"legally\s+guaranteed|guarantees?\s+(?:approval|issuance|compliance|permit outcome)|"
    r"no\s+(?:legal|permitting)\s+risk|certain\s+(?:approval|permit issuance))\b",
    re.IGNORECASE,
)

_READINESS_CLAIM_RE = re.compile(
    r"\b(ready\s+for\s+(?:release|promotion|production|operator use)|release\s+ready|"
    r"approved\s+for\s+release|safe\s+to\s+promote|promotion\s+ready|ship\s+ready)\b",
    re.IGNORECASE,
)

_PRIVATE_PATH_RE = re.compile(
    r"(^|[\s:'\"])(/home/|/Users/|/root/|/var/folders/|/tmp/|~/|[A-Za-z]:\\|\\\\)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ReadinessViolation:
    code: str
    message: str


def validate_release_readiness_packet(packet: Mapping[str, Any]) -> list[ReadinessViolation]:
    """Return deterministic validation violations for an offline readiness packet."""
    violations: list[ReadinessViolation] = []
    text = _flatten_text(packet)

    citations = _as_list(packet.get("citations"))
    claims = _as_list(packet.get("readiness_claims"))
    if not claims and _READINESS_CLAIM_RE.search(text):
        claims = ["implicit readiness claim"]
    if claims and not citations:
        violations.append(ReadinessViolation("uncited_readiness_claim", "Readiness claims require at least one public citation."))

    if _RAW_REFERENCE_RE.search(text):
        violations.append(ReadinessViolation("raw_reference", "Raw body, download, archive, or crawl-output references are not allowed in release packets."))

    urls = list(_iter_urls(packet))
    if any(_is_private_or_authenticated_url(url) for url in urls):
        violations.append(ReadinessViolation("private_or_authenticated_url", "Private, local, or authenticated URLs are not allowed."))

    if _PRIVATE_PATH_RE.search(text):
        violations.append(ReadinessViolation("local_private_path", "Local private filesystem paths are not allowed."))

    if _LIVE_EXECUTION_RE.search(text):
        violations.append(ReadinessViolation("live_execution_claim", "Release packets must not claim live crawler, processor, compiler, LLM, or DevHub execution."))

    if _OUTCOME_GUARANTEE_RE.search(text):
        violations.append(ReadinessViolation("outcome_guarantee", "Legal or permitting outcome guarantees are not allowed."))

    if not _has_nonempty(packet, "blockers"):
        violations.append(ReadinessViolation("missing_blockers", "Release packets must include blockers, even when the list is empty with an explicit rationale."))

    if not _has_operator_signoff(packet):
        violations.append(ReadinessViolation("missing_operator_signoff", "Release packets require an explicit operator signoff."))

    if not _has_nonempty(packet, "rollback_checkpoints"):
        violations.append(ReadinessViolation("missing_rollback_checkpoints", "Release packets require rollback checkpoints."))

    controls = packet.get("consequential_controls")
    if _is_enabled(controls):
        violations.append(ReadinessViolation("enabled_consequential_controls", "Consequential controls must be disabled for offline release readiness."))

    flags = packet.get("flags", {})
    if isinstance(flags, Mapping):
        active_flags = [name for name in ("promote", "promotion", "mutate", "mutation", "apply", "submit") if _is_enabled(flags.get(name))]
        if active_flags:
            violations.append(ReadinessViolation("active_promotion_or_mutation_flag", "Promotion and mutation flags must be disabled."))
    elif _is_enabled(flags):
        violations.append(ReadinessViolation("active_promotion_or_mutation_flag", "Promotion and mutation flags must be disabled."))

    return violations


def violation_codes(packet: Mapping[str, Any]) -> list[str]:
    return [violation.code for violation in validate_release_readiness_packet(packet)]


def _has_nonempty(packet: Mapping[str, Any], key: str) -> bool:
    value = packet.get(key)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Iterable):
        return bool(list(value))
    return bool(value)


def _has_operator_signoff(packet: Mapping[str, Any]) -> bool:
    signoff = packet.get("operator_signoff", packet.get("operator_signoffs"))
    if isinstance(signoff, Mapping):
        return bool(signoff.get("name") and signoff.get("timestamp") and signoff.get("attestation"))
    if isinstance(signoff, list):
        return any(isinstance(item, Mapping) and item.get("name") and item.get("timestamp") for item in signoff)
    return bool(signoff)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _is_enabled(value: Any) -> bool:
    if isinstance(value, Mapping):
        enabled = value.get("enabled", value.get("active", False))
        return _is_enabled(enabled)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled", "active"}
    return bool(value)


def _flatten_text(value: Any) -> str:
    parts: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            parts.append(str(key))
            parts.append(_flatten_text(item))
    elif isinstance(value, list):
        for item in value:
            parts.append(_flatten_text(item))
    elif value is not None:
        parts.append(str(value))
    return "\n".join(parts)


def _iter_urls(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        for item in value.values():
            yield from _iter_urls(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_urls(item)
    elif isinstance(value, str):
        for match in re.finditer(r"https?://[^\s)\]}'\"]+", value):
            yield match.group(0).rstrip(".,;")


def _is_private_or_authenticated_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if parsed.username or parsed.password:
        return True
    if any(token in parsed.query.lower() for token in ("token=", "apikey=", "api_key=", "access_token=", "signature=")):
        return True
    return any(pattern.search(host) for pattern in _PRIVATE_HOST_PATTERNS)
