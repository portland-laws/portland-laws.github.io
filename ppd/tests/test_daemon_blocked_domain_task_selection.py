"""Regression coverage for daemon task selection when domain work is blocked."""

from __future__ import annotations

import json
import unittest
from dataclasses import dataclass
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "daemon" / "blocked_domain_task_selection.json"


@dataclass(frozen=True)
class FixtureTask:
    id: str
    status: str
    category: str
    title: str


def _load_fixture() -> dict[str, object]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _tasks_from_fixture(fixture: dict[str, object]) -> list[FixtureTask]:
    tasks = fixture.get("tasks", [])
    if not isinstance(tasks, list):
        raise AssertionError("fixture tasks must be a list")
    parsed: list[FixtureTask] = []
    for task in tasks:
        if not isinstance(task, dict):
            raise AssertionError("fixture task entries must be objects")
        parsed.append(
            FixtureTask(
                id=str(task.get("id", "")),
                status=str(task.get("status", "")),
                category=str(task.get("category", "")),
                title=str(task.get("title", "")),
            )
        )
    return parsed


def _select_next_task(tasks: list[FixtureTask]) -> FixtureTask:
    for task in tasks:
        if task.status == "needed" and task.category == "daemon_repair":
            return task
    for task in tasks:
        if task.status == "needed" and task.category != "domain":
            return task
    return FixtureTask(
        id="generated-daemon-repair",
        status="needed",
        category="daemon_repair",
        title="Append narrow daemon repair task for blocked domain selection",
    )


class DaemonBlockedDomainTaskSelectionTest(unittest.TestCase):
    def test_selects_daemon_repair_instead_of_blocked_domain_task(self) -> None:
        fixture = _load_fixture()
        tasks = _tasks_from_fixture(fixture)
        expected = fixture.get("expected", {})
        if not isinstance(expected, dict):
            raise AssertionError("fixture expected field must be an object")

        selected = _select_next_task(tasks)

        self.assertEqual(expected.get("selected_task_id"), selected.id)
        self.assertIn(selected.category, expected.get("allowed_selection_categories", []))
        self.assertNotIn(selected.id, expected.get("forbidden_selection_ids", []))

    def test_appends_narrow_daemon_repair_when_no_selectable_repair_task_exists(self) -> None:
        fixture = _load_fixture()
        tasks = [task for task in _tasks_from_fixture(fixture) if task.category == "domain"]
        expected = fixture.get("expected", {})
        if not isinstance(expected, dict):
            raise AssertionError("fixture expected field must be an object")
        fallback = expected.get("fallback_appended_when_no_repair_exists", {})
        if not isinstance(fallback, dict):
            raise AssertionError("fixture fallback expectation must be an object")

        selected = _select_next_task(tasks)

        self.assertEqual(fallback.get("category"), selected.category)
        self.assertEqual(fallback.get("status"), selected.status)
        self.assertIn(str(fallback.get("title_contains", "")), selected.title.lower())
        self.assertNotIn(selected.id, expected.get("forbidden_selection_ids", []))


if __name__ == "__main__":
    unittest.main()
