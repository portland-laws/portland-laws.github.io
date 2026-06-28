"""Fixture-first requirement rerun review disposition packets.

This module consumes an already-built requirement extraction rerun rehearsal
packet and a committed validation fixture. It produces reviewer disposition
metadata only. It does not run extraction, fetch sources, formalize requirement
nodes, or mutate active requirements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

from ppd.extraction.requirement_extraction_rerun_rehearsal_packet import (
    require_valid_requirement_extraction_rerun_rehearsal_packet,
)

PACKET_TYPE = "requirement_rerun_review_disposition_packet"
SCHEMA_VERSION = 1
MODE = "fixture_first_review_disposition_no_requirement_mutation"
VALIDATION_FIXTURE_TYPE = "requirement_rerun_review_disposition_validation_fixture"

_DISPOSITIONS = ("accepted", "deferred", "superseded", "withdrawn")
_GROUP_KEYS = {
    "accepted": "accepted_candidate_deltas",
    "deferred": "deferred_candidate_deltas",
    "superseded": "superseded_candidate_deltas",
    "withdrawn": "withdrawn_candidate_deltas",
}
_FALSE_ATTESTATION_KEYS = (
    "live_network_used",
    "crawler_invoked",
    "processor_invoked",
    "extraction_executed",
    "requirements_mutated",
    "active_requirements_changed",
    "formal_requirements_written",
    "documents_downloaded",
    "raw_bodies_persisted",
)
_FORBIDDEN_KEYS = {
    "active_requirement_id",
    "active_requirement_mutation",
    "active_requirement_mutation_flag",
    "archive_artifact_ref",
    "archive_path",
    "browser_session_id",
    "download_path",
    "downloaded_document_ref",
    "extracted_source_text",
    "live_extraction",
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
    "/submit",
    "/upload",
)


@dataclass(frozen=True)
class RequirementRerunReviewDispositionValidationResult:
    valid: bool
    errors: tuple[str, ...]


class RequirementRerunReviewDispositionPacketError(ValueError):
    pass


def build_requirement_rerun_review_disposition_packet(
    requirement_extraction_rerun_rehearsal_packet: Mapping[str, Any],
    validation_fixture: Mapping[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    """Build a deterministic reviewer disposition packet from fixtures."""

    require_valid_requirement_extraction_rerun_rehearsal_packet(requirement_extraction_rerun_rehearsal_packet)

    input_errors: list[str] = []
    _reject_forbidden_content(requirement_extraction_rerun_rehearsal_packet, "requirement_extraction_rerun_rehearsal_packet", input_errors)
    _reject_forbidden_content(validation_fixture, "validation_fixture", input_errors)
    if input_errors:
        raise RequirementRerunReviewDispositionPacketError("invalid disposition inputs: " + "; ".join(input_errors))

    deltas = _candidate_deltas(requirement_extraction_rerun_rehearsal_packet)
    delta_by_candidate_id = {_text(delta.get("candidate_id")): delta for delta in deltas}
    reviews = _reviews_by_candidate_id(validation_fixture)
    missing = sorted(set(delta_by_candidate_id) - set(reviews))
    extra = sorted(set(reviews) - set(delta_by_candidate_id))
    if missing or extra:
        detail = []
        if missing:
            detail.append("missing disposition reviews for " + ", ".join(missing))
        if extra:
            detail.append("unknown disposition reviews for " + ", ".join(extra))
        raise RequirementRerunReviewDispositionPacketError("; ".join(detail))

    groups: dict[str, list[dict[str, Any]]] = {disposition: [] for disposition in _DISPOSITIONS}
    owner_assignments: list[dict[str, Any]] = []
    stale_acknowledgements: list[dict[str, Any]] = []
    formalization_deferrals: list[dict[str, Any]] = []
    stale_candidate_ids = _stale_candidate_ids(requirement_extraction_rerun_rehearsal_packet)

    for delta in deltas:
        candidate_id = _text(delta.get("candidate_id"))
        review = reviews[candidate_id]
        disposition = _text(review.get("disposition")).lower()
        reviewer_owner = _text(review.get("reviewer_owner"), _text(delta.get("reviewer_owner")))
        citations = _string_list(review.get("citations")) or _string_list(delta.get("citations"))
        source_ids = _string_list(delta.get("source_ids"))
        rationale = _text(review.get("decision_rationale"), "fixture reviewer disposition recorded without requirement mutation")
        row = {
            "disposition_id": "disp-" + _stable_token(disposition + "-" + candidate_id),
            "candidate_id": candidate_id,
            "source_delta_id": _text(delta.get("delta_id")),
            "disposition": disposition,
            "source_ids": source_ids,
            "citations": citations,
            "reviewer_owner": reviewer_owner,
            "decision_rationale": rationale,
            "requirements_mutated": False,
            "active_requirement_written": False,
        }
        groups[disposition].append(row)
        owner_assignments.append(
            {
                "assignment_id": "owner-" + _stable_token(candidate_id),
                "candidate_id": candidate_id,
                "reviewer_owner": reviewer_owner,
                "disposition": disposition,
                "assignment_basis": "validation_fixture_reviewer_owner",
            }
        )
        if candidate_id in stale_candidate_ids or disposition in {"superseded", "withdrawn"}:
            stale_acknowledgements.append(
                {
                    "acknowledgement_id": "stale-ack-" + _stable_token(candidate_id),
                    "candidate_id": candidate_id,
                    "disposition": disposition,
                    "source_ids": source_ids,
                    "citations": citations,
                    "acknowledgement_status": "acknowledged_no_reuse_without_fresh_review",
                    "requirements_mutated": False,
                }
            )
        formalization_deferrals.append(
            {
                "deferral_id": "formalization-deferral-" + _stable_token(candidate_id),
                "candidate_id": candidate_id,
                "disposition": disposition,
                "reviewer_owner": reviewer_owner,
                "formalization_status": "deferred_pending_separate_formalization_packet",
                "deferral_reason": "review disposition packet records candidate deltas only",
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
            "requirement_extraction_rerun_rehearsal_packet_type": _text(requirement_extraction_rerun_rehearsal_packet.get("packet_type")),
            "requirement_extraction_rerun_rehearsal_packet_id": _text(requirement_extraction_rerun_rehearsal_packet.get("packet_id")),
            "validation_fixture_type": _text(validation_fixture.get("packet_type")),
            "validation_fixture_id": _text(validation_fixture.get("fixture_id")),
        },
        "accepted_candidate_deltas": groups["accepted"],
        "deferred_candidate_deltas": groups["deferred"],
        "superseded_candidate_deltas": groups["superseded"],
        "withdrawn_candidate_deltas": groups["withdrawn"],
        "reviewer_owner_assignments": owner_assignments,
        "stale_evidence_acknowledgements": stale_acknowledgements,
        "formalization_deferrals": formalization_deferrals,
        "no_requirement_mutation_attestations": {
            "live_network_used": False,
            "crawler_invoked": False,
            "processor_invoked": False,
            "extraction_executed": False,
            "requirements_mutated": False,
            "active_requirements_changed": False,
            "formal_requirements_written": False,
            "documents_downloaded": False,
            "raw_bodies_persisted": False,
            "attestation_basis": "fixture_rehearsal_packet_and_validation_fixture_only",
        },
        "disposition_summary": {
            "accepted_count": len(groups["accepted"]),
            "deferred_count": len(groups["deferred"]),
            "superseded_count": len(groups["superseded"]),
            "withdrawn_count": len(groups["withdrawn"]),
            "reviewer_owner_assignment_count": len(owner_assignments),
            "stale_evidence_acknowledgement_count": len(stale_acknowledgements),
            "formalization_deferral_count": len(formalization_deferrals),
            "extraction_executed": False,
            "requirements_mutated": False,
            "active_requirements_changed": False,
        },
    }
    require_valid_requirement_rerun_review_disposition_packet(packet)
    return packet


def validate_requirement_rerun_review_disposition_packet(
    packet: Mapping[str, Any],
) -> RequirementRerunReviewDispositionValidationResult:
    errors: list[str] = []
    _reject_forbidden_content(packet, "packet", errors)

    if packet.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 1")
    if packet.get("packet_type") != PACKET_TYPE:
        errors.append("packet_type must be requirement_rerun_review_disposition_packet")
    if packet.get("mode") != MODE:
        errors.append("mode must be fixture_first_review_disposition_no_requirement_mutation")
    if packet.get("fixture_first") is not True:
        errors.append("fixture_first must be true")
    if not _text(packet.get("generated_at")).endswith("Z"):
        errors.append("generated_at must be an ISO UTC timestamp ending in Z")

    groups: dict[str, list[Any]] = {}
    for disposition, key in _GROUP_KEYS.items():
        values = _require_list(packet.get(key), key, errors)
        groups[disposition] = values
        if not values:
            errors.append(key + " must include at least one " + disposition + " candidate delta")
        _validate_disposition_rows(values, disposition, key, errors)

    owners = _require_list(packet.get("reviewer_owner_assignments"), "reviewer_owner_assignments", errors)
    stale = _require_list(packet.get("stale_evidence_acknowledgements"), "stale_evidence_acknowledgements", errors)
    deferrals = _require_list(packet.get("formalization_deferrals"), "formalization_deferrals", errors)
    _validate_owner_assignments(owners, errors)
    _validate_stale_acknowledgements(stale, errors)
    _validate_formalization_deferrals(deferrals, errors)
    _validate_attestations(packet.get("no_requirement_mutation_attestations"), errors)
    _validate_summary(packet.get("disposition_summary"), groups, owners, stale, deferrals, errors)

    return RequirementRerunReviewDispositionValidationResult(valid=not errors, errors=tuple(errors))


def require_valid_requirement_rerun_review_disposition_packet(packet: Mapping[str, Any]) -> None:
    result = validate_requirement_rerun_review_disposition_packet(packet)
    if not result.valid:
        raise RequirementRerunReviewDispositionPacketError("; ".join(result.errors))


def _validate_disposition_rows(rows: Sequence[Any], disposition: str, key: str, errors: list[str]) -> None:
    seen: set[str] = set()
    for index, row in enumerate(rows):
        path = f"{key}[{index}]"
        if not isinstance(row, Mapping):
            errors.append(path + " must be an object")
            continue
        disposition_id = _text(row.get("disposition_id"))
        if not disposition_id:
            errors.append(path + ".disposition_id is required")
        if disposition_id in seen:
            errors.append(path + ".disposition_id must be unique within its disposition group")
        seen.add(disposition_id)
        if row.get("disposition") != disposition:
            errors.append(path + ".disposition must be " + disposition)
        for field in ("candidate_id", "source_delta_id", "reviewer_owner", "decision_rationale"):
            if not _text(row.get(field)):
                errors.append(f"{path}.{field} is required")
        if not _string_list(row.get("source_ids")):
            errors.append(path + ".source_ids must cite at least one source")
        if not _string_list(row.get("citations")):
            errors.append(path + ".citations must cite at least one evidence id")
        for flag in ("requirements_mutated", "active_requirement_written"):
            if row.get(flag) is not False:
                errors.append(f"{path}.{flag} must be false")


def _validate_owner_assignments(rows: Sequence[Any], errors: list[str]) -> None:
    candidate_ids: set[str] = set()
    for index, row in enumerate(rows):
        path = f"reviewer_owner_assignments[{index}]"
        if not isinstance(row, Mapping):
            errors.append(path + " must be an object")
            continue
        for field in ("assignment_id", "candidate_id", "reviewer_owner", "disposition", "assignment_basis"):
            if not _text(row.get(field)):
                errors.append(f"{path}.{field} is required")
        if row.get("disposition") not in _DISPOSITIONS:
            errors.append(path + ".disposition is not supported")
        candidate_id = _text(row.get("candidate_id"))
        if candidate_id in candidate_ids:
            errors.append(path + ".candidate_id must appear only once")
        candidate_ids.add(candidate_id)


def _validate_stale_acknowledgements(rows: Sequence[Any], errors: list[str]) -> None:
    if not rows:
        errors.append("stale_evidence_acknowledgements must include at least one acknowledgement")
    for index, row in enumerate(rows):
        path = f"stale_evidence_acknowledgements[{index}]"
        if not isinstance(row, Mapping):
            errors.append(path + " must be an object")
            continue
        for field in ("acknowledgement_id", "candidate_id", "disposition", "acknowledgement_status"):
            if not _text(row.get(field)):
                errors.append(f"{path}.{field} is required")
        if row.get("disposition") not in _DISPOSITIONS:
            errors.append(path + ".disposition is not supported")
        if not _string_list(row.get("source_ids")):
            errors.append(path + ".source_ids must cite stale or superseded sources")
        if not _string_list(row.get("citations")):
            errors.append(path + ".citations must cite stale or superseded evidence")
        if row.get("acknowledgement_status") != "acknowledged_no_reuse_without_fresh_review":
            errors.append(path + ".acknowledgement_status must be acknowledged_no_reuse_without_fresh_review")
        if row.get("requirements_mutated") is not False:
            errors.append(path + ".requirements_mutated must be false")


def _validate_formalization_deferrals(rows: Sequence[Any], errors: list[str]) -> None:
    if not rows:
        errors.append("formalization_deferrals must include at least one deferral")
    for index, row in enumerate(rows):
        path = f"formalization_deferrals[{index}]"
        if not isinstance(row, Mapping):
            errors.append(path + " must be an object")
            continue
        for field in ("deferral_id", "candidate_id", "disposition", "reviewer_owner", "formalization_status", "deferral_reason"):
            if not _text(row.get(field)):
                errors.append(f"{path}.{field} is required")
        if row.get("formalization_status") != "deferred_pending_separate_formalization_packet":
            errors.append(path + ".formalization_status must be deferred_pending_separate_formalization_packet")
        if row.get("formal_requirement_written") is not False:
            errors.append(path + ".formal_requirement_written must be false")


def _validate_attestations(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("no_requirement_mutation_attestations must be an object")
        return
    for key in _FALSE_ATTESTATION_KEYS:
        if value.get(key) is not False:
            errors.append(f"no_requirement_mutation_attestations.{key} must be false")
    if value.get("attestation_basis") != "fixture_rehearsal_packet_and_validation_fixture_only":
        errors.append("no_requirement_mutation_attestations.attestation_basis must be fixture_rehearsal_packet_and_validation_fixture_only")


def _validate_summary(
    value: Any,
    groups: Mapping[str, Sequence[Any]],
    owners: Sequence[Any],
    stale: Sequence[Any],
    deferrals: Sequence[Any],
    errors: list[str],
) -> None:
    if not isinstance(value, Mapping):
        errors.append("disposition_summary must be an object")
        return
    expected_counts = {
        "accepted_count": len(groups.get("accepted", ())),
        "deferred_count": len(groups.get("deferred", ())),
        "superseded_count": len(groups.get("superseded", ())),
        "withdrawn_count": len(groups.get("withdrawn", ())),
        "reviewer_owner_assignment_count": len(owners),
        "stale_evidence_acknowledgement_count": len(stale),
        "formalization_deferral_count": len(deferrals),
    }
    for key, expected in expected_counts.items():
        if value.get(key) != expected:
            errors.append(f"disposition_summary.{key} must be {expected}")
    for key in ("extraction_executed", "requirements_mutated", "active_requirements_changed"):
        if value.get(key) is not False:
            errors.append(f"disposition_summary.{key} must be false")


def _reviews_by_candidate_id(validation_fixture: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    if validation_fixture.get("packet_type") != VALIDATION_FIXTURE_TYPE:
        raise RequirementRerunReviewDispositionPacketError("validation_fixture.packet_type is not supported")
    if validation_fixture.get("validation_result") not in {"valid", "accepted_for_disposition"}:
        raise RequirementRerunReviewDispositionPacketError("validation_fixture.validation_result must be valid or accepted_for_disposition")
    if validation_fixture.get("extraction_executed") is not False:
        raise RequirementRerunReviewDispositionPacketError("validation_fixture.extraction_executed must be false")
    if validation_fixture.get("requirements_mutated") is not False:
        raise RequirementRerunReviewDispositionPacketError("validation_fixture.requirements_mutated must be false")

    reviews: dict[str, Mapping[str, Any]] = {}
    for index, review in enumerate(_as_list(validation_fixture.get("disposition_reviews"))):
        if not isinstance(review, Mapping):
            raise RequirementRerunReviewDispositionPacketError(f"disposition_reviews[{index}] must be an object")
        candidate_id = _text(review.get("candidate_id"))
        disposition = _text(review.get("disposition")).lower()
        if not candidate_id:
            raise RequirementRerunReviewDispositionPacketError(f"disposition_reviews[{index}].candidate_id is required")
        if candidate_id in reviews:
            raise RequirementRerunReviewDispositionPacketError("duplicate disposition review for " + candidate_id)
        if disposition not in _DISPOSITIONS:
            raise RequirementRerunReviewDispositionPacketError(f"disposition_reviews[{index}].disposition is not supported")
        if not _text(review.get("reviewer_owner")):
            raise RequirementRerunReviewDispositionPacketError(f"disposition_reviews[{index}].reviewer_owner is required")
        if not _string_list(review.get("citations")):
            raise RequirementRerunReviewDispositionPacketError(f"disposition_reviews[{index}].citations must cite evidence")
        reviews[candidate_id] = review
    return reviews


def _candidate_deltas(packet: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [delta for delta in _as_list(packet.get("cited_candidate_requirement_deltas")) if isinstance(delta, Mapping)]


def _stale_candidate_ids(packet: Mapping[str, Any]) -> set[str]:
    ids: set[str] = set()
    for note in _as_list(packet.get("stale_candidate_withdrawal_notes")):
        if isinstance(note, Mapping):
            candidate_id = _text(note.get("candidate_id"))
            if candidate_id:
                ids.add(candidate_id)
    return ids


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
                errors.append(child_path + " is not allowed in fixture disposition packets")
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


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
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
