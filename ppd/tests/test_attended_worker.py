from __future__ import annotations

import unittest
from dataclasses import replace

from ppd.devhub.attended_worker import (
    AttendedUserCheckpoint,
    AttendedWorkerEventKind,
    AttendedWorkerResumeAction,
    AttendedWorkerStatus,
    AttendedWorkerStep,
    WorkerHardeningReview,
    attempt_attended_step,
    complete_attended_step,
    journal_attended_decision,
    prepare_attended_step,
    record_action_result,
    resume_attended_worker_journal,
    validate_attended_worker_journal,
)
from ppd.devhub.live_action_executor import (
    LiveDevHubActionKind,
    LiveDevHubActionRequest,
    build_required_confirmation_phrase,
)


class FakePage:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, object]] = []

    def fill(self, selector: str, value: str) -> None:
        self.calls.append(("fill", selector, value))

    def click(self, selector: str) -> None:
        self.calls.append(("click", selector, None))

    def set_input_files(self, selector: str, files: str | list[str]) -> None:
        self.calls.append(("set_input_files", selector, files))


def attended_checkpoint(confirmation: str = "") -> AttendedUserCheckpoint:
    return AttendedUserCheckpoint(
        user_present=True,
        reviewed_current_screen=True,
        understands_next_action=True,
        operator_label="attended-test",
        exact_confirmation_phrase=confirmation,
    )


def hardened_preflight(confidence: float = 0.90) -> WorkerHardeningReview:
    return WorkerHardeningReview(
        source_evidence_ids=("ppd-source:devhub-guide",),
        selector_basis="accessible label project address",
        selector_confidence=confidence,
        audit_event_id="audit:test-step",
        rollback_plan="clear the draft field or return to the previous saved draft",
        preview_or_dry_run_completed=True,
        no_private_artifacts_persisted=True,
    )


def completion_hardened(confidence: float = 0.90) -> WorkerHardeningReview:
    return replace(
        hardened_preflight(confidence=confidence),
        post_action_reviewed=True,
        no_unexpected_side_effects=True,
        completion_reviewed_by_user=True,
        completion_evidence_ids=("audit:test-step:after",),
        completion_hardening_passed=True,
    )


def draft_fill_request() -> LiveDevHubActionRequest:
    return LiveDevHubActionRequest(
        action_kind=LiveDevHubActionKind.FILL_FIELD,
        target_description="building permit draft address field",
        selector='input[name="projectAddress"]',
        redacted_value="[REDACTED ADDRESS]",
        user_authorized_browser=True,
        allow_live_execution=True,
    )


class AttendedWorkerTest(unittest.TestCase):
    def test_worker_pauses_without_user_attendance_before_touching_page(self) -> None:
        page = FakePage()
        step = AttendedWorkerStep(
            step_id="draft-address",
            request=draft_fill_request(),
            checkpoint=AttendedUserCheckpoint(),
            hardening=hardened_preflight(),
        )

        decision = attempt_attended_step(step, page=page)

        self.assertEqual(AttendedWorkerStatus.PAUSED, decision.status)
        self.assertFalse(decision.allowed_to_attempt)
        self.assertFalse(decision.attempted)
        self.assertEqual([], page.calls)
        self.assertIn("user must be present", " ".join(decision.required_actions))

    def test_worker_attempts_hardened_draft_but_does_not_complete_it(self) -> None:
        page = FakePage()
        step = AttendedWorkerStep(
            step_id="draft-address",
            request=draft_fill_request(),
            checkpoint=attended_checkpoint(),
            hardening=hardened_preflight(),
        )

        decision = attempt_attended_step(step, page=page)
        completion = complete_attended_step(record_action_result(step, decision.action_result))

        self.assertEqual(AttendedWorkerStatus.ATTEMPTED_REVIEW_REQUIRED, decision.status)
        self.assertTrue(decision.attempted)
        self.assertFalse(decision.complete)
        self.assertEqual([("fill", 'input[name="projectAddress"]', "[REDACTED ADDRESS]")], page.calls)
        self.assertEqual(AttendedWorkerStatus.PAUSED, completion.status)
        self.assertFalse(completion.complete)
        self.assertIn("post-action", " ".join(completion.required_actions))

    def test_worker_completes_only_after_post_action_hardening_passes(self) -> None:
        page = FakePage()
        step = AttendedWorkerStep(
            step_id="draft-address",
            request=draft_fill_request(),
            checkpoint=attended_checkpoint(),
            hardening=completion_hardened(),
        )

        attempted = attempt_attended_step(step, page=page)
        completed = complete_attended_step(record_action_result(step, attempted.action_result))

        self.assertTrue(attempted.attempted)
        self.assertFalse(attempted.complete)
        self.assertEqual(AttendedWorkerStatus.COMPLETE, completed.status)
        self.assertTrue(completed.complete)

    def test_official_action_requires_exact_confirmation_and_stronger_hardening(self) -> None:
        request = LiveDevHubActionRequest(
            action_kind=LiveDevHubActionKind.SUBMIT_APPLICATION,
            target_description="building permit draft 123",
            selector='button:has-text("Submit")',
            user_authorized_browser=True,
            allow_live_execution=True,
            allow_official_execution=True,
        )
        phrase = build_required_confirmation_phrase(request)
        low_confidence = AttendedWorkerStep(
            step_id="submit-draft",
            request=request,
            checkpoint=attended_checkpoint(phrase),
            hardening=hardened_preflight(confidence=0.90),
        )
        missing_confirmation = AttendedWorkerStep(
            step_id="submit-draft",
            request=request,
            checkpoint=attended_checkpoint(),
            hardening=hardened_preflight(confidence=0.96),
        )
        confirmed = replace(
            missing_confirmation,
            checkpoint=attended_checkpoint(phrase),
        )
        page = FakePage()

        low = prepare_attended_step(low_confidence)
        missing = prepare_attended_step(missing_confirmation)
        attempted = attempt_attended_step(confirmed, page=page)

        self.assertEqual(AttendedWorkerStatus.PAUSED, low.status)
        self.assertIn("0.95", " ".join(low.required_actions))
        self.assertEqual(AttendedWorkerStatus.PAUSED, missing.status)
        self.assertIn("exact action confirmation", " ".join(missing.required_actions))
        self.assertEqual(AttendedWorkerStatus.ATTEMPTED_REVIEW_REQUIRED, attempted.status)
        self.assertEqual([("click", 'button:has-text("Submit")', None)], page.calls)

    def test_final_payment_execution_remains_manual_handoff(self) -> None:
        page = FakePage()
        request = LiveDevHubActionRequest(
            action_kind=LiveDevHubActionKind.PAY_FEE,
            target_description="permit fee payment",
            selector='button:has-text("Pay")',
            user_authorized_browser=True,
            allow_live_execution=True,
            allow_official_execution=True,
            provided_confirmation_phrase="anything",
        )
        step = AttendedWorkerStep(
            step_id="pay-fee",
            request=request,
            checkpoint=attended_checkpoint("anything"),
            hardening=completion_hardened(confidence=0.99),
        )

        decision = attempt_attended_step(step, page=page)

        self.assertEqual(AttendedWorkerStatus.MANUAL_HANDOFF, decision.status)
        self.assertFalse(decision.allowed_to_attempt)
        self.assertFalse(decision.attempted)
        self.assertFalse(decision.complete)
        self.assertEqual([], page.calls)

    def test_journal_accepts_ready_attempt_complete_sequence(self) -> None:
        page = FakePage()
        step = AttendedWorkerStep(
            step_id="draft-address",
            request=draft_fill_request(),
            checkpoint=attended_checkpoint(),
            hardening=completion_hardened(),
        )

        ready = prepare_attended_step(step)
        attempted = attempt_attended_step(step, page=page)
        completed_step = record_action_result(step, attempted.action_result)
        completed = complete_attended_step(completed_step)
        entries = (
            journal_attended_decision(step, ready, AttendedWorkerEventKind.PREFLIGHT),
            journal_attended_decision(step, attempted, AttendedWorkerEventKind.ATTEMPT),
            journal_attended_decision(completed_step, completed, AttendedWorkerEventKind.COMPLETION_REVIEW),
        )

        self.assertEqual([], validate_attended_worker_journal(entries))
        self.assertTrue(entries[-1].complete)

    def test_journal_rejects_attempt_without_ready_preflight(self) -> None:
        page = FakePage()
        step = AttendedWorkerStep(
            step_id="draft-address",
            request=draft_fill_request(),
            checkpoint=attended_checkpoint(),
            hardening=completion_hardened(),
        )

        attempted = attempt_attended_step(step, page=page)
        errors = validate_attended_worker_journal(
            (journal_attended_decision(step, attempted, AttendedWorkerEventKind.ATTEMPT),)
        )

        self.assertIn("previous ready preflight", " ".join(errors))

    def test_journal_rejects_completion_without_prior_attempt(self) -> None:
        page = FakePage()
        step = AttendedWorkerStep(
            step_id="draft-address",
            request=draft_fill_request(),
            checkpoint=attended_checkpoint(),
            hardening=completion_hardened(),
        )
        attempted = attempt_attended_step(step, page=page)
        completed_step = record_action_result(step, attempted.action_result)
        completed = complete_attended_step(completed_step)

        errors = validate_attended_worker_journal(
            (journal_attended_decision(completed_step, completed, AttendedWorkerEventKind.COMPLETION_REVIEW),)
        )

        self.assertIn("previous attempted", " ".join(errors))

    def test_journal_redacts_confirmation_selector_value_and_file_path(self) -> None:
        request = LiveDevHubActionRequest(
            action_kind=LiveDevHubActionKind.SUBMIT_APPLICATION,
            target_description="building permit draft 123",
            selector='button:has-text("Submit")',
            redacted_value="[REDACTED ADDRESS]",
            local_file_path="/tmp/private-user-document.pdf",
            user_authorized_browser=True,
            allow_live_execution=True,
            allow_official_execution=True,
        )
        phrase = build_required_confirmation_phrase(request)
        step = AttendedWorkerStep(
            step_id="submit-draft",
            request=request,
            checkpoint=attended_checkpoint("wrong confirmation"),
            hardening=hardened_preflight(confidence=0.96),
        )

        decision = prepare_attended_step(step)
        entry = journal_attended_decision(step, decision, AttendedWorkerEventKind.PREFLIGHT)
        payload = str(entry.to_dict())

        self.assertNotIn(phrase, payload)
        self.assertNotIn('button:has-text("Submit")', payload)
        self.assertNotIn("[REDACTED ADDRESS]", payload)
        self.assertNotIn("/tmp/private-user-document.pdf", payload)
        self.assertIn("[EXACT_CONFIRMATION_PHRASE_REDACTED]", payload)

    def test_resume_report_marks_paused_step_as_needing_attendance_or_hardening(self) -> None:
        step = AttendedWorkerStep(
            step_id="draft-address",
            request=draft_fill_request(),
            checkpoint=AttendedUserCheckpoint(),
            hardening=hardened_preflight(),
        )
        paused = prepare_attended_step(step)
        entry = journal_attended_decision(step, paused, AttendedWorkerEventKind.PREFLIGHT)

        report = resume_attended_worker_journal((entry,))

        self.assertTrue(report.valid)
        self.assertEqual(AttendedWorkerResumeAction.COLLECT_ATTENDANCE_OR_HARDENING, report.states[0].next_action)
        self.assertFalse(report.states[0].can_attempt)
        self.assertFalse(report.states[0].complete)

    def test_resume_report_marks_ready_step_as_attemptable(self) -> None:
        step = AttendedWorkerStep(
            step_id="draft-address",
            request=draft_fill_request(),
            checkpoint=attended_checkpoint(),
            hardening=hardened_preflight(),
        )
        ready = prepare_attended_step(step)
        entry = journal_attended_decision(step, ready, AttendedWorkerEventKind.PREFLIGHT)

        report = resume_attended_worker_journal((entry,))

        self.assertTrue(report.valid)
        self.assertEqual(AttendedWorkerResumeAction.ATTEMPT_WHILE_ATTENDED, report.states[0].next_action)
        self.assertTrue(report.states[0].can_attempt)

    def test_resume_report_marks_attempted_step_as_review_required(self) -> None:
        page = FakePage()
        step = AttendedWorkerStep(
            step_id="draft-address",
            request=draft_fill_request(),
            checkpoint=attended_checkpoint(),
            hardening=hardened_preflight(),
        )
        ready = prepare_attended_step(step)
        attempted = attempt_attended_step(step, page=page)
        entries = (
            journal_attended_decision(step, ready, AttendedWorkerEventKind.PREFLIGHT),
            journal_attended_decision(step, attempted, AttendedWorkerEventKind.ATTEMPT),
        )

        report = resume_attended_worker_journal(entries)

        self.assertTrue(report.valid)
        self.assertEqual(AttendedWorkerResumeAction.REVIEW_POST_ACTION_HARDENING, report.states[0].next_action)
        self.assertFalse(report.states[0].can_attempt)
        self.assertTrue(report.states[0].review_required)
        self.assertFalse(report.states[0].complete)

    def test_resume_report_marks_completed_step_closed(self) -> None:
        page = FakePage()
        step = AttendedWorkerStep(
            step_id="draft-address",
            request=draft_fill_request(),
            checkpoint=attended_checkpoint(),
            hardening=completion_hardened(),
        )
        ready = prepare_attended_step(step)
        attempted = attempt_attended_step(step, page=page)
        completed_step = record_action_result(step, attempted.action_result)
        completed = complete_attended_step(completed_step)
        entries = (
            journal_attended_decision(step, ready, AttendedWorkerEventKind.PREFLIGHT),
            journal_attended_decision(step, attempted, AttendedWorkerEventKind.ATTEMPT),
            journal_attended_decision(completed_step, completed, AttendedWorkerEventKind.COMPLETION_REVIEW),
        )

        report = resume_attended_worker_journal(entries)

        self.assertTrue(report.valid)
        self.assertEqual(AttendedWorkerResumeAction.CLOSED_COMPLETE, report.states[0].next_action)
        self.assertFalse(report.states[0].can_attempt)
        self.assertTrue(report.states[0].complete)

    def test_resume_report_rejects_later_events_after_complete(self) -> None:
        page = FakePage()
        step = AttendedWorkerStep(
            step_id="draft-address",
            request=draft_fill_request(),
            checkpoint=attended_checkpoint(),
            hardening=completion_hardened(),
        )
        ready = prepare_attended_step(step)
        attempted = attempt_attended_step(step, page=page)
        completed_step = record_action_result(step, attempted.action_result)
        completed = complete_attended_step(completed_step)
        entries = (
            journal_attended_decision(step, ready, AttendedWorkerEventKind.PREFLIGHT),
            journal_attended_decision(step, attempted, AttendedWorkerEventKind.ATTEMPT),
            journal_attended_decision(completed_step, completed, AttendedWorkerEventKind.COMPLETION_REVIEW),
            journal_attended_decision(
                step,
                ready,
                AttendedWorkerEventKind.PREFLIGHT,
                event_id="ppd-attended-worker-event:draft-address:extra-preflight",
            ),
        )

        report = resume_attended_worker_journal(entries)

        self.assertFalse(report.valid)
        self.assertIn("completed step must not receive later worker events", " ".join(report.errors))


if __name__ == "__main__":
    unittest.main()
