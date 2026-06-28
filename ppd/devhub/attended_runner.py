"""Attended Playwright DevHub runner guardrails.

This module intentionally keeps live browser automation behind an explicit page
object supplied by the caller. It provides deterministic replay and safety
checks that can be tested without DevHub credentials, browser state, traces, or
network access.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

GUARDED_TRANSITIONS = frozenset(
    {
        "upload",
        "submit",
        "certify",
        "certification",
        "cancel",
        "cancellation",
        "inspection",
        "security",
        "payment",
    }
)


class DevHubSafetyError(RuntimeError):
    """Raised when an attended safety rule would be violated."""


@dataclass(frozen=True)
class JournalEvent:
    """A normalized journal event for deterministic replay."""

    action: str
    selector: str | None = None
    value: str | None = None
    transition: str | None = None
    pause_token: str | None = None
    note: str | None = None

    @classmethod
    def from_mapping(cls, item: Mapping[str, Any]) -> "JournalEvent":
        action = str(item.get("action", "")).strip().lower()
        if not action:
            raise ValueError("journal event is missing action")
        selector = item.get("selector")
        value = item.get("value")
        transition = item.get("transition")
        pause_token = item.get("pause_token")
        note = item.get("note")
        return cls(
            action=action,
            selector=str(selector) if selector is not None else None,
            value=str(value) if value is not None else None,
            transition=str(transition).strip().lower() if transition is not None else None,
            pause_token=str(pause_token) if pause_token is not None else None,
            note=str(note) if note is not None else None,
        )

    def to_mapping(self) -> dict[str, str]:
        data: dict[str, str] = {"action": self.action}
        if self.selector is not None:
            data["selector"] = self.selector
        if self.value is not None:
            data["value"] = self.value
        if self.transition is not None:
            data["transition"] = self.transition
        if self.pause_token is not None:
            data["pause_token"] = self.pause_token
        if self.note is not None:
            data["note"] = self.note
        return data


@dataclass(frozen=True)
class DraftFill:
    """A reversible draft field fill derived from a redacted fact."""

    selector: str
    value: str
    fact_key: str

    def apply_event(self) -> JournalEvent:
        return JournalEvent(
            action="fill",
            selector=self.selector,
            value=self.value,
            note=f"redacted_fact:{self.fact_key}",
        )

    def undo_event(self) -> JournalEvent:
        return JournalEvent(
            action="fill",
            selector=self.selector,
            value="",
            note=f"undo_redacted_fact:{self.fact_key}",
        )


class AttendedDevHubRunner:
    """Small attended runner wrapper for DevHub Playwright pages.

    The caller is responsible for creating and closing the Playwright browser
    context. This class never stores auth state or traces.
    """

    def __init__(self, page: Any | None = None, *, dry_run: bool = True) -> None:
        self.page = page
        self.dry_run = dry_run
        self.events: list[JournalEvent] = []

    def require_manual_login_handoff(self, *, confirmed: bool) -> JournalEvent:
        if not confirmed:
            raise DevHubSafetyError("manual DevHub login handoff must be confirmed before replay")
        event = JournalEvent(action="manual_login_handoff", note="confirmed")
        self.events.append(event)
        return event

    def require_pause(self, transition: str, *, pause_token: str | None) -> JournalEvent:
        normalized = transition.strip().lower()
        if normalized in GUARDED_TRANSITIONS and not pause_token:
            raise DevHubSafetyError(f"mandatory attended pause required before {normalized}")
        event = JournalEvent(action="pause", transition=normalized, pause_token=pause_token)
        self.events.append(event)
        return event

    def plan_draft_fills(self, redacted_facts: Mapping[str, str], field_map: Mapping[str, str]) -> list[DraftFill]:
        fills: list[DraftFill] = []
        for fact_key in sorted(field_map):
            if fact_key not in redacted_facts:
                continue
            selector = field_map[fact_key]
            value = redacted_facts[fact_key]
            fills.append(DraftFill(selector=selector, value=value, fact_key=fact_key))
        return fills

    def reversible_events_for_fills(self, fills: Sequence[DraftFill]) -> list[JournalEvent]:
        events: list[JournalEvent] = []
        for fill in fills:
            events.append(fill.apply_event())
        for fill in reversed(fills):
            events.append(fill.undo_event())
        return events

    async def replay(self, journal: Iterable[JournalEvent | Mapping[str, Any]]) -> list[JournalEvent]:
        applied: list[JournalEvent] = []
        for raw_event in journal:
            event = raw_event if isinstance(raw_event, JournalEvent) else JournalEvent.from_mapping(raw_event)
            if event.action in GUARDED_TRANSITIONS:
                self.require_pause(event.action, pause_token=event.pause_token)
            elif event.transition in GUARDED_TRANSITIONS:
                self.require_pause(event.transition, pause_token=event.pause_token)
            await self._apply(event)
            self.events.append(event)
            applied.append(event)
        return applied

    async def _apply(self, event: JournalEvent) -> None:
        if self.dry_run:
            return
        if self.page is None:
            raise DevHubSafetyError("a Playwright page is required when dry_run is false")
        if event.action == "fill":
            if not event.selector:
                raise ValueError("fill event requires selector")
            await self.page.fill(event.selector, event.value or "")
            return
        if event.action == "click":
            if not event.selector:
                raise ValueError("click event requires selector")
            await self.page.click(event.selector)
            return
        if event.action in {"pause", "manual_login_handoff", "note"}:
            return
        raise DevHubSafetyError(f"unsupported attended replay action: {event.action}")


def load_jsonl_journal(path: Path) -> list[JournalEvent]:
    events: list[JournalEvent] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON journal line {line_number}: {exc.msg}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"journal line {line_number} must be an object")
        events.append(JournalEvent.from_mapping(payload))
    return events


def dump_jsonl_journal(events: Iterable[JournalEvent], path: Path) -> None:
    lines = [json.dumps(event.to_mapping(), sort_keys=True) for event in events]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
