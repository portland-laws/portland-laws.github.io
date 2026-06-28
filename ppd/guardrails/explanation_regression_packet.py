"""Fixture-first guardrail explanation regression packet builder and validator.

This module intentionally stays deterministic: it reads committed fixture packets,
joins them by cited references, and emits synthetic explanations for regression
checks without invoking an LLM or promoting active guardrails.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

_ALLOWED_CLASSES = {
    "allowed_read_only",
    "reversible_draft_limit",
    "exact_confirmation_checkpoint",
    "manual_handoff",
    "refused_consequential_action",
}

_LABELS = {
    "allowed_read_only": "allowed read-only action",
    "reversible_draft_limit": "reversible draft limit",
    "exact_confirmation_checkpoint": "exact-confirmation checkpoint",
    "manual_handoff": "manual handoff",
    "refused_consequential_action": "refused consequential action",
}

_REFUSAL_WORDS = ("cannot", "refuse", "blocked", "must stop", "will not")

_PRIVATE_KEY_FRAGMENTS = (
    "private",
    "secret",
    "credential",
    "cookie",
    "auth_state",
    "session",
    "token",
    "password",
    "phone",
    "email",
    "address_line",
    "case_fact",
    "local_path",
    "raw_document",
)

_PRIVATE_VALUE_PATTERNS = (
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b\d{3}[-.]\d{3}[-.]\d{4}\b"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"(?:/Users/|/home/[^\s/]+/(?:Desktop|Documents|Downloads)|C:\\\\Users\\\\)", re.IGNORECASE),
    re.compile(r"\bhomeowner\s+(?:phone|email|address|name)\b", re.IGNORECASE),
)

_LIVE_EXECUTION_KEY_FRAGMENTS = (
    "live_llm",
    "llm_execution",
    "consumer_execution",
    "consumer_called",
    "called_consumer",
    "ran_consumer",
    "live_execution",
)

_LIVE_EXECUTION_TEXT_PATTERNS = (
    re.compile(r"\b(?:called|queried|ran|executed)\s+(?:the\s+)?(?:live\s+)?llm\b", re.IGNORECASE),
    re.compile(r"\b(?:called|queried|ran|executed)\s+(?:the\s+)?consumer\b", re.IGNORECASE),
    re.compile(r"\blive\s+(?:devhub|consumer|llm)\s+(?:run|execution|call)\b", re.IGNORECASE),
)

_OUTCOME_GUARANTEE_PATTERNS = (
    re.compile(r"\bguarantee(?:d|s)?\b", re.IGNORECASE),
    re.compile(r"\bpermit\s+will\s+(?:be\s+)?(?:approved|issued|granted)\b", re.IGNORECASE),
    re.compile(r"\bapproval\s+is\s+(?:certain|assured|guaranteed)\b", re.IGNORECASE),
    re.compile(r"\b(?:legally|code)\s+compliant\b", re.IGNORECASE),
    re.compile(r"\byou\s+will\s+(?:pass|receive|obtain)\s+(?:inspection|approval|the\s+permit)\b", re.IGNORECASE),
)

_MUTATION_KEY_FRAGMENTS = (
    "active_guardrail_mutation",
    "mutates_active_guardrails",
    "mutation_enabled",
    "replace_active_guardrails",
    "activate_guardrails",
)

_STALE_CURRENT_VALUES = {"stale_current", "current_but_stale", "stale-current"}


@dataclass(frozen=True)
class ExplanationPacketFinding:
    code: str
    path: str
    message: str


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _require_fixture_only(name: str, packet: dict[str, Any]) -> None:
    if packet.get("uses_llm") is not False:
        raise ValueError(f"{name} must declare uses_llm=false")
    if packet.get("promotes_active_guardrails") is not False:
        raise ValueError(f"{name} must declare promotes_active_guardrails=false")


def _index(items: list[dict[str, Any]], name: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for item in items:
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            raise ValueError(f"{name} entries must have string ids")
        indexed[item_id] = item
    return indexed


def build_explanation_packet(
    guardrail_packet_path: Path,
    process_model_packet_path: Path,
    action_matrix_path: Path,
) -> dict[str, Any]:
    guardrail_packet = load_json(guardrail_packet_path)
    process_packet = load_json(process_model_packet_path)
    matrix_packet = load_json(action_matrix_path)

    _require_fixture_only("guardrail packet", guardrail_packet)
    _require_fixture_only("process model packet", process_packet)
    _require_fixture_only("action matrix", matrix_packet)

    guardrails = _index(guardrail_packet.get("guardrails", []), "guardrails")
    impacts = _index(process_packet.get("process_impacts", []), "process_impacts")

    explanations: list[dict[str, Any]] = []
    for action in matrix_packet.get("actions", []):
        action_id = action.get("id")
        action_class = action.get("action_class")
        if not isinstance(action_id, str) or not action_id:
            raise ValueError("actions must have string ids")
        if action_class not in _ALLOWED_CLASSES:
            raise ValueError(f"unsupported action class for {action_id}: {action_class}")

        guardrail_refs = action.get("guardrail_refs", [])
        impact_refs = action.get("impact_refs", [])
        if not guardrail_refs or not impact_refs:
            raise ValueError(f"{action_id} must cite guardrail_refs and impact_refs")

        cited_guardrails = [guardrails[ref] for ref in guardrail_refs]
        cited_impacts = [impacts[ref] for ref in impact_refs]
        citations = []
        for item in [*cited_guardrails, *cited_impacts, action]:
            citation = item.get("citation")
            if isinstance(citation, str) and citation not in citations:
                citations.append(citation)
        if not citations:
            raise ValueError(f"{action_id} must produce at least one citation")

        guardrail_text = "; ".join(item["requirement"] for item in cited_guardrails)
        impact_text = "; ".join(item["impact"] for item in cited_impacts)
        explanation = (
            f"Treat '{action['action']}' as a {_LABELS[action_class]} because "
            f"{guardrail_text}. Process impact: {impact_text}."
        )

        explanations.append(
            {
                "id": action_id,
                "action": action["action"],
                "action_class": action_class,
                "expected_outcome": action["expected_outcome"],
                "predicate_ids": list(guardrail_refs),
                "process_ids": list(impact_refs),
                "explanation": explanation,
                "citations": citations,
            }
        )

    packet = {
        "packet_id": "fixture-first-guardrail-explanation-regression",
        "uses_llm": False,
        "promotes_active_guardrails": False,
        "known_predicate_ids": sorted(guardrails),
        "known_process_ids": sorted(impacts),
        "source_packets": [
            guardrail_packet.get("packet_id"),
            process_packet.get("packet_id"),
            matrix_packet.get("packet_id"),
        ],
        "explanations": explanations,
    }
    require_valid_explanation_packet(packet)
    return packet


def validate_explanation_packet(packet: Mapping[str, Any]) -> list[ExplanationPacketFinding]:
    findings: list[ExplanationPacketFinding] = []

    if packet.get("uses_llm") is not False:
        findings.append(ExplanationPacketFinding("live_llm_execution_claim", "$.uses_llm", "Regression packets must declare uses_llm=false."))
    if packet.get("promotes_active_guardrails") is not False:
        findings.append(ExplanationPacketFinding("active_guardrail_mutation_flag", "$.promotes_active_guardrails", "Regression packets must not promote active guardrails."))

    known_predicate_ids = _string_set(packet.get("known_predicate_ids"))
    known_process_ids = _string_set(packet.get("known_process_ids"))
    explanations = packet.get("explanations")
    if not isinstance(explanations, Sequence) or isinstance(explanations, (str, bytes)):
        findings.append(ExplanationPacketFinding("missing_explanations", "$.explanations", "Regression packet must include explanation rows."))
    else:
        for index, explanation in enumerate(explanations):
            path = f"$.explanations[{index}]"
            if not isinstance(explanation, Mapping):
                findings.append(ExplanationPacketFinding("invalid_explanation_row", path, "Each explanation row must be an object."))
                continue
            _validate_explanation_row(explanation, path, known_predicate_ids, known_process_ids, findings)

    _scan_tree(packet, "$", findings)
    return findings


def require_valid_explanation_packet(packet: Mapping[str, Any]) -> None:
    findings = validate_explanation_packet(packet)
    if findings:
        details = "; ".join(f"{finding.code} at {finding.path}: {finding.message}" for finding in findings)
        raise ValueError(f"invalid guardrail explanation regression packet: {details}")


def _validate_explanation_row(
    row: Mapping[str, Any],
    path: str,
    known_predicate_ids: set[str],
    known_process_ids: set[str],
    findings: list[ExplanationPacketFinding],
) -> None:
    text = row.get("explanation")
    if not isinstance(text, str) or not text.strip():
        findings.append(ExplanationPacketFinding("missing_explanation", f"{path}.explanation", "Each row must include explanation text."))
        text = ""

    citations = _string_list(row.get("citations"))
    source_evidence_ids = _string_list(row.get("source_evidence_ids"))
    if not citations and not source_evidence_ids:
        findings.append(ExplanationPacketFinding("uncited_explanation_claim", path, "Every explanation claim must cite source evidence."))

    predicate_ids = _string_list(row.get("predicate_ids"))
    if not predicate_ids:
        findings.append(ExplanationPacketFinding("missing_predicate_ids", f"{path}.predicate_ids", "Every explanation must identify supporting predicate ids."))
    for predicate_id in predicate_ids:
        if known_predicate_ids and predicate_id not in known_predicate_ids:
            findings.append(ExplanationPacketFinding("unknown_predicate_id", f"{path}.predicate_ids", f"Unknown predicate id: {predicate_id}"))

    process_ids = _string_list(row.get("process_ids"))
    if not process_ids:
        findings.append(ExplanationPacketFinding("missing_process_ids", f"{path}.process_ids", "Every explanation must identify supporting process ids."))
    for process_id in process_ids:
        if known_process_ids and process_id not in known_process_ids:
            findings.append(ExplanationPacketFinding("unknown_process_id", f"{path}.process_ids", f"Unknown process id: {process_id}"))

    action_class = row.get("action_class")
    expected_outcome = row.get("expected_outcome")
    if action_class == "refused_consequential_action" or expected_outcome == "refuse":
        lowered = text.lower()
        if not lowered.strip() or not any(word in lowered for word in _REFUSAL_WORDS):
            findings.append(ExplanationPacketFinding("missing_refusal_explanation", f"{path}.explanation", "Refused consequential actions require explicit refusal explanation text."))


def _scan_tree(value: Any, path: str, findings: list[ExplanationPacketFinding]) -> None:
    if isinstance(value, Mapping):
        stale_current = _has_stale_current_marker(value)
        acknowledged = value.get("stale_current_acknowledgement") is True or value.get("acknowledged_stale_current_evidence") is True
        if stale_current and not acknowledged:
            findings.append(ExplanationPacketFinding("stale_current_evidence_without_acknowledgement", path, "Stale-current evidence requires an explicit acknowledgement."))

        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            lowered_key = key_text.lower()
            if any(fragment in lowered_key for fragment in _PRIVATE_KEY_FRAGMENTS):
                findings.append(ExplanationPacketFinding("private_case_fact", child_path, "Regression packets must not include private case facts or private artifacts."))
            if any(fragment in lowered_key for fragment in _LIVE_EXECUTION_KEY_FRAGMENTS) and child not in (False, None, "false", "disabled"):
                findings.append(ExplanationPacketFinding("live_llm_or_consumer_execution_claim", child_path, "Regression packets must not claim live LLM or consumer execution."))
            if any(fragment in lowered_key for fragment in _MUTATION_KEY_FRAGMENTS) and child not in (False, None, "false", "disabled"):
                findings.append(ExplanationPacketFinding("active_guardrail_mutation_flag", child_path, "Regression packets must not carry active guardrail mutation flags."))
            _scan_tree(child, child_path, findings)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            _scan_tree(child, f"{path}[{index}]", findings)
    elif isinstance(value, str):
        for pattern in _PRIVATE_VALUE_PATTERNS:
            if pattern.search(value):
                findings.append(ExplanationPacketFinding("private_case_fact", path, "Regression packets must not expose private case fact values."))
                break
        if any(pattern.search(value) for pattern in _LIVE_EXECUTION_TEXT_PATTERNS):
            findings.append(ExplanationPacketFinding("live_llm_or_consumer_execution_claim", path, "Regression packets must not claim live LLM or consumer execution."))
        if any(pattern.search(value) for pattern in _OUTCOME_GUARANTEE_PATTERNS):
            findings.append(ExplanationPacketFinding("legal_or_permitting_outcome_guarantee", path, "Explanations must not guarantee legal compliance or permitting outcomes."))


def _has_stale_current_marker(value: Mapping[str, Any]) -> bool:
    for key in ("evidence_freshness", "freshness_status", "source_freshness", "evidence_status"):
        marker = value.get(key)
        if isinstance(marker, str) and marker.lower() in _STALE_CURRENT_VALUES:
            return True
    return value.get("stale_current_evidence") is True


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _string_set(value: Any) -> set[str]:
    return set(_string_list(value))


__all__ = [
    "ExplanationPacketFinding",
    "build_explanation_packet",
    "load_json",
    "require_valid_explanation_packet",
    "validate_explanation_packet",
]
