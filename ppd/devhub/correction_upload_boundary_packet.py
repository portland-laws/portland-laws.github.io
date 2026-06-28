"""Fixture-first correction upload boundary packet validation.

This module intentionally stays side-effect free. It validates committed synthetic
packets that describe what an agent may review locally and what must be handed
off to an attended user in DevHub.
"""

from __future__ import annotations

from typing import Any, Mapping

SAFE_BOUNDARIES = {
    "read_only_correction_review",
    "local_document_checklist_preview",
}

BLOCKED_BOUNDARIES = {
    "official_correction_upload",
    "certification_or_submission",
}

REQUIRED_PACKET_FIELDS = {
    "packet_id",
    "case_id",
    "workflow",
    "synthetic_checksheet",
    "boundaries",
    "manual_handoff",
    "next_safe_actions",
    "source_evidence",
}


def _as_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return value


def _as_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    return value


def validate_correction_upload_boundary_packet(packet: Mapping[str, Any]) -> None:
    """Validate a synthetic correction-upload boundary packet.

    The validation is deliberately narrow: it verifies that the packet separates
    local/read-only assistance from blocked official DevHub actions and that each
    proposed next safe action is backed by source evidence.
    """

    missing_fields = sorted(REQUIRED_PACKET_FIELDS.difference(packet))
    if missing_fields:
        raise ValueError(f"packet missing required fields: {', '.join(missing_fields)}")

    workflow = _as_mapping(packet["workflow"], "workflow")
    if workflow.get("surface") != "DevHub correction upload":
        raise ValueError("workflow.surface must identify DevHub correction upload")
    if workflow.get("mode") != "fixture_only":
        raise ValueError("workflow.mode must be fixture_only")
    if workflow.get("authenticated_automation") is not False:
        raise ValueError("authenticated_automation must be false")

    checksheet = _as_mapping(packet["synthetic_checksheet"], "synthetic_checksheet")
    review_items = _as_list(checksheet.get("review_items"), "synthetic_checksheet.review_items")
    if not review_items:
        raise ValueError("synthetic_checksheet.review_items must not be empty")
    for index, item in enumerate(review_items):
        item_map = _as_mapping(item, f"synthetic_checksheet.review_items[{index}]")
        if not item_map.get("checksheet_item_id"):
            raise ValueError("each checksheet review item needs a checksheet_item_id")
        if not item_map.get("requested_correction"):
            raise ValueError("each checksheet review item needs requested_correction text")

    boundaries = _as_list(packet["boundaries"], "boundaries")
    boundary_by_kind: dict[str, Mapping[str, Any]] = {}
    for index, boundary in enumerate(boundaries):
        boundary_map = _as_mapping(boundary, f"boundaries[{index}]")
        kind = boundary_map.get("kind")
        if not isinstance(kind, str):
            raise ValueError("each boundary needs a string kind")
        boundary_by_kind[kind] = boundary_map

        decision = boundary_map.get("decision")
        if kind in SAFE_BOUNDARIES and decision != "allowed_local_only":
            raise ValueError(f"{kind} must be allowed_local_only")
        if kind in BLOCKED_BOUNDARIES and decision != "blocked_requires_attended_user":
            raise ValueError(f"{kind} must be blocked_requires_attended_user")
        if kind in BLOCKED_BOUNDARIES and not boundary_map.get("manual_handoff_required"):
            raise ValueError(f"{kind} must require manual handoff")
        if not boundary_map.get("citation_ids"):
            raise ValueError(f"{kind} must include citation_ids")

    missing_boundaries = sorted(SAFE_BOUNDARIES.union(BLOCKED_BOUNDARIES).difference(boundary_by_kind))
    if missing_boundaries:
        raise ValueError(f"packet missing boundary kinds: {', '.join(missing_boundaries)}")

    source_evidence = _as_list(packet["source_evidence"], "source_evidence")
    citation_ids = {evidence.get("citation_id") for evidence in source_evidence if isinstance(evidence, dict)}
    if not citation_ids:
        raise ValueError("source_evidence must contain citation_id values")

    for kind, boundary in boundary_by_kind.items():
        for citation_id in _as_list(boundary.get("citation_ids"), f"{kind}.citation_ids"):
            if citation_id not in citation_ids:
                raise ValueError(f"{kind} cites unknown source evidence {citation_id}")

    next_safe_actions = _as_list(packet["next_safe_actions"], "next_safe_actions")
    if not next_safe_actions:
        raise ValueError("next_safe_actions must not be empty")
    for index, action in enumerate(next_safe_actions):
        action_map = _as_mapping(action, f"next_safe_actions[{index}]")
        if action_map.get("requires_devhub_login") is not False:
            raise ValueError("next safe actions must not require DevHub login")
        if action_map.get("changes_official_record") is not False:
            raise ValueError("next safe actions must not change the official record")
        action_citations = _as_list(action_map.get("citation_ids"), f"next_safe_actions[{index}].citation_ids")
        if not action_citations:
            raise ValueError("next safe actions must cite source evidence")
        unknown = [citation_id for citation_id in action_citations if citation_id not in citation_ids]
        if unknown:
            raise ValueError(f"next safe action cites unknown source evidence: {', '.join(unknown)}")

    manual_handoff = _as_mapping(packet["manual_handoff"], "manual_handoff")
    handoff_text = manual_handoff.get("text")
    if not isinstance(handoff_text, str) or "upload" not in handoff_text.lower():
        raise ValueError("manual_handoff.text must explain the upload handoff")
    if manual_handoff.get("agent_may_click_upload") is not False:
        raise ValueError("manual handoff must prohibit agent upload clicks")
    if manual_handoff.get("agent_may_certify_or_submit") is not False:
        raise ValueError("manual handoff must prohibit certification or submission")
