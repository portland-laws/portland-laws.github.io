"""Validate fixture-first PP&D extraction quality review packets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

LOW_CONFIDENCE_THRESHOLD = 0.75
REQUIRED_DOCUMENT_TYPES = frozenset({"html", "pdf", "form"})
LOW_CONFIDENCE_REVIEW_STATUSES = frozenset({"needs_human_review", "pending_human_review", "review_queue"})
RAW_BODY_KEYS = frozenset({"body", "body_html", "body_text", "full_html", "full_text", "html", "pdf_bytes", "raw_body", "raw_download", "raw_html", "raw_pdf", "raw_text"})
PRIVATE_KEYS = frozenset({"auth_state", "card_number", "cookie", "cookies", "cvv", "password", "payment_details", "private_value", "raw_value", "session_state", "ssn", "storage_state", "token"})
PRIVATE_MARKERS = ("/devhub/.auth/", "/devhub/downloads/", "/devhub/traces/", ".har", "bearer ", "cookie=", "password=", "storage-state", "token=")


@dataclass(frozen=True)
class ExtractionQualityReviewFinding:
    code: str
    document_id: str
    path: str
    message: str


@dataclass(frozen=True)
class ExtractionQualityReviewValidation:
    ok: bool
    findings: tuple[ExtractionQualityReviewFinding, ...]


class ExtractionQualityReviewPacketError(ValueError):
    def __init__(self, findings: Sequence[ExtractionQualityReviewFinding]) -> None:
        self.findings = tuple(findings)
        codes = ", ".join(finding.code for finding in self.findings)
        super().__init__(f"extraction quality review packet rejected: {codes}")


def validate_extraction_quality_review_packet(packet: Mapping[str, object], *, low_confidence_threshold: float = LOW_CONFIDENCE_THRESHOLD) -> ExtractionQualityReviewValidation:
    findings: list[ExtractionQualityReviewFinding] = []
    records = _records(packet)

    findings.extend(_privacy_findings(packet))

    present_types = {_document_type(record) for record in records}
    for required_type in sorted(REQUIRED_DOCUMENT_TYPES - present_types):
        findings.append(ExtractionQualityReviewFinding("missing_document_type_sample", "packet", "$.documentRecords", f"packet must include a synthetic {required_type} document record"))

    for index, record in enumerate(records):
        path = f"$.documentRecords[{index}]"
        document_id = _document_id(record)
        if record.get("synthetic") is not True:
            findings.append(ExtractionQualityReviewFinding("non_synthetic_record", document_id, path, "review packet records must be synthetic fixtures"))
        if not _citation_spans(record):
            findings.append(ExtractionQualityReviewFinding("missing_citation_spans", document_id, path, "document records must include citation spans"))
        if not _ordered_items(record.get("headings") or record.get("sections")):
            findings.append(ExtractionQualityReviewFinding("unordered_headings", document_id, f"{path}.headings", "headings or sections must preserve source order"))
        if _document_type(record) in {"html", "pdf"} and not _tables_with_citations(record):
            findings.append(ExtractionQualityReviewFinding("missing_table_review_sample", document_id, f"{path}.tables", "HTML and PDF records must include table samples with citations"))
        if _document_type(record) in {"pdf", "form"} and not _sequence(record.get("fileRules") or record.get("file_rules")):
            findings.append(ExtractionQualityReviewFinding("missing_file_rules", document_id, path, "PDF and form records must include extracted file rules"))
        if _document_type(record) == "form" and not _sequence(record.get("certificationLanguage") or record.get("certification_language")):
            findings.append(ExtractionQualityReviewFinding("missing_certification_language", document_id, path, "form records must include certification or acknowledgement language"))
        if not _sequence(record.get("feeTriggers") or record.get("fee_triggers")):
            findings.append(ExtractionQualityReviewFinding("missing_fee_triggers", document_id, path, "records must include fee trigger extraction samples"))
        if not _sequence(record.get("deadlines")):
            findings.append(ExtractionQualityReviewFinding("missing_deadlines", document_id, path, "records must include deadline extraction samples"))
        if _low_confidence_without_review_route(record, low_confidence_threshold):
            findings.append(ExtractionQualityReviewFinding("low_confidence_without_review_route", document_id, path, "low-confidence records must route to human review"))

    return ExtractionQualityReviewValidation(ok=not findings, findings=tuple(findings))


def require_extraction_quality_review_packet(packet: Mapping[str, object], *, low_confidence_threshold: float = LOW_CONFIDENCE_THRESHOLD) -> None:
    result = validate_extraction_quality_review_packet(packet, low_confidence_threshold=low_confidence_threshold)
    if result.findings:
        raise ExtractionQualityReviewPacketError(result.findings)


def _records(packet: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    value = packet.get("documentRecords") or packet.get("document_records") or packet.get("records")
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _document_id(record: Mapping[str, object]) -> str:
    return _text(record.get("document_id") or record.get("documentId") or record.get("id")) or "unknown-document"


def _document_type(record: Mapping[str, object]) -> str:
    return _text(record.get("document_type") or record.get("documentType") or record.get("type")).lower()


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _sequence(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)):
        return (value,) if _text(value) else ()
    if isinstance(value, Sequence):
        return tuple(item for item in value if isinstance(item, Mapping) or _text(item))
    return (value,) if _text(value) else ()


def _number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _ordered_items(value: object) -> bool:
    items = tuple(item for item in _sequence(value) if isinstance(item, Mapping))
    if not items:
        return False
    orders: list[float] = []
    for item in items:
        order = _number(item.get("sourceOrder") or item.get("source_order") or item.get("order"))
        if order is None:
            return False
        orders.append(order)
    return orders == sorted(orders) and len(set(orders)) == len(orders)


def _citation_spans(record: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    spans = record.get("citation_spans") or record.get("citationSpans") or record.get("citations")
    return tuple(item for item in _sequence(spans) if isinstance(item, Mapping) and _valid_citation_span(item))


def _valid_citation_span(span: Mapping[str, object]) -> bool:
    return bool(_text(span.get("source_id") or span.get("sourceId")) and _text(span.get("excerpt")) and _number(span.get("start")) is not None and _number(span.get("end")) is not None)


def _tables_with_citations(record: Mapping[str, object]) -> bool:
    tables = tuple(item for item in _sequence(record.get("tables")) if isinstance(item, Mapping))
    for table in tables:
        headers = _sequence(table.get("headers"))
        rows = _sequence(table.get("rows"))
        citations = table.get("citation_spans") or table.get("citationSpans") or table.get("citations")
        if headers and rows and any(isinstance(span, Mapping) and _valid_citation_span(span) for span in _sequence(citations)):
            return True
    return False


def _low_confidence_without_review_route(record: Mapping[str, object], threshold: float) -> bool:
    confidence = _number(record.get("extractionConfidence") or record.get("extraction_confidence") or record.get("confidence"))
    if confidence is not None and confidence >= threshold:
        return False
    status = _text(record.get("humanReviewStatus") or record.get("human_review_status") or record.get("review_status")).lower()
    queue = _text(record.get("reviewQueue") or record.get("review_queue"))
    return status not in LOW_CONFIDENCE_REVIEW_STATUSES or not queue


def _privacy_findings(value: object, path: str = "$", document_id: str = "packet") -> tuple[ExtractionQualityReviewFinding, ...]:
    findings: list[ExtractionQualityReviewFinding] = []
    if isinstance(value, Mapping):
        current_document_id = _document_id(value) if any(key in value for key in ("document_id", "documentId", "id")) else document_id
        for key, child in value.items():
            key_text = str(key)
            normalized_key = _normalize_key(key_text)
            child_path = f"{path}.{key_text}"
            if normalized_key in RAW_BODY_KEYS:
                findings.append(ExtractionQualityReviewFinding("raw_document_body_present", current_document_id, child_path, "review packets must not include raw HTML, PDF, form, or download bodies"))
            if normalized_key in PRIVATE_KEYS:
                findings.append(ExtractionQualityReviewFinding("private_value_present", current_document_id, child_path, "review packets must not include private values, credentials, or runtime state"))
            findings.extend(_privacy_findings(child, child_path, current_document_id))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            findings.extend(_privacy_findings(child, f"{path}[{index}]", document_id))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in PRIVATE_MARKERS):
            findings.append(ExtractionQualityReviewFinding("private_value_present", document_id, path, "review packets must not include private values or runtime artifacts"))
    return tuple(findings)


def _normalize_key(value: str) -> str:
    chars: list[str] = []
    for character in value:
        chars.append(character.lower() if character.isalnum() else "_")
    normalized = "".join(chars)
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


validate_packet = validate_extraction_quality_review_packet
require_packet = require_extraction_quality_review_packet

__all__ = ["ExtractionQualityReviewFinding", "ExtractionQualityReviewPacketError", "ExtractionQualityReviewValidation", "LOW_CONFIDENCE_THRESHOLD", "require_extraction_quality_review_packet", "require_packet", "validate_extraction_quality_review_packet", "validate_packet"]
