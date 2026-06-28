"""Fixture-first guardrail consumer contract audit packets.

This module consumes two committed, metadata-only inputs:

* a guardrail consumer integration checklist
* a post-release audit findings packet

It produces cited consumer-facing contract gaps without changing active guardrail
bundles, invoking consumers, or enabling live enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


AUDIT_CATEGORIES = (
    "missing_facts",
    "stale_evidence",
    "local_pdf_preview",
    "devhub_read_only_review",
    "manual_handoffs",
    "refused_consequential_actions",
    "disabled_live_enforcement",
)

_CATEGORY_TITLES = {
    "missing_facts": "Missing facts must remain explicit in the consumer contract",
    "stale_evidence": "Stale evidence must be surfaced before consumer action",
    "local_pdf_preview": "Local PDF preview must stay reversible and local-only",
    "devhub_read_only_review": "DevHub review must remain read-only unless gated",
    "manual_handoffs": "Manual handoffs must be exposed for attended workflows",
    "refused_consequential_actions": "Consequential actions must be refused or gated",
    "disabled_live_enforcement": "Live enforcement must stay disabled for fixture packets",
}

_PRIVATE_OR_LIVE_KEYS = {
    "access_token",
    "auth_state",
    "browser_context",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "devhub_session",
    "email",
    "har",
    "html",
    "local_path",
    "password",
    "payment_details",
    "phone",
    "raw_body",
    "raw_crawl_output",
    "raw_html",
    "raw_text",
    "refresh_token",
    "screenshot",
    "secret",
    "session",
    "session_cookie",
    "session_file",
    "session_state",
    "storage_state",
    "token",
    "trace",
    "user_input",
    "value",
}

_UNSAFE_READY_STATES = {"allowed", "enabled", "ready", "ready_to_submit", "ready_to_upload"}
_SAFE_GAP_STATES = {"blocked", "gap", "manual_handoff_required", "refused", "stale", "disabled"}


@dataclass(frozen=True)
class ConsumerContractAuditValidationResult:
    """Machine-readable validation result for consumer contract audit packets."""

    ready: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"ready": self.ready, "problems": list(self.problems)}


class ConsumerContractAuditError(ValueError):
    """Raised when an audit packet cannot be safely exposed to consumers."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid consumer contract audit packet: " + "; ".join(problems))


def build_consumer_contract_audit_packet(
    *,
    consumer_integration_checklist: Mapping[str, Any],
    post_release_audit_findings: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a cited consumer-facing gap packet from fixture inputs."""

    input_problems = _input_problems(consumer_integration_checklist, post_release_audit_findings)
    if input_problems:
        raise ConsumerContractAuditError(input_problems)

    evidence = _evidence_by_id(consumer_integration_checklist, post_release_audit_findings)
    checklist_items = _items_by_category(consumer_integration_checklist.get("consumer_contract_expectations"))
    findings = _items_by_category(post_release_audit_findings.get("audit_findings"))

    gaps = []
    for category in AUDIT_CATEGORIES:
        checklist_item = checklist_items[category]
        finding = findings[category]
        citations = _ordered_refs(checklist_item, finding)
        gaps.append(
            {
                "gap_id": f"consumer-contract-gap:{category}",
                "category": category,
                "title": _CATEGORY_TITLES[category],
                "consumer_contract_gap": _gap_text(category, checklist_item, finding),
                "required_consumer_behavior": _required_behavior(category),
                "status": _gap_status(category),
                "source_evidence_ids": citations,
                "checklist_item_id": str(checklist_item.get("item_id")),
                "audit_finding_id": str(finding.get("finding_id")),
            }
        )

    packet = {
        "packet_type": "ppd.guardrail_consumer_contract_audit.v1",
        "fixture_first": True,
        "metadata_only": True,
        "live_services_called": False,
        "consumers_invoked": False,
        "active_guardrail_bundles_changed": False,
        "source_packets": {
            "consumer_integration_checklist_id": consumer_integration_checklist.get("checklist_id"),
            "post_release_audit_packet_id": post_release_audit_findings.get("packet_id"),
        },
        "audit_categories": list(AUDIT_CATEGORIES),
        "normalized_source_evidence": list(evidence.values()),
        "consumer_contract_gaps": gaps,
    }

    result = validate_consumer_contract_audit_packet(packet)
    if not result.ready:
        raise ConsumerContractAuditError(list(result.problems))
    return packet


def validate_consumer_contract_audit_packet(packet: Mapping[str, Any]) -> ConsumerContractAuditValidationResult:
    """Validate a consumer contract audit packet before agent exposure."""

    problems: list[str] = []
    if packet.get("packet_type") != "ppd.guardrail_consumer_contract_audit.v1":
        problems.append("packet_type must be ppd.guardrail_consumer_contract_audit.v1")
    for key, expected in (
        ("fixture_first", True),
        ("metadata_only", True),
        ("live_services_called", False),
        ("consumers_invoked", False),
        ("active_guardrail_bundles_changed", False),
    ):
        if packet.get(key) is not expected:
            problems.append(f"{key} must be {expected}")

    if packet.get("audit_categories") != list(AUDIT_CATEGORIES):
        problems.append("audit_categories must match the required deterministic order")

    evidence_ids = set(_packet_evidence_by_id(packet))
    gaps = packet.get("consumer_contract_gaps")
    if not isinstance(gaps, list):
        problems.append("consumer_contract_gaps must be a list")
        gaps = []

    seen_categories: list[str] = []
    for index, gap in enumerate(gaps):
        if not isinstance(gap, Mapping):
            problems.append(f"consumer_contract_gaps[{index}] must be an object")
            continue
        category = gap.get("category")
        seen_categories.append(str(category))
        if category not in AUDIT_CATEGORIES:
            problems.append(f"consumer_contract_gaps[{index}] has unknown category")
        if not _text(gap.get("consumer_contract_gap")):
            problems.append(f"consumer_contract_gaps[{index}] is missing consumer_contract_gap")
        if not _text(gap.get("required_consumer_behavior")):
            problems.append(f"consumer_contract_gaps[{index}] is missing required_consumer_behavior")
        if str(gap.get("status") or "") not in _SAFE_GAP_STATES:
            problems.append(f"consumer_contract_gaps[{index}] has unsafe status")
        refs = gap.get("source_evidence_ids")
        if not isinstance(refs, list) or not refs:
            problems.append(f"consumer_contract_gaps[{index}] must cite source_evidence_ids")
        else:
            for ref in refs:
                if ref not in evidence_ids:
                    problems.append(f"consumer_contract_gaps[{index}] cites unknown evidence {ref}")
    if seen_categories != list(AUDIT_CATEGORIES):
        problems.append("consumer_contract_gaps must cover every required category in order")

    problems.extend(_unsafe_key_problems(packet))
    problems.extend(_unsafe_state_problems(packet))
    return ConsumerContractAuditValidationResult(ready=not problems, problems=tuple(problems))


def require_consumer_contract_audit_packet(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a packet is unsafe for consumer-facing exposure."""

    result = validate_consumer_contract_audit_packet(packet)
    if not result.ready:
        raise ValueError("invalid_consumer_contract_audit_packet: " + "; ".join(result.problems))


def _input_problems(checklist: Mapping[str, Any], findings: Mapping[str, Any]) -> list[str]:
    problems: list[str] = []
    if checklist.get("fixture_first") is not True:
        problems.append("consumer integration checklist must be fixture_first")
    if findings.get("fixture_first") is not True:
        problems.append("post-release audit findings must be fixture_first")
    for packet_name, packet in (("checklist", checklist), ("findings", findings)):
        for key in ("live_services_called", "consumers_invoked", "active_guardrail_bundles_changed"):
            if packet.get(key) not in (None, False):
                problems.append(f"{packet_name}.{key} must be false or absent")
    checklist_categories = set(_items_by_category(checklist.get("consumer_contract_expectations"), strict=False))
    finding_categories = set(_items_by_category(findings.get("audit_findings"), strict=False))
    for category in AUDIT_CATEGORIES:
        if category not in checklist_categories:
            problems.append(f"checklist lacks category {category}")
        if category not in finding_categories:
            problems.append(f"audit findings lack category {category}")
    known_evidence = set(_evidence_by_id(checklist, findings))
    for ref in _collect_refs(checklist) | _collect_refs(findings):
        if ref not in known_evidence:
            problems.append(f"input cites unknown source evidence {ref}")
    problems.extend(_unsafe_key_problems(checklist))
    problems.extend(_unsafe_key_problems(findings))
    return problems


def _items_by_category(raw: Any, *, strict: bool = True) -> dict[str, Mapping[str, Any]]:
    items: dict[str, Mapping[str, Any]] = {}
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, Mapping) and isinstance(item.get("category"), str):
                items[item["category"]] = item
    if strict:
        missing = [category for category in AUDIT_CATEGORIES if category not in items]
        if missing:
            raise ConsumerContractAuditError(["missing categories: " + ", ".join(missing)])
    return items


def _evidence_by_id(*packets: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    evidence: dict[str, dict[str, Any]] = {}
    for packet in packets:
        raw = packet.get("normalized_source_evidence") or packet.get("source_evidence") or []
        if not isinstance(raw, list):
            continue
        for item in raw:
            if not isinstance(item, Mapping):
                continue
            evidence_id = item.get("source_evidence_id") or item.get("evidence_id") or item.get("citation_id")
            if isinstance(evidence_id, str) and evidence_id:
                normalized = dict(item)
                normalized["source_evidence_id"] = evidence_id
                evidence[evidence_id] = normalized
    return evidence


def _packet_evidence_by_id(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    evidence: dict[str, Mapping[str, Any]] = {}
    raw = packet.get("normalized_source_evidence")
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, Mapping) and isinstance(item.get("source_evidence_id"), str):
                evidence[item["source_evidence_id"]] = item
    return evidence


def _ordered_refs(*values: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for value in values:
        for ref in sorted(_collect_refs(value)):
            if ref not in refs:
                refs.append(ref)
    return refs


def _collect_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, Mapping):
        for key in ("source_evidence_id", "source_evidence_ids", "citation_id", "citation_ids", "citations"):
            raw = value.get(key)
            if isinstance(raw, str) and raw:
                refs.add(raw)
            elif isinstance(raw, list):
                refs.update(item for item in raw if isinstance(item, str) and item)
        for child in value.values():
            refs.update(_collect_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.update(_collect_refs(child))
    return refs


def _gap_text(category: str, checklist_item: Mapping[str, Any], finding: Mapping[str, Any]) -> str:
    expected = str(checklist_item.get("consumer_expectation") or checklist_item.get("description") or "").strip()
    observed = str(finding.get("finding") or finding.get("summary") or "").strip()
    return f"{_CATEGORY_TITLES[category]}: expected {expected}; audit found {observed}."


def _required_behavior(category: str) -> str:
    return {
        "missing_facts": "Consumers must ask for cited missing facts before proposing draft readiness.",
        "stale_evidence": "Consumers must mark stale or expired evidence as a blocker until refreshed.",
        "local_pdf_preview": "Consumers may only offer local PDF preview metadata and must not upload or submit PDFs.",
        "devhub_read_only_review": "Consumers may review redacted DevHub metadata but must not perform authenticated changes.",
        "manual_handoffs": "Consumers must hand off attended login, MFA, certification, payment, upload, scheduling, and submission steps.",
        "refused_consequential_actions": "Consumers must refuse consequential official actions unless an exact-confirmation gate is supplied by a later attended workflow.",
        "disabled_live_enforcement": "Consumers must treat this packet as validation-only with live enforcement disabled.",
    }[category]


def _gap_status(category: str) -> str:
    return {
        "missing_facts": "gap",
        "stale_evidence": "stale",
        "local_pdf_preview": "blocked",
        "devhub_read_only_review": "blocked",
        "manual_handoffs": "manual_handoff_required",
        "refused_consequential_actions": "refused",
        "disabled_live_enforcement": "disabled",
    }[category]


def _unsafe_key_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.lower() in _PRIVATE_OR_LIVE_KEYS and child not in (None, False, "", [], {}):
                problems.append(f"private, raw, or live artifact is not allowed at {child_path}")
            problems.extend(_unsafe_key_problems(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_unsafe_key_problems(child, f"{path}[{index}]"))
    return problems


def _unsafe_state_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        category = str(value.get("category") or "")
        state = str(value.get("status") or value.get("state") or value.get("decision") or "").lower()
        if category in AUDIT_CATEGORIES and state in _UNSAFE_READY_STATES:
            problems.append(f"consumer-facing audit category is unsafely enabled at {path}")
        for key, child in value.items():
            problems.extend(_unsafe_state_problems(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_unsafe_state_problems(child, f"{path}[{index}]"))
    return problems


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
