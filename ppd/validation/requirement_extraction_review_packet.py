"""Validate PP&D requirement extraction review packets before promotion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

DEFAULT_LOW_CONFIDENCE_THRESHOLD = 0.75

SUPPORTED_REQUIREMENT_TYPES = frozenset(
    {
        "action_gate",
        "deadline",
        "document_requirement",
        "exception",
        "fee_trigger",
        "license_requirement",
        "obligation",
        "permission",
        "precondition",
        "prohibition",
    }
)

HUMAN_REVIEW_STATUSES = frozenset(
    {
        "approved",
        "fixture_reviewed",
        "human_reviewed",
        "needs_human_review",
        "reviewed",
    }
)

REVIEWED_STATUSES = frozenset(
    {
        "approved",
        "fixture_reviewed",
        "human_reviewed",
        "reviewed",
    }
)

LOW_CONFIDENCE_REVIEW_STATUSES = frozenset(
    {
        "needs_human_review",
        "pending_human_review",
        "review_queue",
        "blocked_pending_review",
    }
)

PRODUCTION_READY_STATUSES = frozenset(
    {
        "production",
        "production_ready",
        "ready_for_production",
        "promoted",
    }
)

RAW_DOCUMENT_BODY_KEYS = frozenset(
    {
        "body",
        "body_html",
        "body_text",
        "document_body",
        "full_html",
        "full_text",
        "html",
        "html_body",
        "page_body",
        "pdf_body",
        "pdf_html",
        "pdf_text",
        "raw_body",
        "raw_document_body",
        "raw_html",
        "raw_html_body",
        "raw_pdf",
        "raw_pdf_body",
        "raw_text",
    }
)

PRIVATE_VALUE_KEYS = frozenset(
    {
        "account_number",
        "auth_state",
        "card_number",
        "cookie",
        "cookies",
        "cvv",
        "file_contents",
        "known_value",
        "password",
        "payment_details",
        "private_value",
        "raw_value",
        "routing_number",
        "session_state",
        "ssn",
        "storage_state",
        "token",
    }
)

PRIVATE_STRING_MARKERS = (
    "/data/private/",
    "/devhub/.auth/",
    "/devhub/downloads/",
    "/devhub/screenshots/",
    "/devhub/traces/",
    ".har",
    "auth-state",
    "bearer ",
    "card_number",
    "cookie=",
    "cvv",
    "password=",
    "real user",
    "routing_number",
    "storage-state",
    "token=",
    "trace.zip",
)

ANCHOR_KEYS = frozenset(
    {
        "anchor",
        "page",
        "page_anchor",
        "page_number",
        "section",
        "section_anchor",
        "section_id",
    }
)

OCR_MARKER_KEYS = frozenset(
    {
        "ocr_derived",
        "ocr_only",
        "ocr_text",
    }
)


@dataclass(frozen=True)
class RequirementExtractionReviewFinding:
    """A deterministic reason a review packet cannot be accepted."""

    code: str
    requirement_id: str
    path: str
    message: str


@dataclass(frozen=True)
class RequirementExtractionReviewValidation:
    """Validation result for a requirement extraction review packet."""

    ok: bool
    findings: tuple[RequirementExtractionReviewFinding, ...]


class RequirementExtractionReviewPacketError(ValueError):
    """Raised when a requirement extraction review packet is unsafe."""

    def __init__(self, findings: Sequence[RequirementExtractionReviewFinding]) -> None:
        self.findings = tuple(findings)
        codes = ", ".join(finding.code for finding in self.findings)
        super().__init__(f"requirement extraction review packet rejected: {codes}")


def validate_requirement_extraction_review_packet(
    packet: Mapping[str, object],
    *,
    low_confidence_threshold: float = DEFAULT_LOW_CONFIDENCE_THRESHOLD,
    supported_requirement_types: Iterable[str] = SUPPORTED_REQUIREMENT_TYPES,
) -> RequirementExtractionReviewValidation:
    """Return all blockers found in a requirement extraction review packet."""

    findings: list[RequirementExtractionReviewFinding] = []
    supported_types = {_text(item) for item in supported_requirement_types if _text(item)}
    requirements = _requirements(packet)

    findings.extend(_privacy_findings(packet))

    if _packet_production_ready_with_low_confidence_review_items(packet, requirements, low_confidence_threshold):
        findings.append(
            RequirementExtractionReviewFinding(
                "production_ready_with_low_confidence_review_items",
                "packet",
                "$",
                "packet cannot be marked production-ready while low-confidence review items remain",
            )
        )

    if _has_reordered_step_evidence(packet):
        findings.append(
            RequirementExtractionReviewFinding(
                "reordered_step_evidence",
                "packet",
                "$",
                "extraction review packets must preserve source step evidence order",
            )
        )

    for index, requirement in enumerate(requirements):
        path = f"$.requirements[{index}]"
        requirement_id = _requirement_id(requirement)

        if not _has_citation(requirement):
            findings.append(
                RequirementExtractionReviewFinding(
                    "uncited_requirement",
                    requirement_id,
                    path,
                    "requirement review nodes must include source evidence or citation spans",
                )
            )
        elif not _has_page_or_section_anchor(requirement):
            findings.append(
                RequirementExtractionReviewFinding(
                    "missing_page_or_section_anchor",
                    requirement_id,
                    path,
                    "cited extraction evidence must include a page or section anchor",
                )
            )

        if _low_confidence_without_human_review(requirement, low_confidence_threshold):
            findings.append(
                RequirementExtractionReviewFinding(
                    "low_confidence_without_human_review_status",
                    requirement_id,
                    path,
                    "low-confidence requirement nodes must carry a human-review status",
                )
            )

        requirement_type = _text(requirement.get("requirement_type") or requirement.get("type"))
        if not requirement_type or requirement_type not in supported_types:
            findings.append(
                RequirementExtractionReviewFinding(
                    "unsupported_requirement_type",
                    requirement_id,
                    path,
                    "requirement type is not supported for PP&D extraction review packets",
                )
            )

        if not _sequence(requirement.get("permit_types") or requirement.get("permit_type_ids") or requirement.get("permitTypeIds")):
            findings.append(
                RequirementExtractionReviewFinding(
                    "missing_permit_link",
                    requirement_id,
                    path,
                    "requirement nodes must link to at least one permit type",
                )
            )

        if not _sequence(requirement.get("process_stage") or requirement.get("process_stages") or requirement.get("processStageIds")):
            findings.append(
                RequirementExtractionReviewFinding(
                    "missing_process_stage_link",
                    requirement_id,
                    path,
                    "requirement nodes must link to a process stage",
                )
            )

        if _formalization_ready_before_review(requirement):
            findings.append(
                RequirementExtractionReviewFinding(
                    "formalization_ready_before_review",
                    requirement_id,
                    path,
                    "formalization_status cannot be ready until human review is complete",
                )
            )

        if _has_unsupported_ocr_confidence_escalation(requirement):
            findings.append(
                RequirementExtractionReviewFinding(
                    "unsupported_ocr_confidence_escalation",
                    requirement_id,
                    path,
                    "OCR-derived extraction confidence cannot exceed OCR confidence without explicit support",
                )
            )

    return RequirementExtractionReviewValidation(ok=not findings, findings=tuple(findings))


def require_requirement_extraction_review_packet(
    packet: Mapping[str, object],
    *,
    low_confidence_threshold: float = DEFAULT_LOW_CONFIDENCE_THRESHOLD,
    supported_requirement_types: Iterable[str] = SUPPORTED_REQUIREMENT_TYPES,
) -> None:
    """Raise when a requirement extraction review packet is not safe to accept."""

    result = validate_requirement_extraction_review_packet(
        packet,
        low_confidence_threshold=low_confidence_threshold,
        supported_requirement_types=supported_requirement_types,
    )
    if result.findings:
        raise RequirementExtractionReviewPacketError(result.findings)


def _requirements(packet: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    value = packet.get("requirements") or packet.get("requirement_nodes") or packet.get("nodes")
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _requirement_id(requirement: Mapping[str, object]) -> str:
    return _text(requirement.get("requirement_id") or requirement.get("id")) or "unknown-requirement"


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalized(value: object) -> str:
    return _text(value).lower().replace("-", "_").replace(" ", "_")


def _sequence(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, Iterable):
        return tuple(text for item in value if (text := _text(item)))
    text = _text(value)
    return (text,) if text else ()


def _has_citation(requirement: Mapping[str, object]) -> bool:
    if _sequence(requirement.get("source_evidence_ids") or requirement.get("sourceEvidenceIds")):
        return True
    for key in ("citation_spans", "citations", "source_evidence"):
        value = requirement.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            if any(isinstance(item, Mapping) for item in value):
                return True
    return False


def _has_page_or_section_anchor(requirement: Mapping[str, object]) -> bool:
    for source_id in _sequence(requirement.get("source_evidence_ids") or requirement.get("sourceEvidenceIds")):
        normalized = _normalized(source_id)
        if "page" in normalized or "section" in normalized:
            return True

    for key in ("citation_spans", "citations", "source_evidence", "evidence_records"):
        value = requirement.get(key)
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
            continue
        for item in value:
            if isinstance(item, Mapping) and _mapping_has_anchor(item):
                return True
    return False


def _mapping_has_anchor(value: Mapping[str, object]) -> bool:
    for key, child in value.items():
        normalized_key = _normalize_key(str(key))
        if normalized_key in ANCHOR_KEYS and _text(child):
            return True
        if normalized_key == "locator":
            locator = _normalized(child)
            if "page" in locator or "section" in locator:
                return True
    return False


def _low_confidence_without_human_review(requirement: Mapping[str, object], threshold: float) -> bool:
    confidence = _number(requirement.get("confidence"))
    if confidence is not None and confidence >= threshold:
        return False
    review_status = _normalized(requirement.get("human_review_status") or requirement.get("review_status"))
    return review_status not in HUMAN_REVIEW_STATUSES


def _formalization_ready_before_review(requirement: Mapping[str, object]) -> bool:
    formalization_status = _normalized(requirement.get("formalization_status") or requirement.get("formalizationStatus"))
    if formalization_status != "ready":
        return False
    review_status = _normalized(requirement.get("human_review_status") or requirement.get("review_status"))
    return review_status not in REVIEWED_STATUSES


def _packet_production_ready_with_low_confidence_review_items(
    packet: Mapping[str, object],
    requirements: Sequence[Mapping[str, object]],
    threshold: float,
) -> bool:
    packet_status = _normalized(
        packet.get("review_status")
        or packet.get("validation_status")
        or packet.get("promotion_status")
        or packet.get("status")
    )
    if packet_status not in PRODUCTION_READY_STATUSES:
        return False
    return any(_is_low_confidence_review_item(requirement, threshold) for requirement in requirements)


def _is_low_confidence_review_item(requirement: Mapping[str, object], threshold: float) -> bool:
    confidence = _number(requirement.get("confidence"))
    if confidence is not None and confidence >= threshold:
        return False
    review_status = _normalized(requirement.get("human_review_status") or requirement.get("review_status"))
    formalization_status = _normalized(requirement.get("formalization_status") or requirement.get("formalizationStatus"))
    return review_status in LOW_CONFIDENCE_REVIEW_STATUSES or formalization_status in LOW_CONFIDENCE_REVIEW_STATUSES


def _has_reordered_step_evidence(packet: Mapping[str, object]) -> bool:
    expected = _sequence(packet.get("expected_step_evidence_order") or packet.get("source_step_order"))
    observed = _sequence(packet.get("extracted_step_evidence_order") or packet.get("observed_step_order"))
    if expected and observed and expected != observed:
        return True

    for requirement in _requirements(packet):
        records = requirement.get("evidence_records")
        if not isinstance(records, Sequence) or isinstance(records, (str, bytes, bytearray)):
            continue
        source_order = tuple(
            _text(record.get("source_order"))
            for record in records
            if isinstance(record, Mapping) and _text(record.get("source_order"))
        )
        extracted_order = tuple(
            _text(record.get("extracted_order"))
            for record in records
            if isinstance(record, Mapping) and _text(record.get("extracted_order"))
        )
        if source_order and extracted_order and source_order != extracted_order:
            return True
    return False


def _has_unsupported_ocr_confidence_escalation(requirement: Mapping[str, object]) -> bool:
    if requirement.get("ocr_confidence_escalation_supported") is True:
        return False
    if not _is_ocr_derived(requirement):
        return False
    confidence = _number(requirement.get("confidence") or requirement.get("extraction_confidence"))
    ocr_confidence = _number(requirement.get("ocr_confidence"))
    if confidence is None or ocr_confidence is None:
        return False
    return confidence > ocr_confidence


def _is_ocr_derived(requirement: Mapping[str, object]) -> bool:
    for key in OCR_MARKER_KEYS:
        if requirement.get(key) is True or _text(requirement.get(key)):
            return True
    method = _normalized(requirement.get("extraction_method") or requirement.get("evidence_derivation"))
    return "ocr" in method


def _number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _privacy_findings(value: object, path: str = "$", requirement_id: str = "packet") -> tuple[RequirementExtractionReviewFinding, ...]:
    findings: list[RequirementExtractionReviewFinding] = []
    if isinstance(value, Mapping):
        current_requirement_id = _requirement_id(value) if ("requirement_id" in value or "id" in value) else requirement_id
        for key, child in value.items():
            key_text = str(key)
            normalized_key = _normalize_key(key_text)
            child_path = f"{path}.{key_text}"
            if normalized_key in RAW_DOCUMENT_BODY_KEYS:
                findings.append(
                    RequirementExtractionReviewFinding(
                        "raw_document_body_present",
                        current_requirement_id,
                        child_path,
                        "review packets must carry citations and excerpts, not raw PDF or HTML document bodies",
                    )
                )
            if normalized_key in PRIVATE_VALUE_KEYS:
                findings.append(
                    RequirementExtractionReviewFinding(
                        "private_value_present",
                        current_requirement_id,
                        child_path,
                        "review packets must not include private values or runtime secrets",
                    )
                )
            findings.extend(_privacy_findings(child, child_path, current_requirement_id))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_privacy_findings(child, f"{path}[{index}]", requirement_id))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in PRIVATE_STRING_MARKERS):
            findings.append(
                RequirementExtractionReviewFinding(
                    "private_value_present",
                    requirement_id,
                    path,
                    "review packets must not include private values or runtime artifacts",
                )
            )
    return tuple(findings)


def _normalize_key(value: str) -> str:
    chars: list[str] = []
    for character in value:
        if character.isalnum():
            chars.append(character.lower())
        else:
            chars.append("_")
    normalized = "".join(chars)
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


validate_packet = validate_requirement_extraction_review_packet
require_packet = require_requirement_extraction_review_packet

__all__ = [
    "DEFAULT_LOW_CONFIDENCE_THRESHOLD",
    "HUMAN_REVIEW_STATUSES",
    "RAW_DOCUMENT_BODY_KEYS",
    "REVIEWED_STATUSES",
    "RequirementExtractionReviewFinding",
    "RequirementExtractionReviewPacketError",
    "RequirementExtractionReviewValidation",
    "SUPPORTED_REQUIREMENT_TYPES",
    "require_packet",
    "require_requirement_extraction_review_packet",
    "validate_packet",
    "validate_requirement_extraction_review_packet",
]
