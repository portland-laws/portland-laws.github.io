"""Fixture-only DevHub surface recorder utilities.

This module intentionally records deterministic, redacted UI structure from static
HTML fixtures. It does not drive a browser, authenticate, download documents, or
invoke DevHub actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Iterable


READ_ONLY = "read_only"
CONSEQUENTIAL = "consequential"
FINANCIAL = "financial"
UNKNOWN = "unknown"

_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_LANDMARK_TAG_ROLES = {
    "main": "main",
    "nav": "navigation",
    "aside": "complementary",
    "header": "banner",
    "footer": "contentinfo",
    "form": "form",
}
_ACTION_TAGS = {"button", "a", "input"}
_FINANCIAL_TERMS = ("pay", "payment", "fee", "checkout", "card", "receipt")
_CONSEQUENTIAL_TERMS = (
    "upload",
    "submit",
    "certify",
    "schedule",
    "cancel",
    "withdraw",
    "purchase",
    "reactivate",
    "extension",
)
_READ_ONLY_TERMS = ("view", "review", "download", "print", "open", "details")


@dataclass(frozen=True)
class RecordedAction:
    """A redacted action-like control discovered in fixture HTML."""

    label: str
    role: str
    classification: str
    reason: str


@dataclass(frozen=True)
class SurfaceRecording:
    """Redacted structure captured from a static DevHub page fixture."""

    surface_id: str
    headings: tuple[str, ...]
    roles: tuple[str, ...]
    validation_messages: tuple[str, ...]
    attachment_labels: tuple[str, ...]
    status_labels: tuple[str, ...]
    actions: tuple[RecordedAction, ...]

    def actions_by_label(self) -> dict[str, RecordedAction]:
        return {action.label: action for action in self.actions}


@dataclass
class _Node:
    tag: str
    attrs: dict[str, str]
    text_parts: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(" ".join(self.text_parts).split())


class _FixtureRecorderParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.surface_id = "devhub-fixture-surface"
        self._stack: list[_Node] = []
        self.headings: list[str] = []
        self.roles: list[str] = []
        self.validation_messages: list[str] = []
        self.attachment_labels: list[str] = []
        self.status_labels: list[str] = []
        self.actions: list[RecordedAction] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name: value or "" for name, value in attrs}
        if "data-surface-id" in attr_map:
            self.surface_id = _redacted_text(attr_map["data-surface-id"], attr_map)
        self._record_role(tag, attr_map)
        self._stack.append(_Node(tag=tag, attrs=attr_map))

    def handle_data(self, data: str) -> None:
        if self._stack:
            self._stack[-1].text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self._stack:
            return
        node = self._pop_matching_node(tag)
        if node is None:
            return
        if self._stack and node.text:
            self._stack[-1].text_parts.append(node.text)
        self._record_closed_node(node)

    def _pop_matching_node(self, tag: str) -> _Node | None:
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index].tag == tag:
                node = self._stack.pop(index)
                trailing = self._stack[index:]
                del self._stack[index:]
                for child in trailing:
                    if child.text:
                        node.text_parts.append(child.text)
                return node
        return None

    def _record_role(self, tag: str, attrs: dict[str, str]) -> None:
        role = attrs.get("role") or _LANDMARK_TAG_ROLES.get(tag)
        if role:
            self.roles.append(role)

    def _record_closed_node(self, node: _Node) -> None:
        text = _redacted_text(node.text, node.attrs)
        if not text:
            return
        if node.tag in _HEADING_TAGS:
            self.headings.append(text)
        if _is_validation_node(node):
            self.validation_messages.append(text)
        if "data-attachment-label" in node.attrs:
            self.attachment_labels.append(_redacted_text(node.attrs["data-attachment-label"], node.attrs))
        if "data-status-label" in node.attrs:
            self.status_labels.append(_redacted_text(node.attrs["data-status-label"], node.attrs))
        if node.tag in _ACTION_TAGS and _is_action_node(node):
            label = _action_label(node)
            classification, reason = classify_action(label, node.attrs)
            self.actions.append(
                RecordedAction(
                    label=label,
                    role=node.attrs.get("role") or _default_action_role(node),
                    classification=classification,
                    reason=reason,
                )
            )


def record_devhub_fixture_surface(html: str) -> SurfaceRecording:
    """Record redacted structure from deterministic DevHub fixture HTML."""

    parser = _FixtureRecorderParser()
    parser.feed(html)
    parser.close()
    return SurfaceRecording(
        surface_id=parser.surface_id,
        headings=tuple(_dedupe(parser.headings)),
        roles=tuple(_dedupe(parser.roles)),
        validation_messages=tuple(_dedupe(parser.validation_messages)),
        attachment_labels=tuple(_dedupe(parser.attachment_labels)),
        status_labels=tuple(_dedupe(parser.status_labels)),
        actions=tuple(parser.actions),
    )


def classify_action(label: str, attrs: dict[str, str] | None = None) -> tuple[str, str]:
    """Classify a fixture action without triggering the action."""

    attrs = attrs or {}
    declared = attrs.get("data-action-classification")
    if declared in {READ_ONLY, CONSEQUENTIAL, FINANCIAL, UNKNOWN}:
        return declared, "declared fixture classification"

    haystack = " ".join(
        part.lower()
        for part in (
            label,
            attrs.get("id", ""),
            attrs.get("name", ""),
            attrs.get("type", ""),
            attrs.get("data-action", ""),
            attrs.get("href", ""),
        )
    )
    if any(term in haystack for term in _FINANCIAL_TERMS):
        return FINANCIAL, "payment or fee workflow"
    if any(term in haystack for term in _CONSEQUENTIAL_TERMS):
        return CONSEQUENTIAL, "official DevHub state-changing workflow"
    if any(term in haystack for term in _READ_ONLY_TERMS):
        return READ_ONLY, "read-only review workflow"
    return UNKNOWN, "no deterministic fixture rule matched"


def _redacted_text(text: str, attrs: dict[str, str]) -> str:
    if attrs.get("data-redact") in {"true", "1", "yes"}:
        replacement = attrs.get("data-redacted-label", "[REDACTED]")
        return " ".join(replacement.split())
    return " ".join(text.split())


def _is_validation_node(node: _Node) -> bool:
    return (
        node.attrs.get("data-validation-message") in {"true", "1", "yes"}
        or node.attrs.get("role") == "alert"
        or node.attrs.get("aria-live") in {"polite", "assertive"}
    )


def _is_action_node(node: _Node) -> bool:
    if node.tag == "button":
        return True
    if node.tag == "a":
        return bool(node.attrs.get("href") or node.attrs.get("role") == "button")
    if node.tag == "input":
        return node.attrs.get("type") in {"button", "submit", "file"}
    return False


def _action_label(node: _Node) -> str:
    for attr_name in ("aria-label", "value", "title", "data-action-label"):
        value = node.attrs.get(attr_name)
        if value:
            return _redacted_text(value, node.attrs)
    return _redacted_text(node.text, node.attrs)


def _default_action_role(node: _Node) -> str:
    if node.tag == "a":
        return "link"
    return "button"


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result
