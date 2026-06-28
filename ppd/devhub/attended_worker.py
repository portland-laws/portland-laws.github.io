"""Attended worker gates for live DevHub automation.

This module sits above ``live_action_executor``. It does not make the live
executor more permissive; it adds an operator-attended workflow so browser
actions can be attempted only after the user is present and the step has enough
preflight evidence, then forces a post-action hardening review before any step
can be marked complete.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Optional

from ppd.devhub.live_action_executor import (
    ALWAYS_REFUSED_ACTIONS,
    OFFICIAL_ACTIONS,
    LiveDevHubActionKind,
    LiveDevHubActionRequest,
    LiveDevHubActionResult,
    PlaywrightLikePage,
    evaluate_live_devhub_action,
    execute_live_devhub_action,
)


DRAFT_SELECTOR_CONFIDENCE_MINIMUM = 0.80
OFFICIAL_SELECTOR_CONFIDENCE_MINIMUM = 0.95


class AttendedWorkerStatus(str, Enum):
    PAUSED = "paused"
    READY_TO_ATTEMPT = "ready_to_attempt"
    ATTEMPTED_REVIEW_REQUIRED = "attempted_review_required"
    COMPLETE = "complete"
    MANUAL_HANDOFF = "manual_handoff"
    REFUSED = "refused"


class AttendedWorkerEventKind(str, Enum):
    PREFLIGHT = "preflight"
    ATTEMPT = "attempt"
    COMPLETION_REVIEW = "completion_review"


class AttendedWorkerResumeAction(str, Enum):
    COLLECT_ATTENDANCE_OR_HARDENING = "collect_attendance_or_hardening"
    ATTEMPT_WHILE_ATTENDED = "attempt_while_attended"
    REVIEW_POST_ACTION_HARDENING = "review_post_action_hardening"
    MANUAL_HANDOFF = "manual_handoff"
    CLOSED_COMPLETE = "closed_complete"
    REPAIR_JOURNAL = "repair_journal"


@dataclass(frozen=True)
class AttendedUserCheckpoint:
    """User-attendance proof captured before a worker touches DevHub."""

    user_present: bool = False
    reviewed_current_screen: bool = False
    understands_next_action: bool = False
    operator_label: str = ""
    exact_confirmation_phrase: str = ""

    def preflight_errors(self) -> list[str]:
        errors: list[str] = []
        if not self.user_present:
            errors.append("user must be present with the worker before any attempt")
        if not self.reviewed_current_screen:
            errors.append("user must review the current browser screen before any attempt")
        if not self.understands_next_action:
            errors.append("user must understand the next proposed worker action")
        return errors


@dataclass(frozen=True)
class WorkerHardeningReview:
    """Evidence that a worker step is hardened enough to attempt or complete."""

    source_evidence_ids: tuple[str, ...] = ()
    selector_basis: str = ""
    selector_confidence: float = 0.0
    audit_event_id: str = ""
    rollback_plan: str = ""
    preview_or_dry_run_completed: bool = False
    no_private_artifacts_persisted: bool = False
    post_action_reviewed: bool = False
    no_unexpected_side_effects: bool = False
    completion_reviewed_by_user: bool = False
    completion_evidence_ids: tuple[str, ...] = ()
    completion_hardening_passed: bool = False

    def preflight_errors(self, request: LiveDevHubActionRequest) -> list[str]:
        errors: list[str] = []
        if not self.source_evidence_ids:
            errors.append("source evidence ids are required before any attempt")
        if not self.audit_event_id.strip():
            errors.append("audit event id is required before any attempt")
        if not self.rollback_plan.strip():
            errors.append("rollback or manual recovery plan is required before any attempt")
        if not self.preview_or_dry_run_completed:
            errors.append("preview or dry-run must complete before any attempt")
        if not self.no_private_artifacts_persisted:
            errors.append("private artifacts must be excluded from worker persistence")
        if request.selector:
            if not self.selector_basis.strip():
                errors.append("selector basis is required before touching the page")
            minimum = _selector_confidence_minimum(request.action_kind)
            if self.selector_confidence < minimum:
                errors.append(
                    f"selector confidence must be at least {minimum:.2f} "
                    f"for {request.action_kind.value}"
                )
        return errors

    def completion_errors(self) -> list[str]:
        errors: list[str] = []
        if not self.post_action_reviewed:
            errors.append("post-action screen and audit review is required before completion")
        if not self.no_unexpected_side_effects:
            errors.append("unexpected side effects must be ruled out before completion")
        if not self.completion_reviewed_by_user:
            errors.append("user must review the step outcome before completion")
        if not self.completion_evidence_ids:
            errors.append("completion evidence ids are required before completion")
        if not self.completion_hardening_passed:
            errors.append("completion hardening must explicitly pass before completion")
        return errors


@dataclass(frozen=True)
class AttendedWorkerStep:
    step_id: str
    request: LiveDevHubActionRequest
    checkpoint: AttendedUserCheckpoint
    hardening: WorkerHardeningReview
    action_result: Optional[LiveDevHubActionResult] = None


@dataclass(frozen=True)
class AttendedWorkerDecision:
    step_id: str
    status: AttendedWorkerStatus
    allowed_to_attempt: bool
    attempted: bool
    complete: bool
    reason: str
    required_actions: tuple[str, ...] = ()
    action_result: Optional[LiveDevHubActionResult] = None

    def to_dict(self) -> dict[str, object]:
        return {
            "stepId": self.step_id,
            "status": self.status.value,
            "allowedToAttempt": self.allowed_to_attempt,
            "attempted": self.attempted,
            "complete": self.complete,
            "reason": self.reason,
            "requiredActions": list(self.required_actions),
            "actionResult": self.action_result.to_dict() if self.action_result else None,
        }


@dataclass(frozen=True)
class AttendedWorkerJournalEntry:
    """Commit-safe event for an attended worker decision.

    The journal records guardrail state and redacted decision metadata only. It
    deliberately omits selectors, field values, local paths, browser storage,
    screenshots, traces, and raw DevHub artifacts.
    """

    event_id: str
    step_id: str
    event_kind: AttendedWorkerEventKind
    status: AttendedWorkerStatus
    action_kind: LiveDevHubActionKind
    allowed_to_attempt: bool
    attempted: bool
    complete: bool
    reason: str
    required_actions: tuple[str, ...]
    source_evidence_ids: tuple[str, ...]
    audit_event_id: str
    selector_confidence: float
    user_present: bool
    reviewed_current_screen: bool
    understands_next_action: bool
    no_private_artifacts_persisted: bool
    post_action_reviewed: bool
    no_unexpected_side_effects: bool
    completion_reviewed_by_user: bool
    completion_evidence_ids: tuple[str, ...]
    completion_hardening_passed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "eventId": self.event_id,
            "stepId": self.step_id,
            "eventKind": self.event_kind.value,
            "status": self.status.value,
            "actionKind": self.action_kind.value,
            "allowedToAttempt": self.allowed_to_attempt,
            "attempted": self.attempted,
            "complete": self.complete,
            "reason": self.reason,
            "requiredActions": list(self.required_actions),
            "sourceEvidenceIds": list(self.source_evidence_ids),
            "auditEventId": self.audit_event_id,
            "selectorConfidence": self.selector_confidence,
            "userPresent": self.user_present,
            "reviewedCurrentScreen": self.reviewed_current_screen,
            "understandsNextAction": self.understands_next_action,
            "noPrivateArtifactsPersisted": self.no_private_artifacts_persisted,
            "postActionReviewed": self.post_action_reviewed,
            "noUnexpectedSideEffects": self.no_unexpected_side_effects,
            "completionReviewedByUser": self.completion_reviewed_by_user,
            "completionEvidenceIds": list(self.completion_evidence_ids),
            "completionHardeningPassed": self.completion_hardening_passed,
        }


@dataclass(frozen=True)
class AttendedWorkerResumeState:
    step_id: str
    action_kind: LiveDevHubActionKind
    latest_event_id: str
    latest_status: AttendedWorkerStatus
    next_action: AttendedWorkerResumeAction
    can_attempt: bool
    review_required: bool
    complete: bool
    required_actions: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "stepId": self.step_id,
            "actionKind": self.action_kind.value,
            "latestEventId": self.latest_event_id,
            "latestStatus": self.latest_status.value,
            "nextAction": self.next_action.value,
            "canAttempt": self.can_attempt,
            "reviewRequired": self.review_required,
            "complete": self.complete,
            "requiredActions": list(self.required_actions),
        }


@dataclass(frozen=True)
class AttendedWorkerResumeReport:
    valid: bool
    states: tuple[AttendedWorkerResumeState, ...]
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "states": [state.to_dict() for state in self.states],
        }


def prepare_attended_step(step: AttendedWorkerStep) -> AttendedWorkerDecision:
    """Return whether the attended worker may attempt this step now."""

    request = _request_with_checkpoint_confirmation(step)

    if request.action_kind in ALWAYS_REFUSED_ACTIONS:
        decision = evaluate_live_devhub_action(request)
        return AttendedWorkerDecision(
            step_id=step.step_id,
            status=AttendedWorkerStatus.MANUAL_HANDOFF,
            allowed_to_attempt=False,
            attempted=False,
            complete=False,
            reason=decision.reason,
            required_actions=("manual user handoff is required",),
            action_result=decision,
        )

    errors = step.checkpoint.preflight_errors()
    errors.extend(step.hardening.preflight_errors(request))
    if request.action_kind in OFFICIAL_ACTIONS and not step.checkpoint.exact_confirmation_phrase.strip():
        errors.append("official exact action confirmation must be captured in the attended checkpoint")
    if errors:
        return AttendedWorkerDecision(
            step_id=step.step_id,
            status=AttendedWorkerStatus.PAUSED,
            allowed_to_attempt=False,
            attempted=False,
            complete=False,
            reason="user attendance and hardening are required before any attempt",
            required_actions=tuple(errors),
        )

    decision = evaluate_live_devhub_action(request)
    if not decision.allowed:
        status = (
            AttendedWorkerStatus.MANUAL_HANDOFF
            if decision.requires_manual_handoff and not decision.requires_exact_confirmation
            else AttendedWorkerStatus.PAUSED
        )
        required_actions = _required_actions_for_policy_decision(decision)
        return AttendedWorkerDecision(
            step_id=step.step_id,
            status=status,
            allowed_to_attempt=False,
            attempted=False,
            complete=False,
            reason=decision.reason,
            required_actions=required_actions,
            action_result=decision,
        )
    if decision.status != "allowed":
        return AttendedWorkerDecision(
            step_id=step.step_id,
            status=AttendedWorkerStatus.PAUSED,
            allowed_to_attempt=False,
            attempted=False,
            complete=False,
            reason=decision.reason,
            required_actions=("enable the live execution flag only while attended",),
            action_result=decision,
        )

    return AttendedWorkerDecision(
        step_id=step.step_id,
        status=AttendedWorkerStatus.READY_TO_ATTEMPT,
        allowed_to_attempt=True,
        attempted=False,
        complete=False,
        reason="attended preflight passed; worker may attempt the action",
        action_result=decision,
    )


def attempt_attended_step(
    step: AttendedWorkerStep,
    *,
    page: Optional[PlaywrightLikePage] = None,
) -> AttendedWorkerDecision:
    """Attempt an attended step, then force post-action review before completion."""

    prepared = prepare_attended_step(step)
    if not prepared.allowed_to_attempt:
        return prepared

    request = _request_with_checkpoint_confirmation(step)
    result = execute_live_devhub_action(request, page=page)
    if not result.executed:
        return AttendedWorkerDecision(
            step_id=step.step_id,
            status=AttendedWorkerStatus.READY_TO_ATTEMPT,
            allowed_to_attempt=True,
            attempted=False,
            complete=False,
            reason=result.reason,
            required_actions=("supply a live Playwright page before attempting",),
            action_result=result,
        )

    return AttendedWorkerDecision(
        step_id=step.step_id,
        status=AttendedWorkerStatus.ATTEMPTED_REVIEW_REQUIRED,
        allowed_to_attempt=False,
        attempted=True,
        complete=False,
        reason="action attempted; post-action hardening review is required before completion",
        required_actions=tuple(step.hardening.completion_errors()),
        action_result=result,
    )


def complete_attended_step(step: AttendedWorkerStep) -> AttendedWorkerDecision:
    """Mark a worker step complete only after explicit post-action hardening."""

    request = _request_with_checkpoint_confirmation(step)
    if request.action_kind in ALWAYS_REFUSED_ACTIONS:
        decision = evaluate_live_devhub_action(request)
        return AttendedWorkerDecision(
            step_id=step.step_id,
            status=AttendedWorkerStatus.MANUAL_HANDOFF,
            allowed_to_attempt=False,
            attempted=False,
            complete=False,
            reason=decision.reason,
            required_actions=("manual user handoff is required",),
            action_result=decision,
        )

    errors = step.checkpoint.preflight_errors()
    errors.extend(step.hardening.preflight_errors(request))
    if request.action_kind in OFFICIAL_ACTIONS and not step.checkpoint.exact_confirmation_phrase.strip():
        errors.append("official exact action confirmation must be captured in the attended checkpoint")
    errors.extend(step.hardening.completion_errors())
    if step.action_result is None or not step.action_result.executed:
        errors.append("executed action result is required before completion")
    if step.action_result and not step.action_result.allowed:
        errors.append("refused action result cannot be completed")
    if step.action_result and step.action_result.action_kind != request.action_kind:
        errors.append("executed action result must match the worker step request")

    if errors:
        return AttendedWorkerDecision(
            step_id=step.step_id,
            status=AttendedWorkerStatus.PAUSED,
            allowed_to_attempt=False,
            attempted=bool(step.action_result and step.action_result.executed),
            complete=False,
            reason="step is not complete until post-action hardening passes",
            required_actions=tuple(errors),
            action_result=step.action_result,
        )

    return AttendedWorkerDecision(
        step_id=step.step_id,
        status=AttendedWorkerStatus.COMPLETE,
        allowed_to_attempt=False,
        attempted=True,
        complete=True,
        reason="post-action hardening passed and the attended user reviewed the outcome",
        action_result=step.action_result,
    )


def record_action_result(
    step: AttendedWorkerStep,
    result: LiveDevHubActionResult,
) -> AttendedWorkerStep:
    return replace(step, action_result=result)


def journal_attended_decision(
    step: AttendedWorkerStep,
    decision: AttendedWorkerDecision,
    event_kind: AttendedWorkerEventKind,
    *,
    event_id: str = "",
) -> AttendedWorkerJournalEntry:
    """Create a commit-safe journal event for an attended worker decision."""

    return AttendedWorkerJournalEntry(
        event_id=event_id.strip() or _default_event_id(step.step_id, event_kind, decision.status),
        step_id=step.step_id,
        event_kind=event_kind,
        status=decision.status,
        action_kind=step.request.action_kind,
        allowed_to_attempt=decision.allowed_to_attempt,
        attempted=decision.attempted,
        complete=decision.complete,
        reason=decision.reason,
        required_actions=_commit_safe_required_actions(decision.required_actions),
        source_evidence_ids=step.hardening.source_evidence_ids,
        audit_event_id=step.hardening.audit_event_id,
        selector_confidence=step.hardening.selector_confidence,
        user_present=step.checkpoint.user_present,
        reviewed_current_screen=step.checkpoint.reviewed_current_screen,
        understands_next_action=step.checkpoint.understands_next_action,
        no_private_artifacts_persisted=step.hardening.no_private_artifacts_persisted,
        post_action_reviewed=step.hardening.post_action_reviewed,
        no_unexpected_side_effects=step.hardening.no_unexpected_side_effects,
        completion_reviewed_by_user=step.hardening.completion_reviewed_by_user,
        completion_evidence_ids=step.hardening.completion_evidence_ids,
        completion_hardening_passed=step.hardening.completion_hardening_passed,
    )


def validate_attended_worker_journal(entries: tuple[AttendedWorkerJournalEntry, ...]) -> list[str]:
    """Validate attended worker journal transitions and commit-safe metadata."""

    errors: list[str] = []
    seen_event_ids: set[str] = set()
    ready_steps: set[str] = set()
    attempted_steps: set[str] = set()
    completed_steps: set[str] = set()
    for index, entry in enumerate(entries):
        path = f"journal[{index}]"
        if entry.step_id in completed_steps:
            errors.append(f"{path}: completed step must not receive later worker events")
        if not entry.event_id.startswith("ppd-attended-worker-event:"):
            errors.append(f"{path}: event id must use ppd-attended-worker-event prefix")
        if entry.event_id in seen_event_ids:
            errors.append(f"{path}: event id must be unique")
        seen_event_ids.add(entry.event_id)
        if not entry.step_id.strip():
            errors.append(f"{path}: step id is required")
        if entry.status in {
            AttendedWorkerStatus.READY_TO_ATTEMPT,
            AttendedWorkerStatus.ATTEMPTED_REVIEW_REQUIRED,
            AttendedWorkerStatus.COMPLETE,
        }:
            errors.extend(_journal_guardrail_errors(path, entry))
        if entry.event_kind == AttendedWorkerEventKind.PREFLIGHT:
            if entry.attempted:
                errors.append(f"{path}: preflight event must not be attempted")
            if entry.status == AttendedWorkerStatus.READY_TO_ATTEMPT:
                ready_steps.add(entry.step_id)
        if entry.event_kind == AttendedWorkerEventKind.ATTEMPT:
            if entry.step_id not in ready_steps:
                errors.append(f"{path}: attempt event requires a previous ready preflight event")
            if entry.complete:
                errors.append(f"{path}: attempt event must not complete a step")
            if entry.status == AttendedWorkerStatus.ATTEMPTED_REVIEW_REQUIRED and entry.attempted:
                attempted_steps.add(entry.step_id)
        if entry.event_kind == AttendedWorkerEventKind.COMPLETION_REVIEW:
            if entry.step_id not in attempted_steps:
                errors.append(f"{path}: completion review requires a previous attempted event")
            if entry.complete and entry.status != AttendedWorkerStatus.COMPLETE:
                errors.append(f"{path}: complete event must use complete status")
            if entry.status == AttendedWorkerStatus.COMPLETE:
                errors.extend(_journal_completion_errors(path, entry))
                completed_steps.add(entry.step_id)
        elif entry.complete:
            errors.append(f"{path}: only completion_review events may complete a step")
    return errors


def resume_attended_worker_journal(
    entries: tuple[AttendedWorkerJournalEntry, ...],
) -> AttendedWorkerResumeReport:
    """Replay a commit-safe attended-worker journal into resumable step states."""

    errors = tuple(validate_attended_worker_journal(entries))
    latest_by_step: dict[str, AttendedWorkerJournalEntry] = {}
    for entry in entries:
        latest_by_step[entry.step_id] = entry
    states = tuple(
        _resume_state_from_entry(entry)
        for entry in sorted(latest_by_step.values(), key=lambda item: item.step_id)
    )
    if errors:
        return AttendedWorkerResumeReport(valid=False, states=states, errors=errors)
    return AttendedWorkerResumeReport(valid=True, states=states)


def _request_with_checkpoint_confirmation(step: AttendedWorkerStep) -> LiveDevHubActionRequest:
    if step.request.provided_confirmation_phrase.strip():
        return step.request
    if not step.checkpoint.exact_confirmation_phrase.strip():
        return step.request
    return replace(
        step.request,
        provided_confirmation_phrase=step.checkpoint.exact_confirmation_phrase.strip(),
    )


def _selector_confidence_minimum(action_kind: LiveDevHubActionKind) -> float:
    if action_kind in OFFICIAL_ACTIONS:
        return OFFICIAL_SELECTOR_CONFIDENCE_MINIMUM
    return DRAFT_SELECTOR_CONFIDENCE_MINIMUM


def _required_actions_for_policy_decision(
    decision: LiveDevHubActionResult,
) -> tuple[str, ...]:
    if decision.requires_exact_confirmation:
        if decision.required_confirmation_phrase:
            return (
                "provide the exact action confirmation phrase",
                decision.required_confirmation_phrase,
            )
        return ("configure an exact action confirmation phrase",)
    if decision.requires_manual_handoff:
        return ("manual user handoff is required",)
    return (decision.reason,)


def _default_event_id(
    step_id: str,
    event_kind: AttendedWorkerEventKind,
    status: AttendedWorkerStatus,
) -> str:
    normalized_step = "-".join(step_id.split()) or "missing-step"
    return f"ppd-attended-worker-event:{normalized_step}:{event_kind.value}:{status.value}"


def _resume_state_from_entry(entry: AttendedWorkerJournalEntry) -> AttendedWorkerResumeState:
    if entry.status == AttendedWorkerStatus.READY_TO_ATTEMPT and entry.allowed_to_attempt:
        next_action = AttendedWorkerResumeAction.ATTEMPT_WHILE_ATTENDED
        can_attempt = True
        review_required = False
    elif entry.status == AttendedWorkerStatus.ATTEMPTED_REVIEW_REQUIRED:
        next_action = AttendedWorkerResumeAction.REVIEW_POST_ACTION_HARDENING
        can_attempt = False
        review_required = True
    elif entry.status == AttendedWorkerStatus.COMPLETE and entry.complete:
        next_action = AttendedWorkerResumeAction.CLOSED_COMPLETE
        can_attempt = False
        review_required = False
    elif entry.status == AttendedWorkerStatus.MANUAL_HANDOFF:
        next_action = AttendedWorkerResumeAction.MANUAL_HANDOFF
        can_attempt = False
        review_required = False
    elif entry.status == AttendedWorkerStatus.REFUSED:
        next_action = AttendedWorkerResumeAction.REPAIR_JOURNAL
        can_attempt = False
        review_required = False
    else:
        next_action = AttendedWorkerResumeAction.COLLECT_ATTENDANCE_OR_HARDENING
        can_attempt = False
        review_required = False

    return AttendedWorkerResumeState(
        step_id=entry.step_id,
        action_kind=entry.action_kind,
        latest_event_id=entry.event_id,
        latest_status=entry.status,
        next_action=next_action,
        can_attempt=can_attempt,
        review_required=review_required,
        complete=entry.complete,
        required_actions=entry.required_actions,
    )


def _commit_safe_required_actions(required_actions: tuple[str, ...]) -> tuple[str, ...]:
    safe_actions: list[str] = []
    for action in required_actions:
        normalized = " ".join(action.split())
        if normalized.startswith("I authorize "):
            safe_actions.append("[EXACT_CONFIRMATION_PHRASE_REDACTED]")
        else:
            safe_actions.append(action)
    return tuple(safe_actions)


def _journal_guardrail_errors(path: str, entry: AttendedWorkerJournalEntry) -> list[str]:
    errors: list[str] = []
    if not entry.user_present:
        errors.append(f"{path}: attended user presence is required")
    if not entry.reviewed_current_screen:
        errors.append(f"{path}: current-screen review is required")
    if not entry.understands_next_action:
        errors.append(f"{path}: next-action understanding is required")
    if not entry.source_evidence_ids:
        errors.append(f"{path}: source evidence ids are required")
    if not entry.audit_event_id.strip():
        errors.append(f"{path}: audit event id is required")
    if not entry.no_private_artifacts_persisted:
        errors.append(f"{path}: private artifact exclusion proof is required")
    return errors


def _journal_completion_errors(path: str, entry: AttendedWorkerJournalEntry) -> list[str]:
    errors: list[str] = []
    if not entry.post_action_reviewed:
        errors.append(f"{path}: post-action review is required")
    if not entry.no_unexpected_side_effects:
        errors.append(f"{path}: side-effect review is required")
    if not entry.completion_reviewed_by_user:
        errors.append(f"{path}: user outcome review is required")
    if not entry.completion_evidence_ids:
        errors.append(f"{path}: completion evidence ids are required")
    if not entry.completion_hardening_passed:
        errors.append(f"{path}: completion hardening must pass")
    return errors
