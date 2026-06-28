from __future__ import annotations

from ppd.daemon.circuit_breaker_resume import (
    SELECTED_VETTED_RECOVERY,
    SKIPPED_GENERATED_CASCADE,
    ResumeTask,
    select_circuit_breaker_resume_task,
)


def test_blocked_generated_cascade_tasks_stay_skipped_while_recovery_selected_first() -> None:
    tasks = [
        ResumeTask(
            task_id="generated-cascade-1",
            generated=True,
            cascade=True,
        ),
        ResumeTask(
            task_id="generated-cascade-2",
            generated=True,
            cascade=True,
        ),
        ResumeTask(
            task_id="fresh-vetted-recovery",
            vetted_recovery=True,
        ),
        ResumeTask(task_id="ordinary-followup"),
    ]

    decision = select_circuit_breaker_resume_task(tasks)

    assert decision.selected_task_id == "fresh-vetted-recovery"
    assert decision.reason == SELECTED_VETTED_RECOVERY
    assert decision.skipped_task_ids == (
        "generated-cascade-1",
        "generated-cascade-2",
    )


def test_blocked_or_completed_tasks_are_not_selected_during_resume() -> None:
    tasks = [
        ResumeTask(
            task_id="generated-cascade",
            generated=True,
            cascade=True,
        ),
        ResumeTask(
            task_id="blocked-vetted-recovery",
            vetted_recovery=True,
            blocked=True,
        ),
        ResumeTask(
            task_id="completed-vetted-recovery",
            status="completed",
            vetted_recovery=True,
        ),
        ResumeTask(task_id="ordinary-pending"),
    ]

    decision = select_circuit_breaker_resume_task(tasks)

    assert decision.selected_task_id == "ordinary-pending"
    assert decision.reason == "selected_ordinary_pending_after_circuit_breaker"
    assert decision.skipped_task_ids == ("generated-cascade",)


def test_resume_reports_only_skipped_generated_cascade_when_no_recovery_exists() -> None:
    tasks = [
        ResumeTask(
            task_id="generated-cascade-1",
            generated=True,
            cascade=True,
        ),
        ResumeTask(
            task_id="generated-cascade-2",
            generated=True,
            cascade=True,
        ),
    ]

    decision = select_circuit_breaker_resume_task(tasks)

    assert decision.selected_task_id is None
    assert decision.reason == SKIPPED_GENERATED_CASCADE
    assert decision.skipped_task_ids == (
        "generated-cascade-1",
        "generated-cascade-2",
    )
