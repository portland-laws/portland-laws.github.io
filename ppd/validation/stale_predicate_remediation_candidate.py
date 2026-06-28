"""Validation for stale-predicate remediation candidate packets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


DRAFT_FIX_GROUPS: tuple[str, ...] = (
    "draft_predicate_fixes",
    "draft_explanation_template_fixes",
    "draft_refused_action_rule_fixes",
    "draft_exact_confirmation_gate_fixes",
)

_ACTIVE_MUTATION_KEYS: tuple[str, ...] = (
    "active_guardrail_bundle",
    "active_guardrail_bundle_inputs",
    "active_bundle_patch",
    "active_bundle_mutation",
    "replacement_guardrail_bundle",
    "compiled_guardrail_bundle",
    "promoted_guardrail_bundle",
)

_RESOLVED_REVIEW_STATUSES: set[str] = {"resolved", "approved", "accepted", "complete", "completed"}


@dataclass(frozen=True)
class StalePredicateRemediationFinding:
    code: str
    path: str
    message: str


def validate_stale_predicate_remediation_candidate(packet: Mapping[str, Any]) -> list[StalePredicateRemediationFinding]:
    """Return validation findings for a draft remediation candidate packet."""

    if not isinstance(packet, Mapping):
        return [StalePredicateRemediationFinding("invalid_packet", "$", "Packet must be an object.")]

    findings: list[StalePredicateRemediationFinding] = []
    _validate_fixture_first_immutability(packet, findings)
    _validate_draft_fix_groups(packet, findings)
    _validate_unresolved_review_notes(packet, findings)
    return findings


def require_valid_stale_predicate_remediation_candidate(packet: Mapping[str, Any]) -> None:
    findings = validate_stale_predicate_remediation_candidate(packet)
    if findings:
        details = "; ".join(f"{finding.code} at {finding.path}: {finding.message}" for finding in findings)
        raise ValueError(f"invalid stale predicate remediation candidate: {details}")


def finding_codes(findings: Iterable[StalePredicateRemediationFinding]) -> set[str]:
    return {finding.code for finding in findings}


def _validate_fixture_first_immutability(
    packet: Mapping[str, Any],
    findings: list[StalePredicateRemediationFinding],
) -> None:
    if packet.get("candidate_mode") != "fixture_first_review_only":
        findings.append(StalePredicateRemediationFinding(
            "not_fixture_first",
            "$.candidate_mode",
            "Remediation candidates must be fixture-first and review-only.",
        ))
    if packet.get("does_not_replace_active_bundle") is not True:
        findings.append(StalePredicateRemediationFinding(
            "active_bundle_replacement",
            "$.does_not_replace_active_bundle",
            "Candidate packets must explicitly preserve active bundle immutability.",
        ))
    if packet.get("active_bundle_mutated") is not False:
        findings.append(StalePredicateRemediationFinding(
            "active_bundle_mutation",
            "$.active_bundle_mutated",
            "Candidate packets must not mutate active guardrail bundles.",
        ))
    for path, value in _walk(packet):
        key = _path_key(path)
        if key in _ACTIVE_MUTATION_KEYS and _has_value(value):
            findings.append(StalePredicateRemediationFinding(
                "active_bundle_mutation",
                path,
                "Candidate packets must not carry replacement active-bundle content.",
            ))


def _validate_draft_fix_groups(
    packet: Mapping[str, Any],
    findings: list[StalePredicateRemediationFinding],
) -> None:
    packet_evidence_ids = set(_string_list(packet.get("source_evidence_ids")))
    for group_name in DRAFT_FIX_GROUPS:
        group = packet.get(group_name)
        if not isinstance(group, list):
            findings.append(StalePredicateRemediationFinding(
                "missing_draft_fix_group",
                f"$.{group_name}",
                "Candidate packets must include every draft fix group.",
            ))
            continue
        for index, item in enumerate(group):
            path = f"$.{group_name}[{index}]"
            if not isinstance(item, Mapping):
                findings.append(StalePredicateRemediationFinding("invalid_draft_fix", path, "Draft fixes must be objects."))
                continue
            _validate_draft_fix(path, item, packet_evidence_ids, findings)


def _validate_draft_fix(
    path: str,
    item: Mapping[str, Any],
    packet_evidence_ids: set[str],
    findings: list[StalePredicateRemediationFinding],
) -> None:
    for key in ("fix_id", "target_group", "target_item_id"):
        if not isinstance(item.get(key), str) or not item.get(key, "").strip():
            findings.append(StalePredicateRemediationFinding("invalid_draft_fix", f"{path}.{key}", f"Draft fixes must include {key}."))
    if item.get("review_status") != "draft_requires_human_review":
        findings.append(StalePredicateRemediationFinding(
            "draft_fix_without_human_review",
            f"{path}.review_status",
            "Draft fixes must remain blocked on human review.",
        ))
    if item.get("preserves_active_item") is not True:
        findings.append(StalePredicateRemediationFinding(
            "active_bundle_replacement",
            f"{path}.preserves_active_item",
            "Draft fixes must preserve the active item until separately reviewed and promoted.",
        ))

    source_evidence_ids = set(_string_list(item.get("source_evidence_ids")))
    if not source_evidence_ids:
        findings.append(StalePredicateRemediationFinding(
            "missing_normalized_citation_evidence",
            f"{path}.source_evidence_ids",
            "Every draft fix must cite normalized public citation evidence.",
        ))
    elif packet_evidence_ids and not source_evidence_ids.issubset(packet_evidence_ids):
        findings.append(StalePredicateRemediationFinding(
            "uncited_draft_fix",
            f"{path}.source_evidence_ids",
            "Draft fix evidence IDs must be listed in packet source_evidence_ids.",
        ))

    evidence_rows = item.get("normalized_citation_evidence")
    if not isinstance(evidence_rows, list) or not evidence_rows:
        findings.append(StalePredicateRemediationFinding(
            "missing_normalized_citation_evidence",
            f"{path}.normalized_citation_evidence",
            "Draft fixes must carry normalized citation evidence summaries.",
        ))
    else:
        cited = set()
        for index, row in enumerate(evidence_rows):
            row_path = f"{path}.normalized_citation_evidence[{index}]"
            if not isinstance(row, Mapping):
                findings.append(StalePredicateRemediationFinding("missing_normalized_citation_evidence", row_path, "Citation evidence summaries must be objects."))
                continue
            evidence_id = row.get("evidence_id")
            if isinstance(evidence_id, str) and evidence_id.strip():
                cited.add(evidence_id.strip())
            for key in ("source_id", "canonical_url", "citation_span_id", "normalized_claim"):
                if not isinstance(row.get(key), str) or not row.get(key, "").strip():
                    findings.append(StalePredicateRemediationFinding("missing_normalized_citation_evidence", f"{row_path}.{key}", f"Citation evidence must include {key}."))
            canonical_url = row.get("canonical_url")
            if isinstance(canonical_url, str) and not canonical_url.startswith("https://"):
                findings.append(StalePredicateRemediationFinding("uncited_draft_fix", f"{row_path}.canonical_url", "Citation evidence must use a public HTTPS source URL."))
        if source_evidence_ids and cited != source_evidence_ids:
            findings.append(StalePredicateRemediationFinding(
                "uncited_draft_fix",
                f"{path}.normalized_citation_evidence",
                "Draft fix citation summaries must match source_evidence_ids exactly.",
            ))

    draft_fix = item.get("draft_fix")
    if not isinstance(draft_fix, Mapping) or not draft_fix:
        findings.append(StalePredicateRemediationFinding("invalid_draft_fix", f"{path}.draft_fix", "Draft fixes must include a non-empty draft_fix object."))
    elif draft_fix.get("replaces_active_item") is not False:
        findings.append(StalePredicateRemediationFinding(
            "active_bundle_replacement",
            f"{path}.draft_fix.replaces_active_item",
            "Draft fixes must not claim to replace active guardrail items.",
        ))


def _validate_unresolved_review_notes(
    packet: Mapping[str, Any],
    findings: list[StalePredicateRemediationFinding],
) -> None:
    notes = packet.get("unresolved_human_review_notes")
    if not isinstance(notes, list) or not notes:
        findings.append(StalePredicateRemediationFinding(
            "missing_unresolved_human_review_notes",
            "$.unresolved_human_review_notes",
            "Candidate packets must preserve unresolved human-review notes.",
        ))
        return
    for index, note in enumerate(notes):
        path = f"$.unresolved_human_review_notes[{index}]"
        if not isinstance(note, Mapping):
            findings.append(StalePredicateRemediationFinding("invalid_human_review_note", path, "Human-review notes must be objects."))
            continue
        status = str(note.get("status", "")).strip().lower()
        if status != "unresolved" or status in _RESOLVED_REVIEW_STATUSES:
            findings.append(StalePredicateRemediationFinding(
                "resolved_human_review_note",
                f"{path}.status",
                "Remediation candidates must not resolve human-review notes.",
            ))
        for key in ("note_id", "message"):
            if not isinstance(note.get(key), str) or not note.get(key, "").strip():
                findings.append(StalePredicateRemediationFinding("invalid_human_review_note", f"{path}.{key}", f"Human-review notes must include {key}."))


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


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


__all__ = [
    "StalePredicateRemediationFinding",
    "finding_codes",
    "require_valid_stale_predicate_remediation_candidate",
    "validate_stale_predicate_remediation_candidate",
]
