"""Validation for attended DevHub read-only readiness decision packets.

The validator is intentionally schema-tolerant: daemon tasks and fixtures can pass
plain dictionaries from JSON packets without requiring a shared contract rewrite.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePath
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ReadOnlyReadinessViolation:
    """A policy violation found in a DevHub read-only readiness packet."""

    code: str
    path: str
    message: str


class ReadOnlyReadinessError(ValueError):
    """Raised when a readiness packet does not satisfy read-only guardrails."""

    def __init__(self, violations: Sequence[ReadOnlyReadinessViolation]) -> None:
        self.violations = tuple(violations)
        codes = ", ".join(v.code for v in self.violations)
        super().__init__(f"DevHub read-only readiness packet rejected: {codes}")


CONSEQUENTIAL_CONTROL_TERMS = (
    "submit",
    "certify",
    "acknowledge",
    "upload",
    "attach",
    "payment",
    "pay",
    "purchase",
    "schedule",
    "cancel",
    "withdraw",
    "extension",
    "reactivation",
    "account settings",
    "security settings",
)

FORBIDDEN_AUTOMATION_TERMS = (
    "captcha",
    "mfa",
    "multi-factor",
    "multifactor",
    "one-time code",
    "otp",
    "account creation",
    "create account",
    "register account",
    "password recovery",
    "live browser",
    "browser execution",
    "playwright executed",
    "clicked in devhub",
    "filled in devhub",
    "ran against devhub",
)

PRIVATE_ARTIFACT_KEY_TERMS = (
    "screenshot",
    "trace",
    "har",
    "storage_state",
    "storage state",
    "auth_state",
    "auth state",
    "session",
    "cookie",
    "credential",
    "password",
    "token",
)

PRIVATE_ARTIFACT_VALUE_TERMS = (
    ".har",
    "trace.zip",
    "storage_state",
    "auth_state",
    "cookies.json",
    "session.json",
    "playwright/.auth",
    "devhub-session",
    "screenshot",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
)


def validate_read_only_readiness_packet(packet: Mapping[str, Any]) -> None:
    """Raise if an attended DevHub read-only readiness packet is unsafe.

    The packet must include cited prerequisite links, cited readiness claims,
    explicit abort conditions, no private browser/session artifacts, no live
    browser execution claims, and no enabled consequential controls.
    """

    violations = list(iter_read_only_readiness_violations(packet))
    if violations:
        raise ReadOnlyReadinessError(violations)


def iter_read_only_readiness_violations(packet: Mapping[str, Any]) -> Iterable[ReadOnlyReadinessViolation]:
    if not isinstance(packet, Mapping):
        yield ReadOnlyReadinessViolation(
            "invalid_packet",
            "$",
            "Read-only readiness packet must be a mapping.",
        )
        return

    yield from _validate_prerequisite_links(packet)
    yield from _validate_readiness_claims(packet)
    yield from _validate_abort_conditions(packet)
    yield from _scan_for_private_artifacts(packet)
    yield from _scan_for_forbidden_automation(packet)
    yield from _validate_consequential_controls(packet)


def packet_is_read_only_ready(packet: Mapping[str, Any]) -> bool:
    """Return True only when the packet satisfies all readiness checks."""

    return not any(iter_read_only_readiness_violations(packet))


def _validate_prerequisite_links(packet: Mapping[str, Any]) -> Iterable[ReadOnlyReadinessViolation]:
    links = _first_present(packet, ("prerequisite_links", "prerequisites", "source_links"))
    if not _non_empty_sequence(links):
        yield ReadOnlyReadinessViolation(
            "missing_prerequisite_links",
            "$.prerequisite_links",
            "Read-only readiness requires at least one cited prerequisite link.",
        )
        return

    for index, link in enumerate(links):
        path = f"$.prerequisite_links[{index}]"
        if isinstance(link, str):
            if not link.strip():
                yield ReadOnlyReadinessViolation(
                    "missing_prerequisite_links",
                    path,
                    "Prerequisite link entries cannot be blank.",
                )
            continue
        if not isinstance(link, Mapping):
            yield ReadOnlyReadinessViolation(
                "invalid_prerequisite_link",
                path,
                "Prerequisite link entries must be URLs or mappings with URL and citation fields.",
            )
            continue
        if not _text_value(link.get("url") or link.get("href") or link.get("canonical_url")):
            yield ReadOnlyReadinessViolation(
                "missing_prerequisite_link_url",
                f"{path}.url",
                "Prerequisite link is missing a URL.",
            )
        if not _has_citation(link):
            yield ReadOnlyReadinessViolation(
                "missing_prerequisite_link_citation",
                path,
                "Prerequisite link is missing source evidence or citation metadata.",
            )


def _validate_readiness_claims(packet: Mapping[str, Any]) -> Iterable[ReadOnlyReadinessViolation]:
    claims = _first_present(packet, ("readiness_claims", "claims", "decisions"))
    if not _non_empty_sequence(claims):
        yield ReadOnlyReadinessViolation(
            "missing_readiness_claims",
            "$.readiness_claims",
            "Read-only readiness requires cited readiness claims.",
        )
        return

    for index, claim in enumerate(claims):
        path = f"$.readiness_claims[{index}]"
        if not isinstance(claim, Mapping):
            yield ReadOnlyReadinessViolation(
                "invalid_readiness_claim",
                path,
                "Readiness claims must be mappings with claim text and citations.",
            )
            continue
        if not _text_value(claim.get("claim") or claim.get("summary") or claim.get("text")):
            yield ReadOnlyReadinessViolation(
                "missing_readiness_claim_text",
                path,
                "Readiness claim is missing claim text.",
            )
        if not _has_citation(claim):
            yield ReadOnlyReadinessViolation(
                "uncited_readiness_claim",
                path,
                "Readiness claim must cite source evidence.",
            )


def _validate_abort_conditions(packet: Mapping[str, Any]) -> Iterable[ReadOnlyReadinessViolation]:
    abort_conditions = _first_present(packet, ("abort_conditions", "stop_conditions", "manual_handoff_conditions"))
    if not _non_empty_sequence(abort_conditions):
        yield ReadOnlyReadinessViolation(
            "missing_abort_conditions",
            "$.abort_conditions",
            "Read-only readiness requires explicit abort or manual handoff conditions.",
        )


def _scan_for_private_artifacts(value: Any, path: str = "$", key_hint: str = "") -> Iterable[ReadOnlyReadinessViolation]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            lowered_key = key_text.lower().replace("-", "_")
            if any(term in lowered_key for term in PRIVATE_ARTIFACT_KEY_TERMS) and _is_present(child):
                yield ReadOnlyReadinessViolation(
                    "private_or_session_artifact",
                    child_path,
                    "Read-only readiness packets must not include screenshots, traces, HAR files, stored auth state, credentials, cookies, tokens, or session artifacts.",
                )
            yield from _scan_for_private_artifacts(child, child_path, lowered_key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _scan_for_private_artifacts(child, f"{path}[{index}]", key_hint)
    elif isinstance(value, str):
        lowered_value = value.lower()
        if any(term in lowered_value for term in PRIVATE_ARTIFACT_VALUE_TERMS):
            yield ReadOnlyReadinessViolation(
                "private_or_session_artifact",
                path,
                "Read-only readiness packets must not reference screenshots, traces, HAR paths, stored auth state, or private browser artifacts.",
            )
        if _looks_like_private_path(value):
            yield ReadOnlyReadinessViolation(
                "private_or_session_artifact",
                path,
                "Read-only readiness packets must not include local private artifact paths.",
            )


def _scan_for_forbidden_automation(value: Any, path: str = "$") -> Iterable[ReadOnlyReadinessViolation]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _scan_for_forbidden_automation(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _scan_for_forbidden_automation(child, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        for term in FORBIDDEN_AUTOMATION_TERMS:
            if term in lowered:
                code = "live_browser_execution_claim" if "browser" in term or "devhub" in term else "forbidden_auth_or_account_automation"
                yield ReadOnlyReadinessViolation(
                    code,
                    path,
                    "Read-only readiness packets must not claim live browser execution or automation of CAPTCHA, MFA, account creation, or account recovery.",
                )
                break


def _validate_consequential_controls(packet: Mapping[str, Any]) -> Iterable[ReadOnlyReadinessViolation]:
    controls = _first_present(packet, ("controls", "ui_controls", "action_controls", "consequential_controls"))
    if not _non_empty_sequence(controls):
        return

    for index, control in enumerate(controls):
        path = f"$.controls[{index}]"
        if not isinstance(control, Mapping):
            continue
        label = str(control.get("label") or control.get("name") or control.get("action") or "").lower()
        kind = str(control.get("kind") or control.get("classification") or control.get("category") or "").lower()
        enabled = control.get("enabled")
        disabled = control.get("disabled")
        is_enabled = enabled is True or disabled is False
        is_consequential = "consequential" in kind or any(term in label for term in CONSEQUENTIAL_CONTROL_TERMS)
        if is_enabled and is_consequential:
            yield ReadOnlyReadinessViolation(
                "enabled_consequential_control",
                path,
                "Consequential controls must be absent or disabled in a read-only readiness packet.",
            )


def _first_present(packet: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in packet:
            return packet[key]
    return None


def _has_citation(value: Mapping[str, Any]) -> bool:
    citation_keys = (
        "citation",
        "citations",
        "source_evidence_id",
        "source_evidence_ids",
        "evidence",
        "evidence_ids",
        "evidence_links",
    )
    for key in citation_keys:
        if key in value and _is_present(value[key]):
            return True
    return False


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value) > 0
    if isinstance(value, Mapping):
        return len(value) > 0
    return True


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and len(value) > 0


def _text_value(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _looks_like_private_path(value: str) -> bool:
    lowered = value.lower()
    if not ("/" in lowered or "\\" in lowered):
        return False
    path_name = PurePath(lowered.replace("\\", "/")).name
    private_parts = ("auth", "cookie", "session", "trace", "har", "screenshot", "storage")
    return any(part in lowered for part in private_parts) or path_name.endswith((".har", ".png", ".jpg", ".jpeg", ".webp", ".zip"))
