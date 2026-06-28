"""Exact-confirmation checkpoint fixtures for consequential DevHub actions.

These helpers are intentionally fixture-backed and side-effect free. They describe
where an attended user confirmation is required; they do not execute browser,
upload, submission, scheduling, cancellation, reactivation, or payment actions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


EXPECTED_BOUNDARIES: tuple[str, ...] = (
    "acknowledgement_certification",
    "official_upload",
    "submission",
    "scheduling",
    "cancellation",
    "extension_reactivation",
    "payment",
)


@dataclass(frozen=True)
class ExactConfirmationCheckpoint:
    checkpoint_id: str
    boundary: str
    display_name: str
    consequence: str
    allowed_before_confirmation: tuple[str, ...]
    blocked_without_confirmation: tuple[str, ...]
    confirmation_prompt: str
    required_confirmation_text: str
    manual_handoff: bool
    prohibited_automation: tuple[str, ...]
    fixture_kind: str
    source_basis: tuple[str, ...]

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "ExactConfirmationCheckpoint":
        return cls(
            checkpoint_id=_require_text(value, "checkpoint_id"),
            boundary=_require_text(value, "boundary"),
            display_name=_require_text(value, "display_name"),
            consequence=_require_text(value, "consequence"),
            allowed_before_confirmation=tuple(_require_text_list(value, "allowed_before_confirmation")),
            blocked_without_confirmation=tuple(_require_text_list(value, "blocked_without_confirmation")),
            confirmation_prompt=_require_text(value, "confirmation_prompt"),
            required_confirmation_text=_require_text(value, "required_confirmation_text"),
            manual_handoff=_require_bool(value, "manual_handoff"),
            prohibited_automation=tuple(_require_text_list(value, "prohibited_automation")),
            fixture_kind=_require_text(value, "fixture_kind"),
            source_basis=tuple(_require_text_list(value, "source_basis")),
        )

    def blocks(self, action_name: str) -> bool:
        normalized = action_name.strip().lower().replace(" ", "_").replace("-", "_")
        return normalized in self.blocked_without_confirmation or normalized in self.prohibited_automation

    def accepts_confirmation(self, user_text: str) -> bool:
        return user_text == self.required_confirmation_text


def default_fixture_path() -> Path:
    return Path(__file__).parents[1] / "tests" / "fixtures" / "devhub" / "exact_confirmation_checkpoints.json"


def load_checkpoint_fixtures(path: Path | None = None) -> tuple[ExactConfirmationCheckpoint, ...]:
    fixture_path = path or default_fixture_path()
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    checkpoints = raw.get("checkpoints")
    if not isinstance(checkpoints, list):
        raise ValueError("exact confirmation fixture must contain a checkpoints list")
    loaded = tuple(ExactConfirmationCheckpoint.from_mapping(item) for item in checkpoints)
    validate_checkpoint_fixtures(loaded)
    return loaded


def validate_checkpoint_fixtures(checkpoints: Iterable[ExactConfirmationCheckpoint]) -> None:
    loaded = tuple(checkpoints)
    by_boundary = {checkpoint.boundary: checkpoint for checkpoint in loaded}
    missing = sorted(set(EXPECTED_BOUNDARIES) - set(by_boundary))
    extra = sorted(set(by_boundary) - set(EXPECTED_BOUNDARIES))
    if missing or extra:
        raise ValueError(f"unexpected checkpoint boundaries: missing={missing}, extra={extra}")

    ids = [checkpoint.checkpoint_id for checkpoint in loaded]
    if len(ids) != len(set(ids)):
        raise ValueError("checkpoint ids must be unique")

    for checkpoint in loaded:
        if checkpoint.fixture_kind != "exact_confirmation_checkpoint":
            raise ValueError(f"{checkpoint.checkpoint_id} has unsupported fixture kind")
        if not checkpoint.manual_handoff:
            raise ValueError(f"{checkpoint.checkpoint_id} must require manual handoff")
        if not checkpoint.required_confirmation_text.startswith("CONFIRM "):
            raise ValueError(f"{checkpoint.checkpoint_id} must use an exact CONFIRM phrase")
        if checkpoint.required_confirmation_text not in checkpoint.confirmation_prompt:
            raise ValueError(f"{checkpoint.checkpoint_id} prompt must show the exact confirmation text")
        if not checkpoint.blocked_without_confirmation:
            raise ValueError(f"{checkpoint.checkpoint_id} must block at least one action")
        if not checkpoint.prohibited_automation:
            raise ValueError(f"{checkpoint.checkpoint_id} must declare prohibited automation")
        if not checkpoint.source_basis:
            raise ValueError(f"{checkpoint.checkpoint_id} must include source basis")


def _require_text(value: dict[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return item


def _require_bool(value: dict[str, Any], key: str) -> bool:
    item = value.get(key)
    if not isinstance(item, bool):
        raise ValueError(f"{key} must be a boolean")
    return item


def _require_text_list(value: dict[str, Any], key: str) -> list[str]:
    item = value.get(key)
    if not isinstance(item, list) or not item:
        raise ValueError(f"{key} must be a non-empty list")
    if not all(isinstance(entry, str) and entry.strip() for entry in item):
        raise ValueError(f"{key} must contain only non-empty strings")
    return item
