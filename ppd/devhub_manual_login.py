"""Attended DevHub manual-login scaffold helpers.

This module intentionally avoids browser state persistence. It is designed for
preflight checks and selector capture around a human-attended login flow.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Sequence


SENSITIVE_KEY_RE = re.compile(
    r"(password|passcode|token|secret|session|cookie|credential|authorization|auth|csrf|mfa)",
    re.IGNORECASE,
)
SENSITIVE_VALUE_RE = re.compile(
    r"(Bearer\s+[A-Za-z0-9._~+/=-]+|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SelectorCandidate:
    role: str
    name: str
    selector: str


@dataclass(frozen=True)
class AuthenticatedState:
    authenticated: bool
    evidence: tuple[str, ...]


class RedactionPolicy:
    """Redacts credential-bearing keys and common sensitive values."""

    replacement = "[REDACTED]"

    def redact_mapping(self, data: Mapping[str, Any]) -> dict[str, Any]:
        redacted: dict[str, Any] = {}
        for key, value in data.items():
            if SENSITIVE_KEY_RE.search(str(key)):
                redacted[str(key)] = self.replacement
            elif isinstance(value, Mapping):
                redacted[str(key)] = self.redact_mapping(value)
            elif isinstance(value, str):
                redacted[str(key)] = self.redact_text(value)
            else:
                redacted[str(key)] = value
        return redacted

    def redact_text(self, value: str) -> str:
        return SENSITIVE_VALUE_RE.sub(self.replacement, value)


class AuthenticatedStateDetector:
    """Detects whether a DevHub page appears to be logged in from safe signals."""

    default_positive_markers = (
        "sign out",
        "log out",
        "my permits",
        "dashboard",
        "account",
    )
    default_negative_markers = (
        "sign in",
        "log in",
        "create account",
    )

    def __init__(
        self,
        positive_markers: Iterable[str] | None = None,
        negative_markers: Iterable[str] | None = None,
    ) -> None:
        self.positive_markers = tuple(positive_markers or self.default_positive_markers)
        self.negative_markers = tuple(negative_markers or self.default_negative_markers)

    def detect_from_text(self, text: str) -> AuthenticatedState:
        normalized = text.casefold()
        evidence: list[str] = []
        for marker in self.positive_markers:
            if marker.casefold() in normalized:
                evidence.append(marker)
        for marker in self.negative_markers:
            if marker.casefold() in normalized:
                return AuthenticatedState(False, tuple(evidence + [marker]))
        return AuthenticatedState(bool(evidence), tuple(evidence))


class AccessibleSelectorCapture:
    """Builds stable Playwright-style selectors from accessible role/name data."""

    allowed_roles = frozenset(("button", "link", "textbox", "combobox", "checkbox", "heading"))

    def capture(self, elements: Sequence[Mapping[str, str]]) -> tuple[SelectorCandidate, ...]:
        candidates: list[SelectorCandidate] = []
        for element in elements:
            role = element.get("role", "").strip().lower()
            name = element.get("name", "").strip()
            if not role or not name or role not in self.allowed_roles:
                continue
            escaped_name = name.replace("\\", "\\\\").replace('"', '\\"')
            candidates.append(
                SelectorCandidate(
                    role=role,
                    name=name,
                    selector=f'get_by_role("{role}", name="{escaped_name}")',
                )
            )
        return tuple(candidates)


@dataclass(frozen=True)
class ManualLoginPreflightResult:
    authenticated: AuthenticatedState
    selectors: tuple[SelectorCandidate, ...]
    redacted_metadata: dict[str, Any]
    persisted_state: bool = False


class ManualLoginScaffold:
    """Coordinates safe attended-login preflight analysis from mocked snapshots."""

    def __init__(
        self,
        detector: AuthenticatedStateDetector | None = None,
        selector_capture: AccessibleSelectorCapture | None = None,
        redaction_policy: RedactionPolicy | None = None,
    ) -> None:
        self.detector = detector or AuthenticatedStateDetector()
        self.selector_capture = selector_capture or AccessibleSelectorCapture()
        self.redaction_policy = redaction_policy or RedactionPolicy()

    def analyze_snapshot(self, snapshot: Mapping[str, Any]) -> ManualLoginPreflightResult:
        text = str(snapshot.get("text", ""))
        raw_elements = snapshot.get("accessible_elements", ())
        if not isinstance(raw_elements, Sequence) or isinstance(raw_elements, (str, bytes)):
            raw_elements = ()
        elements = [item for item in raw_elements if isinstance(item, Mapping)]
        metadata = snapshot.get("metadata", {})
        if not isinstance(metadata, Mapping):
            metadata = {}
        return ManualLoginPreflightResult(
            authenticated=self.detector.detect_from_text(text),
            selectors=self.selector_capture.capture(elements),
            redacted_metadata=self.redaction_policy.redact_mapping(metadata),
        )
