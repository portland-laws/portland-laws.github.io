"""Validation for PP&D guardrail consumer contract audit packets.

The validator is intentionally fixture-friendly and side-effect free. It accepts a
plain mapping parsed from JSON and returns deterministic findings that can be
used by tests, daemon checks, or future contract adapters without executing any
live PP&D, DevHub, or LLM workflow.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


PRIVATE_PATH_RE = re.compile(
    r"(?:^|\s)(?:file://|/home/|/Users/|/var/folders/|/tmp/|/private/|[A-Za-z]:\\\\|[A-Za-z]:/)"
)
PRIVATE_ARTIFACT_RE = re.compile(
    r"(?:auth[_-]?state|cookie|credential|session[_-]?state|trace\.zip|\.har\b|screenshots?/|downloads?/)",
    re.IGNORECASE,
)
LIVE_EXECUTION_RE = re.compile(
    r"\b(?:live\s+llm|llm\s+(?:ran|executed|called)|devhub\s+(?:ran|executed|submitted|uploaded|paid|scheduled|cancelled)|browser\s+(?:executed|submitted|uploaded)|playwright\s+(?:submitted|uploaded))\b",
    re.IGNORECASE,
)
CONSEQUENTIAL_ACTION_WORDS = {
    "submit",
    "submission",
    "upload",
    "payment",
    "pay",
    "schedule",
    "cancel",
    "certify",
    "acknowledge",
    "sign",
    "purchase",
}
SAFE_DOWNGRADE_WORDS = {"safe", "allowed", "reversible", "draft", "read_only", "read-only", "informational"}


@dataclass(frozen=True)
class AuditFinding:
    """A deterministic validation finding for a consumer audit packet."""

    code: str
    message: str
    path: str


def validate_guardrail_consumer_contract_audit_packet(packet: Mapping[str, Any]) -> list[AuditFinding]:
    """Return validation findings for an audit packet.

    The function performs only structural/content checks. It does not load files,
    call model providers, open browsers, or contact Portland systems.
    """

    findings: list[AuditFinding] = []
    findings.extend(_validate_contract_gaps(packet))
    findings.extend(_validate_private_material(packet))
    findings.extend(_validate_stale_current_claims(packet))
    findings.extend(_validate_blocked_action_downgrades(packet))
    findings.extend(_validate_manual_handoff(packet))
    findings.extend(_validate_live_execution_claims(packet))
    findings.extend(_validate_enabled_consequential_controls(packet))
    return findings


def assert_valid_guardrail_consumer_contract_audit_packet(packet: Mapping[str, Any]) -> None:
    """Raise ``ValueError`` when a packet violates the consumer audit contract."""

    findings = validate_guardrail_consumer_contract_audit_packet(packet)
    if findings:
        formatted = "; ".join(f"{finding.code} at {finding.path}: {finding.message}" for finding in findings)
        raise ValueError(formatted)


def is_valid_guardrail_consumer_contract_audit_packet(packet: Mapping[str, Any]) -> bool:
    """Return ``True`` when the packet has no audit findings."""

    return not validate_guardrail_consumer_contract_audit_packet(packet)


def _validate_contract_gaps(packet: Mapping[str, Any]) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for path, gap in _iter_named_items(packet, ("contract_gaps", "gaps", "missing_contract_terms")):
        if not isinstance(gap, Mapping):
            continue
        if not _has_citation(gap):
            findings.append(
                AuditFinding(
                    "uncited_contract_gap",
                    "contract gaps must include source evidence or citations",
                    path,
                )
            )
    return findings


def _validate_private_material(packet: Mapping[str, Any]) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for path, value in _walk(packet):
        key = path.rsplit(".", 1)[-1].lower()
        if "private_case_fact" in key or key in {"private_facts", "private_fact"}:
            findings.append(
                AuditFinding(
                    "private_case_fact",
                    "consumer audit packets must not contain private case facts",
                    path,
                )
            )
            continue
        if isinstance(value, Mapping):
            classification = str(value.get("privacy_classification", value.get("privacy", ""))).lower()
            if classification in {"private", "confidential", "credential", "payment", "auth_state"}:
                findings.append(
                    AuditFinding(
                        "private_case_fact",
                        "consumer audit packets must not contain private or confidential facts",
                        path,
                    )
                )
        if isinstance(value, str) and (PRIVATE_PATH_RE.search(value) or PRIVATE_ARTIFACT_RE.search(value)):
            findings.append(
                AuditFinding(
                    "local_private_path",
                    "consumer audit packets must not expose local private paths or session artifacts",
                    path,
                )
            )
    return findings


def _validate_stale_current_claims(packet: Mapping[str, Any]) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for path, claim in _iter_named_items(packet, ("current_claims", "claims", "source_claims")):
        if not isinstance(claim, Mapping):
            continue
        says_current = str(claim.get("status", claim.get("claim_status", ""))).lower() == "current"
        stale = bool(claim.get("is_stale")) or str(claim.get("freshness_status", "")).lower() == "stale"
        acknowledged = bool(
            claim.get("staleness_acknowledged")
            or claim.get("stale_current_acknowledged")
            or claim.get("requires_reverification_acknowledged")
        )
        if says_current and stale and not acknowledged:
            findings.append(
                AuditFinding(
                    "stale_current_claim_without_acknowledgement",
                    "stale sources may not be presented as current without an explicit acknowledgement",
                    path,
                )
            )
    return findings


def _validate_blocked_action_downgrades(packet: Mapping[str, Any]) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    blocked_labels = {_action_label(action) for _, action in _iter_named_items(packet, ("blocked_actions", "refused_actions"))}
    blocked_labels.discard("")

    for path, action in _iter_named_items(packet, ("next_safe_actions", "proposed_actions", "allowed_actions")):
        if not isinstance(action, Mapping):
            continue
        label = _action_label(action)
        classification = str(action.get("classification", action.get("safety_classification", ""))).lower()
        downgraded = bool(action.get("downgraded_from_blocked")) or str(action.get("source_decision", "")).lower() == "blocked"
        if (label and label in blocked_labels and classification in SAFE_DOWNGRADE_WORDS) or downgraded:
            findings.append(
                AuditFinding(
                    "blocked_action_downgrade",
                    "blocked actions may not be reclassified as safe, reversible, draft, or allowed",
                    path,
                )
            )
    return findings


def _validate_manual_handoff(packet: Mapping[str, Any]) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for path, action in _iter_named_items(packet, ("blocked_actions", "refused_actions", "consequential_actions", "action_gates")):
        if not isinstance(action, Mapping):
            continue
        if _is_consequential_action(action) and not _has_manual_handoff(action):
            findings.append(
                AuditFinding(
                    "missing_manual_handoff_expectation",
                    "consequential or blocked actions must state the manual handoff expectation",
                    path,
                )
            )
    return findings


def _validate_live_execution_claims(packet: Mapping[str, Any]) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for path, value in _walk(packet):
        if isinstance(value, Mapping):
            executor = str(value.get("executor", value.get("system", ""))).lower()
            mode = str(value.get("mode", value.get("execution_mode", ""))).lower()
            status = str(value.get("status", value.get("claim", ""))).lower()
            if executor in {"llm", "devhub", "playwright", "browser"} and mode in {"live", "executed", "remote"}:
                findings.append(
                    AuditFinding(
                        "live_execution_claim",
                        "audit packets may not claim live LLM, DevHub, browser, or Playwright execution",
                        path,
                    )
                )
            elif executor in {"llm", "devhub"} and any(word in status for word in ("executed", "submitted", "uploaded", "paid")):
                findings.append(
                    AuditFinding(
                        "live_execution_claim",
                        "audit packets may not claim live LLM or DevHub execution outcomes",
                        path,
                    )
                )
        elif isinstance(value, str) and LIVE_EXECUTION_RE.search(value):
            findings.append(
                AuditFinding(
                    "live_execution_claim",
                    "audit packets may not claim live LLM, DevHub, browser, or Playwright execution",
                    path,
                )
            )
    return findings


def _validate_enabled_consequential_controls(packet: Mapping[str, Any]) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for path, value in _iter_named_items(packet, ("controls", "automation_controls", "action_controls")):
        if not isinstance(value, Mapping):
            continue
        enabled = bool(value.get("enabled") or value.get("automation_enabled"))
        if enabled and _is_consequential_action(value):
            findings.append(
                AuditFinding(
                    "enabled_consequential_control",
                    "consequential controls must be disabled in consumer audit packets",
                    path,
                )
            )
    for path, value in _iter_named_items(packet, ("actions", "proposed_actions", "next_safe_actions")):
        if not isinstance(value, Mapping):
            continue
        enabled = bool(value.get("enabled") or value.get("automation_enabled"))
        if enabled and _is_consequential_action(value):
            findings.append(
                AuditFinding(
                    "enabled_consequential_control",
                    "consequential actions may not have enabled automation controls",
                    path,
                )
            )
    return findings


def _has_citation(item: Mapping[str, Any]) -> bool:
    for key in ("source_evidence_ids", "citations", "citation_ids", "source_citations"):
        value = item.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) > 0:
            return True
    return bool(item.get("citation") or item.get("source_evidence_id"))


def _has_manual_handoff(item: Mapping[str, Any]) -> bool:
    value = item.get("manual_handoff_expectation", item.get("manual_handoff"))
    return bool(value or item.get("requires_manual_handoff") or item.get("requires_attendance"))


def _is_consequential_action(item: Mapping[str, Any]) -> bool:
    action_type = str(item.get("action_type", item.get("type", ""))).lower()
    classification = str(item.get("classification", item.get("safety_classification", ""))).lower()
    label = _action_label(item).lower()
    if classification in {"consequential", "blocked", "official", "irreversible"}:
        return True
    if action_type in {"consequential", "blocked", "official_action", "payment", "submission", "upload", "schedule", "cancel"}:
        return True
    return any(word in label for word in CONSEQUENTIAL_ACTION_WORDS)


def _action_label(item: Any) -> str:
    if not isinstance(item, Mapping):
        return ""
    for key in ("action_id", "id", "action", "name", "label"):
        value = item.get(key)
        if value:
            return str(value).strip().lower()
    return ""


def _iter_named_items(value: Any, names: Iterable[str], path: str = "$") -> Iterable[tuple[str, Any]]:
    wanted = set(names)
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in wanted:
                if isinstance(child, Sequence) and not isinstance(child, (str, bytes, bytearray)):
                    for index, item in enumerate(child):
                        yield f"{child_path}[{index}]", item
                else:
                    yield child_path, child
            yield from _iter_named_items(child, wanted, child_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            yield from _iter_named_items(child, wanted, f"{path}[{index}]")


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")
