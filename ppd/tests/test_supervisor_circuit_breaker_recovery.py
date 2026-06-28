from datetime import datetime, timezone

from ppd.supervisor_circuit_breaker_recovery import (
    SupervisorTask,
    TerminationStorm,
    build_expired_storm_recovery_plan,
)


def test_expired_termination_storm_appends_vetted_non_generated_recovery_tasks():
    storm = TerminationStorm(
        storm_id="storm-446",
        terminated_task_ids=("crawl-devhub", "normalize-forms"),
        expires_at=datetime(2026, 5, 8, 10, 0, tzinfo=timezone.utc),
    )
    tasks = (
        SupervisorTask(
            task_id="generated-cascade-1",
            title="Generated blocked cascade follow-up",
            state="blocked",
            generated=True,
            reason="blocked-cascade",
        ),
        SupervisorTask(
            task_id="manual-review-open",
            title="Manual review",
            state="open",
            generated=False,
        ),
    )

    plan = build_expired_storm_recovery_plan(
        storm=storm,
        tasks=tasks,
        now=datetime(2026, 5, 8, 10, 1, tzinfo=timezone.utc),
    )

    assert plan.restart_supervisor is True
    assert [task.generated for task in plan.appended_tasks] == [False, False]
    assert [task.vetted for task in plan.appended_tasks] == [True, True]
    assert [task.reopens_blocked_cascade for task in plan.appended_tasks] == [False, False]
    assert plan.preserved_blocked_generated_task_ids == ("generated-cascade-1",)


def test_unexpired_termination_storm_does_not_restart_or_append_recovery_tasks():
    storm = TerminationStorm(
        storm_id="storm-446",
        terminated_task_ids=("crawl-devhub",),
        expires_at=datetime(2026, 5, 8, 10, 0, tzinfo=timezone.utc),
    )

    plan = build_expired_storm_recovery_plan(
        storm=storm,
        tasks=(
            SupervisorTask(
                task_id="generated-cascade-1",
                title="Generated blocked cascade follow-up",
                state="blocked",
                generated=True,
                reason="blocked-cascade",
            ),
        ),
        now=datetime(2026, 5, 8, 9, 59, tzinfo=timezone.utc),
    )

    assert plan.restart_supervisor is False
    assert plan.appended_tasks == ()
    assert plan.preserved_blocked_generated_task_ids == ("generated-cascade-1",)
