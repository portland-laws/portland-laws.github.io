"""Fixture-only DevHub draft-readiness decisions.

This module does not automate DevHub. It models the reversible draft-readiness
checks an agent must satisfy before it may prepare a draft-only form preview.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


REFUSED_OFFICIAL_ACTIONS = (
    "upload",
    "submit",
    "payment",
    "certification",
    "cancellation",
    "inspection_scheduling",
)


@dataclass(frozen=True)
class DraftReadinessInput:
    permit_type: str
    source_ids: tuple[str, ...]
    missing_facts: tuple[str, ...]
    redacted_file_placeholders: tuple[str, ...]
    selector_confidence: float
    upload_ready: bool
    fee_notice_required: bool
    exact_confirmation: bool


@dataclass(frozen=True)
class DraftReadinessDecision:
    permit_type: str
    ready_for_draft_preview: bool
    missing_facts: tuple[str, ...]
    redacted_file_placeholders: tuple[str, ...]
    selector_review_required: bool
    upload_blocked: bool
    fee_notice_required: bool
    exact_confirmation_required: bool
    refused_official_actions: tuple[str, ...]
    source_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "permitType": self.permit_type,
            "readyForDraftPreview": self.ready_for_draft_preview,
            "missingFacts": list(self.missing_facts),
            "redactedFilePlaceholders": list(self.redacted_file_placeholders),
            "selectorReviewRequired": self.selector_review_required,
            "uploadBlocked": self.upload_blocked,
            "feeNoticeRequired": self.fee_notice_required,
            "exactConfirmationRequired": self.exact_confirmation_required,
            "refusedOfficialActions": list(self.refused_official_actions),
            "sourceIds": list(self.source_ids),
        }


def decide_draft_readiness(case: DraftReadinessInput) -> DraftReadinessDecision:
    """Return a deterministic draft-only readiness decision."""

    selector_review_required = case.selector_confidence < 0.85
    missing_or_placeholder_inputs = bool(case.missing_facts or case.redacted_file_placeholders)
    ready_for_draft_preview = (
        not missing_or_placeholder_inputs
        and not selector_review_required
        and case.exact_confirmation
    )
    return DraftReadinessDecision(
        permit_type=case.permit_type,
        ready_for_draft_preview=ready_for_draft_preview,
        missing_facts=case.missing_facts,
        redacted_file_placeholders=case.redacted_file_placeholders,
        selector_review_required=selector_review_required,
        upload_blocked=not case.upload_ready or not case.exact_confirmation,
        fee_notice_required=case.fee_notice_required,
        exact_confirmation_required=not case.exact_confirmation,
        refused_official_actions=REFUSED_OFFICIAL_ACTIONS,
        source_ids=case.source_ids,
    )


def fixture_decision_matrix() -> tuple[DraftReadinessDecision, ...]:
    """Return the committed fixture-only decision matrix for validation."""

    cases = (
        DraftReadinessInput(
            permit_type="residential-building",
            source_ids=("ppd-devhub-building-permit-guide", "ppd-fee-schedule"),
            missing_facts=("project valuation", "contractor license number"),
            redacted_file_placeholders=("site-plan.pdf",),
            selector_confidence=0.92,
            upload_ready=False,
            fee_notice_required=True,
            exact_confirmation=False,
        ),
        DraftReadinessInput(
            permit_type="trade-permit",
            source_ids=("ppd-devhub-trade-permit-guide",),
            missing_facts=(),
            redacted_file_placeholders=(),
            selector_confidence=0.73,
            upload_ready=True,
            fee_notice_required=False,
            exact_confirmation=True,
        ),
        DraftReadinessInput(
            permit_type="demolition-permit",
            source_ids=("ppd-devhub-demolition-permit-guide", "ppd-demolition-code-summary"),
            missing_facts=(),
            redacted_file_placeholders=(),
            selector_confidence=0.91,
            upload_ready=True,
            fee_notice_required=True,
            exact_confirmation=True,
        ),
    )
    return tuple(decide_draft_readiness(case) for case in cases)


def validate_draft_readiness_matrix(decisions: Sequence[DraftReadinessDecision]) -> list[str]:
    """Validate the matrix remains source-backed and draft-only."""

    errors: list[str] = []
    if not decisions:
        return ["draft-readiness matrix must include at least one decision"]

    for decision in decisions:
        if not decision.source_ids:
            errors.append(f"{decision.permit_type}: source_ids must not be empty")
        if any(not source_id.startswith("ppd-") for source_id in decision.source_ids):
            errors.append(f"{decision.permit_type}: every source_id must be a stable PP&D identifier")
        if set(decision.refused_official_actions) != set(REFUSED_OFFICIAL_ACTIONS):
            errors.append(f"{decision.permit_type}: refused official action set changed")
        if decision.ready_for_draft_preview and (
            decision.missing_facts
            or decision.redacted_file_placeholders
            or decision.selector_review_required
            or decision.exact_confirmation_required
        ):
            errors.append(f"{decision.permit_type}: draft preview cannot be ready while gates remain")
        if decision.upload_blocked is False and decision.exact_confirmation_required:
            errors.append(f"{decision.permit_type}: upload cannot be unblocked without exact confirmation")
    return errors


def decisions_to_dicts(decisions: Iterable[DraftReadinessDecision]) -> list[dict[str, object]]:
    return [decision.to_dict() for decision in decisions]
