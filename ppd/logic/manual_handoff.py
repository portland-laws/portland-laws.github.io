"""Manual handoff planning for PP&D process models.

This module is intentionally small and fixture-friendly. It gives tests and future
callers a deterministic way to turn process-model unsupported paths into
agent-facing next-safe-action records without invoking DevHub automation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


MANUAL_HANDOFF_ACTION_TYPE = "manual_handoff"
DEVHUB_AUTOMATION_ACTION_TYPE = "devhub_automation"


@dataclass(frozen=True)
class ManualHandoffReason:
    """A normalized unsupported/manual permit-path reason from a process model."""

    path_id: str
    permit_path: str
    reason: str
    required_channel: str
    source_evidence_ids: tuple[str, ...]


def _string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return tuple(str(item) for item in value)
    return (str(value),)


def manual_handoff_reasons(process_model: Mapping[str, Any]) -> tuple[ManualHandoffReason, ...]:
    """Return normalized handoff reasons declared by a PP&D process model."""

    reasons: list[ManualHandoffReason] = []
    for index, item in enumerate(process_model.get("unsupported_paths", ())):
        if not isinstance(item, Mapping):
            continue
        path_id = str(item.get("path_id") or f"unsupported_path_{index + 1}")
        permit_path = str(item.get("permit_path") or item.get("permit_type") or "unspecified permit path")
        reason = str(item.get("reason") or "This permit path is not supported for DevHub automation.")
        required_channel = str(item.get("required_channel") or "manual")
        source_evidence_ids = _string_tuple(item.get("source_evidence_ids"))
        reasons.append(
            ManualHandoffReason(
                path_id=path_id,
                permit_path=permit_path,
                reason=reason,
                required_channel=required_channel,
                source_evidence_ids=source_evidence_ids,
            )
        )
    return tuple(reasons)


def next_safe_actions(process_model: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Build next-safe-action records for a process model.

    Unsupported paths always produce manual handoff actions. The function avoids
    proposing DevHub automation for these paths even when the model also contains
    DevHub surface references.
    """

    handoff_reasons = manual_handoff_reasons(process_model)
    if handoff_reasons:
        return [
            {
                "action_type": MANUAL_HANDOFF_ACTION_TYPE,
                "action_id": f"manual_handoff:{reason.path_id}",
                "permit_path": reason.permit_path,
                "summary": "Hand off this permit path for manual handling.",
                "reason": reason.reason,
                "required_channel": reason.required_channel,
                "blocked_action_types": [DEVHUB_AUTOMATION_ACTION_TYPE],
                "requires_user_attendance": True,
                "requires_exact_confirmation": False,
                "source_evidence_ids": list(reason.source_evidence_ids),
            }
            for reason in handoff_reasons
        ]

    return [
        {
            "action_type": DEVHUB_AUTOMATION_ACTION_TYPE,
            "action_id": "devhub_automation:preflight",
            "summary": "Run DevHub attended preflight before any reversible draft work.",
            "requires_user_attendance": True,
            "requires_exact_confirmation": False,
            "source_evidence_ids": list(_string_tuple(process_model.get("source_evidence_ids"))),
        }
    ]


def assert_no_devhub_automation_for_unsupported_paths(process_model: Mapping[str, Any]) -> None:
    """Raise AssertionError if unsupported paths produce DevHub automation."""

    if not manual_handoff_reasons(process_model):
        return
    actions = next_safe_actions(process_model)
    automated = [action for action in actions if action.get("action_type") == DEVHUB_AUTOMATION_ACTION_TYPE]
    if automated:
        action_ids = ", ".join(str(action.get("action_id")) for action in automated)
        raise AssertionError(f"unsupported paths must not produce DevHub automation: {action_ids}")
