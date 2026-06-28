"""Validation for DevHub attended read-only pilot runbook packets.

The pilot packet is intentionally limited to preflight instructions and public,
committable metadata. It may describe prohibitions, but it must not carry any
instruction, artifact, selector, credential request, private value, or evidence
claim that would imply authenticated automation has already occurred.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence
import re


_ALLOWED_PACKET_KIND = "devhub_attended_read_only_pilot_runbook"
_ALLOWED_MODE = "attended_read_only_pilot"

_FORBIDDEN_KEY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("credential prompts", re.compile(r"(password|passcode|credential|secret|token|api[_-]?key)", re.IGNORECASE)),
    ("cookies", re.compile(r"cookie", re.IGNORECASE)),
    ("auth state", re.compile(r"(auth|storage|session)[_-]?(state|file|path|json)?", re.IGNORECASE)),
    ("screenshots", re.compile(r"screenshot", re.IGNORECASE)),
    ("traces", re.compile(r"\btrace(s)?\b|trace[_-]?path", re.IGNORECASE)),
    ("HAR data", re.compile(r"\bhar\b|har[_-]?path", re.IGNORECASE)),
    ("private field values", re.compile(r"(private|raw|captured|field)[_-]?(value|values|payload|data)", re.IGNORECASE)),
)

_FORBIDDEN_INSTRUCTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("automated login", re.compile(r"\b(auto(mate|mated)?|script|bot|worker|playwright)\b.{0,80}\b(login|log in|sign in|signin|authenticate)\b|\b(login|log in|sign in|signin|authenticate)\b.{0,80}\b(auto(mate|mated)?|script|bot|worker|playwright)\b", re.IGNORECASE)),
    ("MFA automation", re.compile(r"\b(auto(mate|mated)?|script|bot|worker|playwright|solve|bypass)\b.{0,80}\b(mfa|2fa|multi[- ]factor|one[- ]time code|otp)\b|\b(mfa|2fa|multi[- ]factor|one[- ]time code|otp)\b.{0,80}\b(auto(mate|mated)?|script|bot|worker|playwright|solve|bypass)\b", re.IGNORECASE)),
    ("CAPTCHA automation", re.compile(r"\b(auto(mate|mated)?|script|bot|worker|playwright|solve|bypass)\b.{0,80}\b(captcha|recaptcha|hcaptcha)\b|\b(captcha|recaptcha|hcaptcha)\b.{0,80}\b(auto(mate|mated)?|script|bot|worker|playwright|solve|bypass)\b", re.IGNORECASE)),
    ("account creation", re.compile(r"\b(create|register|open|provision)\b.{0,80}\b(account|profile|login)\b", re.IGNORECASE)),
    ("credential prompts", re.compile(r"\b(prompt|ask|request|collect|enter|fill|type|store)\b.{0,80}\b(password|passcode|credential|secret|token|otp|mfa code)\b", re.IGNORECASE)),
    ("consequential controls", re.compile(r"\b(click|press|select|activate|invoke|submit|confirm)\b.{0,80}\b(submit|certif(y|ication)|acknowledge|upload|attach|schedule|cancel|withdraw|pay|purchase|payment|finalize|issue|reactivate|extend)\b", re.IGNORECASE)),
    ("claims live authenticated capture occurred", re.compile(r"\b(live|authenticated|account[- ]scoped|private)\b.{0,80}\b(capture|crawl|scrape|recording|recorded|collected|extracted|observed)\b.{0,80}\b(complete|completed|done|occurred|already|successful|captured)\b|\b(captured|recorded|collected|extracted|scraped)\b.{0,80}\b(live|authenticated|account[- ]scoped|private)\b", re.IGNORECASE)),
)

_PRIVATE_VALUE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("credential prompts", re.compile(r"password\s*[:=]|credential\s*[:=]|secret\s*[:=]|token\s*[:=]", re.IGNORECASE)),
    ("cookies", re.compile(r"\b(set-cookie|cookie)\s*[:=]", re.IGNORECASE)),
    ("auth state", re.compile(r"\b(localStorage|sessionStorage|storageState|authState)\b", re.IGNORECASE)),
    ("HAR data", re.compile(r"\b(log\.entries|request\.headers|response\.headers)\b", re.IGNORECASE)),
    ("private field values", re.compile(r"\b(owner|applicant|email|phone|address|permit|case|invoice|license)\s*[:=]\s*[^\s,;{}\[\]]+", re.IGNORECASE)),
)

_PROHIBITION_KEYS = frozenset({
    "blocked_actions",
    "disallowed_actions",
    "forbidden_actions",
    "guardrails",
    "manual_handoff_required_for",
    "must_not",
    "non_negotiable_boundaries",
    "policy_notes",
    "prohibited_artifacts",
    "prohibitions",
    "refusals",
})

_INSTRUCTION_KEYS = frozenset({
    "actions",
    "allowed_actions",
    "automation_steps",
    "browser_steps",
    "capture_steps",
    "claims",
    "controls",
    "evidence",
    "expected_artifacts",
    "fields",
    "instructions",
    "outputs",
    "postconditions",
    "recorded_artifacts",
    "selectors",
    "steps",
    "success_criteria",
})


@dataclass(frozen=True)
class PilotRunbookValidationIssue:
    """A deterministic validation issue for a pilot runbook packet."""

    path: str
    category: str
    message: str


@dataclass(frozen=True)
class PilotRunbookValidationResult:
    """Validation result for a DevHub attended read-only pilot packet."""

    ok: bool
    issues: tuple[PilotRunbookValidationIssue, ...]

    def require_ok(self) -> None:
        if self.ok:
            return
        details = "; ".join(f"{issue.path}: {issue.message}" for issue in self.issues)
        raise ValueError(f"DevHub pilot runbook packet rejected: {details}")


def validate_devhub_attended_read_only_pilot_runbook(packet: Mapping[str, Any]) -> PilotRunbookValidationResult:
    """Reject unsafe DevHub attended read-only pilot runbook packets.

    Safe packets are limited to public preflight metadata, human-attended login
    handoff requirements, read-only observation scope, and explicit refusals.
    The validator is conservative for executable fields while allowing safety
    language in prohibition fields.
    """

    issues: list[PilotRunbookValidationIssue] = []

    if not isinstance(packet, Mapping):
        issues.append(PilotRunbookValidationIssue("$", "packet", "packet must be a mapping"))
        return PilotRunbookValidationResult(ok=False, issues=tuple(issues))

    if packet.get("packet_kind") != _ALLOWED_PACKET_KIND:
        issues.append(
            PilotRunbookValidationIssue(
                "packet_kind",
                "packet",
                f"packet_kind must be {_ALLOWED_PACKET_KIND!r}",
            )
        )

    if packet.get("mode") != _ALLOWED_MODE:
        issues.append(
            PilotRunbookValidationIssue(
                "mode",
                "packet",
                f"mode must be {_ALLOWED_MODE!r}",
            )
        )

    for path, key, value, ancestors in _walk_packet(packet):
        normalized_key = _normalize_key(key)
        if _is_prohibition_context(ancestors):
            continue

        for category, pattern in _FORBIDDEN_KEY_PATTERNS:
            if pattern.search(normalized_key):
                issues.append(
                    PilotRunbookValidationIssue(
                        path,
                        category,
                        f"field name is not allowed in read-only pilot packets: {key!r}",
                    )
                )

        if isinstance(value, str):
            text = value.strip()
            if not text:
                continue
            patterns = _PRIVATE_VALUE_PATTERNS
            if _is_instruction_context(ancestors) or normalized_key in _INSTRUCTION_KEYS:
                patterns = _FORBIDDEN_INSTRUCTION_PATTERNS + _PRIVATE_VALUE_PATTERNS
            for category, pattern in patterns:
                if pattern.search(text):
                    issues.append(
                        PilotRunbookValidationIssue(
                            path,
                            category,
                            f"content is not allowed in read-only pilot packets: {category}",
                        )
                    )

    return PilotRunbookValidationResult(ok=not issues, issues=tuple(issues))


def assert_devhub_attended_read_only_pilot_runbook(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a pilot runbook packet is unsafe."""

    validate_devhub_attended_read_only_pilot_runbook(packet).require_ok()


def _walk_packet(value: Any, path: str = "$", key: str = "$", ancestors: Sequence[str] = ()) -> Iterable[tuple[str, str, Any, tuple[str, ...]]]:
    yield path, key, value, tuple(ancestors)
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_key_text = str(child_key)
            child_path = f"{path}.{child_key_text}"
            yield from _walk_packet(child_value, child_path, child_key_text, (*ancestors, _normalize_key(child_key_text)))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child_value in enumerate(value):
            child_path = f"{path}[{index}]"
            yield from _walk_packet(child_value, child_path, key, ancestors)


def _normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")


def _is_prohibition_context(ancestors: Sequence[str]) -> bool:
    return any(part in _PROHIBITION_KEYS for part in ancestors)


def _is_instruction_context(ancestors: Sequence[str]) -> bool:
    return any(part in _INSTRUCTION_KEYS for part in ancestors)
