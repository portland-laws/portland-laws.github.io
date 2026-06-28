"""Validation for stale guardrail predicate remediation candidates.

The validator is intentionally fixture-friendly: remediation candidates are plain
JSON-like mappings and validation returns deterministic, stable error codes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

CONSEQUENTIAL_ACTIONS = frozenset(
    {
        "submit_permit_request",
        "certify_acknowledgement",
        "upload_correction",
        "purchase_trade_permit",
        "schedule_inspection",
        "cancel_or_withdraw",
        "request_extension",
        "reactivate_permit",
        "enter_payment_details",
        "submit_payment",
    }
)

RESOLVED_HUMAN_REVIEW_STATUSES = frozenset(
    {
        "reviewed",
        "approved",
        "accepted",
        "resolved",
    }
)

PRODUCTION_READY_STATUSES = frozenset(
    {
        "production_ready",
        "ready_for_production",
        "ready",
    }
)

PRIVATE_PRIVACY_MARKERS = frozenset(
    {
        "private",
        "private_case_fact",
        "case_fact",
        "authenticated",
        "credential",
        "payment_detail",
    }
)


@dataclass(frozen=True)
class StalePredicateRemediationValidationResult:
    """Result for a remediation candidate validation pass."""

    ok: bool
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "errors": list(self.errors)}


def validate_stale_predicate_remediation_candidate(
    candidate: Mapping[str, Any],
) -> StalePredicateRemediationValidationResult:
    """Validate a proposed stale-predicate remediation candidate.

    The candidate is rejected when it attempts to change predicates without
    citations, omits stale-input comparisons, lacks refusal rules for
    consequential actions, includes private case facts, mutates an active bundle,
    or marks itself production-ready before human review is resolved.
    """

    errors: list[str] = []
    citations = _citation_ids(candidate.get("citations"))
    changes = _mapping_list(candidate.get("proposed_predicate_changes"))

    if not changes:
        errors.append("missing_predicate_changes")

    _validate_cited_predicate_changes(changes, citations, errors)
    _validate_stale_input_comparisons(candidate, changes, errors)
    _validate_consequential_action_refusals(candidate, changes, errors)
    _validate_private_case_facts(candidate, errors)
    _validate_active_bundle_mutation(candidate, errors)
    _validate_production_status_review(candidate, errors)

    return StalePredicateRemediationValidationResult(ok=not errors, errors=errors)


def _validate_cited_predicate_changes(
    changes: list[Mapping[str, Any]], citations: set[str], errors: list[str]
) -> None:
    for index, change in enumerate(changes):
        change_id = _change_id(change, index)
        citation_ids = _string_list(change.get("citation_ids"))
        if not citation_ids:
            errors.append(f"uncited_predicate_change:{change_id}")
            continue
        missing = [citation_id for citation_id in citation_ids if citation_id not in citations]
        for citation_id in missing:
            errors.append(f"unknown_predicate_change_citation:{change_id}:{citation_id}")


def _validate_stale_input_comparisons(
    candidate: Mapping[str, Any], changes: list[Mapping[str, Any]], errors: list[str]
) -> None:
    comparisons = _mapping_list(candidate.get("stale_input_comparisons"))
    compared_predicates = {
        str(comparison.get("predicate_id", "")).strip()
        for comparison in comparisons
        if str(comparison.get("predicate_id", "")).strip()
    }
    changed_predicates = {
        str(change.get("predicate_id", "")).strip()
        for change in changes
        if str(change.get("predicate_id", "")).strip()
    }

    if not comparisons:
        errors.append("missing_stale_input_comparisons")
        return

    for predicate_id in sorted(changed_predicates - compared_predicates):
        errors.append(f"missing_stale_input_comparison:{predicate_id}")

    for comparison in comparisons:
        predicate_id = str(comparison.get("predicate_id", "")).strip() or "unknown"
        if not str(comparison.get("stale_input", "")).strip():
            errors.append(f"missing_stale_input_value:{predicate_id}")
        if not str(comparison.get("replacement_input", "")).strip():
            errors.append(f"missing_replacement_input_value:{predicate_id}")


def _validate_consequential_action_refusals(
    candidate: Mapping[str, Any], changes: list[Mapping[str, Any]], errors: list[str]
) -> None:
    refusal_actions = {
        str(rule.get("action", "")).strip()
        for rule in _mapping_list(candidate.get("refusal_rules"))
        if str(rule.get("action", "")).strip()
    }
    consequential_actions = sorted(
        action
        for action in {_change_action(change) for change in changes}
        if action in CONSEQUENTIAL_ACTIONS
    )

    for action in consequential_actions:
        if action not in refusal_actions:
            errors.append(f"missing_consequential_action_refusal:{action}")


def _validate_private_case_facts(candidate: Mapping[str, Any], errors: list[str]) -> None:
    if _non_empty(candidate.get("private_case_facts")):
        errors.append("private_case_facts_present")

    for citation in _mapping_list(candidate.get("citations")):
        citation_id = str(citation.get("id", "unknown")).strip() or "unknown"
        privacy = str(citation.get("privacy_classification", "")).strip().lower()
        if privacy in PRIVATE_PRIVACY_MARKERS:
            errors.append(f"private_citation_used:{citation_id}")

    for change in _mapping_list(candidate.get("proposed_predicate_changes")):
        change_id = _change_id(change, 0)
        if _non_empty(change.get("private_case_facts")):
            errors.append(f"private_case_facts_in_change:{change_id}")


def _validate_active_bundle_mutation(candidate: Mapping[str, Any], errors: list[str]) -> None:
    if bool(candidate.get("active_bundle_mutation")):
        errors.append("active_bundle_mutation")

    if bool(candidate.get("in_place_update")):
        errors.append("active_bundle_in_place_update")

    active_bundle_id = str(candidate.get("active_bundle_id", "")).strip()
    replacement_bundle_id = str(candidate.get("replacement_bundle_id", "")).strip()
    if active_bundle_id and replacement_bundle_id and active_bundle_id == replacement_bundle_id:
        errors.append("replacement_reuses_active_bundle_id")

    for mutation in _mapping_list(candidate.get("mutations")):
        target = str(mutation.get("target", "")).strip().lower()
        operation = str(mutation.get("operation", "")).strip().lower()
        if target == "active_bundle" or operation in {"mutate_active_bundle", "patch_active_bundle"}:
            errors.append("active_bundle_mutation")
            return


def _validate_production_status_review(candidate: Mapping[str, Any], errors: list[str]) -> None:
    validation_status = str(candidate.get("validation_status", "")).strip().lower()
    human_review_status = str(candidate.get("human_review_status", "")).strip().lower()
    if validation_status in PRODUCTION_READY_STATUSES and human_review_status not in RESOLVED_HUMAN_REVIEW_STATUSES:
        errors.append("production_ready_before_human_review")


def _citation_ids(value: Any) -> set[str]:
    citation_ids: set[str] = set()
    for citation in _mapping_list(value):
        citation_id = str(citation.get("id", "")).strip()
        if citation_id:
            citation_ids.add(citation_id)
    return citation_ids


def _mapping_list(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _change_action(change: Mapping[str, Any]) -> str:
    return str(change.get("action") or change.get("official_action") or "").strip()


def _change_id(change: Mapping[str, Any], index: int) -> str:
    return str(change.get("id") or change.get("predicate_id") or f"change_{index}").strip()


def _non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True
