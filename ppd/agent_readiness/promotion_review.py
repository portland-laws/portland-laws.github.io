"""Validation for PP&D guardrail bundle promotion review packets.

Promotion review packets are the handoff artifact between a reviewed candidate
bundle and any production-facing guardrail bundle registry. The checks here are
fixture-first and side-effect free: they reject packets that would make predicate
changes without citations, skip regression coverage, weaken gates for
consequential actions, include private case facts, mutate an active bundle in
place, or claim production readiness while review items remain unresolved.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

_HIGH_RISK_ACTIONS = {
    "payment",
    "upload",
    "submission",
    "scheduling",
    "cancellation",
    "certification",
}

_EXACT_GATE_NAMES = {
    "exact_confirmation",
    "exact-confirmation",
    "exact_confirmation_gate",
    "requires_exact_confirmation",
}

_REFUSAL_GATE_NAMES = {
    "refusal",
    "refusal_gate",
    "refused_action_predicate",
    "refused_official_action_predicate",
    "refuse_official_action_without_authority",
}

_READY_FOR_PRODUCTION = {
    "production_ready",
    "ready_for_production",
    "promote_to_production",
    "production-ready",
}

_UNRESOLVED_REVIEW_STATUSES = {
    "",
    "blocked",
    "blocking",
    "needs_review",
    "open",
    "pending",
    "unresolved",
}

_PRIVATE_FACT_CLASSIFICATIONS = {
    "private",
    "private_case_fact",
    "confidential",
    "sensitive",
    "user_private",
}

_PRIVATE_VALUE_KEYS = {
    "answer",
    "case_fact_value",
    "entered_value",
    "field_value",
    "private_value",
    "raw_value",
    "user_input",
    "user_supplied_value",
    "value",
}

_EVIDENCE_REF_KEYS = ("source_evidence_ids", "source_evidence_id", "citation_ids", "citation_id")


@dataclass(frozen=True)
class PromotionReviewValidationResult:
    """Machine-readable validation result for a promotion review packet."""

    valid: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "problems": list(self.problems)}


class PromotionReviewPacketError(ValueError):
    """Raised when a guardrail bundle promotion review packet is unsafe."""

    def __init__(self, problems: tuple[str, ...]) -> None:
        self.problems = problems
        super().__init__("invalid_guardrail_bundle_promotion_review_packet: " + "; ".join(problems))


def validate_guardrail_bundle_promotion_review_packet(packet: Mapping[str, Any]) -> PromotionReviewValidationResult:
    """Validate a PP&D guardrail bundle promotion review packet fail-closed."""

    problems: list[str] = []
    problems.extend(_predicate_diff_problems(packet))
    problems.extend(_regression_coverage_problems(packet))
    problems.extend(_high_risk_gate_problems(packet))
    problems.extend(_private_case_fact_problems(packet))
    problems.extend(_active_bundle_mutation_problems(packet))
    problems.extend(_production_status_problems(packet))
    return PromotionReviewValidationResult(valid=not problems, problems=tuple(problems))


def require_guardrail_bundle_promotion_review_packet_valid(packet: Mapping[str, Any]) -> None:
    """Raise if a PP&D guardrail bundle promotion review packet is unsafe."""

    result = validate_guardrail_bundle_promotion_review_packet(packet)
    if not result.valid:
        raise PromotionReviewPacketError(result.problems)


def _predicate_diff_problems(packet: Mapping[str, Any]) -> list[str]:
    diffs = packet.get("predicate_diffs")
    if not isinstance(diffs, list) or not diffs:
        return ["promotion review packet must include predicate_diffs"]

    problems: list[str] = []
    for index, diff in enumerate(diffs):
        if not isinstance(diff, Mapping):
            problems.append(f"predicate_diffs[{index}] must be an object")
            continue
        diff_id = _diff_id(diff, index)
        if not _evidence_refs(diff):
            problems.append(f"predicate diff {diff_id} must cite source evidence")
        if not diff.get("predicate_id"):
            problems.append(f"predicate diff {diff_id} is missing predicate_id")
        if not diff.get("change_type"):
            problems.append(f"predicate diff {diff_id} is missing change_type")
    return problems


def _regression_coverage_problems(packet: Mapping[str, Any]) -> list[str]:
    diffs = [diff for diff in packet.get("predicate_diffs", []) if isinstance(diff, Mapping)]
    diff_ids = {_diff_id(diff, index) for index, diff in enumerate(diffs)}
    links = packet.get("regression_coverage_links")
    if not isinstance(links, list) or not links:
        return ["promotion review packet must include regression_coverage_links"]

    problems: list[str] = []
    covered_diff_ids: set[str] = set()
    for index, link in enumerate(links):
        if not isinstance(link, Mapping):
            problems.append(f"regression_coverage_links[{index}] must be an object")
            continue
        if not any(link.get(key) for key in ("test_id", "test_path", "fixture_path", "validation_command")):
            problems.append(f"regression coverage link {index} is missing a test or fixture reference")
        raw_covered = link.get("covered_diff_ids")
        if isinstance(raw_covered, list):
            covered_diff_ids.update(item for item in raw_covered if isinstance(item, str) and item)

    for diff_id in sorted(diff_ids - covered_diff_ids):
        problems.append(f"predicate diff {diff_id} lacks regression coverage")
    return problems


def _high_risk_gate_problems(packet: Mapping[str, Any]) -> list[str]:
    gates = _gate_records(packet)
    by_action: dict[str, set[str]] = {action: set() for action in _HIGH_RISK_ACTIONS}

    for gate in gates:
        action = _normalize_action(gate.get("action_type") or gate.get("action") or gate.get("official_action"))
        if action not in by_action:
            continue
        gate_type = _normalize_gate(gate.get("gate_type") or gate.get("predicate") or gate.get("kind"))
        if gate.get("requires_exact_confirmation") is True:
            gate_type = "exact_confirmation"
        if gate.get("refuses_without_authority") is True or gate.get("refusal_required") is True:
            gate_type = "refusal"
        if gate_type:
            by_action[action].add(gate_type)

    problems: list[str] = []
    for action in sorted(_HIGH_RISK_ACTIONS):
        gate_types = by_action[action]
        if "refusal" not in gate_types:
            problems.append(f"high-risk action {action} is missing a refusal gate")
        if "exact_confirmation" not in gate_types:
            problems.append(f"high-risk action {action} is missing an exact-confirmation gate")
    return problems


def _private_case_fact_problems(packet: Mapping[str, Any]) -> list[str]:
    facts = []
    for key in ("case_facts", "known_facts", "user_case_facts"):
        raw = packet.get(key)
        if isinstance(raw, list):
            facts.extend((key, index, fact) for index, fact in enumerate(raw))

    problems: list[str] = []
    for collection, index, fact in facts:
        if not isinstance(fact, Mapping):
            problems.append(f"{collection}[{index}] must be an object")
            continue
        fact_id = str(fact.get("fact_id") or f"{collection}[{index}]")
        classification = str(fact.get("privacy_classification") or fact.get("classification") or "").lower()
        if classification in _PRIVATE_FACT_CLASSIFICATIONS:
            problems.append(f"case fact {fact_id} uses private privacy classification")
        if fact.get("value_policy") not in (None, "metadata_only", "redacted", "reference_only"):
            problems.append(f"case fact {fact_id} must be metadata-only or redacted")
        for key, value in fact.items():
            if str(key).lower() in _PRIVATE_VALUE_KEYS and value not in (None, "", [], {}):
                problems.append(f"case fact {fact_id} contains private value field {key}")
    return problems


def _active_bundle_mutation_problems(packet: Mapping[str, Any]) -> list[str]:
    problems: list[str] = []
    active_bundle_id = packet.get("active_bundle_id")
    candidate_bundle_id = packet.get("candidate_bundle_id") or packet.get("proposed_bundle_id")

    if packet.get("active_bundle_mutation") is True or packet.get("mutates_active_bundle") is True:
        problems.append("promotion review packet must not mutate the active bundle")
    active_changes = packet.get("active_bundle_changes")
    if isinstance(active_changes, list) and active_changes:
        problems.append("promotion review packet must not include active_bundle_changes")
    if active_bundle_id and candidate_bundle_id and active_bundle_id == candidate_bundle_id:
        problems.append("candidate bundle id must differ from active bundle id")

    for index, diff in enumerate(packet.get("predicate_diffs", [])):
        if not isinstance(diff, Mapping):
            continue
        target_bundle_id = diff.get("target_bundle_id") or diff.get("bundle_id")
        if active_bundle_id and target_bundle_id == active_bundle_id:
            problems.append(f"predicate diff {_diff_id(diff, index)} targets the active bundle")
    return problems


def _production_status_problems(packet: Mapping[str, Any]) -> list[str]:
    status = str(
        packet.get("promotion_status")
        or packet.get("proposed_status")
        or packet.get("validation_status")
        or ""
    ).strip().lower()
    if status not in _READY_FOR_PRODUCTION:
        return []

    problems: list[str] = []
    review_items = packet.get("review_items")
    if not isinstance(review_items, list):
        return ["production-ready promotion packet must include resolved review_items"]

    for index, item in enumerate(review_items):
        if not isinstance(item, Mapping):
            problems.append(f"review_items[{index}] must be an object")
            continue
        item_id = item.get("item_id") or f"review_items[{index}]"
        item_status = str(item.get("status") or "").strip().lower()
        if item_status in _UNRESOLVED_REVIEW_STATUSES:
            problems.append(f"production-ready promotion packet has unresolved review item {item_id}")
    return problems


def _gate_records(packet: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    records: list[Mapping[str, Any]] = []
    for key in ("guardrail_gates", "exact_confirmation_gates", "refusal_gates"):
        raw = packet.get(key)
        if isinstance(raw, list):
            records.extend(item for item in raw if isinstance(item, Mapping))

    candidate = packet.get("candidate_bundle")
    if isinstance(candidate, Mapping):
        for key in ("exact_confirmation_predicates", "refused_official_action_predicates", "refused_action_predicates"):
            raw = candidate.get(key)
            if isinstance(raw, list):
                records.extend(item for item in raw if isinstance(item, Mapping))
    return records


def _evidence_refs(value: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    for key in _EVIDENCE_REF_KEYS:
        raw = value.get(key)
        if isinstance(raw, str) and raw:
            refs.add(raw)
        elif isinstance(raw, list):
            refs.update(item for item in raw if isinstance(item, str) and item)
    return refs


def _diff_id(diff: Mapping[str, Any], index: int) -> str:
    raw = diff.get("diff_id") or diff.get("id")
    if isinstance(raw, str) and raw:
        return raw
    return f"index-{index}"


def _normalize_action(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_")
    aliases = {
        "fee_payment": "payment",
        "pay_fees": "payment",
        "upload_correction": "upload",
        "upload_to_official_record": "upload",
        "submit": "submission",
        "submit_application": "submission",
        "schedule": "scheduling",
        "schedule_inspection": "scheduling",
        "cancel": "cancellation",
        "withdraw": "cancellation",
        "certify": "certification",
        "acknowledgement_certification": "certification",
    }
    return aliases.get(text, text)


def _normalize_gate(value: Any) -> str:
    text = str(value or "").strip().lower().replace("_gate", "")
    if text in _EXACT_GATE_NAMES or text == "requires_exact_confirmation":
        return "exact_confirmation"
    if text in _REFUSAL_GATE_NAMES or text.startswith("refuse_"):
        return "refusal"
    return ""
