"""Validation for DevHub read-only pilot readiness reconciliation packets.

The validator is intentionally deterministic and conservative. Readiness packets are
commit-safe summaries only; they must not carry browser artifacts, authenticated
state, private values, credential prompts, or claims that the pilot completed an
official/consequential action.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ReadinessPacketViolation:
    """A single readiness packet validation violation."""

    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ReadinessPacketValidationResult:
    """Validation result for a DevHub read-only pilot readiness packet."""

    ok: bool
    violations: tuple[ReadinessPacketViolation, ...]

    def require_ok(self) -> None:
        if self.ok:
            return
        details = "; ".join(
            f"{violation.code} at {violation.path}: {violation.message}"
            for violation in self.violations
        )
        raise ValueError(details)


_ARTIFACT_EXTENSIONS = (
    ".har",
    ".trace",
    ".trace.zip",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".bmp",
    ".tiff",
)

_ARTIFACT_KEYWORDS = (
    "screenshot",
    "screenshots",
    "screen_capture",
    "screen-capture",
    "trace",
    "traces",
    "playwright_trace",
    "har",
    "network_har",
)

_SENSITIVE_KEYWORDS = (
    "cookie",
    "cookies",
    "auth_state",
    "authstate",
    "storage_state",
    "session_state",
    "local_storage",
    "session_storage",
    "authorization",
    "bearer",
    "password",
    "passwd",
    "credential",
    "credentials",
    "secret",
    "token",
    "private_value",
    "private_values",
    "raw_value",
    "raw_values",
    "payment_detail",
    "payment_details",
    "card_number",
    "ssn",
)

_CREDENTIAL_PROMPT_PHRASES = (
    "enter your password",
    "entered password",
    "prompted for password",
    "asked for password",
    "credential prompt",
    "asked for credentials",
    "enter credentials",
    "entered credentials",
)

_FORBIDDEN_AUTOMATION_PHRASES = (
    "automated login",
    "logged in automatically",
    "auto login",
    "auto-login",
    "automated sign in",
    "automated sign-in",
    "completed mfa",
    "automated mfa",
    "bypassed mfa",
    "solved mfa",
    "completed captcha",
    "automated captcha",
    "bypassed captcha",
    "solved captcha",
    "created account",
    "created a devhub account",
    "registered account",
    "automated account creation",
)

_CONSEQUENTIAL_COMPLETION_PHRASES = (
    "completed consequential action",
    "consequential action completed",
    "official action completed",
    "finished official action",
    "post-action completion",
)

_OFFICIAL_ACTION_PHRASES = (
    "uploaded corrections",
    "uploaded documents",
    "uploaded plans",
    "completed upload",
    "submitted application",
    "submitted permit",
    "submitted request",
    "completed submission",
    "paid fee",
    "paid fees",
    "submitted payment",
    "completed payment",
    "scheduled inspection",
    "scheduled appointment",
    "cancelled inspection",
    "canceled inspection",
    "cancelled permit",
    "canceled permit",
    "certified application",
    "completed certification",
    "signed certification",
)

_NEGATING_PHRASES = (
    "did not",
    "do not",
    "does not",
    "must not",
    "not completed",
    "not automate",
    "not automated",
    "not uploaded",
    "not submitted",
    "not paid",
    "not scheduled",
    "not cancelled",
    "not canceled",
    "not certified",
    "blocked",
    "refused",
    "rejected",
    "without completing",
    "no official",
    "no upload",
    "no submission",
    "no payment",
    "no scheduling",
    "no cancellation",
    "no certification",
)

_REQUIRED_ATTESTATION_TERMS = (
    "screenshots",
    "traces",
    "har",
    "cookies",
    "auth state",
    "private values",
    "credentials",
)


def validate_read_only_pilot_readiness_packet(
    packet: Mapping[str, Any],
) -> ReadinessPacketValidationResult:
    """Validate a DevHub read-only pilot readiness reconciliation packet.

    The accepted packet is a redacted, commit-safe mapping. Any browser artifact,
    sensitive authenticated value, credential prompt, forbidden automation claim,
    official action completion claim, or missing redaction attestation is rejected.
    """

    violations: list[ReadinessPacketViolation] = []

    if not isinstance(packet, Mapping):
        violations.append(
            ReadinessPacketViolation(
                code="packet_not_mapping",
                path="$",
                message="readiness packet must be a mapping",
            )
        )
        return ReadinessPacketValidationResult(ok=False, violations=tuple(violations))

    for path, key, value in _walk_packet(packet):
        key_text = _normalize_token(key)
        value_text = _normalize_text(value) if isinstance(value, str) else ""

        if _contains_any(key_text, _ARTIFACT_KEYWORDS) or _looks_like_artifact(value):
            violations.append(
                ReadinessPacketViolation(
                    code="prohibited_browser_artifact",
                    path=path,
                    message="screenshots, traces, HAR files, and image captures are not allowed in readiness packets",
                )
            )

        if _contains_any(key_text, _SENSITIVE_KEYWORDS):
            violations.append(
                ReadinessPacketViolation(
                    code="prohibited_sensitive_field",
                    path=path,
                    message="cookies, auth state, credentials, tokens, private values, and payment details are not allowed",
                )
            )

        if value_text:
            if _contains_any(value_text, _CREDENTIAL_PROMPT_PHRASES):
                violations.append(
                    ReadinessPacketViolation(
                        code="credential_prompt_claim",
                        path=path,
                        message="credential prompts must not be represented as pilot readiness evidence",
                    )
                )

            if _contains_claim(value_text, _FORBIDDEN_AUTOMATION_PHRASES):
                violations.append(
                    ReadinessPacketViolation(
                        code="forbidden_automation_claim",
                        path=path,
                        message="automated login, MFA, CAPTCHA, and account-creation claims are prohibited",
                    )
                )

            if _contains_claim(value_text, _CONSEQUENTIAL_COMPLETION_PHRASES):
                violations.append(
                    ReadinessPacketViolation(
                        code="consequential_completion_claim",
                        path=path,
                        message="read-only readiness packets cannot claim consequential action completion",
                    )
                )

            if _contains_claim(value_text, _OFFICIAL_ACTION_PHRASES):
                violations.append(
                    ReadinessPacketViolation(
                        code="official_action_completion_claim",
                        path=path,
                        message="upload, submission, payment, scheduling, cancellation, and certification completion claims are prohibited",
                    )
                )

    if not _has_redaction_attestation(packet):
        violations.append(
            ReadinessPacketViolation(
                code="missing_redaction_attestation",
                path="$.redaction_attestation",
                message="packet must attest that prohibited artifacts and private values were absent or redacted",
            )
        )

    return ReadinessPacketValidationResult(
        ok=not violations,
        violations=tuple(violations),
    )


def assert_read_only_pilot_readiness_packet(packet: Mapping[str, Any]) -> None:
    """Raise ValueError unless the readiness packet is commit-safe."""

    validate_read_only_pilot_readiness_packet(packet).require_ok()


def _walk_packet(value: Any, path: str = "$", key: str = "") -> Iterable[tuple[str, str, Any]]:
    yield path, key, value
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_key_text = str(child_key)
            yield from _walk_packet(
                child_value,
                f"{path}.{child_key_text}",
                child_key_text,
            )
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child_value in enumerate(value):
            yield from _walk_packet(child_value, f"{path}[{index}]", key)


def _has_redaction_attestation(packet: Mapping[str, Any]) -> bool:
    for key in ("redaction_attestation", "redaction_attestations", "privacy_attestation"):
        if key in packet and _attestation_is_sufficient(packet[key]):
            return True
    return False


def _attestation_is_sufficient(value: Any) -> bool:
    if isinstance(value, Mapping):
        attested = value.get("attested", value.get("redacted", value.get("commit_safe")))
        if attested is not True:
            return False
        text = _normalize_text(" ".join(str(item) for item in _flatten_values(value)))
        return all(term in text for term in _REQUIRED_ATTESTATION_TERMS)

    if isinstance(value, str):
        text = _normalize_text(value)
        return (
            ("attest" in text or "redact" in text or "commit safe" in text)
            and all(term in text for term in _REQUIRED_ATTESTATION_TERMS)
        )

    return False


def _flatten_values(value: Any) -> Iterable[Any]:
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            yield child_key
            yield from _flatten_values(child_value)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child_value in value:
            yield from _flatten_values(child_value)
    else:
        yield value


def _looks_like_artifact(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = _normalize_text(value)
    path_name = PurePosixPath(text.replace("\\", "/")).name
    return path_name.endswith(_ARTIFACT_EXTENSIONS)


def _contains_claim(text: str, phrases: Sequence[str]) -> bool:
    if not _contains_any(text, phrases):
        return False
    return not _contains_any(text, _NEGATING_PHRASES)


def _contains_any(text: str, needles: Sequence[str]) -> bool:
    return any(needle in text for needle in needles)


def _normalize_token(value: str) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _normalize_text(value: Any) -> str:
    return " ".join(str(value).strip().lower().replace("_", " ").replace("-", " ").split())
