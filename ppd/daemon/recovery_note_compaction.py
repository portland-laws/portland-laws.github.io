"""Bound repeated supervisor repair notes before prompt construction."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable


SUPERVISOR_REPAIR_NOTE_HEADINGS = frozenset(
    {
        "## Built-In Supervisor Repair Notes",
        "## Built-In Generated Blocked-Cascade Quarantine Notes",
        "## Built-In Supervisor Planning Notes",
    }
)


@dataclass(frozen=True)
class RecoveryNoteSummary:
    total_notes: int
    unique_notes: int
    summary: str

    def to_prompt_text(self) -> str:
        if self.total_notes == 0:
            return "Supervisor repair notes summarized: total=0 unique=0. No supervisor repair notes found."
        return (
            f"Supervisor repair notes summarized: total={self.total_notes} "
            f"unique={self.unique_notes}. {self.summary}"
        )


def _normalize_note(note: str) -> str:
    return " ".join(str(note).split())


def extract_repair_notes(markdown: str) -> tuple[str, ...]:
    """Return list items from supervisor repair-note sections only."""

    notes: list[str] = []
    in_repair_notes = False
    for raw_line in str(markdown).splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            in_repair_notes = line in SUPERVISOR_REPAIR_NOTE_HEADINGS
            continue
        if in_repair_notes and line.startswith("- "):
            normalized = _normalize_note(line[2:])
            if normalized:
                notes.append(normalized)
    return tuple(notes)


def summarize_recovery_notes(
    notes: Iterable[str],
    *,
    max_items: int = 3,
    max_chars: int = 700,
) -> RecoveryNoteSummary:
    """Summarize repeated notes deterministically for compact prompt context."""

    note_list = tuple(_normalize_note(note) for note in notes if _normalize_note(note))
    unique: list[str] = []
    seen: set[str] = set()
    for note in note_list:
        digest = sha256(note.encode("utf-8")).hexdigest()[:10]
        if digest in seen:
            continue
        seen.add(digest)
        unique.append(note)

    selected = unique[: max(0, max_items)]
    summary = " | ".join(selected)
    omitted = len(unique) - len(selected)
    if omitted > 0:
        summary = (summary + " " if summary else "") + f"{omitted} additional unique note(s) omitted."
    if not summary:
        summary = "No supervisor repair notes found."
    if max_chars > 3 and len(summary) > max_chars:
        summary = summary[: max_chars - 3].rstrip() + "..."
    return RecoveryNoteSummary(total_notes=len(note_list), unique_notes=len(unique), summary=summary)


def compact_task_board_repair_notes(
    markdown: str,
    *,
    max_items: int = 3,
    max_chars: int = 700,
) -> str:
    return summarize_recovery_notes(
        extract_repair_notes(markdown),
        max_items=max_items,
        max_chars=max_chars,
    ).to_prompt_text()
