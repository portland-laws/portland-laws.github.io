from __future__ import annotations

from ppd.daemon.task_selection_diagnostics import diagnose_task_selection


def test_diagnose_task_selection_reports_first_selectable_task() -> None:
    result = diagnose_task_selection(
        [
            {"id": "done-task", "status": "complete"},
            {"id": "retry-task", "retries": 3},
            {"id": "fixture-gated", "requires_live_crawl": True},
            {"id": "ready-task", "retries": 1},
        ]
    )

    assert result.as_dict() == {
        "selected_task_id": "ready-task",
        "reason": "selected first validation-passing task",
        "checked": 4,
        "skipped": [
            "done-task: already complete",
            "retry-task: retry limit reached (3/3)",
            "fixture-gated: live crawl gated until fixture validation passes",
        ],
    }


def test_diagnose_task_selection_keeps_retry_limit_bounded() -> None:
    result = diagnose_task_selection(
        [
            {"id": "bad-retry", "retries": "not-an-int"},
            {"id": "blocked-task", "blocked": True},
        ],
        retry_limit=2,
    )

    assert result.selected_task_id is None
    assert result.reason == "no validation-passing task candidates"
    assert result.checked == 2
    assert result.skipped == (
        "bad-retry: retry limit reached (3/2)",
        "blocked-task: blocked",
    )


def test_diagnose_task_selection_allows_fixture_validated_live_task() -> None:
    result = diagnose_task_selection(
        [
            {
                "task_id": "fixture-backed-task",
                "requires_live_crawl": True,
                "fixture_validated": True,
                "retry_count": 0,
            }
        ]
    )

    assert result.selected_task_id == "fixture-backed-task"
    assert result.skipped == ()
