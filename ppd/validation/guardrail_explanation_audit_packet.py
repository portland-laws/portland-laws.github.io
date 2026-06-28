"""Validation for fixture-first PP&D guardrail explanation audit packets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Any, Iterable


_REQUIRED_STATES = frozenset({
    "allowed_local_preview",
    "missing_fact",
    "refused_action",
    "manual_handoff",
    "stale_evidence",
    "unresolved_review",
})

_REQUIRED_FORBIDDEN_SIDE_EFFECTS = frozenset({
    "launch_devhub",
    "read_private_files",
    "create_auth_state",
    "create_trace",
    "download_documents",
    "submit_application",
    "upload_documents",
    "pay_fee",
    "certify_or_attest",
})

_PRIVATE_KEY_MARKERS = (
    "password",
    "passcode",
    "mfa",
    "captcha",
    "cookie",
    "token",
    "secret",
    "credential",
    "auth_state",
    "session",
    "trace",
    "har",
    "screenshot",
    "payment_card",
    "card_number",
    "cvv",
    "routing_number",
    "account_number",
    "ssn",
    "private_file",
    "local_file",
    "download_path",
    "raw_body",
)

_PRIVATE_VALUE_MARKERS = (
    "BEGIN PRIVATE",
    "PRIVATE_VALUE",
    "AUTH_STATE",
    "SESSION_COOKIE",
    "/home/",
    "/Users/",
    "playwright/.auth",
    ".har",
    ".trace",
)

_AGENT_EXECUTABLE_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(?:i|we|the agent|this agent)\s+(?:can|will|may|am able to|are able to|shall)\s+(?:[^.?!]{0,40}\s)?(?:pay|make payment|enter payment|upload|submit|file|schedule|cancel|certify|attest)\b",
        r"\b(?:i|we|the agent|this agent)\s+(?:can|will|may|am able to|are able to|shall)\s+(?:[^.?!]{0,40}\s)?(?:payment|upload|submission|scheduling|cancellation|certification)\b",
        r"\b(?:payment|upload|submission|scheduling|cancellation|certification)\s+(?:is|are)\s+(?:handled|performed|completed|executed)\s+by\s+(?:me|us|the agent)\b",
    )
)


@dataclass(frozen=True)
class GuardrailExplanationAuditFinding:
    code: str
    path: str
    message: str


def validate_guardrail_explanation_audit_packet(packet: dict[str, Any]) -> list[GuardrailExplanationAuditFinding]:
    """Return validation findings for a guardrail explanation audit packet."""

    findings: list[GuardrailExplanationAuditFinding] = []
    if not isinstance(packet, dict):
        return [GuardrailExplanationAuditFinding("invalid_packet", "$", "Packet must be a dictionary.")]

    _validate_fixture_first_flags(packet, findings)
    _validate_private_values(packet, findings)
    _validate_guardrail_inputs_freshness(packet, findings)
    _validate_sampled_outcomes(packet, findings)
    return findings


def require_valid_guardrail_explanation_audit_packet(packet: dict[str, Any]) -> None:
    findings = validate_guardrail_explanation_audit_packet(packet)
    if findings:
        details = "; ".join(f"{finding.code} at {finding.path}: {finding.message}" for finding in findings)
        raise ValueError(f"invalid guardrail explanation audit packet: {details}")


def finding_codes(findings: Iterable[GuardrailExplanationAuditFinding]) -> set[str]:
    return {finding.code for finding in findings}


def _validate_fixture_first_flags(packet: dict[str, Any], findings: list[GuardrailExplanationAuditFinding]) -> None:
    for key in ("devhub_launch_required", "private_file_access_required", "live_crawl_required"):
        if packet.get(key) is not False:
            findings.append(GuardrailExplanationAuditFinding(
                "fixture_first_violation",
                f"$.{key}",
                "Explanation audit packets must not require live DevHub, private file access, or crawling.",
            ))

    side_effects = packet.get("forbidden_side_effects")
    if not isinstance(side_effects, list) or set(side_effects) != set(_REQUIRED_FORBIDDEN_SIDE_EFFECTS):
        findings.append(GuardrailExplanationAuditFinding(
            "missing_forbidden_side_effect",
            "$.forbidden_side_effects",
            "Packet must enumerate all forbidden DevHub, private-file, download, payment, upload, submission, and certification effects.",
        ))


def _validate_private_values(packet: dict[str, Any], findings: list[GuardrailExplanationAuditFinding]) -> None:
    for path, value in _walk(packet):
        key = path.rsplit(".", 1)[-1].lower()
        if any(marker in key for marker in _PRIVATE_KEY_MARKERS):
            if value not in (False, None, [], {}) and not _is_allowed_policy_path(path):
                findings.append(GuardrailExplanationAuditFinding(
                    "private_value",
                    path,
                    "Packets must not include private values, auth/session artifacts, traces, payment details, or local file paths.",
                ))
        if isinstance(value, str) and any(marker in value for marker in _PRIVATE_VALUE_MARKERS):
            findings.append(GuardrailExplanationAuditFinding(
                "private_value",
                path,
                "Packets must not include private values, auth/session artifacts, traces, payment details, or local file paths.",
            ))


def _validate_guardrail_inputs_freshness(packet: dict[str, Any], findings: list[GuardrailExplanationAuditFinding]) -> None:
    inputs = packet.get("guardrail_inputs")
    if not isinstance(inputs, dict):
        findings.append(GuardrailExplanationAuditFinding(
            "missing_guardrail_inputs",
            "$.guardrail_inputs",
            "Packet must declare guardrail input snapshot and audit dates.",
        ))
        return

    source_snapshot_date = _parse_date(inputs.get("source_snapshot_date"))
    audit_date = _parse_date(inputs.get("audit_date"))
    freshness_window_days = inputs.get("freshness_window_days")
    if source_snapshot_date is None or audit_date is None or not isinstance(freshness_window_days, int):
        findings.append(GuardrailExplanationAuditFinding(
            "invalid_guardrail_inputs",
            "$.guardrail_inputs",
            "Guardrail inputs must include ISO dates and an integer freshness window.",
        ))
        return

    if source_snapshot_date > audit_date or (audit_date - source_snapshot_date).days > freshness_window_days:
        findings.append(GuardrailExplanationAuditFinding(
            "stale_guardrail_input",
            "$.guardrail_inputs.source_snapshot_date",
            "Guardrail inputs are stale and must be refreshed before explanation use.",
        ))


def _validate_sampled_outcomes(packet: dict[str, Any], findings: list[GuardrailExplanationAuditFinding]) -> None:
    outcomes = packet.get("sampled_outcomes")
    if not isinstance(outcomes, list):
        findings.append(GuardrailExplanationAuditFinding("missing_sampled_outcomes", "$.sampled_outcomes", "Packet must include sampled outcomes."))
        return

    states = {outcome.get("state") for outcome in outcomes if isinstance(outcome, dict)}
    if states != set(_REQUIRED_STATES):
        findings.append(GuardrailExplanationAuditFinding(
            "missing_required_state",
            "$.sampled_outcomes",
            "Packet must cover allowed preview, missing fact, refused action, manual handoff, stale evidence, and unresolved review states.",
        ))

    for index, outcome in enumerate(outcomes):
        path = f"$.sampled_outcomes[{index}]"
        if not isinstance(outcome, dict):
            findings.append(GuardrailExplanationAuditFinding("invalid_outcome", path, "Each sampled outcome must be a dictionary."))
            continue
        _validate_outcome(path, outcome, findings)


def _validate_outcome(path: str, outcome: dict[str, Any], findings: list[GuardrailExplanationAuditFinding]) -> None:
    explanation = outcome.get("user_facing_explanation")
    citations = outcome.get("citations")
    state = outcome.get("state")

    if not isinstance(explanation, str) or not explanation.strip():
        findings.append(GuardrailExplanationAuditFinding(
            "missing_explanation",
            f"{path}.user_facing_explanation",
            "Each outcome must include user-facing explanation text.",
        ))
    elif _implies_agent_can_execute_consequential_action(explanation):
        findings.append(GuardrailExplanationAuditFinding(
            "agent_executable_consequential_language",
            f"{path}.user_facing_explanation",
            "Explanation text must not imply payment, upload, submission, scheduling, cancellation, or certification is agent-executable.",
        ))

    if not isinstance(citations, list) or not citations:
        findings.append(GuardrailExplanationAuditFinding(
            "uncited_explanation_text",
            f"{path}.citations",
            "Every user-facing explanation must include supporting citation evidence.",
        ))
    else:
        for citation_index, citation in enumerate(citations):
            citation_path = f"{path}.citations[{citation_index}]"
            if not isinstance(citation, dict):
                findings.append(GuardrailExplanationAuditFinding("invalid_citation", citation_path, "Each citation must be a dictionary."))
                continue
            source_id = citation.get("source_id")
            supports = citation.get("supports")
            if not isinstance(source_id, str) or not source_id.startswith("fixture."):
                findings.append(GuardrailExplanationAuditFinding(
                    "uncited_explanation_text",
                    f"{citation_path}.source_id",
                    "Explanation citations must reference committed fixture evidence.",
                ))
            if not isinstance(supports, str) or not supports.strip():
                findings.append(GuardrailExplanationAuditFinding(
                    "uncited_explanation_text",
                    f"{citation_path}.supports",
                    "Explanation citations must explain what they support.",
                ))

    if state == "refused_action":
        if not outcome.get("refused_action"):
            findings.append(GuardrailExplanationAuditFinding(
                "missing_refused_action_explanation",
                f"{path}.refused_action",
                "Refused-action outcomes must identify the refused action.",
            ))
        if not _contains_refusal_language(explanation):
            findings.append(GuardrailExplanationAuditFinding(
                "missing_refused_action_explanation",
                f"{path}.user_facing_explanation",
                "Refused-action outcomes must explain that the action is blocked or refused.",
            ))

    if state == "manual_handoff":
        rationale = outcome.get("manual_handoff_rationale") or outcome.get("handoff_reason")
        if not isinstance(rationale, str) or not rationale.strip():
            findings.append(GuardrailExplanationAuditFinding(
                "missing_manual_handoff_rationale",
                path,
                "Manual-handoff outcomes must include a non-empty rationale.",
            ))


def _contains_refusal_language(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    return any(marker in lowered for marker in ("cannot", "can't", "refuse", "blocked", "not allowed"))


def _implies_agent_can_execute_consequential_action(explanation: str) -> bool:
    return any(pattern.search(explanation) for pattern in _AGENT_EXECUTABLE_PATTERNS)


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, nested in value.items():
            yield from _walk(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _walk(nested, f"{path}[{index}]")


def _is_allowed_policy_path(path: str) -> bool:
    return path.startswith("$.forbidden_side_effects") or path.endswith("_required")


def _parse_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


__all__ = [
    "GuardrailExplanationAuditFinding",
    "finding_codes",
    "require_valid_guardrail_explanation_audit_packet",
    "validate_guardrail_explanation_audit_packet",
]
