"""Safety validation for PP&D form-field extraction fixtures.

These validators are intentionally fixture-focused. They check committed,
redacted extraction records and reject data shapes that would make later agent
planning unsafe: uncited required fields, raw document bodies, downloaded bytes,
private user values, or instructions to perform consequential DevHub actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence
import re


@dataclass(frozen=True)
class FormFieldFixtureFinding:
    path: str
    reason: str


RAW_PDF_BODY_KEYS = {
    "rawPdfBody",
    "raw_pdf_body",
    "pdfBody",
    "pdf_body",
    "rawPdfText",
    "raw_pdf_text",
    "responseBody",
    "response_body",
}

DOWNLOADED_DOCUMENT_BYTE_KEYS = {
    "downloadedDocumentBytes",
    "downloaded_document_bytes",
    "downloadedBytes",
    "downloaded_bytes",
    "documentBytes",
    "document_bytes",
    "pdfBytes",
    "pdf_bytes",
}

PRIVATE_USER_VALUE_KEYS = {
    "privateUserValue",
    "private_user_value",
    "privateUserValues",
    "private_user_values",
    "userValue",
    "user_value",
    "actualValue",
    "actual_value",
    "enteredValue",
    "entered_value",
}

INSTRUCTION_KEYS = {
    "instruction",
    "instructions",
    "instructionText",
    "instruction_text",
    "actionInstruction",
    "action_instruction",
    "agentInstruction",
    "agent_instruction",
    "nextStep",
    "next_step",
}

CONSEQUENTIAL_ACTION_RE = re.compile(
    r"\b(submit|certify|certification|upload|pay|payment|cancel|cancellation)\b"
    r"|\bschedule\s+(?:an?\s+)?inspection\b"
    r"|\binspection\s+scheduling\b",
    re.IGNORECASE,
)


def validate_form_field_extraction_fixture(fixture: Mapping[str, Any]) -> list[FormFieldFixtureFinding]:
    """Return deterministic safety findings for a form-field extraction fixture."""

    findings: list[FormFieldFixtureFinding] = []
    evidence_ids = _source_evidence_ids(fixture, findings)
    fields = fixture.get("fields")

    if not isinstance(fields, Sequence) or isinstance(fields, (str, bytes, bytearray)):
        findings.append(FormFieldFixtureFinding("$.fields", "fixture requires a fields array"))
    else:
        for index, field in enumerate(fields):
            field_path = f"$.fields[{index}]"
            if not isinstance(field, Mapping):
                findings.append(FormFieldFixtureFinding(field_path, "field record must be an object"))
                continue
            _validate_field(field, field_path, evidence_ids, findings)

    for path, key, value in _walk_json(fixture):
        if key in RAW_PDF_BODY_KEYS and _has_retained_value(value):
            findings.append(FormFieldFixtureFinding(path, "raw PDF bodies are not allowed in form-field fixtures"))
        if key in DOWNLOADED_DOCUMENT_BYTE_KEYS and _has_retained_value(value):
            findings.append(FormFieldFixtureFinding(path, "downloaded document bytes are not allowed in form-field fixtures"))
        if key in PRIVATE_USER_VALUE_KEYS and _has_private_value(value):
            findings.append(FormFieldFixtureFinding(path, "private user values are not allowed in form-field fixtures"))
        if key in INSTRUCTION_KEYS and _contains_consequential_instruction(value):
            findings.append(
                FormFieldFixtureFinding(
                    path,
                    "fixtures must not instruct agents to submit, certify, upload, pay, cancel, or schedule inspections",
                )
            )

    return findings


def assert_form_field_extraction_fixture_safe(fixture: Mapping[str, Any]) -> None:
    findings = validate_form_field_extraction_fixture(fixture)
    if findings:
        details = "; ".join(f"{finding.path}: {finding.reason}" for finding in findings)
        raise AssertionError(details)


def _source_evidence_ids(fixture: Mapping[str, Any], findings: list[FormFieldFixtureFinding]) -> set[str]:
    evidence = fixture.get("sourceEvidence")
    if not isinstance(evidence, Sequence) or isinstance(evidence, (str, bytes, bytearray)):
        findings.append(FormFieldFixtureFinding("$.sourceEvidence", "fixture requires a sourceEvidence array"))
        return set()

    ids: set[str] = set()
    for index, item in enumerate(evidence):
        path = f"$.sourceEvidence[{index}]"
        if not isinstance(item, Mapping):
            findings.append(FormFieldFixtureFinding(path, "source evidence record must be an object"))
            continue
        evidence_id = item.get("id")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            findings.append(FormFieldFixtureFinding(f"{path}.id", "source evidence id is required"))
            continue
        ids.add(evidence_id)
        if not isinstance(item.get("url"), str) or not item.get("url", "").startswith("https://"):
            findings.append(FormFieldFixtureFinding(f"{path}.url", "source evidence url must be https"))
        if not isinstance(item.get("quote"), str) or not item.get("quote", "").strip():
            findings.append(FormFieldFixtureFinding(f"{path}.quote", "source evidence quote is required"))
    return ids


def _validate_field(
    field: Mapping[str, Any],
    path: str,
    evidence_ids: set[str],
    findings: list[FormFieldFixtureFinding],
) -> None:
    field_id = field.get("id")
    if not isinstance(field_id, str) or not field_id.strip():
        findings.append(FormFieldFixtureFinding(f"{path}.id", "field id is required"))

    required = field.get("required") is True
    citations = field.get("citations")
    if required:
        if not isinstance(citations, Sequence) or isinstance(citations, (str, bytes, bytearray)) or not citations:
            findings.append(FormFieldFixtureFinding(f"{path}.citations", "required fields must cite source evidence"))
            return
        for citation_index, citation in enumerate(citations):
            citation_path = f"{path}.citations[{citation_index}]"
            if not isinstance(citation, str) or citation not in evidence_ids:
                findings.append(FormFieldFixtureFinding(citation_path, "required field citation must reference source evidence"))


def _walk_json(value: Any, path: str = "$", key: str | None = None) -> Iterable[tuple[str, str | None, Any]]:
    yield path, key, value
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_key_text = str(child_key)
            yield from _walk_json(child_value, f"{path}.{child_key_text}", child_key_text)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child_value in enumerate(value):
            yield from _walk_json(child_value, f"{path}[{index}]", key)


def _has_retained_value(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return bool(value)
    if isinstance(value, Mapping):
        return bool(value)
    return True


def _has_private_value(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return value.strip() not in {"", "[REDACTED]", "", "REDACTED"}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_has_private_value(item) for item in value)
    if isinstance(value, Mapping):
        return any(_has_private_value(item) for item in value.values())
    return True


def _contains_consequential_instruction(value: Any) -> bool:
    if isinstance(value, str):
        return CONSEQUENT_ACTION_TEXT_FOUND(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_consequential_instruction(item) for item in value)
    if isinstance(value, Mapping):
        return any(_contains_consequential_instruction(item) for item in value.values())
    return False


def CONSEQUENT_ACTION_TEXT_FOUND(text: str) -> bool:
    return bool(CONSEQUENTIAL_ACTION_RE.search(text))
