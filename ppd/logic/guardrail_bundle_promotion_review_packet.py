"""Fixture-first guardrail bundle promotion review packet builder.

The packet produced here is a review artifact only. It records draft bundle diffs,
source citations, regression rerun consequences, blocked actions, exact-confirmation
gates, reviewer prompts, and rollback notes without emitting replacement active
bundle content or mutating the supplied candidate inputs.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any


DRAFT_FIX_GROUPS = (
    "draft_predicate_fixes",
    "draft_explanation_template_fixes",
    "draft_refused_action_rule_fixes",
    "draft_exact_confirmation_gate_fixes",
)

PRIVATE_FIELD_NAMES = {
    "auth_state",
    "authorization",
    "cookie",
    "credentials",
    "devhub_session",
    "password",
    "payment_details",
    "private_file",
    "private_path",
    "secret",
    "session_state",
    "token",
    "trace",
}

PRIVATE_PATH_MARKERS = (
    "/home/",
    "/Users/",
    "C:/Users/",
    "file://",
    "devhub/session",
    "auth_state",
    ".har",
    "trace.zip",
)

LIVE_EXECUTION_KEYS = {
    "call_llm",
    "calls_llm",
    "execute_live_devhub",
    "launch_devhub",
    "launches_devhub",
    "open_browser",
    "playwright_enabled",
    "read_private_files",
    "reads_private_files",
    "uses_authenticated_session",
    "uses_devhub",
    "writes_private_artifacts",
}

CONSEQUENTIAL_ACTION_TERMS = (
    "acknowledge",
    "cancel",
    "certify",
    "payment",
    "purchase",
    "schedule",
    "submit",
    "upload",
    "withdraw",
)


class GuardrailBundlePromotionReviewPacketError(ValueError):
    """Raised when a promotion review packet fixture is malformed."""


def build_guardrail_bundle_promotion_review_packet(packet_input: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic, fixture-only bundle promotion review packet."""

    _reject_private_or_live_inputs(packet_input)
    remediation_candidate = _mapping(packet_input, "stale_predicate_remediation_candidate")
    rerun_plan = _mapping(packet_input, "agent_regression_rerun_plan")
    original_candidate = deepcopy(remediation_candidate)
    original_plan = deepcopy(rerun_plan)

    draft_bundle_diffs = _draft_bundle_diffs(remediation_candidate)
    source_citations = _source_evidence_citations(remediation_candidate, rerun_plan)
    blocked_actions = _blocked_consequential_actions(remediation_candidate, rerun_plan)
    exact_gates = _exact_confirmation_gates(remediation_candidate, blocked_actions)
    reviewer_prompts = _reviewer_prompts(remediation_candidate, rerun_plan, draft_bundle_diffs, blocked_actions)

    packet = {
        "packet_id": str(packet_input.get("packet_id") or "guardrail-bundle-promotion-review-" + _stable_hash({"candidate": remediation_candidate, "rerun_plan": rerun_plan})),
        "packet_status": "draft_review_required_no_active_bundle_mutation",
        "packet_mode": "fixture_first_promotion_review_only",
        "candidate_id": _text(remediation_candidate.get("candidate_id")) or _text(remediation_candidate.get("packet_id")),
        "active_guardrail_bundle_id": _required_text(remediation_candidate, "active_guardrail_bundle_id"),
        "does_not_replace_active_bundle": True,
        "active_bundle_mutated": False,
        "promotion_decision": "blocked_pending_human_review",
        "draft_bundle_diffs": draft_bundle_diffs,
        "source_evidence_citations": source_citations,
        "blocked_consequential_actions": blocked_actions,
        "exact_confirmation_gates": exact_gates,
        "reviewer_prompts": reviewer_prompts,
        "rollback_notes": _rollback_notes(remediation_candidate, rerun_plan, draft_bundle_diffs),
        "execution_boundaries": {
            "calls_llm": False,
            "launches_devhub": False,
            "uses_authenticated_session": False,
            "reads_private_files": False,
            "writes_private_artifacts": False,
            "mutates_active_bundles": False,
            "source": "committed PP&D fixtures only",
        },
    }

    if remediation_candidate != original_candidate:
        raise GuardrailBundlePromotionReviewPacketError("stale predicate remediation candidate input was mutated")
    if rerun_plan != original_plan:
        raise GuardrailBundlePromotionReviewPacketError("agent regression rerun plan input was mutated")

    errors = validate_guardrail_bundle_promotion_review_packet(packet)
    if errors:
        raise GuardrailBundlePromotionReviewPacketError("; ".join(errors))
    return packet


def validate_guardrail_bundle_promotion_review_packet(packet: Mapping[str, Any]) -> list[str]:
    """Return validation errors for a review-only promotion packet."""

    errors: list[str] = []
    try:
        _reject_private_or_live_inputs(packet)
    except GuardrailBundlePromotionReviewPacketError as exc:
        errors.append(str(exc))

    if packet.get("packet_status") != "draft_review_required_no_active_bundle_mutation":
        errors.append("packet status must keep promotion in draft review")
    if packet.get("does_not_replace_active_bundle") is not True:
        errors.append("packet must not replace active bundle")
    if packet.get("active_bundle_mutated") is not False:
        errors.append("packet must record active_bundle_mutated false")
    if "active_guardrail_bundle" in packet:
        errors.append("packet must not include active bundle replacement content")
    if packet.get("promotion_decision") != "blocked_pending_human_review":
        errors.append("promotion decision must remain blocked pending human review")

    for index, diff in enumerate(_sequence_of_mappings(packet.get("draft_bundle_diffs"))):
        if not _string_list(diff.get("source_evidence_ids")):
            errors.append(f"draft bundle diff is uncited: draft_bundle_diffs[{index}]")
        if diff.get("mutates_active_bundle") is not False:
            errors.append(f"draft bundle diff mutates active bundle: draft_bundle_diffs[{index}]")
        if diff.get("review_status") != "draft_requires_human_review":
            errors.append(f"draft bundle diff must require human review: draft_bundle_diffs[{index}]")

    cited_ids = {citation["evidence_id"] for citation in _sequence_of_mappings(packet.get("source_evidence_citations")) if _text(citation.get("evidence_id"))}
    if not cited_ids:
        errors.append("packet must include source evidence citations")
    for index, citation in enumerate(_sequence_of_mappings(packet.get("source_evidence_citations"))):
        if not _text(citation.get("canonical_url")) and not _text(citation.get("source_id")):
            errors.append(f"source evidence citation lacks source locator: source_evidence_citations[{index}]")

    exact_gate_actions = {_normalize_action(gate.get("action_id") or gate.get("action")) for gate in _sequence_of_mappings(packet.get("exact_confirmation_gates"))}
    for index, action in enumerate(_sequence_of_mappings(packet.get("blocked_consequential_actions"))):
        action_id = _text(action.get("action_id"))
        if not action_id:
            errors.append(f"blocked action lacks action_id: blocked_consequential_actions[{index}]")
            continue
        if _is_consequential_action(action_id):
            if action.get("requires_attendance") is not True:
                errors.append(f"consequential action must require attendance: {action_id}")
            if action.get("requires_exact_confirmation") is not True:
                errors.append(f"consequential action must require exact confirmation: {action_id}")
            if _normalize_action(action_id) not in exact_gate_actions:
                errors.append(f"consequential action lacks exact confirmation gate: {action_id}")
        if not _string_list(action.get("source_evidence_ids")):
            errors.append(f"blocked action is uncited: {action_id}")

    if not _sequence_of_mappings(packet.get("reviewer_prompts")):
        errors.append("packet must include reviewer prompts")
    if not _sequence_of_mappings(packet.get("rollback_notes")):
        errors.append("packet must include rollback notes")

    boundaries = packet.get("execution_boundaries")
    if not isinstance(boundaries, Mapping):
        errors.append("packet must include execution boundaries")
    else:
        for key in ("calls_llm", "launches_devhub", "uses_authenticated_session", "reads_private_files", "writes_private_artifacts", "mutates_active_bundles"):
            if boundaries.get(key) is not False:
                errors.append("execution boundary is not explicitly disabled: " + key)

    return errors


def _draft_bundle_diffs(candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    diffs: list[dict[str, Any]] = []
    for group_name in DRAFT_FIX_GROUPS:
        for fix in _sequence_of_mappings(candidate.get(group_name)):
            target_group = _required_text(fix, "target_group")
            target_item_id = _required_text(fix, "target_item_id")
            diffs.append(
                {
                    "diff_id": "draft-diff." + target_group + "." + target_item_id,
                    "fix_id": _required_text(fix, "fix_id"),
                    "target_group": target_group,
                    "target_item_id": target_item_id,
                    "review_status": "draft_requires_human_review",
                    "source_evidence_ids": sorted(_string_list(fix.get("source_evidence_ids"))),
                    "normalized_citation_evidence": list(_sequence_of_mappings(fix.get("normalized_citation_evidence"))),
                    "proposed_change": dict(_mapping_value(fix.get("draft_fix"))),
                    "mutates_active_bundle": False,
                }
            )
    return sorted(diffs, key=lambda item: item["diff_id"])


def _source_evidence_citations(candidate: Mapping[str, Any], rerun_plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    citations: dict[str, dict[str, Any]] = {}

    for group_name in DRAFT_FIX_GROUPS:
        for fix in _sequence_of_mappings(candidate.get(group_name)):
            for evidence in _sequence_of_mappings(fix.get("normalized_citation_evidence")):
                evidence_id = _required_text(evidence, "evidence_id")
                citations[evidence_id] = {
                    "evidence_id": evidence_id,
                    "source_id": _text(evidence.get("source_id")),
                    "canonical_url": _text(evidence.get("canonical_url")),
                    "citation_span_id": _text(evidence.get("citation_span_id")),
                    "normalized_claim": _text(evidence.get("normalized_claim")),
                    "used_by": ["draft_bundle_diff"],
                }

    for evidence_id in _string_list(candidate.get("source_evidence_ids")):
        citations.setdefault(
            evidence_id,
            {
                "evidence_id": evidence_id,
                "source_id": evidence_id.split("#", 1)[0],
                "canonical_url": "",
                "citation_span_id": evidence_id.split("#", 1)[1] if "#" in evidence_id else "",
                "normalized_claim": "Source evidence carried by stale-predicate remediation candidate.",
                "used_by": ["stale_predicate_remediation_candidate"],
            },
        )

    for case in _sequence_of_mappings(rerun_plan.get("selected_cases")):
        for group_name in ("expected_allowed_prompts", "refused_actions", "manual_handoffs"):
            for outcome in _sequence_of_mappings(case.get(group_name)):
                for evidence_id in _string_list(outcome.get("source_evidence_ids")):
                    citation = citations.setdefault(
                        evidence_id,
                        {
                            "evidence_id": evidence_id,
                            "source_id": evidence_id.split("#", 1)[0],
                            "canonical_url": "",
                            "citation_span_id": evidence_id.split("#", 1)[1] if "#" in evidence_id else "",
                            "normalized_claim": "Source evidence carried by agent regression rerun plan.",
                            "used_by": [],
                        },
                    )
                    if "agent_regression_rerun_plan" not in citation["used_by"]:
                        citation["used_by"].append("agent_regression_rerun_plan")

    return [citations[evidence_id] for evidence_id in sorted(citations)]


def _blocked_consequential_actions(candidate: Mapping[str, Any], rerun_plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    blocked: dict[str, dict[str, Any]] = {}

    for fix in _sequence_of_mappings(candidate.get("draft_refused_action_rule_fixes")):
        draft_fix = _mapping_value(fix.get("draft_fix"))
        action_id = _text(draft_fix.get("action")) or _text(fix.get("target_item_id"))
        if action_id:
            blocked[_normalize_action(action_id)] = {
                "action_id": action_id,
                "reason": _text(draft_fix.get("refusal_reason")) or "Consequential PP&D action remains blocked pending attended review.",
                "requires_attendance": True,
                "requires_exact_confirmation": True,
                "source": "stale_predicate_remediation_candidate",
                "source_evidence_ids": sorted(_string_list(fix.get("source_evidence_ids"))),
            }

    for case in _sequence_of_mappings(rerun_plan.get("selected_cases")):
        for action in _sequence_of_mappings(case.get("refused_actions")):
            action_id = _text(action.get("action_id") or action.get("action"))
            if not action_id:
                continue
            normalized = _normalize_action(action_id)
            existing = blocked.get(normalized, {})
            evidence_ids = sorted(set(_string_list(existing.get("source_evidence_ids"))) | set(_string_list(action.get("source_evidence_ids"))))
            blocked[normalized] = {
                "action_id": action_id,
                "reason": _text(action.get("reason")) or _text(existing.get("reason")) or "Agent regression rerun expects this action to remain blocked.",
                "requires_attendance": True,
                "requires_exact_confirmation": True,
                "source": "agent_regression_rerun_plan",
                "case_ids": sorted(set(_string_list(existing.get("case_ids"))) | {_required_text(case, "case_id")}),
                "source_evidence_ids": evidence_ids,
            }
        for handoff in _sequence_of_mappings(case.get("manual_handoffs")):
            action_id = _text(handoff.get("action_id") or handoff.get("handoff_id") or handoff.get("action"))
            if not action_id or not _is_consequential_action(action_id):
                continue
            normalized = _normalize_action(action_id)
            existing = blocked.get(normalized, {})
            evidence_ids = sorted(set(_string_list(existing.get("source_evidence_ids"))) | set(_string_list(handoff.get("source_evidence_ids"))))
            blocked[normalized] = {
                "action_id": action_id,
                "reason": _text(handoff.get("reason")) or _text(existing.get("reason")) or "Manual handoff remains required for this consequential action.",
                "requires_attendance": True,
                "requires_exact_confirmation": True,
                "source": "agent_regression_rerun_plan_manual_handoff",
                "case_ids": sorted(set(_string_list(existing.get("case_ids"))) | {_required_text(case, "case_id")}),
                "source_evidence_ids": evidence_ids,
            }

    return [blocked[action_id] for action_id in sorted(blocked)]


def _exact_confirmation_gates(candidate: Mapping[str, Any], blocked_actions: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    gates: dict[str, dict[str, Any]] = {}
    for fix in _sequence_of_mappings(candidate.get("draft_exact_confirmation_gate_fixes")):
        draft_fix = _mapping_value(fix.get("draft_fix"))
        action_id = _text(draft_fix.get("action")) or _text(fix.get("target_item_id"))
        if not action_id:
            continue
        gates[_normalize_action(action_id)] = {
            "gate_id": _required_text(fix, "fix_id"),
            "action_id": action_id,
            "required_confirmation_text": _text(draft_fix.get("required_confirmation_text")) or "I confirm I am ready to take this PP&D action.",
            "review_status": "draft_requires_human_review",
            "source_evidence_ids": sorted(_string_list(fix.get("source_evidence_ids"))),
        }

    for action in blocked_actions:
        action_id = _text(action.get("action_id"))
        normalized = _normalize_action(action_id)
        if action_id and _is_consequential_action(action_id) and normalized not in gates:
            gates[normalized] = {
                "gate_id": "review-required." + normalized.replace(" ", "_"),
                "action_id": action_id,
                "required_confirmation_text": "Reviewer must supply exact confirmation text before this action can ever be offered.",
                "review_status": "draft_requires_human_review",
                "source_evidence_ids": sorted(_string_list(action.get("source_evidence_ids"))),
            }
    return [gates[action_id] for action_id in sorted(gates)]


def _reviewer_prompts(candidate: Mapping[str, Any], rerun_plan: Mapping[str, Any], diffs: Sequence[Mapping[str, Any]], blocked_actions: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    prompts: list[dict[str, Any]] = []
    for note in _sequence_of_mappings(candidate.get("unresolved_human_review_notes")):
        prompts.append(
            {
                "prompt_id": "review-note." + _required_text(note, "note_id"),
                "prompt_type": "unresolved_human_review_note",
                "question": _required_text(note, "message"),
                "blocks_promotion": True,
                "source_evidence_ids": sorted(_string_list(note.get("source_evidence_ids"))),
            }
        )
    for diff in diffs:
        prompts.append(
            {
                "prompt_id": "review-diff." + _required_text(diff, "diff_id"),
                "prompt_type": "draft_bundle_diff",
                "question": "Confirm whether the draft change for " + _required_text(diff, "target_item_id") + " is source-grounded and should remain draft-only until approval.",
                "blocks_promotion": True,
                "source_evidence_ids": sorted(_string_list(diff.get("source_evidence_ids"))),
            }
        )
    for action in blocked_actions:
        prompts.append(
            {
                "prompt_id": "review-blocked-action." + _normalize_action(action.get("action_id")).replace(" ", "_"),
                "prompt_type": "blocked_consequential_action",
                "question": "Confirm that " + _required_text(action, "action_id") + " remains blocked until attendance and exact confirmation.",
                "blocks_promotion": True,
                "source_evidence_ids": sorted(_string_list(action.get("source_evidence_ids"))),
            }
        )
    if _sequence_of_mappings(rerun_plan.get("selected_cases")):
        prompts.append(
            {
                "prompt_id": "review-agent-regression-rerun-plan",
                "prompt_type": "agent_regression_rerun_plan",
                "question": "Review selected synthetic regression cases before approving any bundle promotion.",
                "blocks_promotion": True,
                "source_evidence_ids": sorted(_string_list(candidate.get("source_evidence_ids"))),
            }
        )
    return sorted(prompts, key=lambda item: item["prompt_id"])


def _rollback_notes(candidate: Mapping[str, Any], rerun_plan: Mapping[str, Any], diffs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    active_bundle_id = _required_text(candidate, "active_guardrail_bundle_id")
    notes = [
        {
            "note_id": "rollback.keep-active-bundle",
            "instruction": "Keep " + active_bundle_id + " active until a separate reviewed promotion explicitly replaces it.",
            "applies_to": active_bundle_id,
        },
        {
            "note_id": "rollback.discard-draft-diffs",
            "instruction": "If review fails, discard the draft diffs in this packet and rerun fixture remediation from cited public evidence.",
            "applies_to": ",".join(_required_text(diff, "diff_id") for diff in diffs),
        },
        {
            "note_id": "rollback.rerun-agent-regression-fixtures",
            "instruction": "Before any future promotion attempt, rerun only the committed fixture regression cases listed in the agent rerun plan.",
            "applies_to": _text(rerun_plan.get("plan_id")) or "agent_regression_rerun_plan",
        },
    ]
    return notes


def _reject_private_or_live_inputs(value: Any, key: str = "") -> None:
    if key in PRIVATE_FIELD_NAMES:
        raise GuardrailBundlePromotionReviewPacketError("private field is not allowed in promotion review packet: " + key)
    if key in LIVE_EXECUTION_KEYS and value is True:
        raise GuardrailBundlePromotionReviewPacketError("live execution is not allowed in promotion review packet: " + key)
    if isinstance(value, str) and any(marker in value for marker in PRIVATE_PATH_MARKERS):
        raise GuardrailBundlePromotionReviewPacketError("private local path or session artifact is not allowed")
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            _reject_private_or_live_inputs(child_value, str(child_key))
    elif isinstance(value, list):
        for child in value:
            _reject_private_or_live_inputs(child, key)


def _is_consequential_action(action_id: Any) -> bool:
    normalized = _normalize_action(action_id)
    return any(term in normalized for term in CONSEQUENTIAL_ACTION_TERMS)


def _normalize_action(value: Any) -> str:
    return _text(value).replace("-", "_").replace("_", " ").lower().strip()


def _mapping(raw: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = raw.get(key)
    if not isinstance(value, Mapping):
        raise GuardrailBundlePromotionReviewPacketError(key + " must be an object")
    return value


def _mapping_value(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence_of_mappings(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        return []
    return [str(item) for item in value if str(item)]


def _required_text(mapping: Mapping[str, Any], key: str) -> str:
    value = _text(mapping.get(key))
    if not value:
        raise GuardrailBundlePromotionReviewPacketError(key + " is required")
    return value


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _stable_hash(value: Mapping[str, Any]) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
