"""Validation for PP&D guardrail bundle update candidate packets.

The validator is intentionally side-effect free. It accepts plain dictionaries so
supervisor fixtures, daemon tasks, and future compiler output can share the same
preflight without importing broader contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set


@dataclass(frozen=True)
class ValidationFinding:
    """A deterministic candidate-packet rejection reason."""

    code: str
    message: str
    path: str

    def as_dict(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


CONSEQUENTIAL_ACTION_WORDS = (
    "submit",
    "submission",
    "certify",
    "certification",
    "acknowledge",
    "upload correction",
    "official upload",
    "pay",
    "payment",
    "purchase",
    "schedule inspection",
    "cancel",
    "withdraw",
    "reactivate",
    "extension",
)

LIVE_EXECUTION_WORDS = (
    "live compiler",
    "compiler executed",
    "executed compiler",
    "ran compiler",
    "live consumer",
    "consumer executed",
    "executed consumer",
    "production consumer",
    "called consumer",
    "live run",
)

OUTCOME_GUARANTEE_WORDS = (
    "guarantee",
    "guaranteed",
    "will be approved",
    "will approve",
    "approval is assured",
    "permit will issue",
    "permit must issue",
    "legally valid",
    "legal outcome",
    "no legal risk",
    "cannot be denied",
)

PRIVATE_CLASSIFICATIONS = {
    "private",
    "confidential",
    "restricted",
    "user_private",
    "case_private",
    "devhub_authenticated_private",
}


class GuardrailBundleCandidateValidator:
    """Validate guardrail bundle update candidate packets before acceptance."""

    def __init__(
        self,
        known_requirement_ids: Optional[Iterable[str]] = None,
        known_process_ids: Optional[Iterable[str]] = None,
        known_guardrail_ids: Optional[Iterable[str]] = None,
    ) -> None:
        self.known_requirement_ids = _string_set(known_requirement_ids)
        self.known_process_ids = _string_set(known_process_ids)
        self.known_guardrail_ids = _string_set(known_guardrail_ids)

    def validate(self, packet: Mapping[str, Any]) -> List[ValidationFinding]:
        findings: List[ValidationFinding] = []
        findings.extend(self._validate_known_ids(packet))
        findings.extend(self._validate_citations(packet))
        findings.extend(self._validate_stale_evidence(packet))
        findings.extend(self._validate_private_case_facts(packet))
        findings.extend(self._validate_live_execution_claims(packet))
        findings.extend(self._validate_outcome_guarantees(packet))
        findings.extend(self._validate_consequential_actions(packet))
        findings.extend(self._validate_required_review_controls(packet))
        findings.extend(self._validate_mutation_flags(packet))
        return findings

    def _validate_known_ids(self, packet: Mapping[str, Any]) -> List[ValidationFinding]:
        findings: List[ValidationFinding] = []
        known_requirements = self.known_requirement_ids | _string_set(packet.get("known_requirement_ids"))
        known_processes = self.known_process_ids | _string_set(packet.get("known_process_ids"))
        known_guardrails = self.known_guardrail_ids | _string_set(packet.get("known_guardrail_ids"))

        for path, value in _walk(packet):
            key = path.rsplit(".", 1)[-1].lower()
            if key in {"requirement_id", "requirement_ids", "affected_requirement_ids"}:
                for item in _as_string_list(value):
                    if known_requirements and item not in known_requirements:
                        findings.append(_finding("unknown_requirement_id", "Requirement ID is not registered for this packet.", path))
            if key in {"process_id", "process_ids", "affected_process_ids"}:
                for item in _as_string_list(value):
                    if known_processes and item not in known_processes:
                        findings.append(_finding("unknown_process_id", "Process ID is not registered for this packet.", path))
            if key in {"guardrail_id", "guardrail_ids", "guardrail_bundle_id", "guardrail_bundle_ids"}:
                for item in _as_string_list(value):
                    if known_guardrails and item not in known_guardrails:
                        findings.append(_finding("unknown_guardrail_id", "Guardrail ID is not registered for this packet.", path))
        return findings

    def _validate_citations(self, packet: Mapping[str, Any]) -> List[ValidationFinding]:
        findings: List[ValidationFinding] = []
        changes = packet.get("changes", [])
        if isinstance(changes, Mapping):
            changes = [changes]
        if not isinstance(changes, Sequence) or isinstance(changes, (str, bytes)):
            return [_finding("invalid_changes", "Changes must be a list or mapping.", "changes")]

        for index, change in enumerate(changes):
            if not isinstance(change, Mapping):
                continue
            change_type = str(change.get("type") or change.get("change_type") or "").lower()
            touches_predicate = "predicate" in change_type or "predicate" in change
            touches_explanation = "explanation" in change_type or "explanation" in change or "explanation_template" in change
            if touches_predicate or touches_explanation:
                citations = _as_string_list(change.get("source_evidence_ids") or change.get("citations") or change.get("citation_ids"))
                if not citations:
                    findings.append(_finding("uncited_guardrail_change", "Predicate and explanation changes require source evidence citations.", "changes.%d" % index))
        return findings

    def _validate_stale_evidence(self, packet: Mapping[str, Any]) -> List[ValidationFinding]:
        findings: List[ValidationFinding] = []
        for path, value in _walk(packet):
            if not isinstance(value, Mapping):
                continue
            status = str(value.get("freshness_status") or value.get("status") or "").lower()
            current = bool(value.get("current") is True or value.get("is_current") is True)
            stale = status in {"stale", "expired", "superseded"} or value.get("stale") is True
            acknowledged = value.get("stale_current_acknowledged") is True or value.get("stale_acknowledgement") is True
            if current and stale and not acknowledged:
                findings.append(_finding("stale_current_evidence_unacknowledged", "Evidence marked current is stale and lacks acknowledgement.", path))
        return findings

    def _validate_private_case_facts(self, packet: Mapping[str, Any]) -> List[ValidationFinding]:
        findings: List[ValidationFinding] = []
        for key in ("private_case_facts", "case_facts", "observed_private_values", "private_values"):
            value = packet.get(key)
            if value:
                findings.append(_finding("private_case_facts", "Candidate packets must not carry private case facts.", key))
        for path, value in _walk(packet):
            if isinstance(value, Mapping):
                classification = str(value.get("privacy_classification") or value.get("privacy") or "").lower()
                if classification in PRIVATE_CLASSIFICATIONS:
                    findings.append(_finding("private_case_facts", "Private or authenticated case material is not allowed in candidate packets.", path))
        return findings

    def _validate_live_execution_claims(self, packet: Mapping[str, Any]) -> List[ValidationFinding]:
        return _reject_text_patterns(packet, LIVE_EXECUTION_WORDS, "live_execution_claim", "Candidate packets must not claim live compiler or consumer execution.")

    def _validate_outcome_guarantees(self, packet: Mapping[str, Any]) -> List[ValidationFinding]:
        return _reject_text_patterns(packet, OUTCOME_GUARANTEE_WORDS, "outcome_guarantee", "Candidate packets must not guarantee legal or permitting outcomes.")

    def _validate_consequential_actions(self, packet: Mapping[str, Any]) -> List[ValidationFinding]:
        findings: List[ValidationFinding] = []
        for key in ("enabled_actions", "actions", "proposed_actions"):
            value = packet.get(key)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                for index, action in enumerate(value):
                    path = "%s.%d" % (key, index)
                    if _is_enabled_consequential_action(action):
                        findings.append(_finding("enabled_consequential_action", "Consequential, financial, or official actions must not be enabled by a candidate packet.", path))
        return findings

    def _validate_required_review_controls(self, packet: Mapping[str, Any]) -> List[ValidationFinding]:
        findings: List[ValidationFinding] = []
        if not str(packet.get("rollback_notes") or "").strip():
            findings.append(_finding("missing_rollback_notes", "Candidate packets require rollback notes.", "rollback_notes"))
        owners = _as_string_list(packet.get("reviewer_owners"))
        if not owners:
            findings.append(_finding("missing_reviewer_owners", "Candidate packets require at least one reviewer owner.", "reviewer_owners"))
        return findings

    def _validate_mutation_flags(self, packet: Mapping[str, Any]) -> List[ValidationFinding]:
        findings: List[ValidationFinding] = []
        for path, value in _walk(packet):
            key = path.rsplit(".", 1)[-1].lower()
            if "mutation" not in key and "mutate" not in key:
                continue
            if _truthy(value):
                findings.append(_finding("active_guardrail_mutation_flag", "Guardrail mutation flags must be inactive in update candidates.", path))
        return findings


def validate_guardrail_bundle_update_candidate(
    packet: Mapping[str, Any],
    known_requirement_ids: Optional[Iterable[str]] = None,
    known_process_ids: Optional[Iterable[str]] = None,
    known_guardrail_ids: Optional[Iterable[str]] = None,
) -> List[Dict[str, str]]:
    """Return JSON-friendly validation findings for a candidate packet."""

    validator = GuardrailBundleCandidateValidator(
        known_requirement_ids=known_requirement_ids,
        known_process_ids=known_process_ids,
        known_guardrail_ids=known_guardrail_ids,
    )
    return [finding.as_dict() for finding in validator.validate(packet)]


def _finding(code: str, message: str, path: str) -> ValidationFinding:
    return ValidationFinding(code=code, message=message, path=path)


def _string_set(values: Optional[Iterable[str]]) -> Set[str]:
    if values is None:
        return set()
    if isinstance(values, (str, bytes)):
        return {str(values)}
    return {str(value) for value in values if str(value)}


def _as_string_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return [str(value)] if str(value).strip() else []
    if isinstance(value, Sequence):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if str(value).strip() else []


def _walk(value: Any, prefix: str = "") -> Iterable[tuple]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            path = "%s.%s" % (prefix, key) if prefix else str(key)
            yield path, child
            for nested in _walk(child, path):
                yield nested
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            path = "%s.%d" % (prefix, index) if prefix else str(index)
            yield path, child
            for nested in _walk(child, path):
                yield nested


def _truthy(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "enabled", "active", "on"}
    if isinstance(value, Mapping):
        return any(_truthy(child) for child in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_truthy(child) for child in value)
    return False


def _reject_text_patterns(packet: Mapping[str, Any], patterns: Sequence[str], code: str, message: str) -> List[ValidationFinding]:
    findings: List[ValidationFinding] = []
    for path, value in _walk(packet):
        if not isinstance(value, str):
            continue
        text = value.lower()
        if any(pattern in text for pattern in patterns):
            findings.append(_finding(code, message, path))
    return findings


def _is_enabled_consequential_action(action: Any) -> bool:
    if isinstance(action, str):
        return any(word in action.lower() for word in CONSEQUENTIAL_ACTION_WORDS)
    if not isinstance(action, Mapping):
        return False
    enabled = action.get("enabled", True) is not False and str(action.get("status", "enabled")).lower() != "disabled"
    if not enabled:
        return False
    action_class = str(action.get("classification") or action.get("action_class") or action.get("category") or "").lower()
    if action_class in {"consequential", "official", "financial", "submission", "certification"}:
        return True
    joined = " ".join(str(action.get(key, "")) for key in ("id", "name", "label", "description", "action"))
    return any(word in joined.lower() for word in CONSEQUENTIAL_ACTION_WORDS)
