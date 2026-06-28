"""Validation and loading for PP&D agent guardrail bundles."""
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

EVIDENCE_ID_FIELDS = (
    "source_evidence_ids",
    "evidence_ids",
    "source_ids",
    "source_evidence_id",
    "evidence_id",
)
CITATION_SPAN_FIELDS = (
    "citation_spans",
    "source_citation_spans",
    "explanation_citation_spans",
    "citation_span_ids",
    "citations",
)
PROCESS_STAGE_KEYS = ("stages", "process_stages")
STAGE_CITATION_MAP_KEYS = (
    "stage_source_evidence_ids",
    "stage_evidence_ids",
    "stage_citation_spans",
    "citations_by_stage",
    "evidence_by_stage",
)
UNSUPPORTED_ACTION_KEYS = (
    "unsupported_actions",
    "unsupported_paths",
    "unsupported_devhub_actions",
)
OUTCOME_FIELDS = (
    "outcome",
    "outcomes",
    "required_outcome",
    "policy_outcome",
    "guardrail_outcome",
    "terminal_outcome",
    "resolution",
)
OUTCOME_MAP_KEYS = (
    "unsupported_action_outcomes",
    "action_outcomes",
    "outcomes_by_action",
)
PREDICATE_COLLECTION_KEYS = (
    "deterministic_predicates",
    "reversible_action_predicates",
    "exact_confirmation_predicates",
    "refused_action_predicates",
    "guardrail_predicates",
)
PREDICATE_EVIDENCE_MAP_KEYS = (
    "predicate_source_evidence_ids",
    "predicate_evidence_ids",
    "source_evidence_by_predicate",
    "evidence_by_predicate",
)
NEXT_SAFE_ACTION_KEYS = ("next_safe_actions", "next_safe_action_candidates")
EXPLANATION_FIELDS = ("explanation", "explanation_template", "rationale", "reason")
NEXT_ACTION_CITATION_MAP_KEYS = (
    "next_safe_action_citation_spans",
    "citation_spans_by_next_safe_action",
    "explanation_citation_spans_by_action",
)


@dataclass(frozen=True)
class AgentBundleValidationIssue:
    """A deterministic bundle validation failure."""

    code: str
    path: str
    message: str

    def as_dict(self) -> Dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


class AgentBundleValidationError(ValueError):
    """Raised when an agent bundle is not safe to load."""

    def __init__(self, issues: Iterable[AgentBundleValidationIssue]):
        self.issues = list(issues)
        detail = "; ".join(
            f"{issue.code} at {issue.path}: {issue.message}" for issue in self.issues
        )
        super().__init__(detail or "agent bundle validation failed")


def load_agent_bundle(path: Any) -> Dict[str, Any]:
    """Load a JSON agent bundle from disk and reject unsafe bundle records."""

    bundle_path = Path(path)
    with bundle_path.open("r", encoding="utf-8") as handle:
        bundle = json.load(handle)
    if not isinstance(bundle, dict):
        raise AgentBundleValidationError(
            [
                AgentBundleValidationIssue(
                    "bundle_not_object",
                    "$",
                    "agent bundle JSON must be an object",
                )
            ]
        )
    validate_agent_bundle(bundle)
    return bundle


def loads_agent_bundle(content: str) -> Dict[str, Any]:
    """Load a JSON agent bundle string and reject unsafe bundle records."""

    bundle = json.loads(content)
    if not isinstance(bundle, dict):
        raise AgentBundleValidationError(
            [
                AgentBundleValidationIssue(
                    "bundle_not_object",
                    "$",
                    "agent bundle JSON must be an object",
                )
            ]
        )
    validate_agent_bundle(bundle)
    return bundle


def load_bundle(path: Any) -> Dict[str, Any]:
    return load_agent_bundle(path)


def validate_bundle(bundle: Mapping[str, Any]) -> Mapping[str, Any]:
    return validate_agent_bundle(bundle)


def validate_agent_bundle(bundle: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate source-grounding and safety requirements for an agent bundle."""

    issues = collect_agent_bundle_validation_errors(bundle)
    if issues:
        raise AgentBundleValidationError(issues)
    return bundle


def collect_agent_bundle_validation_errors(
    bundle: Mapping[str, Any],
) -> List[AgentBundleValidationIssue]:
    if not isinstance(bundle, Mapping):
        return [
            AgentBundleValidationIssue(
                "bundle_not_object",
                "$",
                "agent bundle JSON must be an object",
            )
        ]

    issues: List[AgentBundleValidationIssue] = []
    _validate_process_stages(bundle, issues)
    _validate_unsupported_actions(bundle, issues)
    _validate_guardrail_predicates(bundle, issues)
    _validate_next_safe_action_explanations(bundle, issues)
    return issues


def _validate_process_stages(
    bundle: Mapping[str, Any], issues: List[AgentBundleValidationIssue]
) -> None:
    for container_path, container in _walk_mappings(bundle, "$"):
        for key in PROCESS_STAGE_KEYS:
            if key not in container:
                continue
            stages_path = _join_path(container_path, key)
            for stage_path, stage in _iter_collection_items(container[key], stages_path):
                if not _stage_has_citation(stage, container):
                    label = _record_label(stage) or "process stage"
                    issues.append(
                        AgentBundleValidationIssue(
                            "uncited_process_stage",
                            stage_path,
                            f"process stage {label!r} must include evidence IDs or citation spans",
                        )
                    )


def _validate_unsupported_actions(
    bundle: Mapping[str, Any], issues: List[AgentBundleValidationIssue]
) -> None:
    validated_paths = set()
    for container_path, container in _walk_mappings(bundle, "$"):
        for key in UNSUPPORTED_ACTION_KEYS:
            if key not in container:
                continue
            collection_path = _join_path(container_path, key)
            for action_path, action in _iter_collection_items(container[key], collection_path):
                validated_paths.add(action_path)
                if not _has_manual_handoff_outcome(action, container):
                    label = _record_label(action) or "unsupported action"
                    issues.append(
                        AgentBundleValidationIssue(
                            "unsupported_action_missing_manual_handoff",
                            action_path,
                            f"unsupported action {label!r} must resolve to a manual-handoff outcome",
                        )
                    )

        if container_path in validated_paths:
            continue
        if _is_unsupported_action_record(container) and not _has_manual_handoff_outcome(container, None):
            label = _record_label(container) or "unsupported action"
            issues.append(
                AgentBundleValidationIssue(
                    "unsupported_action_missing_manual_handoff",
                    container_path,
                    f"unsupported action {label!r} must resolve to a manual-handoff outcome",
                )
            )


def _validate_guardrail_predicates(
    bundle: Mapping[str, Any], issues: List[AgentBundleValidationIssue]
) -> None:
    for container_path, container in _walk_mappings(bundle, "$"):
        for key in PREDICATE_COLLECTION_KEYS:
            if key not in container:
                continue
            predicates_path = _join_path(container_path, key)
            for predicate_path, predicate in _iter_collection_items(container[key], predicates_path):
                if not _predicate_has_evidence(predicate, container):
                    label = _record_label(predicate) or "guardrail predicate"
                    issues.append(
                        AgentBundleValidationIssue(
                            "guardrail_predicate_missing_evidence_ids",
                            predicate_path,
                            f"guardrail predicate {label!r} must include source evidence IDs",
                        )
                    )


def _validate_next_safe_action_explanations(
    bundle: Mapping[str, Any], issues: List[AgentBundleValidationIssue]
) -> None:
    for container_path, container in _walk_mappings(bundle, "$"):
        for key in NEXT_SAFE_ACTION_KEYS:
            if key not in container:
                continue
            actions_path = _join_path(container_path, key)
            for action_path, action in _iter_collection_items(container[key], actions_path):
                if _has_explanation(action) and not _has_citation_span(action, container):
                    label = _record_label(action) or "next safe action"
                    issues.append(
                        AgentBundleValidationIssue(
                            "next_safe_action_explanation_missing_citation_spans",
                            action_path,
                            f"next-safe-action explanation for {label!r} must include citation spans",
                        )
                    )


def _stage_has_citation(stage: Any, container: Mapping[str, Any]) -> bool:
    if isinstance(stage, Mapping) and (
        _has_any_non_empty(stage, EVIDENCE_ID_FIELDS)
        or _has_any_non_empty(stage, CITATION_SPAN_FIELDS)
    ):
        return True

    labels = _record_identifiers(stage)
    for map_key in STAGE_CITATION_MAP_KEYS:
        citation_map = container.get(map_key)
        if not isinstance(citation_map, Mapping):
            continue
        for label in labels:
            if _non_empty(citation_map.get(label)):
                return True
    return False


def _has_manual_handoff_outcome(action: Any, container: Mapping[str, Any] | None) -> bool:
    if isinstance(action, Mapping):
        if action.get("manual_handoff") is True or action.get("requires_manual_handoff") is True:
            return True
        for field in OUTCOME_FIELDS:
            if _contains_manual_handoff(action.get(field)):
                return True
        return False

    if container is None:
        return False
    labels = _record_identifiers(action)
    for map_key in OUTCOME_MAP_KEYS:
        outcome_map = container.get(map_key)
        if not isinstance(outcome_map, Mapping):
            continue
        for label in labels:
            if _contains_manual_handoff(outcome_map.get(label)):
                return True
    return False


def _is_unsupported_action_record(record: Mapping[str, Any]) -> bool:
    if record.get("unsupported") is True:
        return True
    for key in ("classification", "category", "action_class", "safety_class", "policy", "status"):
        value = record.get(key)
        if _normalized(value) in {"unsupported", "unsupportedpath", "manualhandoffrequired"}:
            return True
    return False


def _predicate_has_evidence(predicate: Any, container: Mapping[str, Any]) -> bool:
    if isinstance(predicate, Mapping) and _has_any_non_empty(predicate, EVIDENCE_ID_FIELDS):
        return True

    labels = _record_identifiers(predicate)
    for map_key in PREDICATE_EVIDENCE_MAP_KEYS:
        evidence_map = container.get(map_key)
        if not isinstance(evidence_map, Mapping):
            continue
        for label in labels:
            if _non_empty(evidence_map.get(label)):
                return True
    return False


def _has_explanation(action: Any) -> bool:
    if not isinstance(action, Mapping):
        return False
    return _has_any_non_empty(action, EXPLANATION_FIELDS)


def _has_citation_span(action: Any, container: Mapping[str, Any]) -> bool:
    if isinstance(action, Mapping):
        if _has_any_non_empty(action, CITATION_SPAN_FIELDS):
            return True
        for field in EXPLANATION_FIELDS:
            explanation = action.get(field)
            if isinstance(explanation, Mapping) and _has_any_non_empty(explanation, CITATION_SPAN_FIELDS):
                return True

    labels = _record_identifiers(action)
    for map_key in NEXT_ACTION_CITATION_MAP_KEYS:
        citation_map = container.get(map_key)
        if not isinstance(citation_map, Mapping):
            continue
        for label in labels:
            if _non_empty(citation_map.get(label)):
                return True
    return False


def _walk_mappings(value: Any, path: str) -> Iterable[Tuple[str, Mapping[str, Any]]]:
    if isinstance(value, Mapping):
        yield path, value
        for key, child in value.items():
            yield from _walk_mappings(child, _join_path(path, str(key)))
    elif _is_sequence(value):
        for index, child in enumerate(value):
            yield from _walk_mappings(child, f"{path}[{index}]")


def _iter_collection_items(value: Any, path: str) -> Iterable[Tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield _join_path(path, str(key)), item
    elif _is_sequence(value):
        for index, item in enumerate(value):
            yield f"{path}[{index}]", item
    elif value is not None:
        yield path, value


def _join_path(path: str, key: str) -> str:
    return f"{path}.{key}" if key.isidentifier() else f"{path}[{key!r}]"


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _has_any_non_empty(record: Mapping[str, Any], fields: Sequence[str]) -> bool:
    return any(_non_empty(record.get(field)) for field in fields)


def _non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if _is_sequence(value):
        return any(_non_empty(item) for item in value)
    return True


def _contains_manual_handoff(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, Mapping):
        return any(_contains_manual_handoff(item) for item in value.values())
    if _is_sequence(value):
        return any(_contains_manual_handoff(item) for item in value)
    token = _normalized(value)
    return "manualhandoff" in token


def _normalized(value: Any) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isalnum())


def _record_identifiers(record: Any) -> List[str]:
    if isinstance(record, str):
        return [record]
    if not isinstance(record, Mapping):
        return []
    labels: List[str] = []
    for key in ("stage_id", "action_id", "predicate_id", "id", "name", "label"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            labels.append(value)
    return labels


def _record_label(record: Any) -> str | None:
    identifiers = _record_identifiers(record)
    return identifiers[0] if identifiers else None


__all__ = [
    "AgentBundleValidationError",
    "AgentBundleValidationIssue",
    "collect_agent_bundle_validation_errors",
    "load_agent_bundle",
    "load_bundle",
    "loads_agent_bundle",
    "validate_agent_bundle",
    "validate_bundle",
]
