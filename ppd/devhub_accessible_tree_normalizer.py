"""Synthetic DevHub accessible-tree normalizer.

This module accepts only small, redacted accessibility-tree fixtures and returns
DevHubSurfaceMap-style candidate dictionaries. It intentionally rejects browser
artifacts, private values, and transactional actions before normalization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


FORBIDDEN_KEYS = {
    "auth",
    "auth_state",
    "authorization",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "download",
    "file",
    "har",
    "password",
    "payment",
    "private",
    "raw_crawl_output",
    "screenshot",
    "session",
    "storage_state",
    "submission",
    "trace",
    "upload",
}

FORBIDDEN_VALUE_MARKERS = {
    "auth state",
    "captcha",
    "certification",
    "cookie",
    "credential",
    "credit card",
    "download document",
    "har",
    "mfa",
    "password",
    "payment",
    "private value",
    "raw crawl",
    "schedule inspection",
    "screenshot",
    "session token",
    "submit application",
    "trace.zip",
    "upload file",
}

FORBIDDEN_ACTIONS = {
    "cancel",
    "certify",
    "checkout",
    "create_account",
    "login",
    "pay",
    "schedule",
    "submit",
    "upload",
}

SAFE_ROLES = {"button", "heading", "link", "menuitem", "tab", "textbox"}


class UnsafeDevHubFixtureError(ValueError):
    """Raised when a fixture contains data this normalizer must not handle."""


@dataclass(frozen=True)
class DevHubSurfaceCandidate:
    surface_id: str
    route: str
    role: str
    name: str
    heading: str | None = None
    validation_message: str | None = None

    def to_dict(self) -> dict[str, str]:
        item = {
            "surface_id": self.surface_id,
            "route": self.route,
            "role": self.role,
            "name": self.name,
        }
        if self.heading:
            item["heading"] = self.heading
        if self.validation_message:
            item["validation_message"] = self.validation_message
        return item


def normalize_devhub_accessible_tree(fixture: Mapping[str, Any]) -> list[dict[str, str]]:
    """Return deterministic DevHubSurfaceMap candidate dictionaries.

    The input must be a synthetic, redacted mapping with a ``nodes`` list. Each
    node may include ``role``, ``name``, ``heading``, ``route``, and
    ``validation_message``. Unsafe browser artifacts or transactional actions
    are rejected before any candidates are produced.
    """

    _reject_unsafe_fixture(fixture)
    nodes = fixture.get("nodes", [])
    if not isinstance(nodes, list):
        raise TypeError("fixture.nodes must be a list")

    candidates: list[DevHubSurfaceCandidate] = []
    seen: set[tuple[str, str, str]] = set()

    for raw_node in nodes:
        if not isinstance(raw_node, Mapping):
            raise TypeError("each accessible-tree node must be a mapping")

        role = _clean_text(raw_node.get("role", "")).lower()
        name = _clean_text(raw_node.get("name", ""))
        route = _clean_route(raw_node.get("route", fixture.get("route", "/devhub")))
        heading = _optional_clean_text(raw_node.get("heading"))
        validation_message = _optional_clean_text(raw_node.get("validation_message"))

        if role not in SAFE_ROLES or not name:
            continue

        dedupe_key = (route, role, name.casefold())
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        candidates.append(
            DevHubSurfaceCandidate(
                surface_id=_surface_id(route, role, name),
                route=route,
                role=role,
                name=name,
                heading=heading,
                validation_message=validation_message,
            )
        )

    candidates.sort(key=lambda item: (item.route, item.role, item.name.casefold()))
    return [item.to_dict() for item in candidates]


def _reject_unsafe_fixture(value: Any) -> None:
    for key, item in _walk(value):
        lowered_key = key.casefold() if key is not None else ""
        if lowered_key in FORBIDDEN_KEYS:
            raise UnsafeDevHubFixtureError(f"forbidden fixture key: {key}")

        if lowered_key == "action" and isinstance(item, str):
            action = item.strip().casefold().replace("-", "_").replace(" ", "_")
            if action in FORBIDDEN_ACTIONS:
                raise UnsafeDevHubFixtureError(f"forbidden action: {item}")

        if isinstance(item, str):
            lowered_value = item.casefold()
            for marker in FORBIDDEN_VALUE_MARKERS:
                if marker in lowered_value:
                    raise UnsafeDevHubFixtureError(f"forbidden fixture value: {marker}")


def _walk(value: Any, key: str | None = None) -> Iterable[tuple[str | None, Any]]:
    yield key, value
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            yield from _walk(child_value, str(child_key))
    elif isinstance(value, list):
        for child_value in value:
            yield from _walk(child_value, None)


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise TypeError("accessible-tree text values must be strings")
    return " ".join(value.split())


def _optional_clean_text(value: Any) -> str | None:
    cleaned = _clean_text(value)
    return cleaned or None


def _clean_route(value: Any) -> str:
    route = _clean_text(value) or "/devhub"
    if not route.startswith("/"):
        route = "/" + route
    return route


def _surface_id(route: str, role: str, name: str) -> str:
    raw = f"{route}-{role}-{name}".casefold()
    chars: list[str] = []
    previous_dash = False
    for char in raw:
        if char.isalnum():
            chars.append(char)
            previous_dash = False
        elif not previous_dash:
            chars.append("-")
            previous_dash = True
    return "devhub-" + "".join(chars).strip("-")
