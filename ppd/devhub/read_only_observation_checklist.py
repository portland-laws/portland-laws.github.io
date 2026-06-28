"""Validation for commit-safe DevHub read-only observation checklist packets.

The validator is intentionally conservative. Read-only observation packets may describe
public or redacted UI structure, but they must not contain private authenticated capture
artifacts, credential prompts, consequential controls, or claims that a live authenticated
capture occurred.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ObservationChecklistFinding:
    """A policy violation found in a DevHub read-only observation packet."""

    path: str
    category: str
    message: str


@dataclass(frozen=True)
class ObservationChecklistValidation:
    """Validation result for a read-only observation checklist packet."""

    ok: bool
    findings: tuple[ObservationChecklistFinding, ...]


_FORBIDDEN_KEY_TOKENS: tuple[tuple[str, str], ...] = (
    ("automated_login", "automated login"),
    ("login_automation", "automated login"),
    ("auto_login", "automated login"),
    ("password", "credential prompt"),
    ("passcode", "credential prompt"),
    ("credential", "credential prompt"),
    ("secret", "credential prompt"),
    ("mfa", "MFA"),
    ("otp", "MFA"),
    ("totp", "MFA"),
    ("captcha", "CAPTCHA"),
    ("account_creation", "account creation"),
    ("create_account", "account creation"),
    ("register_account", "account creation"),
    ("private_value", "private field value"),
    ("private_field", "private field value"),
    ("field_value", "private field value"),
    ("observed_value", "private field value"),
    ("raw_value", "private field value"),
    ("screenshot", "screenshot"),
    ("trace", "trace"),
    ("har", "HAR data"),
    ("cookie", "cookie"),
    ("auth_state", "auth state"),
    ("storage_state", "auth state"),
    ("session_state", "auth state"),
    ("local_storage", "auth state"),
    ("session_storage", "auth state"),
)

_FORBIDDEN_TEXT_PATTERNS: tuple[tuple[str, str], ...] = (
    ("automated login", "automated login"),
    ("auto login", "automated login"),
    ("scripted login", "automated login"),
    ("filled password", "credential prompt"),
    ("password prompt", "credential prompt"),
    ("credential prompt", "credential prompt"),
    ("entered credentials", "credential prompt"),
    ("entered mfa", "MFA"),
    ("mfa code", "MFA"),
    ("one-time code", "MFA"),
    ("otp code", "MFA"),
    ("captcha", "CAPTCHA"),
    ("created account", "account creation"),
    ("account was created", "account creation"),
    ("register account", "account creation"),
    ("private field value", "private field value"),
    ("captured field value", "private field value"),
    ("observed value", "private field value"),
    ("screenshot", "screenshot"),
    ("playwright trace", "trace"),
    ("trace.zip", "trace"),
    ("har file", "HAR data"),
    (".har", "HAR data"),
    ("cookie", "cookie"),
    ("auth state", "auth state"),
    ("storage state", "auth state"),
    ("authenticated capture", "live authenticated capture claim"),
    ("live authenticated", "live authenticated capture claim"),
    ("captured while signed in", "live authenticated capture claim"),
    ("captured from my account", "live authenticated capture claim"),
)

_CONSEQUENTIAL_TEXT_PATTERNS: tuple[str, ...] = (
    "submit application",
    "submit permit",
    "final submit",
    "certify",
    "acknowledge and submit",
    "upload correction",
    "upload document",
    "attach file",
    "schedule inspection",
    "cancel inspection",
    "withdraw",
    "request extension",
    "reactivate",
    "purchase permit",
    "pay fee",
    "submit payment",
    "save payment",
    "payment details",
)

_CONSEQUENTIAL_ACTIONS: tuple[str, ...] = (
    "submit",
    "certify",
    "upload",
    "attach",
    "schedule",
    "cancel",
    "withdraw",
    "extend",
    "reactivate",
    "purchase",
    "pay",
)

_EMPTY_VALUES: tuple[Any, ...] = (None, "", (), [], {})


def validate_read_only_observation_packet(packet: Mapping[str, Any]) -> ObservationChecklistValidation:
    """Return policy findings for a DevHub read-only observation checklist packet."""

    findings = list(_walk(packet, "$"))
    return ObservationChecklistValidation(ok=not findings, findings=tuple(findings))


def assert_valid_read_only_observation_packet(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a packet is not commit-safe."""

    result = validate_read_only_observation_packet(packet)
    if result.ok:
        return
    details = "; ".join(f"{finding.path}: {finding.message}" for finding in result.findings)
    raise ValueError(f"DevHub read-only observation packet rejected: {details}")


def _walk(value: Any, path: str) -> Iterable[ObservationChecklistFinding]:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            key_path = f"{path}.{key}"
            yield from _check_key(key, child, key_path)
            yield from _walk(child, key_path)
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")
        return

    if isinstance(value, str):
        yield from _check_text(value, path)


def _check_key(key: str, value: Any, path: str) -> Iterable[ObservationChecklistFinding]:
    normalized = _normalize(key)
    for token, category in _FORBIDDEN_KEY_TOKENS:
        if token in normalized and value not in _EMPTY_VALUES:
            yield ObservationChecklistFinding(
                path=path,
                category=category,
                message=f"read-only observation packets must not include {category}",
            )

    if normalized in {"controls", "actions", "buttons", "links"}:
        yield from _check_consequential_controls(value, path)


def _check_text(text: str, path: str) -> Iterable[ObservationChecklistFinding]:
    normalized = _normalize(text)
    for pattern, category in _FORBIDDEN_TEXT_PATTERNS:
        if pattern in normalized:
            yield ObservationChecklistFinding(
                path=path,
                category=category,
                message=f"read-only observation packets must not include {category}",
            )

    for pattern in _CONSEQUENTIAL_TEXT_PATTERNS:
        if pattern in normalized:
            yield ObservationChecklistFinding(
                path=path,
                category="consequential control",
                message="read-only observation packets must not include consequential controls",
            )


def _check_consequential_controls(value: Any, path: str) -> Iterable[ObservationChecklistFinding]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            label = _control_label(item)
            if _is_consequential_label(label):
                yield ObservationChecklistFinding(
                    path=f"{path}[{index}]",
                    category="consequential control",
                    message="read-only observation packets must not include consequential controls",
                )
        return

    label = _control_label(value)
    if _is_consequential_label(label):
        yield ObservationChecklistFinding(
            path=path,
            category="consequential control",
            message="read-only observation packets must not include consequential controls",
        )


def _control_label(value: Any) -> str:
    if isinstance(value, Mapping):
        parts = []
        for key in ("label", "text", "name", "action", "aria_label", "role"):
            child = value.get(key)
            if isinstance(child, str):
                parts.append(child)
        return " ".join(parts)
    if isinstance(value, str):
        return value
    return ""


def _is_consequential_label(label: str) -> bool:
    normalized = _normalize(label)
    return any(action in normalized for action in _CONSEQUENTIAL_ACTIONS) or any(
        pattern in normalized for pattern in _CONSEQUENTIAL_TEXT_PATTERNS
    )


def _normalize(value: str) -> str:
    return value.lower().replace("-", "_").replace(" ", "_")
