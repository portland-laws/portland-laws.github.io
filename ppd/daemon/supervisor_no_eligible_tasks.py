"""Validation helpers for PP&D daemon no-eligible-task supervisor states.

This module is deliberately fixture-only. It does not select live work, mutate the
task board, write daemon ledgers, or inspect runtime state. Its purpose is to
classify deterministic regression fixtures for supervisor scheduling failures.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


MODULE_STATUS = "validation_only_no_eligible_tasks_regression"
PROGRAMMING_ERROR_KIND = "supervisor_programming_error"
EXPECTED_ERROR = "no_eligible_tasks_after_parked_stale_retry_without_fixture_first_task"


class SupervisorFixtureError(ValueError):
    """Raised when a supervisor regression fixture is malformed."""


def classify_no_eligible_tasks_fixture(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Classify a deterministic no_eligible_tasks supervisor fixture.

    A reported no_eligible_tasks result is a supervisor programming error when
    every remaining task is only parked stale retry work and no newer
    fixture-first task was appended to replace it.
    """

    reported_result = _required_text(fixture, "reported_result")
    remaining_work = _required_sequence(fixture, "remaining_work")
    appended_tasks = _optional_sequence(fixture, "appended_tasks")

    if reported_result != "no_eligible_tasks":
        return {
            "classification": "not_applicable",
            "reason": "reported_result_is_not_no_eligible_tasks",
            "is_supervisor_programming_error": False,
        }

    if not remaining_work:
        return {
            "classification": "normal_backlog_exhaustion",
            "reason": "no_remaining_work_records",
            "is_supervisor_programming_error": False,
        }

    remaining_are_parked_stale_retries = all(
        _is_parked_stale_retry(item) for item in remaining_work
    )
    has_new_fixture_first_task = any(_is_new_fixture_first_task(item) for item in appended_tasks)

    if remaining_are_parked_stale_retries and not has_new_fixture_first_task:
        parked_task_ids = [_task_id(item) for item in remaining_work]
        return {
            "classification": PROGRAMMING_ERROR_KIND,
            "error": EXPECTED_ERROR,
            "is_supervisor_programming_error": True,
            "reported_result": reported_result,
            "parked_task_ids": parked_task_ids,
            "required_repair": "append_new_fixture_first_task_before_reporting_no_eligible_tasks",
        }

    return {
        "classification": "not_programming_error",
        "reason": "new_fixture_first_task_available_or_remaining_work_not_only_parked_stale_retry",
        "is_supervisor_programming_error": False,
    }


def assert_no_eligible_tasks_supervisor_error(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Return classification or raise when the regression expectation is not met."""

    result = classify_no_eligible_tasks_fixture(fixture)
    if result.get("classification") != PROGRAMMING_ERROR_KIND:
        raise AssertionError(
            "expected no_eligible_tasks with only parked stale retry work and no "
            "new fixture-first task to be classified as a supervisor programming error"
        )
    if result.get("error") != EXPECTED_ERROR:
        raise AssertionError("unexpected supervisor programming error code")
    return result


def _is_parked_stale_retry(item: Any) -> bool:
    if not isinstance(item, Mapping):
        return False
    return (
        item.get("checkbox_state") == "[ ]"
        and item.get("retry_state") == "parked_stale_retry"
        and item.get("selectable") is False
    )


def _is_new_fixture_first_task(item: Any) -> bool:
    if not isinstance(item, Mapping):
        return False
    return (
        item.get("checkbox_state") == "[ ]"
        and item.get("task_style") == "fixture_first"
        and item.get("selectable") is True
        and item.get("appended_after_stale_retry_parking") is True
    )


def _task_id(item: Any) -> str:
    if not isinstance(item, Mapping):
        return ""
    value = item.get("task_id", "")
    if not isinstance(value, str) or not value.strip():
        return ""
    return value


def _required_text(fixture: Mapping[str, Any], key: str) -> str:
    value = fixture.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SupervisorFixtureError(f"fixture field {key} must be a non-empty string")
    return value


def _required_sequence(fixture: Mapping[str, Any], key: str) -> Sequence[Any]:
    value = fixture.get(key)
    if not isinstance(value, list):
        raise SupervisorFixtureError(f"fixture field {key} must be a list")
    return value


def _optional_sequence(fixture: Mapping[str, Any], key: str) -> Sequence[Any]:
    value = fixture.get(key, [])
    if not isinstance(value, list):
        raise SupervisorFixtureError(f"fixture field {key} must be a list when present")
    return value
