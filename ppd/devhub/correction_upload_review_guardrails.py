"""Guardrails for DevHub correction-upload review actions.

This module is fixture-oriented and intentionally does not automate DevHub. It
models the decision boundary needed by agents: a correction-upload review may
produce a preview, but official upload and certification actions require exact,
session-specific user confirmation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional


class CorrectionReviewAction(str, Enum):
    PREVIEW = "preview"
    OFFICIAL_UPLOAD = "official_upload"
    CERTIFICATION = "certification"


class CorrectionReviewDecision(str, Enum):
    ALLOW_PREVIEW = "allow_preview"
    ALLOW_CONFIRMED_CONSEQUENTIAL_ACTION = "allow_confirmed_consequential_action"
    REFUSE_MISSING_EXACT_CONFIRMATION = "refuse_missing_exact_confirmation"
    REFUSE_INVALID_REVIEW_STATE = "refuse_invalid_review_state"
    REFUSE_PRIVATE_VALUE_RISK = "refuse_private_value_risk"
    REFUSE_UNKNOWN_ACTION = "refuse_unknown_action"


@dataclass(frozen=True)
class CorrectionUploadReviewState:
    session_id: str
    permit_reference: str
    workflow_state: str
    draft_state: str
    accepted_file_hints: tuple[str, ...]
    validation_messages: tuple[str, ...]
    upload_control_label: str
    certification_label: str
    exact_upload_confirmation: str
    exact_certification_confirmation: str
    redacted_values_only: bool = True

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CorrectionUploadReviewState":
        return cls(
            session_id=str(data.get("sessionId", data.get("session_id", ""))),
            permit_reference=str(data.get("permitReference", data.get("permit_reference", ""))),
            workflow_state=str(data.get("workflowState", data.get("workflow_state", ""))),
            draft_state=str(data.get("draftState", data.get("draft_state", ""))),
            accepted_file_hints=tuple(str(item) for item in data.get("acceptedFileHints", data.get("accepted_file_hints", ()))),
            validation_messages=tuple(str(item) for item in data.get("validationMessages", data.get("validation_messages", ()))),
            upload_control_label=str(data.get("uploadControlLabel", data.get("upload_control_label", ""))),
            certification_label=str(data.get("certificationLabel", data.get("certification_label", ""))),
            exact_upload_confirmation=str(data.get("exactUploadConfirmation", data.get("exact_upload_confirmation", ""))),
            exact_certification_confirmation=str(data.get("exactCertificationConfirmation", data.get("exact_certification_confirmation", ""))),
            redacted_values_only=bool(data.get("redactedValuesOnly", data.get("redacted_values_only", True))),
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        required_fields = {
            "session_id": self.session_id,
            "permit_reference": self.permit_reference,
            "workflow_state": self.workflow_state,
            "draft_state": self.draft_state,
            "upload_control_label": self.upload_control_label,
            "certification_label": self.certification_label,
            "exact_upload_confirmation": self.exact_upload_confirmation,
            "exact_certification_confirmation": self.exact_certification_confirmation,
        }
        for field_name, value in required_fields.items():
            if not value.strip():
                errors.append(f"{field_name} is required")
        if self.workflow_state != "correction_upload_review":
            errors.append("workflow_state must be correction_upload_review")
        if self.draft_state not in {"draft", "ready_for_review"}:
            errors.append("draft_state must be draft or ready_for_review")
        if not self.accepted_file_hints:
            errors.append("accepted_file_hints are required")
        if not self.validation_messages:
            errors.append("validation_messages are required")
        if not self.redacted_values_only:
            errors.append("review state must contain only redacted values")
        if self.session_id and self.session_id not in self.exact_upload_confirmation:
            errors.append("upload confirmation must include the session id")
        if self.session_id and self.session_id not in self.exact_certification_confirmation:
            errors.append("certification confirmation must include the session id")
        if "official correction upload" not in self.exact_upload_confirmation.lower():
            errors.append("upload confirmation must name official correction upload")
        if "certify correction upload" not in self.exact_certification_confirmation.lower():
            errors.append("certification confirmation must name certify correction upload")
        return errors


@dataclass(frozen=True)
class CorrectionReviewRequest:
    action: CorrectionReviewAction
    session_id: str
    user_confirmation: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CorrectionReviewRequest":
        return cls(
            action=CorrectionReviewAction(str(data.get("action", ""))),
            session_id=str(data.get("sessionId", data.get("session_id", ""))),
            user_confirmation=_optional_string(data.get("userConfirmation", data.get("user_confirmation"))),
        )


@dataclass(frozen=True)
class CorrectionReviewGuardrailResult:
    allowed: bool
    decision: CorrectionReviewDecision
    reasons: tuple[str, ...]
    action_preview: tuple[str, ...]
    executed_browser_actions: tuple[str, ...] = ()


def evaluate_correction_upload_review(
    state: CorrectionUploadReviewState,
    request: CorrectionReviewRequest,
) -> CorrectionReviewGuardrailResult:
    """Evaluate a fixture-backed correction-upload review request.

    Preview is read-only and can be allowed for a valid redacted review state.
    Official upload and certification are consequential actions and require the
    exact confirmation phrase bound to the same session id.
    """

    validation_errors = state.validate()
    if validation_errors:
        private_value_errors = [error for error in validation_errors if "redacted" in error]
        decision = (
            CorrectionReviewDecision.REFUSE_PRIVATE_VALUE_RISK
            if private_value_errors
            else CorrectionReviewDecision.REFUSE_INVALID_REVIEW_STATE
        )
        return CorrectionReviewGuardrailResult(
            allowed=False,
            decision=decision,
            reasons=tuple(validation_errors),
            action_preview=(),
        )

    if request.session_id != state.session_id:
        return CorrectionReviewGuardrailResult(
            allowed=False,
            decision=CorrectionReviewDecision.REFUSE_MISSING_EXACT_CONFIRMATION,
            reasons=("request session id does not match the reviewed DevHub session",),
            action_preview=_build_preview(state),
        )

    if request.action == CorrectionReviewAction.PREVIEW:
        return CorrectionReviewGuardrailResult(
            allowed=True,
            decision=CorrectionReviewDecision.ALLOW_PREVIEW,
            reasons=("preview is read-only and performs no upload or certification",),
            action_preview=_build_preview(state),
        )

    if request.action == CorrectionReviewAction.OFFICIAL_UPLOAD:
        return _evaluate_exact_confirmation(
            expected=state.exact_upload_confirmation,
            confirmation=request.user_confirmation,
            preview=_build_preview(state),
            action_name="official correction upload",
        )

    if request.action == CorrectionReviewAction.CERTIFICATION:
        return _evaluate_exact_confirmation(
            expected=state.exact_certification_confirmation,
            confirmation=request.user_confirmation,
            preview=_build_preview(state),
            action_name="certification",
        )

    return CorrectionReviewGuardrailResult(
        allowed=False,
        decision=CorrectionReviewDecision.REFUSE_UNKNOWN_ACTION,
        reasons=(f"unknown correction review action {request.action.value}",),
        action_preview=(),
    )


def _evaluate_exact_confirmation(
    expected: str,
    confirmation: Optional[str],
    preview: tuple[str, ...],
    action_name: str,
) -> CorrectionReviewGuardrailResult:
    if confirmation != expected:
        return CorrectionReviewGuardrailResult(
            allowed=False,
            decision=CorrectionReviewDecision.REFUSE_MISSING_EXACT_CONFIRMATION,
            reasons=(f"{action_name} requires the exact session-specific confirmation phrase",),
            action_preview=preview,
        )
    return CorrectionReviewGuardrailResult(
        allowed=True,
        decision=CorrectionReviewDecision.ALLOW_CONFIRMED_CONSEQUENTIAL_ACTION,
        reasons=(f"{action_name} has exact session-specific user confirmation",),
        action_preview=preview,
    )


def _build_preview(state: CorrectionUploadReviewState) -> tuple[str, ...]:
    return (
        f"Review correction-upload draft for {state.permit_reference}",
        f"Check upload control: {state.upload_control_label}",
        f"Accepted file hints: {', '.join(state.accepted_file_hints)}",
        f"Validation messages: {'; '.join(state.validation_messages)}",
        f"Certification gate: {state.certification_label}",
        "No browser upload, certification, submission, payment, or scheduling action is executed by this preview.",
    )


def _optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)
