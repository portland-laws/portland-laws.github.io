"""Local validation helpers for attended DevHub handoff packets.

The helper in this module is intentionally side-effect free. It normalizes a
small, commit-safe packet that can be inspected before an attended DevHub task
continues, while rejecting session state, browser actions, credentials, traces,
screenshots, HAR data, local private paths, and other private artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse


class HandoffPacketError(ValueError):
    """Raised when an attended handoff packet is missing or unsafe."""


@dataclass(frozen=True)
class NormalizedHandoffPacket:
    """Commit-safe representation of an attended DevHub handoff packet."""

    task_id: str
    handoff_reason: str
    attendance_required: bool
    source_url: str
    page_title: str
    visible_headings: tuple[str, ...]
    required_user_actions: tuple[str, ...]
    safe_next_actions: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "handoff_reason": self.handoff_reason,
            "attendance_required": self.attendance_required,
            "source_url": self.source_url,
            "page_title": self.page_title,
            "visible_headings": list(self.visible_headings),
            "required_user_actions": list(self.required_user_actions),
            "safe_next_actions": list(self.safe_next_actions),
            "blocked_actions": list(self.blocked_actions),
            "evidence_refs": list(self.evidence_refs),
            "warnings": list(self.warnings),
        }


_FORBIDDEN_KEY_FRAGMENTS = (
    "auth",
    "cookie",
    "credential",
    "har",
    "localstorage",
    "mfa",
    "password",
    "payment",
    "screenshot",
    "session",
    "storagestate",
    "token",
    "trace",
)

_BROWSER_ACTION_KEYS = frozenset(
    {
        "actions",
        "browser_actions",
        "clicks",
        "fills",
        "keystrokes",
        "playwright_steps",
        "submissions",
        "uploads",
    }
)

_CONSEQUENTIAL_ACTION_WORDS = (
    "cancel",
    "certify",
    "pay",
    "purchase",
    "schedule",
    "submit",
    "upload",
    "withdraw",
)

_ALLOWED_HOSTS = frozenset(
    {
        "devhub.portlandoregon.gov",
        "www.portland.gov",
        "www.portlandoregon.gov",
    }
)


def normalize_attended_handoff_packet(packet: Mapping[str, Any]) -> NormalizedHandoffPacket:
    """Normalize and validate a minimal attended DevHub handoff packet.

    The input is a plain mapping from local observation code. The output is a
    deterministic, commit-safe object that contains only public or redacted UI
    metadata and explicit handoff instructions.
    """

    if not isinstance(packet, Mapping):
        raise HandoffPacketError("handoff packet must be a mapping")

    _reject_forbidden_material(packet)

    task_id = _required_text(packet, "task_id")
    handoff_reason = _required_text(packet, "handoff_reason")
    attendance_required = _required_bool(packet, "attendance_required")
    if not attendance_required:
        raise HandoffPacketError("handoff packet must require user attendance")

    source_url = _normalize_url(_required_text(packet, "source_url"))
    page_title = _optional_text(packet, "page_title")
    visible_headings = _text_tuple(packet.get("visible_headings"), "visible_headings")
    required_user_actions = _text_tuple(packet.get("required_user_actions"), "required_user_actions")
    safe_next_actions = _text_tuple(packet.get("safe_next_actions"), "safe_next_actions")
    blocked_actions = _text_tuple(packet.get("blocked_actions"), "blocked_actions")
    evidence_refs = _text_tuple(packet.get("evidence_refs"), "evidence_refs")
    warnings = _text_tuple(packet.get("warnings"), "warnings")

    if not required_user_actions:
        raise HandoffPacketError("handoff packet must name at least one required user action")
    if not blocked_actions:
        raise HandoffPacketError("handoff packet must name blocked actions")

    _reject_consequential_safe_actions(safe_next_actions)

    return NormalizedHandoffPacket(
        task_id=task_id,
        handoff_reason=handoff_reason,
        attendance_required=attendance_required,
        source_url=source_url,
        page_title=page_title,
        visible_headings=visible_headings,
        required_user_actions=required_user_actions,
        safe_next_actions=safe_next_actions,
        blocked_actions=blocked_actions,
        evidence_refs=evidence_refs,
        warnings=warnings,
    )


def normalize_attended_handoff_packet_dict(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Return a JSON-serializable normalized handoff packet."""

    return normalize_attended_handoff_packet(packet).to_dict()


def _reject_forbidden_material(value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.replace("_", "").replace("-", "").lower()
            if key_text in _BROWSER_ACTION_KEYS:
                raise HandoffPacketError(f"{path}.{key_text} would record browser actions")
            if any(fragment in normalized_key for fragment in _FORBIDDEN_KEY_FRAGMENTS):
                raise HandoffPacketError(f"{path}.{key_text} would record private session material")
            _reject_forbidden_material(child, f"{path}.{key_text}")
        return

    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_forbidden_material(child, f"{path}[{index}]")
        return

    if isinstance(value, str):
        lowered = value.lower()
        if "file://" in lowered or "/users/" in lowered or "/home/" in lowered:
            raise HandoffPacketError(f"{path} contains a local private path")


def _required_text(packet: Mapping[str, Any], key: str) -> str:
    value = packet.get(key)
    if not isinstance(value, str) or not value.strip():
        raise HandoffPacketError(f"{key} is required")
    return " ".join(value.split())


def _optional_text(packet: Mapping[str, Any], key: str) -> str:
    value = packet.get(key, "")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise HandoffPacketError(f"{key} must be text")
    return " ".join(value.split())


def _required_bool(packet: Mapping[str, Any], key: str) -> bool:
    value = packet.get(key)
    if not isinstance(value, bool):
        raise HandoffPacketError(f"{key} must be true or false")
    return value


def _text_tuple(value: Any, key: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise HandoffPacketError(f"{key} must be a list of strings")

    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise HandoffPacketError(f"{key} must contain only non-empty strings")
        text = " ".join(item.split())
        dedupe_key = text.casefold()
        if dedupe_key not in seen:
            normalized.append(text)
            seen.add(dedupe_key)
    return tuple(normalized)


def _normalize_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme != "https":
        raise HandoffPacketError("source_url must use https")
    if parsed.netloc.lower() not in _ALLOWED_HOSTS:
        raise HandoffPacketError("source_url host is not allowed for PP&D handoff validation")
    path = parsed.path or "/"
    return parsed._replace(netloc=parsed.netloc.lower(), path=path, params="", query="", fragment="").geturl()


def _reject_consequential_safe_actions(actions: tuple[str, ...]) -> None:
    for action in actions:
        lowered = action.lower()
        if any(word in lowered for word in _CONSEQUENTIAL_ACTION_WORDS):
            raise HandoffPacketError("safe_next_actions must not include consequential official actions")
