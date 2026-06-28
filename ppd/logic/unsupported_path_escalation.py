"""Evaluate PP&D permit processes that must not be automated in DevHub.

The helpers in this module are intentionally fixture-friendly and side-effect free.
They turn source-grounded unsupported path guidance into a blocked action response
that an agent can show to a user before attempting DevHub draft automation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


UNSUPPORTED_ROUTE_TYPES = {"email", "manual_review", "non_devhub", "other_portal"}
DEVHUB_DRAFT_ACTIONS = {"devhub_draft_application", "devhub_draft_automation", "create_devhub_draft"}


@dataclass(frozen=True)
class UnsupportedPathDecision:
    """A deterministic decision for an unsupported PP&D process path."""

    action: str
    blocked: bool
    user_visible_reason: str
    source_evidence_ids: tuple[str, ...]
    manual_handoff_recommendations: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    next_safe_actions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "blocked": self.blocked,
            "user_visible_reason": self.user_visible_reason,
            "source_evidence_ids": list(self.source_evidence_ids),
            "manual_handoff_recommendations": list(self.manual_handoff_recommendations),
            "blocked_actions": list(self.blocked_actions),
            "next_safe_actions": list(self.next_safe_actions),
        }


def evaluate_unsupported_path_escalation(
    process_model: Mapping[str, Any], requested_action: str
) -> UnsupportedPathDecision:
    """Return a blocked manual-handoff decision for official non-DevHub paths.

    ``process_model`` is expected to contain an ``unsupported_paths`` list. Each
    path may identify a ``route_type`` of ``email``, ``manual_review``,
    ``non_devhub``, or ``other_portal`` and should include source evidence ids.
    The function is conservative: only DevHub draft actions are blocked here,
    and only when the unsupported path is explicitly source-backed.
    """

    unsupported_path = _first_source_backed_unsupported_path(process_model)
    if requested_action not in DEVHUB_DRAFT_ACTIONS or unsupported_path is None:
        return UnsupportedPathDecision(
            action=requested_action,
            blocked=False,
            user_visible_reason="No source-backed unsupported path blocks this action.",
            source_evidence_ids=(),
            manual_handoff_recommendations=(),
            blocked_actions=(),
            next_safe_actions=("continue_guardrail_evaluation",),
        )

    permit_type = str(process_model.get("permit_type", "this permit process"))
    route_label = str(unsupported_path.get("route_label") or unsupported_path.get("route_type"))
    reason = str(
        unsupported_path.get("user_visible_reason")
        or f"Official PP&D guidance routes {permit_type} through {route_label}, not DevHub draft automation."
    )
    recommendations = _tuple_of_strings(
        unsupported_path.get("manual_handoff_recommendations")
        or unsupported_path.get("handoff_recommendations")
    )
    if not recommendations:
        recommendations = (
            "Do not create a DevHub draft for this process.",
            "Show the cited official guidance to the user and hand off the listed email or manual review instructions.",
        )

    return UnsupportedPathDecision(
        action=requested_action,
        blocked=True,
        user_visible_reason=reason,
        source_evidence_ids=_tuple_of_strings(unsupported_path.get("source_evidence_ids")),
        manual_handoff_recommendations=recommendations,
        blocked_actions=(requested_action,),
        next_safe_actions=("manual_handoff", "show_source_evidence"),
    )


def _first_source_backed_unsupported_path(process_model: Mapping[str, Any]) -> Mapping[str, Any] | None:
    unsupported_paths = process_model.get("unsupported_paths")
    if not isinstance(unsupported_paths, list):
        return None

    for path in unsupported_paths:
        if not isinstance(path, Mapping):
            continue
        route_type = path.get("route_type")
        evidence_ids = _tuple_of_strings(path.get("source_evidence_ids"))
        if route_type in UNSUPPORTED_ROUTE_TYPES and evidence_ids:
            return path
    return None


def _tuple_of_strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)
