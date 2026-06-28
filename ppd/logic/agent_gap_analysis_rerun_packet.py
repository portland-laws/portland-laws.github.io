from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ppd.logic.guardrail_regeneration_candidate import compile_guardrail_regeneration_candidate
from ppd.logic.user_gap_analysis import analyze_user_gaps

PRIVATE_PATH_MARKERS = ("/home/", "/Users/", "C:\\Users\\", "devhub/session", "auth_state", "trace.zip", ".har")
DEVHUB_LAUNCH_KEYS = ("launch_devhub", "open_browser", "playwright_enabled", "authenticated_session")
MANUAL_HANDOFF_KEYWORDS = ("captcha", "mfa", "payment", "pay", "schedule", "submit", "upload", "certify", "acknowledge", "cancel", "purchase")
LOCAL_PREVIEW_ACTIONS = ("render_local_pdf_field_mapping_preview", "preview_missing_fact_question_list", "preview_reversible_draft_plan")


def compile_agent_gap_analysis_rerun_packet(packet_input: Mapping[str, Any]) -> dict[str, Any]:
    """Compile a fixture-only gap-analysis rerun packet for one synthetic PP&D case."""

    _reject_private_or_live_inputs(packet_input)

    process_model_change = _mapping(packet_input.get("process_model_change"))
    synthetic_case = _mapping(packet_input.get("synthetic_case"))
    requested_actions = _string_list(synthetic_case.get("requested_actions"))
    known_facts = _mapping(synthetic_case.get("known_facts"))
    user_documents = _sequence_of_mappings(synthetic_case.get("user_documents"))

    candidate = compile_guardrail_regeneration_candidate(process_model_change)
    process_id = str(process_model_change.get("process_id") or "unknown_process")
    before_model = {"process_id": process_id, **_mapping(process_model_change.get("before"))}
    after_model = {"process_id": process_id, **_mapping(process_model_change.get("after"))}
    case_id = str(synthetic_case.get("case_id") or "synthetic_case")

    baseline = analyze_user_gaps(
        case_id=case_id,
        process_model=before_model,
        known_facts=known_facts,
        user_documents=user_documents,
        requested_actions=requested_actions,
    ).to_dict()
    rerun = analyze_user_gaps(
        case_id=case_id,
        process_model=after_model,
        known_facts=known_facts,
        user_documents=user_documents,
        requested_actions=requested_actions,
    ).to_dict()

    changed_missing_facts = _changed_values(baseline["missing_facts"], rerun["missing_facts"])
    blocked_actions = _merge_blocked_actions(rerun["blocked_actions"], candidate["refused_action_predicates"])

    return {
        "packet_id": "agent-gap-analysis-rerun-" + case_id,
        "packet_status": "fixture_only_no_private_file_reads_no_devhub_launch",
        "case_id": case_id,
        "process_id": process_id,
        "guardrail_candidate": {
            "candidate_id": candidate["candidate_id"],
            "candidate_status": candidate["candidate_status"],
            "does_not_replace_active_bundle": candidate["does_not_replace_active_bundle"],
            "active_guardrail_bundle_id": candidate["active_guardrail_bundle_id"],
            "source_evidence_ids": list(candidate["source_evidence_ids"]),
        },
        "baseline_missing_facts": list(baseline["missing_facts"]),
        "rerun_missing_facts": list(rerun["missing_facts"]),
        "changed_missing_facts": changed_missing_facts,
        "missing_documents": list(rerun["missing_documents"]),
        "stale_evidence": list(rerun["stale_evidence"]),
        "conflicting_evidence": list(rerun["conflicting_evidence"]),
        "blocked_actions": blocked_actions,
        "manual_handoffs": _manual_handoffs(blocked_actions, requested_actions),
        "allowed_local_previews": _allowed_local_previews(rerun, candidate),
        "user_facing_questions": _user_questions(changed_missing_facts["added"], rerun["missing_documents"], rerun["stale_evidence"]),
        "privacy_and_execution_limits": {
            "reads_private_files": False,
            "launches_devhub": False,
            "uses_authenticated_session": False,
            "stores_raw_user_documents": False,
        },
    }


def _changed_values(before: Sequence[str], after: Sequence[str]) -> dict[str, list[str]]:
    before_set = set(before)
    after_set = set(after)
    return {"added": sorted(after_set - before_set), "removed": sorted(before_set - after_set), "unchanged": sorted(before_set & after_set)}


def _merge_blocked_actions(blocked_actions: Sequence[Mapping[str, Any]], refused_predicates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for action in blocked_actions:
        action_id = str(action.get("action_id") or action.get("action") or "")
        if action_id:
            merged[action_id] = {
                "action_id": action_id,
                "reason": str(action.get("reason") or "Consequential PP&D action is blocked."),
                "requires_attendance": bool(action.get("requires_attendance", True)),
                "requires_exact_confirmation": bool(action.get("requires_exact_confirmation", True)),
                "source": "gap_analysis",
            }
    for predicate in refused_predicates:
        action_id = str(predicate.get("action") or "")
        if action_id:
            merged[action_id] = {
                "action_id": action_id,
                "reason": str(predicate.get("refusal_reason") or "Draft guardrail candidate refuses this action until attended confirmation."),
                "requires_attendance": True,
                "requires_exact_confirmation": True,
                "source": "draft_guardrail_candidate",
            }
    return [merged[action_id] for action_id in sorted(merged)]


def _manual_handoffs(blocked_actions: Sequence[Mapping[str, Any]], requested_actions: Sequence[str]) -> list[dict[str, Any]]:
    handoff_ids = {str(action.get("action_id") or "") for action in blocked_actions}
    handoff_ids.update(action for action in requested_actions if _is_manual_handoff(action))
    return [
        {
            "handoff_id": action_id,
            "reason": "User attendance is required before this PP&D or account-scoped action can continue.",
            "agent_may_continue_locally": True,
        }
        for action_id in sorted(handoff_ids)
        if action_id
    ]


def _allowed_local_previews(rerun: Mapping[str, Any], candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    previews = [
        {"action_id": action_id, "allowed": True, "requires_devhub": False, "requires_private_file_read": False, "basis": "local_preview_only"}
        for action_id in LOCAL_PREVIEW_ACTIONS
    ]
    if candidate.get("draft_predicates"):
        previews.append({"action_id": "preview_draft_guardrail_explanations", "allowed": True, "requires_devhub": False, "requires_private_file_read": False, "basis": "draft_candidate_review_only"})
    if not rerun.get("missing_facts") and not rerun.get("missing_documents"):
        previews.append({"action_id": "prepare_reversible_form_draft_values", "allowed": True, "requires_devhub": False, "requires_private_file_read": False, "basis": "gap_analysis_complete_for_reversible_draft"})
    return previews


def _user_questions(missing_facts: Sequence[str], missing_documents: Sequence[str], stale_evidence: Sequence[str]) -> list[dict[str, str]]:
    questions: list[dict[str, str]] = []
    for fact_id in missing_facts:
        questions.append({"question_id": "missing_fact." + fact_id, "question": "Please provide the PP&D case fact: " + fact_id.replace("_", " ") + ".", "reason": "The draft guardrail candidate made this fact required for the rerun."})
    for document_id in missing_documents:
        questions.append({"question_id": "missing_document." + document_id, "question": "Do you have a current document for " + document_id.replace("_", " ") + "?", "reason": "The synthetic document inventory did not include a matching metadata record."})
    for evidence_id in stale_evidence:
        questions.append({"question_id": "stale_evidence." + evidence_id, "question": "Is " + evidence_id.replace("_", " ") + " still current for this permit case?", "reason": "The fixture marks this fact or document as stale, so the agent should not rely on it silently."})
    return questions


def _reject_private_or_live_inputs(value: Any) -> None:
    for key, nested in _walk(value):
        if key in DEVHUB_LAUNCH_KEYS and nested is True:
            raise ValueError("rerun packet fixtures must not request DevHub launch or authenticated automation")
        if isinstance(nested, str) and any(marker in nested for marker in PRIVATE_PATH_MARKERS):
            raise ValueError("rerun packet fixtures must not include private local paths or session artifacts")


def _walk(value: Any, key: str = "") -> list[tuple[str, Any]]:
    items = [(key, value)]
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            items.extend(_walk(child_value, str(child_key)))
    elif isinstance(value, list):
        for child in value:
            items.extend(_walk(child, key))
    return items


def _is_manual_handoff(action_id: str) -> bool:
    normalized = action_id.replace("-", "_").lower()
    return any(keyword in normalized for keyword in MANUAL_HANDOFF_KEYWORDS)


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _sequence_of_mappings(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if not isinstance(value, Sequence):
        return []
    return [str(item) for item in value if str(item)]
