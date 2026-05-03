"""Bound repeated supervisor repair notes before prompt construction."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable


@dataclass(frozen=True)
class RecoveryNoteSummary:
    total_notes: int
    unique_notes: int
    summary: str

    def to_prompt_text(self) -> str:
        return (
            f"Supervisor repair notes summarized: total={self.total_notes} "
            f"unique={self.unique_notes}. {self.summary}"
        )


def extract_repair_notes(markdown: str) -> tuple[str, ...]:
    notes: list[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line.startswith("- ") and (
            "repair" in line.lower()
            or "parked" in line.lower()
            or "blocked-cascade" in line.lower()
        ):
            notes.append(" ".join(line.removeprefix("- ").split()))
    return tuple(notes)


def summarize_recovery_notes(notes: Iterable[str], *, max_items: int = 3, max_chars: int = 700) -> RecoveryNoteSummary:
    note_list = tuple(str(note) for note in notes if str(note).strip())
    unique: list[str] = []
    seen: set[str] = set()
    for note in note_list:
        normalized = " ".join(note.split())
        digest = sha256(normalized.encode("utf-8")).hexdigest()[:10]
        if digest in seen:
            continue
        seen.add(digest)
        unique.append(normalized)

    selected = unique[:max_items]
    suffix = ""
    if len(unique) > len(selected):
        suffix = f" {len(unique) - len(selected)} additional unique note(s) omitted."
    summary = " | ".join(selected) + suffix
    if len(summary) > max_chars:
        summary = summary[: max_chars - 3].rstrip() + "..."
    return RecoveryNoteSummary(total_notes=len(note_list), unique_notes=len(unique), summary=summary)


def compact_task_board_repair_notes(markdown: str, *, max_items: int = 3, max_chars: int = 700) -> str:
    return summarize_recovery_notes(
        extract_repair_notes(markdown),
        max_items=max_items,
        max_chars=max_chars,
    ).to_prompt_text()
