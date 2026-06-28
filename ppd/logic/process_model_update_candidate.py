"""Build fixture-first process-model update candidate packets.

This module is intentionally side-effect free. It converts reviewed requirement
rerun dispositions and an impact rehearsal packet into proposed process-model
changes for human review. It does not compile, promote, or mutate active process
models.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping

DIFF_TYPES = (
    "stage",
    "required_fact",
    "document_rule",
    "deadline",
    "exception",
    "unsupported_path",
)

_ACCEPTED_STATUSES = {"accepted", "approved", "candidate"}
_UNSUPPORTED_STATUSES = {"unsupported", "unsupported_path"}
_ACTIVE_MUTATION_KEYS = {
    "active_process_model_mutation",
    "active_process_model_mutated",
    "active_process_mutation",
    "process_model_mutation_enabled",
    "process_model_update_enabled",
    "mutation_enabled",
    "mutates_active_process_model",
    "mutate_active_process_model",
}
_LIVE_EXECUTION_KEYS = {
    "live_crawl_executed",
    "live_crawler_executed",
    "crawler_executed",
    "compiler_executed",
    "process_model_compiler_executed",
    "compiled_process_model",
    "compiled_process_models",
}
_PRIVATE_FACT_KEYS = {
    "private_case_fact",
    "private_case_facts",
    "case_fact",
    "case_facts",
    "known_fact",
    "known_facts",
    "applicant_name",
    "owner_name",
    "phone_number",
    "email_address",
    "permit_number",
    "tax_account_number",
    "project_address",
}
_ACK_KEYS = {
    "stale_current_acknowledged",
    "stale_current_evidence_acknowledged",
    "reviewer_acknowledged_stale_current",
    "reviewer_acknowledged_stale_evidence",
    "stale_evidence_acknowledgement",
}
_LOCAL_PATH_PREFIXES = ("/home/", "/Users/", "/private/", "/tmp/", "file://", "C:\\", "D:\\")
_LIVE_EXECUTION_PHRASES = (
    "ran live crawler",
    "live crawler ran",
    "live crawl completed",
    "executed crawler",
    "compiler executed",
    "compiled the process model",
    "compiled active process model",
)
_OUTCOME_GUARANTEE_PHRASES = (
    "guarantee approval",
    "guaranteed approval",
    "permit will be approved",
    "application will be approved",
    "approval is guaranteed",
    "guarantees issuance",
    "permit issuance guaranteed",
    "will receive the permit",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in _as_list(value) if str(item)]


def _collect_citations(disposition: Mapping[str, Any], rehearsal: Mapping[str, Any]) -> list[dict[str, str]]:
    citations: list[dict[str, str]] = []
    for citation in _as_list(disposition.get("citations")):
        if isinstance(citation, Mapping):
            source_id = str(citation.get("source_id") or citation.get("source_evidence_id") or "")
            quote = str(citation.get("quote") or citation.get("summary") or "")
            if source_id:
                citations.append({"source_id": source_id, "quote": quote})
        elif citation:
            citations.append({"source_id": str(citation), "quote": ""})
    for evidence_id in _string_list(disposition.get("source_evidence_ids")):
        citations.append({"source_id": evidence_id, "quote": ""})

    evidence_by_id = {
        str(item.get("source_id") or item.get("source_evidence_id")): item
        for item in _as_list(rehearsal.get("source_evidence"))
        if isinstance(item, Mapping)
    }
    enriched: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for citation in citations:
        source_id = citation["source_id"]
        evidence = evidence_by_id.get(source_id, {})
        quote = citation.get("quote") or str(evidence.get("quote") or evidence.get("summary") or "")
        key = (source_id, quote)
        if key not in seen:
            enriched.append({"source_id": source_id, "quote": quote})
            seen.add(key)
    return enriched


def _reviewer_owner(disposition: Mapping[str, Any], rehearsal: Mapping[str, Any]) -> str:
    owner = disposition.get("reviewer_owner") or disposition.get("owner")
    if owner:
        return str(owner)
    owners = _string_list(rehearsal.get("reviewer_owners"))
    return owners[0] if owners else "ppd-process-model-reviewer"


def _rollback_note(disposition: Mapping[str, Any]) -> str:
    note = disposition.get("rollback_note") or disposition.get("rollback")
    if note:
        return str(note)
    target = disposition.get("target_id") or disposition.get("requirement_id") or "proposed change"
    return f"Drop candidate diff for {target}; no active process model state is changed by this packet."


def _diff_type(disposition: Mapping[str, Any]) -> str:
    proposed_change = disposition.get("proposed_change")
    if isinstance(proposed_change, Mapping):
        value = proposed_change.get("diff_type") or proposed_change.get("type")
        if value:
            return str(value)
    value = disposition.get("diff_type") or disposition.get("type")
    if value:
        return str(value)
    if str(disposition.get("status") or "").lower() in _UNSUPPORTED_STATUSES:
        return "unsupported_path"
    raise ValueError(f"Disposition {disposition.get('disposition_id', '')} is missing diff_type")


def _operation(disposition: Mapping[str, Any]) -> str:
    proposed_change = disposition.get("proposed_change")
    if isinstance(proposed_change, Mapping) and proposed_change.get("operation"):
        return str(proposed_change["operation"])
    return str(disposition.get("operation") or "add")


def _target_id(disposition: Mapping[str, Any]) -> str:
    proposed_change = disposition.get("proposed_change")
    if isinstance(proposed_change, Mapping) and proposed_change.get("target_id"):
        return str(proposed_change["target_id"])
    return str(disposition.get("target_id") or disposition.get("requirement_id") or disposition.get("disposition_id"))


def _proposed_payload(disposition: Mapping[str, Any]) -> Any:
    proposed_change = disposition.get("proposed_change")
    if isinstance(proposed_change, Mapping) and "proposed" in proposed_change:
        return deepcopy(proposed_change["proposed"])
    if "proposed" in disposition:
        return deepcopy(disposition["proposed"])
    return {}


def _current_payload(disposition: Mapping[str, Any]) -> Any:
    proposed_change = disposition.get("proposed_change")
    if isinstance(proposed_change, Mapping) and "current" in proposed_change:
        return deepcopy(proposed_change["current"])
    if "current" in disposition:
        return deepcopy(disposition["current"])
    return None


def build_process_model_update_candidate(
    requirement_rerun_review: Mapping[str, Any],
    impact_rehearsal: Mapping[str, Any],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Return a proposed-only process-model update candidate packet."""
    diffs = {diff_type: [] for diff_type in DIFF_TYPES}
    dispositions = _as_list(requirement_rerun_review.get("dispositions"))
    for disposition in dispositions:
        if not isinstance(disposition, Mapping):
            raise TypeError("Each disposition must be a mapping")
        status = str(disposition.get("status") or "").lower()
        if status not in _ACCEPTED_STATUSES and status not in _UNSUPPORTED_STATUSES:
            continue
        diff_type = _diff_type(disposition)
        if diff_type not in diffs:
            raise ValueError(f"Unsupported diff_type: {diff_type}")
        if status in _UNSUPPORTED_STATUSES:
            diff_type = "unsupported_path"
        diff = {
            "candidate_diff_id": str(disposition.get("disposition_id") or disposition.get("requirement_id") or _target_id(disposition)),
            "requirement_id": str(disposition.get("requirement_id") or ""),
            "operation": _operation(disposition),
            "target_id": _target_id(disposition),
            "current": _current_payload(disposition),
            "proposed": _proposed_payload(disposition),
            "citations": _collect_citations(disposition, impact_rehearsal),
            "reviewer_owner": _reviewer_owner(disposition, impact_rehearsal),
            "rollback_note": _rollback_note(disposition),
            "review_disposition": status,
            "impact_rehearsal_refs": _string_list(disposition.get("impact_rehearsal_refs") or impact_rehearsal.get("rehearsal_id")),
        }
        diffs[diff_type].append(diff)

    for diff_list in diffs.values():
        diff_list.sort(key=lambda item: (item["target_id"], item["candidate_diff_id"]))

    packet = {
        "packet_type": "process_model_update_candidate",
        "packet_id": str(requirement_rerun_review.get("packet_id") or "process-model-update-candidate"),
        "generated_at": generated_at or str(requirement_rerun_review.get("generated_at") or _utc_now()),
        "process_model_id": str(impact_rehearsal.get("process_model_id") or requirement_rerun_review.get("process_model_id") or ""),
        "known_process_model_ids": _string_list(impact_rehearsal.get("known_process_model_ids") or requirement_rerun_review.get("known_process_model_ids")),
        "known_requirement_ids": _string_list(impact_rehearsal.get("known_requirement_ids") or requirement_rerun_review.get("known_requirement_ids")),
        "requirement_rerun_review_packet_id": str(requirement_rerun_review.get("packet_id") or ""),
        "impact_rehearsal_packet_id": str(impact_rehearsal.get("rehearsal_id") or impact_rehearsal.get("packet_id") or ""),
        "proposed_diffs": diffs,
        "reviewer_owners": sorted(set(_string_list(requirement_rerun_review.get("reviewer_owners")) + _string_list(impact_rehearsal.get("reviewer_owners")))),
        "rollback_notes": [diff["rollback_note"] for diff_list in diffs.values() for diff in diff_list],
        "attestations": {
            "fixture_first": True,
            "compiled_process_models": False,
            "promoted_process_models": False,
            "mutated_active_process_models": False,
            "no_active_process_mutation": bool(impact_rehearsal.get("no_active_process_mutation_attestation", True)),
        },
    }
    validate_process_model_update_candidate(packet)
    return packet


def validate_process_model_update_candidate(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a candidate packet is not review-ready."""
    errors: list[str] = []
    attestations = packet.get("attestations")
    if not isinstance(attestations, Mapping):
        errors.append("Candidate packet is missing attestations")
    else:
        for key in ("fixture_first", "no_active_process_mutation"):
            if attestations.get(key) is not True:
                errors.append(f"Attestation must be true: {key}")
        for key in ("compiled_process_models", "promoted_process_models", "mutated_active_process_models"):
            if attestations.get(key) is not False:
                errors.append(f"Attestation must be false: {key}")

    _validate_known_ids(packet, errors)
    _validate_reviewer_and_rollback(packet, errors)
    _validate_process_diffs(packet, errors)
    _validate_recursive_safety(packet, errors)
    if errors:
        raise ValueError("; ".join(errors))


def _validate_known_ids(packet: Mapping[str, Any], errors: list[str]) -> None:
    process_model_id = str(packet.get("process_model_id") or "")
    known_process_ids = set(_string_list(packet.get("known_process_model_ids") or packet.get("known_process_ids")))
    if known_process_ids and process_model_id not in known_process_ids:
        errors.append(f"unknown process_model_id: {process_model_id}")
    known_requirement_ids = set(_string_list(packet.get("known_requirement_ids") or packet.get("known_requirement_refs")))
    if known_requirement_ids:
        for path, diff in _iter_diffs(packet, errors):
            requirement_id = str(diff.get("requirement_id") or "")
            if requirement_id and requirement_id not in known_requirement_ids:
                errors.append(f"unknown requirement_id at {path}: {requirement_id}")


def _validate_reviewer_and_rollback(packet: Mapping[str, Any], errors: list[str]) -> None:
    if not _string_list(packet.get("reviewer_owners")):
        errors.append("Candidate packet is missing reviewer_owners")
    if not _string_list(packet.get("rollback_notes")):
        errors.append("Candidate packet is missing rollback_notes")


def _validate_process_diffs(packet: Mapping[str, Any], errors: list[str]) -> None:
    proposed_diffs = packet.get("proposed_diffs")
    if not isinstance(proposed_diffs, Mapping):
        errors.append("Candidate packet is missing proposed_diffs")
        return
    for diff_type in DIFF_TYPES:
        if diff_type not in proposed_diffs:
            errors.append(f"Candidate packet is missing proposed_diffs.{diff_type}")
    for _path, diff in _iter_diffs(packet, errors):
        if not _has_citation(diff.get("citations") or diff.get("source_evidence_ids")):
            errors.append(f"Diff {diff.get('candidate_diff_id')} is missing citations")
        if not str(diff.get("reviewer_owner") or "").strip():
            errors.append(f"Diff {diff.get('candidate_diff_id')} is missing reviewer_owner")
        if not str(diff.get("rollback_note") or diff.get("rollback") or "").strip():
            errors.append(f"Diff {diff.get('candidate_diff_id')} is missing rollback_note")
        if not str(diff.get("requirement_id") or "").strip():
            errors.append(f"Diff {diff.get('candidate_diff_id')} is missing requirement_id")
        if _contains_stale_current_evidence(diff) and not _has_stale_acknowledgement(diff):
            errors.append(f"Diff {diff.get('candidate_diff_id')} has stale current evidence without acknowledgement")


def _iter_diffs(packet: Mapping[str, Any], errors: list[str]) -> list[tuple[str, Mapping[str, Any]]]:
    proposed_diffs = packet.get("proposed_diffs")
    if not isinstance(proposed_diffs, Mapping):
        return []
    found: list[tuple[str, Mapping[str, Any]]] = []
    for diff_type, raw_diffs in proposed_diffs.items():
        for index, diff in enumerate(_as_list(raw_diffs)):
            path = f"$.proposed_diffs.{diff_type}[{index}]"
            if isinstance(diff, Mapping):
                found.append((path, diff))
            else:
                errors.append(f"Diff entries for {diff_type} must be mappings")
    return found


def _has_citation(value: Any) -> bool:
    for citation in _as_list(value):
        if isinstance(citation, Mapping):
            if str(citation.get("source_id") or citation.get("source_evidence_id") or citation.get("citation_id") or "").strip():
                return True
        elif str(citation or "").strip():
            return True
    return False


def _contains_stale_current_evidence(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).lower()
            if "current" in key_text and _contains_stale_marker(child):
                return True
            if key_text in {"freshness_status", "evidence_status", "current_evidence_status"} and "stale" in str(child).lower():
                return True
            if _contains_stale_current_evidence(child):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_stale_current_evidence(item) for item in value)
    return False


def _contains_stale_marker(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).lower()
            if key_text in {"freshness_status", "evidence_status", "status"} and "stale" in str(child).lower():
                return True
            if _contains_stale_marker(child):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_stale_marker(item) for item in value)
    else:
        return "stale_current" in str(value).lower()
    return False


def _has_stale_acknowledgement(diff: Mapping[str, Any]) -> bool:
    for key in _ACK_KEYS:
        if diff.get(key) is True:
            return True
        value = diff.get(key)
        if isinstance(value, str) and value.strip():
            return True
    reviewer_review = diff.get("reviewer_review")
    if isinstance(reviewer_review, Mapping):
        return any(reviewer_review.get(key) is True for key in _ACK_KEYS)
    return False


def _validate_recursive_safety(packet: Mapping[str, Any], errors: list[str]) -> None:
    for path, key, value in _walk(packet):
        key_text = key.lower()
        if key_text in _ACTIVE_MUTATION_KEYS and value is not False:
            errors.append(f"active process-model mutation flag at {path} must be false")
        if key_text in _LIVE_EXECUTION_KEYS and value not in (False, None, "", "not_run", "fixture_only"):
            errors.append(f"live crawler/compiler execution claim is not allowed at {path}")
        if key_text in _PRIVATE_FACT_KEYS and _non_empty_private_value(value):
            errors.append(f"private case facts are not allowed at {path}")
        if key_text in {"privacy", "privacy_classification", "case_fact_privacy"} and str(value).lower() in {"private", "confidential", "restricted"}:
            errors.append(f"private case facts are not allowed at {path}")
        if isinstance(value, str):
            lowered = value.lower()
            if _looks_like_local_private_path(value):
                errors.append(f"local private path is not allowed at {path}")
            if any(phrase in lowered for phrase in _LIVE_EXECUTION_PHRASES):
                errors.append(f"live crawler/compiler execution claim is not allowed at {path}")
            if any(phrase in lowered for phrase in _OUTCOME_GUARANTEE_PHRASES):
                errors.append(f"legal or permitting outcome guarantee is not allowed at {path}")


def _walk(value: Any, path: str = "$", key: str = "") -> list[tuple[str, str, Any]]:
    rows = [(path, key, value)]
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            child_key_text = str(child_key)
            rows.extend(_walk(child, f"{path}.{child_key_text}", child_key_text))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            rows.extend(_walk(child, f"{path}[{index}]", key))
    return rows


def _non_empty_private_value(value: Any) -> bool:
    if value in (None, False, "", [], {}):
        return False
    if isinstance(value, (list, tuple)):
        return any(_non_empty_private_value(item) for item in value)
    if isinstance(value, Mapping):
        return any(_non_empty_private_value(item) for item in value.values())
    return True


def _looks_like_local_private_path(value: str) -> bool:
    stripped = value.strip()
    if stripped.startswith(_LOCAL_PATH_PREFIXES):
        return True
    if "\\" in stripped and len(stripped) > 2 and stripped[1:3] == ":\\":
        return True
    return False
