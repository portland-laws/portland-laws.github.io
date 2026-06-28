"""Validation for PP&D guardrail bundle recompile candidates, v5.

The validator is intentionally data-shape tolerant so fixtures and daemon callers can
pass parsed JSON without depending on a shared contract rewrite.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

_PRIVATE_KEY_PARTS = (
    "auth",
    "cookie",
    "credential",
    "csrf",
    "jwt",
    "login",
    "password",
    "private",
    "secret",
    "session",
    "token",
)

_PRIVATE_VALUE_PARTS = (
    ".daemon/",
    "auth_state",
    "cookie",
    "devhub_session",
    "session_storage",
    "trace.zip",
)

_LEGAL_GUARANTEE_PARTS = (
    "approval guaranteed",
    "approved permit",
    "guarantee permit",
    "guaranteed approval",
    "legal guarantee",
    "permit guaranteed",
    "will be approved",
)


def validate_guardrail_bundle_recompile_candidate_v5(candidate: Mapping[str, Any]) -> list[str]:
    """Return stable error codes for missing or prohibited v5 candidate fields."""

    errors: list[str] = []

    if not _non_empty(candidate.get("process_model_impact_references")):
        errors.append("missing_process_model_impact_references")

    if not _has_inactive_guardrail_bundle_delta(candidate.get("guardrail_bundle_deltas")):
        errors.append("missing_inactive_guardrail_bundle_delta_rows")

    predicate_kinds = _kinds(candidate.get("predicate_deltas"))
    if "deterministic" not in predicate_kinds:
        errors.append("missing_deterministic_predicate_deltas")
    if "deontic" not in predicate_kinds:
        errors.append("missing_deontic_predicate_deltas")

    required_non_empty = (
        ("temporal_rule_deltas", "missing_temporal_rule_deltas"),
        ("reversible_action_handling", "missing_reversible_action_handling"),
        ("exact_confirmation_gates", "missing_exact_confirmation_gates"),
        ("stale_evidence_blocks", "missing_stale_evidence_blocks"),
        ("explanation_templates", "missing_explanation_templates"),
        ("reviewer_holds", "missing_reviewer_holds"),
        ("rollback_notes", "missing_rollback_notes"),
        ("validation_commands", "missing_validation_commands"),
    )
    for field, code in required_non_empty:
        if not _non_empty(candidate.get(field)):
            errors.append(code)

    refused_gate_kinds = _kinds(candidate.get("refused_action_gates"))
    if "consequential" not in refused_gate_kinds:
        errors.append("missing_refused_consequential_action_gates")
    if "financial" not in refused_gate_kinds:
        errors.append("missing_refused_financial_action_gates")

    if _has_active_mutation_claim(candidate):
        errors.append("active_guardrail_mutation_claims")
    if _contains_private_artifact(candidate):
        errors.append("private_session_or_auth_artifacts")
    if _has_official_action_completion_claim(candidate):
        errors.append("official_action_completion_claims")
    if _has_legal_or_permitting_guarantee(candidate):
        errors.append("legal_or_permitting_guarantees")
    if _has_active_mutation_flag(candidate):
        errors.append("active_mutation_flags")

    return errors


def assert_valid_guardrail_bundle_recompile_candidate_v5(candidate: Mapping[str, Any]) -> None:
    errors = validate_guardrail_bundle_recompile_candidate_v5(candidate)
    if errors:
        raise ValueError("guardrail bundle recompile candidate v5 rejected: " + ", ".join(errors))


def _non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return len(value) > 0
    return bool(value)


def _items(value: Any) -> list[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return list(value)
    if isinstance(value, Mapping):
        return [value]
    return []


def _text(value: Any) -> str:
    return str(value).strip().lower().replace("_", "-")


def _kinds(value: Any) -> set[str]:
    kinds: set[str] = set()
    for item in _items(value):
        if isinstance(item, Mapping):
            for key in ("kind", "type", "category", "mode"):
                if key in item:
                    kinds.add(_text(item[key]).replace("-", "_"))
        else:
            kinds.add(_text(item).replace("-", "_"))
    return kinds


def _has_inactive_guardrail_bundle_delta(value: Any) -> bool:
    for item in _items(value):
        if not isinstance(item, Mapping):
            continue
        name = _text(item.get("entity") or item.get("bundle") or item.get("target") or item.get("type"))
        status = _text(item.get("status") or item.get("state"))
        active = item.get("active")
        if "guardrailbundle" in name.replace("-", "") and (active is False or status == "inactive"):
            return True
    return False


def _has_active_mutation_claim(candidate: Mapping[str, Any]) -> bool:
    for field in ("guardrail_mutation_claims", "mutation_claims", "claims"):
        for item in _items(candidate.get(field)):
            if isinstance(item, Mapping):
                target = _text(item.get("target") or item.get("entity") or item.get("type"))
                active = item.get("active") is True or _text(item.get("state")) == "active"
                if active and ("guardrail" in target or field != "claims"):
                    return True
    return False


def _has_active_mutation_flag(candidate: Mapping[str, Any]) -> bool:
    for key in ("active_mutation", "active_mutations", "mutates_active_guardrails", "writes_active_guardrails"):
        if candidate.get(key) is True:
            return True
    flags = candidate.get("flags")
    if isinstance(flags, Mapping):
        return any(flags.get(key) is True for key in ("active_mutation", "mutates_active_guardrails", "writes_active_guardrails"))
    return False


def _contains_private_artifact(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            lowered_key = str(key).lower()
            if any(part in lowered_key for part in _PRIVATE_KEY_PARTS):
                return True
            if _contains_private_artifact(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return any(_contains_private_artifact(child) for child in value)
    elif isinstance(value, str):
        lowered_value = value.lower()
        return any(part in lowered_value for part in _PRIVATE_VALUE_PARTS)
    return False


def _has_official_action_completion_claim(candidate: Mapping[str, Any]) -> bool:
    if _non_empty(candidate.get("official_action_completion_claims")):
        return True
    for item in _items(candidate.get("completion_claims")):
        if isinstance(item, Mapping) and "official" in _text(item.get("type") or item.get("action") or item.get("target")):
            return True
        if isinstance(item, str) and "official action" in item.lower() and "complete" in item.lower():
            return True
    return False


def _has_legal_or_permitting_guarantee(value: Any) -> bool:
    if isinstance(value, Mapping):
        if _non_empty(value.get("legal_guarantees")) or _non_empty(value.get("permitting_guarantees")):
            return True
        return any(_has_legal_or_permitting_guarantee(child) for child in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return any(_has_legal_or_permitting_guarantee(child) for child in value)
    if isinstance(value, str):
        lowered = value.lower()
        return any(part in lowered for part in _LEGAL_GUARANTEE_PARTS)
    return False
