"""Validation for fixture-first PP&D stale guardrail audit packets."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping


_STALE_ITEM_GROUPS: tuple[str, ...] = (
    "stale_predicates",
    "stale_explanations",
    "stale_refused_action_rules",
    "stale_exact_confirmation_gates",
)

_PRIVATE_KEY_MARKERS: tuple[str, ...] = (
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
    "payment",
    "card_number",
    "cvv",
    "routing_number",
    "account_number",
    "ssn",
    "private_file",
    "local_file",
    "download_path",
    "raw_body",
    "case_fact",
    "case_facts",
    "known_fact",
    "known_facts",
    "applicant_name",
    "owner_name",
    "phone",
    "email",
    "property_address",
    "permit_number",
)

_PRIVATE_VALUE_MARKERS: tuple[str, ...] = (
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

_MUTATION_KEY_MARKERS: tuple[str, ...] = (
    "active_guardrail_bundle_inputs",
    "active_bundle_inputs",
    "active_bundle_patch",
    "active_bundle_mutation",
    "active_bundle_mutations",
    "mutated_active_bundle",
    "mutated_active_guardrail_bundle",
    "proposed_active_bundle",
    "proposed_active_guardrail_bundle",
    "compiled_active_bundle",
    "compiled_guardrail_bundle",
)

_CONSEQUENTIAL_ACTION_TERMS: tuple[str, ...] = (
    "submit",
    "submission",
    "upload",
    "payment",
    "pay",
    "schedule",
    "scheduling",
    "cancel",
    "cancellation",
    "certify",
    "certification",
    "attest",
)

_ENABLEMENT_KEY_MARKERS: tuple[str, ...] = (
    "enabled_actions",
    "allowed_actions",
    "next_safe_actions",
    "agent_executable_actions",
    "action_enabled",
    "enabled",
)

_AGENT_ENABLEMENT_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(?:i|we|the agent|this agent)\s+(?:can|will|may|am able to|are able to|shall)\s+(?:[^.?!]{0,40}\s)?(?:pay|make payment|enter payment|upload|submit|file|schedule|cancel|certify|attest)\b",
        r"\b(?:payment|upload|submission|scheduling|cancellation|certification)\s+(?:is|are)\s+(?:enabled|allowed|available|performed|completed|executed)\s+by\s+(?:me|us|the agent)\b",
    )
)


@dataclass(frozen=True)
class StaleGuardrailAuditFinding:
    code: str
    path: str
    message: str


def validate_stale_guardrail_audit_packet(packet: Mapping[str, Any]) -> list[StaleGuardrailAuditFinding]:
    """Return validation findings for a stale guardrail audit packet."""

    if not isinstance(packet, Mapping):
        return [StaleGuardrailAuditFinding("invalid_packet", "$", "Packet must be an object.")]

    findings: list[StaleGuardrailAuditFinding] = []
    changed_source_ids = _validate_changed_sources(packet, findings)
    _validate_fixture_first_no_mutation(packet, findings)
    _validate_private_case_facts(packet, findings)
    _validate_stale_item_groups(packet, changed_source_ids, findings)
    _validate_required_human_review(packet, findings)
    _validate_consequential_action_enablement(packet, findings)
    return findings


def require_valid_stale_guardrail_audit_packet(packet: Mapping[str, Any]) -> None:
    findings = validate_stale_guardrail_audit_packet(packet)
    if findings:
        details = "; ".join(f"{finding.code} at {finding.path}: {finding.message}" for finding in findings)
        raise ValueError(f"invalid stale guardrail audit packet: {details}")


def finding_codes(findings: Iterable[StaleGuardrailAuditFinding]) -> set[str]:
    return {finding.code for finding in findings}


def _validate_fixture_first_no_mutation(packet: Mapping[str, Any], findings: list[StaleGuardrailAuditFinding]) -> None:
    if packet.get("audit_mode") != "fixture_first_no_recompile":
        findings.append(StaleGuardrailAuditFinding(
            "active_bundle_mutation",
            "$.audit_mode",
            "Stale guardrail audits must run in fixture-first no-recompile mode.",
        ))
    if packet.get("recompiled_active_guardrails") is not False:
        findings.append(StaleGuardrailAuditFinding(
            "active_bundle_mutation",
            "$.recompiled_active_guardrails",
            "Stale guardrail audits must not recompile or mutate active guardrails.",
        ))

    for path, value in _walk(packet):
        key = _path_key(path)
        if any(marker == key for marker in _MUTATION_KEY_MARKERS) and _has_value(value):
            findings.append(StaleGuardrailAuditFinding(
                "active_bundle_mutation",
                path,
                "Audit packets must not carry active-bundle mutations or replacement bundle inputs.",
            ))


def _validate_changed_sources(packet: Mapping[str, Any], findings: list[StaleGuardrailAuditFinding]) -> set[str]:
    changed_sources = packet.get("changed_sources")
    if not isinstance(changed_sources, list) or not changed_sources:
        findings.append(StaleGuardrailAuditFinding(
            "missing_changed_sources",
            "$.changed_sources",
            "Packet must list changed or stale sources that drive the audit.",
        ))
        return set()

    source_ids: set[str] = set()
    for index, source in enumerate(changed_sources):
        path = f"$.changed_sources[{index}]"
        if not isinstance(source, Mapping):
            findings.append(StaleGuardrailAuditFinding("invalid_changed_source", path, "Changed source entries must be objects."))
            continue
        source_id = source.get("source_id")
        canonical_url = source.get("canonical_url")
        if isinstance(source_id, str) and source_id.strip():
            source_ids.add(source_id.strip())
        else:
            findings.append(StaleGuardrailAuditFinding("invalid_changed_source", f"{path}.source_id", "Changed sources must include source_id."))
        if not isinstance(canonical_url, str) or not canonical_url.startswith("https://"):
            findings.append(StaleGuardrailAuditFinding("uncited_stale_claim", f"{path}.canonical_url", "Changed sources must cite their public canonical URL."))

        status = str(source.get("freshness_status", "")).strip().lower()
        if status == "current" and _has_unresolved_blocker(source):
            findings.append(StaleGuardrailAuditFinding(
                "unresolved_blocker_marked_current",
                path,
                "Sources with unresolved blockers must not be marked current.",
            ))
    return source_ids


def _validate_stale_item_groups(
    packet: Mapping[str, Any],
    changed_source_ids: set[str],
    findings: list[StaleGuardrailAuditFinding],
) -> None:
    for group_name in _STALE_ITEM_GROUPS:
        group = packet.get(group_name)
        if not isinstance(group, list):
            findings.append(StaleGuardrailAuditFinding("missing_stale_group", f"$.{group_name}", "Packet must include every stale guardrail item group."))
            continue
        for index, item in enumerate(group):
            path = f"$.{group_name}[{index}]"
            if not isinstance(item, Mapping):
                findings.append(StaleGuardrailAuditFinding("invalid_stale_item", path, "Stale guardrail entries must be objects."))
                continue
            _validate_stale_item(path, item, changed_source_ids, findings)


def _validate_stale_item(
    path: str,
    item: Mapping[str, Any],
    changed_source_ids: set[str],
    findings: list[StaleGuardrailAuditFinding],
) -> None:
    item_id = item.get("id")
    if not isinstance(item_id, str) or not item_id.strip():
        findings.append(StaleGuardrailAuditFinding("invalid_stale_item", f"{path}.id", "Stale items must include an id."))

    source_evidence_ids = _string_list(item.get("source_evidence_ids"))
    stale_source_ids = _string_list(item.get("stale_source_ids"))
    staleness_reasons = item.get("staleness_reasons")

    if not source_evidence_ids:
        findings.append(StaleGuardrailAuditFinding(
            "missing_source_dependency_link",
            f"{path}.source_evidence_ids",
            "Every stale guardrail item must retain its source-to-predicate dependency links.",
        ))

    if not stale_source_ids:
        findings.append(StaleGuardrailAuditFinding(
            "uncited_stale_claim",
            f"{path}.stale_source_ids",
            "Every stale claim must identify the changed source that made it stale.",
        ))

    for source_id in stale_source_ids:
        if source_id not in source_evidence_ids or source_id not in changed_source_ids:
            findings.append(StaleGuardrailAuditFinding(
                "missing_source_dependency_link",
                f"{path}.stale_source_ids",
                "Stale source IDs must be present in source_evidence_ids and changed_sources.",
            ))

    if not isinstance(staleness_reasons, list) or not staleness_reasons:
        findings.append(StaleGuardrailAuditFinding(
            "uncited_stale_claim",
            f"{path}.staleness_reasons",
            "Stale items must include cited staleness reasons.",
        ))
        return

    cited_reason_source_ids: set[str] = set()
    for reason_index, reason in enumerate(staleness_reasons):
        reason_path = f"{path}.staleness_reasons[{reason_index}]"
        if not isinstance(reason, Mapping):
            findings.append(StaleGuardrailAuditFinding("uncited_stale_claim", reason_path, "Staleness reasons must be objects."))
            continue
        reason_source_id = reason.get("source_id")
        if isinstance(reason_source_id, str) and reason_source_id.strip():
            cited_reason_source_ids.add(reason_source_id.strip())
            if not isinstance(reason.get("canonical_url"), str) or not reason.get("canonical_url", "").startswith("https://"):
                findings.append(StaleGuardrailAuditFinding(
                    "uncited_stale_claim",
                    f"{reason_path}.canonical_url",
                    "Source-backed staleness reasons must include a public canonical URL citation.",
                ))
        if str(reason.get("freshness_status", "")).strip().lower() == "current" and _has_unresolved_blocker(reason):
            findings.append(StaleGuardrailAuditFinding(
                "unresolved_blocker_marked_current",
                reason_path,
                "Unresolved blockers cannot be represented as current stale-reason evidence.",
            ))

    missing_citations = set(stale_source_ids) - cited_reason_source_ids
    if missing_citations:
        findings.append(StaleGuardrailAuditFinding(
            "uncited_stale_claim",
            f"{path}.staleness_reasons",
            "Every stale_source_id must have a matching cited staleness reason.",
        ))


def _validate_required_human_review(packet: Mapping[str, Any], findings: list[StaleGuardrailAuditFinding]) -> None:
    review_items = packet.get("required_human_review")
    if not isinstance(review_items, list):
        findings.append(StaleGuardrailAuditFinding("missing_human_review", "$.required_human_review", "Packet must list required human review entries."))
        return
    for index, review in enumerate(review_items):
        path = f"$.required_human_review[{index}]"
        if not isinstance(review, Mapping):
            findings.append(StaleGuardrailAuditFinding("missing_human_review", path, "Human review entries must be objects."))
            continue
        stale_item_ids = _string_list(review.get("stale_item_ids"))
        reason = review.get("review_reason")
        if not stale_item_ids or not isinstance(reason, str) or not reason.strip():
            findings.append(StaleGuardrailAuditFinding(
                "uncited_stale_claim",
                path,
                "Human review entries must cite stale item IDs and the review reason.",
            ))


def _validate_private_case_facts(packet: Mapping[str, Any], findings: list[StaleGuardrailAuditFinding]) -> None:
    for path, value in _walk(packet):
        key = _path_key(path)
        if any(marker in key for marker in _PRIVATE_KEY_MARKERS) and _has_value(value) and not _is_allowed_policy_path(path):
            findings.append(StaleGuardrailAuditFinding(
                "private_case_fact",
                path,
                "Stale guardrail audit packets must not include private case facts or auth/session/payment artifacts.",
            ))
        if isinstance(value, str) and any(marker in value for marker in _PRIVATE_VALUE_MARKERS):
            findings.append(StaleGuardrailAuditFinding(
                "private_case_fact",
                path,
                "Stale guardrail audit packets must not include private values or local artifact paths.",
            ))


def _validate_consequential_action_enablement(packet: Mapping[str, Any], findings: list[StaleGuardrailAuditFinding]) -> None:
    for path, value in _walk(packet):
        key = _path_key(path)
        if any(marker in key for marker in _ENABLEMENT_KEY_MARKERS) and _mentions_consequential_action(value):
            findings.append(StaleGuardrailAuditFinding(
                "consequential_action_enablement",
                path,
                "Audit packets must not enable payment, upload, submission, scheduling, cancellation, or certification actions.",
            ))
        if isinstance(value, str) and any(pattern.search(value) for pattern in _AGENT_ENABLEMENT_PATTERNS):
            findings.append(StaleGuardrailAuditFinding(
                "consequential_action_enablement",
                path,
                "Audit text must not imply consequential official actions are agent-executable.",
            ))


def _has_unresolved_blocker(value: Mapping[str, Any]) -> bool:
    for key in ("unresolved_blockers", "open_blockers", "blockers", "required_human_review", "review_blockers"):
        if _has_value(value.get(key)):
            return True
    text = " ".join(str(value.get(key, "")) for key in ("change_reason", "rationale", "review_reason", "status_reason"))
    lowered = text.lower()
    return "unresolved" in lowered and "block" in lowered


def _mentions_consequential_action(value: Any) -> bool:
    if isinstance(value, str):
        lowered = value.lower()
        return any(term in lowered for term in _CONSEQUENTIAL_ACTION_TERMS)
    if isinstance(value, bool):
        return value is True
    if isinstance(value, list):
        return any(_mentions_consequential_action(item) for item in value)
    if isinstance(value, Mapping):
        return any(_mentions_consequential_action(item) for item in value.values())
    return False


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, nested in value.items():
            yield from _walk(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _walk(nested, f"{path}[{index}]")


def _path_key(path: str) -> str:
    return path.rsplit(".", 1)[-1].split("[", 1)[0].lower()


def _has_value(value: Any) -> bool:
    return value not in (None, False, "", [], {})


def _is_allowed_policy_path(path: str) -> bool:
    key = _path_key(path)
    return key in {"recompiled_active_guardrails"} or path.startswith("$.required_human_review")


__all__ = [
    "StaleGuardrailAuditFinding",
    "finding_codes",
    "require_valid_stale_guardrail_audit_packet",
    "validate_stale_guardrail_audit_packet",
]
