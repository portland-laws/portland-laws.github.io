from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


class SelectorConfidenceError(RuntimeError):
    """Raised when draft-fill selector evidence is not specific enough."""

    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("; ".join(self.problems))


@dataclass(frozen=True)
class SelectorConfidenceResult:
    allowed: bool
    problems: tuple[str, ...]
    labels: tuple[str, ...]
    headings: tuple[str, ...]
    routes: tuple[str, ...]


def check_draft_fill_selector_confidence(surface_map: dict[str, Any]) -> SelectorConfidenceResult:
    """Validate that a synthetic surface map is specific enough for draft-fill.

    The check is intentionally conservative. Draft-fill actions should only run
    when labels, headings, and route evidence are present and unambiguous.
    """

    labels = _evidence_values(surface_map, ("labels", "label_evidence"))
    headings = _evidence_values(surface_map, ("headings", "heading_evidence"))
    routes = _evidence_values(surface_map, ("routes", "route_evidence"))

    problems: list[str] = []
    _require_unique_evidence("label", labels, problems)
    _require_unique_evidence("heading", headings, problems)
    _require_unique_evidence("route", routes, problems)

    return SelectorConfidenceResult(
        allowed=not problems,
        problems=tuple(problems),
        labels=labels,
        headings=headings,
        routes=routes,
    )


def assert_draft_fill_selector_confidence(surface_map: dict[str, Any]) -> SelectorConfidenceResult:
    result = check_draft_fill_selector_confidence(surface_map)
    if not result.allowed:
        raise SelectorConfidenceError(result.problems)
    return result


def _require_unique_evidence(kind: str, values: tuple[str, ...], problems: list[str]) -> None:
    if not values:
        problems.append(f"missing {kind} evidence")
        return

    duplicates = _duplicates(values)
    if duplicates:
        problems.append(f"ambiguous {kind} evidence: {', '.join(duplicates)}")


def _evidence_values(surface_map: dict[str, Any], keys: tuple[str, ...]) -> tuple[str, ...]:
    values: list[str] = []
    for key in keys:
        raw = surface_map.get(key)
        if raw is None:
            continue
        values.extend(_flatten_evidence(raw))
    return tuple(value for value in (_normalize(value) for value in values) if value)


def _flatten_evidence(raw: Any) -> list[str]:
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, dict):
        values: list[str] = []
        for key in ("text", "label", "name", "title", "heading", "path", "href", "route"):
            value = raw.get(key)
            if isinstance(value, str):
                values.append(value)
        return values
    if isinstance(raw, list) or isinstance(raw, tuple):
        values = []
        for item in raw:
            values.extend(_flatten_evidence(item))
        return values
    return []


def _normalize(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _duplicates(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicated: list[str] = []
    for value in values:
        if value in seen and value not in duplicated:
            duplicated.append(value)
        seen.add(value)
    return tuple(duplicated)
