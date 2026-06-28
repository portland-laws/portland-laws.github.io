"""Fixture-first PP&D agent readiness packet assembly.

The packet produced here is intentionally metadata-only. It joins already-normalized
PP&D process, case-gap, source-evidence, crawl-audit, DevHub surface, and action
signal fixtures without carrying private user values or raw page/document bodies.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping


class AgentReadinessPacketError(ValueError):
    """Raised when a readiness packet would violate PP&D agent guardrails."""

    def __init__(self, code: str, problems: Iterable[str]) -> None:
        self.code = code
        self.problems = tuple(problems)
        detail = "; ".join(self.problems)
        super().__init__(f"{code}: {detail}")


_PRIVATE_VALUE_KEYS = {
    "access_token",
    "answer",
    "auth_state",
    "bank_account",
    "card_number",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "cvv",
    "email",
    "entered_value",
    "field_value",
    "file_path",
    "local_path",
    "password",
    "payment_details",
    "phone",
    "private_value",
    "raw_value",
    "refresh_token",
    "secret",
    "session_cookie",
    "session_state",
    "ssn",
    "token",
    "user_input",
    "user_supplied_value",
    "value",
}

_RAW_CONTENT_KEYS = {
    "body",
    "document_text",
    "downloaded_document",
    "har",
    "html",
    "page_text",
    "raw_body",
    "raw_html",
    "raw_text",
    "screenshot",
    "text",
    "trace",
}

_EXPLANATION_KEYS = {"description", "explanation", "rationale", "reason", "summary"}
_CONSEQUENTIAL_CLASSES = {
    "certification",
    "consequential",
    "consequential_official",
    "financial",
    "official",
    "payment",
    "submission",
    "upload_to_official_record",
}

_SAFE_METADATA_KEYS = {
    "accessible_landmarks",
    "action_id",
    "action_ids",
    "actions",
    "allowed",
    "audit_id",
    "auth_scope",
    "blocked",
    "blocked_actions",
    "case_id",
    "checkpoint_id",
    "classification",
    "conflicting_evidence",
    "decision",
    "decision_id",
    "devhub_surface_refs",
    "evidence_id",
    "explanation",
    "fact_id",
    "field_id",
    "fields",
    "freshness_status",
    "guardrail_bundle_id",
    "known_fact_ids",
    "known_facts",
    "label",
    "manifest_ids",
    "manual_handoff_required",
    "matched_document_ids",
    "missing_document_ids",
    "missing_documents",
    "missing_fact_ids",
    "missing_facts",
    "no_raw_body_persisted",
    "page_heading",
    "permit_type",
    "presence",
    "process_id",
    "promotable",
    "promotion_status",
    "rationale",
    "readiness",
    "readiness_status",
    "reason",
    "redaction_policy",
    "requested_action_id",
    "required_confirmations",
    "required_document_ids",
    "required_for",
    "required_user_fact_ids",
    "requires_attendance",
    "requires_exact_confirmation",
    "requires_manual_handoff",
    "scope",
    "selector_confidence",
    "skipped_count",
    "skipped_reason_codes",
    "source_evidence_id",
    "source_evidence_ids",
    "stale_evidence",
    "state_transitions",
    "status",
    "summary",
    "surface_id",
    "upload_controls",
    "url_pattern",
    "validation_messages",
    "validation_status",
    "value_policy",
}


def assemble_agent_readiness_packet(
    readiness_fixture: Mapping[str, Any],
    *,
    generated_at: str | None = None,
    now: datetime | None = None,
    max_evidence_age_days: int = 45,
) -> dict[str, Any]:
    """Assemble a cited metadata-only readiness packet for PP&D agents.

    The input is expected to be a deterministic fixture or fixture-shaped mapping.
    Validation is intentionally performed before any output is assembled so stale
    or private material cannot be partially copied into an agent response.
    """

    fixture = deepcopy(dict(readiness_fixture))
    check_time = _normalize_now(now)
    evidence_by_id = _evidence_by_id(fixture.get("normalized_source_evidence"))

    problems: list[str] = []
    problems.extend(_private_value_problems(fixture))
    problems.extend(_evidence_freshness_problems(evidence_by_id, check_time, max_evidence_age_days))
    problems.extend(_citation_reference_problems(fixture, evidence_by_id))
    problems.extend(_uncited_explanation_problems(fixture, evidence_by_id))
    problems.extend(_raw_body_persistence_problems(fixture))
    problems.extend(_consequential_action_problems(fixture))

    if problems:
        raise AgentReadinessPacketError("invalid_agent_readiness_packet", problems)

    referenced_evidence_ids = sorted(_collect_evidence_refs(fixture))
    citations = [_citation_metadata(evidence_by_id[evidence_id]) for evidence_id in referenced_evidence_ids]

    process_bundle = _metadata_copy(fixture.get("process_bundle", {}))
    case_gap_report = _metadata_copy(fixture.get("case_gap_report", {}))
    crawl_promotion_audit = _metadata_copy(fixture.get("crawl_promotion_audit", {}))
    surface_readiness = _metadata_copy(fixture.get("devhub_surface_map_readiness", {}))
    action_decision = _metadata_copy(fixture.get("action_decision_output", {}))

    return {
        "packet_type": "ppd.agent_readiness_packet.v1",
        "generated_at": generated_at or fixture.get("generated_at") or check_time.isoformat().replace("+00:00", "Z"),
        "metadata_only": True,
        "case_id": case_gap_report.get("case_id"),
        "process_id": process_bundle.get("process_id"),
        "readiness_status": _readiness_status(case_gap_report, action_decision),
        "citation_ids": referenced_evidence_ids,
        "citations": citations,
        "process_bundle": process_bundle,
        "case_gap_report": case_gap_report,
        "normalized_source_evidence": citations,
        "crawl_promotion_audit": crawl_promotion_audit,
        "devhub_surface_map_readiness": surface_readiness,
        "action_decision_output": action_decision,
        "guardrail_enforcement": {
            "stale_evidence": "rejected",
            "uncited_explanations": "rejected",
            "private_values": "rejected",
            "consequential_actions": "manual_handoff_and_exact_confirmation_required",
        },
    }


def _normalize_now(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(timezone.utc)
    if now.tzinfo is None:
        return now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc)


def _evidence_by_id(raw_evidence: Any) -> dict[str, Mapping[str, Any]]:
    if not isinstance(raw_evidence, list):
        raise AgentReadinessPacketError("invalid_source_evidence", ["normalized_source_evidence must be a list"])

    evidence_by_id: dict[str, Mapping[str, Any]] = {}
    problems: list[str] = []
    for index, item in enumerate(raw_evidence):
        if not isinstance(item, Mapping):
            problems.append(f"normalized_source_evidence[{index}] must be an object")
            continue
        evidence_id = item.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id:
            problems.append(f"normalized_source_evidence[{index}] is missing evidence_id")
            continue
        if evidence_id in evidence_by_id:
            problems.append(f"duplicate source evidence id: {evidence_id}")
        evidence_by_id[evidence_id] = item

    if problems:
        raise AgentReadinessPacketError("invalid_source_evidence", problems)
    return evidence_by_id


def _private_value_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            normalized_key = key_text.lower()
            if normalized_key in _PRIVATE_VALUE_KEYS and child not in (None, "", [], {}):
                problems.append(f"private value field is not allowed at {child_path}")
            if normalized_key in _RAW_CONTENT_KEYS and child not in (None, "", [], {}):
                problems.append(f"raw content field is not allowed at {child_path}")
            problems.extend(_private_value_problems(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_private_value_problems(child, f"{path}[{index}]"))
    return problems


def _evidence_freshness_problems(
    evidence_by_id: Mapping[str, Mapping[str, Any]],
    now: datetime,
    max_evidence_age_days: int,
) -> list[str]:
    problems: list[str] = []
    for evidence_id, evidence in evidence_by_id.items():
        citation = evidence.get("citation") if isinstance(evidence.get("citation"), Mapping) else {}
        canonical_url = evidence.get("canonical_url") or citation.get("url")
        if not canonical_url:
            problems.append(f"source evidence {evidence_id} is missing canonical_url or citation.url")

        status = str(evidence.get("freshness_status", "current")).lower()
        if status in {"expired", "needs_refresh", "stale", "unknown_stale"}:
            problems.append(f"source evidence {evidence_id} has stale freshness_status {status}")

        timestamp_value = (
            evidence.get("last_verified_at")
            or evidence.get("captured_at")
            or evidence.get("capture_finished_at")
            or evidence.get("updated_at")
        )
        timestamp = _parse_datetime(timestamp_value)
        if timestamp is None:
            problems.append(f"source evidence {evidence_id} is missing a freshness timestamp")
            continue

        age_days = (now - timestamp).days
        if age_days > max_evidence_age_days:
            problems.append(f"source evidence {evidence_id} is stale at {age_days} days old")
    return problems


def _citation_reference_problems(
    fixture: Mapping[str, Any], evidence_by_id: Mapping[str, Mapping[str, Any]]
) -> list[str]:
    problems: list[str] = []
    referenced = _collect_evidence_refs(fixture)
    if not referenced:
        problems.append("packet fixture must reference at least one source_evidence_id")

    for evidence_id in sorted(referenced):
        if evidence_id not in evidence_by_id:
            problems.append(f"referenced source evidence id is not normalized: {evidence_id}")

    for component_name in (
        "process_bundle",
        "case_gap_report",
        "crawl_promotion_audit",
        "devhub_surface_map_readiness",
        "action_decision_output",
    ):
        component = fixture.get(component_name)
        if component is None:
            problems.append(f"missing readiness component: {component_name}")
        elif not _collect_evidence_refs(component):
            problems.append(f"readiness component has no source_evidence_ids: {component_name}")
    return problems


def _uncited_explanation_problems(
    value: Any,
    evidence_by_id: Mapping[str, Mapping[str, Any]],
    path: str = "$",
) -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        local_refs = _collect_direct_evidence_refs(value)
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.lower() in _EXPLANATION_KEYS and child not in (None, "", [], {}):
                child_refs = _collect_evidence_refs(child)
                refs = local_refs | child_refs
                if not refs:
                    problems.append(f"explanation field lacks source_evidence_ids at {child_path}")
                unknown_refs = sorted(ref for ref in refs if ref not in evidence_by_id)
                for ref in unknown_refs:
                    problems.append(f"explanation field references unknown source evidence {ref} at {child_path}")
            problems.extend(_uncited_explanation_problems(child, evidence_by_id, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_uncited_explanation_problems(child, evidence_by_id, f"{path}[{index}]"))
    return problems


def _raw_body_persistence_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        if value.get("raw_body_persisted") is True:
            problems.append(f"raw_body_persisted must be false in agent packets at {path}")
        if value.get("no_raw_body_persisted") is False:
            problems.append(f"no_raw_body_persisted must not be false in agent packets at {path}")
        for key, child in value.items():
            problems.extend(_raw_body_persistence_problems(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_raw_body_persistence_problems(child, f"{path}[{index}]"))
    return problems


def _consequential_action_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        action_class = _action_classification(value)
        if action_class in _CONSEQUENTIAL_CLASSES:
            has_handoff = any(
                value.get(key) is True
                for key in ("manual_handoff_required", "requires_manual_handoff", "requires_attendance")
            )
            has_exact_confirmation = value.get("requires_exact_confirmation") is True
            if not has_handoff:
                problems.append(f"consequential action lacks manual handoff or attendance requirement at {path}")
            if not has_exact_confirmation:
                problems.append(f"consequential action lacks exact-confirmation requirement at {path}")
        for key, child in value.items():
            problems.extend(_consequential_action_problems(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_consequential_action_problems(child, f"{path}[{index}]"))
    return problems


def _action_classification(value: Mapping[str, Any]) -> str | None:
    for key in ("classification", "action_class", "action_type", "decision"):
        raw = value.get(key)
        if isinstance(raw, str):
            normalized = raw.lower()
            if normalized in _CONSEQUENTIAL_CLASSES:
                return normalized
    return None


def _collect_evidence_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, Mapping):
        refs.update(_collect_direct_evidence_refs(value))
        for child in value.values():
            refs.update(_collect_evidence_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.update(_collect_evidence_refs(child))
    return refs


def _collect_direct_evidence_refs(value: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    raw_many = value.get("source_evidence_ids")
    if isinstance(raw_many, list):
        refs.update(item for item in raw_many if isinstance(item, str) and item)
    raw_one = value.get("source_evidence_id")
    if isinstance(raw_one, str) and raw_one:
        refs.add(raw_one)
    return refs


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if not isinstance(value, str) or not value:
        return None

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _citation_metadata(evidence: Mapping[str, Any]) -> dict[str, Any]:
    citation = evidence.get("citation") if isinstance(evidence.get("citation"), Mapping) else {}
    return {
        "evidence_id": evidence.get("evidence_id"),
        "source_id": evidence.get("source_id") or citation.get("source_id"),
        "source_type": evidence.get("source_type"),
        "title": evidence.get("title") or citation.get("title"),
        "canonical_url": evidence.get("canonical_url") or citation.get("url"),
        "captured_at": evidence.get("captured_at"),
        "last_verified_at": evidence.get("last_verified_at"),
        "freshness_status": evidence.get("freshness_status", "current"),
        "content_hash": evidence.get("content_hash"),
        "no_raw_body_persisted": evidence.get("no_raw_body_persisted", True),
    }


def _metadata_copy(value: Any) -> Any:
    if isinstance(value, Mapping):
        copied: dict[str, Any] = {}
        for key, child in value.items():
            key_text = str(key)
            if key_text in _SAFE_METADATA_KEYS:
                copied[key_text] = _metadata_copy(child)
        return copied
    if isinstance(value, list):
        return [_metadata_copy(child) for child in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _readiness_status(case_gap_report: Mapping[str, Any], action_decision: Mapping[str, Any]) -> str:
    if action_decision.get("decision") == "manual_handoff_required" or action_decision.get("blocked") is True:
        return "manual_handoff_required"
    if case_gap_report.get("blocked_actions"):
        return "manual_handoff_required"
    if case_gap_report.get("stale_evidence") or case_gap_report.get("conflicting_evidence"):
        return "needs_evidence_review"
    if case_gap_report.get("missing_facts") or case_gap_report.get("missing_documents"):
        return "needs_user_input"
    return "ready_for_safe_agent_use"
