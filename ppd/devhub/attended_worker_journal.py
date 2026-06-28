from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


REQUIRED_COMPLETION_SEQUENCE = (
    "devhub_attended_preflight",
    "devhub_action_classification",
    "devhub_action_preview",
    "exact_confirmation_checkpoint",
    "post_action_review_evidence",
)

FORBIDDEN_PRIVATE_KEYS = {
    "auth_state",
    "captcha_solution",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "har_path",
    "local_private_file_path",
    "mfa_code",
    "password",
    "payment_details",
    "raw_page_value",
    "screenshot_path",
    "session_file",
    "trace_path",
}

FINAL_OFFICIAL_CLASSIFICATIONS = {
    "consequential_official",
    "financial",
    "unsupported_manual_handoff",
}

PROHIBITED_AUTOMATED_FINAL_ACTIONS = {
    "account_creation",
    "captcha",
    "certification",
    "final_payment_execution",
    "mfa",
    "official_upload",
    "password_recovery",
    "payment_detail_entry",
    "permit_submission",
    "schedule_inspection",
}


@dataclass(frozen=True)
class JournalValidationError(ValueError):
    """Raised when an attended-worker journal cannot support completion."""

    message: str

    def __str__(self) -> str:
        return self.message


def validate_attended_worker_journal_sequence(events: Iterable[dict[str, Any]]) -> None:
    """Validate commit-safe DevHub attended-worker journal ordering.

    The validator is intentionally small and deterministic. It checks only the
    evidence shape needed by PP&D guardrails and does not execute browser work.
    """

    action_state: dict[str, dict[str, Any]] = {}

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise JournalValidationError(f"journal event {index} is not an object")

        _reject_private_keys(event, f"journal event {index}")

        event_type = event.get("event_type")
        if not isinstance(event_type, str) or not event_type:
            raise JournalValidationError(f"journal event {index} is missing event_type")

        action_id = event.get("action_id")
        if action_id is not None and not isinstance(action_id, str):
            raise JournalValidationError(f"journal event {index} has a non-string action_id")

        if action_id:
            state = action_state.setdefault(
                action_id,
                {
                    "seen": set(),
                    "classification": None,
                    "official_intent": None,
                    "automation_mode": None,
                },
            )
            state["seen"].add(event_type)

            if event_type == "devhub_action_classification":
                classification = event.get("classification")
                if not isinstance(classification, str) or not classification:
                    raise JournalValidationError(
                        f"action {action_id} classification event lacks classification"
                    )
                state["classification"] = classification
                state["official_intent"] = event.get("official_intent")
                state["automation_mode"] = event.get("automation_mode")
                _reject_prohibited_automation(action_id, event)

            if event_type == "devhub_action_mark_complete":
                _validate_completion_event(action_id, event, state)


def _validate_completion_event(
    action_id: str, event: dict[str, Any], state: dict[str, Any]
) -> None:
    missing = [
        required
        for required in REQUIRED_COMPLETION_SEQUENCE
        if required not in state["seen"]
    ]
    if missing:
        raise JournalValidationError(
            f"action {action_id} cannot be marked complete; missing {', '.join(missing)}"
        )

    if event.get("completion_evidence") != "user_visible_post_action_review":
        raise JournalValidationError(
            f"action {action_id} completion lacks user-visible post-action review evidence"
        )

    classification = state.get("classification")
    if classification in FINAL_OFFICIAL_CLASSIFICATIONS:
        raise JournalValidationError(
            f"action {action_id} is {classification} and must remain a manual handoff"
        )


def _reject_prohibited_automation(action_id: str, event: dict[str, Any]) -> None:
    official_intent = event.get("official_intent")
    automation_mode = event.get("automation_mode")
    if official_intent in PROHIBITED_AUTOMATED_FINAL_ACTIONS and automation_mode != "manual_handoff_only":
        raise JournalValidationError(
            f"action {action_id} attempts prohibited automation for {official_intent}"
        )


def _reject_private_keys(value: Any, location: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FORBIDDEN_PRIVATE_KEYS:
                raise JournalValidationError(f"{location} contains forbidden private key {key}")
            _reject_private_keys(nested, f"{location}.{key}")
    elif isinstance(value, list):
        for offset, nested in enumerate(value):
            _reject_private_keys(nested, f"{location}[{offset}]")
