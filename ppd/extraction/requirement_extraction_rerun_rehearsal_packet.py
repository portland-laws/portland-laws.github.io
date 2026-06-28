"""Fixture-first requirement extraction rerun rehearsal packets.

This module consumes already-reviewed public recrawl packets, requirement
human-review queue packets, and synthetic public document records. It produces
reviewer-facing rerun rehearsal output only. It never extracts from source text,
fetches URLs, invokes processors, or mutates active requirements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlparse

PACKET_TYPE = "requirement_extraction_rerun_rehearsal_packet"
SCHEMA_VERSION = 1
MODE = "fixture_first_no_extraction_execution"

_ALLOWED_PUBLIC_HOSTS = {
    "www.portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
}
_PRIVATE_URL_MARKERS = (
    "/account",
    "/admin",
    "/callback",
    "/dashboard",
    "/login",
    "/logout",
    "/my-permits",
    "/oauth",
    "/payment",
    "/profile",
    "/signin",
    "/sign-in",
    "/upload",
)
_FORBIDDEN_KEYS = {
    "active_requirement_mutation",
    "active_requirement_mutation_flag",
    "archive_artifact_ref",
    "archive_path",
    "browser_session_id",
    "download_path",
    "downloaded_document_ref",
    "extracted_source_text",
    "live_extraction",
    "live_extraction_claim",
    "local_document_path",
    "normalized_text",
    "ocr_text",
    "page_text",
    "playwright_trace",
    "raw_archive_ref",
    "raw_body",
    "raw_html",
    "raw_source_text",
    "source_text",
    "storage_state",
    "target_active_requirement_id",
    "warc_path",
}
_FALSE_ATTESTATION_KEYS = (
    "live_network_used",
    "crawler_invoked",
    "processor_invoked",
    "extraction_executed",
    "requirements_mutated",
    "formal_requirements_written",
    "documents_downloaded",
    "raw_bodies_persisted",
)


@dataclass(frozen=True)
class RequirementExtractionRerunRehearsalValidationResult:
    valid: bool
    errors: tuple[str, ...]


class RequirementExtractionRerunRehearsalPacketError(ValueError):
    pass


def build_requirement_extraction_rerun_rehearsal_packet(
    public_recrawl_post_intake_review_packet: Mapping[str, Any],
    requirement_human_review_queue_packet: Mapping[str, Any],
    synthetic_public_document_records: Sequence[Mapping[str, Any]],
    *,
    generated_at: str,
) -> dict[str, Any]:
    """Build a deterministic rerun rehearsal packet from fixture inputs."""

    input_errors: list[str] = []
    _reject_forbidden_content(public_recrawl_post_intake_review_packet, "public_recrawl_post_intake_review_packet", input_errors)
    _reject_forbidden_content(requirement_human_review_queue_packet, "requirement_human_review_queue_packet", input_errors)
    _reject_forbidden_content(synthetic_public_document_records, "synthetic_public_document_records", input_errors)
    if input_errors:
        raise RequirementExtractionRerunRehearsalPacketError("invalid rehearsal inputs: " + "; ".join(input_errors))

    documents_by_source = _documents_by_source(synthetic_public_document_records)
    stale_source_ids = _stale_source_ids(public_recrawl_post_intake_review_packet)
    candidate_deltas: list[dict[str, Any]] = []
    withdrawal_notes: list[dict[str, Any]] = []
    owner_rows: list[dict[str, Any]] = []
    deferred_notes: list[dict[str, Any]] = []

    candidates = _candidate_rows(requirement_human_review_queue_packet)
    for index, candidate in enumerate(candidates, start=1):
        candidate_id = _text(candidate.get("candidate_id"), f"candidate-{index:02d}")
        source_ids = _candidate_source_ids(candidate)
        citations = _candidate_citations(candidate)
        owner = _text(candidate.get("reviewer_owner"), _text(candidate.get("review_owner"), "requirement-review-owner"))
        matched_document_ids = sorted(
            document.get("document_id", "")
            for source_id in source_ids
            for document in documents_by_source.get(source_id, ())
            if document.get("document_id")
        )
        candidate_deltas.append(
            {
                "delta_id": "rerun-delta-" + _stable_token(candidate_id),
                "candidate_id": candidate_id,
                "delta_type": "candidate_requirement_rehearsal",
                "source_ids": source_ids,
                "citations": citations,
                "matched_document_ids": matched_document_ids,
                "proposed_disposition": "human_review_required",
                "reviewer_owner": owner,
                "requirements_mutated": False,
                "formal_requirement_written": False,
            }
        )
        owner_rows.append(
            {
                "owner_id": "owner-" + _stable_token(candidate_id),
                "candidate_id": candidate_id,
                "reviewer_owner": owner,
                "handoff_reason": "candidate_delta_requires_human_review",
            }
        )
        if any(source_id in stale_source_ids for source_id in source_ids):
            withdrawal_notes.append(
                {
                    "withdrawal_id": "withdraw-stale-" + _stable_token(candidate_id),
                    "candidate_id": candidate_id,
                    "source_ids": source_ids,
                    "reason": "stale_or_changed_public_source_blocks_candidate_reuse",
                    "withdrawal_scope": "candidate_rehearsal_only",
                    "requirements_mutated": False,
                }
            )
        deferred_notes.append(
            {
                "deferred_id": "defer-formalization-" + _stable_token(candidate_id),
                "candidate_id": candidate_id,
                "reviewer_owner": owner,
                "reason": "fixture_rerun_rehearsal_does_not_formalize_requirements",
                "formalization_status": "deferred_pending_human_review",
                "formal_requirement_written": False,
            }
        )

    packet = {
        "schema_version": SCHEMA_VERSION,
        "packet_type": PACKET_TYPE,
        "mode": MODE,
        "generated_at": generated_at,
        "fixture_first": True,
        "input_packet_refs": {
            "public_recrawl_post_intake_review_packet_type": _text(public_recrawl_post_intake_review_packet.get("packet_type")),
            "requirement_review_queue_packet_type": _text(requirement_human_review_queue_packet.get("packet_type")),
            "synthetic_public_document_record_count": len(synthetic_public_document_records),
        },
        "cited_candidate_requirement_deltas": candidate_deltas,
        "stale_candidate_withdrawal_notes": withdrawal_notes,
        "human_review_owners": owner_rows,
        "deferred_formalization_notes": deferred_notes,
        "no_extraction_execution_attestations": {
            "live_network_used": False,
            "crawler_invoked": False,
            "processor_invoked": False,
            "extraction_executed": False,
            "requirements_mutated": False,
            "formal_requirements_written": False,
            "documents_downloaded": False,
            "raw_bodies_persisted": False,
            "attestation_basis": "fixture_inputs_only",
        },
        "rehearsal_summary": {
            "candidate_delta_count": len(candidate_deltas),
            "stale_withdrawal_note_count": len(withdrawal_notes),
            "human_review_owner_count": len(owner_rows),
            "deferred_formalization_note_count": len(deferred_notes),
            "extraction_executed": False,
            "requirements_mutated": False,
        },
    }
    require_valid_requirement_extraction_rerun_rehearsal_packet(packet)
    return packet


def validate_requirement_extraction_rerun_rehearsal_packet(
    packet: Mapping[str, Any],
) -> RequirementExtractionRerunRehearsalValidationResult:
    errors: list[str] = []
    _reject_forbidden_content(packet, "packet", errors)

    if packet.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 1")
    if packet.get("packet_type") != PACKET_TYPE:
        errors.append("packet_type must be requirement_extraction_rerun_rehearsal_packet")
    if packet.get("mode") != MODE:
        errors.append("mode must be fixture_first_no_extraction_execution")
    if packet.get("fixture_first") is not True:
        errors.append("fixture_first must be true")
    if not _text(packet.get("generated_at")).endswith("Z"):
        errors.append("generated_at must be an ISO UTC timestamp ending in Z")

    deltas = _require_list(packet.get("cited_candidate_requirement_deltas"), "cited_candidate_requirement_deltas", errors)
    withdrawals = _require_list(packet.get("stale_candidate_withdrawal_notes"), "stale_candidate_withdrawal_notes", errors)
    owners = _require_list(packet.get("human_review_owners"), "human_review_owners", errors)
    deferred = _require_list(packet.get("deferred_formalization_notes"), "deferred_formalization_notes", errors)
    attestations = packet.get("no_extraction_execution_attestations")

    if not deltas:
        errors.append("cited_candidate_requirement_deltas must include at least one delta")
    _validate_deltas(deltas, errors)
    _validate_withdrawals(withdrawals, errors)
    _validate_owners(owners, errors)
    _validate_deferred(deferred, errors)

    if not isinstance(attestations, Mapping):
        errors.append("no_extraction_execution_attestations must be an object")
    else:
        for key in _FALSE_ATTESTATION_KEYS:
            if attestations.get(key) is not False:
                errors.append(f"no_extraction_execution_attestations.{key} must be false")
        if _text(attestations.get("attestation_basis")) != "fixture_inputs_only":
            errors.append("no_extraction_execution_attestations.attestation_basis must be fixture_inputs_only")

    summary = packet.get("rehearsal_summary")
    if not isinstance(summary, Mapping):
        errors.append("rehearsal_summary must be an object")
    else:
        expected_counts = {
            "candidate_delta_count": len(deltas),
            "stale_withdrawal_note_count": len(withdrawals),
            "human_review_owner_count": len(owners),
            "deferred_formalization_note_count": len(deferred),
        }
        for key, expected in expected_counts.items():
            if summary.get(key) != expected:
                errors.append(f"rehearsal_summary.{key} must be {expected}")
        for key in ("extraction_executed", "requirements_mutated"):
            if summary.get(key) is not False:
                errors.append(f"rehearsal_summary.{key} must be false")

    return RequirementExtractionRerunRehearsalValidationResult(valid=not errors, errors=tuple(errors))


def require_valid_requirement_extraction_rerun_rehearsal_packet(packet: Mapping[str, Any]) -> None:
    result = validate_requirement_extraction_rerun_rehearsal_packet(packet)
    if not result.valid:
        raise RequirementExtractionRerunRehearsalPacketError("; ".join(result.errors))


def _validate_deltas(deltas: Sequence[Any], errors: list[str]) -> None:
    seen: set[str] = set()
    for index, delta in enumerate(deltas):
        path = f"cited_candidate_requirement_deltas[{index}]"
        if not isinstance(delta, Mapping):
            errors.append(path + " must be an object")
            continue
        delta_id = _text(delta.get("delta_id"))
        if not delta_id:
            errors.append(path + ".delta_id is required")
        if delta_id in seen:
            errors.append(path + ".delta_id must be unique")
        seen.add(delta_id)
        for key in ("candidate_id", "delta_type", "proposed_disposition", "reviewer_owner"):
            if not _text(delta.get(key)):
                errors.append(f"{path}.{key} is required")
        if not _string_list(delta.get("source_ids")):
            errors.append(path + ".source_ids must cite at least one source")
        if not _string_list(delta.get("citations")):
            errors.append(path + ".citations must cite at least one evidence id")
        for key in ("requirements_mutated", "formal_requirement_written"):
            if delta.get(key) is not False:
                errors.append(f"{path}.{key} must be false")


def _validate_withdrawals(withdrawals: Sequence[Any], errors: list[str]) -> None:
    for index, note in enumerate(withdrawals):
        path = f"stale_candidate_withdrawal_notes[{index}]"
        if not isinstance(note, Mapping):
            errors.append(path + " must be an object")
            continue
        for key in ("withdrawal_id", "candidate_id", "reason", "withdrawal_scope"):
            if not _text(note.get(key)):
                errors.append(f"{path}.{key} is required")
        if not _string_list(note.get("source_ids")):
            errors.append(path + ".source_ids must identify stale sources")
        if note.get("requirements_mutated") is not False:
            errors.append(path + ".requirements_mutated must be false")


def _validate_owners(owners: Sequence[Any], errors: list[str]) -> None:
    candidate_ids: set[str] = set()
    for index, owner in enumerate(owners):
        path = f"human_review_owners[{index}]"
        if not isinstance(owner, Mapping):
            errors.append(path + " must be an object")
            continue
        for key in ("owner_id", "candidate_id", "reviewer_owner", "handoff_reason"):
            if not _text(owner.get(key)):
                errors.append(f"{path}.{key} is required")
        candidate_id = _text(owner.get("candidate_id"))
        if candidate_id in candidate_ids:
            errors.append(path + ".candidate_id must appear only once")
        candidate_ids.add(candidate_id)


def _validate_deferred(deferred: Sequence[Any], errors: list[str]) -> None:
    for index, note in enumerate(deferred):
        path = f"deferred_formalization_notes[{index}]"
        if not isinstance(note, Mapping):
            errors.append(path + " must be an object")
            continue
        for key in ("deferred_id", "candidate_id", "reviewer_owner", "reason", "formalization_status"):
            if not _text(note.get(key)):
                errors.append(f"{path}.{key} is required")
        if note.get("formalization_status") != "deferred_pending_human_review":
            errors.append(path + ".formalization_status must be deferred_pending_human_review")
        if note.get("formal_requirement_written") is not False:
            errors.append(path + ".formal_requirement_written must be false")


def _documents_by_source(records: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    indexed: dict[str, list[Mapping[str, Any]]] = {}
    for record in records:
        if not isinstance(record, Mapping):
            continue
        source_id = _text(record.get("source_id"))
        canonical_url = _text(record.get("canonical_url"))
        if canonical_url:
            _require_public_url(canonical_url)
        if source_id:
            indexed.setdefault(source_id, []).append(record)
    return indexed


def _stale_source_ids(packet: Mapping[str, Any]) -> set[str]:
    stale: set[str] = set()
    for decision in _as_list(packet.get("source_level_triage_decisions")):
        if not isinstance(decision, Mapping):
            continue
        if decision.get("review_required") is True or _text(decision.get("decision")) in {"changed", "missing", "conflict"}:
            source_id = _text(decision.get("source_id"))
            if source_id:
                stale.add(source_id)
    for blocker in _as_list(packet.get("promotion_blockers")):
        if isinstance(blocker, Mapping):
            source_id = _text(blocker.get("source_id"))
            if source_id:
                stale.add(source_id)
    return stale


def _candidate_rows(packet: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    candidates = packet.get("requirement_candidates", packet.get("candidates", ()))
    return [candidate for candidate in _as_list(candidates) if isinstance(candidate, Mapping)]


def _candidate_source_ids(candidate: Mapping[str, Any]) -> list[str]:
    source_ids = _string_list(candidate.get("source_ids"))
    if source_ids:
        return sorted(source_ids)
    citation_sources: list[str] = []
    for citation in _as_list(candidate.get("citations")):
        if isinstance(citation, Mapping):
            source_id = _text(citation.get("source_id"))
            if source_id:
                citation_sources.append(source_id)
    return sorted(set(citation_sources))


def _candidate_citations(candidate: Mapping[str, Any]) -> list[str]:
    direct = _string_list(candidate.get("source_evidence_ids"))
    if direct:
        return direct
    citations: list[str] = []
    for citation in _as_list(candidate.get("citations")):
        if isinstance(citation, str):
            citations.append(citation)
        elif isinstance(citation, Mapping):
            evidence_id = _text(citation.get("source_evidence_id"), _text(citation.get("evidence_id")))
            if evidence_id:
                citations.append(evidence_id)
    return sorted(set(citations))


def _require_list(value: Any, path: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(path + " must be a list")
        return []
    return value


def _reject_forbidden_content(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = path + "." + key_text
            if key_text in _FORBIDDEN_KEYS:
                errors.append(child_path + " is not allowed in fixture rerun rehearsal packets")
            if isinstance(child, str):
                _validate_string_value(child, child_path, errors)
            _reject_forbidden_content(child, child_path, errors)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _reject_forbidden_content(child, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        _validate_string_value(value, path, errors)


def _validate_string_value(value: str, path: str, errors: list[str]) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in ("password", "cookie", "bearer ", "storage_state", "trace.zip", "file://")):
        errors.append(path + " contains a private or local artifact marker")
    if value.startswith(("http://", "https://")):
        parsed = urlparse(value)
        host = parsed.netloc.lower()
        if host and host not in _ALLOWED_PUBLIC_HOSTS:
            errors.append(path + " must reference an allowed public PP&D host")
        if any(marker in parsed.path.lower() for marker in _PRIVATE_URL_MARKERS):
            errors.append(path + " must not reference private or authenticated URL paths")


def _require_public_url(value: str) -> None:
    errors: list[str] = []
    _validate_string_value(value, "canonical_url", errors)
    if errors:
        raise RequirementExtractionRerunRehearsalPacketError("; ".join(errors))


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, Sequence):
        return sorted({str(item) for item in value if isinstance(item, str) and item})
    return []


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    return []


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _stable_token(value: str) -> str:
    token = "".join(character.lower() if character.isalnum() else "-" for character in value.strip())
    while "--" in token:
        token = token.replace("--", "-")
    return token.strip("-") or "item"
