"""Deterministic guardrails for PP&D autonomous planning.

The checks in this module are intentionally conservative. They validate only
whether an LLM agent may plan autonomous completion. Attended workflows can use
separate confirmation gates, but missing citations, stale evidence, private
values, and consequential or financial actions always fail closed here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

SAFE_ACTION_KINDS = frozenset({"read_only", "analysis", "draft", "local_preview"})
CONSEQUENTIAL_ACTION_KINDS = frozenset(
    {
        "acknowledge",
        "certify",
        "submit",
        "upload",
        "schedule",
        "cancel",
        "purchase",
        "pay",
        "payment",
        "official_change",
    }
)
FINANCIAL_ACTION_KINDS = frozenset({"fee", "pay", "payment", "purchase", "refund"})
STALE_EVIDENCE_STATES = frozenset({"stale", "expired", "superseded", "unknown", "missing"})
CURRENT_EVIDENCE_STATES = frozenset({"current", "verified"})


@dataclass(frozen=True)
class GuardrailFailure:
    """One failed proof obligation for autonomous completion."""

    code: str
    message: str
    ref: str | None = None


@dataclass(frozen=True)
class GuardrailValidation:
    """Result returned to an agent before autonomous planning."""

    allowed: bool
    failures: tuple[GuardrailFailure, ...]
    proof_obligations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "failures": [failure.__dict__ for failure in self.failures],
            "proof_obligations": list(self.proof_obligations),
        }


@dataclass(frozen=True)
class AutonomousPlanningRequest:
    """Minimal request shape for autonomous completion guardrail checks."""

    required_evidence_ids: tuple[str, ...] = ()
    cited_evidence_ids: tuple[str, ...] = ()
    evidence_freshness: Mapping[str, str] = field(default_factory=dict)
    private_value_fields: tuple[str, ...] = ()
    proposed_actions: tuple[Mapping[str, Any], ...] = ()


def _as_string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        values: list[str] = []
        for item in value:
            if isinstance(item, str) and item:
                values.append(item)
        return tuple(values)
    return ()


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _action_kind(action: Mapping[str, Any]) -> str:
    raw_kind = action.get("kind") or action.get("action_type") or action.get("classification")
    if isinstance(raw_kind, str) and raw_kind:
        return raw_kind.strip().lower()
    raw_name = action.get("name") or action.get("action") or action.get("label")
    if not isinstance(raw_name, str):
        return "unknown"
    lowered = raw_name.strip().lower()
    for token in CONSEQUENTIAL_ACTION_KINDS | FINANCIAL_ACTION_KINDS:
        if token in lowered:
            return token
    return lowered or "unknown"


def _action_ref(action: Mapping[str, Any], index: int) -> str:
    raw_ref = action.get("action_id") or action.get("id") or action.get("name") or action.get("action")
    if isinstance(raw_ref, str) and raw_ref:
        return raw_ref
    return f"action[{index}]"


def request_from_mapping(value: Mapping[str, Any]) -> AutonomousPlanningRequest:
    """Build a guardrail request from a JSON-like mapping."""

    action_items: list[Mapping[str, Any]] = []
    for item in value.get("proposed_actions", value.get("actions", ())) or ():
        if isinstance(item, Mapping):
            action_items.append(item)

    return AutonomousPlanningRequest(
        required_evidence_ids=_as_string_tuple(value.get("required_evidence_ids")),
        cited_evidence_ids=_as_string_tuple(value.get("cited_evidence_ids")),
        evidence_freshness=_as_mapping(value.get("evidence_freshness")),
        private_value_fields=_as_string_tuple(value.get("private_value_fields")),
        proposed_actions=tuple(action_items),
    )


def request_from_bundle(bundle: Mapping[str, Any], plan: Mapping[str, Any]) -> AutonomousPlanningRequest:
    """Merge a guardrail bundle and proposed plan into a validation request."""

    bundle_predicates = _as_mapping(bundle.get("deterministic_predicates"))
    bundle_private_fields = _as_string_tuple(bundle_predicates.get("private_value_fields"))
    plan_private_fields = _as_string_tuple(plan.get("private_value_fields"))
    source_evidence_ids = _as_string_tuple(bundle.get("source_evidence_ids"))
    required_evidence_ids = _as_string_tuple(plan.get("required_evidence_ids")) or source_evidence_ids

    freshness = dict(_as_mapping(bundle_predicates.get("evidence_freshness")))
    freshness.update(_as_mapping(plan.get("evidence_freshness")))

    actions: list[Mapping[str, Any]] = []
    for item in plan.get("proposed_actions", plan.get("actions", ())) or ():
        if isinstance(item, Mapping):
            actions.append(item)

    return AutonomousPlanningRequest(
        required_evidence_ids=required_evidence_ids,
        cited_evidence_ids=_as_string_tuple(plan.get("cited_evidence_ids")),
        evidence_freshness=freshness,
        private_value_fields=tuple(dict.fromkeys(bundle_private_fields + plan_private_fields)),
        proposed_actions=tuple(actions),
    )


def validate_autonomous_planning_request(
    request: AutonomousPlanningRequest,
) -> GuardrailValidation:
    """Return whether autonomous completion planning is allowed.

    The validator is fail-closed. Missing or unknown evidence freshness is a
    failure, unknown action kinds are failures, and any private-value dependency
    blocks autonomous completion.
    """

    failures: list[GuardrailFailure] = []
    proof_obligations = (
        "all_required_evidence_is_cited",
        "all_required_evidence_is_current",
        "no_private_value_fields_are_needed",
        "all_actions_are_read_only_or_reversible_drafts",
        "no_financial_or_consequential_action_is_planned",
    )

    required_evidence = set(request.required_evidence_ids)
    cited_evidence = set(request.cited_evidence_ids)
    if not required_evidence:
        failures.append(
            GuardrailFailure(
                code="missing_required_evidence",
                message="Autonomous planning requires at least one source evidence citation.",
            )
        )

    for evidence_id in sorted(required_evidence - cited_evidence):
        failures.append(
            GuardrailFailure(
                code="missing_citation",
                message="Required source evidence is not cited by the proposed plan.",
                ref=evidence_id,
            )
        )

    for evidence_id in sorted(required_evidence):
        state = str(request.evidence_freshness.get(evidence_id, "unknown")).strip().lower()
        if state in STALE_EVIDENCE_STATES or state not in CURRENT_EVIDENCE_STATES:
            failures.append(
                GuardrailFailure(
                    code="stale_evidence",
                    message="Required evidence is stale, missing, or not verified current.",
                    ref=evidence_id,
                )
            )

    for field_name in request.private_value_fields:
        failures.append(
            GuardrailFailure(
                code="private_value_required",
                message="Private user values must not be used for autonomous completion planning.",
                ref=field_name,
            )
        )

    for index, action in enumerate(request.proposed_actions):
        kind = _action_kind(action)
        ref = _action_ref(action, index)
        if kind in FINANCIAL_ACTION_KINDS:
            failures.append(
                GuardrailFailure(
                    code="financial_action_blocked",
                    message="Financial actions fail closed before autonomous planning.",
                    ref=ref,
                )
            )
            continue
        if kind in CONSEQUENTIAL_ACTION_KINDS:
            failures.append(
                GuardrailFailure(
                    code="consequential_action_blocked",
                    message="Consequential official actions fail closed before autonomous planning.",
                    ref=ref,
                )
            )
            continue
        if kind not in SAFE_ACTION_KINDS:
            failures.append(
                GuardrailFailure(
                    code="unknown_action_kind",
                    message="Only read-only, analysis, local preview, or reversible draft actions may be planned autonomously.",
                    ref=ref,
                )
            )

    return GuardrailValidation(
        allowed=not failures,
        failures=tuple(failures),
        proof_obligations=proof_obligations,
    )


def validate_guardrail_bundle(
    bundle: Mapping[str, Any], plan: Mapping[str, Any]
) -> GuardrailValidation:
    """Validate a GuardrailBundle and proposed plan before autonomous completion."""

    request = request_from_bundle(bundle, plan)
    validation = validate_autonomous_planning_request(request)
    failures = list(validation.failures)

    validation_status = str(bundle.get("validation_status", "unknown")).strip().lower()
    if validation_status not in {"validated", "current"}:
        failures.insert(
            0,
            GuardrailFailure(
                code="bundle_not_validated",
                message="Guardrail bundle must be validated before autonomous planning.",
                ref=str(bundle.get("guardrail_bundle_id", "unknown")),
            ),
        )

    return GuardrailValidation(
        allowed=not failures,
        failures=tuple(failures),
        proof_obligations=validation.proof_obligations,
    )
