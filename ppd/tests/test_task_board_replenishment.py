"""Validation for PP&D task-board replenishment with parked blocked work."""

from __future__ import annotations

from ppd.daemon.task_board_replenishment import (
    append_supervisor_tranche_when_only_blocked_remains,
)


NARROW_SUPERVISOR_TRANCHE = (
    "- [ ] Task checkbox-126: Add daemon selector diagnostics for boards with only parked blocked domain tasks.",
    "- [ ] Task checkbox-127: Add daemon prompt guidance that retries blocked domain tasks only after selector diagnostics pass.",
)


def test_replenishment_appends_supervisor_tranche_without_unparking_blocked_domain_task() -> None:
    board = "\n".join(
        [
            "# PP&D Daemon Task Board",
            "",
            "## Completed Work",
            "",
            "- [x] Task checkbox-01: Bootstrap the PP&D daemon task board and operations boundary.",
            "- [x] Task checkbox-81: Add daemon replenishment validation for a completed board.",
            "",
            "## Blocked Tasks",
            "",
            "- [ ] Task checkbox-108: Parked public crawl frontier checkpoint blocked after repeated parser failures.",
        ]
    )

    result = append_supervisor_tranche_when_only_blocked_remains(
        board,
        NARROW_SUPERVISOR_TRANCHE,
    )

    assert result.appended is True
    assert result.preserved_completed_count == 2
    assert result.parked_blocked_count == 1
    assert "- [x] Task checkbox-01: Bootstrap the PP&D daemon task board and operations boundary." in result.board_text
    assert "- [x] Task checkbox-81: Add daemon replenishment validation for a completed board." in result.board_text
    assert "## Blocked Tasks" in result.board_text
    assert "- [ ] Task checkbox-108: Parked public crawl frontier checkpoint blocked after repeated parser failures." in result.board_text
    assert "## Supervisor Replenishment" in result.board_text
    for task_line in NARROW_SUPERVISOR_TRANCHE:
        assert task_line in result.board_text


def test_replenishment_does_not_append_when_selectable_task_exists() -> None:
    board = "\n".join(
        [
            "# PP&D Daemon Task Board",
            "",
            "## Pending Work",
            "",
            "- [ ] Task checkbox-124: Existing selectable supervisor task.",
            "",
            "## Blocked Tasks",
            "",
            "- [ ] Task checkbox-108: Parked public crawl frontier checkpoint blocked after repeated parser failures.",
        ]
    )

    result = append_supervisor_tranche_when_only_blocked_remains(
        board,
        NARROW_SUPERVISOR_TRANCHE,
    )

    assert result.appended is False
    assert result.board_text == board
    assert "## Supervisor Replenishment" not in result.board_text
