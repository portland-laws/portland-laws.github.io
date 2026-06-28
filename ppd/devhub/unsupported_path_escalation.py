"""Deterministic unsupported-path escalation helpers for PP&D workflows.

This module intentionally does not crawl, open browsers, authenticate, upload,
submit, schedule, pay, certify, or infer permit-specific eligibility. It only
turns an already-observed or requested unsupported path into a commit-safe
manual-handoff record that callers can journal or present to an agent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence


CONSEQUENTIAL_ACTIONS = frozenset(
    {
        "account_creation",
        "captcha",
        "certification",
        "mfa",
        "password_recovery",
        "payment",
        "schedule_inspection",
        "submission",
        "upload",
    }
)

_KEYWORD_ACTIONS: tuple[tuple[str, str], ...] = (
    ("captcha", "captcha"),
    ("mfa", "mfa"),
    ("multi-factor", "mfa"),
    ("multifactor", "mfa"),
    ("two-factor", "mfa"),
    ("2fa", "mfa"),
    ("create account", "account_creation"),
    ("register account", "account_creation"),
    ("password recovery", "password_recovery"),
    ("reset password", "password_recovery"),
    ("pay", "payment"),
    ("payment", "payment"),
    ("credit card", "payment"),
    ("submit payment", "payment"),
    ("upload", "upload"),
    ("attach file", "upload"),
    ("attachment", "upload"),
    ("submit", "submission"),
    ("file application", "submission"),
    ("purchase permit", "submission"),
    ("certify", "certification"),
    ("certification", "certification"),
    ("acknowledgement", "certification"),
    ("acknowledgment", "certification"),
    ("schedule", "schedule_inspection"),
    ("inspection appointment", "schedule_inspection"),
)

_DEFAULT_SAFE_ACTIONS = (
    "explain why the path is unsupported for unattended automation",
    "ask the user to handle the official step directly in the live PP&D or DevHub surface",
    "continue only with source-backed read-only review or reversible local draft work",
)


@dataclass(frozen=True)
class UnsupportedPathEscalation:
    """Commit-safe manual-handoff record for an unsupported PP&D path."""

    path_id: str
    reason: str
    blocked_actions: tuple[str, ...]
    required_handoff: str = "manual_user_handoff"
    requires_attendance: bool = True
    requires_exact_confirmation: bool = True
    next_safe_actions: tuple[str, ...] = _DEFAULT_SAFE_ACTIONS
    source_evidence_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_journal_event(self) -> dict[str, object]:
        """Return a redacted event suitable for the PP&D action journal."""

        return {
            "event_type": "manual_handoff",
            "path_id": self.path_id,
            "reason": self.reason,
            "blocked_actions": list(self.blocked_actions),
            "required_handoff": self.required_handoff,
            "requires_attendance": self.requires_attendance,
            "requires_exact_confirmation": self.requires_exact_confirmation,
            "next_safe_actions": list(self.next_safe_actions),
            "source_evidence_ids": list(self.source_evidence_ids),
        }


def classify_unsupported_actions(description: str, explicit_actions: Iterable[str] = ()) -> tuple[str, ...]:
    """Classify consequential actions from text and explicit caller input.

    The classifier is deliberately small and conservative. Unknown text returns
    ``("unsupported_or_unclear_path",)`` instead of trying to infer a permit
    domain, DevHub state, or official consequence.
    """

    detected = {action.strip().lower().replace(" ", "_") for action in explicit_actions if action.strip()}
    lowered = description.casefold()
    for keyword, action in _KEYWORD_ACTIONS:
        if keyword in lowered:
            detected.add(action)

    known_or_unknown = detected.intersection(CONSEQUENTIAL_ACTIONS)
    if known_or_unknown:
        return tuple(sorted(known_or_unknown))
    return ("unsupported_or_unclear_path",)


def escalate_unsupported_path(
    path_id: str,
    description: str,
    *,
    explicit_actions: Iterable[str] = (),
    source_evidence_ids: Sequence[str] = (),
    next_safe_actions: Sequence[str] | None = None,
) -> UnsupportedPathEscalation:
    """Build a deterministic escalation for an unsupported PP&D path."""

    normalized_path_id = path_id.strip()
    if not normalized_path_id:
        raise ValueError("path_id is required")

    blocked_actions = classify_unsupported_actions(description, explicit_actions)
    reason = _reason_for(description, blocked_actions)
    return UnsupportedPathEscalation(
        path_id=normalized_path_id,
        reason=reason,
        blocked_actions=blocked_actions,
        next_safe_actions=tuple(next_safe_actions) if next_safe_actions is not None else _DEFAULT_SAFE_ACTIONS,
        source_evidence_ids=tuple(source_evidence_ids),
    )


def escalation_from_mapping(data: Mapping[str, object]) -> UnsupportedPathEscalation:
    """Create an escalation from a plain mapping without trusting private values."""

    path_id = str(data.get("path_id", "")).strip()
    description = str(data.get("description", ""))
    explicit_actions_value = data.get("explicit_actions", ())
    source_evidence_value = data.get("source_evidence_ids", ())

    explicit_actions = _string_sequence(explicit_actions_value, "explicit_actions")
    source_evidence_ids = _string_sequence(source_evidence_value, "source_evidence_ids")
    return escalate_unsupported_path(
        path_id,
        description,
        explicit_actions=explicit_actions,
        source_evidence_ids=source_evidence_ids,
    )


def _reason_for(description: str, blocked_actions: Sequence[str]) -> str:
    concise_description = " ".join(description.split())
    if not concise_description:
        concise_description = "requested PP&D path has no source-backed supported automation route"
    actions = ", ".join(blocked_actions)
    return f"Unsupported PP&D path requires manual handoff before {actions}: {concise_description}"


def _string_sequence(value: object, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a string or sequence of strings") from exc
    if not all(isinstance(item, str) for item in items):
        raise ValueError(f"{field_name} must contain only strings")
    return tuple(item for item in items if item)
