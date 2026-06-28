"""Fixture-first local PDF draft preview safety packets.

The packet builder maps synthetic case facts to synthetic fillable PDF field
metadata. It never opens PDF binaries and never writes preview artifacts; callers
receive an in-memory dictionary that can be rendered by a UI or test harness.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

_BLOCKED_PURPOSES = frozenset({"signature", "certification", "submission", "upload", "payment"})
_PRIVATE_SENSITIVITIES = frozenset({"contact", "credential", "payment", "private", "sensitive_identifier"})
_REDACTION_RE = re.compile(r"^\[REDACTED:[A-Z_]+\]$")
_PRIVATE_PATH_RE = re.compile(r"(/home/|/Users/|file://|[A-Za-z]:\\\\)")
_READY_SUBMISSION_RE = re.compile(r"\b(ready for submission|ready to submit|submission-ready|ready-for-submission)\b", re.IGNORECASE)
_RAW_PDF_KEYS = frozenset(
    {
        "downloaded_document_path",
        "local_pdf_path",
        "pdf_binary",
        "pdf_binary_base64",
        "pdf_bytes",
        "persisted_pdf_path",
        "raw_pdf_base64",
        "raw_pdf_bytes",
        "raw_pdf_path",
    }
)
_TRUE_RAW_PERSISTENCE_KEYS = frozenset({"document_artifact_written", "pdf_binary_written", "raw_pdf_persisted"})
_TRUE_UPLOAD_STAGING_KEYS = frozenset({"devhub_upload_staged", "official_upload_staged", "official_upload_staging", "upload_staged"})
_TRUE_READY_KEYS = frozenset({"ready_for_submission", "ready_to_submit", "submission_ready"})


def load_safety_packet_fixture(path: str | Path) -> dict[str, Any]:
    """Load a committed synthetic local-preview fixture."""
    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as fixture_file:
        payload = json.load(fixture_file)
    if not isinstance(payload, dict):
        raise ValueError("draft preview safety fixture must be a JSON object")
    return payload


def build_draft_preview_safety_packet(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Build a non-persistent preview packet from synthetic facts and fields."""
    _validate_no_private_paths(fixture)
    _validate_no_raw_pdf_persistence(fixture)
    _validate_no_official_upload_staging(fixture)
    _validate_no_ready_submission_claims(fixture)
    _require_true(fixture.get("synthetic_fixture"), "fixture must declare synthetic_fixture=true")
    _require_true(fixture.get("pdf_binary_read") is False, "fixture must declare pdf_binary_read=false")

    case_id = _required_string(fixture, "case_id")
    document_id = _required_string(fixture, "document_id")
    facts = _required_list(fixture, "case_facts")
    fields = _required_list(fixture, "fillable_pdf_fields")
    evidence = _required_list(fixture, "citation_evidence")

    evidence_ids = _evidence_ids(evidence)
    fact_by_id = _fact_index(facts)

    field_mappings: list[dict[str, Any]] = []
    missing_facts: list[dict[str, Any]] = []
    blocked_fields: list[dict[str, Any]] = []

    for raw_field in fields:
        if not isinstance(raw_field, Mapping):
            raise ValueError("fillable_pdf_fields entries must be objects")
        field_name = _required_string(raw_field, "field_name")
        field_type = _required_string(raw_field, "field_type")
        fact_id = raw_field.get("fact_id")
        purpose = str(raw_field.get("purpose", "data_entry"))
        required = bool(raw_field.get("required", False))
        field_evidence_ids = _string_list(raw_field.get("source_evidence_ids", []), "source_evidence_ids")
        if not field_evidence_ids:
            raise ValueError(f"field {field_name} is missing source evidence citations")
        unknown_evidence = sorted(set(field_evidence_ids) - evidence_ids)
        if unknown_evidence:
            raise ValueError(f"field {field_name} cites unknown evidence ids: {unknown_evidence}")

        is_blocked = purpose in _BLOCKED_PURPOSES or bool(raw_field.get("requires_exact_confirmation", False))
        fact = fact_by_id.get(fact_id) if isinstance(fact_id, str) else None
        value = fact.get("value") if isinstance(fact, Mapping) else None
        redaction_label = fact.get("redaction_label") if isinstance(fact, Mapping) else None
        has_value = _has_value(value)

        if is_blocked:
            if has_value:
                raise ValueError(f"filled signature or certification field is not allowed in local preview: {field_name}")
            blocked_fields.append(
                {
                    "field_name": field_name,
                    "field_type": field_type,
                    "purpose": purpose,
                    "status": "blocked_requires_attended_exact_confirmation",
                    "reason": "signature, certification, upload, submission, and payment fields are not preview-draftable",
                    "source_evidence_ids": field_evidence_ids,
                }
            )
            draft_value = None
            mapping_status = "blocked"
        elif not has_value:
            draft_value = None
            mapping_status = "missing_fact" if required else "blank_optional"
            if required and isinstance(fact_id, str):
                missing_facts.append(
                    {
                        "fact_id": fact_id,
                        "field_name": field_name,
                        "reason": "required synthetic fact is absent from the local preview fixture",
                        "source_evidence_ids": field_evidence_ids,
                    }
                )
        else:
            draft_value = _preview_value(value, redaction_label)
            mapping_status = "redacted_for_preview" if redaction_label else "mapped_for_preview"

        field_mappings.append(
            {
                "field_name": field_name,
                "field_type": field_type,
                "fact_id": fact_id,
                "draft_value": draft_value,
                "mapping_status": mapping_status,
                "redaction_label": redaction_label,
                "source_evidence_ids": field_evidence_ids,
            }
        )

    packet = {
        "packet_kind": "local_pdf_draft_preview_safety_packet",
        "case_id": case_id,
        "document_id": document_id,
        "synthetic_fixture": True,
        "non_persistent_preview_output": True,
        "pdf_binary_read": False,
        "pdf_binary_written": False,
        "document_artifact_written": False,
        "citation_evidence": evidence,
        "field_mappings": field_mappings,
        "missing_facts": missing_facts,
        "blocked_signature_certification_fields": blocked_fields,
        "allowed_actions": ["render_non_persistent_local_preview", "ask_for_missing_synthetic_facts"],
        "blocked_actions": ["read_private_pdf", "write_pdf_artifact", "sign", "certify", "upload", "submit", "pay"],
        "privacy_controls": {
            "stores_credentials": False,
            "stores_session_state": False,
            "stores_payment_details": False,
            "stores_private_pdf_paths": False,
            "uses_redaction_labels": True,
        },
    }
    _validate_no_private_paths(packet)
    _validate_no_raw_pdf_persistence(packet)
    _validate_no_official_upload_staging(packet)
    _validate_no_ready_submission_claims(packet)
    return packet


def _evidence_ids(evidence: list[Any]) -> set[str]:
    evidence_ids: set[str] = set()
    for raw_evidence in evidence:
        if not isinstance(raw_evidence, Mapping):
            raise ValueError("citation_evidence entries must be objects")
        evidence_id = _required_string(raw_evidence, "evidence_id")
        _required_string(raw_evidence, "source_url")
        _required_string(raw_evidence, "evidence_label")
        if evidence_id in evidence_ids:
            raise ValueError(f"duplicate evidence_id: {evidence_id}")
        evidence_ids.add(evidence_id)
    return evidence_ids


def _fact_index(facts: list[Any]) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for raw_fact in facts:
        if not isinstance(raw_fact, Mapping):
            raise ValueError("case_facts entries must be objects")
        fact_id = _required_string(raw_fact, "fact_id")
        if fact_id in indexed:
            raise ValueError(f"duplicate fact_id: {fact_id}")
        sensitivity = str(raw_fact.get("sensitivity", "ordinary"))
        value = raw_fact.get("value")
        label = raw_fact.get("redaction_label")
        if label is not None and (not isinstance(label, str) or not _REDACTION_RE.match(label)):
            raise ValueError(f"invalid redaction label for {fact_id}")
        if sensitivity in _PRIVATE_SENSITIVITIES and _has_value(value):
            if not isinstance(value, str) or not _REDACTION_RE.match(value):
                raise ValueError(f"unredacted private value for {fact_id}")
            if isinstance(label, str) and label != value:
                raise ValueError(f"redaction label must match redacted value for {fact_id}")
        indexed[fact_id] = raw_fact
    return indexed


def _preview_value(value: Any, redaction_label: Any) -> Any:
    if isinstance(redaction_label, str):
        return redaction_label
    return value


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _validate_no_private_paths(value: Any) -> None:
    if isinstance(value, str):
        if _PRIVATE_PATH_RE.search(value):
            raise ValueError("preview packet contains a private local path or file URI")
    elif isinstance(value, Mapping):
        for child in value.values():
            _validate_no_private_paths(child)
    elif isinstance(value, list):
        for child in value:
            _validate_no_private_paths(child)


def _validate_no_raw_pdf_persistence(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in _TRUE_RAW_PERSISTENCE_KEYS and child is not False:
                raise ValueError(f"raw PDF persistence is not allowed: {key}")
            if key in _RAW_PDF_KEYS and _has_value(child):
                raise ValueError(f"raw PDF persistence is not allowed: {key}")
            _validate_no_raw_pdf_persistence(child)
    elif isinstance(value, list):
        for child in value:
            _validate_no_raw_pdf_persistence(child)


def _validate_no_official_upload_staging(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in _TRUE_UPLOAD_STAGING_KEYS and child is not False:
                raise ValueError(f"official upload staging is not allowed: {key}")
            _validate_no_official_upload_staging(child)
    elif isinstance(value, list):
        for child in value:
            _validate_no_official_upload_staging(child)


def _validate_no_ready_submission_claims(value: Any) -> None:
    if isinstance(value, str):
        if _READY_SUBMISSION_RE.search(value):
            raise ValueError("local preview must not claim a draft is ready for submission")
    elif isinstance(value, Mapping):
        for key, child in value.items():
            if key in _TRUE_READY_KEYS and child is not False:
                raise ValueError("local preview must not claim a draft is ready for submission")
            _validate_no_ready_submission_claims(child)
    elif isinstance(value, list):
        for child in value:
            _validate_no_ready_submission_claims(child)


def _required_string(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing required string: {key}")
    return value


def _required_list(mapping: Mapping[str, Any], key: str) -> list[Any]:
    value = mapping.get(key)
    if not isinstance(value, list):
        raise ValueError(f"missing required list: {key}")
    return value


def _string_list(value: Any, key: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{key} must be a list of strings")
    return list(value)


def _require_true(condition: Any, message: str) -> None:
    if condition is not True:
        raise ValueError(message)
