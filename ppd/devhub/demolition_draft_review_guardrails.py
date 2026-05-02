"""Fixture-only guardrails for DevHub demolition draft review actions.

This module models the narrow action gate needed by tests: a demolition
application draft review may produce a preview without user confirmation, but
DevHub actions with official consequences require an exact confirmation phrase
that is scoped to both the current session and the exact action.
"""

from __future__ import annotations

from typing import Any, Mapping

PREVIEW_ACTION = "preview_draft_review"
GUARDED_ACTIONS = frozenset(
    {
        "official_upload",
        "certify_application",
        "submit_application",
        "pay_fees",
        "cancel_application",
        "schedule_inspection",
    }
)


def required_confirmation_phrase(session_id: str, action_id: str) -> str:
    """Return the exact confirmation phrase for a session-scoped action."""

    return f"CONFIRM {session_id} {action_id}"


def review_action(action: Mapping[str, Any], session_id: str) -> dict[str, Any]:
    """Classify whether a fixture action may proceed.

    The result is intentionally serializable so tests and later guardrail
    compilers can compare outcomes without needing browser state.
    """

    action_id = str(action.get("actionId", ""))
    confirmation = str(action.get("userConfirmation", ""))

    if action_id == PREVIEW_ACTION:
        return {
            "actionId": action_id,
            "allowed": True,
            "decision": "preview_allowed",
            "requiresConfirmation": False,
            "requiredConfirmation": "",
        }

    if action_id not in GUARDED_ACTIONS:
        return {
            "actionId": action_id,
            "allowed": False,
            "decision": "unknown_action_refused",
            "requiresConfirmation": True,
            "requiredConfirmation": "",
        }

    required = required_confirmation_phrase(session_id, action_id)
    if confirmation == required:
        return {
            "actionId": action_id,
            "allowed": True,
            "decision": "exact_session_confirmation_present",
            "requiresConfirmation": True,
            "requiredConfirmation": required,
        }

    return {
        "actionId": action_id,
        "allowed": False,
        "decision": "exact_session_confirmation_missing",
        "requiresConfirmation": True,
        "requiredConfirmation": required,
    }


def validate_demolition_draft_review_fixture(fixture: Mapping[str, Any]) -> list[str]:
    """Validate a demolition draft-review guardrail fixture."""

    errors: list[str] = []
    session_id = str(fixture.get("sessionId", ""))
    permit_type = str(fixture.get("permitType", ""))
    actions = fixture.get("actions", [])

    if not session_id.startswith("fixture-session-"):
        errors.append("sessionId must be a redacted fixture session identifier")
    if permit_type != "demolition_application":
        errors.append("permitType must be demolition_application")
    if not isinstance(actions, list) or not actions:
        errors.append("actions must be a non-empty list")
        return errors

    seen_preview = False
    seen_guarded = set()
    for index, action in enumerate(actions):
        if not isinstance(action, Mapping):
            errors.append(f"actions[{index}] must be an object")
            continue
        action_id = str(action.get("actionId", ""))
        result = review_action(action, session_id)
        if action_id == PREVIEW_ACTION:
            seen_preview = True
            if not result["allowed"]:
                errors.append("preview_draft_review must be allowed without confirmation")
        elif action_id in GUARDED_ACTIONS:
            seen_guarded.add(action_id)
            if result["allowed"]:
                errors.append(f"{action_id} fixture case must demonstrate refusal without exact confirmation")
        else:
            errors.append(f"unknown actionId {action_id}")

    missing_guarded = sorted(GUARDED_ACTIONS.difference(seen_guarded))
    if not seen_preview:
        errors.append("fixture must include preview_draft_review")
    if missing_guarded:
        errors.append(f"fixture missing guarded actions: {', '.join(missing_guarded)}")

    return errors
